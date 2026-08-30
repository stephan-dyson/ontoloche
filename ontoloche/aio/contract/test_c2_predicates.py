# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c2_predicates.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C2 -- ``predicates`` (6). Mechanism 4 defensively, and the ROADMAP.md kill row.

Predicates are the structure that stops five locally-correct lists being read as five
duplicates.
"""

from __future__ import annotations
import pytest
from ontoloche.types import Consumer
from ontoloche.aio.contract._support import seed
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter


@pytest.mark.requires_capability("indexes_membership")
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

@pytest.mark.requires_capability("indexes_membership")
async def test_c2_03_of_returns_only_the_predicates_that_type_satisfies(registry):
    await seed(registry, "commentable", kind="predicate", definition="can be commented on")
    await seed(registry, "searchable", kind="predicate", definition="is in the search index")
    await seed(registry, "task", predicates=["commentable", "searchable"])
    await seed(registry, "capture", predicates=["searchable"])

    assert {p.name for p in await registry.predicates(of="task")} == {"commentable", "searchable"}
    assert {p.name for p in await registry.predicates(of="capture")} == {"searchable"}

@pytest.mark.requires_capability("indexes_membership")
async def test_c2_04_include_retired(registry):
    await seed(registry, "commentable", kind="predicate", definition="can be commented on")
    await seed(registry, "shareable", kind="predicate", definition="can be shared")
    await registry.retire("shareable", "nothing gates on it any more", retired_by="user:sd")

    default = await registry.predicates()
    assert {p.name for p in default} == {"commentable"}
    # Rule K (INTERFACE.md 3, 5.2): the default hides a row, so the listing says so.
    # A bare list here would read as "there is one predicate", which is not true.
    assert default.complete is False
    assert default.known == 1
    assert default.why_incomplete and "include_retired" in default.why_incomplete

    everything = await registry.predicates(include_retired=True)
    assert {p.name for p in everything} == {"commentable", "shareable"}
    assert everything.complete is True and everything.why_incomplete is None

@pytest.mark.requires_capability("indexes_membership")
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

@pytest.mark.requires_capability("stores_aliases", "stores_events", "indexes_membership")
async def test_c2_06_the_extent_and_the_of_filter_resolve_the_identity(adapter, make_registry):
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
    registry = await make_registry(adapter, approval_policy="auto")
    for name in ("commentable", "searchable"):
        await seed(registry, name, kind="predicate", definition="a capability")
    await seed(registry, "note", predicates=["commentable", "searchable"])

    merged = await registry.merge_types(
        "commentable", "searchable", "identical non-empty extents", merged_by="user:sd",
        acknowledge=["definitions_diverge", "no_consumer_evidence"],
    )
    assert not isinstance(merged, type(None)) and hasattr(merged, "aliases_added"), merged

    # A type declared AFTER the merge, against the ABSORBED word -- which still
    # resolves, so declaring it is neither an error nor unusual.
    await seed(registry, "memo", predicates=["commentable"])
    await seed(registry, "doc", predicates=["searchable"])

    listing = await registry.predicates(of="memo")
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
    by_note = await registry.predicates(of="note")
    assert [p.name for p in by_note.predicates] == ["searchable"]
    assert set(by_note.predicates[0].extent) == {"note", "memo", "doc"}

    # **Rule U over the CLOSURE, one level above the extent page it already applied to
    # (§5.2.1-3).** Four retired PREDICATE rows and a cap of three: the scan that decides
    # which words this identity spans is truncated with no cursor to the rest, so the
    # identity was NOT resolved -- and a count over an unfinished question is exactly the
    # confident number Rule U forbids. The extent query itself is untouched (three rows,
    # not over the cap), which is what makes this row about the closure rather than about
    # `C10-11`'s page.
    #
    # *(The first cut retired three ENTITIES and the assertion failed: the successor scan
    # is per `(namespace, kind)`, so retiring entities cannot truncate a predicate's
    # closure. A fixture that cannot pose its question is the fifth trip's lesson, and it
    # is cheaper to learn here than in a guard.)*
    for spare in ("alpha", "beta", "gamma"):
        await seed(registry, spare, kind="predicate", definition=f"a {spare} capability")
        await registry.retire(spare, "unused", retired_by="user:sd", force=True)
    capped = await make_registry(AsyncDegradedAdapter(adapter, page_cap=3), approval_policy="auto")
    unresolved = await capped.predicates(of="memo")
    assert unresolved.predicates, "the predicate row itself is still readable"
    assert unresolved.predicates[0].extent_size is None, (
        "the identity could not be resolved to the end, so there is no number to give "
        "-- never a count over an unfinished question"
    )
    assert unresolved.predicates[0].why_extent_incomplete, "and Rule U wants the reason"
