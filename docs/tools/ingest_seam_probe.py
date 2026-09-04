# -*- coding: utf-8 -*-
"""Design test 1 for `docs/specs/INGEST.md` v0 -- **the R78 seam**, and it runs
BEFORE any section of that document is written.

**The question.** R78 (`docs/decisions/2026-09-02-phase3-repoint-R77-R78.md` 4) is a
deliberately falsifiable default: *the host holds the instances; this project defines
the resolution protocol over them through adapter primitives, and stores no instance
rows of its own.* **Pass** = every outcome of ``resolve_instance`` is reachable with a
host-side table and a candidate-retrieval primitive, and no instance row is copied into
the registry. **Fail** = the row stops and the supervisor rules.

**Two engines, exactly as ``actions_nyc_probe.py`` uses them.** The **shipped**
``ontoloche.Registry`` on SQLite holds the vocabulary, so *"no instance rows"* is a
claim about the real store; the host table and ``resolve_instance`` are throwaway kit,
because this row ships no product code.

**The data is real and the numbers are pinned.** ``NH_HealthCitations_Aug2026.csv``
(CMS Provider Data Catalog, ``r5ix-sfxw``) -- 419,479 rows, 14,627 CCNs, 104 provider
names shared by more than one CCN. The 400-row Montana sample checked into
``ontoloche/contract/fixtures/`` carries ten facilities and **zero** shared names, so it
cannot pose this test. The full file is 165 MB and is deliberately not in this
repository: pass its path, or let this probe download it to a temporary directory.

Run: ``py docs/tools/ingest_seam_probe.py [--csv <NH_HealthCitations_Aug2026.csv>]``
"""

from __future__ import annotations

import argparse
import csv
import difflib
import inspect
import json
import os
import re
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

csv.field_size_limit(10_000_000)

CMS_DATASET_URL = "https://data.cms.gov/provider-data/dataset/r5ix-sfxw"
CMS_METASTORE = (
    "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/r5ix-sfxw"
)

#: Pinned so the walk-through reproduces. A design test whose numbers move is not one.
PINNED = {"bytes": 165336194, "rows": 419479, "ccns": 14627, "names": 14498,
          "shared_names": 104}
T1_1 = "BURNS NURSING HOME, INC."          # exactly one CCN: 015009
T1_2 = "MILLER'S MERRY MANOR"              # TWELVE CCNs, all Indiana
T1_3 = "ONTOLOCHE MEMORIAL CARE CENTER"    # in none of the 419,479 rows
T1_4 = "Provider Name"                     # the column header, landed as a value
T1_5 = "Tuskegee Airmen Texas State Veterans Home"   # CCN 745057, row 14,623 of 14,627

CHECKS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))


# --------------------------------------------------------------------------------
# The HOST side. R78's whole claim is that this stays the host's, so it is written the
# way a host's table is written: flat records, no facade shape, deciding nothing.
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class InstanceRecord:
    """One row of the HOST's system of record. The adapter's shape, not the facade's.

    ``attributes`` is opaque to this project exactly as ``EdgeRecord.attributes`` is:
    the host's own columns, carried so a resolver can discriminate, never interpreted
    down here.
    """

    namespace: str
    kind: str            # "entity" -- EDGES 2.1's rule for an InstanceRef's type
    type_name: str
    instance_id: str     # the HOST's identifier. Opaque. EDGES 2.1
    label: str           # the human-facing string a landed row carries
    attributes: dict


@dataclass(frozen=True)
class CandidateQuery:
    namespace: str
    kind: str
    type_name: str
    label: str | None = None
    #: R58: the ADAPTER pages. ``limit`` bounds ONE page; ``after`` is the opaque cursor.
    limit: int | None = None
    after: str | None = None


@dataclass(frozen=True)
class CandidatePage:
    records: tuple[InstanceRecord, ...]
    known: int | None            # None = the backend cannot count. NOT 0. Rule U
    complete: bool
    why_incomplete: str | None
    next_after: str | None


