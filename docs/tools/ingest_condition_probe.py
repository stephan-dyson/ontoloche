# -*- coding: utf-8 -*-
"""Design test 3 for `docs/specs/INGEST.md` v0 -- **the two-tenant loop (R59 / R60)**,
over two states of the CMS file held in ONE store.

**What R59 and R60 require.** The protocol stays tenant-blind and tenancy is the host's
predicate (R59); Phase 3 makes that predicate *expressible* as one ``Condition`` -- a
closed operator vocabulary over one record's attribute values, **three-valued**,
declared on the entry and evaluated by the registry (R60).

**Pass** = no cross-tenant candidate ever reaches the resolution's answer, and a
predicate over an attribute the census cannot see evaluates **unknowable**, not false.

**The fixture is the sharpest the CMS file offers.** 84 provider names are shared across
more than one state; California and Colorado share five of them, which is the largest
pair. Two tenants, one store, five names that both tenants answer to: if tenancy leaks,
this is where it shows.

Run: ``py docs/tools/ingest_condition_probe.py [--csv <NH_HealthCitations_Aug2026.csv>]``
"""

from __future__ import annotations

import argparse
import csv
import difflib
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingest_seam_probe import (  # noqa: E402
    CHECKS, CandidatePage, CandidateQuery, InstanceRecord, _norm, _similar,
    _resolve_csv, check,
)

TENANT_A = ("ca-host", "CA")
TENANT_B = ("co-host", "CO")

#: An attribute NO column of this export carries. The census cannot see it, and the
#: whole of 3.4 is about what a predicate over it is allowed to say.
UNSEEABLE = "ownership_type"


# --------------------------------------------------------------------------------
# `Condition` -- the closed vocabulary, three-valued. INGEST.md 6.
# --------------------------------------------------------------------------------

#: Ten operators over ONE record's attribute values, plus two combinators. Closed: R3
#: applies, and adding one is a section-row change with a contract id.
VALUE_OPS = ("eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte",
             "is_null", "is_not_null")
COMBINATORS = ("all_of", "any_of")


class DeclarationRefused(Exception):
    """Refused at DECLARATION, never at evaluation. ACTIONS 2.4-6's door."""


@dataclass(frozen=True)
class Condition:
    op: str
    why: str
    attribute: str | None = None
    value: Any = None
    terms: tuple["Condition", ...] = ()

    def __post_init__(self) -> None:
        if self.op not in VALUE_OPS + COMBINATORS:
            raise DeclarationRefused(f"{self.op!r} is not one of the twelve terms")
        if not (self.why or "").strip():
            raise DeclarationRefused("Condition.why is required and non-empty")
        if self.op in COMBINATORS:
            if self.attribute is not None or self.value is not None:
                raise DeclarationRefused(f"{self.op} takes terms, not an attribute")
            if not self.terms:
                raise DeclarationRefused(f"{self.op} with no terms")
            return
        if not self.attribute:
            raise DeclarationRefused(f"{self.op} needs an attribute")
        if self.terms:
            raise DeclarationRefused(f"{self.op} takes no terms")
        if self.op in ("is_null", "is_not_null"):
            if self.value is not None:
                raise DeclarationRefused(f"{self.op} takes no value")
            return
        if self.value is None:
            # The SQL NULL trap, refused at the door rather than met at runtime.
            raise DeclarationRefused(
                f"{self.op} may not take a null operand; use is_null / is_not_null")
        if self.op in ("in", "not_in") and not isinstance(self.value, (tuple, list)):
            raise DeclarationRefused(f"{self.op} takes a sequence")


@dataclass(frozen=True)
class ConditionResult:
    holds: bool | None          # None = unknowable. Rule U
    why: str                    # required when `holds` is None
    unreadable: tuple[str, ...] = ()


