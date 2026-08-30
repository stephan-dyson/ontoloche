"""C2 -- ``predicates`` (6). Mechanism 4 defensively, and the ROADMAP.md kill row.

Predicates are the structure that stops five locally-correct lists being read as five
duplicates.
"""

from __future__ import annotations

import pytest

from ..types import Consumer
from ._support import seed
from .doubles import DegradedAdapter


@pytest.mark.requires_capability("indexes_membership")
def test_c2_01_the_extent_is_derived_not_stored_twice(registry, adapter):
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    predicate_before = adapter.get_type("default", "commentable", kind="predicate")
    consumers_before = adapter.find_consumers("default")

    seed(registry, "project", predicates=["commentable"])

    predicate_after = adapter.get_type("default", "commentable", kind="predicate")
    assert predicate_after == predicate_before, (
        "writing membership must touch only the member's rows; nothing is ever written "
        "to the predicate's own row"
    )
    assert adapter.find_consumers("default") == consumers_before, (
        "if a consumer-membership table exists, the extent has been stored twice"
    )

    # The proof that there is no second store: a consumer registered before `project`
    # existed gates on it immediately, with nothing re-registered.
    report = registry.consumers("project")
    assert [c.id for c in report.gates_on] == ["comment_service.can_comment"]

    [entry] = [p for p in registry.predicates() if p.name == "commentable"]
    assert entry.extent == ("project", "task")
    assert entry.extent_size == 2


def test_c2_02_unindexed_membership_reports_an_unknown_extent_not_an_empty_one(
    adapter, make_registry
):
    setup = make_registry(adapter)
    seed(setup, "commentable", kind="predicate", definition="a code path will accept it")
    seed(setup, "task", predicates=["commentable"])

    blind = make_registry(
        DegradedAdapter(
            adapter,
            indexes_membership=False,
            why={"indexes_membership": "work_link_types has no membership table"},
        )
    )
    [entry] = [p for p in blind.predicates() if p.name == "commentable"]
    assert entry.extent == ()
    assert entry.extent_size is None, (
        "extent_size=0 reads as 'nothing is commentable', which is 5.2's named failure"
    )
    assert entry.why_extent_incomplete == "work_link_types has no membership table"


@pytest.mark.requires_capability("indexes_membership")
def test_c2_03_of_returns_only_the_predicates_that_type_satisfies(registry):
    seed(registry, "commentable", kind="predicate", definition="can be commented on")
    seed(registry, "searchable", kind="predicate", definition="is in the search index")
    seed(registry, "task", predicates=["commentable", "searchable"])
    seed(registry, "capture", predicates=["searchable"])

    assert {p.name for p in registry.predicates(of="task")} == {"commentable", "searchable"}
    assert {p.name for p in registry.predicates(of="capture")} == {"searchable"}


@pytest.mark.requires_capability("indexes_membership")
def test_c2_04_include_retired(registry):
    seed(registry, "commentable", kind="predicate", definition="can be commented on")
    seed(registry, "shareable", kind="predicate", definition="can be shared")
    registry.retire("shareable", "nothing gates on it any more", retired_by="user:sd")

    default = registry.predicates()
    assert {p.name for p in default} == {"commentable"}
    # Rule K (INTERFACE.md 3, 5.2): the default hides a row, so the listing says so.
    # A bare list here would read as "there is one predicate", which is not true.
    assert default.complete is False
    assert default.known == 1
    assert default.why_incomplete and "include_retired" in default.why_incomplete

    everything = registry.predicates(include_retired=True)
    assert {p.name for p in everything} == {"commentable", "shareable"}
    assert everything.complete is True and everything.why_incomplete is None


@pytest.mark.requires_capability("indexes_membership")
def test_c2_05_a_predicate_is_not_a_supertype(registry):
    """Membership of `commentable` implies nothing about `searchable`. A registry that
    cannot hold this distinction merges the two and thereby asserts something false."""
    seed(registry, "commentable", kind="predicate", definition="can be commented on")
    seed(registry, "searchable", kind="predicate", definition="is in the search index")
    seed(registry, "task", predicates=["commentable", "searchable"])
    seed(registry, "note", predicates=["commentable"])

    by_name = {p.name: p for p in registry.predicates()}
    assert set(by_name["commentable"].extent) == {"note", "task"}
    assert set(by_name["searchable"].extent) == {"task"}
    assert "note" not in by_name["searchable"].extent
    assert {p.name for p in registry.predicates(of="note")} == {"commentable"}


@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
def test_c2_06_the_extent_and_the_of_filter_resolve_the_identity(adapter, make_registry):
    """**Ruling R54, row 4d — `predicates` answers about an IDENTITY, not a word.**

    `INTERFACE.md` §2.1 rules that a reference resolves to the identity it now belongs
    to. After `merge(commentable → searchable)` this call did not: a type that had
    declared `commentable` was compared, by written string, against a page holding only
    the survivor's name — so `predicates(of=that_type)` answered **`known=0`**, and the
    survivor's `extent` omitted it.

    **That is §5.2's own named failure mode, in the call §5.2 names it in:** an empty
    answer reading as a confident zero, *"this type satisfies no predicates"*, about a
    member the registry can see. And it is reachable by two ordinary governance acts —
    a legal merge, and somebody declaring a type against a word that still resolves.

    The guards are deliberately **not** changed by this: they compare the two **written
    words**, because asking whether one identity equals itself is circular and would
    make every collapse compare equal by construction. `C10-09`, `C10-11`, `C10-13`,
    `C12-08` and `C9-18` all still hold, and `check_merge_guard.py`'s stale axis is the
    mechanical form of that claim.
    """
    registry = make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable"):
        seed(registry, name, kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])

    merged = registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, type(None)) and hasattr(merged, "aliases_added"), merged

    # A type declared AFTER the merge, against the ABSORBED word -- which still
    # resolves, so declaring it is neither an error nor unusual.
    seed(registry, "memo", predicates=["commentable"])
    seed(registry, "doc", predicates=["searchable"])

    listing = registry.predicates(of="memo")
    assert listing.known == 1, (
        "`memo` declared a word that still resolves to a live predicate; answering "
        "known=0 is 5.2's own failure mode -- an empty answer read as a confident zero"
    )
    entry = listing.predicates[0]
    assert entry.name == "searchable", "the identity's live name, not the absorbed one"
    assert set(entry.extent) == {"note", "memo", "doc"}, (
        "the extent is the identity's members: every type that declared either word"
    )
    assert entry.extent_size == 3

    # The survivor's own members are unchanged in meaning and larger in fact.
    by_note = registry.predicates(of="note")
    assert [p.name for p in by_note.predicates] == ["searchable"]
    assert set(by_note.predicates[0].extent) == {"note", "memo", "doc"}
