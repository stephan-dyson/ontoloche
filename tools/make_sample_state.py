# -*- coding: utf-8 -*-
"""Regenerate the 400-row public CMS sample the contract suite's C13 group runs on.

PACKAGE.md 8.4 records the gap this closes: the 400-row `sample_state.csv` that Phase
0.5 actually used was described in the ground truth but never checked in, and
`docs/tools/make_sample.py` regenerates a *different* file (a seeded 300-row national
reservoir sample). Standing constraint 0 argues for fixing that: the data is public CMS
data, and a test that cannot be run on public data is a test this project does not run.

What the sample is, per `docs/findings/0.5-ground-truth-PREREGISTERED.md`: **the first 400
Montana rows, contiguous** -- chosen to resemble what a regional office actually exports
(repeat facilities, multiple surveys each) rather than a random national sample, which
gave 298 distinct facilities in 300 rows and would not test entity resolution at all.

Usage::

    python tools/make_sample_state.py --source nh_full.csv
    python tools/make_sample_state.py --download        # fetches the public file first

The source file is 165 MB and is deliberately NOT in the repository (.gitignore); the
400-row derivative is, because it is the fixture.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import urllib.request
from pathlib import Path

csv.field_size_limit(10_000_000)

# CMS Provider Data Catalog, dataset r5ix-sfxw, distribution downloadURL as returned by
# the metastore API on 2026-08-28. The landing page is
# https://data.cms.gov/provider-data/dataset/r5ix-sfxw
SOURCE_URL = (
    "https://data.cms.gov/provider-data/sites/default/files/resources/"
    "600f5d1861dd2e0280b2e961e8396245_1786724148/NH_HealthCitations_Aug2026.csv"
)
SOURCE_BYTES = 165_336_194  # the size the ground truth records for the file it used

STATE = "MT"
ROWS = 400

DEFAULT_OUT = (
    Path(__file__).resolve().parent.parent
    / "open_ontology"
    / "contract"
    / "fixtures"
    / "cms_sample_400.csv"
)


def download(destination: Path) -> Path:
    print(f"downloading {SOURCE_URL}\n  -> {destination}", file=sys.stderr)
    urllib.request.urlretrieve(SOURCE_URL, destination)
    return destination


def cut(source: Path, out: Path, *, state: str = STATE, rows: int = ROWS) -> dict:
    with source.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        state_index = header.index("State")
        picked: list[list[str]] = []
        for row in reader:
            if row[state_index] == state:
                picked.append(row)
                if len(picked) == rows:
                    break

    if len(picked) != rows:
        raise SystemExit(f"only found {len(picked)} {state} rows; expected {rows}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(picked)

    index = {name: i for i, name in enumerate(header)}
    ccns = {r[index["CMS Certification Number (CCN)"]] for r in picked}
    surveys = {
        (
            r[index["CMS Certification Number (CCN)"]],
            r[index["Survey Date"]],
            r[index["Survey Type"]],
        )
        for r in picked
    }
    tags = {r[index["Deficiency Tag Number"]] for r in picked}
    statuses = {r[index["Deficiency Corrected"]] for r in picked}
    severities = {r[index["Scope Severity Code"]] for r in picked}

    return {
        "rows": len(picked),
        "facility": len(ccns),
        "survey": len(surveys),
        "citation": len(picked),
        "deficiency_tag": len(tags),
        "deficiency_corrected_status": len(statuses),
        "scope_severity_code": len(severities),
        "severity_codes": sorted(severities),
        "bytes": out.stat().st_size,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("nh_full.csv"))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--download", action="store_true", help="fetch the public file first")
    args = parser.parse_args()

    if args.download or not args.source.exists():
        if not args.download:
            raise SystemExit(
                f"{args.source} not found. Re-run with --download to fetch the public file "
                f"({SOURCE_BYTES:,} bytes)."
            )
        download(args.source)

    size = args.source.stat().st_size
    if size != SOURCE_BYTES:
        print(
            f"NOTE: source is {size:,} bytes; the ground truth was cut from a file of "
            f"{SOURCE_BYTES:,} bytes. CMS republishes monthly, so the counts below may "
            f"no longer match docs/findings/0.5-ground-truth-PREREGISTERED.md.",
            file=sys.stderr,
        )

    facts = cut(args.source, args.out)
    width = max(len(k) for k in facts)
    for key, value in facts.items():
        print(f"{key:<{width}}  {value}")


if __name__ == "__main__":
    main()
