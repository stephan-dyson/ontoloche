# -*- coding: utf-8 -*-
"""Design test 1 for `docs/specs/INGEST.md` v0 -- **the R78 seam**, and it runs
BEFORE any section of that document is written.

**The question.** R78 (`docs/decisions/2026-09-02-phase3-repoint-R77-R78.md` 4) is a
deliberately falsifiable default: *the host holds the instances; this project defines
the resolution protocol over them through adapter primitives, and stores no instance
rows of its own.* **Pass** = every outcome of ``resolve_instance`` is reachable with a
host-side table and a candidate-retrieval primitive, and no instance row is copied into
the registry. **Fail** = the row stops and the supervisor rules.

**AMENDED BY ROUND 1, and the amendments are most of this file.** Three lenses found
that the original probe could not pose the questions it claimed to answer: a mutation
deleting `INGEST.md` 3.4's load-bearing sentence left it printing ``16/16 checks pass``;
it took ``min_confidence`` as a call parameter, the exact shape rule 3-10 forbids; and
nine printed shapes were never executed at all. Sections T1.8 onward are what round 1
cost, and **every check that closes a finding is proved by MUTATION** -- run under
``_mutate="rule_u_last"`` it must go red, or it is a decoration.

**Two engines, exactly as ``actions_nyc_probe.py`` uses them.** The **shipped**
``ontoloche.Registry`` on SQLite holds the vocabulary, so *"no instance rows"* is a
claim about the real store; the host table and ``resolve_instance`` are throwaway kit
(``ingest_probe_kit.py``), because this row ships no product code.

**The data is real and the numbers are pinned.** ``NH_HealthCitations_Aug2026.csv``
(CMS Provider Data Catalog, ``r5ix-sfxw``) -- 419,479 rows, 14,627 CCNs, 104 provider
names shared by more than one CCN. The full file is 165 MB and is deliberately not in
this repository: pass its path, or let this probe download it to a temporary directory.

Run: ``py docs/tools/ingest_seam_probe.py [--csv <NH_HealthCitations_Aug2026.csv>]``
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingest_probe_kit import (  # noqa: E402
    Capabilities, CandidateQuery, CandidateRef, Condition, EntryDeclaration, HostTable,
    InstanceContext, InstanceRecord, MatchPolicy, NotSupported, OUTCOMES, Refusal,
    Vocabulary, assert_adapter_boundary, flat_form_ok, resolve_instance,
    CHAIN_CAP, type_closure,
)
from dataclasses import replace  # noqa: E402

csv.field_size_limit(10_000_000)

CMS_DATASET_URL = "https://data.cms.gov/provider-data/dataset/r5ix-sfxw"
CMS_METASTORE = (
    "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/r5ix-sfxw"
)

PINNED = {"bytes": 165336194, "rows": 419479, "ccns": 14627, "names": 14498,
          "shared_names": 104}
T1_1 = "BURNS NURSING HOME, INC."          # exactly one CCN: 015009
T1_2 = "MILLER'S MERRY MANOR"              # TWELVE CCNs, all Indiana
T1_3_CCN = "745040"                        # HELD OUT of the host: a real facility
T1_3 = "THE SARAH ROBERTS FRENCH HOME"     #   arriving new. 0.6415 against the rest
T1_4 = "Provider Name"                     # the column header, landed as a value
T1_5 = "Tuskegee Airmen Texas State Veterans Home"   # CCN 745057, row 14,623 of 14,627

#: INGEST 5. Declared on the ENTRY, never on the call (rules 5-1, 3-10).
CMS_POLICY = MatchPolicy(
    match_at=0.97, propose_below=0.80, ambiguity_margin=0.03,
    why="a provider name matching a held facility to 0.97 is that facility; below 0.80 "
        "it is a different one; the band between is a human's call")

CHECKS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


def ctx(act: str = "act-1", **kw) -> InstanceContext:
    return InstanceContext(act_id=act, proposed_by="ai:ingest", **kw)


# --------------------------------------------------------------------------------
# The fixture
# --------------------------------------------------------------------------------


def _resolve_csv(path: str | None) -> Path:
    if path:
        p = Path(path)
        if not p.exists():
            raise SystemExit(f"no such file: {p}")
        return p
    cached = Path(tempfile.gettempdir()) / "NH_HealthCitations_Aug2026.csv"
    if cached.exists() and cached.stat().st_size == PINNED["bytes"]:
        return cached
    meta = json.load(urllib.request.urlopen(CMS_METASTORE, timeout=120))
    url = meta["distribution"][0]["downloadURL"]
    print(f"  downloading {url}\n            -> {cached}")
    urllib.request.urlretrieve(url, cached)
    return cached


def load_host_rows(path: Path) -> tuple[list[InstanceRecord], dict]:
    """One InstanceRecord per CCN. The HOST's rows; nothing is written to the registry."""
    by_ccn: dict[str, InstanceRecord] = {}
    rows = 0
    processing_date = ""
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            rows += 1
            processing_date = processing_date or row.get("Processing Date", "")
            ccn = row["CMS Certification Number (CCN)"]
            if ccn in by_ccn:
                continue
            by_ccn[ccn] = InstanceRecord(
                namespace="cms", kind="entity", type_name="facility", instance_id=ccn,
                label=row["Provider Name"],
                attributes={"city": row["City/Town"], "state": row["State"],
                            "zip": row["ZIP Code"],
                            "address": row["Provider Address"]},
                # INSTANCE-level source_version: the export's own stamp. INTERFACE 2.4a
                source_version=f"NH_HealthCitations_Aug2026 / {processing_date}",
            )
    names: dict[str, set[str]] = {}
    for rec in by_ccn.values():
        names.setdefault(rec.label, set()).add(rec.instance_id)
    facts = {"bytes": path.stat().st_size, "rows": rows, "ccns": len(by_ccn),
             "names": len(names),
             "shared_names": sum(1 for v in names.values() if len(v) > 1)}
    return list(by_ccn.values()), facts


