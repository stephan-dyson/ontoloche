# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c7_usage.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C7 -- ``usage`` (6). Mechanism 3: added once, never retired.

Also the sensor for the venture's core bet. Every assertion here is about refusing to
turn "we did not look" into a number.
"""

from __future__ import annotations
import pytest
from datetime import timedelta
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


NO_COUNTER = {"counts_usage": "this store keeps no usage counter at all"}

NO_TIMESTAMPS = {"timestamps_usage": "work_link_types has no last_used_at column"}

async def test_c7_01_a_backend_that_does_not_count_reports_none_not_zero(adapter, make_registry):
    setup = await make_registry(adapter)
    await seed(setup, "blocks", definition="this work item blocks that one")

    blind = await make_registry(AsyncDegradedAdapter(adapter, counts_usage=False, why=NO_COUNTER))
    report = await blind.usage("blocks")
    assert report.count is None, "0 would say 'nobody uses this', which we did not check"
    assert report.count != 0
    assert report.why == NO_COUNTER["counts_usage"]
    assert report.complete is False

@pytest.mark.requires_capability("counts_usage")
async def test_c7_02_unknown_timestamps_are_none_not_never(adapter, make_registry):
    setup = await make_registry(adapter)
    await seed(setup, "blocks", definition="this work item blocks that one")
    await setup.record_use("blocks")

    half_blind = await make_registry(AsyncDegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    report = await half_blind.usage("blocks")
    assert report.count == 1
    assert report.last_seen is None
    assert report.first_seen is None
    assert report.why == NO_TIMESTAMPS["timestamps_usage"]

async def test_c7_03_an_unknown_last_seen_makes_orphaned_none_never_false(adapter, make_registry):
    """Contortion 2's test. A bare counter cannot distinguish a type used once in April
    from one used yesterday, so False here would be a claim the data does not support --
    and it is the claim that lets a dead type sit in a vocabulary forever."""
    setup = await make_registry(adapter)
    await seed(setup, "blocks", definition="this work item blocks that one")
    await setup.record_use("blocks")

    half_blind = await make_registry(AsyncDegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    report = await half_blind.usage("blocks")
    assert report.orphaned is None
    assert report.orphaned is not False
    assert report.why

@pytest.mark.requires_capability("timestamps_usage", "counts_usage")
async def test_c7_04_an_active_type_unused_past_the_window_is_orphaned(registry, clock):
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.record_use("watch")
    assert (await registry.usage("watch")).orphaned is False

    clock.advance(timedelta(days=120))
    report = await registry.usage("watch")
    assert report.orphaned is True
    assert report.window == timedelta(days=90), "the window it was judged against is reported"
    assert report.last_seen is not None

@pytest.mark.requires_capability("counts_usage")
async def test_c7_05_nothing_recorded_and_not_counted_are_different_reports(adapter, make_registry):
    setup = await make_registry(adapter)
    await seed(setup, "blocks", definition="this work item blocks that one")

    nothing_recorded = await setup.usage("blocks")
    assert nothing_recorded.count == 0
    assert nothing_recorded.orphaned is True

    blind = await make_registry(AsyncDegradedAdapter(adapter, counts_usage=False, why=NO_COUNTER))
    not_counted = await blind.usage("blocks")
    assert not_counted.count is None
    assert not_counted.orphaned is None

    assert nothing_recorded != not_counted, (
        "'nothing has happened' and 'we did not look' must not collapse into one answer"
    )

async def test_c7_06_record_use_on_a_non_counting_backend_is_a_no_op_that_says_so(
    adapter, make_registry
):
    setup = await make_registry(adapter)
    await seed(setup, "blocks", definition="this work item blocks that one")

    blind = await make_registry(AsyncDegradedAdapter(adapter, counts_usage=False, why=NO_COUNTER))
    await blind.record_use("blocks")
    await blind.record_use("blocks")

    report = await blind.usage("blocks")
    assert report.count is None
    assert report.why == NO_COUNTER["counts_usage"]
    # And nothing leaked into the underlying store either.
    assert await adapter.get_usage("default", "entity", "blocks") is None
