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
import pytest
from datetime import timedelta
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


@pytest.mark.requires_capability("indexes_membership")
async def test_c6_01_any_filter_that_hid_rows_makes_the_listing_incomplete(registry):
    await seed(registry, "facility", definition="a nursing home")
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded", retired_by="user:sd")

    default = await registry.list_types()
    # A store at version 4 ships one seeded family, `default:edge:equivalent_to`
    # (EDGES.md 3.1, ruling R7), so a census of a fresh store counts it. Listed
    # rather than filtered out of the assertion: a census that hid a row would stop
    # being a census, which is this whole group's subject.
    assert [t.name for t in default.types] == ["equivalent_to", "facility"]
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
    # Two seeded here plus the one the store ships -- EDGES.md 3.1.
    assert listing.known == 3 == len(listing.types)

    blind = await make_registry(AsyncDegradedAdapter(adapter, pages_countable=False))
    uncountable = await blind.list_types(include_retired=True, status=None, namespace=None)
    assert uncountable.known is None, "None, not 0 -- 0 means 'we counted and found none'"
    assert uncountable.complete is False
    assert uncountable.why_incomplete

@pytest.mark.requires_capability("indexes_membership")
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
    # A store at version 4 ships one seeded family, `default:edge:equivalent_to`
    # (EDGES.md 3.1, ruling R7), so a census of a fresh store counts it. Listed
    # rather than filtered out of the assertion: a census that hid a row would stop
    # being a census, which is this whole group's subject.
    assert sorted(t.name for t in census.types) == [
        "equivalent_to",
        "facility",
        "watch",
    ]
    assert census.known == 3

@pytest.mark.requires_capability("counts_usage")
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
    # The seeded family has never been recorded either, so it is orphaned too --
    # which is the true answer about a store nobody has written an edge into yet.
    assert [t.name for t in listing.types] == ["equivalent_to", "survey"]
    assert listing.excluded_unknown == 1, (
        "an unknown orphan state is excluded from both answers and counted, not folded "
        "into whichever answer the caller asked for"
    )
    assert listing.complete is False

@pytest.mark.requires_capability("stores_proposals")
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
    # The seeded family asserts no domain semantic and carries its own evidence
    # (ruling R7), so it belongs on the clean side -- which is the assertion that
    # would catch a seed that quietly arrived unverified.
    assert [t.name for t in clean.types] == ["equivalent_to", "facility"]
    assert flagged.complete is False and clean.complete is False

async def test_c6_07_the_census_spans_namespaces_and_a_scoped_listing_says_it_did_not(registry):
    """``list_types`` is the only call in INTERFACE.md 5 whose ``namespace`` may be
    ``None``, so it is the only way a reader sees a word that two publishers scoped
    apart. Added by row 3c after UC3; see docs/findings/3C-VALIDATION.md.

    Mechanism 2, across namespaces: if the city-wide census does not span them, nobody
    can find out that ``status`` is already taken three times over -- and a scoped
    listing that reported ``complete=True`` would say the opposite of the truth.
    """
    await seed(registry, "status", kind="value_set", namespace="dpr",
         definition="whether a street tree is alive, dead, or a stump")
    await seed(registry, "status", kind="value_set", namespace="oti_311",
         definition="where a 311 service request is in its workflow")
    await seed(registry, "status", kind="value_set", namespace="dot",
         definition="whether a parking meter is in service")

    census = await registry.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True and census.why_incomplete is None
    assert sorted(t.namespace for t in census.types) == [
        "default",  # the seeded family -- EDGES.md 3.1
        "dot",
        "dpr",
        "oti_311",
    ]
    assert census.known == 4
    assert len({t.definition for t in census.types}) == 4, "three words, three meanings"

    scoped = await registry.list_types(include_retired=True, status=None, namespace="dot")
    assert [t.namespace for t in scoped.types] == ["dot"]
    assert scoped.complete is False, "a scoped listing hid two rows and must say so"
    assert scoped.why_incomplete and "namespace" in scoped.why_incomplete
