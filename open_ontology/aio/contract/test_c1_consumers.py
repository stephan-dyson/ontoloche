# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c1_consumers.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C1 -- ``consumers`` (8). Mechanism C: silent per-consumer drop.

This is the call that would have prevented the only documented Tenshen incident.
"""

from __future__ import annotations
import pytest
from open_ontology.errors import UnknownType
from open_ontology.types import Consumer
from open_ontology.aio.contract._support import seed


@pytest.fixture
async def world(registry):
    """A predicate, two members, one non-member, and four consumers."""
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await seed(registry, "project", predicates=["commentable"])
    await seed(registry, "capture", definition="a watch a user captured, newly emitted")

    await registry.register_consumer(
        Consumer(
            id="comment_service.can_comment",
            gate="commentable",
            on_unknown="drop",
            owner="platform",
            locator="comment_service.py:31",
        )
    )
    await registry.register_consumer(
        Consumer(id="aura_render.referent_link", gate="commentable", on_unknown="drop")
    )
    await registry.register_consumer(
        Consumer(id="search_index.ingest", gate="searchable", on_unknown="error")
    )
    await registry.register_consumer(
        Consumer(id="audit_log.record", gate="auditable", on_unknown="passthrough")
    )
    return registry

async def test_c1_01_complete_is_false_even_when_every_consumer_is_registered(world):
    report = await world.consumers("task")
    assert report.complete is False, (
        "complete=True would promise a safety this registry cannot deliver: "
        "the registry cannot know that every consumer in a system is registered"
    )

async def test_c1_02_why_incomplete_names_registered_not_discovered(world):
    report = await world.consumers("task")
    assert report.why_incomplete.strip()
    assert "registered" in report.why_incomplete
    assert "discovered" in report.why_incomplete

async def test_c1_03_an_unknown_type_raises_rather_than_returning_an_empty_report(world):
    with pytest.raises(UnknownType):
        await world.consumers("nothing_by_this_name")

@pytest.mark.requires_capability("indexes_membership")
async def test_c1_04_gates_on_is_the_consumers_whose_gate_includes_the_type(world):
    report = await world.consumers("task")
    assert {c.id for c in report.gates_on} == {
        "comment_service.can_comment",
        "aura_render.referent_link",
    }
    gated = next(c for c in report.gates_on if c.id == "comment_service.can_comment")
    assert gated.owner == "platform"
    assert gated.locator == "comment_service.py:31"

async def test_c1_05_would_drop_is_gate_excludes_and_on_unknown_is_drop(world):
    report = await world.consumers("capture")
    assert {c.id for c in report.would_drop} == {
        "comment_service.can_comment",
        "aura_render.referent_link",
    }
    assert all(c.on_unknown == "drop" for c in report.would_drop)

async def test_c1_06_would_error_is_separate_and_passthrough_appears_in_neither(world):
    report = await world.consumers("capture")
    assert {c.id for c in report.would_error} == {"search_index.ingest"}
    everyone = {c.id for c in report.gates_on + report.would_drop + report.would_error}
    assert "audit_log.record" not in everyone, (
        "a passthrough consumer neither sees the type nor breaks on it"
    )

async def test_c1_07_known_is_the_sum_of_the_three_lists(world):
    for name in ("task", "project", "capture", "commentable"):
        report = await world.consumers(name)
        assert report.known == len(report.gates_on) + len(report.would_drop) + len(
            report.would_error
        )

async def test_c1_08_the_capture_incident_replay(registry):
    """Finding 0.1: `capture` began being emitted, `aura_render` gated on a list that
    excluded it, on_unknown was effectively drop, and the feature was dead for exactly
    the watch kind that had just started working."""
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    await registry.register_consumer(
        Consumer(
            id="aura_render.referent_link",
            gate="commentable",
            on_unknown="drop",
            locator="aura/render.py:412",
        )
    )

    newly_approved = await seed(registry, "capture", definition="a captured watch")
    assert newly_approved.status == "active"

    report = await registry.consumers("capture")
    assert report.would_drop, "the call whose absence let this ship silently"
    assert [c.id for c in report.would_drop] == ["aura_render.referent_link"]
    assert report.would_drop[0].locator == "aura/render.py:412", (
        "a human has to be able to go and look"
    )
    assert report.complete is False