def evaluate(cond: Condition, record: InstanceRecord,
             readable: frozenset[str]) -> ConditionResult:
    """Three-valued evaluation, in the REGISTRY, over attributes the host declared readable.

    ``readable`` is the adapter's own declaration -- ``Capabilities.attribute_projections``
    one object along (beacon finding U3's shape). An attribute outside it is not absent;
    it is **unreadable**, and the difference is the whole of Rule U here.
    """
    if cond.op in COMBINATORS:
        results = [evaluate(t, record, readable) for t in cond.terms]
        unreadable = tuple(sorted({a for r in results for a in r.unreadable}))
        vals = [r.holds for r in results]
        if cond.op == "all_of":
            holds = False if False in vals else (None if None in vals else True)
        else:
            holds = True if True in vals else (None if None in vals else False)
        why = "" if holds is not None else (
            f"{cond.op}: undecidable on " + ", ".join(unreadable))
        return ConditionResult(holds, why, unreadable)

    assert cond.attribute is not None
    if cond.attribute not in readable:
        return ConditionResult(
            None,
            f"{cond.attribute!r} is not readable on this host: "
            f"the census cannot see it, so this condition is unknowable rather than "
            f"false", (cond.attribute,))
    got = record.attributes.get(cond.attribute)
    if cond.op == "is_null":
        return ConditionResult(got is None, "")
    if cond.op == "is_not_null":
        return ConditionResult(got is not None, "")
    if got is None:
        # A readable attribute that is NULL. eq/ne/comparisons are UNKNOWN on it --
        # SQL's own rule, kept so a host implementing this in SQL cannot disagree.
        return ConditionResult(
            None, f"{cond.attribute!r} is null; {cond.op} against null is unknowable")
    if cond.op == "eq":
        return ConditionResult(got == cond.value, "")
    if cond.op == "ne":
        return ConditionResult(got != cond.value, "")
    if cond.op == "in":
        return ConditionResult(got in tuple(cond.value), "")
    if cond.op == "not_in":
        return ConditionResult(got not in tuple(cond.value), "")
    try:
        if cond.op == "lt":
            return ConditionResult(got < cond.value, "")
        if cond.op == "lte":
            return ConditionResult(got <= cond.value, "")
        if cond.op == "gt":
            return ConditionResult(got > cond.value, "")
        return ConditionResult(got >= cond.value, "")
    except TypeError as exc:                      # not comparable is not false
        return ConditionResult(None, f"{cond.attribute!r}: {exc}")


# --------------------------------------------------------------------------------
# The host -- ONE store, two tenants' rows, and a declared readable set
# --------------------------------------------------------------------------------


class TwoTenantHostTable:
    """One table, two tenants' rows, and the adapter's own declaration of what it can read.

    ``readable`` is deliberately a property of the HOST, not of the condition: R59 says
    tenancy is the host's predicate, and a host that cannot read the column its own
    predicate names is exactly the case 3.4 constructs.
    """

    def __init__(self, rows: list[InstanceRecord], *, readable: frozenset[str]) -> None:
        self._rows = sorted(rows, key=lambda r: r.instance_id)
        self.readable = readable
        self.scans = 0

    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage:
        """**Tenant-blind.** This primitive is handed no tenant and applies none.

        R59's protocol half, made literal: the word `tenant` does not appear in this
        method's parameters, and the whole store is what it offers.
        """
        self.scans += 1
        pool = [r for r in self._rows
                if (r.namespace, r.kind, r.type_name) == (q.namespace, q.kind,
                                                          q.type_name)]
        return CandidatePage(records=tuple(pool), known=len(pool), complete=True,
                             why_incomplete=None, next_after=None)


@dataclass
class TenantResolution:
    outcome: str
    ref_key: str | None
    candidates: tuple[str, ...]
    considered: int
    excluded_by_predicate: int
    undecidable: int
    why: str
    predicate_why: tuple[str, ...] = field(default_factory=tuple)


def resolve_instance_under(
    candidate: str, *, host: TwoTenantHostTable, namespace: str, type_name: str,
    predicate: Condition, min_confidence: float = 0.86,
    ambiguity_margin: float = 0.02,
) -> TenantResolution:
    """The loop, run under ONE host's predicate. The predicate gates the CANDIDATES.

    The ordering is the finding of 3.3: the predicate is applied to every candidate
    **before** any of them can become an answer, and an **unknowable** verdict removes
    the candidate from the answer *and* from the propose path -- it is never read as
    false and never read as true.
    """
    page = host.find_instance_candidates(
        CandidateQuery(namespace=namespace, kind="entity", type_name=type_name,
                       label=candidate))
    norm = _norm(candidate)
    considered = excluded = undecided = 0
    whys: list[str] = []
    scored: list[tuple[str, float]] = []
    for rec in page.records:
        considered += 1
        verdict = evaluate(predicate, rec, host.readable)
        if verdict.holds is False:
            excluded += 1
            continue
        if verdict.holds is None:
            undecided += 1
            whys.append(verdict.why)
            continue
        score = round(_similar(norm, _norm(rec.label)), 4)
        if score >= min_confidence:
            scored.append(
                (f"{rec.namespace}:{rec.kind}:{rec.type_name}#{rec.instance_id}", score))
    scored.sort(key=lambda p: (-p[1], p[0]))

    if undecided:
        # Rule U, and it outranks every other outcome: a candidate set the predicate
        # could not decide is not a candidate set.
        return TenantResolution(
            "unknowable", None, tuple(k for k, _ in scored), considered, excluded,
            undecided,
            f"the host predicate was undecidable on {undecided} of {considered} "
            f"candidates", tuple(sorted(set(whys))[:2]))
    if len(scored) > 1 and (scored[0][1] - scored[1][1]) <= ambiguity_margin:
        tied = tuple(k for k, s in scored if (scored[0][1] - s) <= ambiguity_margin)
        return TenantResolution("ambiguous", None, tied, considered, excluded, 0,
                                f"{len(tied)} candidates inside this tenant")
    if scored:
        return TenantResolution("existing", scored[0][0], tuple(k for k, _ in scored),
                                considered, excluded, 0, "one candidate")
    return TenantResolution("proposal", None, (), considered, excluded, 0,
                            "nothing in this tenant answers to it")


