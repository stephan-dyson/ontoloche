"""C9 -- ``retire`` and ``reinstate`` (11). Mechanism 3.

Retirement is guarded by ``consumers``, not by usage.
"""

from __future__ import annotations

import pytest

from ..types import Consumer, Refusal, TypeEntry
from ._support import seed
from .doubles import DegradedAdapter

NO_EVENTS = {"stores_events": "work_link_types has no event table"}
NO_TIMESTAMPS = {"timestamps_usage": "work_link_types has no last_used_at column"}


def _with_live_consumer(registry):
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )


@pytest.mark.requires_capability("indexes_membership")
def test_c9_01_a_live_consumer_refuses_the_retirement(registry):
    _with_live_consumer(registry)
    refusal = registry.retire("task", "we think nobody uses it", retired_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "live_consumers"
    assert refusal.detail["gates_on"] == ["comment_service.can_comment"]
    assert registry.list_types(status="active").types


@pytest.mark.requires_capability("indexes_membership")
def test_c9_02_force_overrides_and_records_or_is_refused(adapter, make_registry):
    registry = make_registry(adapter)
    _with_live_consumer(registry)

    # The "overrides AND records" half needs a backend that can record. On one that
    # cannot, the whole call is the refusal below -- which is this test's other half and
    # the more important one. Split by row 3c's capability sweep.
    if adapter.capabilities().stores_events:
        forced = registry.retire(
            "task", "the service is being deleted", retired_by="user:sd", force=True
        )
        assert isinstance(forced, TypeEntry) and forced.status == "retired"
        retired_events = [e for e in forced.provenance.history if e.event == "retired"]
        assert retired_events[0].detail["forced"] is True
        assert retired_events[0].detail["overrode"] == ["comment_service.can_comment"]

    # On a backend that cannot record the override, the override is refused. An
    # unrecorded, unattributable destructive change is what this registry exists to
    # prevent, and a store with no audit trail has not earned the right to be overridden.
    blind = make_registry(DegradedAdapter(adapter, stores_events=False, why=NO_EVENTS))
    seed(blind, "note", predicates=["commentable"])
    refusal = blind.retire("note", "and this one too", retired_by="user:sd", force=True)
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override"
    assert refusal.detail["why"] == NO_EVENTS["stores_events"]


@pytest.mark.requires_capability("indexes_membership")
def test_c9_03_retiring_without_usage_evidence_proceeds_but_warns(adapter, make_registry):
    setup = make_registry(adapter)
    seed(setup, "blocks", definition="this work item blocks that one")
    setup.record_use("blocks")

    half_blind = make_registry(DegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    assert half_blind.usage("blocks").orphaned is None

    entry = half_blind.retire("blocks", "the feature was removed", retired_by="user:sd")
    assert isinstance(entry, TypeEntry)
    assert entry.status == "retired"
    assert "retired_without_usage_evidence" in entry.warnings


@pytest.mark.requires_capability("indexes_membership")
def test_c9_04_a_retired_name_is_not_reusable(registry, adapter):
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd")

    answer = registry.propose_type("watch", "a completely different watch", [], "user:pm")
    assert isinstance(answer, TypeEntry)
    assert answer.status == "retired"
    assert "name_previously_retired" in answer.warnings

    stored = adapter.get_type("default", "watch")
    assert stored.status == "retired", "no new entry was created under the retired name"
    assert stored.definition == "a thing a user watches", (
        "and the retired row was not overwritten by the new proposer's wording"
    )


def test_c9_05_retire_requires_a_reason(registry):
    seed(registry, "watch", definition="a thing a user watches")
    with pytest.raises(ValueError):
        registry.retire("watch", "", retired_by="user:sd")
    with pytest.raises(ValueError):
        registry.retire("watch", "   ", retired_by="user:sd")


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c9_06_the_successor_is_recorded_and_surfaces_in_provenance(registry):
    seed(registry, "capture", definition="the word that replaced it")
    seed(registry, "watch", definition="a thing a user watches")
    entry = registry.retire(
        "watch", "superseded by `capture`", retired_by="user:sd", successor="capture"
    )
    assert isinstance(entry, TypeEntry)

    retired_events = [e for e in registry.provenance("watch").history if e.event == "retired"]
    assert retired_events[0].detail["successor"] == "capture"
    assert retired_events[0].detail["reason"] == "superseded by `capture`"


@pytest.mark.requires_capability("stores_events")
def test_c9_07_an_unknowable_consumer_set_blocks_the_retirement(adapter, make_registry):
    """**Mechanism C, committed by the call built to catch it.** Row 3c, after an
    adversarial review round reproduced this live.

    `retire` is guarded by `consumers`, not by usage (INTERFACE.md 5.9), and it read an
    empty `gates_on` as *"nothing gates on this"*. On a backend that cannot index
    membership every extent is empty, so `gates_on` is empty for a reason that means
    **we could not look** -- and a type with a real, registered, gating consumer retired
    with no refusal and no warning. `merge_types` already took the honest line for the
    identical uncertainty (5.10's `no_consumer_evidence`, *"the one place we do not know
    blocks rather than warns"*); `retire` now takes it too, with `force=True` as the
    override, recorded in history like any other.

    Note what this is NOT: it is not a claim that the backend is non-conformant.
    `indexes_membership=False` is a declared, conformant capability (PACKAGE.md 3.2).
    The registry simply may not convert its own blindness into a confident answer.
    """
    blind = make_registry(DegradedAdapter(adapter, indexes_membership=False))
    seed(blind, "commentable", kind="predicate", definition="a code path will accept it")
    seed(blind, "task", definition="a unit of work", predicates=["commentable"])
    blind.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    report = blind.consumers("task")
    assert report.gates_on == (), "the extent is unknowable, so the report is empty..."
    assert report.complete is False, "...and it already says it is incomplete"

    refusal = blind.retire("task", "no longer needed", retired_by="user:sd")
    assert isinstance(refusal, Refusal), "an empty gates_on we could not verify must block"
    assert refusal.reason == "no_consumer_evidence"
    assert refusal.detail["overridable"] is True
    assert "could not look" in refusal.detail["why"]
    assert blind.list_types(namespace="default").types, "and nothing was retired"

    overridden = blind.retire("task", "I accept the risk", retired_by="user:sd", force=True)
    assert isinstance(overridden, TypeEntry) and overridden.status == "retired"


def test_c9_08_force_is_refused_when_it_cannot_be_recorded_whichever_guard_it_overrides(
    adapter, make_registry
):
    """**Tenshen's own declared shape, and PACKAGE.md 7.3 B6 states this in terms.**

    `work_link_types` declares `indexes_membership=False` (B3 -- it has no predicate
    concept, and B3 says that is *correct*) **and** `stores_events=False` (B6 -- no event
    table). B6 then says plainly that on such a backend `retire(force=True)` returns
    `Refusal("cannot_record_override")`.

    [Observed] it did not. The recordability check lived **inside** the
    `live_consumers` branch, and on a backend that cannot index membership `gates_on` is
    always empty, so the branch never ran: a type with a real, registered, gating
    consumer retired with **no refusal, no warning on the returned entry, and no history
    of any kind** -- the unrecorded, unattributable destructive change this registry
    exists to prevent, on the one backend UC1 is the fixture for.

    `merge_types` has had the unconditional form since v0 (*"if acknowledge and not
    stores_events"*, whichever refusal is being overridden). `retire` now matches it.
    `C9-02` covers one flag, `C9-07` the other; only both together produce this.
    Added by row 3c after an adversarial review round drove the real registry through
    the compound shape.
    """
    tenshen_shaped = make_registry(
        DegradedAdapter(adapter, indexes_membership=False, stores_events=False)
    )
    seed(tenshen_shaped, "commentable", kind="predicate", definition="a code path accepts it")
    seed(tenshen_shaped, "blocks", definition="this work item blocks that one",
         predicates=["commentable"])
    tenshen_shaped.register_consumer(
        Consumer(id="aura_render.referent_link", gate="commentable", on_unknown="drop")
    )

    refusal = tenshen_shaped.retire(
        "blocks", "no longer needed", retired_by="user:sd", force=True
    )
    assert isinstance(refusal, Refusal), "an override nobody can audit is not an override"
    assert refusal.reason == "cannot_record_override"
    assert refusal.detail["gates_on_knowable"] is False, (
        "and it says the consumer set was unknowable, so the reader is not left "
        "believing an empty would_override means nothing was at stake"
    )
    entry = tenshen_shaped.list_types(namespace="default").types
    assert [t.status for t in entry if t.name == "blocks"] == ["active"], "nothing retired"


# ------------------------------------------------------------ C9-09 .. C9-11: reinstate
#
# Ruling R11, row 3e. INTERFACE.md 5.9b. ``retire`` and ``reinstate`` are one story and
# the tests live together, which is why these carry C9 ids rather than a new group:
# 5.9's own justification named ``reinstate`` in a subordinate clause and no such call
# existed.


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c9_09_a_retired_name_can_be_reinstated_and_resolves_again(registry):
    """**The round trip, and the classifier shape from row 3c's round 8.**

    propose -> approve -> retire -> reinstate, then `resolve_type` on the name returns
    `existing` again. That last assertion is the one that matters: round 8 found
    `resolve_type` answering *"nothing in the vocabulary fits 'watch'"* about a word it
    had just read the tombstone of, and the fix made a retired name surface in `reason`
    and in `alternatives` with a `None` score (`C3-10`). A **reinstated** name must go
    all the way back to `existing` -- an auto-approving classifier one step earlier in
    the pipeline is UC1's own shape, and a name that still reads as burned after it has
    been brought back is the same confident wrong answer pointing the other way.

    Also asserted: the retirement is **cleared from the record and kept in the
    history**. INTERFACE.md 5.8's rule is that provenance is append-only and a
    correction is a new event, never an edit -- so `retire_reason` and `successor` come
    off the live row (a stale successor on an active entry is a pointer a later call
    would read as current) and the `reinstated` event carries every field cleared.
    """
    from ..types import ResolveContext

    seed(registry, "watch", definition="a thing a user watches")
    retired = registry.retire("watch", "classifier drift, we think", retired_by="user:sd")
    assert isinstance(retired, TypeEntry) and retired.status == "retired"

    gone = registry.resolve_type("watch", ResolveContext(), tier="opus")
    assert gone.outcome != "existing", "C3-10: a retired name is not an existing one"

    back = registry.reinstate("watch", "the drift correction was wrong", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry), back
    assert back.status == "active"
    assert "retired_without_usage_evidence" not in back.warnings

    again = registry.resolve_type("watch", ResolveContext(), tier="opus")
    assert again.outcome == "existing", "a reinstated name resolves again"
    assert again.type is not None and again.type.name == "watch"
    assert again.confidence == 1.0

    events = [e for e in registry.provenance("watch").history if e.event == "reinstated"]
    assert len(events) == 1
    assert events[0].actor == "user:sd"
    assert events[0].detail["reason"] == "the drift correction was wrong"
    assert events[0].detail["retire_reason"] == "classifier drift, we think", (
        "the retirement is cleared from the row and kept in the history, never lost"
    )


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c9_10_reinstate_refuses_when_the_successor_is_active(registry):
    """**`successor_active` -- the twentieth `Refusal.reason`, added by R11.**

    A retirement that named a successor is a statement that the successor took the
    word's job. Bringing the old word back while the new one is live puts **two live
    words on one meaning**, which is mechanism 4 arriving through the lifecycle -- in
    the registry whose whole thesis is detecting exactly that.

    Not overridable, and it does not need to be: the path back is to retire the
    successor first, which is an ordinary call that records who did it. The refusal
    says so, so the caller is not left guessing whether there is one.
    """
    seed(registry, "capture", definition="the word that replaced it")
    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    refusal = registry.reinstate("watch", "we want it back", reinstated_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "successor_active"
    assert refusal.detail["successor"] == "capture"
    assert refusal.detail["overridable"] is False
    assert "capture" in refusal.detail["path_back"]

    # Nothing was written: the refusal is a refusal, not a warning on a completed act.
    assert [e.event for e in registry.provenance("watch").history].count("reinstated") == 0

    # ...and the path back the refusal names actually works.
    registry.retire("capture", "changed our minds", retired_by="user:sd")
    back = registry.reinstate("watch", "we want it back", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry) and back.status == "active"


@pytest.mark.requires_capability("indexes_membership")
def test_c9_11_reinstate_is_refused_where_it_cannot_be_recorded_and_never_no_ops_silently(
    adapter, make_registry
):
    """**Two halves of one rule: this call never does something quietly.**

    *Half one -- `stores_events=False`.* `reinstate` is the **only** call in this
    surface that REMOVES a lifecycle fact from the live row: `retire` adds a tombstone,
    `merge_types` adds an alias and a tombstone, and nothing anywhere is deleted. The
    event is therefore the record, and on a backend that cannot store one a name would
    come back to life with nothing anywhere saying it had ever been retired or by whom.
    PACKAGE.md 3.6's rule -- *a destructive override that cannot be recorded is
    refused* -- applies, and this is the third call to take it after
    `retire(force=True)` and `merge_types(acknowledge=...)`.

    **The stated cost, which is not a new one:** a `stores_events=False` store cannot
    un-burn a name. That is the world before this row exactly, and it is consistent --
    `retire(force=True)` is already refused on such a store for the same reason.

    *Half two -- the type is not retired.* Nothing was prevented, so it is not a
    refusal; but a call that quietly did nothing is the shape ruling R4 forbade for
    `register_consumer`, so the entry comes back carrying `reinstate_no_op:not_retired`.

    **Needs `indexes_membership` as scaffolding, not as its subject.** Both halves need
    a retirement to exist first, and on a backend that cannot compute an extent `retire`
    refuses with `no_consumer_evidence` (`C9-07`) while `force=True` is refused with
    `cannot_record_override` (`C9-08`) -- so on such a store there is no way to reach a
    retired row to reinstate. That is the honest position rather than a gap: a store
    that cannot record a retirement safely has nothing for this call to undo.
    """
    no_events = make_registry(
        DegradedAdapter(adapter, stores_events=False, why=NO_EVENTS)
    )
    seed(no_events, "watch", definition="a thing a user watches")
    no_events.retire("watch", "classifier drift", retired_by="user:sd")

    refusal = no_events.reinstate("watch", "put it back", reinstated_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override"
    assert refusal.detail["would_clear"]["retire_reason"] == "classifier drift"
    still = [
        t for t in no_events.list_types(include_retired=True).types if t.name == "watch"
    ]
    assert [t.status for t in still] == ["retired"], "and nothing was written"

    # Half two, on a fully capable registry.
    live = make_registry(adapter)
    seed(live, "facility", definition="a Medicare-certified nursing home")
    same = live.reinstate("facility", "belt and braces", reinstated_by="user:sd")
    assert isinstance(same, TypeEntry)
    assert same.status == "active"
    assert "reinstate_no_op:not_retired" in same.warnings, "never a silent no-op"