class HostFacilityTable:
    """The host's own facility table, reached ONLY through two read primitives.

    Nothing here is copied into the registry, and nothing here knows what a resolution
    is -- ``assert_adapter_boundary()`` checks the second half by source inspection, the
    way ``C0-04`` checks the real adapter.

    ``scan_cap`` is the host's own limit on how much of its table one scan may read --
    *a store that capped*, R58's third row. It is what T1.5 needs and it is not a
    fiction: 14,627 rows scanned by a fuzzy name match have no index to ride.
    """

    def __init__(self, rows: list[InstanceRecord], *, scan_cap: int | None = None,
                 can_count: bool = True) -> None:
        self._rows = sorted(rows, key=lambda r: r.instance_id)
        self._scan_cap = scan_cap
        self._can_count = can_count

    # --- primitive 22 -------------------------------------------------------
    def get_instance(self, namespace: str, kind: str, type_name: str,
                     instance_id: str) -> InstanceRecord | None:
        """``None`` means ABSENT, a fact -- the host always knows its own keys."""
        for rec in self._rows:
            if (rec.namespace, rec.kind, rec.type_name, rec.instance_id) == (
                namespace, kind, type_name, instance_id
            ):
                return rec
        return None

    # --- primitive 23 -------------------------------------------------------
    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage:
        """The one call behind the resolution. Pages under R58's one rule.

        ``known`` counts what THIS PAGE materialised; ``complete`` is about the SET;
        ``next_after`` says whether there is more. A cap the host imposed is the third
        state -- incomplete, no cursor, and a ``why``.
        """
        pool = [
            r for r in self._rows
            if (r.namespace, r.kind, r.type_name) == (q.namespace, q.kind, q.type_name)
        ]
        start = 0
        if q.after is not None:
            start = next((i for i, r in enumerate(pool) if r.instance_id > q.after),
                         len(pool))
        window = pool[start:]
        capped = False
        if self._scan_cap is not None:
            allowed = max(self._scan_cap - start, 0)
            if len(window) > allowed:
                window = window[:allowed]
                capped = True
        page = window if q.limit is None else window[: q.limit]
        more_in_window = q.limit is not None and len(window) > q.limit
        return CandidatePage(
            records=tuple(page),
            known=len(page) if self._can_count else None,
            complete=not capped and not more_in_window,
            why_incomplete=(
                f"host scan cap of {self._scan_cap} rows reached; the rest of this "
                "table cannot be read from this surface"
                if capped and not more_in_window else None
            ),
            next_after=page[-1].instance_id if more_in_window and page else None,
        )


def assert_adapter_boundary() -> None:
    """PACKAGE 3.1 / C0-04's rule, applied to this kit's host table."""
    src = inspect.getsource(HostFacilityTable)
    for forbidden in ("InstanceResolution", "Refusal", "InstanceProposal",
                      "resolve_instance", "confidence", "ambiguous"):
        if forbidden in src:
            raise AssertionError(
                f"HostFacilityTable mentions {forbidden!r} -- the host stores records "
                "and decides nothing (PACKAGE 3.1)"
            )


# --------------------------------------------------------------------------------
# The ONTOLOCHE side. Above the primitive, never inside it.
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class InstanceCandidate:
    ref_key: str      # "<namespace>:<kind>:<type>#<instance_id>" -- ACTIONS 2.3's grammar
    label: str
    score: float
    discriminators: dict


@dataclass(frozen=True)
class InstanceResolution:
    outcome: str
    ref_key: str | None
    confidence: float | None
    reason: str
    candidates: tuple[InstanceCandidate, ...]
    known: int
    complete: bool
    why_incomplete: str
    scanned: int
    tier: str