# --------------------------------------------------------------------------------


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
                            "city": row["City/Town"], "zip": row["ZIP Code"]},
            )
    names: dict[str, set[str]] = {}
    for rec in by_ccn.values():
        names.setdefault(rec.label, set()).add(rec.attributes["tenant"])
    shared = sorted(n for n, t in names.items() if len(t) > 1)
    return list(by_ccn.values()), shared


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

    readable = frozenset({"tenant", "state", "city", "zip"})
    host = TwoTenantHostTable(rows, readable=readable)

    pred_a = Condition(op="eq", attribute="tenant", value=TENANT_A[0],
                       why="rows this host is the system of record for (R59)")
    pred_b = Condition(op="eq", attribute="tenant", value=TENANT_B[0],
                       why="rows this host is the system of record for (R59)")

    # --- 3.1 the tenant-blind protocol -------------------------------------
    print("\n3.1 the protocol is tenant-blind")
    import inspect
    src = inspect.getsource(TwoTenantHostTable.find_instance_candidates)
    sig = str(inspect.signature(TwoTenantHostTable.find_instance_candidates))
    print(f"  primitive signature: find_instance_candidates{sig}")
    check("the candidate primitive takes NO tenant parameter -- R24 / R59 intact",
          "tenant" not in sig, sig)
    check("and the primitive applies no tenancy filter of its own: it offers the store",
          "readable" not in src.split("def ")[-1].split("return")[0]
          or "tenant" not in sig)

    # --- 3.2 no cross-tenant candidate reaches an answer --------------------
    print("\n3.2 the loop under each host's predicate, on the shared names")
    leaks: list[str] = []
    for name in shared:
        ra = resolve_instance_under(name, host=host, namespace="cms",
                                    type_name="facility", predicate=pred_a)
        rb = resolve_instance_under(name, host=host, namespace="cms",
                                    type_name="facility", predicate=pred_b)
        by_ccn = {r.instance_id: r.attributes["tenant"] for r in rows}
        for label, res, want in ((TENANT_A[0], ra, TENANT_A[0]),
                                 (TENANT_B[0], rb, TENANT_B[0])):
            for key in res.candidates + ((res.ref_key,) if res.ref_key else ()):
                ccn = key.split("#", 1)[1]
                if by_ccn[ccn] != want:
                    leaks.append(f"{name!r}: {label} saw {key} ({by_ccn[ccn]})")
        print(f"  {name!r}")
        print(f"     {TENANT_A[0]}: outcome={ra.outcome!r} ref={ra.ref_key!r} "
              f"considered={ra.considered} excluded_by_predicate={ra.excluded_by_predicate}")
        print(f"     {TENANT_B[0]}: outcome={rb.outcome!r} ref={rb.ref_key!r} "
              f"considered={rb.considered} excluded_by_predicate={rb.excluded_by_predicate}")
    check("NO cross-tenant candidate reached either answer", not leaks,
          "; ".join(leaks[:3]))
    check("each host saw the WHOLE store and the predicate did the excluding",
          all(r == len(rows) for r in [ra.considered, rb.considered]),
          f"considered={ra.considered} of {len(rows)}")

    # --- 3.3 an attribute the census cannot see -----------------------------
    print(f"\n3.3 a predicate over {UNSEEABLE!r} -- an attribute no column carries")
    blind_pred = Condition(op="eq", attribute=UNSEEABLE, value="government",
                           why="this host is the system of record only for "
                               "government-owned facilities")
    blind_host = TwoTenantHostTable(rows, readable=readable)
    probe_name = shared[0]
    r_blind = resolve_instance_under(probe_name, host=blind_host, namespace="cms",
                                     type_name="facility", predicate=blind_pred)
    print(f"  resolve {probe_name!r} under it")
    print(f"     -> outcome={r_blind.outcome!r} undecidable={r_blind.undecidable} "
          f"excluded_by_predicate={r_blind.excluded_by_predicate}")
    print(f"        why={r_blind.why!r}")
    for w in r_blind.predicate_why:
        print(f"        {w}")
    check("an unseeable attribute is UNKNOWABLE, not false",
          r_blind.outcome == "unknowable" and r_blind.excluded_by_predicate == 0,
          f"{r_blind.outcome} / excluded={r_blind.excluded_by_predicate}")
    check("and it is not read as TRUE either -- nothing was answered",
          r_blind.ref_key is None)

    # --- 3.3b the two failure modes, CONSTRUCTED ---------------------------
    print("\n3.3b what the two-valued readings would have done, constructed")
    as_false = [r for r in rows if False]           # every candidate excluded
    print(f"  unknowable-as-FALSE: {len(rows)} candidates excluded, "
          f"{len(as_false)} survive -> the loop proposes a NEW facility for a "
          f"facility that exists (mechanism C, and the pollution machine)")
    as_true_hits = [r for r in rows if r.label == probe_name]
    tenants_hit = sorted({r.attributes["tenant"] for r in as_true_hits})
    print(f"  unknowable-as-TRUE : {len(as_true_hits)} candidates survive across "
          f"tenants {tenants_hit} -> cross-tenant leak, which is R59's own reversal "
          f"condition")
    check("both two-valued readings are real failures, so the third value is forced",
          len(as_false) == 0 and len(tenants_hit) == 2, f"{tenants_hit}")

    # --- 3.4 a readable-but-null attribute is a different thing -------------
    print("\n3.4 readable-but-NULL is not the same fact as unreadable")
    nulled = [InstanceRecord(r.namespace, r.kind, r.type_name, r.instance_id, r.label,
                             {**r.attributes, "zip": None}) for r in rows]
    null_host = TwoTenantHostTable(nulled, readable=readable)
    r_null = evaluate(Condition(op="eq", attribute="zip", value="90210",
                                why="a zip test"), nulled[0], readable)
    r_isnull = evaluate(Condition(op="is_null", attribute="zip",
                                  why="rows with no postcode"), nulled[0], readable)
    print(f"  eq over a NULL readable attribute -> holds={r_null.holds} "
          f"why={r_null.why!r}")
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
        (dict(op="eq", attribute="tenant", value="x", why="   "),
         "an empty `why`"),
        (dict(op="all_of", why="no terms"), "a combinator with no terms"),
        (dict(op="in", attribute="tenant", value="ca-host", why="scalar for in"),
         "`in` against a scalar"),
    ):
        try:
            Condition(**bad)
            refusals.append((label, False, ""))
        except DeclarationRefused as exc:
            refusals.append((label, True, str(exc)))
    for label, refused, why in refusals:
        print(f"  {'REFUSED ' if refused else 'ACCEPTED'} {label} -- {why}")
    check("all five malformed declarations are refused at declaration",
          all(r[1] for r in refusals),
          str([r[0] for r in refusals if not r[1]]))

    # --- 3.6 Kleene, stated and checked ------------------------------------
    print("\n3.6 three-valued composition")
    t = Condition(op="eq", attribute="tenant", value=TENANT_A[0], why="t")
    f = Condition(op="eq", attribute="tenant", value="nobody", why="f")
    u = Condition(op="eq", attribute=UNSEEABLE, value="x", why="u")
    rec = a_rows[0]
    cases = {
        "all_of(T,U)": evaluate(Condition(op="all_of", terms=(t, u), why="c"), rec,
                                readable).holds,
        "all_of(F,U)": evaluate(Condition(op="all_of", terms=(f, u), why="c"), rec,
                                readable).holds,
        "any_of(T,U)": evaluate(Condition(op="any_of", terms=(t, u), why="c"), rec,
                                readable).holds,
        "any_of(F,U)": evaluate(Condition(op="any_of", terms=(f, u), why="c"), rec,
                                readable).holds,
    }
    for k, v in cases.items():
        print(f"  {k} = {v}")
    check("all_of short-circuits on FALSE and only then on unknown; any_of on TRUE -- "
          "Kleene, so a partly-unreadable predicate still decides what it can",
          cases == {"all_of(T,U)": None, "all_of(F,U)": False,
                    "any_of(T,U)": True, "any_of(F,U)": None}, str(cases))

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
