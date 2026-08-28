"""C9 -- ``retire`` (6). Mechanism 3.

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


def test_c9_01_a_live_consumer_refuses_the_retirement(registry):
    _with_live_consumer(registry)
    refusal = registry.retire("task", "we think nobody uses it", retired_by="user:sd")
    assert isinstance(refusal, Refusal)
    assert refusal.reason == "live_consumers"
    assert refusal.detail["gates_on"] == ["comment_service.can_comment"]
    assert registry.list_types(status="active").types


def test_c9_02_force_overrides_and_records_or_is_refused(adapter, make_registry):
    registry = make_registry(adapter)
    _with_live_consumer(registry)

    forced = registry.retire("task", "the service is being deleted", retired_by="user:sd", force=True)
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
