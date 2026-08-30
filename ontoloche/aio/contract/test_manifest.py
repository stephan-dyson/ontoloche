"""Suite bookkeeping for the async mirror -- not one of the 115.

Two things to prove, and the second is the point of the whole deliverable:

1. every one of ``PACKAGE.md`` 6.2's 115 contract ids exists as a test function here,
   exactly as it does in the sync suite; and
2. the ids and the function names are **identical between the two suites** -- not
   equivalent, not corresponding, identical. If they were only corresponding, the
   async run would be a second suite whose agreement with the first was a claim rather
   than a fact.
"""

from __future__ import annotations

import re
from pathlib import Path

from ontoloche.contract.test_manifest import EXPECTED_PER_GROUP, TOTAL
from ontoloche.contract.test_manifest import implemented_ids as sync_implemented_ids

_TEST_NAME = re.compile(r"^(?:async )?def (test_c(\d+)_(\d+)_\w+)", re.M)


def implemented_ids() -> dict[str, str]:
    """``{"C5-03": "test_c5_03_the_severity_case_verbatim"}`` over the async suite."""
    found: dict[str, str] = {}
    for path in sorted(Path(__file__).resolve().parent.glob("test_c*.py")):
        source = path.read_text(encoding="utf-8")
        for function, group, index in _TEST_NAME.findall(source):
            found[f"C{int(group)}-{int(index):02d}"] = function
    return found


def test_the_async_suite_implements_every_enumerated_contract_id():
    found = implemented_ids()

    expected = {
        f"C{group}-{index:02d}"
        for group, count in EXPECTED_PER_GROUP.items()
        for index in range(1, count + 1)
    }
    missing = sorted(expected - set(found))
    extra = sorted(set(found) - expected)
    assert not missing, f"contract ids with no async test: {missing}"
    assert not extra, f"async tests claiming ids PACKAGE.md 6.2 does not enumerate: {extra}"
    assert len(found) == TOTAL


def test_the_async_ids_are_the_sync_ids_not_merely_equivalent_ones():
    """The binding claim of deliverable 3b: one suite, compiled twice."""
    assert implemented_ids() == sync_implemented_ids()
