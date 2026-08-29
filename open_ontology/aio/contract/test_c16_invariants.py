# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c16_invariants.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C16 -- whole-store invariants (4).

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
from open_ontology.aio.adapter import TypeQuery
from open_ontology.types import (
    Consumer,
    ConsumerReport,
    MergeResult,
    TypeEntry,
    TypeListing,
)
from open_ontology.aio.contract._support import seed


@pytest.fixture
async def exercised(adapter, make_registry, clock):
    """One store, driven through every write path the registry has."""
    registry = await make_registry(adapter, min_auto_approve_tier="sonnet")
    auto = await make_registry(adapter, approval_policy="auto", auto_policy_name="classifier")

    # Seeding goes through the ungated registry on a backend that cannot hold a pending
    # proposal: there, an untiered proposal meeting `min_auto_approve_tier` has nowhere
    # to fall back to and is refused outright (INTERFACE.md 5.4's last bullet, deviation
    # D-11). That is correct behaviour and it is not what C16 is testing.
    seeder = registry if (await adapter.capabilities()).stores_proposals else auto

    await seed(seeder, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(seeder, "task", definition="a unit of work", predicates=["commentable"])
    await seed(seeder, "note", definition="a unit of work", predicates=["commentable"])
    await registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    await auto.propose_type("citation", "one deficiency, one row", [], "ai:classifier", tier="opus")
    await registry.import_types([{"name": "flight", "status": "active", "apiName": "Flight"}])

    # The rejection and the approver's amendment need somewhere to hold a proposal.
    # PACKAGE.md 3.2 says stores_proposals=False is still conformant and 7.3 B4 says
    # such a backend's propose_type IS the decision, so these two write paths simply do
    # not exist there -- and the invariants below must still hold over everything else.
    # Row 3c: before this, C16 errored out entirely on such a backend.
    if (await adapter.capabilities()).stores_proposals:
        rejected = await registry.propose_type("widget", "a thing", [], "user:pm")
        await registry.reject(rejected.id, "user:sd", "use `component`")

        amended = await registry.propose_type("survey", "an inspection", [], "user:pm")
        await registry.approve(amended.id, "user:sd", definition="an inspection visit to a facility")
    else:
        await seed(seeder, "survey", definition="an inspection visit to a facility")

    await registry.record_use("task")
    clock.advance(timedelta(minutes=1))

    await seed(seeder, "watch", definition="a thing a user watches")
    await registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    # merge_types' consumer-set guard reads the extent of each consumer's gate, so a
    # backend that cannot index membership has no consumer evidence and refuses --
    # correctly, INTERFACE.md 5.10's "the one place we-do-not-know blocks rather than
    # warns". Acknowledged explicitly there rather than skipped, so the merge still
    # happens and the invariants below still have a merge to inspect.
    # `definitions_diverge` is acknowledged unconditionally since row 3c: no resolver
    # here certifies that two definitions are near-synonymous, and 5.10 makes that
    # "we cannot tell" block rather than warn.
    acknowledge = ["definitions_diverge"]
    if not (await adapter.capabilities()).indexes_membership:
        acknowledge.append("no_consumer_evidence")
    merged = await registry.merge_types(
        "note", "task", "the same unit of work", merged_by="user:sd",
        acknowledge=acknowledge,
    )
    assert isinstance(merged, MergeResult), merged
    registry.seeder = seeder  # the registry later writes must go through -- see above
    return registry

@pytest.mark.requires_capability("stores_events")
async def test_c16_01_every_active_entry_has_an_approver(exercised, adapter):
    page = await adapter.find_types(TypeQuery(include_retired=True))
    active = [r for r in page.records if r.status == "active"]
    assert len(active) >= 5
    for rec in active:
        approver = (rec.provenance or {}).get("approved_by")
        assert approver, f"{rec.name} is active with no approver"
        assert approver.strip()

@pytest.mark.requires_capability("stores_events", "indexes_membership")
async def test_c16_02_no_retired_name_was_reused(exercised, adapter):
    page = await adapter.find_types(TypeQuery(include_retired=True))
    retired = {r.name for r in page.records if r.status == "retired"}
    assert retired == {"note", "watch"}

    for name in sorted(retired):
        answer = await exercised.propose_type(name, "a brand new meaning", [], "user:pm")
        assert isinstance(answer, TypeEntry)
        assert answer.status == "retired"
        assert "name_previously_retired" in answer.warnings

    after = await adapter.find_types(TypeQuery(include_retired=True))
    assert {r.name for r in after.records if r.status == "retired"} == retired
    assert len(after.records) == len(page.records), "and no new entry appeared"

@pytest.mark.requires_capability("stores_events")
async def test_c16_03_no_events_bytes_changed_after_they_were_written(exercised, adapter, clock):
    before = list(await adapter.read_events("default"))
    assert before

    clock.advance(timedelta(hours=1))
    await seed(exercised.seeder, "capture", definition="a captured watch")
    await exercised.record_use("capture")

    after = list(await adapter.read_events("default"))
    assert len(after) > len(before)
    assert after[: len(before)] == before, "append-only: a correction is a new event"

@pytest.mark.requires_capability("stores_events")
async def test_c16_04_every_list_shaped_result_carries_complete_and_known(exercised):
    for shape in (TypeListing, ConsumerReport):
        names = {f.name for f in dataclass_fields(shape)}
        assert {"complete", "known"} <= names, f"{shape.__name__} is missing Rule K's fields"

    listing = await exercised.list_types()
    assert listing.complete is not None and listing.known is not None

    census = await exercised.list_types(include_retired=True, status=None, namespace=None)
    assert census.complete is True and isinstance(census.known, int)

    report = await exercised.consumers("task")
    assert report.complete is False and isinstance(report.known, int)

    predicate_entries = await exercised.predicates()
    assert predicate_entries
    for entry in predicate_entries:
        # A predicate's extent carries the same honesty in its own two fields.
        assert entry.extent_size is not None or entry.why_extent_incomplete
