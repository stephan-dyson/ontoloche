"""C6 -- ``list_types`` (8). Mechanism 2: nobody could find the existing types."""

from __future__ import annotations

import pytest

from datetime import timedelta

from ._support import seed
from .doubles import DegradedAdapter


@pytest.mark.requires_capability("indexes_membership")
def test_c6_01_any_filter_that_hid_rows_makes_the_listing_incomplete(registry):
    seed(registry, "facility", definition="a nursing home")
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded", retired_by="user:sd")

    default = registry.list_types()
    # A store at version 4 ships one seeded family, `default:edge:equivalent_to`
    # (EDGES.md 3.1, ruling R7), so a census of a fresh store counts it. Listed
    # rather than filtered out of the assertion: a census that hid a row would stop
    # being a census, which is this whole group's subject.
    assert [t.name for t in default.types] == ["equivalent_to", "facility"]
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
    # Two seeded here plus the one the store ships -- EDGES.md 3.1.
    assert listing.known == 3 == len(listing.types)

    blind = make_registry(DegradedAdapter(adapter, pages_countable=False))
    uncountable = blind.list_types(include_retired=True, status=None, namespace=None)
    assert uncountable.known is None, "None, not 0 -- 0 means 'we counted and found none'"
    assert uncountable.complete is False
    assert uncountable.why_incomplete


@pytest.mark.requires_capability("indexes_membership")
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
    # The seeded family has never been recorded either, so it is orphaned too --
    # which is the true answer about a store nobody has written an edge into yet.
    assert [t.name for t in listing.types] == ["equivalent_to", "survey"]
    assert listing.excluded_unknown == 1, (
        "an unknown orphan state is excluded from both answers and counted, not folded "
        "into whichever answer the caller asked for"
    )
    assert listing.complete is False


@pytest.mark.requires_capability("stores_proposals")
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
    # The seeded family asserts no domain semantic and carries its own evidence
    # (ruling R7), so it belongs on the clean side -- which is the assertion that
    # would catch a seed that quietly arrived unverified.
    assert [t.name for t in clean.types] == ["equivalent_to", "facility"]
    assert flagged.complete is False and clean.complete is False


def test_c6_07_the_census_spans_namespaces_and_a_scoped_listing_says_it_did_not(registry):
    """``list_types`` is the only call in INTERFACE.md 5 whose ``namespace`` may be
    ``None``, so it is the only way a reader sees a word that two publishers scoped
    apart. Added by row 3c after UC3; see docs/findings/3C-VALIDATION.md.

    Mechanism 2, across namespaces: if the city-wide census does not span them, nobody
    can find out that ``status`` is already taken three times over -- and a scoped
    listing that reported ``complete=True`` would say the opposite of the truth.
    """
    seed(registry, "status", kind="value_set", namespace="dpr",
         definition="whether a street tree is alive, dead, or a stump")
    seed(registry, "status", kind="value_set", namespace="oti_311",
         definition="where a 311 service request is in its workflow")
    seed(registry, "status", kind="value_set", namespace="dot",
         definition="whether a parking meter is in service")

    census = registry.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True and census.why_incomplete is None
    assert sorted(t.namespace for t in census.types) == [
        "default",  # the seeded family -- EDGES.md 3.1
        "dot",
        "dpr",
        "oti_311",
    ]
    assert census.known == 4
    assert len({t.definition for t in census.types}) == 4, "three words, three meanings"

    scoped = registry.list_types(include_retired=True, status=None, namespace="dot")
    assert [t.namespace for t in scoped.types] == ["dot"]
    assert scoped.complete is False, "a scoped listing hid two rows and must say so"
    assert scoped.why_incomplete and "namespace" in scoped.why_incomplete


@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
def test_c6_08_the_predicate_filter_resolves_the_identity_per_namespace(
    adapter, make_registry
):
    """**Ruling R54, row 4d — `list_types(predicate=)` names an identity, not a word.**

    `list_types` is the call whose absence means *"nobody could find the existing
    types"*. After a merge it stopped finding them: every type that had declared the
    absorbed word vanished from the survivor's listing, with a `known` that counted only
    what it happened to see. Both directions are asserted — asking by the **survivor**
    finds the type that declared the absorbed word, and asking by the **absorbed** word
    finds the type that declared the survivor — because they are one identity and the
    call cannot have an opinion about which of its names the caller happened to use.

    **The scoping rule is the interesting half.** An identity is per `(namespace, kind)`
    (§2.1, §2.6): the same word in two namespaces is two identities, and that is exactly
    what §2.6 makes `namespace` the answer to mechanism 4 *for*. So the closure is
    resolved **inside** a namespace and never across one, and a second namespace holding
    its own `commentable` is left alone — asserted here, because a fix that merged the
    two would be §2.6's answer to mechanism 4 deleting itself, which is the shape ruling
    R6 was careful to avoid one call along (§5.3.1 rule 4).
    """
    registry = make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])

    # A DIFFERENT agency's `commentable`, in its own namespace, meaning its own thing.
    seed(registry, "commentable", kind="predicate", namespace="dpr", definition="a capability")
    seed(registry, "park_sign", namespace="dpr", predicates=["commentable"])

    merged = registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert hasattr(merged, "aliases_added"), merged

    seed(registry, "memo", predicates=["commentable"])
    seed(registry, "doc", predicates=["searchable"])

    by_survivor = registry.list_types(predicate="searchable", namespace="default")
    assert {t.name for t in by_survivor.types} == {"note", "memo", "doc"}, (
        "`memo` declared the absorbed word; it is a member of this identity and the "
        "call that exists so people can FIND types must find it"
    )
    assert by_survivor.known == 3

    by_absorbed = registry.list_types(predicate="commentable", namespace="default")
    assert {t.name for t in by_absorbed.types} == {"note", "memo", "doc"}, (
        "one identity, and the answer cannot depend on which of its names was used"
    )

    # **The default `namespace=None` is the ordinary call and gets the same answer** --
    # resolved per namespace, by one bounded `name_in` lookup rather than a census.
    unscoped = registry.list_types(predicate="searchable")
    assert {t.name for t in unscoped.types} == {"note", "memo", "doc"}

    # ...and the other agency's identical word is untouched. Scoping is what stops two
    # teams' meanings being collapsed, and R54 must not undo it.
    other = registry.list_types(predicate="commentable", namespace="dpr")
    assert {t.name for t in other.types} == {"park_sign"}
