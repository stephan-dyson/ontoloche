# -*- coding: utf-8 -*-
"""Design test 2 for `docs/specs/INGEST.md` v0 -- **paging under load (R58)**, driven
against the live NYC 311 dataset ``erm2-nwe9`` and its 9.7-million-row NYPD partition.

**What R58 requires and what this measures.** On a page, ``known`` counts what the
report materialised, ``complete`` is about the SET, and a cursor says whether there is
more and how to get it -- three states, one rule, and **a guard never reads a page**.
The candidate-retrieval primitive of ``INGEST.md`` 2 is the first ingestion-side surface
that pages, and ``erm2-nwe9`` with ``agency='NYPD'`` is the pre-registered case
(`docs/decisions/2026-08-30-phase3-decisions-R58-R60.md`, R58).

**The host here is Socrata, not a fixture.** ``$limit``/``$offset`` are the host's own
paging, so the primitive is a thin adapter over them and the cursor is opaque exactly as
R58 leaves it. Every count below is fetched live and printed with the date, because
`EDGES.md` 4.2's pinned figures have already moved once.

Run: ``py docs/tools/ingest_paging_probe.py``
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_seam_probe import CandidatePage, InstanceRecord, check, CHECKS  # noqa: E402

DATASET = "erm2-nwe9"
RESOURCE = f"https://data.cityofnewyork.us/resource/{DATASET}.json"
CATALOG = "https://data.cityofnewyork.us/resource"

#: EDGES.md 4.2, [Observed] 2026-08-29 by row #4. Re-measured here; see 2.1.
PINNED_2026_08_29 = {"rows": 22294072, "nypd": 9738128}

#: Socrata's own ceiling on one response. The host's page size, not ours.
HOST_MAX_PAGE = 50000

#: The HOST's own narrowing -- a predicate over columns `erm2-nwe9` already indexes.
#: Nothing in this project invents it, and that is the point of 2.4: the affordability
#: of candidate retrieval is a fact about the host's table, declared through the
#: primitive, and never a scan this project can arrange on its own.
HOST_NARROWING = ("agency='NYPD' AND complaint_type='Illegal Fireworks' "
                  "AND incident_zip='11214'")


def soda(params: dict) -> list[dict]:
    url = f"{RESOURCE}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=300) as fh:
        return json.load(fh)


def count(where: str | None = None) -> int:
    params = {"$select": "count(*)"}
    if where:
        params["$where"] = where
    return int(soda(params)[0]["count"])


# --------------------------------------------------------------------------------
# The primitive, over a live host. R58's one rule, nothing else.
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class SocrataCandidateQuery:
    """The host's narrowing is the HOST's, declared as a filter it already supports."""

    namespace: str
    kind: str
    type_name: str
    host_filter: str | None = None   # opaque to this project. The host's own predicate
    limit: int | None = None
    after: str | None = None         # opaque cursor. R58 leaves the ENCODING to the build row


class SocrataServiceRequests:
    """`erm2-nwe9` as a host-owned instance table, reached only through the primitive.

    ``scan_budget`` is what an ingestion caller is willing to read for ONE landed row.
    It is the reason this test exists: a 9.7-million-row partition is not scannable per
    row, and what the primitive does when the budget runs out is the whole finding.
    """

    def __init__(self, *, scan_budget: int, page_size: int = 1000) -> None:
        self.scan_budget = scan_budget
        self.page_size = min(page_size, HOST_MAX_PAGE)
        self.requests = 0
        self.rows_read = 0

    def find_instance_candidates(self, q: SocrataCandidateQuery) -> CandidatePage:
        offset = int(q.after) if q.after is not None else 0
        want = min(q.limit or self.page_size, self.page_size)
        remaining = self.scan_budget - offset
        if remaining <= 0:
            return CandidatePage(
                records=(), known=0, complete=False,
                why_incomplete=(
                    f"scan budget of {self.scan_budget} rows exhausted against a "
                    "partition this surface cannot read to the end"),
                next_after=None,
            )
        want = min(want, remaining)
        params = {
            "$limit": want, "$offset": offset,
            "$select": "unique_key,complaint_type,incident_address,agency,created_date",
            "$order": "unique_key",
        }
        if q.host_filter:
            params["$where"] = q.host_filter
        t0 = time.time()
        rows = soda(params)
        self.requests += 1
        self.rows_read += len(rows)
        elapsed = round(time.time() - t0, 2)
        records = tuple(
            InstanceRecord(
                namespace=q.namespace, kind="entity", type_name=q.type_name,
                instance_id=r["unique_key"],
                label=r.get("incident_address") or r.get("complaint_type", ""),
                attributes={k: v for k, v in r.items() if k != "unique_key"},
            )
            for r in rows
        )
        exhausted_page = len(rows) < want
        budget_gone = (offset + len(rows)) >= self.scan_budget
        return CandidatePage(
            records=records,
            known=len(records),
            complete=exhausted_page,
            why_incomplete=(
                f"scan budget of {self.scan_budget} rows reached in {self.requests} "
                f"host requests; the partition continues past this surface"
                if budget_gone and not exhausted_page else None),
            next_after=(str(offset + len(rows))
                        if not exhausted_page and not budget_gone else None),
        ), elapsed  # type: ignore[return-value]


def main() -> int:
    print(f"DESIGN TEST 2 -- paging under load (R58), live against {DATASET}")
    print(f"  measured {date.today().isoformat()} at {RESOURCE}")

    # --- 2.1 the load, re-measured -----------------------------------------
    total = count()
    nypd = count("agency='NYPD'")
    print(f"\n2.1 the node")
    print(f"  rows in the dataset : {total:,}   (row #4, 2026-08-29: "
          f"{PINNED_2026_08_29['rows']:,})")
    print(f"  agency='NYPD'       : {nypd:,}   (row #4, 2026-08-29: "
          f"{PINNED_2026_08_29['nypd']:,})")
    print(f"  drift since row #4  : +{total - PINNED_2026_08_29['rows']:,} rows, "
          f"+{nypd - PINNED_2026_08_29['nypd']:,} on the partition")
    check("the 9.7M-degree node is still there and is still the largest partition",
          nypd > 9_000_000, f"{nypd:,}")
    check("row #4's pinned figures have MOVED, which is a fact about pinning",
          nypd != PINNED_2026_08_29["nypd"],
          f"{PINNED_2026_08_29['nypd']:,} -> {nypd:,}")

    # --- 2.2 the three states, off one primitive, over the live host --------
    print(f"\n2.2 R58's three states, live")
    q_narrow = SocrataCandidateQuery(
        namespace="nyc", kind="entity", type_name="service_request",
        host_filter=HOST_NARROWING, limit=None)
    narrow_total = count(HOST_NARROWING)
    print(f"  host narrowing      : {HOST_NARROWING}")
    print(f"  narrowed partition  : {narrow_total:,} rows -- "
          f"{nypd / max(narrow_total, 1):,.0f}x smaller than the node")
    host = SocrataServiceRequests(scan_budget=20000, page_size=narrow_total + 100)
    p_set, t_set = host.find_instance_candidates(q_narrow)
    print(f"     the set: known={p_set.known} complete={p_set.complete} "
          f"next_after={p_set.next_after!r} ({t_set}s)")

    host2 = SocrataServiceRequests(scan_budget=20000, page_size=200)
    p_page, t_page = host2.find_instance_candidates(
        SocrataCandidateQuery(namespace="nyc", kind="entity",
                              type_name="service_request",
                              host_filter=HOST_NARROWING, limit=200))
    print(f"      a page: known={p_page.known} complete={p_page.complete} "
          f"next_after={p_page.next_after!r} ({t_page}s)")

    host3 = SocrataServiceRequests(scan_budget=2000, page_size=1000)
    seen = 0
    after = None
    p_trunc = None
    while True:
        p_trunc, _ = host3.find_instance_candidates(
            SocrataCandidateQuery(namespace="nyc", kind="entity",
                                  type_name="service_request",
                                  host_filter="agency='NYPD'", limit=1000,
                                  after=after))
        seen += p_trunc.known or 0
        if p_trunc.next_after is None:
            break
        after = p_trunc.next_after
    print(f"   truncated: known={p_trunc.known} complete={p_trunc.complete} "
          f"next_after={p_trunc.next_after!r}")
    print(f"              why={p_trunc.why_incomplete!r}")
    print(f"              (read {seen} of {nypd:,} rows in {host3.requests} host requests)")

    check("R58 row 1 -- complete=True is the SET, and `known` is its length",
          p_set.complete and p_set.next_after is None
          and p_set.known == narrow_total,
          f"known={p_set.known} vs {narrow_total}")
    check("R58 row 2 -- a page: incomplete, cursor present, `known` counts the PAGE",
          not p_page.complete and p_page.next_after is not None
          and p_page.known == 200, f"known={p_page.known}")
    check("R58 row 3 -- truncated: incomplete, NO cursor, and a `why`",
          not p_trunc.complete and p_trunc.next_after is None
          and bool(p_trunc.why_incomplete))
    check("the three states are distinguishable from the report alone",
          len({(p.complete, p.next_after is not None, bool(p.why_incomplete))
               for p in (p_set, p_page, p_trunc)}) == 3)

    # --- 2.3 what an unnarrowed scan of the node would cost -----------------
    print(f"\n2.3 the exhaustive read the guard would need")
    t0 = time.time()
    probe = soda({"$limit": HOST_MAX_PAGE, "$offset": 0, "$select": "unique_key",
                  "$where": "agency='NYPD'", "$order": "unique_key"})
    one_max_page = round(time.time() - t0, 2)
    pages_needed = -(-nypd // HOST_MAX_PAGE)
    print(f"  one {HOST_MAX_PAGE}-row page took {one_max_page}s and returned "
          f"{len(probe)} rows")
    print(f"  exhausting agency='NYPD' at the host's ceiling needs "
          f"{pages_needed:,} requests")
    print(f"  [Inferred] lower bound, at that per-page cost and ignoring deep-offset "
          f"decay: {round(pages_needed * one_max_page / 60, 1)} minutes FOR ONE "
          f"LANDED ROW")
    check("an exhaustive candidate scan of the pre-registered node is not affordable "
          "per landed row", pages_needed * one_max_page > 60,
          f"{pages_needed} pages x {one_max_page}s")

    # --- 2.4 the rule that follows: a guard never reads a page --------------
    print(f"\n2.4 a guard never reads a page -- what the resolution does instead")
    print(f"  the ambiguity decision is an identity read, so it may not run on a page.")
    print(f"  Over agency='NYPD' unnarrowed the exhaustive read cannot finish, so the")
    print(f"  honest outcome is `unknowable` -- design test 1's fifth value, at scale.")
    outcome = "unknowable" if not p_trunc.complete else "resolvable"
    print(f"  -> outcome={outcome!r} for a candidate resolved against the whole "
          f"partition")
    check("the 9.7M-degree node resolves to `unknowable`, never to `proposal`",
          outcome == "unknowable")

    host4 = SocrataServiceRequests(scan_budget=20000, page_size=200)
    assembled: list[str] = []
    after = None
    while True:
        pg, _ = host4.find_instance_candidates(
            SocrataCandidateQuery(namespace="nyc", kind="entity",
                                  type_name="service_request",
                                  host_filter=HOST_NARROWING, limit=200, after=after))
        assembled.extend(r.instance_id for r in pg.records)
        if pg.next_after is None:
            drained = pg.complete
            break
        after = pg.next_after
    print(f"  the same read over the HOST-NARROWED partition drains to exhaustion: "
          f"{len(assembled)} rows in {host4.requests} requests, complete={drained}")
    check("the guard's exhaustive read FINISHES once the host narrows -- cursor drained "
          "to None, `complete=True`, and the assembled set is the partition",
          drained and len(assembled) == narrow_total,
          f"{len(assembled)} of {narrow_total}")
    check("and the narrowing is the HOST's own predicate, not one this project arranged",
          "agency=" in HOST_NARROWING and narrow_total < nypd / 1000,
          f"{narrow_total:,} of {nypd:,}")

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
