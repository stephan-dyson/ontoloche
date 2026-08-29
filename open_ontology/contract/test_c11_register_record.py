"""C11 -- ``register_consumer`` / ``record_use`` (4). Mechanism C.

``usage`` and ``consumers`` cannot answer anything unless something writes to them.
"""

from __future__ import annotations

from datetime import timedelta

from ..types import REFUSAL_REASONS, Consumer, Refusal
from ._support import seed
from .doubles import DegradedAdapter


def test_c11_01_a_consumer_round_trips_intact(registry):
    stored = registry.register_consumer(
        Consumer(
            id="aura_render.referent_link",
            gate="commentable",
            on_unknown="error",
            owner="platform",
            locator="aura/render.py:412",
        )
    )
    assert stored.id == "aura_render.referent_link"
    assert stored.gate == "commentable"
    assert stored.on_unknown == "error"
    assert stored.owner == "platform"
    assert stored.locator == "aura/render.py:412"
    assert stored.registered_at is not None

    seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    seed(registry, "task", predicates=["commentable"])
    [gated] = registry.consumers("task").gates_on
    assert gated == stored


def test_c11_02_a_consumer_may_gate_on_a_predicate_that_does_not_exist(registry):
    """A consumer that gates on a word nobody registered is precisely mechanism C, and
    refusing the registration would hide it."""
    registry.register_consumer(
        Consumer(id="future_service.render", gate="not_yet_a_predicate", on_unknown="drop")
    )
    assert registry.predicates() == []

    seed(registry, "capture", definition="a captured watch")
    report = registry.consumers("capture")
    assert [c.id for c in report.would_drop] == ["future_service.render"]


def test_c11_03_record_use_advances_last_seen(registry, clock):
    seed(registry, "blocks", definition="this work item blocks that one")
    registry.record_use("blocks", by="work_link_service")
    first = registry.usage("blocks")
    assert first.count == 1
    assert first.first_seen == clock.now() and first.last_seen == clock.now()

    clock.advance(timedelta(days=3))
    registry.record_use("blocks", by="work_link_service")
    second = registry.usage("blocks")
    assert second.count == 2
    assert second.last_seen == clock.now()
    assert second.first_seen == first.first_seen


def test_c11_04_a_read_only_consumer_source_fails_loudly_not_silently(
    adapter, make_registry
):
    """A config-backed consumer source is a legitimate adapter (PACKAGE.md 7.3) and it
    cannot be written to.

    PACKAGE.md 3.4 primitive 10 asks for a ``Refusal``, never a silent no-op. Ruling
    **R4** (2026-08-28, row 3c) supplied the reason that says it honestly:
    ``consumer_source_read_only``, the fifteenth value of INTERFACE.md 5.12's closed
    vocabulary, amended into that section in the same change per R3's own rule. Before
    R4 this test asserted a raised ``NotSupported`` and carried deviation D-1; the
    deviation is now resolved.
    """
    read_only = make_registry(DegradedAdapter(adapter, read_only_consumers=True))
    refusal = read_only.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )
    assert isinstance(refusal, Refusal), "a refusal, not an exception and not a no-op"
    assert refusal.reason == "consumer_source_read_only"
    assert refusal.reason in REFUSAL_REASONS, "and the vocabulary stayed closed"
    assert refusal.detail["consumer_id"] == "comment_service.can_comment"
    assert refusal.detail["why"], "the adapter's own sentence, not an invented one"
    assert read_only.adapter.find_consumers("default") == [], "and nothing was written"
