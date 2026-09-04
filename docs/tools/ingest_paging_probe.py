# -*- coding: utf-8 -*-
"""Design test 2 for `docs/specs/INGEST.md` v0 -- **paging under load (R58)**, driven
against the live NYC 311 dataset ``erm2-nwe9`` and its 9.7-million-row NYPD partition.

**What R58 requires and what this measures.** On a page, ``known`` counts what the
report materialised, ``complete`` is about the SET, and a cursor says whether there is
more -- three states, one rule, and **a guard never reads a page**. ``erm2-nwe9`` with
``agency='NYPD'`` is the pre-registered case (R58).

**AMENDED BY ROUND 1 (finding M1).** Section 2.4 used to compute
``outcome = "unknowable" if not page.complete else ...`` -- a restatement of the check
three lines above it -- and **called no resolver at all**, so a rule-3-5-violating
resolver over the same truncated page left it printing ``10/10 checks pass``. It now
calls the **kit's** resolver, the same one design tests 1 and 5 use, and proves the
check goes red under mutation. `INGEST.md` 3.1's "two independent routes to the fifth
outcome" is a claim about THIS section, and until this amendment it was false.

**The host here is Socrata, not a fixture.** ``$limit``/``$offset`` are the host's own
paging, so the primitive is a thin adapter over them and the cursor is opaque exactly as
R58 leaves it. Every count is fetched live and printed with the date, because
`EDGES.md` 4.2's pinned figures have already moved once.

Run: ``py docs/tools/ingest_paging_probe.py``
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_probe_kit import (  # noqa: E402
    Capabilities, CandidatePage, CandidateQuery, EntryDeclaration, InstanceContext,
    InstanceRecord, MatchPolicy, Vocabulary, resolve_instance,
)
from ingest_seam_probe import CHECKS, check  # noqa: E402

DATASET = "erm2-nwe9"
RESOURCE = f"https://data.cityofnewyork.us/resource/{DATASET}.json"

#: EDGES.md 4.2, [Observed] 2026-08-29 by row #4. Re-measured here; see 2.1.
PINNED_2026_08_29 = {"rows": 22294072, "nypd": 9738128}

#: Socrata's own ceiling on one response. The host's page size, not ours.
HOST_MAX_PAGE = 50000

#: The HOST's own narrowing, as a NAMED mapping (INGEST rule 2-12): each key is a column
#: `erm2-nwe9` already indexes, and `instance_filters` can therefore govern it. Round 1
#: finding M8 -- a set of names cannot govern a free-form expression.
HOST_NARROWING = {"agency": "NYPD", "complaint_type": "Illegal Fireworks",
                  "incident_zip": "11214"}

NYC_POLICY = MatchPolicy(
    match_at=0.97, propose_below=0.80, ambiguity_margin=0.03,
    why="a 311 incident address matching a held request to 0.97 is that request")


def soda(params: dict) -> list[dict]:
    url = f"{RESOURCE}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=300) as fh:
        return json.load(fh)


def count(where: str | None = None) -> int:
    params = {"$select": "count(*)"}
    if where:
        params["$where"] = where
    return int(soda(params)[0]["count"])


def as_where(host_filter: dict | None) -> str | None:
    if not host_filter:
        return None
    return " AND ".join(f"{k}='{v}'" for k, v in sorted(host_filter.items()))


class SocrataServiceRequests:
    """`erm2-nwe9` as a host-owned instance table, behind primitive 23.

    ``scan_budget`` is what an ingestion caller is willing to read for ONE landed row.
    It is the reason this test exists: a 9.7-million-row partition is not scannable per
    row, and what the primitive does when the budget runs out is the whole finding.
    """

    def __init__(self, *, scan_budget: int, page_size: int = 1000) -> None:
        self.scan_budget = scan_budget
        self.page_size = min(page_size, HOST_MAX_PAGE)
        self.requests = 0
        self.rows_read = 0
        self.last_seconds = 0.0
        self.capabilities = Capabilities(
            resolves_instances=True,
            instance_filters=frozenset({"agency", "complaint_type", "incident_zip"}))

    def get_instance(self, namespace: str, kind: str, type_name: str,
                     instance_id: str) -> InstanceRecord | None:
        rows = soda({"$where": f"unique_key='{instance_id}'", "$limit": 1})
        if not rows:
            return None
        r = rows[0]
        return InstanceRecord(namespace, "entity", type_name, r["unique_key"],
                              r.get("incident_address") or "", dict(r))

    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage:
        offset = int(q.after) if q.after is not None else 0
        want = min(q.limit or self.page_size, self.page_size)
        remaining = self.scan_budget - offset
        if remaining <= 0:
            return CandidatePage((), 0, False,
                                 f"scan budget of {self.scan_budget} rows exhausted "
                                 "against a partition this surface cannot read to the "
                                 "end", None)
        want = min(want, remaining)
        undeclared = [k for k in (q.host_filter or {})
                      if k not in self.capabilities.instance_filters]
        params = {"$limit": want, "$offset": offset, "$order": "unique_key",
                  "$select": "unique_key,complaint_type,incident_address,agency,"
                             "created_date"}
        where = as_where({k: v for k, v in (q.host_filter or {}).items()
                          if k not in undeclared})
        if where:
            params["$where"] = where
        t0 = time.time()
        rows = soda(params)
        self.last_seconds = round(time.time() - t0, 2)
        self.requests += 1
        self.rows_read += len(rows)
        records = tuple(
            InstanceRecord(q.namespace, "entity", q.type_name, r["unique_key"],
                           r.get("incident_address") or r.get("complaint_type", ""),
                           {k: v for k, v in r.items() if k != "unique_key"})
            for r in rows)
        exhausted = len(rows) < want
        budget_gone = (offset + len(rows)) >= self.scan_budget
        why = None
        if undeclared:
            why = ("host_filter keys this backend does not declare: "
                   + ", ".join(sorted(undeclared)))
        elif budget_gone and not exhausted:
            why = (f"scan budget of {self.scan_budget} rows reached in {self.requests} "
                   "host requests; the partition continues past this surface")
        return CandidatePage(
            records=records, known=len(records),
            complete=exhausted and not undeclared, why_incomplete=why,
            next_after=(str(offset + len(rows))
                        if not exhausted and not budget_gone else None))


def nyc_vocab() -> Vocabulary:
    v = Vocabulary()
    v.declare("nyc", "service_request", EntryDeclaration(policy=NYC_POLICY))
    return v


def main() -> int:
    print(f"DESIGN TEST 2 -- paging under load (R58), live against {DATASET}")
    print(f"  measured {date.today().isoformat()} at {RESOURCE}")

    # --- 2.1 the load, re-measured -----------------------------------------
    total = count()
    nypd = count("agency='NYPD'")
    print("\n2.1 the node")
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
    print("\n2.2 R58's three states, live")
    narrow_total = count(as_where(HOST_NARROWING))
    print(f"  host narrowing (NAMED keys): {HOST_NARROWING}")
    print(f"  narrowed partition  : {narrow_total:,} rows -- "
          f"{nypd / max(narrow_total, 1):,.0f}x smaller than the node")
    q_narrow = CandidateQuery(namespace="nyc", kind="entity",
                              type_name="service_request",
                              host_filter=HOST_NARROWING)
    host = SocrataServiceRequests(scan_budget=20000, page_size=narrow_total + 100)
    p_set = host.find_instance_candidates(q_narrow)
    print(f"     the set: known={p_set.known} complete={p_set.complete} "
          f"next_after={p_set.next_after!r} ({host.last_seconds}s)")
    host2 = SocrataServiceRequests(scan_budget=20000, page_size=200)
    p_page = host2.find_instance_candidates(
        CandidateQuery(namespace="nyc", kind="entity", type_name="service_request",
                       host_filter=HOST_NARROWING, limit=200))
    print(f"      a page: known={p_page.known} complete={p_page.complete} "
          f"next_after={p_page.next_after!r} ({host2.last_seconds}s)")
    host3 = SocrataServiceRequests(scan_budget=2000, page_size=1000)
    after, seen, p_trunc = None, 0, None
    while True:
        p_trunc = host3.find_instance_candidates(
            CandidateQuery(namespace="nyc", kind="entity",
                           type_name="service_request",
                           host_filter={"agency": "NYPD"}, limit=1000, after=after))
        seen += p_trunc.known or 0
        if p_trunc.next_after is None:
            break
        after = p_trunc.next_after
    print(f"   truncated: known={p_trunc.known} complete={p_trunc.complete} "
          f"next_after={p_trunc.next_after!r}")
    print(f"              why={p_trunc.why_incomplete!r}")
    print(f"              (read {seen} of {nypd:,} rows in {host3.requests} requests)")

    check("R58 row 1 -- complete=True is the SET, and `known` is its length",
          p_set.complete and p_set.next_after is None and p_set.known == narrow_total,
          f"known={p_set.known} vs {narrow_total}")
    check("R58 row 2 -- a page: incomplete, cursor present, `known` counts the PAGE",
          not p_page.complete and p_page.next_after is not None and p_page.known == 200,
          f"known={p_page.known}")
    check("R58 row 3 -- truncated: incomplete, NO cursor, and a `why`",
          not p_trunc.complete and p_trunc.next_after is None
          and bool(p_trunc.why_incomplete))
    check("the three states are distinguishable from the report alone",
          len({(p.complete, p.next_after is not None, bool(p.why_incomplete))
               for p in (p_set, p_page, p_trunc)}) == 3)

    # --- 2.2b rule 2-7/2-10 over the LIVE host ------------------------------
    undeclared = host2.find_instance_candidates(
        CandidateQuery(namespace="nyc", kind="entity", type_name="service_request",
                       host_filter={"agency": "NYPD", "borough_president": "x"},
                       limit=10))
    print(f"\n  an undeclared host_filter key -> complete={undeclared.complete} "
          f"why={undeclared.why_incomplete!r}")
    check("rules 2-7/2-10: an undeclared key is named, and the page is incomplete "
          "rather than filtered-looking",
          not undeclared.complete
          and "borough_president" in (undeclared.why_incomplete or ""))

    # --- 2.3 what an unnarrowed scan of the node would cost -----------------
    print("\n2.3 the exhaustive read the guard would need")
    t0 = time.time()
    probe = soda({"$limit": HOST_MAX_PAGE, "$offset": 0, "$select": "unique_key",
                  "$where": "agency='NYPD'", "$order": "unique_key"})
    one_max_page = round(time.time() - t0, 2)
    pages_needed = -(-nypd // HOST_MAX_PAGE)
    minutes = pages_needed * one_max_page / 60
    print(f"  one {HOST_MAX_PAGE}-row page took {one_max_page}s and returned "
          f"{len(probe)} rows")
    print(f"  exhausting agency='NYPD' at the host's ceiling needs "
          f"{pages_needed:,} requests")
    print(f"  [Inferred] lower bound at that per-page cost, ignoring deep-offset decay: "
          f"MINUTES, not seconds ({minutes:.0f}) FOR ONE LANDED ROW")
    check("an exhaustive candidate scan of the pre-registered node is not affordable "
          "per landed row", minutes > 1, f"{pages_needed} pages x {one_max_page}s")

    # --- 2.4 the resolver, ACTUALLY CALLED (round 1, M1) --------------------
    print("\n2.4 the RESOLVER over the truncated partition -- round 1 finding M1")
    vocab = nyc_vocab()
    live = SocrataServiceRequests(scan_budget=2000, page_size=1000)
    sample = soda({"$where": as_where(HOST_NARROWING), "$limit": 1,
                   "$select": "incident_address"})
    landed = (sample[0].get("incident_address") or "").strip().upper()
    print(f"  landing {landed!r} against agency='NYPD', unnarrowed")
    r_trunc = resolve_instance(landed, InstanceContext(act_id="dt2"), host=live,
                               vocab=vocab, namespace="nyc",
                               type_name="service_request", tier="sonnet",
                               host_filter={"agency": "NYPD"}, page_size=1000)
    print(f"  -> outcome={r_trunc.outcome!r} complete={r_trunc.complete} "
          f"scanned={r_trunc.scanned}")
    print(f"     why={r_trunc.why_incomplete!r}")
    mut = SocrataServiceRequests(scan_budget=2000, page_size=1000)
    r_mut = resolve_instance(landed, InstanceContext(act_id="dt2"), host=mut,
                             vocab=vocab, namespace="nyc",
                             type_name="service_request", tier="sonnet",
                             host_filter={"agency": "NYPD"}, page_size=1000,
                             _mutate="rule_u_last")
    print(f"  MUTATED (Rule U last) -> outcome={r_mut.outcome!r} "
          f"complete={r_mut.complete}")
    check("2.4 the 9.7M-degree node resolves to `unknowable` -- and a RESOLVER said so, "
          "not a restatement of the page's own flag",
          r_trunc.outcome == "unknowable" and not r_trunc.complete, r_trunc.outcome)
    check("2.4 MUTATION: a rule-3-5-violating ordering returns a CONFIDENT outcome "
          "over an incomplete read of 9.7M rows -- exactly what rule 3-6 forbids -- so "
          "INGEST 3.1's second route to the fifth outcome is real this time",
          r_mut.outcome not in ("unknowable", "not_an_instance")
          and not r_mut.complete,
          f"{r_mut.outcome} complete={r_mut.complete}")

    # --- 2.5 and the narrowed partition DOES resolve ------------------------
    print("\n2.5 the same read, once the HOST narrows")
    narrow_host = SocrataServiceRequests(scan_budget=20000, page_size=200)
    r_ok = resolve_instance(landed, InstanceContext(act_id="dt2"), host=narrow_host,
                            vocab=vocab, namespace="nyc",
                            type_name="service_request", tier="sonnet",
                            host_filter=HOST_NARROWING, page_size=200)
    print(f"  -> outcome={r_ok.outcome!r} scanned={r_ok.scanned} "
          f"complete={r_ok.complete} in {narrow_host.requests} host requests")
    print(f"     warnings={r_ok.warnings}")
    check("2.5 the guard's exhaustive read FINISHES once the host narrows, and the "
          "answer is a real outcome rather than `unknowable`",
          r_ok.complete and r_ok.outcome in ("existing", "ambiguous"),
          f"{r_ok.outcome} / scanned={r_ok.scanned}")
    check("2.5 rule 2-13: and it says which keys narrowed it",
          any(w.startswith("instance_narrowed_proposal:") for w in r_ok.warnings),
          str(r_ok.warnings))
    check("2.5 the narrowing is the HOST's own predicate, not one this project arranged",
          narrow_total < nypd / 1000, f"{narrow_total:,} of {nypd:,}")

    print("\n" + "=" * 78)
    failed = [c for c in CHECKS if not c[1]]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} checks pass")
    for label, ok, detail in failed:
        print(f"  FAILED: {label} -- {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
