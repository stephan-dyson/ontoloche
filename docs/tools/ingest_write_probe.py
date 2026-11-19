"""Row 7c's design tests, through the SHIPPED ingest act -- 7C-RUN.md 0.4 and 0.5.

Row 7b's ``ingest_build_probe.py`` held the read side's predictions. This holds the
write side's, through ``Registry.ingest_act`` and ``IngestAct.land`` over a host-owned
table on the reference SQLite backend:

* **UC2 CMS**, the five landings 7C-RUN 0.4 tabled, and the review queue they leave;
* **UC3 item 2**, rule 4-11 across four acts: proposed, pending, still pending after
  review, existing after the host writes and ``record_result`` records the ref;
* **the allowlist**, a predicate-proposing ingest family refused at ``propose_type``,
  ``approve``, ``import_types`` and ``ingest_act``, nothing recorded;
* **finding 3 (Q92)**, rule 4-10's recall over a live NYC ``erm2-nwe9`` slice, measured
  and not fixed;
* **finding 6 (ING11)**, the dual-write curve, both arms, over 400 CMS labels;
* **finding 7**, route 9's concurrent clause: two acts whose A4 reads both run before
  either records.

Run::

    py docs/tools/ingest_write_probe.py            # print every result
    py docs/tools/ingest_write_probe.py --assert   # exit 1 on any failed check
    py docs/tools/ingest_write_probe.py --offline  # skip the live NYC fetch

Findings 3, 6 and 7 are MEASUREMENTS: their lines print what was observed, and a check
holds only the prediction 7C-RUN 0.5 made. The CMS file is the one
``ingest_build_probe.py`` reads (``$OO_CMS_CSV`` or the temp folder).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ontoloche.actions import Effect, InputSpec, action_attributes  # noqa: E402
from ontoloche.contract._support import host_instances, seed  # noqa: E402
from ontoloche.edges import InstanceRef, TypeRef  # noqa: E402
from ontoloche.ingest import MATCH_POLICY_KEY  # noqa: E402
from ontoloche.registry import Registry  # noqa: E402
from ontoloche.types import Refusal  # noqa: E402

import ingest_build_probe as build  # noqa: E402
from ingest_build_probe import (  # noqa: E402
    CHECKS,
    CMS_POLICY,
    NYC_POLICY,
    check,
    cms_facilities,
    fresh,
    registry_over,
    rows_of,
)

HOST_WRITE = Effect(op="host_state", why="the host writes the instance row (INGEST.md 4.2)")
NYC_SLICE = {"agency": "NYPD", "complaint_type": "Illegal Fireworks", "incident_zip": "10032"}
NYC_OTHER_ZIP = "11214"


def family(reg, name="propose_facility", *, namespace="cms", mode="auto"):
    return seed(reg, name, kind="action", namespace=namespace,
                definition=f"the {name} action, row 7c's probe",
                attributes=action_attributes(
                    reversibility="reversible", approval_mode=mode,
                    inputs=[InputSpec("instance", "candidate")], effects=[HOST_WRITE]))


def act(reg, act_id, *, namespace="cms", fam="propose_facility", tier="small"):
    out = reg.ingest_act(act_id, family=fam, actor="ai:ingest", tier=tier,
                         namespace=namespace)
    assert not isinstance(out, Refusal), out
    return out


def ledger(reg) -> list:
    return list(reg.invocations(limit=10_000).invocations)


def host_write(adapter, type_name, host_id, label, state=""):
    """Act as the host writing one row into the table it bound (INGEST.md rule 4-2)."""
    target = getattr(adapter, "inner", adapter)
    (table,) = [t for (t,) in target._fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
        (f"host_{type_name}_%",))][-1:]
    target._execute(f"INSERT INTO {table} (host_id, label, state) VALUES (?, ?, ?)",
                    (host_id, label, state))


# ------------------------------------------------------------------------------- UC2
def uc2(facilities) -> None:
    print("\nUC2 CMS -- the five landings 7C-RUN 0.4 tabled")
    ids = sorted(facilities)
    adapter = fresh()
    reg = registry_over(adapter, "facility", "cms", CMS_POLICY, rows=rows_of(facilities))
    family(reg)
    a = act(reg, "uc2")
    burns = a.land("BURNS NURSING HOME, INC.", type_name="facility")
    check("BURNS is existing, cms:entity:facility#015009, no invocation",
          burns.outcome == "existing" and burns.ref.id == "015009" and burns.invocation is None,
          f"{burns.outcome} {burns.ref}")
    miller = a.land("MILLER'S MERRY MANOR", type_name="facility")
    inv = miller.invocation
    check("MILLER'S MERRY MANOR is proposed in review carrying "
          "instance_ambiguous_at_proposal:instance:12",
          miller.outcome == "proposed" and inv is not None
          and inv.declared_policy.get("approval_mode") == "review"
          and "instance_ambiguous_at_proposal:instance:12" in inv.warnings,
          f"{miller.outcome} mode={inv and inv.declared_policy.get('approval_mode')} "
          f"warnings={inv and inv.warnings}")
    provider = a.land("Provider Name", type_name="facility")
    check("'Provider Name' is not_an_instance, no invocation",
          provider.outcome == "not_an_instance" and provider.invocation is None,
          provider.outcome)

    held = fresh()
    held_reg = registry_over(held, "facility", "cms", CMS_POLICY,
                             rows=rows_of(facilities, exclude={"745040"}))
    family(held_reg)
    sarah = act(held_reg, "uc2-held").land("THE SARAH ROBERTS FRENCH HOME",
                                          type_name="facility")
    sinv = sarah.invocation
    check("THE SARAH ROBERTS FRENCH HOME with 745040 held out is proposed in auto, no "
          "ambiguity warning",
          sarah.outcome == "proposed" and sinv is not None
          and sinv.declared_policy.get("approval_mode") == "auto"
          and not any(w.startswith("instance_ambiguous_at_proposal") for w in sinv.warnings),
          f"{sarah.outcome} mode={sinv and sinv.declared_policy.get('approval_mode')}")

    capped = fresh()
    capped_reg = registry_over(capped, "facility", "cms", CMS_POLICY,
                               rows=rows_of(facilities), scan_cap=ids.index("745057"))
    family(capped_reg)
    tusk = act(capped_reg, "uc2-capped").land("Tuskegee Airmen Texas State Veterans Home",
                                              type_name="facility")
    check("Tuskegee under a scan cap one row short is unknowable, no invocation",
          tusk.outcome == "unknowable" and tusk.invocation is None
          and not ledger(capped_reg), tusk.outcome)

    queue = reg.invocations(unreviewed=True).invocations
    check("invocations(unreviewed=True) returns exactly the MILLER'S MERRY MANOR invocation",
          [i.invocation_id for i in queue] == [inv.invocation_id],
          f"{len(queue)} queued")
    print("  [note] the held-out and capped labels need their own host tables, so UC2 "
          "ran as three acts over three hosts, not one act (7C-RUN section 1 records it)")


# --------------------------------------------------------------------------- UC3.2
def uc3_sequence(facilities) -> None:
    print("\nUC3 item 2 -- rule 4-11 across four acts, on the CMS fixture")
    adapter = fresh()
    reg = registry_over(adapter, "facility", "cms", CMS_POLICY,
                        rows=rows_of(facilities, exclude={"745040"}))
    family(reg)
    label = "THE SARAH ROBERTS FRENCH HOME"
    one = act(reg, "act-1").land(label, type_name="facility")
    two = act(reg, "act-2").land(label, type_name="facility")
    holder = one.invocation.invocation_id if one.invocation else None
    reviewed = reg.review_invocation(holder, reviewed_by="user:sd", namespace="cms")
    held_after_review = reg.invocations(unwritten_for=one.candidate)
    three = act(reg, "act-3").land(label, type_name="facility")
    host_write(adapter, "facility", "745040", label, "TX")
    ref = InstanceRef(TypeRef("cms", "entity", "facility"), "745040")
    recorded = reg.record_result(holder, {"instance": ref}, actor="host:cms",
                                 namespace="cms")
    held_after_result = reg.invocations(unwritten_for=one.candidate)
    four = act(reg, "act-4").land(label, type_name="facility")
    seq = [one.outcome, two.outcome, three.outcome, four.outcome]
    print(f"  sequence: {seq}; record_result -> {type(recorded).__name__}")
    check("act 1 proposed, act 2 pending naming act 1, act 3 pending after review, "
          "act 4 existing after the host writes",
          seq == ["proposed", "pending", "pending", "existing"]
          and f"instance_proposal_pending:{holder}" in (two.invocation.warnings
                                                       if two.invocation else ()),
          str(seq))
    # Round 1 (lens 3, M1): act 4 is `existing` from resolve_instance before A4 is read,
    # so the sequence alone never depended on review or record_result. These do.
    check("review is recorded and does NOT release the holder (A4 still holds act 1)",
          not isinstance(reviewed, Refusal) and held_after_review.complete
          and [i.invocation_id for i in held_after_review.invocations] == [holder],
          f"{type(reviewed).__name__}, holders {len(held_after_review.invocations)}")
    check("record_result is recorded and DOES release it (A4 holds nothing, complete)",
          not isinstance(recorded, Refusal) and held_after_result.complete
          and not held_after_result.invocations,
          f"{type(recorded).__name__}, holders {len(held_after_result.invocations)}")


# ------------------------------------------------------------------------- allowlist
def allowlist() -> None:
    print("\nALLOWLIST -- a predicate-proposing ingest family, at four doors")
    adapter = fresh()
    reg = Registry(adapter)
    seed(reg, "facility", namespace="cms", attributes={MATCH_POLICY_KEY: CMS_POLICY})
    bad = [HOST_WRITE, Effect(op="propose_type", namespace="cms", kind="predicate")]
    attrs = action_attributes(reversibility="reversible", approval_mode="auto",
                              inputs=[InputSpec("instance", "candidate")], effects=bad)
    refusals = []
    first = reg.propose_type("mint_a", "mints predicates", [], "user:sd", kind="action",
                             namespace="cms", attributes=attrs)
    refusals.append(("propose_type", getattr(first, "reason", type(first).__name__)))

    ok = reg.propose_type("mint_b", "a clean family, amended past validation", [],
                          "user:sd", kind="action", namespace="cms",
                          attributes=action_attributes(
                              reversibility="reversible", approval_mode="auto",
                              inputs=[InputSpec("instance", "candidate")],
                              effects=[HOST_WRITE]))
    pid = getattr(ok, "id", None)
    if pid is not None:
        rec = adapter.get_proposal(pid)
        adapter.put_proposal(dataclasses.replace(rec, attributes={
            **rec.attributes, "effects": [e.to_dict() for e in bad]}))
        approved = reg.approve(pid, "user:sd")
        refusals.append(("approve", getattr(approved, "reason", type(approved).__name__)))
    else:
        refusals.append(("approve", f"no pending proposal to amend: {ok!r}"[:80]))

    imported = reg.import_types([{"name": "mint_c", "kind": "action", "status": "active",
                                  "definition": "mints predicates, imported",
                                  "attributes": attrs}], namespace="cms", kind="action")[0]
    refusals.append(("import_types", ",".join(w for w in imported.warnings
                                              if w.startswith("import_refused"))))

    family(reg, "propose_facility")
    stored = adapter.get_type("cms", "propose_facility", kind="action")
    adapter.put_type(dataclasses.replace(stored, attributes={
        **stored.attributes, "effects": [e.to_dict() for e in bad]}))
    door4 = reg.ingest_act("a", family="propose_facility", actor="ai:ingest", tier="small",
                           namespace="cms")
    refusals.append(("ingest_act", getattr(door4, "reason", type(door4).__name__)))
    for door, why in refusals:
        print(f"  {door}: {why}")
    # The type store, not only the reasons: no refused family was minted, and the one
    # amended past validation is still pending (round 2, lens 3, m5).
    minted = [n for n in ("mint_a", "mint_b", "mint_c")
              if adapter.get_type("cms", n, kind="action") is not None]
    still_pending = pid is not None and adapter.get_proposal(pid).status == "pending"
    print(f"  minted: {minted}; mint_b still pending: {still_pending}")
    check("no refused family reached the type store, and mint_b is still pending",
          not minted and still_pending, f"minted={minted} pending={still_pending}")
    check("four refusals, nothing recorded",
          refusals[0][1] == "effect_not_permitted" and refusals[1][1] == "effect_not_permitted"
          and refusals[2][1] == "import_refused:effect_not_permitted"
          and refusals[3][1] == "attributes_schema_violation" and not ledger(reg),
          str(refusals))


# ------------------------------------------------------------------- finding 3 (Q92)
def soda_slice() -> list[dict]:
    where = " AND ".join(f"{k}='{v}'" for k, v in sorted(NYC_SLICE.items()))
    url = (f"{build.NYC}?"
           + urllib.parse.urlencode({"$limit": 50000, "$order": "unique_key",
                                     "$select": "unique_key,incident_address",
                                     "$where": where}))
    with urllib.request.urlopen(url, context=build._context(), timeout=600) as fh:
        return [r for r in json.load(fh) if r.get("incident_address")]


def other_zip_rows() -> list[dict]:
    build.NYC_NARROWING = {**build.NYC_NARROWING, "incident_zip": NYC_OTHER_ZIP}
    raw = build.soda({"$limit": 400, "$order": "unique_key",
                      "$select": "unique_key,incident_address,incident_zip"})
    return [{"host_id": r["unique_key"], "label": r["incident_address"].strip().upper(),
             "state": r.get("incident_zip")} for r in raw if r.get("incident_address")]


def finding3() -> None:
    print("\nFINDING 3 (Q92) -- rule 4-10's recall over the live erm2-nwe9 slice")
    rows = soda_slice()
    adapter = fresh()
    reg = registry_over(adapter, "service_request", "nyc", NYC_POLICY,
                        rows=other_zip_rows())
    family(reg, "propose_request", namespace="nyc")
    a = act(reg, "q92", namespace="nyc", fam="propose_request", tier="sonnet")
    tally = Counter(a.land(r["incident_address"].strip().upper(),
                           type_name="service_request").outcome for r in rows)
    share = tally["reused"] / max(1, len(rows))
    print(f"  {len(rows)} rows: {dict(sorted(tally.items()))}, reused {share:.1%} "
          f"(7a: proposed 1044, reused 2298 of 3342)")
    check("Q92: landings split into proposed and reused, reused at least 60% of rows",
          set(tally) <= {"proposed", "reused", "pending", "existing"} and share >= 0.60,
          f"{share:.1%}")


# --------------------------------------------------------------- finding 6 (ING11)
def dual_write_arm(facilities, labels, fraction, *, new_id, per_label=None) -> Counter:
    """``facility`` retired with successor ``ltc_facility``; every row stays in
    ``facility`` and ``fraction`` of them are also written to ``ltc_facility``,
    under the same id or a new one."""
    ids = sorted(facilities)
    dual = set(ids[: int(len(ids) * fraction)])
    adapter = fresh()
    host_instances(adapter, rows_of(facilities), type_name="facility", namespace="cms")
    succ = [{"host_id": ("N" + ccn) if new_id else ccn, "label": facilities[ccn][0],
             "state": facilities[ccn][1]} for ccn in ids if ccn in dual]
    host_instances(adapter, succ, type_name="ltc_facility", namespace="cms")
    reg = Registry(adapter)
    seed(reg, "facility", namespace="cms", attributes={MATCH_POLICY_KEY: CMS_POLICY})
    seed(reg, "ltc_facility", namespace="cms", attributes={MATCH_POLICY_KEY: CMS_POLICY})
    reg.retire("facility", "renamed", retired_by="user:sd", namespace="cms",
               successor="ltc_facility")
    family(reg)
    out = Counter()
    for ccn, label in labels:
        landing = act(reg, f"ing11-{ccn}").land(label, type_name="facility")
        mode = (landing.invocation.declared_policy.get("approval_mode")
                if landing.invocation else None)
        out[(landing.outcome, mode, ccn in dual)] += 1
        if per_label is not None:
            per_label[ccn] = (landing.outcome, mode)
    return out


def finding6(facilities) -> None:
    print("\nFINDING 6 (ING11) -- the dual-write curve, 400 CMS labels, both arms")
    ids = sorted(facilities)
    step = max(1, len(ids) // 400)
    labels = [(ccn, facilities[ccn][0]) for ccn in ids[::step][:400]]
    # Per label, (outcome, approval mode). Round 1 (lens 3): the earlier version
    # flattened a Counter through a dict comprehension, so colliding keys overwrote
    # instead of summing, and it compared aggregates, which can hide per-label swaps.
    base: dict[str, tuple] = {}
    dual_write_arm(facilities, labels, 0.0, new_id=False, per_label=base)
    print(f"  0% dual-written: {dict(Counter(base.values()))}")
    for frac in (0.5, 1.0):
        same: dict[str, tuple] = {}
        new: dict[str, tuple] = {}
        dual_write_arm(facilities, labels, frac, new_id=False, per_label=same)
        dual_write_arm(facilities, labels, frac, new_id=True, per_label=new)
        dual_ids = set(ids[: int(len(ids) * frac)]) & set(base)
        was_existing = {c for c in dual_ids if base[c][0] == "existing"}
        changed_same = [c for c in base if same[c] != base[c]]
        print(f"  {frac:.0%} same id: {dict(Counter(same.values()))}  "
              f"(labels changed vs 0%: {len(changed_same)})")
        print(f"  {frac:.0%} new id:  {dict(Counter(new.values()))}  "
              f"(dual-written: {len(dual_ids)}, of them existing at 0%: {len(was_existing)})")
        check(f"ING11 same-id arm at {frac:.0%} changes 0 outcomes, label by label "
              "(rule 2-17 collapses it)", not changed_same, f"{len(changed_same)} changed")
        flipped = [c for c in was_existing if new[c][1] == "review"
                   and new[c][0] in ("proposed", "pending")]
        untouched = [c for c in set(base) - dual_ids if new[c] != base[c]]
        check(f"ING11 new-id arm at {frac:.0%}: every dual-written label that was existing "
              "becomes a review-mode proposal, and no other label changes",
              len(flipped) == len(was_existing) and not untouched,
              f"{len(flipped)} of {len(was_existing)} flipped; {len(untouched)} "
              "non-dual labels changed")


# ------------------------------------------------------------------------ finding 7
def finding7(facilities) -> None:
    print("\nFINDING 7 -- route 9's concurrent clause: both A4 reads before either records")
    adapter = fresh()
    reg = registry_over(adapter, "facility", "cms", CMS_POLICY,
                        rows=rows_of(facilities, exclude={"745040"}))
    family(reg)
    label = "THE SARAH ROBERTS FRENCH HOME"
    first, second = act(reg, "worker-a"), act(reg, "worker-b")
    original = reg.invocations
    state = {"b": None, "armed": True}

    def interleaved(*args, **kwargs):
        answer = original(*args, **kwargs)      # worker A's read: no holder yet
        if state["armed"] and kwargs.get("unwritten_for") is not None:
            state["armed"] = False
            state["b"] = second.land(label, type_name="facility")  # B reads and records
        return answer                           # A records over its stale read

    reg.invocations = interleaved
    try:
        a = first.land(label, type_name="facility")
    finally:
        reg.invocations = original
    b = state["b"]
    warned = [x for x in (a, b) if x and x.invocation and any(
        w.startswith("instance_proposal_pending") for w in x.invocation.warnings)]
    print(f"  worker A: {a.outcome}; worker B: {b.outcome if b else None}; "
          f"pending warnings: {len(warned)}")
    check("finding 7: the concurrent case is OPEN -- two proposed landings for one "
          "identity, no warning on either",
          a.outcome == "proposed" and b is not None and b.outcome == "proposed"
          and not warned, f"{a.outcome}/{b and b.outcome}")
    third = act(reg, "worker-c").land(label, type_name="facility")
    check("and the sequential case stays closed: a third act after both is pending",
          third.outcome == "pending", third.outcome)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assert", dest="strict", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    facilities = cms_facilities()
    uc2(facilities)
    uc3_sequence(facilities)
    allowlist()
    finding6(facilities)
    finding7(facilities)
    if not args.offline:
        finding3()
    failed = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    return 1 if (args.strict and failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
