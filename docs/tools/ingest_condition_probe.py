# -*- coding: utf-8 -*-
"""Design test 3 for `docs/specs/INGEST.md` v0 -- **the two-tenant loop (R59 / R60)**,
over two states of the CMS file held in ONE store.

**What R59 and R60 require.** The protocol stays tenant-blind and tenancy is the host's
predicate (R59); Phase 3 makes that predicate *expressible* as one ``Condition`` -- a
closed operator vocabulary over one record's attribute values, **three-valued**,
declared on the entry and evaluated by the registry (R60).

**Pass** = no cross-tenant candidate ever reaches the resolution's answer, and a
predicate over an attribute the census cannot see evaluates **unknowable**, not false.

**AMENDED BY ROUND 1.** Three findings landed here. **P3:** the predicate was a CALL
PARAMETER and this probe only ever tested that path -- omitting the keyword made five of
five shared names resolve differently and handed one tenant another's refs, which is
R59's own reversal condition reached by leaving out an argument. It is now read from the
**entry**, through the shared kit, and there is no parameter to omit. **M7:** primitive
22 had no tenancy surface at all, so a caller in one tenant could confirm another's row
by key; 3.7 exercises rule 2-15. **M5:** ``Condition`` cannot compare two attributes of
one record and the nearest expressible form is accepted at declaration and false for
every record; 3.8 constructs it on UC2's own pre-registered pathology.

**The fixture is the sharpest the CMS file offers.** 84 provider names are shared across
more than one state; California and Colorado share five of them, the largest pair.

Run: ``py docs/tools/ingest_condition_probe.py [--csv <NH_HealthCitations_Aug2026.csv>]``
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingest_probe_kit import (  # noqa: E402
    COMBINATORS, Condition, DeclarationRefused, EntryDeclaration, HostTable,
    InstanceContext, InstanceRecord, MatchPolicy, Refusal, VALUE_OPS, Vocabulary,
    evaluate, get_instance_checked, resolve_instance,
)
from ingest_seam_probe import CHECKS, CMS_POLICY, _resolve_csv, check  # noqa: E402

csv.field_size_limit(10_000_000)

TENANT_A = ("ca-host", "CA")
TENANT_B = ("co-host", "CO")
UNSEEABLE = "ownership_type"
READABLE = frozenset({"tenant", "state", "city", "zip"})


def load_two_states(path: Path) -> tuple[list[InstanceRecord], list[str]]:
    keep = {TENANT_A[1], TENANT_B[1]}
    by_ccn: dict[str, InstanceRecord] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row["State"] not in keep:
                continue
            ccn = row["CMS Certification Number (CCN)"]
            if ccn in by_ccn:
                continue
            tenant = TENANT_A[0] if row["State"] == TENANT_A[1] else TENANT_B[0]
            by_ccn[ccn] = InstanceRecord(
                namespace="cms", kind="entity", type_name="facility", instance_id=ccn,
                label=row["Provider Name"],
                attributes={"tenant": tenant, "state": row["State"],
                            "city": row["City/Town"], "zip": row["ZIP Code"]})
    names: dict[str, set[str]] = {}
    for rec in by_ccn.values():
        names.setdefault(rec.label, set()).add(rec.attributes["tenant"])
    return list(by_ccn.values()), sorted(n for n, t in names.items() if len(t) > 1)


def tenant_vocab(tenant: str, *, readable: frozenset[str] = READABLE) -> Vocabulary:
    """The ENTRY declares the predicate. Rule 6-14: it is never a call parameter."""
    v = Vocabulary()
    v.declare("cms", "facility", EntryDeclaration(
        policy=CMS_POLICY, readable=readable,
        predicate=Condition(op="eq", attribute="tenant", value=tenant,
                            why="rows this host is the system of record for (R59)")))
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.environ.get("CMS_CITATIONS_CSV"))
    args = ap.parse_args()

    print("DESIGN TEST 3 -- the two-tenant loop (R59 / R60), over CMS CA + CO")
    path = _resolve_csv(args.csv)
    rows, shared = load_two_states(path)
    a_rows = [r for r in rows if r.attributes["tenant"] == TENANT_A[0]]
    b_rows = [r for r in rows if r.attributes["tenant"] == TENANT_B[0]]
    print(f"  one store: {len(rows)} facilities -- {len(a_rows)} {TENANT_A[0]}, "
          f"{len(b_rows)} {TENANT_B[0]}")
    print(f"  provider names BOTH tenants answer to: {len(shared)}")
    for n in shared:
        print(f"     {n!r}")
    check("the two-tenant fixture has real cross-tenant collisions to leak",
          len(shared) >= 5, f"{len(shared)} shared names")

    host = HostTable(rows)
    vocab_a, vocab_b = tenant_vocab(TENANT_A[0]), tenant_vocab(TENANT_B[0])
    by_ccn = {r.instance_id: r.attributes["tenant"] for r in rows}

    # --- 3.1 the protocol is tenant-blind -----------------------------------
    print("\n3.1 the protocol is tenant-blind")
    import inspect
    sig = str(inspect.signature(HostTable.find_instance_candidates))
    call_sig = str(inspect.signature(resolve_instance))
    print(f"  primitive 23: find_instance_candidates{sig}")
    check("the candidate primitive takes NO tenant parameter -- R24 / R59 intact",
          "tenant" not in sig, sig)
    check("and rule 6-14 / round 1's P3: `resolve_instance` takes no `predicate` "
          "parameter either, so there is no keyword to omit",
          "predicate" not in call_sig, call_sig[:90])

    # --- 3.2 no cross-tenant candidate reaches an answer --------------------
    print("\n3.2 the loop under each host's DECLARED predicate, on the shared names")
    leaks: list[str] = []
    for name in shared:
        ra = resolve_instance(name, InstanceContext(act_id="a"), host=host,
                              vocab=vocab_a, namespace="cms", type_name="facility",
                              tier="sonnet")
        rb = resolve_instance(name, InstanceContext(act_id="b"), host=host,
                              vocab=vocab_b, namespace="cms", type_name="facility",
                              tier="sonnet")
        for want, res in ((TENANT_A[0], ra), (TENANT_B[0], rb)):
            refs = [c.ref_key for c in res.candidates] + ([res.ref] if res.ref else [])
            for ref in refs:
                if by_ccn[ref.split("#", 1)[1]] != want:
                    leaks.append(f"{name!r}: {want} saw {ref}")
        print(f"  {name!r}")
        print(f"     {TENANT_A[0]}: outcome={ra.outcome!r} ref={ra.ref!r} "
              f"scanned={ra.scanned}")
        print(f"     {TENANT_B[0]}: outcome={rb.outcome!r} ref={rb.ref!r} "
              f"scanned={rb.scanned}")
    check("NO cross-tenant candidate reached either answer", not leaks,
          "; ".join(leaks[:3]))
    check("each host saw the WHOLE store and the PREDICATE did the excluding",
          ra.scanned == rb.scanned == len(rows), f"scanned={ra.scanned} of {len(rows)}")

    # --- 3.3 an attribute the census cannot see -----------------------------
    print(f"\n3.3 a predicate over {UNSEEABLE!r} -- an attribute no column carries")
    blind = Vocabulary()
    blind.declare("cms", "facility", EntryDeclaration(
        policy=CMS_POLICY, readable=READABLE,
        predicate=Condition(op="eq", attribute=UNSEEABLE, value="government",
                            why="this host is the system of record only for "
                                "government-owned facilities")))
    probe_name = shared[0]
    r_blind = resolve_instance(probe_name, InstanceContext(act_id="blind"), host=host,
                               vocab=blind, namespace="cms", type_name="facility",
                               tier="sonnet")
    print(f"  resolve {probe_name!r} under it")
    print(f"     -> outcome={r_blind.outcome!r} ref={r_blind.ref!r}")
    print(f"        why={r_blind.why_incomplete!r}")
    check("an unseeable attribute is UNKNOWABLE, not false",
          r_blind.outcome == "unknowable", r_blind.outcome)
    check("and it is not read as TRUE either -- nothing was answered",
          r_blind.ref is None)

    print("\n3.3b what the two-valued readings would have done, constructed")
    as_true = [r for r in rows if r.label == probe_name]
    tenants_hit = sorted({r.attributes["tenant"] for r in as_true})
    print(f"  unknowable-as-FALSE: all {len(rows)} candidates excluded, 0 survive -> "
          f"the loop proposes a NEW facility for one that exists (mechanism C)")
    print(f"  unknowable-as-TRUE : {len(as_true)} survive across tenants {tenants_hit} "
          f"-> cross-tenant leak, R59's own reversal condition")
    check("both two-valued readings are real failures, so the third value is forced",
          len(tenants_hit) == 2, str(tenants_hit))

    # --- 3.4 readable-but-null is a different fact --------------------------
    print("\n3.4 readable-but-NULL is not the same fact as unreadable")
    nulled = InstanceRecord("cms", "entity", "facility", "x", "y",
                            {**rows[0].attributes, "zip": None})
    r_null = evaluate(Condition(op="eq", attribute="zip", value="90210",
                                why="a zip test"), nulled, READABLE)
    r_isnull = evaluate(Condition(op="is_null", attribute="zip",
                                  why="rows with no postcode"), nulled, READABLE)
    print(f"  eq over a NULL readable attribute -> holds={r_null.holds}")
    print(f"  is_null over the same             -> holds={r_isnull.holds}")
    check("eq against null is UNKNOWABLE -- SQL's own rule, so a SQL host cannot "
          "disagree with the registry", r_null.holds is None)
    check("is_null answers it as a FACT, which is why the two operators exist",
          r_isnull.holds is True)

    # --- 3.5 the closed vocabulary refuses at DECLARATION -------------------
    print("\n3.5 the vocabulary is closed, and it refuses at the declaration door")
    refusals = []
    for bad, label in (
        (dict(op="matches", attribute="label", value=".*HOME", why="regex"),
         "a thirteenth term"),
        (dict(op="eq", attribute="tenant", value=None, why="null operand"),
         "eq against a null operand"),
        (dict(op="eq", attribute="tenant", value="x", why="   "), "an empty `why`"),
        (dict(op="all_of", why="no terms"), "a combinator with no terms"),
        (dict(op="in", attribute="tenant", value="ca-host", why="scalar"),
         "`in` against a scalar"),
        (dict(op="all_of", attribute="tenant", value="x", why="mixed",
              terms=(Condition(op="eq", attribute="tenant", value="y", why="t"),)),
         "a combinator carrying an attribute"),
        (dict(op="eq", attribute="tenant", value="x", why="mixed",
              terms=(Condition(op="eq", attribute="tenant", value="y", why="t"),)),
         "an operator carrying terms"),
    ):
        try:
            Condition(**bad)
            refusals.append((label, False, ""))
        except DeclarationRefused as exc:
            refusals.append((label, True, str(exc)))
    for label, refused, why in refusals:
        print(f"  {'REFUSED ' if refused else 'ACCEPTED'} {label} -- {why}")
    check(f"all {len(refusals)} malformed declarations are refused at declaration",
          all(r[1] for r in refusals), str([r[0] for r in refusals if not r[1]]))
    check("the vocabulary is exactly twelve terms",
          len(VALUE_OPS) + len(COMBINATORS) == 12,
          f"{len(VALUE_OPS)}+{len(COMBINATORS)}")

    # --- 3.6 Kleene ---------------------------------------------------------
    print("\n3.6 three-valued composition")
    t = Condition(op="eq", attribute="tenant", value=TENANT_A[0], why="t")
    f = Condition(op="eq", attribute="tenant", value="nobody", why="f")
    u = Condition(op="eq", attribute=UNSEEABLE, value="x", why="u")
    rec = a_rows[0]
    cases = {
        "all_of(T,U)": evaluate(Condition(op="all_of", terms=(t, u), why="c"), rec,
                                READABLE).holds,
        "all_of(F,U)": evaluate(Condition(op="all_of", terms=(f, u), why="c"), rec,
                                READABLE).holds,
        "any_of(T,U)": evaluate(Condition(op="any_of", terms=(t, u), why="c"), rec,
                                READABLE).holds,
        "any_of(F,U)": evaluate(Condition(op="any_of", terms=(f, u), why="c"), rec,
                                READABLE).holds,
    }
    for k, v in cases.items():
        print(f"  {k} = {v}")
    check("all_of short-circuits on FALSE and only then on unknown; any_of on TRUE -- "
          "Kleene, so a partly-unreadable predicate still decides what it can",
          cases == {"all_of(T,U)": None, "all_of(F,U)": False,
                    "any_of(T,U)": True, "any_of(F,U)": None}, str(cases))

    # --- 3.7 primitive 22 through the predicate (round 1, M7) ---------------
    print("\n3.7 rule 2-15: primitive 22 THROUGH the entry's predicate")
    co_ccn = next(r.instance_id for r in rows
                  if r.label == probe_name and r.attributes["tenant"] == TENANT_B[0])
    ca_ccn = next(r.instance_id for r in rows
                  if r.label == probe_name and r.attributes["tenant"] == TENANT_A[0])
    own = get_instance_checked(host, vocab_a, namespace="cms", type_name="facility",
                               instance_id=ca_ccn)
    other = get_instance_checked(host, vocab_a, namespace="cms", type_name="facility",
                                 instance_id=co_ccn)
    undecidable = get_instance_checked(host, blind, namespace="cms",
                                       type_name="facility", instance_id=ca_ccn)
    raw = host.get_instance("cms", "entity", "facility", co_ccn)
    print(f"  {TENANT_A[0]} confirms its OWN row {ca_ccn}  -> "
          f"{own.label if hasattr(own, 'label') else own!r}")
    print(f"  {TENANT_A[0]} confirms {TENANT_B[0]}'s {co_ccn} -> {other!r}")
    print(f"  under an UNDECIDABLE predicate            -> {undecidable!r}")
    print(f"  the RAW primitive (no registry)           -> "
          f"{raw.attributes['tenant']!r} -- which is what M7 measured")
    check("3.7 a record the predicate FAILS is absent through the registry",
          other is None and raw is not None)
    check("3.7 a record the predicate cannot DECIDE is a refusal, never a silent pass",
          isinstance(undecidable, Refusal), str(undecidable)[:60])
    check("3.7 and the tenant's own row still comes back",
          getattr(own, "instance_id", None) == ca_ccn)

    # --- 3.8 ING10: the attribute-to-attribute gap (round 1, M5) ------------
    print("\n3.8 ING10 -- the gate `Condition` cannot express, constructed")
    print("  UC2's own pre-registered pathology: a Correction Date BEFORE the Survey "
          "Date")
    gate = Condition(op="gte", attribute="correction_date", value="survey_date",
                     why="a correction cannot precede the survey it corrects")
    cases2 = [("2024-03-01", "2024-05-01", "INVERTED - should FAIL"),
              ("2024-06-01", "2024-05-01", "VALID    - should HOLD"),
              ("2019-01-02", "2019-01-01", "VALID    - should HOLD")]
    readable2 = frozenset({"correction_date", "survey_date"})
    verdicts = []
    for corr, surv, note in cases2:
        rec2 = InstanceRecord("cms", "entity", "citation", "c", "c",
                              {"correction_date": corr, "survey_date": surv})
        v = evaluate(gate, rec2, readable2)
        verdicts.append(v.holds)
        print(f"  correction={corr} survey={surv}  [{note}]  -> holds={v.holds}")
    check("3.8 the nearest expressible form is ACCEPTED at declaration and FALSE for "
          "every record -- design test 3's own mechanism C, through a predicate that "
          "passes rules 6-1..6-13. Recorded as ING10 and routed to Q90",
          verdicts == [False, False, False], str(verdicts))

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