def cms_vocab(*, predicate: Condition | None = None,
              readable: frozenset[str] = frozenset(),
              successor: str | None = None,
              consumers_known: int = 0) -> Vocabulary:
    v = Vocabulary()
    v.declare("cms", "facility", EntryDeclaration(
        policy=CMS_POLICY, predicate=predicate, readable=readable,
        consumers_known=consumers_known, successor=successor))
    return v


# --------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.environ.get("CMS_CITATIONS_CSV"))
    args = ap.parse_args()

    print("DESIGN TEST 1 -- the R78 seam, over CMS `NH_HealthCitations_Aug2026.csv`")
    print(f"  source: {CMS_DATASET_URL}")
    path = _resolve_csv(args.csv)
    rows, facts = load_host_rows(path)
    print(f"  file: {facts['bytes']} bytes, {facts['rows']} rows")
    print(f"  host table: {facts['ccns']} CCNs, {facts['names']} distinct provider "
          f"names, {facts['shared_names']} names shared by more than one CCN")
    check("the pre-registered CMS figures reproduce", facts == PINNED, f"{facts}")

    assert_adapter_boundary()
    check("the host table names no facade shape (PACKAGE 3.1, C0-04's rule)", True)

    host = HostTable(rows)
    vocab = cms_vocab()

    # --- the registry: vocabulary only, and it is the SHIPPED one ---------------
    from ontoloche import Evidence, NamespacePolicy, Registry
    from ontoloche.backends.sqlite import SQLiteAdapter
    from ontoloche.types import ResolveContext

    registry = Registry(
        SQLiteAdapter.open(":memory:"),
        policies={"cms": NamespacePolicy(namespace="cms", approval_policy="auto",
                                         min_auto_approve_tier="haiku")},
    )
    proposal = registry.propose_type(
        "facility", kind="entity",
        definition="A CMS-certified nursing facility, identified by its CCN.",
        namespace="cms", tier="sonnet", proposed_by="ai:ingest",
        evidence=[Evidence(
            kind="data", summary="14,627 CCNs in NH_HealthCitations_Aug2026.csv",
            locator="NH_HealthCitations_Aug2026.csv#CMS Certification Number (CCN)")],
    )
    if hasattr(proposal, "proposal_id"):
        registry.approve(proposal.proposal_id, namespace="cms", mode="auto",
                         by="auto:test")

    # --- R77: the instance string is NOT a type question -----------------------
    rt = registry.resolve_type(
        T1_1,
        ResolveContext(definition_hint="one nursing facility", sample_values=[T1_1],
                       source="NH_HealthCitations_Aug2026.csv#Provider Name",
                       sibling_columns=["CMS Certification Number (CCN)", "City/Town",
                                        "State"],
                       proposed_by="ai:ingest"),
        namespace="cms", tier="sonnet",
    )
    print(f"\n  R77 control -- resolve_type({T1_1!r})")
    print(f"    -> outcome={rt.outcome!r} reason={rt.reason!r}")
    check("R77: the type registry refuses the instance question rather than answering it",
          rt.outcome == "not_a_type", f"outcome={rt.outcome}")

    def resolve(label, *, h=None, v=None, **kw):
        return resolve_instance(label, ctx(**kw.pop("ctx_kw", {})), host=h or host,
                                vocab=v or vocab, namespace="cms",
                                type_name="facility", tier="sonnet", **kw)

    # --- T1.1 existing ----------------------------------------------------------
    print(f"\nT1.1 -- {T1_1!r} (one CCN in the file)")
    r = resolve(T1_1)
    print(f"  -> outcome={r.outcome!r} ref={r.ref!r} confidence={r.confidence} "
          f"scanned={r.scanned} complete={r.complete}")
    print(f"     warnings={r.warnings}")
    check("T1.1 existing, at the CCN the file gives",
          r.outcome == "existing" and r.ref == "cms:entity:facility#015009",
          f"{r.outcome} / {r.ref}")
    check("T1.1 the resolution carries rule 7-1's and 7-4's warnings, which round 1 "
          "found had no carrier",
          {"consumers_unregistered", "no_tenancy_predicate"} <= set(r.warnings),
          str(r.warnings))

    # --- T1.2 ambiguous ---------------------------------------------------------
    print(f"\nT1.2 -- {T1_2!r} (twelve CCNs in the file)")
    r2 = resolve(T1_2)
    print(f"  -> outcome={r2.outcome!r} known={r2.known} confidence={r2.confidence}")
    for c in r2.candidates[:3]:
        print(f"       {c.ref_key}  {c.score}  {c.discriminators['city']}, "
              f"{c.discriminators['state']}")
    print(f"       ... {r2.known} in the tied set")
    check("T1.2 ambiguous, never `existing`, and all twelve are handed back",
          r2.outcome == "ambiguous" and r2.known == 12,
          f"{r2.outcome} / known={r2.known}")
    check("T1.2 no ref: nothing answered for twelve facilities at once",
          r2.ref is None)
    check("T1.2 a CandidateRef is minted instead, and it has no id (rule 4-9)",
          isinstance(r2.candidate, CandidateRef) and not hasattr(r2.candidate, "id"))

    # --- T1.3 proposal ----------------------------------------------------------
    print(f"\nT1.3 -- {T1_3!r} (CCN {T1_3_CCN}), HELD OUT of the host table")
    print("        a real facility arriving new, which is the honest shape of a "
          "proposal")
    without = HostTable([rec for rec in rows if rec.instance_id != T1_3_CCN])
    r3 = resolve(T1_3, h=without)
    print(f"  -> outcome={r3.outcome!r} confidence={r3.confidence} "
          f"scanned={r3.scanned} complete={r3.complete}")
    check("T1.3 proposal, off a scan that finished",
          r3.outcome == "proposal" and r3.complete
          and r3.scanned == facts["ccns"] - 1,
          f"{r3.outcome} / complete={r3.complete} / scanned={r3.scanned}")
    check("T1.3 a proposal mints a CandidateRef with no id (rule 4-9)",
          isinstance(r3.candidate, CandidateRef)
          and r3.candidate.resolution == "proposal")

    # --- T1.4 not_an_instance ---------------------------------------------------
    print(f"\nT1.4 -- {T1_4!r}, the column header landed as a value")
    r4 = resolve(T1_4)
    print(f"  -> outcome={r4.outcome!r} scanned={r4.scanned}")
    check("T1.4 not_an_instance, and the host table was never scanned for it",
          r4.outcome == "not_an_instance" and r4.scanned == 0,
          f"{r4.outcome} / scanned={r4.scanned}")

    # --- T1.5 truncation with the match UNREAD ----------------------------------
    cap = 14000
    print(f"\nT1.5 -- {T1_5!r}, row 14,623 of 14,627, host scan capped at {cap}")
    capped = HostTable(rows, scan_cap=cap)
    r5 = resolve(T1_5, h=capped)
    r5_ok = resolve(T1_5)
    print(f"  capped   -> outcome={r5.outcome!r} complete={r5.complete} "
          f"scanned={r5.scanned}")
    print(f"  uncapped -> outcome={r5_ok.outcome!r} ref={r5_ok.ref!r}")
    r5_mut = resolve(T1_5, h=capped, _mutate="rule_u_last")
    print(f"  MUTATED (Rule U last) -> outcome={r5_mut.outcome!r}")
    check("T1.5 a truncated scan that finds NOTHING is `unknowable`",
          r5.outcome == "unknowable" and not r5.complete, r5.outcome)
    check("T1.5 the row really is there and really was passed over",
          r5_ok.outcome == "existing" and r5_ok.ref == "cms:entity:facility#745057",
          f"{r5_ok.outcome} / {r5_ok.ref}")
    # THE FIXTURE'S OWN BLIND SPOT, asserted rather than discovered a second time.
    # Round 1 (K1/P1) counted it: `scan_cap` was set twice, both against a target the
    # cap put OUT of reach, so this case cannot tell the two orderings apart -- and
    # that is exactly why the trip survived four readers. T1.8 is the case that can.
    check("T1.5 MUTATION: the broken ordering and the fixed one AGREE here -- so this "
          "fixture cannot pose the question, and asserting that is what stops it being "
          "mistaken for coverage",
          r5_mut.outcome == r5.outcome == "unknowable",
          f"fixed={r5.outcome} mutated={r5_mut.outcome}")

    # --- T1.6 R58's three states -------------------------------------------------
    print("\nT1.6 -- R58's three states off one primitive")
    q = CandidateQuery(namespace="cms", kind="entity", type_name="facility")
    p_all = host.find_instance_candidates(q)
    p_page = host.find_instance_candidates(
        CandidateQuery(namespace="cms", kind="entity", type_name="facility", limit=500))
    p_trunc = capped.find_instance_candidates(q)
    for name, p in (("the set", p_all), ("a page", p_page), ("truncated", p_trunc)):
        print(f"  {name:>10}: known={p.known} complete={p.complete} "
              f"next_after={p.next_after!r}")
    check("R58 row 1 -- complete=True is the set",
          p_all.complete and p_all.known == facts["ccns"] and p_all.next_after is None)
    check("R58 row 2 -- a page: incomplete, cursor present, `known` counts the PAGE",
          not p_page.complete and p_page.next_after is not None and p_page.known == 500)
    check("R58 row 3 -- truncated: incomplete, NO cursor, and a `why`",
          not p_trunc.complete and p_trunc.next_after is None
          and bool(p_trunc.why_incomplete))

    # --- T1.7 the seam's own assertion ------------------------------------------
    print("\nT1.7 -- what the registry holds after all of it")
    listing = registry.list_types(namespace="cms")
    held = sorted((t.kind, t.name) for t in listing.types)
    print(f"  registry rows: {held}")
    instance_strings = {rec.instance_id for rec in rows} | {rec.label for rec in rows}
    leaked = [n for _, n in held if n in instance_strings]
    check("T1.7 the registry holds vocabulary only -- ONE kind='entity' row, `facility`",
          held == [("entity", "facility")], str(held))
    check("T1.7 no instance identifier or label reached the registry",
          not leaked, str(leaked))

    # ==========================================================================
    #  Round 1's findings, each CONSTRUCTED and each proved by mutation
    # ==========================================================================

    # --- T1.8 THE TRIP: truncation with the match FOUND (K1 / P1) ---------------
    print(f"\nT1.8 -- ROUND 1's TRIP: truncation with the match FOUND")
    ids = sorted(r.instance_id for r in rows)
    first_tied = min(r.instance_id for r in rows if r.label == T1_2)
    cut = ids.index(first_tied) + 1
    part = HostTable(rows, scan_cap=cut)
    r8 = resolve(T1_2, h=part)
    r8_mut = resolve(T1_2, h=part, _mutate="rule_u_last")
    print(f"  cap={cut} (1 of the twelve read, 11 unread)")
    print(f"  FIXED   -> outcome={r8.outcome!r} ref={r8.ref!r} complete={r8.complete} "
          f"scanned={r8.scanned}")
    print(f"  MUTATED -> outcome={r8_mut.outcome!r} ref={r8_mut.ref!r} "
          f"confidence={r8_mut.confidence}")
    check("T1.8 a truncated read that FINDS a match is `unknowable` (rules 3-5, 3-6)",
          r8.outcome == "unknowable" and r8.ref is None,
          f"{r8.outcome} / {r8.ref}")
    check("T1.8 MUTATION: the old ordering answers `existing` at 1.0 on a label twelve "
          "facilities answer to -- the check goes red",
          r8_mut.outcome == "existing" and r8_mut.confidence == 1.0,
          f"{r8_mut.outcome} / {r8_mut.confidence}")
    check("T1.8 rule 3-6: NO complete=False result carries any outcome but unknowable "
          "or not_an_instance",
          all(x.complete or x.outcome in ("unknowable", "not_an_instance")
              for x in (r5, r8)), f"{r5.outcome},{r8.outcome}")

    # --- T1.9 the band is wider than the margin (K2) ----------------------------
    print("\nT1.9 -- two candidates both at or above match_at, over a COMPLETE scan")
    pair = [(a, b) for a, b in (("115688", "265412"),)]
    near = [rec for rec in rows if rec.instance_id in {p for t in pair for p in t}]
    near_host = HostTable(near)
    r9 = resolve_instance(near[0].label, ctx(), host=near_host, vocab=vocab,
                          namespace="cms", type_name="facility", tier="sonnet")
    print(f"  {near[0].label!r} ({near[0].instance_id}) vs "
          f"{near[1].label!r} ({near[1].instance_id})")
    print(f"  -> outcome={r9.outcome!r} ref={r9.ref!r} known={r9.known} "
          f"complete={r9.complete}")
    check("T1.9 the tie test is a SET test: two match-grade candidates are `ambiguous`, "
          "not `existing` (rules 3-3, 5-8)",
          r9.outcome == "ambiguous" and r9.ref is None and r9.known == 2,
          f"{r9.outcome} / known={r9.known}")

    # --- T1.10 the review band answers in the five (K3) -------------------------
    print("\nT1.10 -- a score inside the band answers in the FIVE, not a sixth verdict")
    banded = "BURNS NURSING HM INC"            # 0.9524 against T1_1: inside the band
    r10 = resolve(banded)
    print(f"  {banded!r} -> outcome={r10.outcome!r} confidence={r10.confidence}")
    check("T1.10 a banded score is `ambiguous` and the gate mints no vocabulary of its "
          "own (rules 5-4, 5-9)",
          r10.outcome in OUTCOMES and r10.outcome == "ambiguous",
          f"{r10.outcome} @ {r10.confidence}")

    # --- T1.11 the successor chain and the zero-row read (K6) -------------------
    print("\nT1.11 -- the type is retired underneath the instances")
    moved = Vocabulary()
    moved.declare("cms", "facility", EntryDeclaration(
        policy=CMS_POLICY, successor="nursing_facility"))
    moved.declare("cms", "nursing_facility", EntryDeclaration(policy=CMS_POLICY))
    renamed = HostTable([
        InstanceRecord("cms", "entity", "nursing_facility", rec.instance_id, rec.label,
                       rec.attributes) for rec in rows])
    r11 = resolve_instance(T1_1, ctx(), host=renamed, vocab=moved, namespace="cms",
                           type_name="facility", tier="sonnet")
    print(f"  resolve(type_name='facility') after retire(successor='nursing_facility')")
    print(f"  -> outcome={r11.outcome!r} ref={r11.ref!r} scanned={r11.scanned}")
    print(f"     warnings={r11.warnings}")
    check("T1.11 the identity read follows the successor chain, as R38 requires of "
          "`neighbors` (rule 3-14)",
          r11.outcome == "existing"
          and r11.ref == "cms:entity:nursing_facility#015009",
          f"{r11.outcome} / {r11.ref}")
    check("T1.11 and it says so", any(w.startswith("instance_type_succeeded:")
                                      for w in r11.warnings), str(r11.warnings))
    empty = HostTable([], capabilities=host.capabilities)
    r11b = resolve_instance(T1_1, ctx(), host=empty, vocab=vocab, namespace="cms",
                            type_name="facility", tier="sonnet")
    print(f"  a read of ZERO rows -> outcome={r11b.outcome!r} scanned={r11b.scanned}")
    check("T1.11 a read of zero rows is `unknowable`, never a confident `proposal` "
          "(rule 3-13)", r11b.outcome == "unknowable", r11b.outcome)

    # --- T1.12 the capability flags and NotSupported (F9) -----------------------
    print("\nT1.12 -- the two capability flags 2.3 mints")
    blind = HostTable(rows, capabilities=Capabilities(
        resolves_instances=False,
        why={"resolves_instances": "this backend predates the ingest primitives"}))
    r12 = resolve(T1_1, h=blind)
    raised = False
    try:
        blind.get_instance("cms", "entity", "facility", "015009")
    except NotSupported:
        raised = True
    print(f"  resolves_instances=False -> {r12}")
    check("T1.12 rule 1-3: `instance_source_absent`, never an empty candidate set",
          isinstance(r12, Refusal) and r12.reason == "instance_source_absent", str(r12))
    check("T1.12 primitive 22 raises NotSupported and the registry never calls it",
          raised)
    undeclared = host.find_instance_candidates(CandidateQuery(
        namespace="cms", kind="entity", type_name="facility",
        host_filter={"ownership_type": "government"}))
    print(f"  a host_filter key outside instance_filters -> complete="
          f"{undeclared.complete} why={undeclared.why_incomplete!r}")
    check("T1.12 rule 2-7/2-10: an undeclared host_filter KEY is reported by name, "
          "never silently ignored",
          not undeclared.complete and "ownership_type" in (undeclared.why_incomplete or ""),
          str(undeclared.why_incomplete))
    narrowed = resolve(T1_1, host_filter={"state": "AL"})
    print(f"  a DECLARED host_filter -> outcome={narrowed.outcome!r} "
          f"scanned={narrowed.scanned} warnings={narrowed.warnings}")
    check("T1.12 rule 2-13: a narrowed query says which keys narrowed it",
          any(w.startswith("instance_narrowed_proposal:") for w in narrowed.warnings),
          str(narrowed.warnings))

    # --- T1.13 primitive 22 has a caller, and the flat-form guard (F13, K8) -----
    print("\nT1.13 -- primitive 22's caller, and the flat-form guard")
    confirmed = host.get_instance("cms", "entity", "facility", "015009")
    print(f"  get_instance re-confirms {r.ref!r} -> {confirmed.label!r}")
    check("T1.13 primitive 22 re-confirms a resolved ref at the moment of use "
          "(R54/R55's lesson at the instance surface)",
          confirmed is not None and confirmed.label == T1_1)
    bad = InstanceRecord("cms", "entity", "facility#015009", "2024-03-11", "x", {})
    good = InstanceRecord("cms", "entity", "facility", "015009#2024-03-11", "x", {})
    print(f"  flat_form_ok(type_name carrying '#') -> {flat_form_ok(bad)!r}")
    print(f"  flat_form_ok(opaque id carrying '#') -> {flat_form_ok(good)!r}")
    check("T1.13 rule 2-14: a record whose type_name would make ref_key unfaithful is "
          "caught; a legal opaque id is not",
          flat_form_ok(bad) is not None and flat_form_ok(good) is None)
    guarded = HostTable([bad], capabilities=host.capabilities)
    r13 = resolve_instance("x", ctx(), host=guarded, vocab=cms_vocab(), namespace="cms",
                           type_name="facility#015009", tier="sonnet")
    check("T1.13 and the primitive refuses rather than handing out a colliding ref",
          isinstance(r13, Refusal), str(r13)[:70])

    # --- T1.14 InstanceContext is actually executed (F9) ------------------------
    print("\nT1.14 -- InstanceContext, the call's second positional argument")
    context = InstanceContext(
        label_source="NH_HealthCitations_Aug2026.csv#Provider Name",
        row_attributes={"State": "AL", "City/Town": "RUSSELLVILLE"},
        siblings=(("facility", T1_2), ("value_set", "Deficiency Corrected")),
        act_id="act-cms-1", proposed_by="ai:ingest")
    r14 = resolve_instance(T1_1, context, host=host, vocab=vocab, namespace="cms",
                           type_name="facility", tier="sonnet")
    print(f"  label_source={context.label_source!r}")
    print(f"  siblings={context.siblings}")
    print(f"  -> outcome={r14.outcome!r}")
    check("T1.14 the context object is executed, and `siblings` is TYPED (F6)",
          r14.outcome == "existing"
          and all(len(s) == 2 for s in context.siblings))
    check("T1.14 a CandidateRef carries the act it belongs to (rule 4-10's scope)",
          resolve(T1_3, h=without).candidate.act_id == "act-1", "")

    # =====================================================================
    # T1.13 -- ROUND 3's DEBT. The eight rules 6.9c obliged this row to prove
    #         with a red check, plus the three of E3's survivors that are rules
    #         rather than probe wiring. Round 3's E22/P1 found NONE of them had
    #         one, a full round after the row wrote the obligation.
    #
    #         "A check that cannot go red is a decoration" -- this row's own
    #         standard, applied to the rules it leaned on hardest.
    # =====================================================================
    print("\nT1.13 -- the eight rules 6.9c named, and E3's survivors")

    # rule 1-1 / C20-01 -- the rule the whole R78 verdict rests on
    novel = HostTable([rec for rec in host._rows if rec.instance_id != T1_3_CCN])
    r = resolve_instance(T1_3, InstanceContext(act_id="t13"), host=novel,
                         vocab=cms_vocab(), namespace="cms", type_name="facility",
                         tier="sonnet", _mutate="registry_mints")
    print(f"  C20-01 MUTATED -> outcome={r.outcome!r} ref={r.ref!r}")
    check("T1.13 rule 1-1 / `C20-01`: this project MINTS NO instance identifiers -- "
          "the mutation hands back a registry-invented ref and this check is what "
          "makes that visible. Round 3's P1 reached it on a live path over 209 real "
          "Colorado facilities with all 104 checks green",
          r.ref == "cms:entity:facility#minted-by-registry",
          f"the mutation must be reachable: {r.ref}")
    control = resolve_instance(T1_3, InstanceContext(act_id="t13"), host=novel,
                               vocab=cms_vocab(), namespace="cms",
                               type_name="facility", tier="sonnet")
    check("T1.13 rule 1-1 / `C20-01`, the FIXED arm: no ref the registry invented",
          control.ref is None and control.outcome == "proposal",
          f"{control.outcome} / {control.ref}")

    # rule 2-1 / C20-04 -- two primitives, both READS
    writers = [n for n in dir(HostTable)
               if n.startswith(("put", "write", "set_", "add_", "delete", "upsert"))]
    print(f"  C20-04: write-shaped methods on the host adapter -> {writers}")
    check("T1.13 rule 2-1 / `C20-04`: the adapter surface is TWO READS and no write. "
          "A `put_instance` would make this go red, and round 3 found nothing that "
          "would have noticed", writers == [], str(writers))

    # rule 6-17 / C20-58 -- the candidate primitive takes no tenant
    fields = set(CandidateQuery.__dataclass_fields__)
    print(f"  C20-58: CandidateQuery fields -> {sorted(fields)}")
    check("T1.13 rule 6-17 / `C20-58`: the candidate primitive takes NO tenant "
          "parameter -- R24/R59's tenant-blind protocol, checked on the shape rather "
          "than asserted in prose",
          not (fields & {"tenant", "tenant_id", "host", "owner"}), str(sorted(fields)))

    # rule 3-11 / C20-25 -- tier echoed back for provenance
    r = resolve_instance(T1_3, InstanceContext(act_id="t13"), host=novel,
                         vocab=cms_vocab(), namespace="cms", type_name="facility",
                         tier="sonnet", _mutate="tier_dropped")
    print(f"  C20-25 MUTATED -> tier={r.tier!r}  (control {control.tier!r})")
    check("T1.13 rule 3-11 / `C20-25`: `tier` is echoed back, because "
          "`InvocationProvenance.model_tier` depends on it and a dropped tier is a "
          "provenance hole nothing else reports",
          control.tier == "sonnet" and r.tier == "", f"{control.tier!r}/{r.tier!r}")

    # rule 3-4 / C20-18 -- EVERY tied candidate is returned
    r = resolve_instance(T1_2, InstanceContext(act_id="t13"), host=host,
                         vocab=cms_vocab(), namespace="cms", type_name="facility",
                         tier="sonnet", _mutate="one_of_tied")
    full = resolve_instance(T1_2, InstanceContext(act_id="t13"), host=host,
                            vocab=cms_vocab(), namespace="cms", type_name="facility",
                            tier="sonnet")
    print(f"  C20-18 MUTATED -> known={r.known} len(candidates)={len(r.candidates)}"
          f"   (control {full.known}/{len(full.candidates)})")
    check("T1.13 rule 3-4 / `C20-18`: on `ambiguous` EVERY tied candidate is returned "
          "-- `known` agreeing with `len(candidates)` is the invariant, and the "
          "mutation reporting 2 while returning 1 is the shape trips 11 and 12 took",
          full.known == len(full.candidates) == 12
          and r.known != len(r.candidates),
          f"control {full.known}/{len(full.candidates)}, mutated {r.known}/{len(r.candidates)}")

    # rule 2-14 / C20-65 -- E3's survivor, and 13's route 12 rests on it
    bad_rec = InstanceRecord("cms", "entity", "facility#015009", "2024-03-11",
                             "AMBIGUOUS FLAT FORM", {})
    for mut, tag in ((None, "GUARD ON"), ("flat_form_off", "MUTATED")):
        v_bad = cms_vocab()
        v_bad.declare("cms", "facility#015009", v_bad.entry("cms", "facility"))
        out = resolve_instance("AMBIGUOUS FLAT FORM", InstanceContext(act_id="t13"),
                               host=HostTable([bad_rec]), vocab=v_bad,
                               namespace="cms", type_name="facility#015009",
                               tier="sonnet", _mutate=mut)
        got = out.reason if isinstance(out, Refusal) else out.outcome
        print(f"  C20-65 {tag} -> {type(out).__name__} {got}")
        if mut is None:
            check("T1.13 rule 2-14 / `C20-65`: a record whose `type_name` would make "
                  "`ref_key` unfaithful is REFUSED at the surface that hands out refs. "
                  "13's route 12 rests on this rule and round 3's E3 found it had no "
                  "check that could go red",
                  isinstance(out, Refusal), str(got))
        else:
            check("T1.13 rule 2-14 MUTATION: with the guard off the caller is handed a "
                  "ref `parse_ref` reads back as a different reference",
                  not isinstance(out, Refusal), str(got))

    # rules 3-16 / 3-17 -- E3's other two survivors
    chain = cms_vocab()
    for i in range(20):
        chain.declare("cms", f"t{i}", replace(chain.entry("cms", "facility"),
                                              successor=f"t{i+1}"))
    chain.declare("cms", "t20", replace(chain.entry("cms", "facility")))
    c_on = type_closure(chain, "cms", "t0")
    c_off = type_closure(chain, "cms", "t0", no_cap=True)
    print(f"  C20-77: cap ON -> complete={c_on.complete} hops={len(c_on.hops)}; "
          f"OFF -> complete={c_off.complete} hops={len(c_off.hops)}")
    check("T1.13 rule 3-16 / `C20-77`: the walk carries a hop cap and reaching it is "
          "`complete=False` with a `why`, never a silent answer. The cap is 16, the "
          "SHIPPED `_IDENTITY_CHAIN_CAP` value (round 3, E6)",
          (not c_on.complete) and len(c_on.hops) == CHAIN_CAP and c_off.complete,
          f"{c_on.complete}/{len(c_on.hops)} vs {c_off.complete}")

    cyc = cms_vocab()
    cyc.declare("cms", "a", replace(cyc.entry("cms", "facility"), successor="b"))
    cyc.declare("cms", "b", replace(cyc.entry("cms", "facility"), successor="a"))
    y_on = type_closure(cyc, "cms", "a")
    y_off = type_closure(cyc, "cms", "a", no_cycle_guard=True, no_cap=True)
    print(f"  C20-78: cycle guard ON -> complete={y_on.complete}; "
          f"OFF -> hops={len(y_off.hops)}")
    check("T1.13 rule 3-17 / `C20-78`: a CYCLE stops the walk with a `why` -- 5.9 does "
          "not forbid constructing one, so the walk must survive it",
          (not y_on.complete) and "cycles at" in y_on.why and len(y_off.hops) > 16,
          f"{y_on.complete} / {y_on.why[:40]} / {len(y_off.hops)}")

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    if failed:
        for label, _, detail in failed:
            print(f"  FAILED: {label} -- {detail}")
        print("R78 VERDICT: FAIL -- stop and route to the supervisor")
        return 1
    print("R78 VERDICT: CONFIRMED -- every outcome is reachable over a host-held table,")
    print("             through two read primitives, with no instance row in the "
          "registry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
