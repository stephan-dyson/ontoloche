# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c6_list_types.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C6 -- ``list_types`` (6). Mechanism 2: nobody could find the existing types."""

from __future__ import annotations
from datetime import timedelta
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


async def test_c6_01_any_filter_that_hid_rows_makes_the_listing_incomplete(registry):
    await seed(registry, "facility", definition="a nursing home")
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded", retired_by="user:sd")

    default = await registry.list_types()
    assert [t.name for t in default.types] == ["facility"]
    assert default.complete is False, (
        "include_retired=False is the default AND hides things"
    )
    assert "include_retired=False" in default.why_incomplete

    by_kind = await registry.list_types("entity", include_retired=True)
    assert by_kind.complete is False
    assert "kind" in by_kind.why_incomplete

async def test_c6_02_known_counts_the_returned_set_and_is_none_when_uncountable(
    adapter, make_registry
):
    setup = await make_registry(adapter)
    await seed(setup, "facility", definition="a nursing home")
    await seed(setup, "survey", definition="an inspection visit")

    listing = await setup.list_types(include_retired=True, status=None, namespace=None)
    assert listing.known == 2 == len(listing.types)

    blind = await make_registry(AsyncDegradedAdapter(adapter, pages_countable=False))
    uncountable = await blind.list_types(include_retired=True, status=None, namespace=None)
    assert uncountable.known is None, "None, not 0 -- 0 means 'we counted and found none'"
    assert uncountable.complete is False
    assert uncountable.why_incomplete

async def test_c6_03_the_predicate_filter_is_the_extent_read_the_other_way(registry):
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await seed(registry, "note", predicates=["commentable"])
    await seed(registry, "capture", definition="not commentable")

    listing = await registry.list_types(predicate="commentable")
    assert sorted(t.name for t in listing.types) == ["note", "task"]

    [entry] = [p for p in await registry.predicates() if p.name == "commentable"]
    assert sorted(entry.extent) == sorted(t.name for t in listing.types)

async def test_c6_04_the_true_census_is_complete(registry):
    await seed(registry, "facility", definition="a nursing home")
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded", retired_by="user:sd")

    census = await registry.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True
    assert census.why_incomplete is None
    assert sorted(t.name for t in census.types) == ["facility", "watch"]
    assert census.known == 2

async def test_c6_05_orphaned_excludes_the_unknowable_and_says_how_many(adapter, make_registry, clock):
    setup = await make_registry(adapter)
    await seed(setup, "facility", definition="a nursing home")
    await seed(setup, "survey", definition="an inspection visit")
    await setup.record_use("facility")

    half_blind = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            timestamps_usage=False,
            why={"timestamps_usage": "work_link_types has no last_used_at column"},
        )
    )
    # `facility` has been used, but without a timestamp its orphan state is unknowable;
    # `survey` has a count of zero, which IS knowable.
    assert (await half_blind.usage("facility")).orphaned is None
    assert (await half_blind.usage("survey")).orphaned is True

    listing = await half_blind.list_types(orphaned=True)
    assert [t.name for t in listing.types] == ["survey"]
    assert listing.excluded_unknown == 1, (
        "an unknown orphan state is excluded from both answers and counted, not folded "
        "into whichever answer the caller asked for"
    )
    assert listing.complete is False

async def test_c6_06_unverified_semantics_enumerates_exactly_the_carriers(registry):
    await seed(registry, "facility", definition="a nursing home")
    proposal = await registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L. Higher letters are LESS serious.",
        [],
        "ai:proposer",
        kind="value_set",
        tier="opus",
    )
    await registry.approve(proposal.id, "user:sd")

    flagged = await registry.list_types(unverified_semantics=True)
    assert [t.name for t in flagged.types] == ["scope_severity_code"]

    clean = await registry.list_types(unverified_semantics=False)
    assert [t.name for t in clean.types] == ["facility"]
    assert flagged.complete is False and clean.complete is False
