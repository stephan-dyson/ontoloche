"""C10 -- ``merge_types``, and the door its operands come through (10). Mechanism 4, constrained to the point of near-uselessness
on purpose.

Merging two types about which nothing is known is the single most destructive thing this
interface can do, so this is the one place where "we do not know" blocks rather than
warns.
"""

from __future__ import annotations

import pytest

from ..types import Consumer, MergeResult, Refusal, TypeEntry
from ._support import seed
from .doubles import DegradedAdapter

NO_EVENTS = {"stores_events": "work_link_types has no event table"}


def _shared_consumer(registry, *members):
    """One predicate, one consumer, and both operands inside its extent -- so the
    consumer-set guard passes and the test's actual subject is reachable."""
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )


@pytest.mark.requires_capability("indexes_membership")
def test_c10_01_different_consumer_sets_refuse_and_nothing_overrides_it(registry):
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", definition="a unit of work", predicates=["commentable"])
    seed(registry, "todo", definition="a unit of work")
    registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    refusal = registry.merge_types("todo", "task", "same thing", merged_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "different_consumer_sets"
    assert refusal.detail["overridable"] is False

    still_refused = registry.merge_types(
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
def test_c10_02_the_kill_row_predicate_merge_is_non_overridable(registry):
    """ROADMAP.md's kill criterion: a capability predicate gets merged as a duplicate.
    Structurally blocked, not merely discouraged."""
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "searchable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable", "searchable"])
    seed(registry, "note", predicates=["commentable"])

    refusal = registry.merge_types(
        "commentable", "searchable", "these two lists look identical", merged_by="user:sd"
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "predicate_merge"
    assert refusal.detail["overridable"] is False
    assert sorted(refusal.detail["from_extent"]) == ["note", "task"]
    assert sorted(refusal.detail["into_extent"]) == ["task"]

    for acknowledgement in ("predicate_merge", "definitions_diverge", "no_consumer_evidence"):
        again = registry.merge_types(
            "commentable",
            "searchable",
            "I really mean it",
            merged_by="user:sd",
            acknowledge=[acknowledgement],
        )
        assert isinstance(again, Refusal) and again.reason == "predicate_merge"


def test_c10_03_different_kinds_refuse(registry):
    _shared_consumer(registry)
    seed(registry, "severity", kind="entity", definition="how serious a thing is",
         predicates=["commentable"])
    seed(registry, "severity_code", kind="value_set", definition="how serious a thing is",
         predicates=["commentable"])

    refusal = registry.merge_types(
        "severity", "severity_code", "same idea", merged_by="user:sd"
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "kind_mismatch"
    assert refusal.detail == {"from": "entity", "into": "value_set", "overridable": False}


def test_c10_04_a_cross_namespace_merge_refuses(registry):
    """Cross-namespace collision is what namespaces exist to *preserve*, not resolve."""
    seed(registry, "entity", definition="a subject noun", namespace="view_query_spec")
    seed(registry, "entity", definition="a task or a project", namespace="comment_service")

    refusal = registry.merge_types(
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
def test_c10_05_a_retired_operand_refuses_but_can_be_acknowledged(registry):
    _shared_consumer(registry)
    seed(registry, "task", definition="a unit of work", predicates=["commentable"])
    seed(registry, "todo", definition="a unit of work", predicates=["commentable"])
    # force, because a consumer gates on it -- which is the point of C9-01, and here
    # it is only setup for the operand this test actually cares about.
    retired = registry.retire("todo", "nobody uses it", retired_by="user:sd", force=True)
    assert retired.status == "retired"

    refusal = registry.merge_types("todo", "task", "same thing", merged_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "retired_operand"
    assert refusal.detail["overridable"] is True

    merged = registry.merge_types(
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
def test_c10_06_diverging_definitions_refuse_but_can_be_acknowledged(registry):
    _shared_consumer(registry)
    seed(
        registry,
        "task",
        definition="a unit of work assigned to a person with a due date",
        predicates=["commentable"],
    )
    seed(
        registry,
        "milestone",
        definition="a calendar marker denoting a contractual delivery obligation",
        predicates=["commentable"],
    )

    refusal = registry.merge_types(
        "milestone", "task", "close enough", merged_by="user:sd"
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "definitions_diverge"
    assert refusal.detail["overridable"] is True

    merged = registry.merge_types(
        "milestone",
        "task",
        "close enough, and I have read both",
        merged_by="user:sd",
        acknowledge=["definitions_diverge"],
    )
    assert isinstance(merged, MergeResult)
    assert "milestone" in merged.entry.aliases
    assert registry.list_types(include_retired=True, status="retired").types[0].name == "milestone"


@pytest.mark.requires_capability("stores_events")
def test_c10_07_two_types_nobody_gates_on_refuse_for_want_of_evidence(registry):
    seed(registry, "task", definition="a unit of work")
    seed(registry, "todo", definition="a unit of work")

    refusal = registry.merge_types("todo", "task", "same thing", merged_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "no_consumer_evidence"
    assert refusal.detail["overridable"] is True

    merged = registry.merge_types(
        "todo",
        "task",
        "same thing, and I accept nothing is known about what breaks",
        merged_by="user:sd",
        acknowledge=["no_consumer_evidence"],
    )
    assert isinstance(merged, MergeResult)


def test_c10_08_every_acknowledgement_is_recorded_or_the_merge_is_refused(
    adapter, make_registry
):
    registry = make_registry(adapter)
    seed(registry, "task", definition="a unit of work")
    seed(registry, "todo", definition="a unit of work")

    # Same split as C9-02: "every acknowledgement is recorded" needs a backend that can
    # record one. On a backend that cannot, the acknowledgement is refused -- which is
    # this test's other half. Row 3c's capability sweep.
    if adapter.capabilities().stores_events:
        merged = registry.merge_types(
            "todo",
            "task",
            "same thing",
            merged_by="user:sd",
            acknowledge=["no_consumer_evidence"],
        )
        assert isinstance(merged, MergeResult)
        events = [e for e in registry.provenance("todo").history if e.event == "merged"]
        assert events and events[0].detail["acknowledge"] == ["no_consumer_evidence"]
        assert events[0].detail["into"] == "task"

    blind = make_registry(DegradedAdapter(adapter, stores_events=False, why=NO_EVENTS))
    seed(blind, "chore", definition="a unit of work")
    seed(blind, "errand", definition="a unit of work")
    refusal = blind.merge_types(
        "errand",
        "chore",
        "same thing",
        merged_by="user:sd",
        acknowledge=["no_consumer_evidence"],
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override"


@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
def test_c10_09_two_empty_extents_are_not_a_byte_identical_extent(registry):
    """`ROADMAP.md`'s kill row, reached by the OTHER end of guard 2's expression.

    `C10-02` pins the case where the two extents DIFFER. Row 3c closed the case
    where they cannot be COMPUTED (`indexes_membership=False`). Nothing pinned the
    case where they are both **empty** -- and `set() == set()`, so two predicates
    that nothing satisfies compared byte-identical, guard 2 did not fire, and the
    merge fell through to the *overridable* guards.

    Reproduced end to end by row #6's second adversarial round against this
    registry: two predicates proposed by an `ai:` actor at Haiku into an
    auto-approving namespace, live, then merged under two acknowledgements. An
    empty extent is *no evidence of membership*, not *evidence of identical
    membership* -- and 5.10 says of the guard one row down that "merging two types
    about which nothing is known is the single most destructive thing this
    interface can do".
    """
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "searchable", kind="predicate", definition="a code path will accept it")

    refusal = registry.merge_types(
        "commentable", "searchable", "nothing carries either, so they must be the same",
        merged_by="ai:ingest",
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "predicate_merge"
    assert refusal.detail["overridable"] is False
    assert refusal.detail["extents_empty"] is True
    assert refusal.detail["from_extent"] == [] and refusal.detail["into_extent"] == []
    assert "no evidence of membership" in refusal.detail["why"]

    # Non-overridable means non-overridable, including under the two
    # acknowledgements the round-2 reviewer used to get through.
    for ack in (["predicate_merge"], ["definitions_diverge", "no_consumer_evidence"]):
        again = registry.merge_types(
            "commentable", "searchable", "I really mean it",
            merged_by="ai:ingest", acknowledge=ack,
        )
        assert isinstance(again, Refusal) and again.reason == "predicate_merge"

    # And a NON-empty identical extent still merges -- the rule narrows the guard,
    # it does not ban predicate merges outright (5.10's "unless byte-identical").
    seed(registry, "task", predicates=["commentable", "searchable"])
    merged = registry.merge_types(
        "commentable", "searchable", "identical, and demonstrably so",
        merged_by="user:sd", acknowledge=["no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged


def test_c10_10_a_predicate_proposal_never_takes_the_auto_path(adapter, make_registry):
    """Ruling **R40**, row 4c. **Belt-and-braces over `C10-09` and `C9-18`.**

    Those two guard the **merge**: a predicate pair may not be collapsed unless their
    extents are non-empty and identical, whether the collapse arrives through
    `merge_types` or through `retire(successor=)`. This guards the door the merge's
    operands came through. *"A capability predicate is the one kind where an
    auto-approval policy approving is the kill row"* -- and it is not a hypothesis: **two
    of the three kill-row trips began with a predicate that went live without a human**,
    the second one with two `ai:`-proposed predicates auto-approved at Haiku into an
    auto-approving namespace and then merged under two acknowledgements.

    `propose_type(kind="predicate")` therefore returns a **pending `Proposal` regardless
    of the policy**, warning `predicate_requires_review`. It is a warning and not a
    refusal because the proposal is perfectly valid -- INTERFACE.md 5.4 refuses two
    things and warns about everything else, *because refusing a near-duplicate is how you
    flatten a capability predicate*. What R40 removes is the auto path, not the proposal.

    Three things are asserted, and the third is the one that would rot: an `entity` in
    the same auto namespace still auto-approves, so this is a rule about **one kind** and
    not a policy that quietly stopped working.
    """
    registry = make_registry(adapter, approval_policy="auto")
    if not registry.caps.stores_proposals:
        # PACKAGE.md 7.3 B4: no proposal table means no review step, so there is nowhere
        # to hold a predicate. The entry is written and SAYS SO -- which is what makes
        # "a predicate went live without the review R40 requires" enumerable rather than
        # silent -- and asserting that here is the honest unknown, not a skip.
        entry = registry.propose_type(
            "commentable", "things a user may comment on", [], "user:sd", kind="predicate"
        )
        assert isinstance(entry, TypeEntry), entry
        assert "predicate_requires_review" in entry.warnings, (
            "the one place R40 cannot be honoured says so on the entry it wrote"
        )
        return

    proposal = registry.propose_type(
        "commentable", "things a user may comment on", [], "ai:haiku_classifier",
        kind="predicate", tier="haiku",
    )
    assert not isinstance(proposal, TypeEntry), (
        "R40 -- an auto-approving namespace does NOT auto-approve a capability predicate, "
        "and this is the shape two of the three kill-row trips began with"
    )
    assert not isinstance(proposal, Refusal), proposal
    assert proposal.status == "pending"
    assert "predicate_requires_review" in proposal.warnings

    # The human review still works, and it is the only way through.
    approved = registry.approve(proposal.id, "user:sd")
    assert isinstance(approved, TypeEntry), approved
    assert approved.status == "active"
    assert approved.provenance.approved_by == "user:sd", (
        "never `auto:<policy>` -- the point of the ruling is that a person signed off"
    )

    # And the rule is about ONE KIND. An entity in the same namespace under the same
    # policy still auto-approves, so a policy that quietly stopped working would fail
    # here rather than pass silently.
    entity = registry.propose_type(
        "task", "a unit of work", [], "user:sd", kind="entity"
    )
    assert isinstance(entity, TypeEntry), (
        "R40 narrows `propose_type` for predicates and for nothing else"
    )
    assert "predicate_requires_review" not in entity.warnings
