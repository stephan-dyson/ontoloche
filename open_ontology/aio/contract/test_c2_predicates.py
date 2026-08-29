# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c2_predicates.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C2 -- ``predicates`` (5). Mechanism 4 defensively, and the ROADMAP.md kill row.

Predicates are the structure that stops five locally-correct lists being read as five
duplicates.
"""

from __future__ import annotations
from open_ontology.types import Consumer
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


async def test_c2_01_the_extent_is_derived_not_stored_twice(registry, adapter):
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    predicate_before = await adapter.get_type("default", "commentable", kind="predicate")
    consumers_before = await adapter.find_consumers("default")

    await seed(registry, "project", predicates=["commentable"])

    predicate_after = await adapter.get_type("default", "commentable", kind="predicate")
    assert predicate_after == predicate_before, (
        "writing membership must touch only the member's rows; nothing is ever written "
        "to the predicate's own row"
    )
    assert await adapter.find_consumers("default") == consumers_before, (
        "if a consumer-membership table exists, the extent has been stored twice"
    )

    # The proof that there is no second store: a consumer registered before `project`
    # existed gates on it immediately, with nothing re-registered.
    report = await registry.consumers("project")
    assert [c.id for c in report.gates_on] == ["comment_service.can_comment"]

    [entry] = [p for p in await registry.predicates() if p.name == "commentable"]
    assert entry.extent == ("project", "task")
    assert entry.extent_size == 2

async def test_c2_02_unindexed_membership_reports_an_unknown_extent_not_an_empty_one(
    adapter, make_registry
):
    setup = await make_registry(adapter)
    await seed(setup, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(setup, "task", predicates=["commentable"])

    blind = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            indexes_membership=False,
            why={"indexes_membership": "work_link_types has no membership table"},
        )
    )
    [entry] = [p for p in await blind.predicates() if p.name == "commentable"]
    assert entry.extent == ()
    assert entry.extent_size is None, (
        "extent_size=0 reads as 'nothing is commentable', which is 5.2's named failure"
    )
    assert entry.why_extent_incomplete == "work_link_types has no membership table"

async def test_c2_03_of_returns_only_the_predicates_that_type_satisfies(registry):
    await seed(registry, "commentable", kind="predicate", definition="can be commented on")
    await seed(registry, "searchable", kind="predicate", definition="is in the search index")
    await seed(registry, "task", predicates=["commentable", "searchable"])
    await seed(registry, "capture", predicates=["searchable"])

    assert {p.name for p in await registry.predicates(of="task")} == {"commentable", "searchable"}
    assert {p.name for p in await registry.predicates(of="capture")} == {"searchable"}

async def test_c2_04_include_retired(registry):
    await seed(registry, "commentable", kind="predicate", definition="can be commented on")
    await seed(registry, "shareable", kind="predicate", definition="can be shared")
    await registry.retire("shareable", "nothing gates on it any more", retired_by="user:sd")

    assert {p.name for p in await registry.predicates()} == {"commentable"}
    assert {p.name for p in await registry.predicates(include_retired=True)} == {
        "commentable",
        "shareable",
    }

async def test_c2_05_a_predicate_is_not_a_supertype(registry):
    """Membership of `commentable` implies nothing about `searchable`. A registry that
    cannot hold this distinction merges the two and thereby asserts something false."""
    await seed(registry, "commentable", kind="predicate", definition="can be commented on")
    await seed(registry, "searchable", kind="predicate", definition="is in the search index")
    await seed(registry, "task", predicates=["commentable", "searchable"])
    await seed(registry, "note", predicates=["commentable"])

    by_name = {p.name: p for p in await registry.predicates()}
    assert set(by_name["commentable"].extent) == {"note", "task"}
    assert set(by_name["searchable"].extent) == {"task"}
    assert "note" not in by_name["searchable"].extent
    assert {p.name for p in await registry.predicates(of="note")} == {"commentable"}
