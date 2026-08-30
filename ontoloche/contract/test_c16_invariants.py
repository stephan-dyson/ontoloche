"""C16 -- whole-store invariants (6).

PACKAGE.md 6.2 describes these as running once at suite end over everything the suite
wrote. The suite's adapters are function-scoped so that a failure in one test cannot
make another fail for the wrong reason, so these run instead over a store exercised by
**every write path the suite uses** -- propose, auto-approve, amend, reject, retire,
merge, import, record_use. Recorded as deviation D-9 in docs/runs/2A-RUN.md.
"""

from __future__ import annotations

from dataclasses import fields as dataclass_fields
from datetime import timedelta

import pytest

from ..adapter import TypeQuery
from ..types import (
    CREATED_BY,
    STATUSES,
    Consumer,
    ConsumerReport,
    MergeResult,
    TypeEntry,
    TypeListing,
)
from ._support import seed


@pytest.fixture
def exercised(adapter, make_registry, clock):
    """One store, driven through every write path the registry has."""
    registry = make_registry(adapter, min_auto_approve_tier="sonnet")
    auto = make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")

    # Seeding goes through the ungated registry on a backend that cannot hold a pending
    # proposal: there, an untiered proposal meeting `min_auto_approve_tier` has nowhere
    # to fall back to and is refused outright (INTERFACE.md 5.4's last bullet, deviation
    # D-11). That is correct behaviour and it is not what C16 is testing.
    seeder = registry if adapter.capabilities().stores_proposals else auto

    seed(seeder, "commentable", kind="predicate", definition="a code path will accept it")
    seed(seeder, "task", definition="a unit of work", predicates=["commentable"])
    seed(seeder, "note", definition="a unit of work", predicates=["commentable"])
    registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    auto.propose_type("citation", "one deficiency, one row", [], "ai:classifier", tier="opus")
    registry.import_types([{"name": "flight", "status": "active", "apiName": "Flight"}])

    # The rejection and the approver's amendment need somewhere to hold a proposal.
    # PACKAGE.md 3.2 says stores_proposals=False is still conformant and 7.3 B4 says
    # such a backend's propose_type IS the decision, so these two write paths simply do
    # not exist there -- and the invariants below must still hold over everything else.
    # Row 3c: before this, C16 errored out entirely on such a backend.
    if adapter.capabilities().stores_proposals:
        rejected = registry.propose_type("widget", "a thing", [], "user:pm")
        registry.reject(rejected.id, "user:sd", "use `component`")

        amended = registry.propose_type("survey", "an inspection", [], "user:pm")
        registry.approve(amended.id, "user:sd", definition="an inspection visit to a facility")
    else:
        seed(seeder, "survey", definition="an inspection visit to a facility")

    registry.record_use("task")
    clock.advance(timedelta(minutes=1))

    # `capture` is seeded because `retire` now refuses a successor that names no entry
    # (`successor_unregistered`, row 4d round 1). The subject is the whole-store
    # invariants after a merge; the successor is scaffolding.
    # ...and it is named `recording` rather than `capture` because `C16-03` seeds
    # `capture` itself and asserts that seeding it writes NEW events. A shared fixture is
    # a shared fixture.
    seed(seeder, "recording", definition="the word that replaced it")
    seed(seeder, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `recording`", retired_by="user:sd", successor="recording")

    # merge_types' consumer-set guard reads the extent of each consumer's gate, so a
    # backend that cannot index membership has no consumer evidence and refuses --
    # correctly, INTERFACE.md 5.10's "the one place we-do-not-know blocks rather than
    # warns". Acknowledged explicitly there rather than skipped, so the merge still
    # happens and the invariants below still have a merge to inspect.
    # `definitions_diverge` is acknowledged unconditionally since row 3c: no resolver
    # here certifies that two definitions are near-synonymous, and 5.10 makes that
    # "we cannot tell" block rather than warn.
    acknowledge = ["definitions_diverge"]
    if not adapter.capabilities().indexes_membership:
        acknowledge.append("no_consumer_evidence")
    merged = registry.merge_types(
        "note", "task", "the same unit of work", merged_by="user:sd",
        acknowledge=acknowledge,
    )
    assert isinstance(merged, MergeResult), merged
    registry.seeder = seeder  # the registry later writes must go through -- see above
    return registry


@pytest.mark.requires_capability("stores_events")
def test_c16_01_every_active_entry_has_an_approver(exercised, adapter):
    page = adapter.find_types(TypeQuery(include_retired=True))
    active = [r for r in page.records if r.status == "active"]
    assert len(active) >= 5
    for rec in active:
        approver = (rec.provenance or {}).get("approved_by")
        assert approver, f"{rec.name} is active with no approver"
        assert approver.strip()


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c16_02_no_retired_name_was_reused(exercised, adapter):
    page = adapter.find_types(TypeQuery(include_retired=True))
    retired = {r.name for r in page.records if r.status == "retired"}
    assert retired == {"note", "watch"}

    for name in sorted(retired):
        answer = exercised.propose_type(name, "a brand new meaning", [], "user:pm")
        assert isinstance(answer, TypeEntry)
        assert answer.status == "retired"
        assert "name_previously_retired" in answer.warnings

    after = adapter.find_types(TypeQuery(include_retired=True))
    assert {r.name for r in after.records if r.status == "retired"} == retired
    assert len(after.records) == len(page.records), "and no new entry appeared"


@pytest.mark.requires_capability("stores_events")
def test_c16_03_no_events_bytes_changed_after_they_were_written(exercised, adapter, clock):
    before = list(adapter.read_events("default"))
    assert before

    clock.advance(timedelta(hours=1))
    seed(exercised.seeder, "capture", definition="a captured watch")
    exercised.record_use("capture")

    after = list(adapter.read_events("default"))
    assert len(after) > len(before)
    assert after[: len(before)] == before, "append-only: a correction is a new event"


@pytest.mark.requires_capability("stores_events")
def test_c16_04_every_list_shaped_result_carries_complete_and_known(exercised):
    for shape in (TypeListing, ConsumerReport):
        names = {f.name for f in dataclass_fields(shape)}
        assert {"complete", "known"} <= names, f"{shape.__name__} is missing Rule K's fields"

    listing = exercised.list_types()
    assert listing.complete is not None and listing.known is not None

    census = exercised.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True and isinstance(census.known, int)

    report = exercised.consumers("task")
    assert report.complete is False and isinstance(report.known, int)

    predicate_entries = exercised.predicates()
    assert predicate_entries
    for entry in predicate_entries:
        # A predicate's extent carries the same honesty in its own two fields.
        assert entry.extent_size is not None or entry.why_extent_incomplete


@pytest.mark.requires_capability("stores_events", "indexes_membership")
def test_c16_05_every_created_by_is_in_the_closed_vocabulary(exercised, adapter):
    """**INTERFACE.md §2.1 prints `created_by` as a four-value vocabulary and nothing
    enforced it.** Row 3e, second adversarial round.

    `Refusal.reason`, `Evidence.kind`, `Consumer.on_unknown` and `NotAType.reason` all
    raise on an unknown value in `__post_init__`; `created_by` did not, and no
    invariant checked it -- so a third-party backend's garbage flowed straight out to a
    caller through `list_types`. Pre-existing, and ruling **R17** is what made this
    vocabulary extensible, which is when an unenforced closed list starts to matter.
    `kind` is deliberately **not** checked here: §2.2 says it is an OPEN vocabulary.
    """
    page = adapter.find_types(TypeQuery(include_retired=True))
    assert page.records
    for rec in page.records:
        assert rec.created_by in CREATED_BY, (
            f"{rec.name} has created_by={rec.created_by!r}, which INTERFACE.md 2.1 "
            f"does not define"
        )
        assert rec.status in STATUSES, f"{rec.name} has status={rec.status!r}"


@pytest.mark.requires_capability("stores_events", "indexes_membership", "stores_aliases")
def test_c16_06_no_two_active_entries_in_one_namespace_hold_one_word(exercised, adapter):
    """**The mechanical form of the thing three separate calls each refuse.**

    `merge_types`, `propose_type` and `reinstate` all refuse to leave two ACTIVE entries
    with one word between them -- and row 3e's adversarial loop found three different
    walks into that state anyway, each one closed by a guard added to whichever call the
    reviewer happened to come in through. This is the whole-store invariant those guards
    are approximating, asserted directly: it would have caught all three without anybody
    walking four calls to find them. Mechanism **4**, checked rather than argued.
    """
    page = adapter.find_types(TypeQuery(include_retired=True))
    active = [r for r in page.records if r.status == "active"]
    spoken_for: dict[tuple[str, str], str] = {}
    for rec in active:
        for word in (rec.name, *(rec.aliases or ())):
            key = (rec.namespace, word)
            owner = spoken_for.get(key)
            assert owner is None or owner == rec.name, (
                f"{rec.namespace}:{word!r} is answered by BOTH {owner!r} and "
                f"{rec.name!r}, both active -- mechanism 4"
            )
            spoken_for[key] = rec.name
