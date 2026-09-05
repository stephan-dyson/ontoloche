# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c9_retire.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C9 -- ``retire`` and ``reinstate`` (31). Mechanism 3.

Retirement is guarded by ``consumers``, not by usage.
"""

from __future__ import annotations
import pytest
from ontoloche.aio.adapter import TypeRecord
from ontoloche.types import Consumer, Refusal, ResolveContext, TypeEntry
from ontoloche.aio.contract._support import seed
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter


NO_EVENTS = {"stores_events": "work_link_types has no event table"}

NO_TIMESTAMPS = {"timestamps_usage": "work_link_types has no last_used_at column"}

def _CTX():
    """A resolve context with nothing in it: this group's questions are about the
    registry's own identity answers, not about the scorer's signal."""
    return ResolveContext()

async def _with_live_consumer(registry):
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

@pytest.mark.requires_capability("indexes_membership")
async def test_c9_01_a_live_consumer_refuses_the_retirement(registry):
    await _with_live_consumer(registry)
    refusal = await registry.retire("task", "we think nobody uses it", retired_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "live_consumers"
    assert refusal.detail["gates_on"] == ["comment_service.can_comment"]
    assert (await registry.list_types(status="active")).types

@pytest.mark.requires_capability("indexes_membership")
async def test_c9_02_force_overrides_and_records_or_is_refused(adapter, make_registry):
    registry = await make_registry(adapter)
    await _with_live_consumer(registry)

    # The "overrides AND records" half needs a backend that can record. On one that
    # cannot, the whole call is the refusal below -- which is this test's other half and
    # the more important one. Split by row 3c's capability sweep.
    if (await adapter.capabilities()).stores_events:
        forced = await registry.retire(
            "task", "the service is being deleted", retired_by="user:sd", force=True
        )
        assert isinstance(forced, TypeEntry) and forced.status == "retired"
        retired_events = [e for e in forced.provenance.history if e.event == "retired"]
        assert retired_events[0].detail["forced"] is True
        assert retired_events[0].detail["overrode"] == ["comment_service.can_comment"]

    # On a backend that cannot record the override, the override is refused. An
    # unrecorded, unattributable destructive change is what this registry exists to
    # prevent, and a store with no audit trail has not earned the right to be overridden.
    blind = await make_registry(AsyncDegradedAdapter(adapter, stores_events=False, why=NO_EVENTS))
    await seed(blind, "note", predicates=["commentable"])
    refusal = await blind.retire("note", "and this one too", retired_by="user:sd", force=True)
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override"
    assert refusal.detail["why"] == NO_EVENTS["stores_events"]

@pytest.mark.requires_capability("indexes_membership")
async def test_c9_03_retiring_without_usage_evidence_proceeds_but_warns(adapter, make_registry):
    setup = await make_registry(adapter)
    await seed(setup, "blocks", definition="this work item blocks that one")
    await setup.record_use("blocks")

    half_blind = await make_registry(AsyncDegradedAdapter(adapter, timestamps_usage=False, why=NO_TIMESTAMPS))
    assert (await half_blind.usage("blocks")).orphaned is None

    entry = await half_blind.retire("blocks", "the feature was removed", retired_by="user:sd")
    assert isinstance(entry, TypeEntry)
    assert entry.status == "retired"
    assert "retired_without_usage_evidence" in entry.warnings

@pytest.mark.requires_capability("indexes_membership")
async def test_c9_04_a_retired_name_is_not_reusable(registry, adapter):
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded by `capture`", retired_by="user:sd")

    answer = await registry.propose_type("watch", "a completely different watch", [], "user:pm")
    assert isinstance(answer, TypeEntry)
    assert answer.status == "retired"
    assert "name_previously_retired" in answer.warnings

    stored = await adapter.get_type("default", "watch")
    assert stored.status == "retired", "no new entry was created under the retired name"
    assert stored.definition == "a thing a user watches", (
        "and the retired row was not overwritten by the new proposer's wording"
    )

async def test_c9_05_retire_requires_a_reason(registry):
    await seed(registry, "watch", definition="a thing a user watches")
    with pytest.raises(ValueError):
        await registry.retire("watch", "", retired_by="user:sd")
    with pytest.raises(ValueError):
        await registry.retire("watch", "   ", retired_by="user:sd")

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c9_06_the_successor_is_recorded_and_surfaces_in_provenance(registry):
    await seed(registry, "capture", definition="the word that replaced it")
    await seed(registry, "watch", definition="a thing a user watches")
    entry = await registry.retire(
        "watch", "superseded by `capture`", retired_by="user:sd", successor="capture"
    )
    assert isinstance(entry, TypeEntry)

    retired_events = [e for e in (await registry.provenance("watch")).history if e.event == "retired"]
    assert retired_events[0].detail["successor"] == "capture"
    assert retired_events[0].detail["reason"] == "superseded by `capture`"

@pytest.mark.requires_capability("stores_events")
async def test_c9_07_an_unknowable_consumer_set_blocks_the_retirement(adapter, make_registry):
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
    blind = await make_registry(AsyncDegradedAdapter(adapter, indexes_membership=False))
    await seed(blind, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(blind, "task", definition="a unit of work", predicates=["commentable"])
    await blind.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    report = await blind.consumers("task")
    assert report.gates_on == (), "the extent is unknowable, so the report is empty..."
    assert report.complete is False, "...and it already says it is incomplete"

    refusal = await blind.retire("task", "no longer needed", retired_by="user:sd")
    assert isinstance(refusal, Refusal), "an empty gates_on we could not verify must block"
    assert refusal.reason == "no_consumer_evidence"
    assert refusal.detail["overridable"] is True
    assert "could not look" in refusal.detail["why"]
    assert (await blind.list_types(namespace="default")).types, "and nothing was retired"

    overridden = await blind.retire("task", "I accept the risk", retired_by="user:sd", force=True)
    assert isinstance(overridden, TypeEntry) and overridden.status == "retired"

async def test_c9_08_force_is_refused_when_it_cannot_be_recorded_whichever_guard_it_overrides(
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
    tenshen_shaped = await make_registry(
        AsyncDegradedAdapter(adapter, indexes_membership=False, stores_events=False)
    )
    await seed(tenshen_shaped, "commentable", kind="predicate", definition="a code path accepts it")
    await seed(tenshen_shaped, "blocks", definition="this work item blocks that one",
         predicates=["commentable"])
    await tenshen_shaped.register_consumer(
        Consumer(id="aura_render.referent_link", gate="commentable", on_unknown="drop")
    )

    refusal = await tenshen_shaped.retire(
        "blocks", "no longer needed", retired_by="user:sd", force=True
    )
    assert isinstance(refusal, Refusal), "an override nobody can audit is not an override"
    assert refusal.reason == "cannot_record_override"
    assert refusal.detail["gates_on_knowable"] is False, (
        "and it says the consumer set was unknowable, so the reader is not left "
        "believing an empty would_override means nothing was at stake"
    )
    entry = (await tenshen_shaped.list_types(namespace="default")).types
    assert [t.status for t in entry if t.name == "blocks"] == ["active"], "nothing retired"

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c9_09_a_retired_name_can_be_reinstated_and_resolves_again(registry, adapter):
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
    from ontoloche.types import ResolveContext

    # The retirement names a SUCCESSOR, and the successor is then retired too -- which
    # is what makes the `successor` assertion below mean anything. [Observed, row 3e
    # second adversarial round] this test used a retirement with no successor, so the
    # `successor is None` leg was vacuous: a `reinstate` that kept the field ran the
    # whole suite green, on the one field §5.9b spends a block quote on.
    await seed(registry, "capture", definition="the word that replaced it")
    await seed(registry, "watch", definition="a thing a user watches")
    retired = await registry.retire(
        "watch", "classifier drift, we think", retired_by="user:sd", successor="capture"
    )
    assert isinstance(retired, TypeEntry) and retired.status == "retired"
    await registry.retire("capture", "and that one went too", retired_by="user:sd")

    gone = await registry.resolve_type("watch", ResolveContext(), tier="opus")
    assert gone.outcome != "existing", "C3-10: a retired name is not an existing one"

    back = await registry.reinstate("watch", "the drift correction was wrong", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry), back
    assert back.status == "active"
    assert "retired_without_usage_evidence" not in back.warnings

    again = await registry.resolve_type("watch", ResolveContext(), tier="opus")
    assert again.outcome == "existing", "a reinstated name resolves again"
    assert again.type is not None and again.type.name == "watch"
    assert again.confidence == 1.0

    events = [e for e in (await registry.provenance("watch")).history if e.event == "reinstated"]
    assert len(events) == 1
    assert events[0].actor == "user:sd"
    assert events[0].detail["reason"] == "the drift correction was wrong"
    # **Every field, not one.** §5.9b says the `reinstated` event "carries every one of
    # them", and this asserted only `retire_reason` -- so a mutation dropping the other
    # three ran the whole suite green, on the record `cannot_record_override` refuses
    # the entire call to protect. Row 3e, third adversarial round.
    assert events[0].detail["retire_reason"] == "classifier drift, we think", (
        "the retirement is cleared from the row and kept in the history, never lost"
    )
    assert events[0].detail["retired_by"] == "user:sd"
    assert events[0].detail["retired_at"], "the when, not just the why"
    assert events[0].detail["successor"] == "capture"

    # **The clearing itself, asserted on the STORED RECORD.** `TypeEntry` has no
    # retirement fields, so the only surface where the difference is visible is
    # `TypeRecord` -- which is exactly the surface a third-party backend implements.
    # [Observed, row 3e first adversarial round] a `reinstate` identical to the shipped
    # one except that it kept all four fields on the live row ran the whole suite green.
    # That is the half of R11 §5.9b spends a block quote on, and the sole premise of the
    # `cannot_record_override` refusal `C9-11` covers, so leaving it unasserted made
    # that refusal buy nothing testable.
    stored = await adapter.get_type("default", "watch", kind="entity")
    assert stored is not None and stored.status == "active"
    for field in ("retire_reason", "retired_by", "retired_at", "successor"):
        assert getattr(stored, field, None) is None, (
            f"{field} is a statement about a retirement that is no longer in force"
        )

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c9_10_reinstate_refuses_when_the_successor_is_active(registry):
    """**`successor_active` -- the twentieth `Refusal.reason`, added by R11.**

    A retirement that named a successor is a statement that the successor took the
    word's job. Bringing the old word back while the new one is live puts **two live
    words on one meaning**, which is mechanism 4 arriving through the lifecycle -- in
    the registry whose whole thesis is detecting exactly that.

    Not overridable, and it does not need to be: the path back is to retire the
    successor first, which is an ordinary call that records who did it. The refusal
    says so, so the caller is not left guessing whether there is one.
    """
    await seed(registry, "capture", definition="the word that replaced it")
    await seed(registry, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    refusal = await registry.reinstate("watch", "we want it back", reinstated_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "successor_active"
    assert refusal.detail["successor"] == "capture"
    assert refusal.detail["overridable"] is False
    assert "capture" in refusal.detail["path_back"]

    # Nothing was written: the refusal is a refusal, not a warning on a completed act.
    assert [e.event for e in (await registry.provenance("watch")).history].count("reinstated") == 0

    # ...and the path back the refusal names actually works.
    await registry.retire("capture", "changed our minds", retired_by="user:sd")
    back = await registry.reinstate("watch", "we want it back", reinstated_by="user:sd")
    assert isinstance(back, TypeEntry) and back.status == "active"

@pytest.mark.requires_capability("indexes_membership")
async def test_c9_11_reinstate_is_refused_where_it_cannot_be_recorded_and_never_no_ops_silently(
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
    no_events = await make_registry(
        AsyncDegradedAdapter(adapter, stores_events=False, why=NO_EVENTS)
    )
    await seed(no_events, "watch", definition="a thing a user watches")
    await no_events.retire("watch", "classifier drift", retired_by="user:sd")

    refusal = await no_events.reinstate("watch", "put it back", reinstated_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "cannot_record_override"
    assert refusal.detail["would_clear"]["retire_reason"] == "classifier drift"
    still = [
        t for t in (await no_events.list_types(include_retired=True)).types if t.name == "watch"
    ]
    assert [t.status for t in still] == ["retired"], "and nothing was written"

    # Half two, on a fully capable registry.
    live = await make_registry(adapter)
    await seed(live, "facility", definition="a Medicare-certified nursing home")
    same = await live.reinstate("facility", "belt and braces", reinstated_by="user:sd")
    assert isinstance(same, TypeEntry)
    assert same.status == "active"
    assert "reinstate_no_op:not_retired" in same.warnings, "never a silent no-op"

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c9_12_reinstate_refuses_to_manufacture_two_live_words_for_one_meaning(registry):
    """**`alias_collision` -- the twenty-first `Refusal.reason`, and the door R11
    opened.** Row 3e, first adversarial round; reproduced on the UC3 fixture.

    `merge_types` refuses by default and carries four non-overridable refusals;
    `propose_type` on a name a live type holds as an alias returns the tombstone. So
    mechanism 4 -- two active entries with one word between them -- was *thought* to be
    unreachable through the surface. It was not: three adversarial rounds found three
    different walks into it, and `C16-06` is the whole-store invariant that catches the
    class rather than the entrance. This one is `reinstate`'s, in **four ordinary
    calls**:

        merge bike_lane into cycle_track    # cycle_track gains the alias `bike_lane`
        retire cycle_track                  # ...so `successor_active` no longer bites
        reinstate bike_lane                 # allowed: its successor is retired
        reinstate cycle_track               # BOTH now active, and cycle_track still
                                            #   carries `bike_lane` as an alias

    [Observed] the fourth call succeeded with no refusal and no warning, leaving a
    consumer's alias map saying `bike_lane -> cycle_track` while the registry's own
    `resolve_type` answered `bike_lane -> bike_lane` at confidence 1.0. That is the
    kill-criterion state, created by the registry whose thesis is detecting it.

    **Refused, not warned.** This is not an uncertainty -- it is a collision the
    registry can see, inside ONE namespace, which is the case §2.6 says scoping exists
    to prevent rather than preserve. The refusal names a real path back (retire the
    other word) and both directions of the collision are checked, because either side
    of a merge can be the one being reinstated.
    """
    await seed(registry, "bike_lane", definition="A DOT bike facility.")
    await seed(registry, "cycle_track",
         definition="A DOT bike facility. The newer term for the same thing.")
    merged = await registry.merge_types(
        "bike_lane", "cycle_track", "one word for one facility", merged_by="user:dot",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    await registry.retire("cycle_track", "we changed our minds", retired_by="user:dot")

    back = await registry.reinstate("bike_lane", "the merge was a mistake", reinstated_by="user:dot")
    assert isinstance(back, TypeEntry) and back.status == "active", (
        "reinstating the merged-away word is legal: its successor is retired"
    )

    refusal = await registry.reinstate(
        "cycle_track", "and we want this one back too", reinstated_by="user:dot"
    )
    assert isinstance(refusal, Refusal), (
        "two active entries with one word between them is mechanism 4"
    )
    assert refusal.reason == "alias_collision"
    assert refusal.detail["collides_with"] == "bike_lane"
    assert refusal.detail["relation"] == "alias"
    assert refusal.detail["overridable"] is False
    assert "bike_lane" in refusal.detail["path_back"]

    live = sorted([t.name for t in (await registry.list_types()).types])
    # `equivalent_to` is seeded at store creation (EDGES.md 3.1); "nothing was written"
    # is about the refused reinstatement, not about the store being empty.
    assert live == ["bike_lane", "equivalent_to"], "and nothing was written"

    # The other direction: the same collision reached with the reinstatements swapped.
    # `successor_active` catches the first step there, which is why BOTH guards are
    # needed and neither is redundant.
    other_way = await registry.retire("bike_lane", "put it back the way it was",
                                retired_by="user:dot")
    assert isinstance(other_way, TypeEntry)
    revived = await registry.reinstate("cycle_track", "take two", reinstated_by="user:dot")
    assert isinstance(revived, TypeEntry) and revived.status == "active"
    blocked = await registry.reinstate("bike_lane", "and now this one", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal)
    assert blocked.reason in ("alias_collision", "successor_active")

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c9_13_the_successor_relation_is_checked_through_the_chain_not_one_hop(registry):
    """**The path back that `successor_active` itself names ended in the state the
    refusal exists to forbid.** Row 3e, second adversarial round; reproduced on both
    reference backends.

    `retire(successor=...)` writes **no alias**, so `C9-12`'s guard does not see it, and
    `reinstate` **clears `successor` off the live row** -- so a one-hop check on that
    column is a check on a fact this very call deletes. Walk it:

        retire bike_lane, successor=cycle_track
        reinstate bike_lane        -> Refusal(successor_active), path_back="retire
                                      'cycle_track' first"
        retire cycle_track          # ...so the caller does exactly that
        reinstate bike_lane        -> allowed          <- `C9-10` stopped HERE
        reinstate cycle_track      -> both active, one meaning, no refusal

    The guard is now read out of the `retired` EVENTS, transitively, in both
    directions: forward (this word was replaced by something that is live) and backward
    (something live was replaced by this word). Events are available because
    `reinstate` refuses `cannot_record_override` first -- the order of the two guards
    is load-bearing.
    """
    await seed(registry, "cycle_track", definition="A DOT bike facility, current term.")
    await seed(registry, "bike_lane", definition="A DOT bike facility, older term.")
    await registry.retire(
        "bike_lane", "superseded by cycle_track", retired_by="user:tlc",
        successor="cycle_track",
    )

    refused = await registry.reinstate("bike_lane", "we want it back", reinstated_by="user:tlc")
    assert isinstance(refused, Refusal) and refused.reason == "successor_active"
    assert "cycle_track" in refused.detail["path_back"]

    # Follow the path the refusal names.
    await registry.retire("cycle_track", "changed our minds", retired_by="user:dot")
    back = await registry.reinstate("bike_lane", "we want it back", reinstated_by="user:tlc")
    assert isinstance(back, TypeEntry) and back.status == "active"

    blocked = await registry.reinstate("cycle_track", "and this one", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal), (
        "two live words for one meaning, reached by following the documented path back"
    )
    assert blocked.reason == "alias_collision"
    assert blocked.detail["collides_with"] == "bike_lane"
    assert blocked.detail["relation"] == "predecessor"
    assert sorted([t.name for t in (await registry.list_types()).types]) == [
        "bike_lane",
        "equivalent_to",  # seeded at store creation -- EDGES.md 3.1
    ]

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c9_14_the_chain_is_transitive_and_the_scan_is_namespace_scoped(registry):
    """**Two hops, and one namespace.** Row 3e, second adversarial round.

    *Transitive:* `street_name` replaced by `on_street` replaced by `corridor` needs no
    second retirement at all -- reinstating `street_name` while `corridor` is live is
    two live words for one meaning, two hops apart.

    *Namespace-scoped:* the scan must not reach across namespaces. INTERFACE.md §2.6
    makes scoping the answer to mechanism 4, so two agencies holding one word is the
    state namespaces exist to **preserve** -- a guard that refused a legitimate
    reinstatement because another agency's namespace holds the word would delete UC3's
    whole premise. [Observed] a mutation dropping the `namespace` filter from the scan
    ran the full suite green.
    """
    for name in ("street_name", "on_street", "corridor"):
        await seed(registry, name, definition=f"the {name} of a DOT segment")
    await registry.retire("street_name", "renamed", retired_by="user:dot", successor="on_street")
    await registry.retire("on_street", "renamed again", retired_by="user:dot", successor="corridor")

    two_hops = await registry.reinstate("street_name", "bring it back", reinstated_by="user:dot")
    assert isinstance(two_hops, Refusal) and two_hops.reason == "alias_collision"
    assert two_hops.detail["collides_with"] == "corridor"
    assert two_hops.detail["relation"] == "successor"

    # ...and the identical word live in ANOTHER namespace is not a collision.
    await seed(registry, "corridor", namespace="dpr", definition="a parks corridor")
    await seed(registry, "greenway", namespace="dpr", definition="a parks greenway")
    await registry.retire("greenway", "renamed", retired_by="user:dpr", namespace="dpr",
                    successor="corridor")
    await registry.retire("corridor", "and that too", retired_by="user:dpr", namespace="dpr")
    scoped = await registry.reinstate("greenway", "back please", reinstated_by="user:dpr",
                                namespace="dpr")
    assert isinstance(scoped, TypeEntry) and scoped.status == "active", (
        "`default:corridor` is live and irrelevant -- 2.6 keeps namespaces apart"
    )

@pytest.mark.requires_capability("indexes_membership")
async def test_c9_15_reinstate_says_when_it_could_not_look_and_when_it_is_not_yet_durable(
    adapter, make_registry
):
    """**Three things §5.9b promises that nothing was checking.** Row 3e, second
    adversarial round, where three separate mutations of `reinstate` ran the whole
    suite green.

    1. **`stores_aliases=False`** -- every alias list is empty, so finding no collision
       means *we could not look*. Rule U: the entry comes back carrying
       `reinstate_alias_check_unavailable:<why>`.
    2. **A backend that pages** -- the collision scan reads `find_types` to exhaustion
       via `next_after`, and if the backend still declares the answer partial the same
       warning carries its reason. Reproduced before the fix: the exact end state
       `C9-12` asserts is refused, reached with **no refusal and no warning**.
    3. **A savepoint scope** -- `reinstate` is a WRITE, so ruling R5's durability
       sentence belongs on its result like every other write's. Reproduced before the
       fix: dropping `_written` from this call was conformant, because no leg drove
       `reinstate` over a borrowed connection.
    """
    from ontoloche.aio.contract.doubles import AsyncDegradedAdapter

    blind = await make_registry(AsyncDegradedAdapter(adapter, stores_aliases=False))
    await seed(blind, "watch", definition="a thing a user watches")
    await blind.retire("watch", "drift", retired_by="user:sd")
    if (await blind.adapter.capabilities()).stores_events:
        entry = await blind.reinstate("watch", "put it back", reinstated_by="user:sd")
        assert isinstance(entry, TypeEntry)
        assert any(
            w.startswith("reinstate_alias_check_unavailable:") for w in entry.warnings
        ), "we could not look, and an absence we could not check is not an absence"

    paging = await make_registry(AsyncDegradedAdapter(adapter, page_cap=1))
    await seed(paging, "first_word", definition="one")
    await seed(paging, "second_word", definition="two")
    await paging.retire("second_word", "drift", retired_by="user:sd")
    if (await paging.adapter.capabilities()).stores_events:
        entry = await paging.reinstate("second_word", "put it back", reinstated_by="user:sd")
        assert isinstance(entry, TypeEntry)
        assert any(
            w.startswith("reinstate_alias_check_unavailable:") for w in entry.warnings
        ), "the backend said its page was partial; an absence over it is not an absence"

    borrowed = await make_registry(AsyncDegradedAdapter(adapter, transaction_scope="savepoint"))
    await seed(borrowed, "third_word", definition="three")
    await borrowed.retire("third_word", "drift", retired_by="user:sd")
    if (await borrowed.adapter.capabilities()).stores_events:
        entry = await borrowed.reinstate("third_word", "put it back", reinstated_by="user:sd")
        assert isinstance(entry, TypeEntry)
        assert any(
            w.startswith("not_durable_until_host_commits:") for w in entry.warnings
        ), "a write over a borrowed connection is not durable until the host commits"

@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
async def test_c9_16_a_merge_the_guard_can_only_see_in_events_still_blocks(registry, adapter):
    """**The alias column was the guard's only evidence for a merge, and one ordinary
    call erases it.** Row 3e, third adversarial round.

    `merge_types` retires `from_` with `into` as its successor **and** writes the alias
    onto the survivor, and `_lifecycle_collisions` read only `retired` events plus the
    live `aliases` column. `import_types` rewrites a live row -- wiping its aliases --
    so inserting one import into §5.9b's own four-call walk erased the evidence and let
    the walk through: both words active, no refusal, no warning. The graph now reads
    `merged` events too, which is the record neither call can overwrite.
    """
    await seed(registry, "bike_lane", definition="A DOT bike facility.")
    await seed(registry, "cycle_track",
         definition="A DOT bike facility. The newer term for the same thing.")
    merged = await registry.merge_types(
        "bike_lane", "cycle_track", "one word for one facility", merged_by="user:dot",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged

    # An ordinary re-import of the survivor, which rewrites the row and its aliases.
    await registry.import_types(
        [{"name": "cycle_track", "status": "active", "definition": "from the dump"}]
    )
    survivor = await adapter.get_type("default", "cycle_track", kind="entity")
    assert survivor is not None and not survivor.aliases, (
        "the import wiped the alias -- which is the point: the guard cannot rely on it"
    )

    await registry.retire("cycle_track", "we changed our minds", retired_by="user:dot")
    back = await registry.reinstate("bike_lane", "the merge was a mistake", reinstated_by="user:dot")
    assert isinstance(back, TypeEntry) and back.status == "active"

    blocked = await registry.reinstate("cycle_track", "and this one", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal), "the merge is still on the record, in events"
    assert blocked.reason == "alias_collision"
    assert sorted([t.name for t in (await registry.list_types()).types]) == [
        "bike_lane",
        "equivalent_to",  # seeded at store creation -- EDGES.md 3.1
    ]

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c9_17_the_collision_scan_pages_to_exhaustion(adapter, make_registry):
    """**§5.9b says the scan "reads to exhaustion through `next_after`" and nothing
    checked it.** Row 3e, third adversarial round.

    `C9-15`'s paging double returns **no** cursor by design, so it exercises the
    *cannot read the rest* branch and the exhaustion loop is never entered: a mutation
    replacing `cursor = page.next_after` with `cursor = None` ran the whole suite green.
    Against an honest paging backend -- partial **plus** a cursor, which PACKAGE.md
    §3.3 permits and UC3's scale produces -- that mutation silently converts a refusal
    into a warning and lets the collision through.
    """
    from ontoloche.aio.contract.doubles import AsyncDegradedAdapter

    paging = await make_registry(AsyncDegradedAdapter(adapter, page_cap=2, page_cursor=True))
    for filler in ("aa_filler", "bb_filler"):
        await seed(paging, filler, definition=f"a {filler} to push the survivor off page one")
    await seed(paging, "bike_lane", definition="A DOT bike facility.")
    await seed(paging, "cycle_track",
         definition="A DOT bike facility. The newer term for the same thing.")
    merged = await paging.merge_types(
        "bike_lane", "cycle_track", "one word", merged_by="user:dot",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    await paging.retire("cycle_track", "changed our minds", retired_by="user:dot")
    assert isinstance(
        await paging.reinstate("bike_lane", "undo", reinstated_by="user:dot"), TypeEntry
    )

    blocked = await paging.reinstate("cycle_track", "and this", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal), (
        "the survivor is past page one; a scan that stops there misses the collision"
    )
    assert blocked.reason == "alias_collision"

@pytest.mark.requires_capability("indexes_membership", "stores_events")
async def test_c9_18_retire_with_a_successor_takes_the_merges_identity_guards(registry):
    """`ROADMAP.md`'s kill row, THIRD trip -- and the first through a call that is
    not `merge_types`.

    `resolve_type` on a retired name returns its successor at confidence 1.0
    (`INTERFACE.md` 5.3, which this registry calls a guarantee), so
    `retire(successor=)` performs the collapse `merge_types` refuses. Row #6's
    third adversarial round reproduced it: `merge_types("commentable",
    "searchable")` refused `predicate_merge` NON-OVERRIDABLY under all five
    acknowledgements, and the identical pair collapsed through `retire` with no
    refusal, no acknowledgement and no warning -- across kinds too.

    The two guards that transfer are 5.10's refusals #2 and #3, the two about
    IDENTITY rather than about evidence. `force=True` overrides the consumer
    guards, which are about what we could see; it does not override these, which
    are about what would become true.
    """
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "searchable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await seed(registry, "doc", predicates=["searchable"])
    await seed(registry, "person", definition="a human being")

    # The merge is refused non-overridably -- the precondition of this test.
    merge = await registry.merge_types("commentable", "searchable", "duplicate capability",
                                 merged_by="user:sd", acknowledge=["predicate_merge"])
    assert isinstance(merge, Refusal) and merge.reason == "predicate_merge"

    # ... and so is the retirement that would produce the same redirect.
    refusal = await registry.retire("commentable", reason="duplicate capability",
                              retired_by="user:sd", successor="searchable")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "predicate_merge"
    assert refusal.detail["overridable"] is False
    assert refusal.detail["successor"] == "searchable"
    assert sorted(refusal.detail["from_extent"]) == ["task"]
    assert sorted(refusal.detail["into_extent"]) == ["doc"]

    # `force=True` overrides the consumer guards and NOT this one.
    forced = await registry.retire("commentable", reason="I really mean it",
                             retired_by="user:sd", successor="searchable", force=True)
    assert isinstance(forced, Refusal) and forced.reason == "predicate_merge"

    # A successor of another KIND is refused too: a redirect at confidence 1.0
    # would answer a question about one kind with an entry of another.
    crossed = await registry.retire("commentable", reason="close enough",
                              retired_by="user:sd", successor="person")
    assert isinstance(crossed, Refusal) and crossed.reason == "kind_mismatch"
    assert crossed.detail["overridable"] is False

    # The guard is NARROW: a plain retirement, and a retirement whose successor
    # shares a non-empty extent, both still work.
    plain = await registry.retire("commentable", reason="nothing uses it",
                            retired_by="user:sd")
    assert isinstance(plain, TypeEntry) and plain.status == "retired"

    await seed(registry, "linkable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "shareable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "note", predicates=["linkable", "shareable"])
    same = await registry.retire("linkable", reason="genuinely the same set",
                           retired_by="user:sd", successor="shareable")
    assert isinstance(same, TypeEntry), same

async def test_c9_19_a_non_overridable_guard_is_never_reached_through_an_overridable_one(
    adapter, make_registry
):
    """Row 4c, found by ``docs/tools/check_merge_guard.py``. **Row 3c's lesson, applied
    to the second caller.**

    `merge_types` moved its `cannot_record_override` check to *after* its four
    non-overridable refusals in row 3c, and INTERFACE.md §5.10 states why: *"a caller
    trying to acknowledge past the kill row must be told **predicate_merge,
    non-overridable**, not that the audit log is missing."* Answering with the wrong
    reason for the right outcome sends the caller to do something that cannot work.

    **`retire` had the same defect the other way round.** Its overridable consumer
    guards ran first, so on a backend that cannot index membership, retiring one
    predicate with another as its successor was refused **`no_consumer_evidence`** --
    which the refusal itself advertises as overridable with `force=True` -- while the
    true answer was `predicate_merge`, which is not overridable at all and never will
    be. The outcome was safe: the forced call then met the identity guard. What was
    wrong was the story, and the story is what a caller acts on.

    This is the third instance of one class in this repository, and naming it is the
    point: **a non-overridable guard reached through an overridable one.** The kill
    row's first trip was its most dangerous form -- the merge *fell through* to an
    overridable guard and went ahead. This is its mild form, and the mild form is what a
    checker catches before the dangerous one recurs.
    """
    blind = await make_registry(
        AsyncDegradedAdapter(
            adapter,
            indexes_membership=False,
            why={
                "indexes_membership": "this store has no type-predicate table, so an "
                "extent cannot be computed"
            },
        ),
        approval_policy="auto",
    )
    await seed(blind, "commentable", kind="predicate", definition="a capability")
    await seed(blind, "searchable", kind="predicate", definition="a capability")
    await seed(blind, "note", predicates=["commentable"])
    await seed(blind, "doc", predicates=["searchable"])

    refusal = await blind.retire(
        "commentable", "folded into searchable", retired_by="user:sd",
        successor="searchable",
    )
    assert isinstance(refusal, Refusal), refusal
    assert refusal.reason == "predicate_merge", (
        "the identity guards run BEFORE the consumer guards, so a caller is told the "
        "refusal that will not move rather than the one that advertises an override"
    )
    assert refusal.detail["overridable"] is False
    assert refusal.detail["extents_knowable"] is False

    forced = await blind.retire(
        "commentable", "folded into searchable", retired_by="user:sd",
        successor="searchable", force=True,
    )
    assert isinstance(forced, Refusal) and forced.reason == "predicate_merge", (
        "and `force=True` does not move it either -- force overrides what could be "
        "SEEN, never what would become TRUE"
    )

    # The consumer guards still work, and still come second: a retirement with NO
    # successor has no identity question to answer, so the unknowable-extent guard is
    # the one that fires. A reorder that swallowed it would pass every assertion above.
    plain = await blind.retire("searchable", "nobody uses it", retired_by="user:sd")
    assert isinstance(plain, Refusal), plain
    assert plain.reason == "no_consumer_evidence"
    assert plain.detail["overridable"] is True

async def test_c9_20_refusal_one_transfers_to_a_successor_and_force_does_not_move_it(
    adapter, make_registry
):
    """§5.10's refusal **#1**, on `retire(successor=)`. Row 4c, third adversarial round.

    `C9-18` gave this call §5.10's refusals #2 and #3 on the argument that *"the two
    guards that transfer are the two that are about IDENTITY rather than about
    evidence"*. **That filed `different_consumer_sets` under evidence, and it is not.**
    §5.10's own rationale for #1 is *"merging asserts that every consumer of one accepts
    the other — which is exactly the false claim 0.1 describes"*, an identity claim; the
    refusal table marks it *"No. Not by `force`, not by `acknowledge`"*; and
    `ROADMAP.md` states the requirement with no qualification at all — *"It MUST refuse
    when the two have different consumer sets."*

    **[Observed]** a pair `merge_types` refuses under all seven acknowledgements,
    collapsed by `retire(successor=, force=True)`. Two documents disagreed about which
    bucket #1 was in, and the disagreement had a `force=True` door in it.

    `force` overrides what could be **seen**, never what would become **true** — the
    sentence `C9-18` already carries, applied to the guard it left behind.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.indexes_membership:
        pytest.skip(
            "PACKAGE.md 3.2 -- indexes_membership=False makes every extent unknowable, "
            "so `predicate_merge` fires first and this guard is never reached. C9-08 "
            "holds that half"
        )
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable"])
    await registry.register_consumer(
        Consumer(id="app.comments", gate="commentable", on_unknown="drop",
                 owner="team-a", locator="app/comments.py")
    )
    await registry.register_consumer(
        Consumer(id="app.search", gate="searchable", on_unknown="drop",
                 owner="team-b", locator="app/search.py")
    )

    merged = await registry.merge_types(
        "commentable", "searchable", "they look alike", merged_by="user:sd",
        acknowledge=[
            "different_consumer_sets", "predicate_merge", "kind_mismatch",
            "cross_namespace_merge", "retired_operand", "definitions_diverge",
            "no_consumer_evidence",
        ],
    )
    assert isinstance(merged, Refusal) and merged.reason == "different_consumer_sets"
    assert merged.detail["overridable"] is False

    for force in (False, True):
        refused = await registry.retire(
            "commentable", "folded", retired_by="user:sd", successor="searchable",
            force=force,
        )
        assert isinstance(refused, Refusal), (
            f"retire(successor=, force={force}) reaches the identical collapse, so it "
            f"reaches the identical refusal"
        )
        assert refused.reason in ("different_consumer_sets", "live_consumers"), refused
        if refused.reason == "different_consumer_sets":
            assert refused.detail["overridable"] is False

