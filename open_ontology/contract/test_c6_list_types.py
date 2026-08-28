"""C6 -- ``list_types`` (6). Mechanism 2: nobody could find the existing types."""

from __future__ import annotations

from datetime import timedelta

from ._support import seed
from .doubles import DegradedAdapter


def test_c6_01_any_filter_that_hid_rows_makes_the_listing_incomplete(registry):
    seed(registry, "facility", definition="a nursing home")
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded", retired_by="user:sd")

    default = registry.list_types()
    assert [t.name for t in default.types] == ["facility"]
    assert default.complete is False, (
        "include_retired=False is the default AND hides things"
    )
    assert "include_retired=False" in default.why_incomplete

    by_kind = registry.list_types("entity", include_retired=True)
    assert by_kind.complete is False
    assert "kind" in by_kind.why_incomplete


def test_c6_02_known_counts_the_returned_set_and_is_none_when_uncountable(
    adapter, make_registry
):
    setup = make_registry(adapter)
    seed(setup, "facility", definition="a nursing home")
    seed(setup, "survey", definition="an inspection visit")

    listing = setup.list_types(include_retired=True, status=None, namespace=None)
    assert listing.known == 2 == len(listing.types)

    blind = make_registry(DegradedAdapter(adapter, pages_countable=False))
    uncountable = blind.list_types(include_retired=True, status=None, namespace=None)
    assert uncountable.known is None, "None, not 0 -- 0 means 'we counted and found none'"
    assert uncountable.complete is False
    assert uncountable.why_incomplete


def test_c6_03_the_predicate_filter_is_the_extent_read_the_other_way(registry):
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    seed(registry, "note", predicates=["commentable"])
    seed(registry, "capture", definition="not commentable")

    listing = registry.list_types(predicate="commentable")
    assert sorted(t.name for t in listing.types) == ["note", "task"]

    [entry] = [p for p in registry.predicates() if p.name == "commentable"]
    assert sorted(entry.extent) == sorted(t.name for t in listing.types)


def test_c6_04_the_true_census_is_complete(registry):
    seed(registry, "facility", definition="a nursing home")
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded", retired_by="user:sd")

    census = registry.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True
    assert census.why_incomplete is None
    assert sorted(t.name for t in census.types) == ["facility", "watch"]
    assert census.known == 2


def test_c6_05_orphaned_excludes_the_unknowable_and_says_how_many(adapter, make_registry, clock):
    setup = make_registry(adapter)
    seed(setup, "facility", definition="a nursing home")
    seed(setup, "survey", definition="an inspection visit")
    setup.record_use("facility")

    half_blind = make_registry(
        DegradedAdapter(
            adapter,
            timestamps_usage=False,
            why={"timestamps_usage": "work_link_types has no last_used_at column"},
        )
    )
    # `facility` has been used, but without a timestamp its orphan state is unknowable;
    # `survey` has a count of zero, which IS knowable.
    assert half_blind.usage("facility").orphaned is None
    assert half_blind.usage("survey").orphaned is True

    listing = half_blind.list_types(orphaned=True)
    assert [t.name for t in listing.types] == ["survey"]
    assert listing.excluded_unknown == 1, (
        "an unknown orphan state is excluded from both answers and counted, not folded "
        "into whichever answer the caller asked for"
    )
    assert listing.complete is False


def test_c6_06_unverified_semantics_enumerates_exactly_the_carriers(registry):
    seed(registry, "facility", definition="a nursing home")
    proposal = registry.propose_type(
        "scope_severity_code",
        "Ordered severity scale A-L. Higher letters are LESS serious.",
        [],
        "ai:proposer",
        kind="value_set",
        tier="opus",
    )
    registry.approve(proposal.id, "user:sd")

    flagged = registry.list_types(unverified_semantics=True)
    assert [t.name for t in flagged.types] == ["scope_severity_code"]

    clean = registry.list_types(unverified_semantics=False)
    assert [t.name for t in clean.types] == ["facility"]
    assert flagged.complete is False and clean.complete is False
