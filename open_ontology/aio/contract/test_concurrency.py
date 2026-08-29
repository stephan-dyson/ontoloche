"""The race the sync suite cannot run -- not one of the 109.

``PACKAGE.md`` 3.5 guarantee G2 and ``registry.approve``'s own docstring both say the
read and all four writes happen in one transaction, *which is what turns
``already_decided`` from a race into an idempotent refusal*. In the sync package that
sentence is an argument: one process, one thread, no way to have two approvals in
flight at once.

Asynchronously it is a test. Two registries on two connections, one event loop,
``asyncio.gather``. Exactly one call must come back with a ``TypeEntry`` and the other
with ``Refusal("already_decided")`` -- never two entries, never two refusals, and never
a half-written type.

SQLite gets the guarantee from ``BEGIN IMMEDIATE`` taking the write lock up front (a
DEFERRED transaction that reads then writes is where a routine approval turns into a
spurious SQLITE_BUSY); Postgres gets it from ``SELECT ... FOR UPDATE`` on the proposal
read. The two mechanisms are different and the observable answer is the same, which is
the claim worth having.

Outside conformance: it asserts a property of the two reference backends' concurrency
control, and PACKAGE.md 6.2 does not enumerate it.
"""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest

from open_ontology._clock import FixedClock
from open_ontology.aio.registry import AsyncRegistry
from open_ontology.types import Refusal, TypeEntry

pytestmark = pytest.mark.nonbinding

POSTGRES_DSN = os.environ.get("OO_POSTGRES_DSN")


async def _sqlite_pair(tmp_path):
    """Two adapters over one file. ``:memory:`` gives each connection its own database,
    so a shared store has to be a file -- which is also how anyone deploys it."""
    from open_ontology.aio.backends.sqlite import AsyncSQLiteAdapter

    path = str(tmp_path / "race.sqlite")
    first = await AsyncSQLiteAdapter.open(path)
    await first.migrate()
    second = await AsyncSQLiteAdapter.open(path)
    return first, second


async def _postgres_pair():
    from open_ontology.aio.backends.postgres import AsyncPostgresAdapter

    schema = "oo_race_" + uuid.uuid4().hex[:8]
    first = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema)
    await first.migrate()
    second = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema)
    return first, second


async def _run_the_race(first, second):
    clock = FixedClock()
    left = await AsyncRegistry.open(first, clock=clock)
    right = await AsyncRegistry.open(second, clock=clock)

    proposal = await left.propose_type(
        "facility",
        "a Medicare/Medicaid-certified nursing home, identified by its CCN",
        [],
        "ai:proposer",
        tier="opus",
    )
    outcomes = await asyncio.gather(
        left.approve(proposal.id, "user:sd"),
        right.approve(proposal.id, "user:other"),
    )

    entries = [o for o in outcomes if isinstance(o, TypeEntry)]
    refusals = [o for o in outcomes if isinstance(o, Refusal)]
    assert len(entries) == 1, f"expected exactly one approval, got {outcomes}"
    assert len(refusals) == 1, f"expected exactly one refusal, got {outcomes}"
    assert refusals[0].reason == "already_decided"
    assert refusals[0].detail["proposal_id"] == proposal.id

    # And the store holds one type, approved once -- not a half-written second copy.
    listing = await left.list_types()
    assert [t.name for t in listing.types] == ["facility"]
    approvals = [
        e for e in (await left.provenance("facility")).history if e.event == "approved"
    ]
    assert len(approvals) == 1


async def test_two_concurrent_approvals_of_one_proposal_settle_once_sqlite(tmp_path):
    first, second = await _sqlite_pair(tmp_path)
    try:
        await _run_the_race(first, second)
    finally:
        await first.close()
        await second.close()


async def test_two_concurrent_approvals_of_one_proposal_settle_once_postgres():
    if not POSTGRES_DSN:
        pytest.skip(
            "PENDING -- no local Postgres. Set OO_POSTGRES_DSN to run this leg; "
            "SQLite and Postgres reach the guarantee by different mechanisms and only "
            "one of them is exercised without it."
        )
    pytest.importorskip("psycopg", reason="PENDING -- psycopg is not installed")
    first, second = await _postgres_pair()
    try:
        await _run_the_race(first, second)
    finally:
        try:
            await first._execute(f'DROP SCHEMA IF EXISTS "{first.schema}" CASCADE')
        finally:
            await first.close()
            await second.close()
