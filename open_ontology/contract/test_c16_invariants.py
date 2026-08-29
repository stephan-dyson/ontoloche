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

from ..adapter import TypeQuery
from ..types import (
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

    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", definition="a unit of work", predicates=["commentable"])
    seed(registry, "note", definition="a unit of work", predicates=["commentable"])
    registry.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )

    auto.propose_type("citation", "one deficiency, one row", [], "ai:classifier", tier="opus")
    registry.import_types([{"name": "flight", "status": "active", "apiName": "Flight"}])

    rejected = registry.propose_type("widget", "a thing", [], "user:pm")
    registry.reject(rejected.id, "user:sd", "use `component`")

    amended = registry.propose_type("survey", "an inspection", [], "user:pm")
    registry.approve(amended.id, "user:sd", definition="an inspection visit to a facility")

    registry.record_use("task")
    clock.advance(timedelta(minutes=1))

    seed(registry, "watch", definition="a thing a user watches")
    registry.retire("watch", "superseded by `capture`", retired_by="user:sd", successor="capture")

    merged = registry.merge_types(
        "note", "task", "the same unit of work", merged_by="user:sd"
    )
    assert isinstance(merged, MergeResult), merged
    return registry


def test_c16_01_every_active_entry_has_an_approver(exercised, adapter):
    page = adapter.find_types(TypeQuery(include_retired=True))
    active = [r for r in page.records if r.status == "active"]
    assert len(active) >= 5
    for rec in active:
        approver = (rec.provenance or {}).get("approved_by")
        assert approver, f"{rec.name} is active with no approver"
        assert approver.strip()


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


def test_c16_03_no_events_bytes_changed_after_they_were_written(exercised, adapter, clock):
    before = list(adapter.read_events("default"))
    assert before

    clock.advance(timedelta(hours=1))
    seed(exercised, "capture", definition="a captured watch")
    exercised.record_use("capture")

    after = list(adapter.read_events("default"))
    assert len(after) > len(before)
    assert after[: len(before)] == before, "append-only: a correction is a new event"


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
