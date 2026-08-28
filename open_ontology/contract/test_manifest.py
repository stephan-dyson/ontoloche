"""Suite bookkeeping -- not one of the 109.

PACKAGE.md 6.2 enumerates 109 contract tests in seventeen groups and calls the
enumeration *the coverage floor, not a budget*. This checks the floor is actually on the
floor: every enumerated id exists as a test function, and nothing has quietly gone
missing while the suite was being written.

The number of collected pytest items is larger than 109 -- both because the suite is
parametrised over backends and because C4-09 is parametrised over malformed names.
"""

from __future__ import annotations

import re
from pathlib import Path

#: PACKAGE.md 6.2, group by group.
EXPECTED_PER_GROUP = {
    0: 6,
    1: 8,
    2: 5,
    3: 9,
    4: 9,
    5: 11,
    6: 6,
    7: 6,
    8: 5,
    9: 6,
    10: 8,
    11: 4,
    12: 4,
    13: 5,
    14: 7,
    15: 6,
    16: 4,
}
TOTAL = 109

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
