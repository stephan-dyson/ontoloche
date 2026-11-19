"""Row 8d's landing snapshot: what `import_foundry` reports for the five Foundry fixtures.

8D-RUN.md §0.5 predicts that the D14 and B5 fixes leave every landing byte-identical
except where a new warning is added. This writes, for each fixture, the dry-run and the
real-run report on a fresh in-memory SQLite store (every item's kind, apiName, name,
outcome, reason, warnings and detail, plus the properties report, `looks_like`,
`unmatched` and `not_imported`) as one sorted JSON document, so two commits can be
compared with ``--compare``.

Run from the repo root::

    py docs/tools/type_surface_snapshot.py --write <file>
    py docs/tools/type_surface_snapshot.py --compare <file>

``--compare`` exits 1 and prints each differing path when the reports differ.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ontoloche import Registry  # noqa: E402
from ontoloche.backends.sqlite import SQLiteAdapter  # noqa: E402
from ontoloche.contract._support import foundry_fixture  # noqa: E402

FIXTURES = ("faux_employee", "faux_legacy", "uc2_cms", "uc3_nyc", "edge_cases")


def _report(report) -> dict:
    return {
        "items": [
            {
                "kind": i.kind, "api_name": i.api_name, "name": i.name,
                "outcome": i.outcome, "reason": i.reason, "warnings": list(i.warnings),
                "detail": i.detail, "carried_properties": i.carried_properties,
            }
            for i in report.items
        ],
        "looks_like": [dataclasses.asdict(x) for x in report.looks_like],
        "unmatched": report.unmatched,
        "not_imported": report.not_imported,
        "properties": report.properties,
    }


def snapshot() -> dict:
    out = {}
    for name in FIXTURES:
        for dry in (True, False):
            reg = Registry(SQLiteAdapter(":memory:"))
            report = reg.import_foundry(foundry_fixture(name), dry_run=dry)
            out[f"{name}:{'dry' if dry else 'real'}"] = _report(report)
    return json.loads(json.dumps(out, sort_keys=True, default=str))


def _diff(a, b, path="") -> list[str]:
    if type(a) is not type(b):
        return [f"{path}: {a!r} -> {b!r}"]
    if isinstance(a, dict):
        found = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                found.append(f"{path}/{k}: {a.get(k, '<absent>')!r} -> {b.get(k, '<absent>')!r}")
            else:
                found += _diff(a[k], b[k], f"{path}/{k}")
        return found
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: {len(a)} entries -> {len(b)} entries"]
        found = []
        for n, (x, y) in enumerate(zip(a, b)):
            found += _diff(x, y, f"{path}[{n}]")
        return found
    return [] if a == b else [f"{path}: {a!r} -> {b!r}"]


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write")
    group.add_argument("--compare")
    args = parser.parse_args()
    now = snapshot()
    if args.write:
        Path(args.write).write_text(json.dumps(now, sort_keys=True, indent=1), encoding="utf-8")
        print(f"wrote {len(now)} reports to {args.write}")
        return 0
    before = json.loads(Path(args.compare).read_text(encoding="utf-8"))
    found = _diff(before, now)
    for line in found:
        print(line)
    print(f"{len(found)} differences across {len(now)} reports")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
