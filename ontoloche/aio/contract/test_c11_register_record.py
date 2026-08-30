# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit ontoloche/contract/test_c11_register_record.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). ontoloche/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""C11 -- ``register_consumer`` / ``record_use`` (5). Mechanism C.

``usage`` and ``consumers`` cannot answer anything unless something writes to them.
"""

from __future__ import annotations
import pytest
from datetime import timedelta
from ontoloche.types import REFUSAL_REASONS, Consumer, Refusal
from ontoloche.aio.contract._support import seed
from ontoloche.aio.contract.doubles import AsyncDegradedAdapter


@pytest.mark.requires_capability("indexes_membership")
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
    assert list(await registry.predicates()) == []

    await seed(registry, "capture", definition="a captured watch")
    report = await registry.consumers("capture")
    assert [c.id for c in report.would_drop] == ["future_service.render"]

@pytest.mark.requires_capability("timestamps_usage", "counts_usage")
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

    PACKAGE.md 3.4 primitive 10 asks for a ``Refusal``, never a silent no-op. Ruling
    **R4** (2026-08-28, row 3c) supplied the reason that says it honestly:
    ``consumer_source_read_only``, the fifteenth value of INTERFACE.md 5.12's closed
    vocabulary, amended into that section in the same change per R3's own rule. Before
    R4 this test asserted a raised ``NotSupported`` and carried deviation D-1; the
    deviation is now resolved.
    """
    read_only = await make_registry(AsyncDegradedAdapter(adapter, read_only_consumers=True))
    refusal = await read_only.register_consumer(
        Consumer(id="comment_service.can_comment", gate="commentable", on_unknown="drop")
    )
    assert isinstance(refusal, Refusal), "a refusal, not an exception and not a no-op"
    assert refusal.reason == "consumer_source_read_only"
    assert refusal.reason in REFUSAL_REASONS, "and the vocabulary stayed closed"
    assert refusal.detail["consumer_id"] == "comment_service.can_comment"
    assert refusal.detail["why"], "the adapter's own sentence, not an invented one"
    assert await read_only.adapter.find_consumers("default") == [], "and nothing was written"

async def test_c11_05_an_unregistered_gate_is_warned_about_not_reported_as_a_live_gate(
    registry,
):
    """**Ruling R8, row 3d.** `C11-02` establishes that a consumer may gate on a word
    nobody registered and that the registration must not be refused -- that IS mechanism
    C. This is the other half: the *report* must not then read as a fact about a live
    gate.

    `would_drop: [future_service.render]` invites exactly one reading -- *this consumer
    gates on `not_yet_a_predicate`, and `capture` is not in its extent.* The truth is
    weaker and worse: **there is no `not_yet_a_predicate`**, so the extent is not
    "excludes `capture`", it is undefined, and every type in the namespace would drop.

    So the report carries `gate_unregistered:<gate>`. Three things are asserted, and
    the third is the one that keeps `C11-02` true:

    1. the warning names the gate;
    2. a gate that IS a registered predicate raises no warning -- including a **retired**
       one, which is a registered entry with a tombstone (`C3-10`), not an absent word;
    3. `would_drop` still lists the consumer. Dropping it would delete mechanism-C
       visibility, which is ruling R8's rejected option 2.
    """
    await registry.register_consumer(
        Consumer(id="future_service.render", gate="not_yet_a_predicate", on_unknown="drop")
    )
    await seed(registry, "capture", definition="a captured watch")

    report = await registry.consumers("capture")
    assert "gate_unregistered:not_yet_a_predicate" in report.warnings, (
        "the report must say the gate is a word nobody registered"
    )
    assert [c.id for c in report.would_drop] == ["future_service.render"], (
        "and must still list the consumer -- C11-02's mechanism-C visibility is intact"
    )

    # A gate that IS registered raises nothing, and a RETIRED one is still registered.
    await seed(registry, "commentable", kind="predicate", definition="a code path will accept it")
    await registry.register_consumer(
        Consumer(id="aura_render.referent_link", gate="commentable", on_unknown="drop")
    )
    after = await registry.consumers("capture")
    assert "gate_unregistered:commentable" not in after.warnings
    assert "gate_unregistered:not_yet_a_predicate" in after.warnings, (
        "one registered gate does not clear the warning about the other"
    )
