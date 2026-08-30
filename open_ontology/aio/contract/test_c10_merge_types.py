# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c10_merge_types.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C10 -- ``merge_types``, and the doors its operands come through (13). Mechanism 4, constrained to the point of near-uselessness
on purpose.

Merging two types about which nothing is known is the single most destructive thing this
interface can do, so this is the one place where "we do not know" blocks rather than
warns.
"""

from __future__ import annotations
import pytest
from open_ontology.types import Consumer, MergeResult, Refusal, ResolveContext, TypeEntry
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
