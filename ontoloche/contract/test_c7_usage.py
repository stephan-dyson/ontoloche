"""C7 -- ``usage`` (6). Mechanism 3: added once, never retired.

Also the sensor for the venture's core bet. Every assertion here is about refusing to
turn "we did not look" into a number.
"""

from __future__ import annotations

import pytest

from datetime import timedelta

from ._support import seed
from .doubles import DegradedAdapter

NO_COUNTER = {"counts_usage": "this store keeps no usage counter at all"}
NO_TIMESTAMPS = {"timestamps_usage": "work_link_types has no last_used_at column"}


def test_c7_01_a_backend_that_does_not_count_reports_none_not_zero(adapter, make_registry):
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")

    blind = make_registry(DegradedAdapter(adapter, counts_usage=False, why=NO_COUNTER))
    report = blind.usage("blocks")
    assert report.count is None, "0 would say 'nobody uses this', which we did not check"
    assert report.count != 0
    assert report.why == NO_COUNTER["counts_usage"]
    assert report.complete is False


@pytest.mark.requires_capability("counts_usage")
def test_c7_02_unknown_timestamps_are_none_not_never(adapter, make_registry):
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")
    setup.record_use("blocks")

    half_blind = make_registry(DegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    report = half_blind.usage("blocks")
    assert report.count == 1
    assert report.last_seen is None
    assert report.first_seen is None
    assert report.why == NO_TIMESTAMPS["timestamps_usage"]


def test_c7_03_an_unknown_last_seen_makes_orphaned_none_never_false(adapter, make_registry):
    """Contortion 2's test. A bare counter cannot distinguish a type used once in April
    from one used yesterday, so False here would be a claim the data does not support --
    and it is the claim that lets a dead type sit in a vocabulary forever."""
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")
    setup.record_use("blocks")

    half_blind = make_registry(DegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    report = half_blind.usage("blocks")
    assert report.orphaned is None
    assert report.orphaned is not False
    assert report.why


@pytest.mark.requires_capability("timestamps_usage", "counts_usage")
def test_c7_04_an_active_type_unused_past_the_window_is_orphaned(registry, clock):
    seed(registry, "watch", definition="a thing a user watches")
    registry.record_use("watch")
    assert registry.usage("watch").orphaned is False

    clock.advance(timedelta(days=120))
    report = registry.usage("watch")
    assert report.orphaned is True
    assert report.window == timedelta(days=90), "the window it was judged against is reported"
    assert report.last_seen is not None


@pytest.mark.requires_capability("counts_usage")
def test_c7_05_nothing_recorded_and_not_counted_are_different_reports(adapter, make_registry):
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")

    nothing_recorded = setup.usage("blocks")
    assert nothing_recorded.count == 0
    assert nothing_recorded.orphaned is True

    blind = make_registry(DegradedAdapter(adapter, counts_usage=False, why=NO_COUNTER))
    not_counted = blind.usage("blocks")
    assert not_counted.count is None
    assert not_counted.orphaned is None

    assert nothing_recorded != not_counted, (
        "'nothing has happened' and 'we did not look' must not collapse into one answer"
    )


def test_c7_06_record_use_on_a_non_counting_backend_is_a_no_op_that_says_so(
    adapter, make_registry
):
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")

    blind = make_registry(DegradedAdapter(adapter, counts_usage=False, why=NO_COUNTER))
    blind.record_use("blocks")
    blind.record_use("blocks")

    report = blind.usage("blocks")
    assert report.count is None
    assert report.why == NO_COUNTER["counts_usage"]
    # And nothing leaked into the underlying store either.
    assert adapter.get_usage("default", "entity", "blocks") is None


@pytest.mark.requires_capability("timestamps_usage", "counts_usage")
def test_c7_07_last_seen_never_moves_backwards(adapter, clock, make_registry):
    """§3.4 primitive 12 states it unconditionally: `bump_usage` *"advances `last_seen`
    to `max(last_seen, at)`"*. **Nothing tested it**, and [Observed] an adapter that
    simply overwrites instead of taking the max ran the whole suite to a clean
    conformant pass. Added by row 3c after an adversarial review round built one.

    This is **not** the G3 carve-out. G3 (§3.5) waives *serialisation under a race* --
    a lost update costs one count -- and explicitly does not waive the `max()` semantic,
    which is what stops a late or replayed write from dragging `last_seen` into the past.

    Why it matters beyond tidiness: `orphaned` is *"the sensor for the venture's core
    bet"* (INTERFACE.md 5.7), and it is computed from `last_seen < now - window`. A
    regressed `last_seen` reports a live type as dead. Out-of-order arrival is the normal
    case for both remaining fixtures -- UC2 is a 419,479-row bulk export whose
    `record_use` calls need not be in temporal order, and UC3 is dozens of agencies
    loading independently, with replays.
    """
    registry = make_registry(adapter)
    seed(registry, "facility", definition="a Medicare-certified nursing home")

    registry.record_use("facility")
    live = registry.usage("facility").last_seen
    assert live == clock.now()

    # A backfill arriving late, stamped with the time it happened, not the time it landed.
    registry.record_use("facility", at=clock.now() - timedelta(days=240))

    after = registry.usage("facility")
    assert after.last_seen == live, (
        "last_seen moved backwards: a replayed or out-of-order write dragged the "
        "orphan sensor into the past, and a live type now reads as dead"
    )
    assert after.count == 2, "the count still counts it -- only the clock is monotonic"
