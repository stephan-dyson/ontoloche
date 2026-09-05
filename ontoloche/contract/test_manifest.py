"""Suite bookkeeping -- not one of the 347.

PACKAGE.md 6.2 enumerates 347 contract tests in twenty groups and calls the
enumeration *the coverage floor, not a budget*. This checks the floor is actually on the
floor: every enumerated id exists as a test function, and nothing has quietly gone
missing while the suite was being written.

The number of collected pytest items is larger than 150 -- both because the suite is
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
    2: 6,
    3: 16,
    4: 16,
    5: 14,
    6: 9,
    7: 7,
    8: 6,
    9: 36,
    10: 21,
    11: 5,
    12: 23,
    13: 5,
    14: 7,
    15: 13,
    16: 7,
    17: 53,
    18: 10,
    19: 96,
}
TOTAL = 373

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


def test_the_kill_row_is_guarded_at_every_caller_and_in_every_state():
    """Not one of the ids -- suite bookkeeping, and the gate row 4c was told to build.

    `ROADMAP.md`'s kill row -- *"a capability predicate gets merged as a duplicate ->
    Stop. This is the failure that destroys meaning"* -- **tripped three times in one
    day**, and the supervisor's ruling after the third was explicit: *"the fix owed is a
    checker, not a fourth patch."* ``docs/tools/check_merge_guard.py`` is that checker,
    and it runs here for the reason ``check_spec_drift.py`` does: a guard that is only
    verified when somebody remembers to run a script is a guard nobody is verifying.

    It has two halves and neither is sufficient alone. **Part A** discovers, from
    ``registry.py``'s own AST, every function that writes a ``successor`` or an
    ``aliases`` onto a stored record -- the two fields that change what a name RESOLVES
    to -- and fails on any it has not been told about, because whether a caller can
    collapse two identities is a person's judgement and has to be written down. **Part
    B** drives every collapsing caller through every state a predicate extent pair can
    be in -- known-different, known-equal, empty, unknowable, kind-mismatch -- on every
    leg, and checks the guard's answer for each.

    **Part A found the kill row's fourth trip on its first run**, in `import_types`.

    Skipped rather than failed when the checked-in tools are not on disk, since an
    installed wheel does not ship ``docs/``.
    """
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    checker = root / "docs" / "tools" / "check_merge_guard.py"
    if not checker.exists():  # pragma: no cover - an installed wheel has no docs/
        import pytest

        pytest.skip("PENDING -- docs/tools/check_merge_guard.py is not in this install")

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


def test_the_document_and_this_module_agree_group_by_group():
    """Not one of the 150 -- suite bookkeeping, like the id census above.

    ``PACKAGE.md`` 6.2 states a count per group in each group's header and then
    enumerates the ids in a table beneath it. Row 3e's third adversarial round found the
    headers summing to **142** over tables enumerating **145**, with this module's
    ``EXPECTED_PER_GROUP`` agreeing with the tables -- a number in prose that nothing
    derives, which is the fourth time this repository has been bitten by exactly that.

    So both halves of 6.2 are now held against this module: the header count, and the
    number of enumerated rows. Skipped rather than failed outside a source checkout,
    since an installed wheel ships no ``docs/``.
    """
    root = Path(__file__).resolve().parents[2]
    spec = root / "docs" / "specs" / "PACKAGE.md"
    if not spec.exists():  # pragma: no cover - an installed wheel has no docs/
        pytest.skip("PENDING -- docs/specs/PACKAGE.md is not in this install")

    text = spec.read_text(encoding="utf-8")
    headers = {
        int(group): int(count)
        for group, count in re.findall(r"^\*\*C(\d+) [^(]*\((\d+)\)\.", text, re.M)
    }
    enumerated: dict[int, set[str]] = {}
    for full, group in re.findall(r"^\| (C(\d+)-\d+) \|", text, re.M):
        enumerated.setdefault(int(group), set()).add(full)
    rows = {group: len(ids) for group, ids in enumerated.items()}

    assert headers == EXPECTED_PER_GROUP, (
        "PACKAGE.md 6.2's group HEADERS disagree with this module: "
        f"{sorted(set(headers.items()) ^ set(EXPECTED_PER_GROUP.items()))}"
    )
    assert rows == EXPECTED_PER_GROUP, (
        "PACKAGE.md 6.2's enumerated ROWS disagree with this module: "
        f"{sorted(set(rows.items()) ^ set(EXPECTED_PER_GROUP.items()))}"
    )
    assert sum(rows.values()) == TOTAL


@pytest.mark.nonbinding
def test_stacked_requires_capability_markers_are_all_honoured():
    """Not one of the ids -- harness bookkeeping, and it exists because a RED on main.

    `conftest`'s capability gate used `get_closest_marker("requires_capability")`, which
    returns exactly **one** mark. So a test that stacked two decorators --
    `@NEEDS_ATTRIBUTES` above `@requires_capability("stores_edges")` -- was skipped for
    edges and **run** with `stores_attributes=False`, in a configuration where its
    fixture cannot exist. Three ids did that; `check_capability_matrix.py` went from
    every configuration conformant to **five** that could not pass; and nothing between
    the decorator and the run said a declaration had been dropped.

    **A declaration this harness silently ignores is the shape the register refuses
    everywhere else**, and the matrix caught it only as *"five configurations fail"* --
    true, and three steps from the cause. This asserts the cause directly, so the next
    regression names itself.
    """
    from . import conftest as sync_conftest

    source = Path(sync_conftest.__file__).read_text(encoding="utf-8")
    assert "iter_markers(\"requires_capability\")" in source, (
        "the capability gate must honour EVERY declaration, not the closest one"
    )
    assert "get_closest_marker(\"requires_capability\")" not in source

    # The async conftest is NOT generated by `tools/unasync.py`, so it is the call site
    # a fix reaches last -- which is this project's most-repeated defect.
    aio = Path(sync_conftest.__file__).parents[1] / "aio" / "contract" / "conftest.py"
    if aio.exists():
        mirror = aio.read_text(encoding="utf-8")
        assert "iter_markers(\"requires_capability\")" in mirror, (
            "a fix is only as good as its application: the async mirror keeps its own "
            "conftest and this one was fixed by hand"
        )
        assert "get_closest_marker(\"requires_capability\")" not in mirror