@pytest.mark.requires_capability("stores_events")
async def test_c9_21_a_consumers_gate_and_a_types_usage_follow_the_identity(
    adapter, make_registry
):
    """**Ruling R38 was ruled for BOTH documents and shipped for one call.** Row 4c, r3.

    `INTERFACE.md` §2.1 says *"a reference to a type resolves to the identity that type
    now belongs to"* — and it landed in `resolve_type` and `neighbors` while every other
    surface holding a reference went on comparing the written string. Two of those are
    confident false negatives in the calls §5.9 guards a retirement with:

    * **`Consumer.gate`.** A live gating consumer of an absorbed predicate was filed
      under `would_drop` on the survivor **with no warning**, and `retire(survivor)` then
      succeeded with **no `live_consumers` refusal** — verbatim the row-3c defect
      `_consumer_report`'s own comment calls *"the exact opposite of the truth"*, one
      axis along.
    * **`usage`.** 500 uses recorded under the word the registry says still resolves left
      the survivor reading `count=0, orphaned=True, why="no use of this type has been
      recorded"`, and `list_types(orphaned=True)` nominated it for retirement. §5.7 calls
      that *"the sensor for the venture's core bet"*; it read zero on the most-used word
      in the vocabulary.

    `record_use` still writes under whichever name the caller used — the record is what
    happened, and nothing rewrites it. It is the **report** that sums the identity.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.indexes_membership or not registry.caps.counts_usage:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend cannot compute an extent or does not count "
            "usage, so neither half of this has a fact to be right or wrong about"
        )
    await seed(registry, "commentable", kind="predicate", definition="can carry comments")
    await seed(registry, "searchable", kind="predicate", definition="can carry comments")
    await seed(registry, "note", predicates=["commentable", "searchable"])
    merged = await registry.merge_types(
        "commentable", "searchable", "one word for one capability", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged

    await registry.register_consumer(
        Consumer(id="app.comments", gate="commentable", on_unknown="drop",
                 owner="team-a", locator="app/comments.py")
    )
    report = await registry.consumers("searchable")
    assert [c.id for c in report.gates_on] == ["app.comments"], (
        "the gate names the word the registry says still resolves, at confidence 1.0 -- "
        "so it gates on this type"
    )
    assert not report.would_drop, (
        "and it is NOT a consumer that would silently drop this type, which is the "
        "opposite claim"
    )
    blocked = await registry.retire("searchable", "no longer needed", retired_by="user:sd")
    assert isinstance(blocked, Refusal) and blocked.reason == "live_consumers", (
        "§5.9 guards retirement with `consumers`, and it can only guard what that call "
        "can see"
    )

    for _ in range(5):
        await registry.record_use("commentable", by="svc.notes")
    survivor = await registry.usage("searchable")
    assert survivor.count == 5, (
        "usage is summed over the IDENTITY -- a survivor reading zero about the "
        "most-used word in the vocabulary is §5.7's own named failure"
    )
    assert survivor.orphaned is not True, (
        "and it is not nominated for retirement as an orphan. `orphaned is None` on a "
        "backend that cannot timestamp usage is Rule U and correct; `True` here would "
        "be the confident false negative"
    )

@pytest.mark.requires_capability("stores_events")
async def test_c9_22_a_successor_that_does_not_exist_yet_is_refused(registry):
    """**`ROADMAP.md`'s kill row, SEVENTH trip — the forward-declared successor.**
    Row 4d, first adversarial round, lens A.

    Every one of §5.10's identity guards on `retire(successor=)` is evaluated against the
    successor's **row** — refusal #1 (`different_consumer_sets`, transferred by `C9-20`),
    #2 (`predicate_merge`) and #3 (`kind_mismatch`). Naming a successor **before it is
    registered** gave all three nothing to compare, so none of them ran; the word was
    then created by an ordinary `propose_type` + `approve`, and `resolve_type` cashed the
    redirect at confidence **1.0** — which §5.3 calls a guarantee — over a pair nothing
    had ever compared.

    **[Observed]** on both fully-capable legs and the async mirror. The `kind` case is
    worse than the predicate case and is asserted below: a question about a `predicate`
    answered with an `entity` at 1.0 is refusal #3 verbatim, and the **Q56 default cannot
    warn about it**, because it re-verifies predicate pairs and this is not one.

    **A guard that could not be EVALUATED has not said the collapse is safe.** Rule U, at
    the one call §5.3 calls a guarantee — and it is the sixth trip's own shape applied to
    the guards the sixth trip's commit shipped: the guard looked, found nothing, and then
    the fact arrived.

    The narrowing is asserted too: retiring toward a successor that **does** exist and
    agrees is still legal, and the refusal names the one reordering that fixes it.
    """
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable"])

    refusal = await registry.retire(
        "commentable", "superseded by a word we have not registered yet",
        retired_by="user:sd", successor="searchable",
    )
    assert isinstance(refusal, Refusal), (
        "naming a successor that does not exist skips every identity guard, and the "
        "word can be created afterwards"
    )
    assert refusal.reason == "successor_unregistered"
    assert refusal.detail["overridable"] is False
    assert "searchable" in refusal.detail["why"]

    # ...and `force` does not open it either: force overrides what could be SEEN, never
    # what would become TRUE.
    forced = await registry.retire(
        "commentable", "we really mean it", retired_by="user:sd",
        successor="searchable", force=True,
    )
    assert isinstance(forced, Refusal) and forced.reason == "successor_unregistered"

    # **The guard is narrowed, not banned.** Register the successor first -- the one
    # reordering the refusal names -- and the identical retirement is legal.
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "doc", predicates=["searchable"])
    await seed(registry, "shared", predicates=["commentable", "searchable"])
    # Extents now differ, so the IDENTITY guard is what answers -- which is the point:
    # a real guard ran, instead of no guard at all.
    answered = await registry.retire(
        "commentable", "superseded", retired_by="user:sd", successor="searchable",
    )
    assert isinstance(answered, Refusal) and answered.reason == "predicate_merge", (
        "with the successor registered there is finally something to compare, and the "
        "refusal is the identity guard rather than the absence of one"
    )

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c9_23_reinstate_asks_the_collision_question_its_sibling_asks(
    adapter, make_registry
):
    """**§5.9b's own named failure, reached through `reinstate`.** Row 4d, round 1.

    Row 4c gave `reinstate` §5.10's **extent** guards over the aliases it re-activates.
    It never asked §5.9b's **collision** question — *is one of those dormant aliases
    already held by a LIVE entry?* — which is the question its sibling `import_types`
    asks with `_alias_clash` on the same field.

    So a row retired while carrying an alias, and a live entry that comes to answer to
    that word while the row is dormant, produce **two active entries holding one word
    between them** the moment the row is reinstated — `C16-06`'s whole-store invariant
    and mechanism **4** itself, in four ordinary calls.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["searchable", "taggable"])

    parked = await registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentable"], "status": "active"}],
        namespace="default", kind="predicate",
    )
    assert "commentable" in (parked[0].aliases or ()), parked[0].warnings
    assert isinstance(
        await registry.retire("searchable", "parked", retired_by="user:sd", force=True),
        TypeEntry,
    )

    # **AMENDED, row 6d, the fix for the SIXTEENTH trip.** This step used to be an
    # ordinary `import_types` alias write, and that write is now REFUSED
    # `word_held_by_tombstone` -- it is the sixteenth trip's own construction, and the
    # door that let the collision be built is the door that fix closes. The subject of
    # this id is `reinstate`'s collision question, not the route to the state, so the
    # route moves BELOW the doors and the door's new refusal is asserted here as the
    # proof it is closed. That is ruling **R80**'s own pattern for a state the doors no
    # longer permit: *pin the impossibility as a test rather than carry it as a claim.*
    blocked = await registry.import_types(
        [{"name": "taggable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentable"], "status": "active"}],
        namespace="default", kind="predicate",
    )
    assert "import_refused:word_held_by_tombstone" in (blocked[0].warnings or ()), (
        "the alias-write door must refuse a word a tombstone still answers to -- "
        "the kill row's SIXTEENTH trip"
    )
    written = await adapter.get_type("default", "taggable", kind="predicate")
    assert written is not None and "commentable" not in (written.aliases or ()), (
        "nothing was written: a refusal is a refusal, not a warning on a completed act"
    )

    # The state this id is about, seeded BELOW the doors, because no door will build it
    # any more. `reinstate`'s guard must still refuse it.
    live = await adapter.get_type("default", "taggable", kind="predicate")
    assert live is not None
    await adapter.put_type(TypeRecord(**{**live.__dict__, "aliases": ("commentable",)}))

    refusal = await registry.reinstate("searchable", "unparked", reinstated_by="user:sd")
    assert isinstance(refusal, Refusal), (
        "re-activating this row puts two live entries under one word -- 5.9b's own "
        "named failure, and `import_types` refuses the identical act"
    )
    assert refusal.reason == "alias_collision"
    assert refusal.detail["overridable"] is False
    assert refusal.detail["held_by"] == "taggable"

    # Nothing was written: a refusal is a refusal, not a warning on a completed act.
    assert (await registry.list_types(namespace="default")).types
    assert [
        t.status for t in (await registry.list_types(namespace="default", include_retired=True)).types
        if t.name == "searchable"
    ] == ["retired"]

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_24_reinstate_asks_the_mirror_question_and_a_word_is_not_its_own_successor(
    adapter, make_registry
):
    """**Two halves of `reinstate`/`retire` that round 1's fixes left open.** Round 2.

    **(a) The mirror case.** Round 1 gave `reinstate` `_alias_clash` over the aliases the
    row being brought back carries — fenced behind `if dormant:`. The row may carry
    **none** while another live row holds **its name** as an alias, which is exactly the
    shape `import_types` writes, and that never entered the branch. Four ordinary calls
    then left two live entries under one word. `rec.name` is already in `_alias_clash`'s
    own `wanted` set, so the dormant-free case is precisely what it covers.

    **(b) A word is not its own successor.** `retire(X, successor=X)` was accepted, and
    the tombstone then said *"this word now means this word"* — a claim nobody made, and
    a cycle `_identity_closure` has to keep guarding for no reason.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "commentable", definition="a word")
    await seed(registry, "searchable", definition="a word")
    assert isinstance(
        await registry.retire("commentable", "parked", retired_by="user:sd", force=True),
        TypeEntry,
    )
    held = (await registry.import_types(
        [{"name": "searchable", "kind": "entity", "definition": "a word",
          "aliases": ["Commentable"], "status": "active"}],
        namespace="default", kind="entity",
    ))[0]
    assert "Commentable" in (held.aliases or ()), held.warnings

    refusal = await registry.reinstate("commentable", "we want it back", reinstated_by="user:sd")
    assert isinstance(refusal, Refusal), (
        "`searchable` answers to this word already -- reinstating leaves two live "
        "entries holding one word, which is 5.9b's own named failure"
    )
    assert refusal.reason == "alias_collision"
    assert refusal.detail["overridable"] is False

    # (b)
    await seed(registry, "aaa", definition="a word")
    selfish = await registry.retire("aaa", "x", retired_by="user:sd", successor="aaa")
    assert isinstance(selfish, Refusal) and selfish.reason == "successor_is_self", (
        "its OWN reason: `successor_unregistered` says *register the successor first*, "
        "which is false here and is a sentence a caller would act on"
    )
    assert (await registry.adapter.get_type("default", "aaa")).status == "active", "nothing written"

@pytest.mark.requires_capability("stores_events")
async def test_c9_25_a_retired_successor_leaves_the_old_word_resolving_to_nothing(registry):
    """**§5.10's promise, destroyed with no refusal and no warning.** Row 4d, round 3.

    `retire(a, successor=b)` where `b` is **itself retired** leaves `a` resolving to
    nothing — and §5.10 promises *"the old word still resolves"*. `merge_types` refuses
    the identical act `retired_operand` and lets a caller acknowledge past it; this door
    did not ask at all.

    **Overridable**, exactly as §5.10's is — `force` is this call's acknowledgement —
    because the outcome is a **loss** rather than a false claim, and a steward may mean
    it. `C17-45` is the test that means it: constructing a cycle is its subject.
    """
    for name in ("ma", "mb"):
        await seed(registry, name, definition="a word")
    assert isinstance(
        await registry.retire("mb", "gone", retired_by="user:sd", force=True), TypeEntry
    )

    refusal = await registry.retire("ma", "folded", retired_by="user:sd", successor="mb")
    assert isinstance(refusal, Refusal) and refusal.reason == "retired_operand"
    assert refusal.detail["overridable"] is True
    assert (await registry.adapter.get_type("default", "ma")).status == "active", "nothing written"

    # ...and a steward who means it says so.
    assert isinstance(
        await registry.retire("ma", "folded", retired_by="user:sd", successor="mb", force=True),
        TypeEntry,
    )

async def _alias_only_predicate(registry, *, alias="zzz_widget_flag"):
    """`commentable`, carrying an alias no row holds, with `taggable`'s extent equal."""
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    await seed(registry, "bbb_memo", predicates=["commentable", "taggable"])
    rows = await registry.import_types(
        [
            {
                "name": "commentable",
                "status": "active",
                "aliases": [alias],
                "definition": "a capability",
            }
        ],
        kind="predicate",
    )
    return rows[0] if rows else None

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_26_retire_with_a_successor_re_points_the_aliases_it_guards(
    adapter, make_registry
):
    """Ruling **R75**. The words a retirement re-points must still resolve to the
    successor -- and until row 6c they stopped.

    **[Observed, row 6c's design test, sqlite and postgres, entity and predicate]**
    ``resolve_type`` on an alias of the retired row went from ``existing / commentable /
    1.0`` -- the confidence INTERFACE.md 5.3 calls a **guarantee** -- to ``proposal /
    None / 0.3568``, because ``_alias_map`` scans **active** rows only and the word's
    holder had just been retired. The guard on this call has been reading those words as
    *transferred* since row 4d and this path transferred none.

    The write is ``merge_types``' own line one call along: the successor takes the words
    the retired row answered to, deduplicated, and the retired row **keeps its own** --
    a tombstone is a record of what a word meant, and editing it would be rewriting a
    provenance-bearing row (INTERFACE.md 5.8).
    """
    registry = await make_registry(adapter)
    row = await _alias_only_predicate(registry)
    assert row is not None and "zzz_widget_flag" in (row.aliases or ()), row

    before = await registry.resolve_type("zzz_widget_flag", _CTX(), tier="unspecified")
    assert before.outcome == "existing" and before.type.name == "commentable"
    assert before.confidence == 1.0

    retired = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(retired, TypeEntry), retired

    after = await registry.resolve_type("zzz_widget_flag", _CTX(), tier="unspecified")
    assert after.outcome == "existing", (after.outcome, after.confidence)
    assert after.type.name == "taggable"
    assert after.confidence == 1.0, "the redirect is real, and now it is real by a write"

    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "taggable"]
    assert "zzz_widget_flag" in survivor[0].aliases
    assert "zzz_widget_flag" in retired.aliases, (
        "the tombstone keeps its own words; `merge_types` leaves them on the absorbed "
        "row for the same reason"
    )

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_27_a_refused_retirement_writes_no_alias_onto_the_successor(
    adapter, make_registry
):
    """Ruling **R75**, and this is the half a careless fix deletes.

    *The write a guard permits and the write a call performs must be the same write* --
    the kill row's TENTH trip stated from the other end. The alias transfer happens
    **only** where ``_alias_identity_breach`` passed on exactly those words, so a
    retirement the identity guard refuses leaves the successor untouched: no tombstone,
    no alias, nothing.

    **The fixture is Q77's own observation, and it is the STALE shape** (the kill row's
    sixth trip): the alias is written while every extent agrees, the world then moves,
    and the retirement arrives with the ROW pair still agreeing and the ALIAS pair no
    longer agreeing. So the refusal is the guard firing on the transfer specifically --
    the case row 6b described as *"a legal retirement refused `predicate_merge` about a
    transfer that does not happen."* It happens now, and the refusal is therefore about
    a write rather than about a phantom.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    # t0 -- every extent agrees, so the alias is legal when it is written. `searchable`
    # is retired first because `alias_collision` forbids two ACTIVE entries holding one
    # word between them (§5.9b): an alias always names a word no live row answers to.
    await seed(registry, "aaa_note", predicates=["commentable", "taggable", "searchable"])
    assert isinstance(
        await registry.retire("searchable", "an ordinary, permitted governance act",
                        retired_by="user:sd", force=True),
        TypeEntry,
    )
    rows = await registry.import_types(
        [
            {
                "name": "commentable",
                "status": "active",
                "aliases": ["searchable"],
                "definition": "a capability",
            }
        ],
        kind="predicate",
    )
    assert rows and "searchable" in (rows[0].aliases or ()), (
        "the alias is legal at t0 -- every extent agrees",
        list(rows[0].warnings) if rows else None,
    )
    # t1 -- the world moves. `commentable` and `taggable` still agree with each other;
    # `searchable` no longer agrees with either. Rule U's fourth operand: STALE is not
    # equal.
    await seed(registry, "ccc_doc", predicates=["commentable", "taggable"])

    refusal = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(refusal, Refusal), refusal
    assert refusal.reason in ("predicate_merge", "different_consumer_sets", "kind_mismatch")
    assert refusal.detail["overridable"] is False

    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "taggable"]
    assert "searchable" not in survivor[0].aliases, (
        "a write the guard did not permit is the tenth trip pointing the other way"
    )
    still = [t for t in (await registry.list_types("predicate")).types if t.name == "commentable"]
    assert still and still[0].status == "active", "and no tombstone either"

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_28_the_retired_names_own_word_is_not_added_as_an_alias(
    adapter, make_registry
):
    """Ruling **R75**, and the boundary of it.

    The retired row's **own name** is deliberately not written onto the successor. The
    successor relation already makes ``resolve_type(<retired name>)`` answer with the
    successor at 1.0 through the chain -- row 6c's design test observed exactly that on
    every leg -- so adding it would be a **second home for one fact** (EDGES.md 2.4's
    rule), and it would be a write no guard on this call examined: the guard's operand
    is ``rec.aliases``, so the write is ``rec.aliases``.

    Stated as an id rather than as a comment because *"we deliberately did not write
    that"* is exactly the kind of decision a later row silently reverses.
    """
    registry = await make_registry(adapter)
    row = await _alias_only_predicate(registry)
    assert row is not None and "zzz_widget_flag" in (row.aliases or ())

    retired = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(retired, TypeEntry), retired

    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "taggable"]
    assert "commentable" not in survivor[0].aliases, (
        "the successor CHAIN answers the retired name; a second home for one fact is "
        "EDGES.md 2.4's rule"
    )
    # ...and the chain does answer it, which is why the alias is unnecessary.
    chained = await registry.resolve_type("commentable", _CTX(), tier="unspecified")
    assert chained.outcome == "existing" and chained.type.name == "taggable"
    assert chained.confidence == 1.0

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_29_a_second_retirement_is_a_no_op_and_writes_no_alias_onto_a_second_successor(
    adapter, make_registry
):
    """**The kill row's TWELFTH trip**, and the guard that was missing is `rec.status`.

    `retire` read `.status` exactly twice and **both times on the successor**. Before
    ruling R75 a repeat retirement merely rewrote the tombstone; R75 attached an alias
    write to it, so a second retirement toward a **different** successor copied the
    retired row's words onto a second live row **while the first still held them**.

    **[Observed, sqlite, Postgres and the async mirror, three ordinary calls]**
    ``retire(alpha, successor=beta)`` then ``retire(alpha, successor=gamma)`` left
    ``beta.aliases == gamma.aliases == ('zeta',)`` — **two ACTIVE rows answering to one
    word**, which is `C16-06`'s whole-store invariant and mechanism **4** itself, on a
    pair `merge_types` refuses `predicate_merge` **non-overridably**, with
    `resolve_type("zeta")` answering one of them at **1.0** and *which one* decided by
    nothing but page order.

    **The diagnosis is a new sentence rather than a repeat.** Trip 9 was the operand
    absent, trip 10 the operand on one branch of two, trip 11 the operand at one call
    site of four; this is **the guard evaluated once for a call that can run twice**.
    *The write a guard permits and the write a call performs must be the same write*
    holds per call and fails across calls, because `rec.aliases` is not consumed by the
    write — the tombstone keeps its words by design (`INTERFACE.md` §5.8) — so the same
    permission is cashed again on every repeat.

    **Fixed the way the sibling call already answers the identical question**, and the
    fix is also the more correct answer to what the old behaviour was answering badly:
    rewriting a standing tombstone's four retirement columns is an **edit** of a
    provenance-bearing row, which §5.8 forbids. **The path to change a successor is
    `retire` the SUCCESSOR, then `reinstate`, then `retire`** -- `reinstate` refuses
    `successor_active` non-overridably while the successor is live, and its own
    `detail["path_back"]` says so *(round 2's fix-auditor lens; the first cut of this
    sentence prescribed a remedy the registry refuses)*.
    """
    registry = await make_registry(adapter)
    for name in ("alpha", "beta", "gamma"):
        await seed(registry, name, kind="predicate", definition="one and the same thing")
    for member in ("aaa_note", "bbb_memo"):
        await seed(registry, member, predicates=["alpha", "beta", "gamma"])
    rows = await registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zeta"],
          "definition": "one and the same thing"}],
        kind="predicate",
    )
    assert rows and "zeta" in (rows[0].aliases or ()), rows

    first = await registry.retire(
        "alpha", "superseded by beta", retired_by="user:sd", successor="beta", force=True
    )
    assert isinstance(first, TypeEntry), first

    second = await registry.retire(
        "alpha", "actually gamma", retired_by="user:sd", successor="gamma", force=True
    )
    assert isinstance(second, TypeEntry), "nothing was prevented, so this is not a refusal"
    assert "retire_no_op:already_retired" in second.warnings, second.warnings

    live = {t.name: tuple(t.aliases) for t in (await registry.list_types("predicate")).types}
    holders = sorted(name for name, aliases in live.items() if "zeta" in aliases)
    assert holders == ["beta"], (
        "C16-06: no two active entries in one namespace hold one word between them",
        live,
    )

    # ...and nothing about the standing tombstone moved, which is §5.8's rule.
    tombstone = [
        t
        for t in (await registry.list_types("predicate", include_retired=True)).types
        if t.name == "alpha"
    ][0]
    assert tombstone.status == "retired"

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_30_the_successors_own_name_is_not_transferred_into_its_own_aliases(
    adapter, make_registry
):
    """Row 6c, round 1, kill-row lens, MINOR — *the second home for one fact by the
    other route.*

    `C9-28` pins that the retired row's **own name** is not added to the successor's
    aliases, because the succession chain already answers it. The same argument binds
    the word on the other side: `_alias_identity_breach` skips the self row when it
    compares, so an alias list containing the **successor's** name passed the guard and
    would have written ``taggable`` into ``taggable.aliases``. A row does not answer to
    its own name as an alias; it answers to it as its name.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    await seed(registry, "bbb_memo", predicates=["commentable", "taggable"])
    # `commentable` is aliased to a word that IS the successor's name -- reachable
    # because `alias_collision` looks at LIVE holders and this alias is written before
    # anything makes the pair a collision at this door.
    rows = await registry.import_types(
        [{"name": "commentable", "status": "active", "aliases": ["zzz_flag"],
          "definition": "a capability"}],
        kind="predicate",
    )
    assert rows and "zzz_flag" in (rows[0].aliases or ())

    out = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(out, TypeEntry), out
    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "taggable"][0]
    assert "taggable" not in survivor.aliases, "a row does not alias its own name"
    assert "zzz_flag" in survivor.aliases, "and the transfer still happened"

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_31_the_alias_transfer_is_its_own_event_and_not_a_retirement(
    adapter, make_registry
):
    """Row 6c, round 1, kill-row lens, MAJOR — *safe by the accident of a missing dict
    key is not safe.*

    The first cut of R75's write appended ``event="retired"`` on the row that is **alive
    and is the survivor**, so `provenance(successor)` read
    ``[('proposed', …), ('approved', …), ('retired', …)]`` and a reader asking *"was
    this ever retired?"* was told **yes** by the log the write added precisely so the
    transfer would not be invisible.

    It did not corrupt `_lifecycle_collisions` — that reader takes
    ``detail["successor"]`` and this detail has none — and that is the point: **one
    event value carrying two facts is `INTERFACE.md` §2.3's Cause B**, and the guard is
    one dict key away from reading it as a succession edge. `"merged"` is not reused
    either: that is the value the same guard reads as *this word was absorbed into that
    one*, which is a different act.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    await registry.import_types(
        [{"name": "commentable", "status": "active", "aliases": ["zzz_widget_flag"],
          "definition": "a capability"}],
        kind="predicate",
    )
    assert isinstance(
        await registry.retire(
            "commentable", "taggable says it better", retired_by="user:sd",
            successor="taggable", force=True,
        ),
        TypeEntry,
    )

    survivor = await registry.provenance("taggable", namespace="default")
    events = [e.event for e in survivor.history]
    assert "retired" not in events, (
        "the survivor is alive; an event saying otherwise is one word for two facts",
        events,
    )
    transfer = [e for e in survivor.history if e.event == "aliases_transferred"]
    assert transfer, events
    assert transfer[0].detail["aliases_added"] == ["zzz_widget_flag"]
    assert transfer[0].detail["from"] == "commentable"

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_32_the_retired_rows_own_name_is_not_transferred_either(
    adapter, make_registry
):
    """Row 6c, round 3, closing round 2's fix-auditor MAJOR — *`C9-30`'s filter was
    one-sided.*

    `C9-28` forbids adding the retired row's **own name** to the successor's aliases:
    the succession chain already answers it at 1.0, so a second copy is a second home
    for one fact. `C9-30` then dropped the **successor's** name and nothing else — so a
    retired row carrying its own name inside its own alias list still transferred it,
    which is `C9-28`'s forbidden write arriving by a third route.

    **[Observed, before the fix]** ``taggable.aliases == ('commentable', 'zeta')``.

    And the skipped words are **stated** rather than silently filtered: a caller who
    hands this call two words and sees one arrive is owed the reason, which is §5.8's
    rule about corrections pointed at a drop instead of at an edit.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    await seed(registry, "bbb_memo", predicates=["commentable", "taggable"])
    rows = await registry.import_types(
        [{"name": "commentable", "status": "active",
          "aliases": ["commentable", "zzz_flag"], "definition": "a capability"}],
        kind="predicate",
    )
    assert rows and set(rows[0].aliases or ()) == {"commentable", "zzz_flag"}

    out = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(out, TypeEntry), out
    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "taggable"][0]
    assert "commentable" not in survivor.aliases, (
        "C9-28: the retired row's own name has a home already -- the succession chain",
        survivor.aliases,
    )
    assert "zzz_flag" in survivor.aliases, "and the transfer still happened"

    transfer = [
        e
        for e in (await registry.provenance("taggable", namespace="default")).history
        if e.event == "aliases_transferred"
    ]
    assert transfer, "the transfer is recorded"
    assert transfer[0].detail["aliases_not_added"] == ["commentable"], (
        "a word this call deliberately did not write is STATED, never silently dropped",
        transfer[0].detail,
    )

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_33_the_alias_transfer_is_announced_at_the_call_that_performs_it(
    adapter, make_registry
):
    """Row 6c, round 3, closing round 1's integrator MINOR — *the write lands on the
    successor and the call returns the tombstone.*

    R75's transfer moves a word from one identity to another, and the caller performing
    it got back an entry carrying the **retired** row's own aliases with no signal that a
    second row had started answering to them. The `aliases_transferred` **event** is on
    the survivor: the right home for the history, the wrong one for the caller, because
    reading it means already knowing to look.

    `aliases_transferred:<successor>` is the thirty-fifth warning value, and it carries
    the successor's **name** because *which row answers now* is the half a caller acts
    on. A warning and never a refusal: nothing was prevented.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    await registry.import_types(
        [{"name": "commentable", "status": "active", "aliases": ["zzz_widget_flag"],
          "definition": "a capability"}],
        kind="predicate",
    )
    out = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(out, TypeEntry), out
    assert "aliases_transferred:taggable" in out.warnings, (
        "the call that moved the word says so, and says where it went",
        out.warnings,
    )

    # ...and a retirement that transferred NOTHING does not claim it did.
    await seed(registry, "quiet_one", kind="predicate", definition="a capability")
    await seed(registry, "quiet_two", kind="predicate", definition="a capability")
    await seed(registry, "ccc_draft", predicates=["quiet_one", "quiet_two"])
    plain = await registry.retire(
        "quiet_one", "folded in", retired_by="user:sd", successor="quiet_two",
        force=True,
    )
    assert isinstance(plain, TypeEntry), plain
    assert not [w for w in plain.warnings if w.startswith("aliases_transferred")], (
        "a warning that never turns off is noise -- row 3d's own lesson",
        plain.warnings,
    )

async def test_c9_34_no_consumer_evidence_says_what_it_could_not_see_about_this_kind(
    adapter, make_registry
):
    """Row 6c, round 3, closing round 1's kill-row MINOR — *the right refusal reached
    by a sentence about the wrong fact.*

    On a backend that cannot index membership an empty ``gates_on`` means *we could not
    look*, and `retire` refuses `no_consumer_evidence` for that reason. The refusal is
    correct. Its `why` said **"this backend cannot compute a predicate's extent"**
    whatever it was retiring — about an ENTITY, which has no extent and never had one.

    `C9-19`'s own class one noun along, in the one field a caller reads to decide what
    to do next.
    """
    registry = await make_registry(AsyncDegradedAdapter(adapter, indexes_membership=False))
    await seed(registry, "note", definition="a note")
    await seed(registry, "memo", definition="a memo")
    out = await registry.retire("note", "folded into memo", retired_by="user:sd")
    assert isinstance(out, Refusal) and out.reason == "no_consumer_evidence", out
    why = out.detail["why"]
    assert "predicate's extent" not in why, ("an entity has no extent", why)
    assert "entity" in why, ("the sentence names the kind it could not see", why)

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c9_35_a_retirement_that_skipped_every_word_still_says_so(
    adapter, make_registry
):
    """Row 6c, round 3's own fix-auditor lens, MINOR — *a defect in this round's own
    fix, one commit old.*

    `C9-32` claims the skipped words are stated rather than silently filtered, and
    `INTERFACE.md` §5.9 says so in the specification. Both were true only when at least
    one word ALSO survived, because the whole write block was gated on `repoint_words`.

    **[Observed]** a tombstone whose aliases are exactly the successor's own name
    transferred nothing, warned nothing and filed nothing — the pure case, where the
    statement is the entire value there is.

    The `aliases_transferred` **warning** stays gated on an actual write: it claims a
    transfer, and a warning fired for a write nobody performed is `retire_no_op`'s
    defect pointed the other way.
    """
    registry = await make_registry(adapter)
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "taggable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "taggable"])
    await seed(registry, "bbb_memo", predicates=["commentable", "taggable"])
    # the retired row's ONLY alias is its OWN name -- every word is skipped by `C9-32`'s
    # filter, so the transfer writes nothing and the statement is all there is.
    rows = await registry.import_types(
        [{"name": "commentable", "status": "active", "aliases": ["commentable"],
          "definition": "a capability"}],
        kind="predicate",
    )
    assert rows and tuple(rows[0].aliases or ()) == ("commentable",), rows[0].aliases

    out = await registry.retire(
        "commentable", "taggable says it better", retired_by="user:sd",
        successor="taggable", force=True,
    )
    assert isinstance(out, TypeEntry), out
    survivor = [t for t in (await registry.list_types("predicate")).types if t.name == "taggable"][0]
    assert survivor.aliases == (), ("C9-28 and C9-32 both hold", survivor.aliases)
    assert not [
        w for w in out.warnings if w.startswith("aliases_transferred")
    ], ("nothing was transferred, so nothing claims one was", out.warnings)

    skipped = [
        e
        for e in (await registry.provenance("taggable", namespace="default")).history
        if e.event == "aliases_transferred"
    ]
    assert skipped, (
        "the pure case is where the statement is the whole value, and it was silent"
    )
    assert skipped[0].detail["aliases_added"] == []
    assert skipped[0].detail["aliases_not_added"] == ["commentable"], skipped[0].detail

async def _tombstone_holding(registry, word="zzz_moved"):
    """A RETIRED predicate that still answers to ``word``, and nothing named ``word``."""
    await seed(registry, "alpha", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["alpha"])
    written = await registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": [word],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or word not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = await registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")
    return gone

@pytest.mark.requires_capability("indexes_membership")
# **Declared, and the declaration is the finding.** On a backend that cannot
# report membership, both extents come back EMPTY and §5.10's refusal #2 fires
# FIRST -- honestly, and for the reason trip 2 minted it: *empty is not equal*.
# The door still refuses; it refuses with the older, more specific reason, so
# this id cannot assert its own value there. `check_capability_matrix.py` caught
# the omission within one run of the fix, which is what R2's matrix is for.
async def test_c9_36_the_r75_transfer_refuses_a_word_a_tombstone_answers_to(
    adapter, make_registry
):
    """**The SIXTEENTH trip at the TRANSFER door.** Row 6d; ruling **R91**.

    Ruling **R75** re-points a retired row's aliases onto its successor. Nothing asked
    whether a **second** tombstone still answers to one of those words — and if one does,
    the transfer leaves it permanently un-reinstatable, which is the governance act
    ruling **R11** created `reinstate` to provide. `word_held_by_tombstone`,
    non-overridable: `force` overrides what could be SEEN, never what would become TRUE.
    """
    registry = await make_registry(adapter)
    first = await _tombstone_holding(registry)
    assert first.name == "alpha"

    # A second row that carries the SAME word, and a successor to move it onto.
    await seed(registry, "gamma", kind="predicate", definition="a capability")
    await seed(registry, "delta", kind="predicate", definition="a capability")
    # Identical NON-EMPTY extents, so §5.10's refusals #1/#2/#3 pass honestly and the
    # door reaches the guard this id is about. They run FIRST by design -- see the
    # ordering note at `INTERFACE.md` §5.12's `word_held_by_tombstone`.
    await seed(registry, "bbb_memo", predicates=["gamma", "delta"])

    # **The alias is seeded BELOW the doors, and finding out why is worth more than the
    # id.** The first cut of this test built it with `import_types`, and the fix's own
    # alias-door guard (`C12-23`) REFUSES that write -- so the test SKIPPED on every leg
    # and asserted nothing while reporting green. *A check that is green for a reason
    # other than the one it claims* is this register's own repeated finding (M1, A9,
    # §6.10e-i), and it arrived inside the fix for the fifteenth and sixteenth trips.
    #
    # The state is nonetheless real and the guard is not dead code: **every store written
    # before this fix shipped can hold it**, which is exactly what a guard for legacy
    # state is for. That the ordinary doors now refuse to build it is asserted at
    # `C12-23`, and this id drives the transfer over a store that already has it.
    live = await adapter.get_type("default", "gamma", kind="predicate")
    assert live is not None
    await adapter.put_type(TypeRecord(**{**live.__dict__, "aliases": ("zzz_moved",)}))

    out = await registry.retire(
        "gamma", "superseded", retired_by="user:sd", successor="delta", force=True
    )
    assert isinstance(out, Refusal), (
        "the transfer would burn the tombstone that still answers to this word", out
    )
    assert out.reason == "word_held_by_tombstone", out.reason
    assert out.detail["overridable"] is False
    assert out.detail["holder"] == "alpha", out.detail
    assert "path_back" in out.detail and out.detail["path_back"], out.detail

    # Nothing was written: the word did not reach the successor, and `gamma` is not
    # retired. A refusal is a refusal, not a warning on a completed act.
    moved_to = await adapter.get_type("default", "delta", kind="predicate")
    assert moved_to is not None and "zzz_moved" not in (moved_to.aliases or ()), (
        "the transfer must not spend a word a tombstone still answers to"
    )
    still_live = await adapter.get_type("default", "gamma", kind="predicate")
    assert still_live is not None and still_live.status == "active", still_live.status