_CLASS_WORDS = {
    "facility", "provider", "provider name", "nursing home", "nursing facility",
    "hospital", "organisation", "organization", "entity", "name", "id",
}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def resolve_instance(
    candidate: str,
    *,
    host: HostFacilityTable,
    namespace: str,
    type_name: str,
    tier: str,
    min_confidence: float = 0.86,
    ambiguity_margin: float = 0.02,
    page_size: int | None = None,
    outcomes: tuple[str, ...] = (
        "existing", "ambiguous", "proposal", "not_an_instance", "unknowable",
    ),
) -> InstanceResolution:
    """The four-outcome shape mirrored from ``resolve_type``, plus the fifth T1.5 argues for.

    ``outcomes`` is a parameter ONLY so this probe can run one walk-through under the
    brief's four-value set and under the five-value one, and report what the ``proposal``
    value has to absorb when the fifth does not exist. It is not a design.
    """
    # 1. Is this an instance at all? The mirror of `resolve_type`'s `not_a_type`.
    norm = _norm(candidate)
    if not norm or norm in _CLASS_WORDS:
        return InstanceResolution(
            outcome="not_an_instance", ref_key=None, confidence=None,
            reason=f"{candidate!r} names a class or a column, not one thing of that class",
            candidates=(), known=0, complete=True, why_incomplete="", scanned=0,
            tier=tier,
        )

    # 2. Scan the HOST through the primitive. The registry never reads the table.
    scanned = 0
    scored: list[InstanceCandidate] = []
    after: str | None = None
    complete = True
    why_incomplete = ""
    while True:
        page = host.find_instance_candidates(
            CandidateQuery(namespace=namespace, kind="entity", type_name=type_name,
                           label=candidate, limit=page_size, after=after)
        )
        scanned += len(page.records)
        for rec in page.records:
            scored.append(
                InstanceCandidate(
                    ref_key=f"{rec.namespace}:{rec.kind}:{rec.type_name}#{rec.instance_id}",
                    label=rec.label,
                    score=round(_similar(norm, _norm(rec.label)), 4),
                    discriminators=rec.attributes,
                )
            )
        if not page.complete and page.next_after is None:
            complete = False
            why_incomplete = page.why_incomplete or "the scan did not finish"
            break
        if page.next_after is None:
            break
        after = page.next_after
    scored.sort(key=lambda c: (-c.score, c.ref_key))
    top = [c for c in scored if c.score >= min_confidence]

    # 3. Rule U FIRST, and that ordering is the whole finding of T1.5.
    if not top and not complete:
        if "unknowable" in outcomes:
            return InstanceResolution(
                outcome="unknowable", ref_key=None, confidence=None,
                reason=f"the candidate scan did not finish: {why_incomplete}",
                candidates=tuple(scored[:5]), known=len(scored[:5]), complete=False,
                why_incomplete=why_incomplete, scanned=scanned, tier=tier,
            )
        # The four-outcome set has nowhere to put it. This branch is the evidence.
        return InstanceResolution(
            outcome="proposal", ref_key=None, confidence=None,
            reason="nothing in the scanned rows matched",
            candidates=tuple(scored[:5]), known=len(scored[:5]), complete=False,
            why_incomplete=why_incomplete, scanned=scanned, tier=tier,
        )

    # 4. Ambiguity BEFORE existence: two instances answering to one identity is the kill
    #    row one level down, and it must never be resolved to the first of them.
    if len(top) > 1 and (top[0].score - top[1].score) <= ambiguity_margin:
        tied = tuple(c for c in top if (top[0].score - c.score) <= ambiguity_margin)
        return InstanceResolution(
            outcome="ambiguous", ref_key=None, confidence=top[0].score,
            reason=(
                f"{len(tied)} host rows answer to {candidate!r} within "
                f"{ambiguity_margin} of each other; nothing here separates them"
            ),
            candidates=tied, known=len(tied), complete=complete,
            why_incomplete=why_incomplete, scanned=scanned, tier=tier,
        )
    if top:
        return InstanceResolution(
            outcome="existing", ref_key=top[0].ref_key, confidence=top[0].score,
            reason=f"one host row answers to {candidate!r}",
            candidates=tuple(top[:5]), known=len(top[:5]), complete=complete,
            why_incomplete=why_incomplete, scanned=scanned, tier=tier,
        )
    return InstanceResolution(
        outcome="proposal", ref_key=None,
        confidence=(scored[0].score if scored else None),
        reason=f"nothing in {scanned} scanned host rows answers to {candidate!r}",
        candidates=tuple(scored[:5]), known=len(scored[:5]), complete=complete,
        why_incomplete=why_incomplete, scanned=scanned, tier=tier,
    )


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
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            rows += 1
            ccn = row["CMS Certification Number (CCN)"]
            if ccn in by_ccn:
                continue
            by_ccn[ccn] = InstanceRecord(
                namespace="cms", kind="entity", type_name="facility", instance_id=ccn,
                label=row["Provider Name"],
                attributes={
                    "city": row["City/Town"], "state": row["State"],
                    "zip": row["ZIP Code"], "address": row["Provider Address"],
                },
            )
    names: dict[str, set[str]] = {}
    for rec in by_ccn.values():
        names.setdefault(rec.label, set()).add(rec.instance_id)
    facts = {
        "bytes": path.stat().st_size,
        "rows": rows,
        "ccns": len(by_ccn),
        "names": len(names),
        "shared_names": sum(1 for v in names.values() if len(v) > 1),
    }
    return list(by_ccn.values()), facts


