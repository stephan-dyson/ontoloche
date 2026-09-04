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
from dataclasses import dataclass, field, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingest_probe_kit import (  # noqa: E402
    ACT_RULES, CandidateRef, HostTable, IngestAct, InstanceContext, InstanceRecord,
    Invocation, Ledger, Vocabulary, act_key, resolve_instance, type_closure,
)
from ingest_seam_probe import (  # noqa: E402
    CHECKS, T1_2, T1_3, T1_3_CCN, _resolve_csv, check, cms_vocab, load_host_rows,
)


# The LEDGER and the ACT now live in `ingest_probe_kit`, imported above.
#
# Round 2 found three doors of one question answered three ways -- the act keyed
# identity on the raw label while the gate keyed it on `norm` (`I-4`), the act's
# ledger key did not follow the successor chain the read follows (`I-3`), and the
# guard's window closed when a proposal DRAINED rather than when its identity was
# WRITTEN (`I-5`). A second implementation is how that happens, which is the same
# lesson round 1 learned about the resolver. **Standing rule (e).**


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

    # =====================================================================
    # 5.6 -- THE TABLE. One check per row of the instance-surface family, and
    #        each one goes RED under the mutation that reproduces the record.
    #        R85: six records, one question, one change -- so one block.
    # =====================================================================
    print("\n5.6 -- the six instance-surface records, each proved by MUTATION")

    def _chain_vocab(*, two_hop: bool = True, dangling: bool = False,
                     other_policy: bool = False):
        """`facility` retired toward `nursing_facility` (-> `ltc_facility`)."""
        v = cms_vocab()
        base = v.entry("cms", "facility")
        v.declare("cms", "facility", replace(base, successor="nursing_facility"))
        if dangling:
            return v
        nxt = replace(base, successor="ltc_facility") if two_hop else replace(base)
        v.declare("cms", "nursing_facility", nxt)
        tail = replace(base, policy=replace(base.policy, match_at=0.995,
                                            why="a different governed policy")) \
            if other_policy else replace(base)
        v.declare("cms", "ltc_facility", tail)
        return v

    host = HostTable(list(without))
    ctx = InstanceContext(act_id="t")

    # --- I-2, mis-walked: the chain, not one hop -------------------------
    for one_hop, tag in ((False, "CHAIN "), (True, "MUTATED (one hop)")):
        r = resolve_instance(T1_3, ctx, host=host, vocab=_chain_vocab(),
                             namespace="cms", type_name="facility", tier="sonnet",
                             _mutate="chain_one_hop" if one_hop else None)
        print(f"  I-2 {tag}: hops={[w for w in r.warnings if 'succeeded' in w]}")
        if not one_hop:
            check("5.6 I-2 rule 3-14: the successor CHAIN is followed to its end, "
                  "not one hop -- and `_identity_closure` is what it is written from",
                  "instance_type_succeeded:ltc_facility" in r.warnings,
                  str(r.warnings))
        else:
            check("5.6 I-2 MUTATION: one hop stops at the intermediate name, which is "
                  "the state two ordinary curation passes reach",
                  "instance_type_succeeded:ltc_facility" not in r.warnings,
                  str(r.warnings))

    # --- I-2's rider: a dangling successor is an HONEST early stop -------
    for keep, tag in ((False, "HONEST STOP"), (True, "MUTATED (keeps predecessor)")):
        r = resolve_instance(T1_3, ctx, host=host, vocab=_chain_vocab(dangling=True),
                             namespace="cms", type_name="facility", tier="sonnet",
                             _mutate="chain_keeps_predecessor" if keep else None)
        print(f"  I-2 rider {tag}: outcome={r.outcome!r} complete={r.complete}")
        if not keep:
            check("5.6 I-2 rider (R84 part 2, the EIGHTH trip's shape): a dangling "
                  "successor stops the walk with `complete=False` and a `why`, rather "
                  "than querying one type while holding another's entry",
                  r.outcome == "unknowable" and not r.complete
                  and "no entry declares" in r.why_incomplete, str(r.outcome))
        else:
            check("5.6 I-2 rider MUTATION: keeping the predecessor's entry DECIDES "
                  "over a chain it could not walk -- one type queried while "
                  "another's entry supplies the governed facts, which is the "
                  "EIGHTH trip's shape (a guard holding one fact while deciding "
                  "about another)",
                  r.outcome != "unknowable" and r.complete,
                  f"{r.outcome} complete={r.complete}")

    # --- D3, the governed-fact half of mis-walked ------------------------
    migrated = HostTable([replace(rec, type_name="ltc_facility")
                          for rec in without])
    for ignore, tag in ((False, "GOVERNED "), (True, "MUTATED (ignored)")):
        r = resolve_instance(T1_3, ctx, host=migrated,
                             vocab=_chain_vocab(other_policy=True),
                             namespace="cms", type_name="facility", tier="sonnet",
                             _mutate="governed_facts_ignored" if ignore else None)
        print(f"  D3 {tag}: outcome={r.outcome!r}")
        if not ignore:
            check("5.6 D3 rule 3-18: a successor declaring a different MatchPolicy or "
                  "predicate is a different extent, so the read does not decide",
                  r.outcome == "unknowable" and "governed facts" in r.reason,
                  f"{r.outcome} / {r.reason[:60]}")
        else:
            check("5.6 D3 MUTATION: ignoring it decides under governed facts the "
                  "caller never declared",
                  r.outcome != "unknowable", str(r.outcome))

    # --- I-6, mis-counted: a page's instance_ids are distinct ------------
    twins = [InstanceRecord("cms", "entity", "facility", "015009",
                            "BURNS NURSING HOME, INC.", {"state": "AL"}),
             InstanceRecord("cms", "entity", "facility", "015009",
                            "BURNS NURSING HOME INC", {"state": "TX"})]
    for ignore, tag in ((False, "DISTINCT "), (True, "MUTATED (ignored)")):
        r = resolve_instance("BURNS NURSING HOME, INC.", ctx, host=HostTable(twins),
                             vocab=cms_vocab(), namespace="cms",
                             type_name="facility", tier="sonnet",
                             _mutate="dup_ids_ignored" if ignore else None)
        print(f"  I-6 {tag}: outcome={r.outcome!r} known={r.known} scanned={r.scanned}")
        if not ignore:
            check("5.6 I-6 rule 2-16: two host records under one `instance_id` make "
                  "the extent uncountable, so the read answers `unknowable`",
                  r.outcome == "unknowable" and "not countable" in r.reason,
                  f"{r.outcome} / {r.reason[:60]}")
        else:
            check("5.6 I-6 MUTATION: ignoring it collapses the two to one and answers "
                  "`existing` at 1.0 with known=1 -- the second row vanishes",
                  r.outcome == "existing" and r.known == 1,
                  f"{r.outcome} / known={r.known}")

    # --- I-4, mis-keyed: the act's key is the gate's key ------------------
    spellings = (T1_3, T1_3.title() + ".")
    for on, tag in ((True, "NORM KEY"), (False, "MUTATED (raw label)")):
        rules = ACT_RULES if on else (ACT_RULES - {"4-10-key", "4-10-relation"})
        h = HostTable(list(without))
        led = Ledger()
        a = IngestAct("act-i4", host=h, vocab=cms_vocab(), ledger=led,
                      namespace="cms", type_name="facility", enforce=rules)
        got = [a.land(spellings[0]), a.land(spellings[1])]
        print(f"  I-4 {tag}: {[k for k, _ in got]}  ledger={len(led.rows)}")
        if on:
            check("5.6 I-4 rule 4-10: the act scopes on the key the GATE decides on, "
                  "so two spellings of one facility are one identity in one act",
                  [k for k, _ in got] == ["proposed", "reused"], str(got[:1]))
        else:
            check("5.6 I-4 MUTATION: keying on the raw label proposes twice for one "
                  "facility the gate itself calls `existing` at 1.0",
                  [k for k, _ in got] == ["proposed", "proposed"], str(got[:1]))

    # --- B1, the TYPE half of the same key -------------------------------
    v_two = cms_vocab()
    v_two.declare("cms", "wing", v_two.entry("cms", "facility"))
    h = HostTable(list(without)
                  + [replace(rec, type_name="wing") for rec in without[:200]])
    a = IngestAct("act-b1", host=h, vocab=v_two, ledger=Ledger(),
                  namespace="cms", type_name="facility")
    k1, o1 = a.land(T1_3)
    k2, o2 = a.land(T1_3, type_name="wing")
    print(f"  B1 per-land type: {k1!r} then {k2!r}")
    check("5.6 B1 rule 4-10: the key carries (namespace, kind, type_name), so a second "
          "TYPE answering to one label is proposed rather than handed the first's ref",
          k1 == "proposed" and k2 == "proposed", f"{k1}/{k2}")

    # --- I-5, mis-timed: drained is not written --------------------------
    for on, tag in ((True, "UNWRITTEN"), (False, "MUTATED (unreviewed only)")):
        rules = ACT_RULES if on else (ACT_RULES - {"4-11-written"})
        h = HostTable(list(without))
        led = Ledger()
        a1 = IngestAct("act-mon", host=h, vocab=cms_vocab(), ledger=led,
                       namespace="cms", type_name="facility", enforce=rules)
        kind1, inv1 = a1.land(T1_3)
        inv1.reviewed_by = "user:curator"          # the drain, and nothing written yet
        a2 = IngestAct("act-tue", host=h, vocab=cms_vocab(), ledger=led,
                       namespace="cms", type_name="facility", enforce=rules)
        kind2, _ = a2.land(T1_3)
        print(f"  I-5 {tag}: {kind1!r} -> drained -> {kind2!r}")
        if on:
            check("5.6 I-5 rule 4-11: the guard asks who holds a proposal whose row is "
                  "NOT YET WRITTEN, so draining one does not re-issue the permission",
                  kind2 == "pending", str(kind2))
        else:
            check("5.6 I-5 MUTATION: asking `unreviewed=True` stands the guard down at "
                  "the moment the permission is live and unconsumed -- rule (c)",
                  kind2 == "proposed", str(kind2))

    # --- I-3, mis-written: the extent is the CLOSURE, not its endpoint ----
    # Z1's construction exactly: act 1 proposes and the host writes the row under the
    # name in force. A governance act then retires that name, and the host migrates
    # the rows it knows about -- leaving the freshly minted one behind, as Z1 observed.
    for on, tag in ((True, "WHOLE CLOSURE"), (False, "MUTATED (endpoint only)")):
        led = Ledger()
        h1 = HostTable(list(without))
        a1 = IngestAct("act-1", host=h1, vocab=cms_vocab(), ledger=led,
                       namespace="cms", type_name="facility")
        _, inv = a1.land(T1_3)
        minted = a1.host_writes_for(inv, "HOST-1")
        v2 = _chain_vocab(two_hop=False)           # facility -> nursing_facility
        after_retire = HostTable(
            [replace(rec, type_name="nursing_facility") for rec in without] + [minted])
        a2 = IngestAct("act-2", host=after_retire, vocab=v2, ledger=led,
                       namespace="cms", type_name="facility")
        kind2, _ = a2.land(
            T1_3, tier="sonnet") if on else (None, None)
        if not on:
            r = resolve_instance(T1_3, ctx, host=after_retire, vocab=v2,
                                 namespace="cms", type_name="facility", tier="sonnet",
                                 _mutate="extent_endpoint_only")
            kind2 = "proposed" if r.outcome == "proposal" else r.outcome
        print(f"  I-3 {tag}: the minted row stayed under 'facility'; "
              f"the second act -> {kind2!r}")
        if on:
            check("5.6 I-3 rule 3-19: the identity's extent is the WHOLE closure, so a "
                  "row written under a name that has since been retired is still found "
                  "and no second identity is minted",
                  kind2 == "existing", str(kind2))
        else:
            check("5.6 I-3 MUTATION: reading the closure's ENDPOINT alone is a smaller "
                  "set than the identity's extent -- the row is unreadable and the act "
                  "proposes a duplicate for a facility the same store holds",
                  kind2 == "proposed", str(kind2))

    # --- Z6: `not_an_instance` mints nothing, like `unknowable` -----------
    for on, tag in ((True, "FENCED"), (False, "MUTATED (unfenced)")):
        rules = ACT_RULES if on else (ACT_RULES - {"4-7-nai"})
        led = Ledger()
        a = IngestAct("act-nai", host=HostTable(list(without)), vocab=cms_vocab(),
                      ledger=led, namespace="cms", type_name="facility",
                      enforce=rules)
        kind, _ = a.land("Provider Name")
        print(f"  Z6 {tag}: land('Provider Name') -> {kind!r}; ledger={len(led.rows)}")
        if on:
            check("5.6 Z6 rule 4-7: `not_an_instance` is the OTHER outcome that mints "
                  "nothing -- the classifier succeeded and said this is not a thing",
                  kind == "not_an_instance" and len(led.rows) == 0,
                  f"{kind}/{len(led.rows)}")
        else:
            check("5.6 Z6 MUTATION: unfenced, a column header becomes a well-formed "
                  "provenance-bearing proposal in `auto` mode",
                  kind == "proposed" and len(led.rows) == 1,
                  f"{kind}/{len(led.rows)}")

    # =====================================================================
    # 5.7 -- ROUND 3. `I-8`'s two relations get their OWN mutations (R87), and
    #        K1, K2, K8, K10, B1 and B7 each get a check that can go red.
    # =====================================================================
    print("\n5.7 -- round 3's cells, each relation mutated separately")

    def _retired(**kw):
        """`facility` retired toward `ltc_facility`; the survivor is the live name."""
        v = cms_vocab()
        base = v.entry("cms", "facility")
        v.declare("cms", "facility", replace(base, successor="ltc_facility"))
        v.declare("cms", "ltc_facility", replace(base, **kw))
        return v

    # --- I-8, the BACKWARD relation -------------------------------------
    # A caller naming the SURVIVOR -- the name every caller uses after a retirement.
    part = HostTable([replace(rec, type_name="ltc_facility") for rec in without[:80]]
                     + [InstanceRecord("cms", "entity", "facility", "155049",
                                       T1_2, {"state": "IN"})])
    for fwd, tag in ((False, "BOTH WAYS"), (True, "MUTATED (forward only)")):
        r = resolve_instance(T1_2, ctx, host=part, vocab=_retired(),
                             namespace="cms", type_name="ltc_facility", tier="sonnet",
                             _mutate="closure_forward_only" if fwd else None)
        print(f"  I-8 backward {tag}: outcome={r.outcome!r} scanned={r.scanned}")
        if not fwd:
            check("5.7 I-8 rule 3-20: the closure walks BACKWARD too, so a caller "
                  "naming the SURVIVOR of a retirement sees the row still written "
                  "under the retired name -- the ordinary post-retirement path",
                  r.outcome == "existing", str(r.outcome))
        else:
            check("5.7 I-8 MUTATION (backward): forward-only reads a strict SUBSET of "
                  "the identity and the act proposes a second row in `auto` mode",
                  r.outcome == "proposal", str(r.outcome))

    # --- I-8, the ALIAS relation, mutated SEPARATELY (R87) ---------------
    alias_host = HostTable([InstanceRecord("cms", "entity", "ltc_alias", "155049",
                                           T1_2, {"state": "IN"})])
    v_al = cms_vocab()
    v_al.declare("cms", "ltc_facility",
                 replace(v_al.entry("cms", "facility"),
                         aliases=frozenset({"ltc_alias"})))
    for noal, tag in ((False, "ALIASES ON"), (True, "MUTATED (no aliases)")):
        r = resolve_instance(T1_2, ctx, host=alias_host, vocab=v_al,
                             namespace="cms", type_name="ltc_facility", tier="sonnet",
                             _mutate="closure_no_aliases" if noal else None)
        print(f"  I-8 alias {tag}: outcome={r.outcome!r} scanned={r.scanned}")
        if not noal:
            check("5.7 I-8 rule 3-21: aliases are consulted, because `merge_types` "
                  "writes BOTH a successor and an alias and a hand-written alias is "
                  "one the successor scan would miss",
                  r.outcome == "existing", str(r.outcome))
        else:
            check("5.7 I-8 MUTATION (aliases): dropping the alias relation loses the "
                  "row entirely -- a SEPARATE mutation from the backward one, because "
                  "one mutation over 'the closure' cannot falsify either",
                  r.outcome != "existing", str(r.outcome))

    # --- K1: the governed facts, PER HOP --------------------------------
    mid = cms_vocab()
    base = mid.entry("cms", "facility")
    other = replace(base, policy=replace(base.policy, match_at=0.995, why="different"))
    mid.declare("cms", "facility", replace(base, successor="ltc_facility"))
    mid.declare("cms", "ltc_facility", replace(other, successor="ltc_v2"))
    mid.declare("cms", "ltc_v2", replace(base))
    for ig, tag in ((False, "PER HOP"), (True, "MUTATED (ignored)")):
        r = resolve_instance(T1_3, ctx, host=HostTable(list(without)), vocab=mid,
                             namespace="cms", type_name="facility", tier="sonnet",
                             _mutate="governed_facts_ignored" if ig else None)
        print(f"  K1 {tag}: outcome={r.outcome!r}")
        if not ig:
            check("5.7 K1 rule 3-18: the governed facts are checked at EVERY member of "
                  "the closure, so one extra `retire()` to an endpoint declaring what "
                  "the caller declared cannot silence the guard",
                  r.outcome == "unknowable", str(r.outcome))
        else:
            check("5.7 K1 MUTATION: comparing only the two ENDPOINTS decides under an "
                  "intermediate's policy the caller never declared",
                  r.outcome != "unknowable", str(r.outcome))

    # --- K2: one identity under two closure names is ONE candidate -------
    both_names = HostTable([
        InstanceRecord("cms", "entity", "facility", "155049", T1_2, {"state": "IN"}),
        InstanceRecord("cms", "entity", "ltc_facility", "155049", T1_2, {"state": "IN"})])
    for keep, tag in ((False, "COLLAPSED"), (True, "MUTATED (kept apart)")):
        r = resolve_instance(T1_2, ctx, host=both_names, vocab=_retired(),
                             namespace="cms", type_name="facility", tier="sonnet",
                             _mutate="closure_dupes_kept" if keep else None)
        print(f"  K2 {tag}: outcome={r.outcome!r} known={r.known}")
        if not keep:
            check("5.7 K2 rule 2-17: mid-migration, one host row under two names of one "
                  "closure is ONE candidate -- rule 3-19 widened the extent and rule "
                  "2-16's key could not see the dimension it widened along",
                  r.outcome == "existing" and r.known == 1,
                  f"{r.outcome}/{r.known}")
        else:
            check("5.7 K2 MUTATION: kept apart they answer `ambiguous known=2` for ONE "
                  "facility, and the act then writes a third row",
                  r.outcome == "ambiguous" and r.known == 2,
                  f"{r.outcome}/{r.known}")

    # --- K8: the successor NAME must survive the flat form ---------------
    bad = cms_vocab()
    bad.declare("cms", "facility",
                replace(bad.entry("cms", "facility"), successor="ltc#v2"))
    r = resolve_instance(T1_3, ctx, host=HostTable(list(without)), vocab=bad,
                         namespace="cms", type_name="facility", tier="sonnet")
    print(f"  K8: a successor named 'ltc#v2' -> outcome={r.outcome!r}")
    check("5.7 K8 rule 3-22: a successor NAME carrying ':' or '#' reaches the flat form "
          "by the WRITE door, where rule 2-14's guard over RECORDS never sees it -- so "
          "the closure refuses it rather than minting a ref `parse_ref` misreads",
          r.outcome == "unknowable" and "different reference" in r.why_incomplete,
          f"{r.outcome} / {r.why_incomplete[:50]}")

    # --- K10: rule 5-11's carrier is ASSERTED -----------------------------
    r = resolve_instance(T1_3, ctx, host=HostTable(list(without)), vocab=_retired(),
                         namespace="cms", type_name="facility", tier="sonnet")
    print(f"  K10: governed_by={r.governed_by!r}")
    check("5.7 K10 rule 5-11: the resolution NAMES the entry whose governed facts "
          "judged it, and it is the EFFECTIVE one rather than the declared one -- "
          "round 3 found this rule had no check at all and was therefore a decoration",
          r.governed_by == "cms:ltc_facility", repr(r.governed_by))

    # --- B1: the act asks the GATE's relation, not `norm` equality -------
    long_label = T1_3 + " AND REHABILITATION CENTER"
    typo = (long_label, long_label[:-1] + "F")   # one char; similar 0.981 >= 0.97
    for on, tag in ((True, "RELATION"), (False, "MUTATED (key equality)")):
        rules = ACT_RULES if on else (ACT_RULES - {"4-10-relation"})
        led = Ledger()
        a = IngestAct("act-b1", host=HostTable(list(without)), vocab=cms_vocab(),
                      ledger=led, namespace="cms", type_name="facility",
                      enforce=rules)
        got = [a.land(typo[0])[0], a.land(typo[1])[0]]
        print(f"  B1 {tag}: {got}  ledger={len(led.rows)}")
        if on:
            check("5.7 B1 rule 4-10: the act asks the GATE's relation "
                  "(similar >= match_at), not equality of the gate's PRE-PROCESSOR, so "
                  "an ordinary typo is one identity in one act",
                  got == ["proposed", "reused"], str(got))
        else:
            check("5.7 B1 MUTATION: keying on `norm` equality splits one identity the "
                  "gate itself calls `existing` into two proposals",
                  got == ["proposed", "proposed"], str(got))

    # --- B7: the `existing` branch writes rule 4-10's memory --------------
    held = HostTable(list(rows))   # T1_3's CCN is IN this one
    for on, tag in ((True, "MEMOISED"), (False, "MUTATED (existing not memoised)")):
        rules = ACT_RULES if on else (ACT_RULES - {"4-3-eff"})
        a = IngestAct("act-b7", host=held, vocab=cms_vocab(), ledger=Ledger(),
                      namespace="cms", type_name="facility", enforce=rules)
        verdicts = [a.land(T1_3)[0] for _ in range(4)]
        print(f"  B7 {tag}: {verdicts}")
        if on:
            check("5.7 B7 rule 4-13: `existing` answers with an InstanceRef and still "
                  "writes the per-act memory -- on the partner's shape (one note naming "
                  "one thing repeatedly) that is the COMMON case, not the edge",
                  verdicts == ["existing", "reused", "reused", "reused"], str(verdicts))
        else:
            check("5.7 B7 MUTATION: unmemoised, the branch that resolves an identity "
                  "most cheaply-provably is the one rule 4-10's scope never reaches",
                  verdicts == ["existing"] * 4, str(verdicts))

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
