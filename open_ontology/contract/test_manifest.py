"""Suite bookkeeping -- not one of the 145.

PACKAGE.md 6.2 enumerates 145 contract tests in seventeen groups and calls the
enumeration *the coverage floor, not a budget*. This checks the floor is actually on the
floor: every enumerated id exists as a test function, and nothing has quietly gone
missing while the suite was being written.

The number of collected pytest items is larger than 145 -- both because the suite is
parametrised over backends and because C4-09 is parametrised over malformed names.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: PACKAGE.md 6.2, group by group.
EXPECTED_PER_GROUP = {
    0: 14,
    1: 9,
    2: 5,
    3: 13,
    4: 10,
    5: 12,
    6: 7,
    7: 7,
    8: 6,
    9: 15,
    10: 8,
    11: 5,
    12: 5,
    13: 5,
    14: 7,
    15: 12,
    16: 5,
}
TOTAL = 145

_TEST_NAME = re.compile(r"^def (test_c(\d+)_(\d+)_\w+)", re.M)


def implemented_ids() -> dict[str, str]:
    """``{"C5-03": "test_c5_03_the_severity_case_verbatim"}`` over the whole suite."""
    found: dict[str, str] = {}
    for path in sorted(Path(__file__).resolve().parent.glob("test_c*.py")):
        source = path.read_text(encoding="utf-8")
        for function, group, index in _TEST_NAME.findall(source):
            found[f"C{int(group)}-{int(index):02d}"] = function
    return found


def test_the_suite_implements_every_enumerated_contract_id():
    found = implemented_ids()

    expected = {
        f"C{group}-{index:02d}"
        for group, count in EXPECTED_PER_GROUP.items()
        for index in range(1, count + 1)
    }
    assert sum(EXPECTED_PER_GROUP.values()) == TOTAL

    missing = sorted(expected - set(found))
    extra = sorted(set(found) - expected)
    assert not missing, f"contract ids with no test: {missing}"
    assert not extra, f"test functions claiming ids PACKAGE.md 6.2 does not enumerate: {extra}"
    assert len(found) == TOTAL


def test_the_spec_still_describes_the_code():
    """Not one of the 115 -- suite bookkeeping, like the id census above.

    Six consecutive adversarial review rounds on ``docs/specs/INTERFACE.md`` each found
    at least one defect of the same family: a printed data shape or signature that had
    drifted from this implementation. Each was found by a reader comparing two files by
    eye, and each had survived earlier readers doing the same. ``check_spec_drift.py``
    does it mechanically, and found two more the moment it was written
    (``Provenance.history_why`` and ``TypeListing.excluded_unknown``, both recorded as
    deviations in INTERFACE.md 11 and both missing from the shapes it prints).

    Running it here means the spec cannot drift from the code without the suite saying
    so -- the same move as ``test_generated_matches_source.py`` makes for the async
    mirror. Skipped rather than failed when the checked-in spec is not on disk, since an
    installed wheel does not ship ``docs/``.
    """
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    checker = root / "docs" / "tools" / "check_spec_drift.py"
    if not checker.exists():  # pragma: no cover - an installed wheel has no docs/
        import pytest

        pytest.skip("PENDING -- docs/tools/check_spec_drift.py is not in this install")

    done = subprocess.run(
        [sys.executable, str(checker)], capture_output=True, text=True, cwd=str(root)
    )
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.mark.nonbinding
def test_every_optional_capability_can_be_declined_alone():
    """Not one of the 119 -- suite bookkeeping, and `nonbinding` on purpose.

    `PACKAGE.md` 3.2's claim -- *"every other flag may be False and the backend can
    still be conformant"* -- was false for **six of the eight** optional capabilities
    when row 3c first measured it, and had been for four deliverables. It is now
    checked: `docs/tools/check_capability_matrix.py` runs the whole suite against nine
    degraded configurations and reports a table.

    **`nonbinding`, because it runs the suite inside the suite.** A third-party backend
    running `--adapter` should not pay for nine extra full runs, and the claim it checks
    is about *this repository's* reference backend, not theirs. It is also skipped
    outside a source checkout, since an installed wheel ships no `docs/`.
    """
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    checker = root / "docs" / "tools" / "check_capability_matrix.py"
    if not checker.exists():  # pragma: no cover - an installed wheel has no docs/
        pytest.skip("PENDING -- docs/tools/check_capability_matrix.py is not in this install")

    done = subprocess.run(
        [sys.executable, str(checker)], capture_output=True, text=True, cwd=str(root)
    )
    assert done.returncode == 0, done.stdout + done.stderr
