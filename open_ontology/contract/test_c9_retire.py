"""C9 -- ``retire`` and ``reinstate`` (21). Mechanism 3.

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
def test_c9_09_a_retired_name_can_be_reinstated_and_resolves_again(registry, adapter):
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

    # The retirement names a SUCCESSOR, and the successor is then retired too -- which
    # is what makes the `successor` assertion below mean anything. [Observed, row 3e
    # second adversarial round] this test used a retirement with no successor, so the
    # `successor is None` leg was vacuous: a `reinstate` that kept the field ran the
    # whole suite green, on the one field §5.9b spends a block quote on.
    seed(registry, "capture", definition="the word that replaced it")
    seed(registry, "watch", definition="a thing a user watches")
    retired = registry.retire(
        "watch", "classifier drift, we think", retired_by="user:sd", successor="capture"
    )
    assert isinstance(retired, TypeEntry) and retired.status == "retired"
    registry.retire("capture", "and that one went too", retired_by="user:sd")

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
    stored = adapter.get_type("default", "watch", kind="entity")
    assert stored is not None and stored.status == "active"
    for field in ("retire_reason", "retired_by", "retired_at", "successor"):
        assert getattr(stored, field, None) is None, (
            f"{field} is a statement about a retirement that is no longer in force"
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


@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
def test_c9_12_reinstate_refuses_to_manufacture_two_live_words_for_one_meaning(registry):
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
    seed(registry, "bike_lane", definition="A DOT bike facility.")
    seed(registry, "cycle_track",
         definition="A DOT bike facility. The newer term for the same thing.")
    merged = registry.merge_types(
        "bike_lane", "cycle_track", "one word for one facility", merged_by="user:dot",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    registry.retire("cycle_track", "we changed our minds", retired_by="user:dot")

    back = registry.reinstate("bike_lane", "the merge was a mistake", reinstated_by="user:dot")
    assert isinstance(back, TypeEntry) and back.status == "active", (
        "reinstating the merged-away word is legal: its successor is retired"
    )

    refusal = registry.reinstate(
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

    live = sorted(t.name for t in registry.list_types().types)
    # `equivalent_to` is seeded at store creation (EDGES.md 3.1); "nothing was written"
    # is about the refused reinstatement, not about the store being empty.
    assert live == ["bike_lane", "equivalent_to"], "and nothing was written"

    # The other direction: the same collision reached with the reinstatements swapped.
    # `successor_active` catches the first step there, which is why BOTH guards are
    # needed and neither is redundant.
    other_way = registry.retire("bike_lane", "put it back the way it was",
                                retired_by="user:dot")
    assert isinstance(other_way, TypeEntry)
    revived = registry.reinstate("cycle_track", "take two", reinstated_by="user:dot")
    assert isinstance(revived, TypeEntry) and revived.status == "active"
    blocked = registry.reinstate("bike_lane", "and now this one", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal)
    assert blocked.reason in ("alias_collision", "successor_active")


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c9_13_the_successor_relation_is_checked_through_the_chain_not_one_hop(registry):
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
    seed(registry, "cycle_track", definition="A DOT bike facility, current term.")
    seed(registry, "bike_lane", definition="A DOT bike facility, older term.")
    registry.retire(
        "bike_lane", "superseded by cycle_track", retired_by="user:tlc",
        successor="cycle_track",
    )

    refused = registry.reinstate("bike_lane", "we want it back", reinstated_by="user:tlc")
    assert isinstance(refused, Refusal) and refused.reason == "successor_active"
    assert "cycle_track" in refused.detail["path_back"]

    # Follow the path the refusal names.
    registry.retire("cycle_track", "changed our minds", retired_by="user:dot")
    back = registry.reinstate("bike_lane", "we want it back", reinstated_by="user:tlc")
    assert isinstance(back, TypeEntry) and back.status == "active"

    blocked = registry.reinstate("cycle_track", "and this one", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal), (
        "two live words for one meaning, reached by following the documented path back"
    )
    assert blocked.reason == "alias_collision"
    assert blocked.detail["collides_with"] == "bike_lane"
    assert blocked.detail["relation"] == "predecessor"
    assert sorted(t.name for t in registry.list_types().types) == [
        "bike_lane",
        "equivalent_to",  # seeded at store creation -- EDGES.md 3.1
    ]


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c9_14_the_chain_is_transitive_and_the_scan_is_namespace_scoped(registry):
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
        seed(registry, name, definition=f"the {name} of a DOT segment")
    registry.retire("street_name", "renamed", retired_by="user:dot", successor="on_street")
    registry.retire("on_street", "renamed again", retired_by="user:dot", successor="corridor")

    two_hops = registry.reinstate("street_name", "bring it back", reinstated_by="user:dot")
    assert isinstance(two_hops, Refusal) and two_hops.reason == "alias_collision"
    assert two_hops.detail["collides_with"] == "corridor"
    assert two_hops.detail["relation"] == "successor"

    # ...and the identical word live in ANOTHER namespace is not a collision.
    seed(registry, "corridor", namespace="dpr", definition="a parks corridor")
    seed(registry, "greenway", namespace="dpr", definition="a parks greenway")
    registry.retire("greenway", "renamed", retired_by="user:dpr", namespace="dpr",
                    successor="corridor")
    registry.retire("corridor", "and that too", retired_by="user:dpr", namespace="dpr")
    scoped = registry.reinstate("greenway", "back please", reinstated_by="user:dpr",
                                namespace="dpr")
    assert isinstance(scoped, TypeEntry) and scoped.status == "active", (
        "`default:corridor` is live and irrelevant -- 2.6 keeps namespaces apart"
    )


@pytest.mark.requires_capability("indexes_membership")
def test_c9_15_reinstate_says_when_it_could_not_look_and_when_it_is_not_yet_durable(
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
    from .doubles import DegradedAdapter

    blind = make_registry(DegradedAdapter(adapter, stores_aliases=False))
    seed(blind, "watch", definition="a thing a user watches")
    blind.retire("watch", "drift", retired_by="user:sd")
    if blind.adapter.capabilities().stores_events:
        entry = blind.reinstate("watch", "put it back", reinstated_by="user:sd")
        assert isinstance(entry, TypeEntry)
        assert any(
            w.startswith("reinstate_alias_check_unavailable:") for w in entry.warnings
        ), "we could not look, and an absence we could not check is not an absence"

    paging = make_registry(DegradedAdapter(adapter, page_cap=1))
    seed(paging, "first_word", definition="one")
    seed(paging, "second_word", definition="two")
    paging.retire("second_word", "drift", retired_by="user:sd")
    if paging.adapter.capabilities().stores_events:
        entry = paging.reinstate("second_word", "put it back", reinstated_by="user:sd")
        assert isinstance(entry, TypeEntry)
        assert any(
            w.startswith("reinstate_alias_check_unavailable:") for w in entry.warnings
        ), "the backend said its page was partial; an absence over it is not an absence"

    borrowed = make_registry(DegradedAdapter(adapter, transaction_scope="savepoint"))
    seed(borrowed, "third_word", definition="three")
    borrowed.retire("third_word", "drift", retired_by="user:sd")
    if borrowed.adapter.capabilities().stores_events:
        entry = borrowed.reinstate("third_word", "put it back", reinstated_by="user:sd")
        assert isinstance(entry, TypeEntry)
        assert any(
            w.startswith("not_durable_until_host_commits:") for w in entry.warnings
        ), "a write over a borrowed connection is not durable until the host commits"


@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
def test_c9_16_a_merge_the_guard_can_only_see_in_events_still_blocks(registry, adapter):
    """**The alias column was the guard's only evidence for a merge, and one ordinary
    call erases it.** Row 3e, third adversarial round.

    `merge_types` retires `from_` with `into` as its successor **and** writes the alias
    onto the survivor, and `_lifecycle_collisions` read only `retired` events plus the
    live `aliases` column. `import_types` rewrites a live row -- wiping its aliases --
    so inserting one import into §5.9b's own four-call walk erased the evidence and let
    the walk through: both words active, no refusal, no warning. The graph now reads
    `merged` events too, which is the record neither call can overwrite.
    """
    seed(registry, "bike_lane", definition="A DOT bike facility.")
    seed(registry, "cycle_track",
         definition="A DOT bike facility. The newer term for the same thing.")
    merged = registry.merge_types(
        "bike_lane", "cycle_track", "one word for one facility", merged_by="user:dot",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged

    # An ordinary re-import of the survivor, which rewrites the row and its aliases.
    registry.import_types(
        [{"name": "cycle_track", "status": "active", "definition": "from the dump"}]
    )
    survivor = adapter.get_type("default", "cycle_track", kind="entity")
    assert survivor is not None and not survivor.aliases, (
        "the import wiped the alias -- which is the point: the guard cannot rely on it"
    )

    registry.retire("cycle_track", "we changed our minds", retired_by="user:dot")
    back = registry.reinstate("bike_lane", "the merge was a mistake", reinstated_by="user:dot")
    assert isinstance(back, TypeEntry) and back.status == "active"

    blocked = registry.reinstate("cycle_track", "and this one", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal), "the merge is still on the record, in events"
    assert blocked.reason == "alias_collision"
    assert sorted(t.name for t in registry.list_types().types) == [
        "bike_lane",
        "equivalent_to",  # seeded at store creation -- EDGES.md 3.1
    ]


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c9_17_the_collision_scan_pages_to_exhaustion(adapter, make_registry):
    """**§5.9b says the scan "reads to exhaustion through `next_after`" and nothing
    checked it.** Row 3e, third adversarial round.

    `C9-15`'s paging double returns **no** cursor by design, so it exercises the
    *cannot read the rest* branch and the exhaustion loop is never entered: a mutation
    replacing `cursor = page.next_after` with `cursor = None` ran the whole suite green.
    Against an honest paging backend -- partial **plus** a cursor, which PACKAGE.md
    §3.3 permits and UC3's scale produces -- that mutation silently converts a refusal
    into a warning and lets the collision through.
    """
    from .doubles import DegradedAdapter

    paging = make_registry(DegradedAdapter(adapter, page_cap=2, page_cursor=True))
    for filler in ("aa_filler", "bb_filler"):
        seed(paging, filler, definition=f"a {filler} to push the survivor off page one")
    seed(paging, "bike_lane", definition="A DOT bike facility.")
    seed(paging, "cycle_track",
         definition="A DOT bike facility. The newer term for the same thing.")
    merged = paging.merge_types(
        "bike_lane", "cycle_track", "one word", merged_by="user:dot",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    paging.retire("cycle_track", "changed our minds", retired_by="user:dot")
    assert isinstance(
        paging.reinstate("bike_lane", "undo", reinstated_by="user:dot"), TypeEntry
    )

    blocked = paging.reinstate("cycle_track", "and this", reinstated_by="user:dot")
    assert isinstance(blocked, Refusal), (
        "the survivor is past page one; a scan that stops there misses the collision"
    )
    assert blocked.reason == "alias_collision"


@pytest.mark.requires_capability("indexes_membership", "stores_events")
def test_c9_18_retire_with_a_successor_takes_the_merges_identity_guards(registry):
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
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "searchable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    seed(registry, "doc", predicates=["searchable"])
    seed(registry, "person", definition="a human being")

    # The merge is refused non-overridably -- the precondition of this test.
    merge = registry.merge_types("commentable", "searchable", "duplicate capability",
                                 merged_by="user:sd", acknowledge=["predicate_merge"])
    assert isinstance(merge, Refusal) and merge.reason == "predicate_merge"

    # ... and so is the retirement that would produce the same redirect.
    refusal = registry.retire("commentable", reason="duplicate capability",
                              retired_by="user:sd", successor="searchable")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "predicate_merge"
    assert refusal.detail["overridable"] is False
    assert refusal.detail["successor"] == "searchable"
    assert sorted(refusal.detail["from_extent"]) == ["task"]
    assert sorted(refusal.detail["into_extent"]) == ["doc"]

    # `force=True` overrides the consumer guards and NOT this one.
    forced = registry.retire("commentable", reason="I really mean it",
                             retired_by="user:sd", successor="searchable", force=True)
    assert isinstance(forced, Refusal) and forced.reason == "predicate_merge"

    # A successor of another KIND is refused too: a redirect at confidence 1.0
    # would answer a question about one kind with an entry of another.
    crossed = registry.retire("commentable", reason="close enough",
                              retired_by="user:sd", successor="person")
    assert isinstance(crossed, Refusal) and crossed.reason == "kind_mismatch"
    assert crossed.detail["overridable"] is False

    # The guard is NARROW: a plain retirement, and a retirement whose successor
    # shares a non-empty extent, both still work.
    plain = registry.retire("commentable", reason="nothing uses it",
                            retired_by="user:sd")
    assert isinstance(plain, TypeEntry) and plain.status == "retired"

    seed(registry, "linkable", kind="predicate", definition="a code path will accept it")
    seed(registry, "shareable", kind="predicate", definition="a code path will accept it")
    seed(registry, "note", predicates=["linkable", "shareable"])
    same = registry.retire("linkable", reason="genuinely the same set",
                           retired_by="user:sd", successor="shareable")
    assert isinstance(same, TypeEntry), same


def test_c9_19_a_non_overridable_guard_is_never_reached_through_an_overridable_one(
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
    blind = make_registry(
        DegradedAdapter(
            adapter,
            indexes_membership=False,
            why={
                "indexes_membership": "this store has no type-predicate table, so an "
                "extent cannot be computed"
            },
        ),
        approval_policy="auto",
    )
    seed(blind, "commentable", kind="predicate", definition="a capability")
    seed(blind, "searchable", kind="predicate", definition="a capability")
    seed(blind, "note", predicates=["commentable"])
    seed(blind, "doc", predicates=["searchable"])

    refusal = blind.retire(
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

    forced = blind.retire(
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
    plain = blind.retire("searchable", "nobody uses it", retired_by="user:sd")
    assert isinstance(plain, Refusal), plain
    assert plain.reason == "no_consumer_evidence"
    assert plain.detail["overridable"] is True


def test_c9_20_refusal_one_transfers_to_a_successor_and_force_does_not_move_it(
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
    registry = make_registry(adapter, approval_policy="auto")
    if not registry.caps.indexes_membership:
        pytest.skip(
            "PACKAGE.md 3.2 -- indexes_membership=False makes every extent unknowable, "
            "so `predicate_merge` fires first and this guard is never reached. C9-08 "
            "holds that half"
        )
    seed(registry, "commentable", kind="predicate", definition="a capability")
    seed(registry, "searchable", kind="predicate", definition="a capability")
    seed(registry, "note", predicates=["commentable", "searchable"])
    registry.register_consumer(
        Consumer(id="app.comments", gate="commentable", on_unknown="drop",
                 owner="team-a", locator="app/comments.py")
    )
    registry.register_consumer(
        Consumer(id="app.search", gate="searchable", on_unknown="drop",
                 owner="team-b", locator="app/search.py")
    )

    merged = registry.merge_types(
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
        refused = registry.retire(
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
def test_c9_21_a_consumers_gate_and_a_types_usage_follow_the_identity(
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
    registry = make_registry(adapter, approval_policy="auto")
    if not registry.caps.indexes_membership or not registry.caps.counts_usage:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend cannot compute an extent or does not count "
            "usage, so neither half of this has a fact to be right or wrong about"
        )
    seed(registry, "commentable", kind="predicate", definition="can carry comments")
    seed(registry, "searchable", kind="predicate", definition="can carry comments")
    seed(registry, "note", predicates=["commentable", "searchable"])
    merged = registry.merge_types(
        "commentable", "searchable", "one word for one capability", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged

    registry.register_consumer(
        Consumer(id="app.comments", gate="commentable", on_unknown="drop",
                 owner="team-a", locator="app/comments.py")
    )
    report = registry.consumers("searchable")
    assert [c.id for c in report.gates_on] == ["app.comments"], (
        "the gate names the word the registry says still resolves, at confidence 1.0 -- "
        "so it gates on this type"
    )
    assert not report.would_drop, (
        "and it is NOT a consumer that would silently drop this type, which is the "
        "opposite claim"
    )
    blocked = registry.retire("searchable", "no longer needed", retired_by="user:sd")
    assert isinstance(blocked, Refusal) and blocked.reason == "live_consumers", (
        "§5.9 guards retirement with `consumers`, and it can only guard what that call "
        "can see"
    )

    for _ in range(5):
        registry.record_use("commentable", by="svc.notes")
    survivor = registry.usage("searchable")
    assert survivor.count == 5, (
        "usage is summed over the IDENTITY -- a survivor reading zero about the "
        "most-used word in the vocabulary is §5.7's own named failure"
    )
    assert survivor.orphaned is not True, (
        "and it is not nominated for retirement as an orphan. `orphaned is None` on a "
        "backend that cannot timestamp usage is Rule U and correct; `True` here would "
        "be the confident false negative"
    )
