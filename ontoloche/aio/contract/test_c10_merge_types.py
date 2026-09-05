# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c10_merge_types.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C10 -- ``merge_types``, and the doors its operands come through (19). Mechanism 4, constrained to the point of near-uselessness
on purpose.

Merging two types about which nothing is known is the single most destructive thing this
interface can do, so this is the one place where "we do not know" blocks rather than
warns.
"""

from __future__ import annotations
import pytest
from ontoloche.aio.adapter import TypeRecord
from ontoloche.types import Consumer, Evidence, MergeResult, Refusal, ResolveContext, TypeEntry
from ontoloche.aio.contract._support import seed
from ontoloche._resolve import same_word
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter, OrderedAdapter, by_name_order


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

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c10_09_two_empty_extents_are_not_a_byte_identical_extent(registry):
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
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "searchable", kind="predicate", definition="a code path will accept it")

    refusal = await registry.merge_types(
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
        again = await registry.merge_types(
            "commentable", "searchable", "I really mean it",
            merged_by="ai:ingest", acknowledge=ack,
        )
        assert isinstance(again, Refusal) and again.reason == "predicate_merge"

    # And a NON-empty identical extent still merges -- the rule narrows the guard,
    # it does not ban predicate merges outright (5.10's "unless byte-identical").
    await seed(registry, "task", predicates=["commentable", "searchable"])
    merged = await registry.merge_types(
        "commentable", "searchable", "identical, and demonstrably so",
        merged_by="user:sd", acknowledge=["no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged

async def test_c10_10_a_predicate_proposal_never_takes_the_auto_path(adapter, make_registry):
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
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.stores_proposals:
        # PACKAGE.md 7.3 B4: no proposal table means no review step, so there is nowhere
        # to hold a predicate. The entry is written and SAYS SO -- which is what makes
        # "a predicate went live without the review R40 requires" enumerable rather than
        # silent -- and asserting that here is the honest unknown, not a skip.
        entry = await registry.propose_type(
            "commentable", "things a user may comment on", [], "user:sd", kind="predicate"
        )
        assert isinstance(entry, TypeEntry), entry
        assert "predicate_requires_review" in entry.warnings, (
            "the one place R40 cannot be honoured says so on the entry it wrote"
        )
        return

    proposal = await registry.propose_type(
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
    approved = await registry.approve(proposal.id, "user:sd")
    assert isinstance(approved, TypeEntry), approved
    assert approved.status == "active"
    assert approved.provenance.approved_by == "user:sd", (
        "never `auto:<policy>` -- the point of the ruling is that a person signed off"
    )

    # And the rule is about ONE KIND. An entity in the same namespace under the same
    # policy still auto-approves, so a policy that quietly stopped working would fail
    # here rather than pass silently.
    entity = await registry.propose_type(
        "task", "a unit of work", [], "user:sd", kind="entity"
    )
    assert isinstance(entity, TypeEntry), (
        "R40 narrows `propose_type` for predicates and for nothing else"
    )
    assert "predicate_requires_review" not in entity.warnings

@pytest.mark.requires_capability("stores_events")
async def test_c10_11_a_partial_extent_is_not_an_identical_extent(adapter, make_registry):
    """**`ROADMAP.md`'s kill row, FIFTH trip.** Row 4c, first adversarial round.

    Rule U's third operand. Row 3c fixed *unknowable is not equal*; row #6's second
    round fixed *empty is not equal*; nobody had fixed **partial is not equal**.

    `_extent` read **one page** and returned it, and every guard that compares two
    extents -- `merge_types`' refusal #2, `retire(successor=)`'s, and row 4c's own
    `_alias_identity_breach` -- took `set(self._extent(...)[0])` and **threw away the
    third element**, which is the `why` saying the read was partial. So two predicates
    whose FIRST PAGE of members happened to match compared equal, and all three callers
    performed the collapse the same store refuses non-overridably when it is not paging.

    **[Observed]** on `AsyncDegradedAdapter(page_cap=2, page_cursor=True)` -- this
    repository's own honest-paging double, added by row 3e for a reason it states as
    *"PACKAGE.md 3.3 permits it and UC3's scale produces it"* -- with true extents of
    three members and two: `merge_types` returned a `MergeResult` and
    `resolve_type("commentable")` answered `searchable` at confidence 1.0.

    **Two backends, two defences, and one does not stand in for the other:**

    * an honest **PAGE** (a cursor to the rest) is answered by `_extent` looping to
      exhaustion -- there is a rest, so read it;
    * a **TRUNCATED** answer (capped, no cursor) has no rest to read, so the only
      defence is the guards folding `_extent`'s own `why` into `knowable`.

    The read path has published that `why` as `PredicateEntry.why_extent_incomplete`
    the whole time. The guards discarded the one signal it emits.
    """
    for label, kwargs in (
        ("paged", {"page_cap": 2, "page_cursor": True}),
        ("truncated", {"page_cap": 2}),
    ):
        registry = await make_registry(adapter, approval_policy="auto")
        if not registry.caps.indexes_membership:
            pytest.skip(
                "PACKAGE.md 3.2 -- this backend declares indexes_membership=False, so "
                "every extent is already unknowable and `C9-08` holds that half. This "
                "test needs a computable extent as scaffolding, not as its subject"
            )
        await seed(registry, "commentable", kind="predicate", definition="a capability")
        await seed(registry, "searchable", kind="predicate", definition="a capability")
        # The first page of each extent MATCHES; the extents do not.
        for member in ("aaa_doc", "bbb_note"):
            await seed(registry, member, predicates=["commentable", "searchable"])
        await seed(registry, "zzz_draft", predicates=["commentable"])

        blind = await make_registry(AsyncDegradedAdapter(adapter, **kwargs), approval_policy="auto")
        refusal = await blind.merge_types(
            "commentable", "searchable", "they look alike", merged_by="user:sd",
            acknowledge=[
                "definitions_diverge", "no_consumer_evidence", "retired_operand",
                "predicate_merge", "kind_mismatch",
            ],
        )
        assert isinstance(refusal, Refusal), (
            f"[{label}] merge_types collapsed two predicates whose extents differ, "
            f"because only their first page was compared -- the kill row"
        )
        assert refusal.reason == "predicate_merge", refusal
        assert refusal.detail["overridable"] is False

        retired = await blind.retire(
            "commentable", "folded", retired_by="user:sd", successor="searchable"
        )
        assert isinstance(retired, Refusal) and retired.reason == "predicate_merge", (
            f"[{label}] retire(successor=) reaches the identical collapse (C9-18), so it "
            f"reads the identical extents and must reach the identical answer"
        )

        entry = (await blind.import_types(
            [
                {
                    "name": "searchable",
                    "kind": "predicate",
                    "definition": "a capability",
                    "aliases": ["commentable"],
                    "status": "active",
                }
            ],
            namespace="default",
            kind="predicate",
        ))[0]
        assert "import_refused:predicate_merge" in entry.warnings, (
            f"[{label}] and so does the alias door (C12-08)"
        )

    # And the guard is still NARROWED rather than banned on a paging backend: two
    # predicates whose extents genuinely match, read across two pages, still merge.
    ok_registry = await make_registry(adapter, approval_policy="auto")
    await seed(ok_registry, "taggable", kind="predicate", definition="a capability")
    await seed(ok_registry, "labelable", kind="predicate", definition="a capability")
    for member in ("m_one", "m_two", "m_three"):
        await seed(ok_registry, member, predicates=["taggable", "labelable"])
    paging = await make_registry(
        AsyncDegradedAdapter(adapter, page_cap=2, page_cursor=True), approval_policy="auto"
    )
    merged = await paging.merge_types(
        "taggable", "labelable", "genuinely one capability", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), (
        "paging to exhaustion means the extents ARE knowable, so a real duplicate still "
        "merges -- C10-09 narrowed this guard and did not close the operation"
    )

async def test_c10_12_predicate_requires_review_marks_the_unreviewed_and_only_them(
    adapter, make_registry
):
    """Ruling **R40**'s warning, across the whole lifecycle. Row 4c, first round.

    The value's job is to make *"a predicate went live without the review R40
    requires"* **enumerable** -- that is the entire argument `4C-RUN.md`'s Q50 asks the
    supervisor to rule on. A warning that is present on every predicate carries no
    information at all, which is the durability warning's own recorded failure (row 3d:
    *a signal that never turns off is noise*) moved into the vocabulary.

    **[Observed, row 4c round 1]** it rode onto every approved predicate's `TypeEntry`
    and stayed there, so a predicate a human had reviewed and one that went live
    unreviewed read **identically**. And `import_types` -- the door row 4c's own checker
    found unguarded on the other identity axis -- put a live capability predicate in on
    a **fully capable** backend with no proposal, no review and no warning at all.

    Four states, and the middle two are the ones that were wrong:

    | how it got there | reviewed? | carries the warning |
    |---|---|---|
    | `propose_type` on a proposal-storing backend | not yet | **yes**, on the `Proposal` |
    | `approve` by a human | yes | **no** |
    | `propose_type` with `stores_proposals=False` | nobody could be asked | **yes** |
    | `import_types` | already decided elsewhere | **yes** |
    """
    registry = await make_registry(adapter, approval_policy="auto")
    proposed = await registry.propose_type(
        "commentable", "things a user may comment on", [], "user:sd", kind="predicate"
    )
    if registry.caps.stores_proposals:
        assert "predicate_requires_review" in proposed.warnings
        approved = await registry.approve(proposed.id, "user:sd")
        assert isinstance(approved, TypeEntry), approved
        assert "predicate_requires_review" not in approved.warnings, (
            "a human reviewed it -- an entry that keeps saying it needs review cannot be "
            "told apart from one that never got any, which is the whole signal"
        )
    else:
        assert isinstance(proposed, TypeEntry)
        assert "predicate_requires_review" in proposed.warnings, (
            "PACKAGE.md 7.3 B4 -- there is nowhere to hold it for review, and that fact "
            "is what the warning makes enumerable"
        )

    imported = (await registry.import_types(
        [
            {
                "name": "annotatable",
                "kind": "predicate",
                "definition": "things a user may annotate",
                "status": "active",
            }
        ],
        namespace="default",
        kind="predicate",
    ))[0]
    assert imported.status == "active"
    assert "predicate_requires_review" in imported.warnings, (
        "R40's justification is that two of the three kill-row trips began with a "
        "predicate that went live without a human. `propose_type` honoured that on both "
        "branches and the import door did not, on a fully capable backend"
    )

    entity = (await registry.import_types(
        [{"name": "flight", "definition": "a scheduled movement", "status": "active"}],
        namespace="default",
    ))[0]
    assert "predicate_requires_review" not in entity.warnings, (
        "R40 narrows one kind and nothing else"
    )

@pytest.mark.requires_capability("stores_events")
async def test_c10_13_the_sixth_trip_four_doors_into_one_stale_claim(adapter, make_registry):
    """**`ROADMAP.md`'s kill row, SIXTH trip — four doors, one root cause.** Row 4c,
    third adversarial round.

    Trips 1–5 were all *the guard did not look properly*: unknowable compared equal,
    empty compared equal, a caller with no guard, an alias door, a partial read. **This
    one is different in kind: the guard looked correctly, and then the fact changed.**
    Every identity guard in this registry compares extents at **write** time and
    `resolve_type` grants confidence 1.0 at **read** time; four things move in between.
    Rule U's fourth operand — unknowable is not equal, empty is not equal, partial is not
    equal, and **STALE is not equal**.

    **Door 1 needs nothing but two legal merges.** Guard #2 compares `left`'s extent to
    `right`'s and says nothing about `left.aliases`, which `merge_types` re-points at
    `right` in the same write. So: merge A→B while their extents match; let ordinary
    vocabulary growth make B and C match; merge B→C. **A's alias rides across, never
    compared to C, and `resolve_type(A)` answers C at 1.0** — a pair the registry refuses
    non-overridably when asked directly.

    The other three doors are `reinstate` re-activating a row whose dormant aliases
    nothing re-checked, `import_types` skipping both alias guards for a `deprecated` row,
    and an alias written while the word was free with the predicate created afterwards.
    All four are the same sentence: **an identity claim is checked when it is written and
    never again.**
    """
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.indexes_membership or not registry.caps.stores_aliases:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend cannot compute an extent or cannot store "
            "aliases, so the fixture's premise is unreachable. C9-08 and C10-11 hold the "
            "unknowable half"
        )
    for name in ("commentable", "searchable", "taggable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable", "taggable"])

    first = await registry.merge_types(
        "commentable", "searchable", "identical extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(first, Refusal), (
        "this merge is legal and must stay legal -- the guard is narrowed, not banned"
    )
    assert "commentable" in first.aliases_added

    # Ordinary vocabulary growth: a new type declaring two existing predicates.
    await seed(registry, "doc", predicates=["searchable", "taggable"])

    second = await registry.merge_types(
        "searchable", "taggable", "identical extents", merged_by="user:sd",
        acknowledge=[
            "definitions_diverge", "no_consumer_evidence", "predicate_merge",
            "kind_mismatch", "retired_operand",
        ],
    )
    assert isinstance(second, Refusal), (
        "`searchable` and `taggable` DO have identical extents -- but `searchable` "
        "carries `commentable`'s alias, and `commentable` does not. Transferring it "
        "would assert an equivalence the registry refuses non-overridably when asked"
    )
    assert second.detail["overridable"] is False
    assert "commentable" in second.detail.get("transferred_aliases", [])

    resolution = await registry.resolve_type(
        "commentable", ResolveContext(), tier="unspecified"
    )
    assert resolution.type != "taggable", (
        "the collapse the registry refuses when asked directly must not be reachable by "
        "asking twice"
    )

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c10_14_door_1s_store_read_the_q56_default_at_the_alias_door(
    adapter, make_registry
):
    """**`C10-13` closes Door 1's WRITE; this closes the READ the write left behind.**

    Row 4c gave `merge_types` a guard over the aliases it transfers, so Door 1's *second*
    merge is now refused. What it did not do -- deliberately, at the loop's cap, and
    recorded as **Q56** -- is re-verify the claim the *first* merge wrote, which is still
    answered at confidence 1.0 long after the vocabulary moved underneath it.

    **The alias door is where this arrives, and it is a different branch from `C3-14`'s.**
    `get_type` matches `name` and never `aliases`, so a word another entry answers to
    never reaches `resolve_type`'s exact-match branch at all: it is *scored*, and the
    shipped resolver rates an exact alias 1.0 (which is the accident `C3-11` turned into
    a registry guarantee). So the identity claim a merge writes is cashed through the
    scorer, and this is the row that says so.

    Three assertions, and the last two are the ones a careless fix breaks: the warning
    fires when the extents diverge, is **absent** while they still agree, and is absent
    for an alias between two non-predicates, which reads no extent at all.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    if not registry.caps.indexes_membership or not registry.caps.stores_aliases:
        pytest.skip(
            "PACKAGE.md 3.2 -- this backend cannot compute an extent or cannot store "
            "aliases, so Door 1's store is unreachable here. C9-08 and C10-11 hold the "
            "unknowable half of Rule U"
        )
    for name in ("commentable", "searchable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable"])

    merged = await registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), (
        "this merge is legal and must stay legal -- the guard is narrowed, not banned"
    )
    assert "commentable" in merged.aliases_added

    agreeing = await registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert agreeing.outcome == "existing"
    assert agreeing.type is not None and agreeing.type.name == "searchable"
    assert "identity_stale" not in agreeing.type.warnings, (
        "the claim is still true; warning here would make the value noise"
    )

    # Door 1, step 3: ordinary vocabulary growth. No acknowledgement, no override, no
    # governance act -- somebody declared a type against a live predicate.
    await seed(registry, "doc", predicates=["searchable"])

    stale = await registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert stale.outcome == "existing"
    assert stale.type is not None and stale.type.name == "searchable"
    assert stale.confidence == 1.0, (
        "row 4d ships the CHEAP half of Q56: the fact is reported, never suppressed"
    )
    assert "identity_stale" in stale.type.warnings, (
        "`commentable` is {note} and `searchable` is {doc, note} -- the pair "
        "`merge_types` now refuses non-overridably, answered at 1.0 with no signal"
    )

    # **Two non-predicates joined by a merge cost this call nothing**, and the row is
    # here so a later change cannot quietly make every alias hit read two extents.
    for name in ("capture", "archive_link"):
        await seed(registry, name, definition=f"a {name}")
    joined = await registry.merge_types(
        "capture", "archive_link", "same thing", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(joined, Refusal), joined
    await seed(registry, "unrelated", predicates=[])
    plain = await registry.resolve_type("capture", ResolveContext(), tier="opus")
    assert plain.outcome == "existing" and plain.type is not None
    assert "identity_stale" not in plain.type.warnings

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c10_15_the_seventh_trip_one_word_is_not_one_string(adapter, make_registry):
    """**`ROADMAP.md`'s kill row, SEVENTH trip — and it is a third kind.**
    Row 4d, first adversarial round.

    Trips 1–5 were one sentence: *the guard did not look properly.* Trip 6 was: *the
    guard looked correctly, and then the fact changed.* **This one is: the guard and the
    resolver disagree about what THE SAME WORD is.**

    Every alias guard found its collision by an exact byte comparison — `rec.name ==
    alias`, `alias in rec.aliases`, `candidate in entry.aliases`. The shipped
    `DeterministicResolver` scores `identity_key(candidate)` against
    `identity_key(alias)`, lowercasing and collapsing every run of non-`[a-z0-9]` to
    `_`. So `'Commentable'` was a word the guards had never heard of, and the resolver
    rated it **1.0**.

    > Every operand of Rule U so far has been about the **extent** comparison —
    > unknowable, empty, partial, stale. Nothing in this project had written down the
    > identity of the **name**. *One word is not one string.*

    **The non-canonical spelling is the real one.** `import_types` is UC1 Tenshen's own
    Foundry migration path and UC3's Socrata shape, and a real export's field labels
    arrive as `"Status"`, not as `snake_case`.

    Both halves are pinned: the **write** door refuses whatever the spelling, and the
    **read** carries `identity_stale` whatever the spelling. And the negative that a
    careless fix breaks: a genuinely different word still resolves to nothing.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "commentable", kind="predicate", definition="a capability")
    await seed(registry, "searchable", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "searchable"])
    await seed(registry, "bbb_memo", predicates=["searchable"])

    # HALF ONE -- the direct ask. Two live predicates whose extents genuinely differ.
    direct = await registry.merge_types(
        "commentable", "searchable", "the same thing, we think", merged_by="user:sd",
        acknowledge=[
            "definitions_diverge", "no_consumer_evidence", "retired_operand",
            "predicate_merge", "kind_mismatch",
        ],
    )
    assert isinstance(direct, Refusal) and direct.reason == "predicate_merge"
    assert direct.detail["overridable"] is False

    assert isinstance(
        await registry.retire("commentable", "superseded", retired_by="user:sd", force=True),
        TypeEntry,
    )

    # HALF TWO -- the same claim, spelled the way a foreign system spells it.
    for spelling in ("commentable", "Commentable", "COMMENTABLE", "commentable ", "commentable-"):
        entry = (await registry.import_types(
            [{"name": "searchable", "kind": "predicate", "definition": "a capability",
              "aliases": [spelling], "status": "active"}],
            namespace="default", kind="predicate",
        ))[0]
        assert any(w.startswith("import_refused:") for w in entry.warnings), (
            f"{spelling!r} and 'commentable' are one word to the resolver, which rates "
            f"the alias 1.0 -- so a guard that refuses one spelling and writes another "
            f"is two answers to one question"
        )
        assert spelling not in (entry.aliases or ())

    # **The negative.** A genuinely different word is still a different word: the key is
    # many-to-one, not permissive, and a fix that widened it into a fuzzy match would
    # refuse aliases the vocabulary is entitled to.
    ok = (await registry.import_types(
        [{"name": "searchable", "kind": "predicate", "definition": "a capability",
          "aliases": ["commentary"], "status": "active"}],
        namespace="default", kind="predicate",
    ))[0]
    assert not any(w.startswith("import_refused:") for w in ok.warnings), (
        "`commentary` is not `commentable`; the guard compares words, not neighbourhoods"
    )

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c10_16_the_stale_warning_survives_every_spelling(adapter, make_registry):
    """**The seventh trip's READ half.** Row 4d, first adversarial round.

    Row 4d's own staleness gate was `candidate in entry.aliases` — an exact-string test
    on a redirect the resolver reached by **normalising**. So on Door 1's store the
    canonical spelling carried `identity_stale` and **every variant spelling answered at
    1.0 with the warning silently absent** — and the production shape of this call is a
    raw column header, which is precisely the spelling that lost it.

    `min_confidence`, `kind=` and `search_namespaces` are asserted not to be escapes
    either: they were each tried as one, and none of them is.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["commentable", "searchable"])
    merged = await registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, Refusal), merged
    await seed(registry, "zzz_doc", predicates=["searchable"])

    # **§5.3.2-8: a partial left-hand look is REPORTED**, and until round 3 nothing
    # exercised it -- a mutation deleting the warning left all 245 ids green. The
    # left-hand row is found by a paged scan; on a backend that caps an unlimited query
    # the scan cannot finish, and Rule U's third operand says so rather than answering
    # 1.0 with `identity_stale` silently absent.
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=2), approval_policy="auto")
    truncated = await capped.resolve_type("Commentable", ResolveContext(), tier="opus")
    if truncated.type is not None and truncated.confidence == 1.0:
        said = " ".join(truncated.type.warnings)
        assert "identity_stale" in said or "alias_check_incomplete" in said, (
            f"the left-hand scan could not finish, so this 1.0 stands on a look that did "
            f"not say the word names no row: {truncated.type.warnings}"
        )

    for spelling in ("commentable", "Commentable", "COMMENTABLE", "commentable ", "commentable-"):
        for kwargs in ({}, {"kind": "predicate"}, {"min_confidence": 1.0}):
            resolution = await registry.resolve_type(
                spelling, ResolveContext(), tier="opus", **kwargs
            )
            if resolution.type is None or resolution.type.name != "searchable":
                continue
            assert resolution.confidence == 1.0
            assert "identity_stale" in resolution.type.warnings, (
                f"{spelling!r} reached the same 1.0 redirect as 'commentable' and said "
                f"nothing about the two extents no longer agreeing: {kwargs}"
            )

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c10_17_retire_validates_the_aliases_its_successor_inherits(adapter, make_registry):
    """**Door 1 with a different second act — reopened by a fix for something else.**
    Row 4d, round 2, found by `check_merge_guard.py`'s stale axis within a minute.

    `retire(successor=)` writes no alias, which is exactly why the sixth trip's Door 1
    did not reach this call while `resolve_type` followed a single hop: `commentable`
    resolved to a retired `searchable` and fell back to `proposal`. **Round 2 made
    `resolve_type` follow the chain** — correctly, because one store cannot answer
    `proposal` at one door and name a live identity at three others — and the same change
    re-pointed every alias `searchable` carries at `taggable`, uncompared.

    `merge_types` has carried this guard since `C10-13`. The difference between the two
    calls was never the identity claim, only which write made it.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable", "taggable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    for member in ("aaa_note", "bbb_memo", "ccc_card"):
        await seed(registry, member, predicates=["commentable", "searchable", "taggable"])
    first = await registry.merge_types(
        "commentable", "searchable", "identical extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(first, Refusal), first
    await seed(registry, "zzz_doc", predicates=["searchable", "taggable"])

    refusal = await registry.retire(
        "searchable", "folded", retired_by="user:sd", successor="taggable", force=True,
    )
    assert isinstance(refusal, Refusal), (
        "`searchable` and `taggable` agree -- but `searchable` carries `commentable`'s "
        "alias, which the chain now re-points at `taggable`, and those two do not"
    )
    assert refusal.detail["overridable"] is False
    assert "commentable" in refusal.detail.get("transferred_aliases", [])

    after = await registry.resolve_type("commentable", ResolveContext(), tier="opus")
    assert not (
        after.type is not None
        and after.type.name == "taggable"
        and after.confidence == 1.0
    ), "the collapse the registry refuses when asked directly is not reachable by asking twice"

@pytest.mark.requires_capability("indexes_membership", "stores_aliases", "stores_events")
async def test_c10_18_the_fifth_identity_guard_answers_above_the_capability_gate(
    adapter, make_registry
):
    """**The story is what a caller acts on.** Row 4d, round 2.

    Round 1 moved the transferred-alias check above the three OVERRIDABLE guards and left
    it below `cannot_record_override`. So on a `stores_events=False` backend an
    acknowledging caller was told **the audit log is missing** about a collapse that never
    moves — which is verbatim what that gate's own note says it must not do for the four
    guards above it: *a caller trying to acknowledge past the kill row must be told
    `predicate_merge`, non-overridable, not that the audit log is missing.*

    This is the **fifth** non-overridable identity guard and it belongs with the other
    four. `C9-19`'s defect class, one round along, in the fix for `C9-19`'s defect class.

    UC1: Tenshen's 2B is a third backend behind the adapter — a host-owned event log is
    that shape, and the operator would have been told to fix their logging.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable", "taggable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable", "taggable"])
    assert not isinstance(
        await registry.merge_types(
            "commentable", "searchable", "identical", merged_by="user:sd",
            acknowledge=["definitions_diverge", "no_consumer_evidence"],
        ),
        Refusal,
    )
    await seed(registry, "doc", predicates=["searchable", "taggable"])

    blind = await make_registry(
        AsyncDegradedAdapter(adapter, stores_events=False), approval_policy="auto"
    )
    refusal = await blind.merge_types(
        "searchable", "taggable", "the same thing", merged_by="user:sd",
        acknowledge=[
            "definitions_diverge", "no_consumer_evidence", "retired_operand",
            "predicate_merge", "kind_mismatch",
        ],
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "predicate_merge", (
        f"the caller is told what would become TRUE, not that the audit log is missing: "
        f"{refusal.reason}"
    )
    assert refusal.detail["overridable"] is False

@pytest.mark.requires_capability("indexes_membership", "stores_events")
async def test_c10_19_the_eighth_trip_a_retired_name_reused_under_another_spelling(
    adapter, make_registry
):
    """**`ROADMAP.md`'s kill row, EIGHTH trip.** Row 4d, third adversarial round.

    §5.4's rule — *a retired name is not reusable; silently reusing a retired word is
    mechanism 4 with a time delay* — was a **byte** comparison (`get_type`), and round
    2's keyed guard `_alias_holder` scans **active** rows only. So the retired half of
    the name door was never keyed, and four ordinary calls reached a confidence-1.0
    collapse:

    1. `commentable_` goes live as a predicate and a type declares it — extent `{note}`;
    2. `commentable_` is retired — *an ordinary, permitted governance act*;
    3. `commentable` is proposed and approved, and a type declares it — extent `{doc}`.
       **Accepted, no refusal, no warning**;
    4. `resolve_type("commentable_")` → `commentable` at **1.0**, warnings empty, on the
       pair `merge_types` refuses non-overridably under every acknowledgement.

    `NAME_RE` admits `commentable_`, `bike__lane`, `borough_` — every one a variant by
    `identity_key`, and every one a name two agencies normalising their own column
    headers produce. **The registry already knew**: `retire(commentable_,
    successor=commentable)` is refused *"a word cannot be its own successor"*. One
    function said the two words are one word; the door that let both exist compared bytes.

    Pinned with its narrowing: a genuinely different word is still free.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    await seed(registry, "commentable_", kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable_"])
    assert isinstance(
        await registry.retire(
            "commentable_", "the team stopped using it", retired_by="user:sd", force=True
        ),
        TypeEntry,
    )

    reused = await registry.propose_type(
        "commentable", "a capability", [Evidence(kind="data", summary="a sample")],
        "user:sd", kind="predicate",
    )
    assert isinstance(reused, TypeEntry), (
        "`commentable` and the retired `commentable_` are one word; §5.4 hands back the "
        "tombstone rather than creating a second row"
    )
    assert reused.status == "retired"
    assert "name_previously_retired" in reused.warnings

    # The second write door gives the same answer to the same act.
    imported = (await registry.import_types(
        [{"name": "commentable", "kind": "predicate", "definition": "a capability",
          "status": "active"}],
        namespace="default", kind="predicate",
    ))[0]
    assert "name_previously_retired" in imported.warnings

    # ...and nothing was written, so no 1.0 claim is reachable.
    resolution = await registry.resolve_type("commentable_", ResolveContext(), tier="opus")
    assert not (
        resolution.type is not None
        and resolution.type.name != "commentable_"
        and resolution.confidence == 1.0
    ), "the collapse `merge_types` refuses non-overridably is not reachable by spelling"

    # **The narrowing.** A genuinely different word is still a free word.
    other = await registry.propose_type(
        "commentary", "a different capability",
        [Evidence(kind="data", summary="a sample")], "user:sd", kind="predicate",
    )
    assert not isinstance(other, Refusal) and other.name == "commentary"

@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")
async def test_c10_20_a_merge_may_not_write_a_word_another_live_row_already_answers_to(
    adapter, make_registry
):
    """**The kill row's THIRTEENTH trip**, and `merge_types` is the FIFTH write door.

    Trip 7 closed *"`C16-06`'s invariant unasked at four write doors"* — `propose_type`,
    `approve`, `reinstate`, `import_types` (`C4-12`, `C9-23`, `C12-12`).
    **`merge_types` asked nothing**, because `_identity_breach(left, right)` was assumed
    to cover the transfer: it compares the two **operands** and never asks whether the
    words being **moved** are already held somewhere else. Counted rather than
    described — this method contained zero calls to `_alias_clash`, `_alias_holder` and
    `_word_rows`.

    **[Observed, sqlite, both paging doubles and the async mirror — five ordinary calls,
    no alias, no import, no `force`]** `merge_types(alpha -> beta)`, ordinary vocabulary
    growth, then `merge_types(alpha -> gamma)`: `beta.aliases == gamma.aliases ==
    ('alpha',)`, **two ACTIVE rows answering to one word**, and `resolve_type("alpha")`
    answering `gamma` at **1.0** — the confidence `INTERFACE.md` §5.3 calls a guarantee —
    on a pair `merge_types` itself refuses `predicate_merge` **non-overridably under all
    five acknowledgements**.

    **It is the TWELFTH trip's class at the sibling caller.** Trip 12's rule is *the
    write a call performs must be idempotent in the state the guard read*, and `retire`
    was made idempotent **per caller**. A tombstone keeps its words by design (§5.8), so
    `left.name` and `left.aliases` are an **unconsumed permission** that `merge_types`
    will cash for any `right` a caller names, once per call, forever — so the obligation
    belongs to the **row's words**, not to the caller, and this guard asks *who holds
    them now* rather than *have I run before*.

    **Non-overridable, and `retired_operand` may not buy past it**: that value is an
    EVIDENCE acknowledgement about a row's `status`, and this is an IDENTITY outcome —
    `C9-20`'s own distinction, at a door nobody had applied it to.
    """
    registry = await make_registry(adapter)
    for name in ("alpha", "beta", "gamma"):
        await seed(registry, name, kind="predicate", definition="one and the same thing")
    for member in ("aaa_note", "bbb_memo"):
        await seed(registry, member, predicates=["alpha", "beta", "gamma"])
    acknowledge = [
        "definitions_diverge", "no_consumer_evidence", "retired_operand",
        "predicate_merge", "kind_mismatch",
    ]

    first = await registry.merge_types(
        "alpha", "beta", reason="one word for one meaning", merged_by="user:sd",
        acknowledge=acknowledge,
    )
    assert isinstance(first, MergeResult), first

    # Ordinary vocabulary growth: `beta` and `gamma` now genuinely differ.
    await seed(registry, "ccc_draft", predicates=["beta"])

    second = await registry.merge_types(
        "alpha", "gamma", reason="actually gamma", merged_by="user:sd",
        acknowledge=acknowledge,
    )
    assert isinstance(second, Refusal), second
    assert second.reason == "alias_collision", second.reason
    assert second.detail["overridable"] is False, (
        "every acknowledgement was supplied; an identity outcome is not bought with an "
        "evidence acknowledgement"
    )
    assert second.detail["holder"] == "beta"

    live = {
        t.name: tuple(t.aliases) for t in (await registry.list_types("predicate")).types
    }
    holders = sorted(n for n, aliases in live.items() if "alpha" in aliases)
    assert holders == ["beta"], ("C16-06: one word, one live row", live)

    # The narrowing half: an ordinary merge is untouched — refusing everything passes a
    # test that only tests refusals.
    plain = await make_registry(adapter)
    for name in ("p_one", "q_two"):
        await seed(plain, name, kind="predicate", definition="one and the same thing")
    for member in ("n_one", "n_two"):
        await seed(plain, member, predicates=["p_one", "q_two"])
    ok = await plain.merge_types(
        "p_one", "q_two", reason="same meaning", merged_by="user:sd",
        acknowledge=acknowledge,
    )
    assert isinstance(ok, MergeResult), ok
    assert ok.aliases_added == ("p_one",)

@pytest.mark.requires_capability("indexes_membership")
# **Declared, and the declaration is the finding.** On a backend that cannot
# report membership, both extents come back EMPTY and §5.10's refusal #2 fires
# FIRST -- honestly, and for the reason trip 2 minted it: *empty is not equal*.
# The door still refuses; it refuses with the older, more specific reason, so
# this id cannot assert its own value there. `check_capability_matrix.py` caught
# the omission within one run of the fix, which is what R2's matrix is for.
async def test_c10_21_the_word_move_refuses_a_word_a_tombstone_answers_to(
    adapter, make_registry
):
    """**The SIXTEENTH trip at the FIFTH write door.** Row 6d; ruling **R91**.

    `merge_types` writes ``(left.name, *left.aliases)`` onto ``right``. `_alias_clash`
    asks whether an **ACTIVE** row already answers to one of them — by design, since
    `alias_collision` is §5.9b's *two LIVE entries* — and **nothing asked whether a
    TOMBSTONE does**. If one does, the merge leaves it permanently un-reinstatable.

    Both operands are excluded from the scan, and leaving them in was the fix's own
    near-miss: `left` becomes a tombstone in this very write, so a scan that did not skip
    it would make the door refuse **itself** — the TENTH trip's sentence, *a guard
    evaluating a state the call destroys*, pointed at the fix before it shipped.
    """
    registry = await make_registry(adapter)
    await seed(registry, "alpha", kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["alpha"])
    written = await registry.import_types(
        [{"name": "alpha", "status": "active", "aliases": ["zzz_moved"],
          "definition": "a capability"}],
        kind="predicate",
    )
    if not written or "zzz_moved" not in (written[0].aliases or ()):
        pytest.skip("this backend did not keep the alias the fixture is built on")
    gone = await registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
    if isinstance(gone, Refusal):
        pytest.skip(f"this backend cannot retire the holder ({gone.reason})")

    await seed(registry, "gamma", kind="predicate", definition="a capability")
    await seed(registry, "delta", kind="predicate", definition="a capability")
    await seed(registry, "bbb_memo", predicates=["gamma", "delta"])
    # **Seeded BELOW the doors, and the first cut of this test did not do that.** The
    # fix's own alias-door guard (`C12-23`) refuses the `import_types` write this
    # fixture used to build, so the test SKIPPED on every leg and asserted nothing while
    # reporting green -- *a check green for a reason other than the one it claims*,
    # arriving inside the fix for the fifteenth and sixteenth trips. The state is real
    # in any store written before this fix shipped, which is what the guard is for; that
    # the ordinary doors now refuse to build it is asserted at `C12-23`.
    live = await adapter.get_type("default", "gamma", kind="predicate")
    assert live is not None
    await adapter.put_type(TypeRecord(**{**live.__dict__, "aliases": ("zzz_moved",)}))

    out = await registry.merge_types(
        "gamma", "delta", "one and the same", merged_by="user:sd",
        acknowledge=("definitions_diverge", "no_consumer_evidence"),
    )
    assert isinstance(out, Refusal), (
        "the word move would burn the tombstone that still answers to this word", out
    )
    assert out.reason == "word_held_by_tombstone", out.reason
    assert out.detail["overridable"] is False
    assert out.detail["holder"] == "alpha", out.detail

    # Nothing was written: `delta` did not take the word and `gamma` is still live.
    moved_to = await adapter.get_type("default", "delta", kind="predicate")
    assert moved_to is not None and "zzz_moved" not in (moved_to.aliases or ()), (
        "the word move must not spend a word a tombstone still answers to"
    )
    assert ((await adapter.get_type("default", "gamma", kind="predicate"))).status == "active"

@pytest.mark.requires_capability("indexes_membership")
async def test_c10_22_a_truncated_collision_scan_is_reported_not_silent(adapter, make_registry):
    """**The kill row's EIGHTEENTH trip.** Row 6d, round 1; countersigned by **R92**.

    `merge_types` bound `_alias_clash`'s `why` and never read it. The comment above the
    call said *"it warns and proceeds"* and it did **neither**: `alias_check_incomplete`
    appeared **zero** times in the method, so a merge over a scan that finished and a
    merge over one the backend cut short were **byte-identical to the caller** — and the
    short one proceeded to two live holders and a confidence-1.0 answer.

    It is the FIFTH trip's operand — *partial is not equal* — un-applied to a guard the
    THIRTEENTH trip's fix added. `_alias_clash` did not exist when trip 5 closed that
    operand at `_extent`'s three callers, so it inherited the rule's exemption rather
    than the rule: **rule (d) by number, in R84's clause in its purest form.**

    Rule U on the LOOK and never on its result: the merge is **not** refused on a short
    page — that would ban `merge_types` on every paging backend, which is `C10-09`'s
    lesson, `C3-13`'s and `C12-13`'s — it is reported.
    """
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("gamma", "beta"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "aaa_note", predicates=["gamma", "beta"])

    # A backend that caps an unlimited query: PACKAGE.md 3.3 permits it and UC3's scale
    # produces it. The collision scan cannot finish, and that is the whole subject.
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=2), approval_policy="auto")
    words, why = await capped._alias_clash("default", "beta", "predicate", ("gamma",))
    if why is None:
        pytest.skip("this backend answered the scan in full, so there is no `why` to drop")

    out = await capped.merge_types(
        "gamma", "beta", "one and the same", merged_by="user:sd",
        acknowledge=("definitions_diverge", "no_consumer_evidence"),
    )
    if isinstance(out, Refusal):
        pytest.skip(f"this backend refuses the merge for another reason ({out.reason})")
    # **The COLLISION scan specifically**, and asserting only the value was this id's own
    # first defect: this door runs TWO scans that can each fail to finish, and change 1's
    # tombstone scan already emitted `alias_check_incomplete` -- so a test asserting the
    # bare value passed with `clash_why` still dropped, and the mutation SURVIVED. The
    # detail now names the scan, and this asserts the one this id is about.
    assert any(
        w.startswith("alias_check_incomplete:collision scan:")
        for w in (out.warnings or ())
    ), (
        "a merge over a COLLISION scan that could not finish must say so -- Rule U on "
        "the LOOK, and it must say WHICH look",
        out.warnings,
    )
    assert words == () or words, words

async def test_c10_23_the_escape_is_evaluated_over_the_whole_holder_set(adapter, make_registry):
    """**The kill row's SEVENTEENTH trip — ruling R80's Q82, constructed.** Row 6d; R92.

    `merge_types` excuses a holder that is another spelling of `left.name`, because
    `left` is about to become a tombstone whose words move onto `right`. That is correct.
    What was not correct is asking it of **one** holder: `_alias_clash` returned whichever
    row the backend paged first, `PACKAGE.md` §3.3 guarantees **no ordering at all**, and
    a page whose first match was an excused row hid a genuine holder behind it.

    **[Observed]** over all 120 page orders of one five-row store: **60 refused, 60
    swallowed**, the swallowed half leaving two ACTIVE rows answering to one word with
    `resolve_type` at 1.0 — on a pair this same call refuses `predicate_merge`
    **non-overridably**. A non-overridable identity guard whose answer is a function of
    sort order is R58's own class, *a guard never reads a page*.

    `OrderedAdapter` is a **legal** backend: §3.3 guarantees no ordering, so a backend
    free to page its rows in any order is conformant.
    """
    verdicts = set()
    # **A distinct namespace per order**, because the two runs share one adapter and a
    # store left dirty by the first would decide the second. The first cut did not do
    # this and the second order ran against a spent fixture.
    for i, order in enumerate(
        (
            ("aaa_note", "beta", "delta", "gamma_"),
            ("aaa_note", "beta", "gamma_", "delta"),
        )
    ):
        ns = f"order{i}"
        ordered = await make_registry(
            OrderedAdapter(adapter, by_name_order(order)), approval_policy="auto"
        )
        for name in ("gamma", "beta", "delta"):
            await seed(ordered, name, kind="predicate", definition="a capability", namespace=ns)
        await seed(
            ordered, "aaa_note", predicates=["gamma", "beta", "delta"], namespace=ns
        )
        written = await ordered.import_types(
            [{"name": "gamma", "kind": "predicate", "definition": "a capability",
              "aliases": ["zeta"], "status": "active"}],
            namespace=ns, kind="predicate",
        )
        if not written or "zeta" not in (written[0].aliases or ()):
            pytest.skip("this backend did not keep the alias the fixture is built on")
        # **The escape-firer is minted AFTER the alias write and BEFORE the retirement,
        # and both halves of that sentence are fixture defects this test already made
        # once.** Before the write, `gamma_` is a live row answering to `gamma`, so the
        # import is refused `alias_collision` and the fixture never exists. After the
        # retirement, `gamma_` is the tombstone's word by `identity_key` and the mint
        # door hands back the holder (`C4-16`) -- so it is never created and
        # `_alias_clash` returns ONE holder in every order, which reports a reverted
        # guard as sound. **A fixture that cannot build its own subject reports the guard
        # as sound**, and this id is the second place row 6d has had to write that down.
        await seed(ordered, "gamma_", kind="entity", definition="the escape firer", namespace=ns)
        gone = await ordered.retire(
            "gamma", "no longer used", retired_by="user:sd", namespace=ns, force=True
        )
        if isinstance(gone, Refusal):
            pytest.skip(f"this backend cannot retire the holder ({gone.reason})")
        live = await adapter.get_type(ns, "delta", kind="predicate")
        assert live is not None
        await adapter.put_type(TypeRecord(**{**live.__dict__, "aliases": ("zeta",)}))

        out = await ordered.merge_types(
            "gamma", "beta", "one and the same", merged_by="user:sd", namespace=ns,
            acknowledge=("definitions_diverge", "no_consumer_evidence", "retired_operand"),
        )
        verdicts.add(out.reason if isinstance(out, Refusal) else "MERGED")
        holders = [
            t.name
            for t in (await ordered.list_types("predicate", namespace=ns)).types
            if same_word(t.name, "zeta")
            or any(same_word(a, "zeta") for a in (t.aliases or ()))
        ]
        assert len(holders) <= 1, (
            "two ACTIVE rows answering to one word -- C16-06 and mechanism 4", holders
        )

    assert len(verdicts) == 1, (
        "a non-overridable identity guard answered differently depending on which row "
        "the backend paged first", verdicts,
    )
