"""C0-08 -- G1 and G2 raced by two real concurrent writers. PACKAGE.md 3.5.

**Hand-written, not generated, and binding.** This is the async counterpart of
``open_ontology/contract/test_c0_concurrency.py``; both claim contract id **C0-08**.
A thread race has no mechanical async form -- the async equivalent of two threads is
``asyncio.gather`` over two coroutines, which is a different mechanism rather than a
token substitution -- so ``tools/unasync.py`` excludes the sync module and this file is
maintained by hand, the way the driver-level ``close()`` methods are (D-A12).

``PACKAGE.md`` 3.5 says G1 must come from a real constraint, *"not from a read-then-
write check"*, and that G2 is what turns ``already_decided`` from a race into an
idempotent refusal. Until row 3c, every test of both called the primitives
**sequentially on one thread** -- which a check-then-insert implementation passes just
as happily as a real constraint does. This file and its sync twin race them.

SQLite gets the guarantee from ``BEGIN IMMEDIATE`` taking the write lock up front (a
DEFERRED transaction that reads then writes is where a routine approval turns into a
spurious SQLITE_BUSY); Postgres gets it from ``SELECT ... FOR UPDATE`` on the proposal
read. The two mechanisms are different and the observable answer is the same, which is
the claim worth having.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime

import pytest

from open_ontology._clock import FixedClock
from open_ontology.aio.registry import AsyncRegistry
from open_ontology.adapter import TypeQuery, TypeRecord
from open_ontology.errors import AlreadyExists
from open_ontology.types import Refusal, TypeEntry

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


def _type(name: str, namespace: str = "default") -> TypeRecord:
    now = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)
    return TypeRecord(
        namespace=namespace, kind="entity", name=name,
        definition="a Medicare/Medicaid-certified nursing home, identified by its CCN",
        created_by="ai", status="active", predicates=(), aliases=(), attributes={},
        attr_schema_version=None, provenance={}, warnings=(),
        created_at=now, updated_at=now,
    )


async def _run_the_race(first, second):
    # --- G1: two writers, one absent name. Exactly one insert may win. Two winners
    # would mean uniqueness is a read-then-write check rather than a constraint.
    rec = _type("meter", namespace="g1_race")
    g1 = await asyncio.gather(
        first.put_type(rec, expect_absent=True),
        second.put_type(rec, expect_absent=True),
        return_exceptions=True,
    )
    winners = [r for r in g1 if isinstance(r, TypeRecord)]
    losers = [r for r in g1 if isinstance(r, AlreadyExists)]
    other = [r for r in g1 if not isinstance(r, (TypeRecord, AlreadyExists))]
    assert not other, f"a racing put_type failed in an unspecified way: {other}"
    assert len(winners) == 1 and len(losers) == 1, f"exactly one writer may win: {g1}"
    page = await first.find_types(TypeQuery(namespace="g1_race", name_in=("meter",)))
    assert len(page.records) == 1, "and the store holds one row, not two"

    # --- G2: two approvals, one proposal. Exactly one may decide it.
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
    listing = await left.list_types(namespace="default")
    assert [t.name for t in listing.types] == ["facility"]
    approvals = [
        e for e in (await left.provenance("facility")).history if e.event == "approved"
    ]
    assert len(approvals) == 1


async def test_c0_08_g1_and_g2_hold_against_two_real_concurrent_writers(backend, tmp_path):
    """One id, two stacks. The sync twin is ``contract/test_c0_concurrency.py``."""
    if backend == "sqlite":
        first, second = await _sqlite_pair(tmp_path)
    elif backend == "postgres":
        if not POSTGRES_DSN:
            pytest.skip(
                "PENDING -- no local Postgres. Set OO_POSTGRES_DSN to run this leg; "
                "SQLite and Postgres reach the guarantee by different mechanisms and "
                "only one of them is exercised without it."
            )
        pytest.importorskip("psycopg", reason="PENDING -- psycopg is not installed")
        first, second = await _postgres_pair()
    else:
        pytest.skip(
            "PENDING -- this adapter factory does not hand out two handles on one "
            "store, so G1/G2 cannot be raced here."
        )
    try:
        await _run_the_race(first, second)
    finally:
        if backend == "postgres":
            try:
                await first._execute(f'DROP SCHEMA IF EXISTS "{first.schema}" CASCADE')
            except Exception:  # noqa: BLE001 - teardown must not mask the assertion
                pass
        await first.close()
        await second.close()
