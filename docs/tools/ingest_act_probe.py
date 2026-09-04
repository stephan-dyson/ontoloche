# -*- coding: utf-8 -*-
"""Design test 5 for `docs/specs/INGEST.md` v0 -- **the ingest ACT**, and it exists
because round 1 counted that section 4 had no probe at all.

**The two findings it closes**, both BLOCKING and both ending with two host rows
answering to one identity through ordinary calls:

* **F4 (the beacon-integrator lens).** Two rows in ONE ingest act resolve the same label
  *before either is written*. Both scans finish, so rule 3-7 is satisfied and both
  correctly answer ``proposal``. Both are approved. **Every rule in section 3 fires
  correctly and the state is created between two correct answers** -- a guard that was
  never asked rather than a guard that failed to look.
* **K4 (the kill-row lens).** Between a proposal and the host's write, the state the
  resolution read is unchanged, so the permission can be cashed again -- three passes,
  three unreviewed invocations, no warning. **The concurrent variant needs no repeat
  call at all.** That is standing rule (c) one surface down: *a pending ingest proposal
  is an unconsumed permission to mint an instance identity.*

Rules 4-10 and 4-11 are what close them, and **each is proved by MUTATION**: run with
the rule disabled and the check must go red.

The fixture is UC2's own: two landed rows for one CMS facility that the host does not
yet hold, plus the twelve-way ``MILLER'S MERRY MANOR`` collision for the ambiguous path.

Run: ``py docs/tools/ingest_act_probe.py [--csv <NH_HealthCitations_Aug2026.csv>]``
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingest_probe_kit import (  # noqa: E402
    CandidateRef, HostTable, InstanceContext, InstanceRecord, Vocabulary,
    resolve_instance,
)
from ingest_seam_probe import (  # noqa: E402
    CHECKS, T1_2, T1_3, T1_3_CCN, _resolve_csv, check, cms_vocab, load_host_rows,
)


# --------------------------------------------------------------------------------
# The LEDGER -- ACTIONS.md's, modelled only as far as section 4 needs it
# --------------------------------------------------------------------------------


@dataclass
class Invocation:
    invocation_id: str
    family: str
    namespace: str
    type_name: str
    label: str
    outcome: str
    approval_mode: str
    warnings: tuple[str, ...]
    reviewed_by: str | None = None
    minted_ref: str | None = None          # the `results` slot amendment A2 asks for


@dataclass
class Ledger:
    """`invocations(unreviewed=True)` and `review_invocation`, and nothing else."""

    rows: list[Invocation] = field(default_factory=list)

    def record(self, inv: Invocation) -> Invocation:
        self.rows.append(inv)
        return inv

    def unreviewed(self, *, namespace: str | None = None, type_name: str | None = None,
                   label: str | None = None) -> list[Invocation]:
        out = [i for i in self.rows if i.reviewed_by is None]
        if namespace is not None:
            out = [i for i in out if i.namespace == namespace]
        if type_name is not None:
            out = [i for i in out if i.type_name == type_name]
        if label is not None:
            out = [i for i in out if i.label == label]
        return out


class IngestAct:
    """One ingest act. INGEST 4.3, rules 4-10 and 4-11.

    ``enforce`` is the MUTATION harness: with a rule named here disabled, the check that
    closes it must go red.
    """

    def __init__(self, act_id: str, *, host: HostTable, vocab: Vocabulary,
                 ledger: Ledger, namespace: str, type_name: str,
                 enforce: frozenset[str] = frozenset({"4-10", "4-11"})) -> None:
        self.act_id = act_id
        self.host, self.vocab, self.ledger = host, vocab, ledger
        self.namespace, self.type_name = namespace, type_name
        self.enforce = enforce
        self._minted: dict[str, CandidateRef] = {}     # rule 4-10's per-act memory
        self.host_writes: list[str] = []

    def land(self, label: str, *, tier: str = "sonnet") -> tuple[str, object]:
        """Resolve one landed row and, where the rules allow, record a proposal."""
        # --- rule 4-10: within one act, a label is resolved ONCE --------------
        if "4-10" in self.enforce and label in self._minted:
            return "reused", self._minted[label]

        res = resolve_instance(
            label, InstanceContext(act_id=self.act_id, proposed_by="ai:ingest"),
            host=self.host, vocab=self.vocab, namespace=self.namespace,
            type_name=self.type_name, tier=tier)

        if res.outcome == "existing":
            return "existing", res.ref
        if res.outcome == "unknowable":
            return "unknowable", None            # rule 4-7: no proposal, ever

        warnings: list[str] = []
        mode = "auto"
        if res.outcome == "ambiguous":
            # rule 4-5, with F7's input-name segment
            warnings.append(
                f"instance_ambiguous_at_proposal:{self.type_name}:{res.known}")
            mode = "review"

        # --- rule 4-11: who already holds a pending proposal for this word? ---
        pending = self.ledger.unreviewed(namespace=self.namespace,
                                         type_name=self.type_name, label=label)
        if pending and "4-11" in self.enforce:
            warnings.append(f"instance_proposal_pending:{pending[0].invocation_id}")
            inv = self.ledger.record(Invocation(
                f"inv-{len(self.ledger.rows) + 1}", "propose_instance", self.namespace,
                self.type_name, label, res.outcome, mode, tuple(warnings)))
            return "pending", inv                # mints NO second identity

        inv = self.ledger.record(Invocation(
            f"inv-{len(self.ledger.rows) + 1}", "propose_instance", self.namespace,
            self.type_name, label, res.outcome, mode, tuple(warnings)))
        self._minted[label] = res.candidate
        return "proposed", inv

    def host_writes_for(self, inv: Invocation, instance_id: str) -> InstanceRecord:
        """The HOST mints the identifier and the ledger records it. Rules 4-2, 4-3."""
        inv.minted_ref = (f"{self.namespace}:entity:{self.type_name}#{instance_id}")
        self.host_writes.append(inv.minted_ref)
        return InstanceRecord(self.namespace, "entity", self.type_name, instance_id,
                              inv.label, {})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.environ.get("CMS_CITATIONS_CSV"))
    args = ap.parse_args()

    print("DESIGN TEST 5 -- the ingest ACT (INGEST 4.3), over CMS facilities")
    rows, facts = load_host_rows(_resolve_csv(args.csv))
    print(f"  host: {facts['ccns']} CCNs; the landed rows name a facility it does NOT "
          f"hold")
    without = [rec for rec in rows if rec.instance_id != T1_3_CCN]

    # =====================================================================
    # 5.1 -- F4: two rows in ONE act, resolved before either is written
    # =====================================================================
    print("\n5.1 -- two landed rows in ONE act name the same facility")
    for enforce, tag in ((frozenset({"4-10", "4-11"}), "RULE 4-10 ON "),
                         (frozenset(), "MUTATED (both off)")):
        host = HostTable(list(without))
        ledger = Ledger()
        act = IngestAct("act-1", host=host, vocab=cms_vocab(), ledger=ledger,
                        namespace="cms", type_name="facility", enforce=enforce)
        results = [act.land(T1_3), act.land(T1_3)]
        minted = []
        for i, (kind, obj) in enumerate(results, 1):
            if kind == "proposed":
                rec = act.host_writes_for(obj, f"HOST-{i}")
                minted.append(rec)
                host = HostTable(list(without) + minted)
        after = resolve_instance(
            T1_3, InstanceContext(act_id="after"), host=host, vocab=cms_vocab(),
            namespace="cms", type_name="facility", tier="sonnet")
        print(f"  {tag}: {[k for k, _ in results]}  host writes={act.host_writes}")
        print(f"     the NEXT resolution -> outcome={after.outcome!r} "
              f"known={after.known}")
        if "4-10" in enforce:
            check("5.1 rule 4-10: within one act a label is resolved ONCE, so one "
                  "identity is minted and the next resolution is unambiguous",
                  len(act.host_writes) == 1 and after.outcome == "existing",
                  f"writes={len(act.host_writes)} then {after.outcome}")
        else:
            check("5.1 MUTATION: with the act unbound, ONE act mints TWO identities for "
                  "one label and the next resolution is `ambiguous` -- F4, constructed",
                  len(act.host_writes) == 2 and after.outcome == "ambiguous",
                  f"writes={len(act.host_writes)} then {after.outcome}")

    # =====================================================================
    # 5.2 -- K4: a pending proposal cashed again ACROSS acts
    # =====================================================================
    print("\n5.2 -- the same label landed in three SEPARATE acts, none reviewed")
    print("        (the proposals are PENDING approval, so the host has written "
          "nothing yet -- which is the state K4 is about)")
    for enforce, tag in ((frozenset({"4-10", "4-11"}), "RULE 4-11 ON "),
                         (frozenset({"4-10"}), "MUTATED (4-11 off)")):
        host = HostTable(list(without))
        ledger = Ledger()
        proposed: list[Invocation] = []
        for i in range(1, 4):
            act = IngestAct(f"act-{i}", host=host, vocab=cms_vocab(), ledger=ledger,
                            namespace="cms", type_name="facility", enforce=enforce)
            kind, obj = act.land(T1_3)
            if kind == "proposed":
                proposed.append(obj)
        # ... and only NOW are they approved, and the host writes one row each.
        minted = [InstanceRecord("cms", "entity", "facility", f"HOST-{n}", T1_3, {})
                  for n, _ in enumerate(proposed, 1)]
        host = HostTable(list(without) + minted)
        after = resolve_instance(
            T1_3, InstanceContext(act_id="after"), host=host, vocab=cms_vocab(),
            namespace="cms", type_name="facility", tier="sonnet")
        pend = [w for inv in ledger.rows for w in inv.warnings
                if w.startswith("instance_proposal_pending:")]
        print(f"  {tag}: {len(ledger.rows)} invocations, {len(minted)} host writes")
        print(f"     pending-warnings={pend}")
        print(f"     the NEXT resolution -> outcome={after.outcome!r} "
              f"known={after.known}")
        if "4-11" in enforce:
            check("5.2 rule 4-11: the propose door asks who already holds a pending "
                  "proposal, so three acts mint ONE identity and two carry the warning",
                  len(minted) == 1 and len(pend) == 2 and after.outcome == "existing",
                  f"minted={len(minted)} warned={len(pend)} then {after.outcome}")
        else:
            check("5.2 MUTATION: with rule 4-11 off, three acts mint THREE identities "
                  "for one label with no warning -- K4, constructed",
                  len(minted) == 3 and not pend and after.outcome == "ambiguous",
                  f"minted={len(minted)} warned={len(pend)} then {after.outcome}")

    # =====================================================================
    # 5.3 -- the concurrent variant, which needs no repeat call at all
    # =====================================================================
    print("\n5.3 -- two workers read the SAME state and neither repeats a call")
    host = HostTable(list(without))
    ledger = Ledger()
    acts = [IngestAct(f"worker-{w}", host=host, vocab=cms_vocab(), ledger=Ledger(),
                      namespace="cms", type_name="facility") for w in "AB"]
    both = [a.land(T1_3) for a in acts]          # each has its OWN empty ledger
    minted = [InstanceRecord("cms", "entity", "facility", f"HOST-{w}", T1_3, {})
              for w, (k, _) in zip("AB", both) if k == "proposed"]
    after = resolve_instance(T1_3, InstanceContext(act_id="after"),
                             host=HostTable(list(without) + minted), vocab=cms_vocab(),
                             namespace="cms", type_name="facility", tier="sonnet")
    print(f"  outcomes={[k for k, _ in both]}  host writes={len(minted)}")
    print(f"  the NEXT resolution -> outcome={after.outcome!r} known={after.known}")
    check("5.3 the concurrent case is NOT closed by rules 4-10 or 4-11 and this "
          "document says so: two workers on one store need the host's own uniqueness "
          "constraint, which is `PACKAGE.md` G1's job and not this layer's",
          len(minted) == 2 and after.outcome == "ambiguous",
          f"writes={len(minted)} then {after.outcome}")

    # =====================================================================
    # 5.4 -- the ambiguous path: review mode, the warning grammar, the drain
    # =====================================================================
    print("\n5.4 -- a proposal made while the resolution was `ambiguous`")
    host = HostTable(rows)
    ledger = Ledger()
    act = IngestAct("act-amb", host=host, vocab=cms_vocab(), ledger=ledger,
                    namespace="cms", type_name="facility")
    kind, inv = act.land(T1_2)
    print(f"  land({T1_2!r}) -> {kind}")
    print(f"     outcome={inv.outcome!r} approval_mode={inv.approval_mode!r}")
    print(f"     warnings={inv.warnings}")
    print(f"  invocations(unreviewed=True) -> {len(ledger.unreviewed())}")
    check("5.4 rule 4-5: recorded in `review` mode whatever the family declared",
          inv.approval_mode == "review", inv.approval_mode)
    check("5.4 F7: the warning names WHICH input and how many tied, not just a count",
          any(w.startswith("instance_ambiguous_at_proposal:facility:12")
              for w in inv.warnings), str(inv.warnings))
    check("5.4 rule 4-6: it is enumerable by `invocations(unreviewed=True)`",
          len(ledger.unreviewed()) == 1)
    inv.reviewed_by = "user:curator"
    check("5.4 and `review_invocation` is its only drain",
          len(ledger.unreviewed()) == 0)

    # =====================================================================
    # 5.5 -- rule 4-7: an `unknowable` resolution yields NO proposal
    # =====================================================================
    print("\n5.5 -- rule 4-7: nothing is proposed over an `unknowable` resolution")
    capped = HostTable(list(without), scan_cap=100)
    ledger = Ledger()
    act = IngestAct("act-unk", host=capped, vocab=cms_vocab(), ledger=ledger,
                    namespace="cms", type_name="facility")
    kind, obj = act.land(T1_3)
    print(f"  land over a truncated read -> {kind!r}; ledger holds "
          f"{len(ledger.rows)} invocations")
    check("5.5 rule 4-7: an `unknowable` resolution records no proposal at all",
          kind == "unknowable" and len(ledger.rows) == 0,
          f"{kind} / {len(ledger.rows)}")

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
