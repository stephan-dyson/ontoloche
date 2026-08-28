"""C2 -- ``predicates`` (5). Mechanism 4 defensively, and the ROADMAP.md kill row.

Predicates are the structure that stops five locally-correct lists being read as five
duplicates.
"""

from __future__ import annotations

from ..types import Consumer
from ._support import seed
from .doubles import DegradedAdapter


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


def test_c2_03_of_returns_only_the_predicates_that_type_satisfies(registry):
    seed(registry, "commentable", kind="predicate", definition="can be commented on")
    seed(registry, "searchable", kind="predicate", definition="is in the search index")
    seed(registry, "task", predicates=["commentable", "searchable"])
    seed(registry, "capture", predicates=["searchable"])

    assert {p.name for p in registry.predicates(of="task")} == {"commentable", "searchable"}
    assert {p.name for p in registry.predicates(of="capture")} == {"searchable"}


def test_c2_04_include_retired(registry):
    seed(registry, "commentable", kind="predicate", definition="can be commented on")
    seed(registry, "shareable", kind="predicate", definition="can be shared")
    registry.retire("shareable", "nothing gates on it any more", retired_by="user:sd")

    assert {p.name for p in registry.predicates()} == {"commentable"}
    assert {p.name for p in registry.predicates(include_retired=True)} == {
        "commentable",
        "shareable",
    }


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
