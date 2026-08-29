"""Is `PACKAGE.md` §3.2's claim true? -- run it and find out.

    "Two flags are not optional. `enforces_unique_name=False` or
    `transactional=False` ⇒ non-conformant, full stop. **Every other flag may be
    `False` and the backend can still be conformant**, because the suite asserts
    honest unknowns, not values. That single rule is what lets Tenshen's one-table
    registry be a third backend."

That is the load-bearing sentence of the conformance definition, and ruling A5 makes
the suite it describes the Phase 2B gate. **[Observed] it was false for six of the
eight optional flags** when row 3c first measured it: declining any one of
`stores_events`, `stores_attributes`, `stores_aliases`, `indexes_membership`,
`counts_usage` or `timestamps_usage` -- one at a time, nothing else degraded -- failed
the suite outright, from 1 failure up to 24.

Two of those were real defects in the registry, not the suite:

* with `indexes_membership=False` every extent is empty, so two predicates with
  genuinely different members compared **equal** and the non-overridable
  `predicate_merge` refusal never fired -- ``ROADMAP.md``'s kill row, tripping on the
  declared capability shape of Tenshen's own table;
* ``cannot_record_override`` was checked *before* the four non-overridable merge
  guards, so a caller trying to acknowledge past the kill row was told the audit log
  was missing rather than that the merge was forbidden.

The rest were harness scaffolding: tests using a capability to set up a scenario about
something else. Those now carry ``@pytest.mark.requires_capability(...)`` and skip with
a reason naming the flag and quoting the backend's own ``why``.

**Why this is a script and not a paragraph.** The claim is about nine configurations
nobody runs by hand, and it was wrong for six of them for four deliverables. Now it is
measured on demand, and the answer prints as a table. Same move as
``check_spec_drift.py`` -- the check exists because the eye did not catch it.

Run: ``python docs/tools/check_capability_matrix.py`` -- exit 0 when every optional
capability can be declined alone and still conform, 1 otherwise.
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from open_ontology.adapter import CAPABILITY_FLAGS, REQUIRED_CAPABILITIES  # noqa: E402
from open_ontology.backends.sqlite import SQLiteAdapter  # noqa: E402
from open_ontology.contract import run_contract_suite  # noqa: E402
from open_ontology.contract.doubles import DegradedAdapter, WithoutAttributeStore  # noqa: E402

OPTIONAL = tuple(f for f in CAPABILITY_FLAGS if f not in REQUIRED_CAPABILITIES)
_TALLY = re.compile(r"(\d+) (passed|failed|skipped|error)")


def _fresh() -> SQLiteAdapter:
    adapter = SQLiteAdapter(":memory:")
    adapter.migrate()
    return adapter


def _run(factory) -> tuple[int, dict[str, int]]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = run_contract_suite(
            factory, args=["-q", "--no-header", "-p", "no:cacheprovider", "--tb=no"]
        )
    tally: dict[str, int] = {}
    for line in buf.getvalue().splitlines():
        if " passed" in line or " failed" in line:
            for count, what in _TALLY.findall(line):
                tally[what] = int(count)
    return code, tally


def main() -> int:
    print("PACKAGE.md 3.2 -- every OPTIONAL capability, declined one at a time.")
    print(f"required and never declinable: {', '.join(REQUIRED_CAPABILITIES)}\n")
    print(f"  {'configuration':30s} {'verdict':9s} passed  skipped  failed")

    failures: list[str] = []
    cases: list[tuple[str, object]] = [
        (f"{flag}=False", (lambda f=flag: DegradedAdapter(_fresh(), **{f: False})))
        for flag in OPTIONAL
    ]
    # The optional AttributeStore extension is a PROTOCOL, not a flag -- there is no
    # Capabilities entry a backend could set. PACKAGE.md 5.5 and ruling R2 say
    # declining it leaves a backend fully conformant, so it belongs in this matrix.
    cases.append(("no AttributeStore", lambda: WithoutAttributeStore(_fresh())))
    # Beacon finding U3: `stores_attributes=False` PLUS a declared projection -- the
    # host-owned backend that stores no arbitrary keys and owns two named ones as typed
    # columns. Not a tenth flag; a tenth SHAPE of the ninth, and the one the U3 branch
    # of C0-06 exists for. Row 3d.
    cases.append(
        (
            "stores_attributes=False +proj",
            lambda: DegradedAdapter(
                _fresh(),
                stores_attributes=False,
                attribute_projections=("primary_key", "ordered"),
            ),
        )
    )

    # EDGES.md 6.3 -- U3's shape again, one row down: a host-owned EDGE table with
    # `description` and `confidence` as real typed columns and no JSON blob. `True`
    # would silently lose arbitrary keys; `False` alone would disclaim two the backend
    # round-trips perfectly. Row 4b.
    cases.append(
        (
            "stores_edge_attributes=F +proj",
            lambda: DegradedAdapter(
                _fresh(),
                stores_edge_attributes=False,
                edge_attribute_projections=("description", "confidence"),
            ),
        )
    )

    for label, factory in cases:
        code, tally = _run(factory)
        verdict = "conformant" if code == 0 else "FAILS"
        if code != 0:
            failures.append(label)
        print(
            f"  {label:30s} {verdict:9s} {tally.get('passed', 0):6d}  "
            f"{tally.get('skipped', 0):7d}  {tally.get('failed', 0):6d}"
        )

    print()
    if failures:
        print(
            f"{len(failures)} configuration(s) cannot pass the suite: "
            + ", ".join(failures)
            + "\n\nPACKAGE.md 3.2 claims every one of these is conformant. Either the "
            "claim is wrong and 3.2 must be narrowed to name only what is verified, or "
            "the suite is using a capability as scaffolding where it is not the "
            "subject -- see the `requires_capability` marker and PACKAGE.md 8b.5."
        )
        return 1

    print(
        "Every optional capability can be declined alone and the backend still "
        "conforms. 3.2's claim holds, measured rather than asserted.\n"
        "Note what this does NOT cover: several capabilities declined AT ONCE. Ruling "
        "R12 (2026-08-29) keeps the two-flag rule and requires a COVERAGE REPORT "
        "instead -- a conformance claim without its coverage line is not a claim. "
        "Row 3d carries it, with a natively-degraded reference leg (U2)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
