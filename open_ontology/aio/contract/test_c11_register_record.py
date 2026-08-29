# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/test_c11_register_record.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C11 -- ``register_consumer`` / ``record_use`` (4). Mechanism C.

``usage`` and ``consumers`` cannot answer anything unless something writes to them.
"""

from __future__ import annotations
from datetime import timedelta
import pytest
from open_ontology.errors import NotSupported
from open_ontology.types import Consumer
from open_ontology.aio.contract._support import seed
from open_ontology.aio.contract.doubles import AsyncDegradedAdapter


async def test_c11_01_a_consumer_round_trips_intact(registry):
    stored = await registry.register_consumer(
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

    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await seed(registry, "task", predicates=["commentable"])
    [gated] = (await registry.consumers("task")).gates_on
    assert gated == stored

async def test_c11_02_a_consumer_may_gate_on_a_predicate_that_does_not_exist(registry):
    """A consumer that gates on a word nobody registered is precisely mechanism C, and
    refusing the registration would hide it."""
    await registry.register_consumer(
        Consumer(id="future_service.render", gate="not_yet_a_predicate", on_unknown="drop")
    )
    assert await registry.predicates() == []

    await seed(registry, "capture", definition="a captured watch")
    report = await registry.consumers("capture")
    assert [c.id for c in report.would_drop] == ["future_service.render"]

async def test_c11_03_record_use_advances_last_seen(registry, clock):
    await seed(registry, "blocks", definition="this work item blocks that one")
    await registry.record_use("blocks", by="work_link_service")
    first = await registry.usage("blocks")
    assert first.count == 1
    assert first.first_seen == clock.now() and first.last_seen == clock.now()

    clock.advance(timedelta(days=3))
    await registry.record_use("blocks", by="work_link_service")
    second = await registry.usage("blocks")
    assert second.count == 2
    assert second.last_seen == clock.now()
    assert second.first_seen == first.first_seen

async def test_c11_04_a_read_only_consumer_source_fails_loudly_not_silently(
    adapter, make_registry
):
    """A config-backed consumer source is a legitimate adapter (PACKAGE.md 7.3) and it
    cannot be written to.

    PACKAGE.md 3.4 primitive 10 asks for a ``Refusal`` here. The closed fourteen of
    INTERFACE.md 5.12 (ruling R3) has no value that says this honestly, and
    INTERFACE.md wins where the two documents disagree -- so the registry raises
    ``NotSupported`` instead. What C11-04 is actually about is that this is **never a
    silent no-op**, and a raised exception is the loudest available answer. Recorded as
    deviation D-1 in docs/2A-RUN.md; a founder ruling is wanted.
    """
    read_only = await make_registry(AsyncDegradedAdapter(adapter, read_only_consumers=True))
    with pytest.raises(NotSupported):
        await read_only.register_consumer(
            Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
        )
    assert await read_only.adapter.find_consumers("default") == [], "and nothing was written"
