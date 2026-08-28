"""C1 -- ``consumers`` (8). Mechanism C: silent per-consumer drop.

This is the call that would have prevented the only documented Tenshen incident.
"""

from __future__ import annotations

import pytest

from ..errors import UnknownType
from ..types import Consumer
from ._support import seed


@pytest.fixture
def world(registry):
    """A predicate, two members, one non-member, and four consumers."""
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    seed(registry, "project", predicates=["commentable"])
    seed(registry, "capture", definition="a watch a user captured, newly emitted")

    registry.register_consumer(
        Consumer(
            id="comment_service.can_comment",
            gate="commentable",
            on_unknown="drop",
            owner="platform",
            locator="comment_service.py:31",
        )
    )
    registry.register_consumer(
        Consumer(id="aura_render.referent_link", gate="commentable", on_unknown="drop")
    )
    registry.register_consumer(
        Consumer(id="search_index.ingest", gate="searchable", on_unknown="error")
    )
    registry.register_consumer(
        Consumer(id="audit_log.record", gate="auditable", on_unknown="passthrough")
    )
    return registry


def test_c1_01_complete_is_false_even_when_every_consumer_is_registered(world):
    report = world.consumers("task")
    assert report.complete is False, (
        "complete=True would promise a safety this registry cannot deliver: "
        "the registry cannot know that every consumer in a system is registered"
    )


def test_c1_02_why_incomplete_names_registered_not_discovered(world):
    report = world.consumers("task")
    assert report.why_incomplete.strip()
    assert "registered" in report.why_incomplete
    assert "discovered" in report.why_incomplete


def test_c1_03_an_unknown_type_raises_rather_than_returning_an_empty_report(world):
    with pytest.raises(UnknownType):
        world.consumers("nothing_by_this_name")


def test_c1_04_gates_on_is_the_consumers_whose_gate_includes_the_type(world):
    report = world.consumers("task")
    assert {c.id for c in report.gates_on} == {
        "comment_service.can_comment",
        "aura_render.referent_link",
    }
    gated = next(c for c in report.gates_on if c.id == "comment_service.can_comment")
    assert gated.owner == "platform"
    assert gated.locator == "comment_service.py:31"


def test_c1_05_would_drop_is_gate_excludes_and_on_unknown_is_drop(world):
    report = world.consumers("capture")
    assert {c.id for c in report.would_drop} == {
        "comment_service.can_comment",
        "aura_render.referent_link",
    }
    assert all(c.on_unknown == "drop" for c in report.would_drop)


def test_c1_06_would_error_is_separate_and_passthrough_appears_in_neither(world):
    report = world.consumers("capture")
    assert {c.id for c in report.would_error} == {"search_index.ingest"}
    everyone = {c.id for c in report.gates_on + report.would_drop + report.would_error}
    assert "audit_log.record" not in everyone, (
        "a passthrough consumer neither sees the type nor breaks on it"
    )


def test_c1_07_known_is_the_sum_of_the_three_lists(world):
    for name in ("task", "project", "capture", "commentable"):
        report = world.consumers(name)
        assert report.known == len(report.gates_on) + len(report.would_drop) + len(
            report.would_error
        )


def test_c1_08_the_capture_incident_replay(registry):
    """Finding 0.1: `capture` began being emitted, `aura_render` gated on a list that
    excluded it, on_unknown was effectively drop, and the feature was dead for exactly
    the watch kind that had just started working."""
    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    registry.register_consumer(
        Consumer(
            id="aura_render.referent_link",
            gate="commentable",
            on_unknown="drop",
            locator="aura/render.py:412",
        )
    )

    newly_approved = seed(registry, "capture", definition="a captured watch")
    assert newly_approved.status == "active"

    report = registry.consumers("capture")
    assert report.would_drop, "the call whose absence let this ship silently"
    assert [c.id for c in report.would_drop] == ["aura_render.referent_link"]
    assert report.would_drop[0].locator == "aura/render.py:412", (
        "a human has to be able to go and look"
    )
    assert report.complete is False