# --------------------------------------------------------------------------------
# The walk-through
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
    check("the pre-registered CMS figures reproduce",
          facts == PINNED, f"{facts}")

    assert_adapter_boundary()
    check("the host table names no facade shape (PACKAGE 3.1, C0-04's rule)", True)

    host = HostFacilityTable(rows)

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
            kind="data",
            summary="14,627 CCNs in NH_HealthCitations_Aug2026.csv",
            locator="NH_HealthCitations_Aug2026.csv#CMS Certification Number (CCN)")],
    )
    if hasattr(proposal, "proposal_id"):
        registry.approve(proposal.proposal_id, namespace="cms", mode="auto",
                         by="auto:test")

    # --- R77: the instance string is NOT a type question -----------------------
    rt = registry.resolve_type(
        T1_1,
        ResolveContext(
            definition_hint="one nursing facility",
            sample_values=[T1_1],
            source="NH_HealthCitations_Aug2026.csv#Provider Name",
            sibling_columns=["CMS Certification Number (CCN)", "City/Town", "State"],
            proposed_by="ai:ingest"),
        namespace="cms", tier="sonnet",
    )
    print(f"\n  R77 control -- resolve_type({T1_1!r})")
    print(f"    -> outcome={rt.outcome!r} reason={rt.reason!r}")
    check("R77: the type registry refuses the instance question rather than answering it",
          rt.outcome == "not_a_type", f"outcome={rt.outcome}")

    # --- T1.1 existing ----------------------------------------------------------
    print(f"\nT1.1 -- {T1_1!r} (one CCN in the file)")
    r = resolve_instance(T1_1, host=host, namespace="cms", type_name="facility",
                         tier="sonnet")
    print(f"  -> outcome={r.outcome!r} ref_key={r.ref_key!r} confidence={r.confidence} "
          f"scanned={r.scanned} complete={r.complete}")
    check("T1.1 existing, at the CCN the file gives",
          r.outcome == "existing" and r.ref_key == "cms:entity:facility#015009",
          f"{r.outcome} / {r.ref_key}")

    # --- T1.2 ambiguous ---------------------------------------------------------
    print(f"\nT1.2 -- {T1_2!r} (twelve CCNs in the file)")
    r2 = resolve_instance(T1_2, host=host, namespace="cms", type_name="facility",
                          tier="sonnet")
    print(f"  -> outcome={r2.outcome!r} known={r2.known} confidence={r2.confidence}")
    for c in r2.candidates:
        print(f"       {c.ref_key}  {c.score}  "
              f"{c.discriminators['city']}, {c.discriminators['state']}")
    check("T1.2 ambiguous, never `existing`, and all twelve are handed back",
          r2.outcome == "ambiguous" and r2.known == 12,
          f"{r2.outcome} / known={r2.known}")
    check("T1.2 no ref_key: nothing answered for twelve facilities at once",
          r2.ref_key is None)

    # --- T1.3 proposal ----------------------------------------------------------
    print(f"\nT1.3 -- {T1_3!r}, absent from all {facts['rows']} rows")
    r3 = resolve_instance(T1_3, host=host, namespace="cms", type_name="facility",
                          tier="sonnet")
    print(f"  -> outcome={r3.outcome!r} confidence={r3.confidence} "
          f"scanned={r3.scanned} complete={r3.complete}")
    check("T1.3 proposal, off a scan that finished",
          r3.outcome == "proposal" and r3.complete and r3.scanned == facts["ccns"],
          f"{r3.outcome} / complete={r3.complete} / scanned={r3.scanned}")

    # --- T1.4 not_an_instance ---------------------------------------------------
    print(f"\nT1.4 -- {T1_4!r}, the column header landed as a value")
    r4 = resolve_instance(T1_4, host=host, namespace="cms", type_name="facility",
                          tier="sonnet")
    print(f"  -> outcome={r4.outcome!r} reason={r4.reason!r} scanned={r4.scanned}")
    check("T1.4 not_an_instance, and the host table was never scanned for it",
          r4.outcome == "not_an_instance" and r4.scanned == 0,
          f"{r4.outcome} / scanned={r4.scanned}")

    # --- T1.5 the truncated scan -----------------------------------------------
    cap = 14000
    print(f"\nT1.5 -- {T1_5!r}, whose row is 14,623 of 14,627, with the host's scan "
          f"capped at {cap}")
    capped = HostFacilityTable(rows, scan_cap=cap)
    r5_five = resolve_instance(T1_5, host=capped, namespace="cms",
                               type_name="facility", tier="sonnet")
    print(f"  five-outcome set -> outcome={r5_five.outcome!r} "
          f"complete={r5_five.complete} scanned={r5_five.scanned}")
    print(f"                      why={r5_five.why_incomplete!r}")
    r5_four = resolve_instance(T1_5, host=capped, namespace="cms",
                               type_name="facility", tier="sonnet",
                               outcomes=("existing", "ambiguous", "proposal",
                                         "not_an_instance"))
    print(f"  four-outcome set -> outcome={r5_four.outcome!r} "
          f"complete={r5_four.complete}")
    print(f"                      reason={r5_four.reason!r}")
    r5_uncapped = resolve_instance(T1_5, host=host, namespace="cms",
                                   type_name="facility", tier="sonnet")
    print(f"  uncapped control -> outcome={r5_uncapped.outcome!r} "
          f"ref_key={r5_uncapped.ref_key!r} confidence={r5_uncapped.confidence}")
    check("T1.5 the fifth outcome exists and the scan says why",
          r5_five.outcome == "unknowable" and not r5_five.complete
          and bool(r5_five.why_incomplete), r5_five.outcome)
    check("T1.5 the FOUR-outcome set answers `proposal` for a facility that EXISTS -- "
          "the duplicate-manufacturing branch, constructed",
          r5_four.outcome == "proposal", r5_four.outcome)
    check("T1.5 the row really is there and really was passed over",
          r5_uncapped.outcome == "existing"
          and r5_uncapped.ref_key == "cms:entity:facility#745057",
          f"{r5_uncapped.outcome} / {r5_uncapped.ref_key}")

    # --- R58: paging under one rule --------------------------------------------
    print("\nT1.6 -- R58's three states off one primitive")
    q = CandidateQuery(namespace="cms", kind="entity", type_name="facility")
    p_all = host.find_instance_candidates(q)
    p_page = host.find_instance_candidates(
        CandidateQuery(namespace="cms", kind="entity", type_name="facility", limit=500))
    p_trunc = capped.find_instance_candidates(q)
    for name, p in (("the set", p_all), ("a page", p_page), ("truncated", p_trunc)):
        print(f"  {name:>10}: known={p.known} complete={p.complete} "
              f"next_after={p.next_after!r} why={p.why_incomplete!r}")
    check("R58 row 1 -- complete=True is the set",
          p_all.complete and p_all.known == facts["ccns"] and p_all.next_after is None)
    check("R58 row 2 -- a page: incomplete, cursor present, `known` counts the PAGE",
          not p_page.complete and p_page.next_after is not None and p_page.known == 500)
    check("R58 row 3 -- truncated: incomplete, NO cursor, and a `why`",
          not p_trunc.complete and p_trunc.next_after is None
          and bool(p_trunc.why_incomplete))

    # --- the seam's own assertion ----------------------------------------------
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
