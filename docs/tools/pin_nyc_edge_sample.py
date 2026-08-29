"""Freeze UC3's cross-agency join into a checked-in fixture. Run once; read forever.

`C18-05` … `C18-08` walk the three NYC datasets through the **shipped** edge store, and
a contract test may not depend on a network. `edges_nyc_probe.py` (row #4's design test)
went live to the SODA API; this script runs the same queries once and writes what they
returned to `open_ontology/contract/fixtures/nyc_edge_sample.json`, with the dataset
ids, the `data_updated_at` of each source and the retrieval date on the row -- so the
fixture carries its own provenance and `EdgeProvenance.source_version` has something
true to say.

**Why pinned rather than fetched.** `2A-RUN.md` §8.4 and `EDGES.md` §11.3 record the
same defect twice: a SODA query with a `limit` and no `order` returns an arbitrary
window, and two runs of the probe printed different numbers (73 edges / max 29, then
62 / max 16). *A design test whose numbers move between runs is not a design test.* The
`order=unique_key` pin fixed that for the probe; a checked-in fixture fixes it for the
suite, and also makes the suite runnable on a machine with no network, which is what
`--pyargs open_ontology.contract` promises a third-party backend author.

    py docs/tools/pin_nyc_edge_sample.py

Re-running it is how the fixture is refreshed, and the numbers in `4B-RUN.md` are the
ones the checked-in file holds.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "open_ontology" / "contract" / "fixtures" / "nyc_edge_sample.json"

#: `USE-CASES.md` and `3C-VALIDATION.md` §1 fix these three, and they are kept so the
#: test is reproducible. A = DPR street trees, B = 311 service requests, C = DOT
#: parking meters.
A, B, C = "uvpi-gqnh", "erm2-nwe9", "693u-uax6"
BOROUGH_FIELD = {A: "boroname", B: "borough", C: "borough"}
NAMESPACE = {A: "dpr", B: "oti_311", C: "dot"}

#: The same twenty-five the probe pinned. `order` is not optional: without it the API
#: returns an arbitrary window and the counts move between runs.
COMPLAINT_LIMIT = 25


def soda(dataset: str, **params: str) -> list:
    url = f"https://data.cityofnewyork.us/resource/{dataset}.json"
    query = urllib.parse.urlencode({f"${k}": v for k, v in params.items()})
    with urllib.request.urlopen(f"{url}?{query}", timeout=60) as handle:
        return json.loads(handle.read().decode())


def metadata(dataset: str) -> dict:
    url = f"https://data.cityofnewyork.us/api/views/{dataset}.json"
    with urllib.request.urlopen(url, timeout=60) as handle:
        raw = json.loads(handle.read().decode())
    updated = raw.get("rowsUpdatedAt")
    return {
        "id": dataset,
        "name": raw.get("name"),
        "namespace": NAMESPACE[dataset],
        "data_updated_at": (
            datetime.fromtimestamp(updated, tz=UTC).date().isoformat() if updated else None
        ),
    }


def main() -> int:
    out: dict = {
        "retrieved_at": datetime.now(UTC).isoformat(),
        "note": (
            "Pinned by docs/tools/pin_nyc_edge_sample.py. Public NYC Open Data only. "
            "The borough value sets are the whole distinct set per dataset; the join "
            "sample is the first 25 tree complaints by unique_key that carry a BBL, "
            "and every census tree on those tax lots."
        ),
        "datasets": {},
        "boroughs": {},
    }
    for dataset in (A, B, C):
        out["datasets"][dataset] = metadata(dataset)
        field = BOROUGH_FIELD[dataset]
        rows = soda(dataset, select=field, group=field, limit="50")
        out["boroughs"][dataset] = sorted(
            r[field] for r in rows if r.get(field) not in (None, "")
        )

    complaints = soda(
        B,
        select="unique_key,complaint_type,bbl,borough,created_date",
        where="complaint_type like '%Tree%' AND bbl IS NOT NULL",
        order="unique_key",
        limit=str(COMPLAINT_LIMIT),
    )
    bbls = sorted({c["bbl"] for c in complaints if c.get("bbl")})
    quoted = ",".join(f"'{b}'" for b in bbls)
    trees = soda(
        A,
        select="tree_id,bbl,boroname,spc_common,status",
        where=f"bbl in ({quoted})",
        order="tree_id",
        limit="400",
    )
    out["complaints"] = complaints
    out["trees"] = trees

    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  boroughs: " + "; ".join(f"{d}={len(v)}" for d, v in out['boroughs'].items()))
    print(f"  {len(complaints)} complaints over {len(bbls)} distinct BBLs")
    print(f"  {len(trees)} census trees on those lots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
