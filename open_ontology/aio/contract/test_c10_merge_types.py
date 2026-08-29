# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c10_merge_types.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C10 -- ``merge_types`` (8). Mechanism 4, constrained to the point of near-uselessness
on purpose.

Merging two types about which nothing is known is the single most destructive thing this
interface can do, so this is the one place where "we do not know" blocks rather than
warns.
"""

from __future__ import annotations
import pytest
from open_ontology.types import Consumer, MergeResult, Refusal
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


NO_EVENTS = {"stores_events": "work_link_types has no event table"}

async def _shared_consumer(registry, *members):
    """One predicate, one consumer, and both operands inside its extent -- so the
    consumer-set guard passes and the test's actual subject is reachable."""
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

@pytest.mark.requires_capability("indexes_membership")
async def test_c10_01_different_consumer_sets_refuse_and_nothing_overrides_it(registry):
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", definition="a unit of work", predicates=["commentable"])
    await seed(registry, "todo", definition="a unit of work")
    await registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    refusal = await registry.merge_types("todo", "task", "same thing", merged_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "different_consumer_sets"
    assert refusal.detail["overridable"] is False

    still_refused = await registry.merge_types(
        "todo",
        "task",
        "same thing",
        merged_by="user:sd",
        acknowledge=["different_consumer_sets", "definitions_diverge", "no_consumer_evidence"],
    )
    assert isinstance(still_refused, Refusal)
    assert still_refused.reason == "different_consumer_sets", (
        "merging asserts every consumer of one accepts the other; no acknowledgement "
        "can make that true"
    )

@pytest.mark.requires_capability("indexes_membership")
async def test_c10_02_the_kill_row_predicate_merge_is_non_overridable(registry):
    """ROADMAP.md's kill criterion: a capability predicate gets merged as a duplicate.
    Structurally blocked, not merely discouraged."""
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "searchable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable", "searchable"])
    await seed(registry, "note", predicates=["commentable"])

    refusal = await registry.merge_types(
        "commentable", "searchable", "these two lists look identical", merged_by="user:sd"
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "predicate_merge"
    assert refusal.detail["overridable"] is False
    assert sorted(refusal.detail["from_extent"]) == ["note", "task"]
    assert sorted(refusal.detail["into_extent"]) == ["task"]

    for acknowledgement in ("predicate_merge", "definitions_diverge", "no_consumer_evidence"):
        again = await registry.merge_types(
            "commentable",
            "searchable",
            "I really mean it",
            merged_by="user:sd",
            acknowledge=[acknowledgement],
        )
        assert isinstance(again, Refusal) and again.reason == "predicate_merge"

async def test_c10_03_different_kinds_refuse(registry):
    await _shared_consumer(registry)
    await seed(registry, "severity", kind="entity", definition="how serious a thing is",
         predicates=["commentable"])
    await seed(registry, "severity_code", kind="value_set", definition="how serious a thing is",
         predicates=["commentable"])

    refusal = await registry.merge_types(
        "severity", "severity_code", "same idea", merged_by="user:sd"
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "kind_mismatch"
    assert refusal.detail == {"from": "entity", "into": "value_set", "overridable": False}

async def test_c10_04_a_cross_namespace_merge_refuses(registry):
    """Cross-namespace collision is what namespaces exist to *preserve*, not resolve."""
    await seed(registry, "entity", definition="a subject noun", namespace="view_query_spec")
    await seed(registry, "entity", definition="a task or a project", namespace="comment_service")

    refusal = await registry.merge_types(
        "entity",
        "entity",
        "one word, two meanings",
        merged_by="user:sd",
        namespace="view_query_spec",
        into_namespace="comment_service",
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cross_namespace_merge"
    assert refusal.detail["overridable"] is False

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c10_05_a_retired_operand_refuses_but_can_be_acknowledged(registry):
    await _shared_consumer(registry)
    await seed(registry, "task", definition="a unit of work", predicates=["commentable"])
    await seed(registry, "todo", definition="a unit of work", predicates=["commentable"])
    # force, because a consumer gates on it -- which is the point of C9-01, and here
    # it is only setup for the operand this test actually cares about.
    retired = await registry.retire("todo", "nobody uses it", retired_by="user:sd", force=True)
    assert retired.status == "retired"

    refusal = await registry.merge_types("todo", "task", "same thing", merged_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "retired_operand"
    assert refusal.detail["overridable"] is True

    merged = await registry.merge_types(
        "todo", "task", "same thing", merged_by="user:sd",
        # `definitions_diverge` too: no resolver here certifies synonymy, and this
        # test's subject is the retired operand, not the wording (row 3c).
        acknowledge=["retired_operand", "definitions_diverge"],
    )
    assert isinstance(merged, MergeResult)
    assert merged.acknowledged == ("retired_operand", "definitions_diverge")
    # Row 3c: the divergence acknowledgement is now required whenever the definitions
    # differ and no resolver certifies synonymy, and the score is recorded either way.
    assert any(w.startswith("definitions_similarity:") for w in merged.warnings)

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c10_06_diverging_definitions_refuse_but_can_be_acknowledged(registry):
    await _shared_consumer(registry)
    await seed(
        registry,
        "task",
        definition="a unit of work assigned to a person with a due date",
        predicates=["commentable"],
    )
    await seed(
        registry,
        "milestone",
        definition="a calendar marker denoting a contractual delivery obligation",
        predicates=["commentable"],
    )

    refusal = await registry.merge_types(
        "milestone", "task", "close enough", merged_by="user:sd"
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "definitions_diverge"
    assert refusal.detail["overridable"] is True

    merged = await registry.merge_types(
        "milestone",
        "task",
        "close enough, and I have read both",
        merged_by="user:sd",
        acknowledge=["definitions_diverge"],
    )
    assert isinstance(merged, MergeResult)
    assert "milestone" in merged.entry.aliases
    assert (await registry.list_types(include_retired=True, status="retired")).types[0].name == "milestone"

@pytest.mark.requires_capability("stores_events")
async def test_c10_07_two_types_nobody_gates_on_refuse_for_want_of_evidence(registry):
    await seed(registry, "task", definition="a unit of work")
    await seed(registry, "todo", definition="a unit of work")

    refusal = await registry.merge_types("todo", "task", "same thing", merged_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "no_consumer_evidence"
    assert refusal.detail["overridable"] is True

    merged = await registry.merge_types(
        "todo",
        "task",
        "same thing, and I accept nothing is known about what breaks",
        merged_by="user:sd",
        acknowledge=["no_consumer_evidence"],
    )
    assert isinstance(merged, MergeResult)

async def test_c10_08_every_acknowledgement_is_recorded_or_the_merge_is_refused(
    adapter, make_registry
):
    registry = await make_registry(adapter)
    await seed(registry, "task", definition="a unit of work")
    await seed(registry, "todo", definition="a unit of work")

    # Same split as C9-02: "every acknowledgement is recorded" needs a backend that can
    # record one. On a backend that cannot, the acknowledgement is refused -- which is
    # this test's other half. Row 3c's capability sweep.
    if (await adapter.capabilities()).stores_events:
        merged = await registry.merge_types(
            "todo",
            "task",
            "same thing",
            merged_by="user:sd",
            acknowledge=["no_consumer_evidence"],
        )
        assert isinstance(merged, MergeResult)
        events = [e for e in (await registry.provenance("todo")).history if e.event == "merged"]
        assert events and events[0].detail["acknowledge"] == ["no_consumer_evidence"]
        assert events[0].detail["into"] == "task"

    blind = await make_registry(AsyncDegradedAdapter(adapter, stores_events=False, why=NO_EVENTS))
    await seed(blind, "chore", definition="a unit of work")
    await seed(blind, "errand", definition="a unit of work")
    refusal = await blind.merge_types(
        "errand",
        "chore",
        "same thing",
        merged_by="user:sd",
        acknowledge=["no_consumer_evidence"],
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override"
