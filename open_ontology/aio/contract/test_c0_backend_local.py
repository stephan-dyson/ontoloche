"""C0-08 and C0-09 -- the two contract tests that build backends directly.

**C0-08 -- G1 and G2 raced by two real concurrent writers. PACKAGE.md 3.5.**

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
from open_ontology.policy import NamespacePolicy
from open_ontology.adapter import TypeQuery, TypeRecord
from open_ontology.errors import AlreadyExists, HostTransactionRequired, SchemaMismatch
from open_ontology.types import Refusal, TypeEntry

from . import _support

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


async def _minimal_pair(tmp_path):
    """Two adapters over one natively-degraded store. Its ``oo_type`` has the same
    composite PRIMARY KEY, so the G1 half of the race is real here."""
    from open_ontology.aio.backends.sqlite_minimal import AsyncMinimalSQLiteAdapter

    path = str(tmp_path / "race_minimal.sqlite")
    AsyncMinimalSQLiteAdapter.create_host_schema(path)
    first = await AsyncMinimalSQLiteAdapter.open(path)
    await first.migrate()
    second = await AsyncMinimalSQLiteAdapter.open(path)
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
    if not (await first.capabilities()).stores_proposals:
        # PACKAGE.md 7.3 B4: propose_type returns a TypeEntry on such a backend, so
        # there is no two-step decision and `already_decided` has no subject. G1 was
        # raced above and held. Skipped with a reason so the R12 coverage report sees it.
        pytest.skip(
            "PACKAGE.md 7.3 B4 -- this backend declares stores_proposals=False, so "
            "propose_type returns a TypeEntry and there is no proposal for two "
            "approvals to race. The G1 half above ran and held on this store."
        )

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
    elif backend == "sqlite_minimal":
        first, second = await _minimal_pair(tmp_path)
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


async def test_c0_09_owns_schema_false_makes_migrate_verify_only(backend, tmp_path):
    """C0-09's async twin. Hand-written for the same reason C0-08's is: the async
    backends are built with ``await Adapter.open(...)`` (D-A1), not by calling the
    class, so this cannot be generated by token substitution.

    PACKAGE.md 9.3: when the schema belongs to the host application -- beacon's
    Alembic, or an enterprise Postgres where the DBA owns DDL -- ``migrate()`` is
    verify-only. It raises ``SchemaMismatch`` naming what is missing and never issues
    DDL against a schema it does not own.
    """
    if backend == "sqlite_minimal":
        # This leg IS the owns_schema=False case. Skipping C0-09 here would have been
        # absurd, and the first version of this test did exactly that; the R12 coverage
        # report said so on its first run. Row 3d.
        from open_ontology.aio.backends.sqlite_minimal import AsyncMinimalSQLiteAdapter

        path = str(tmp_path / "host_owned_minimal.sqlite")
        guest = await AsyncMinimalSQLiteAdapter.open(path)
        caps = await guest.capabilities()
        assert caps.owns_schema is False
        assert caps.why.get("owns_schema", "").strip()

        with pytest.raises(SchemaMismatch) as raised:
            await guest.migrate()
        assert "oo_type" in str(raised.value)
        with pytest.raises(SchemaMismatch):
            await guest.migrate()  # nothing was created behind our back

        AsyncMinimalSQLiteAdapter.create_host_schema(path)
        owner = await AsyncMinimalSQLiteAdapter.open(path)
        version = await guest.migrate()
        assert isinstance(version, int) and version >= 1
        await guest.put_type(_type("facility"), expect_absent=True)
        assert await guest.get_type("default", "facility", kind="entity") is not None
        await guest.close()
        await owner.close()
        return

    if backend == "sqlite":
        from open_ontology.aio.backends.sqlite import AsyncSQLiteAdapter

        path = str(tmp_path / "host_owned.sqlite")
        guest = await AsyncSQLiteAdapter.open(path, owns_schema=False)
        owner = await AsyncSQLiteAdapter.open(path)
    elif backend == "postgres":
        if not POSTGRES_DSN:
            pytest.skip("PENDING -- no local Postgres; set OO_POSTGRES_DSN")
        pytest.importorskip("psycopg", reason="PENDING -- psycopg is not installed")
        from open_ontology.aio.backends.postgres import AsyncPostgresAdapter

        schema = "oo_guest_" + uuid.uuid4().hex[:12]
        owner = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema)
        await owner._execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        guest = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema, owns_schema=False)
    elif _support.EXTERNAL_SCHEMA_HARNESS is not None:
        # C0-09's async twin of the third-party path. See the sync module.
        harness = await _support.EXTERNAL_SCHEMA_HARNESS()
        try:
            guest = await harness.guest()
            caps = await guest.capabilities()
            assert caps.owns_schema is False
            assert caps.why.get("owns_schema", "").strip()
            with pytest.raises(SchemaMismatch) as raised:
                await guest.migrate()
            assert "oo_type" in str(raised.value)
            with pytest.raises(SchemaMismatch):
                await guest.migrate()
            await harness.create_host_schema()
            version = await guest.migrate()
            assert isinstance(version, int) and version >= 1
            await guest.put_type(_type("facility"), expect_absent=True)
            assert await guest.get_type("default", "facility", kind="entity") is not None
        finally:
            await harness.teardown()
        return
    else:
        pytest.skip(
            "PENDING -- this adapter supplied no SchemaHarness, so its owns_schema "
            "declaration cannot be verified here. Pass "
            "run_async_contract_suite(schema_harness_factory=...) to verify it; until "
            "then the run reports it as NOT VERIFIED (PACKAGE.md 6.4)."
        )

    try:
        assert (await guest.capabilities()).owns_schema is False

        with pytest.raises(SchemaMismatch) as raised:
            await guest.migrate()
        assert "oo_type" in str(raised.value), "the refusal names what is missing"
        with pytest.raises(SchemaMismatch):
            await guest.migrate()  # nothing was created behind our back

        await owner.migrate()
        version = await guest.migrate()
        assert isinstance(version, int) and version >= 1

        await guest.put_type(_type("facility"), expect_absent=True)
        assert await guest.get_type("default", "facility", kind="entity") is not None
    finally:
        if backend == "postgres":
            try:
                await owner._execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            except Exception:  # noqa: BLE001 - teardown must not mask the assertion
                pass
        await guest.close()
        await owner.close()


class _Boom(RuntimeError):
    """The host's work must survive this; the adapter's must not."""


async def _borrowed_minimal(tmp_path):
    """The natively-degraded leg over a borrowed connection -- the beacon shape exactly:
    the host owns the schema AND the connection. Skipping it was the least defensible of
    the three skips ``_borrowed_pair`` used to make (row 3d, second adversarial round)."""
    import aiosqlite

    from open_ontology.aio.backends.sqlite_minimal import AsyncMinimalSQLiteAdapter

    path = str(tmp_path / "borrowed_minimal.sqlite")
    AsyncMinimalSQLiteAdapter.create_host_schema(path)
    host = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
    async with host.execute("PRAGMA foreign_keys = ON"):
        pass
    async with host.execute("PRAGMA busy_timeout = 5000"):
        pass
    guest = await AsyncMinimalSQLiteAdapter.open(path, connection=host)
    opened = [host]

    async def outsider(name):
        other = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
        try:
            sql = "SELECT count(*) FROM oo_type WHERE name = ?"
            async with other.execute(sql, (name,)) as cur:
                return (await cur.fetchone())[0]
        finally:
            await other.close()

    async def host_begin():
        async with host.execute("BEGIN IMMEDIATE"):
            pass

    async def host_open():
        return bool(host.in_transaction)

    async def host_commit():
        async with host.execute("COMMIT"):
            pass

    async def teardown():
        for conn in opened:
            try:
                await conn.close()
            except Exception:  # noqa: BLE001 - teardown must not mask an assertion
                pass

    async def idle_adapter():
        idle = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
        opened.append(idle)
        return await AsyncMinimalSQLiteAdapter.open(path, connection=idle)

    return _support.BorrowedHarness(
        guest,
        outsider,
        host_begin,
        host_open,
        host_commit,
        teardown,
        idle_adapter=idle_adapter,
    )


async def _borrowed_sqlite(tmp_path):
    import aiosqlite

    from open_ontology.aio.backends.sqlite import AsyncSQLiteAdapter

    path = str(tmp_path / "borrowed.sqlite")
    owner = await AsyncSQLiteAdapter.open(path)
    await owner.migrate()  # the HOST's schema, created and committed before we borrow
    await owner.close()

    host = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
    async with host.execute("PRAGMA foreign_keys = ON"):
        pass
    async with host.execute("PRAGMA busy_timeout = 5000"):
        pass
    guest = await AsyncSQLiteAdapter.open(path, connection=host, owns_schema=False)
    opened = [host]

    async def outsider(name):
        other = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
        try:
            sql = "SELECT count(*) FROM oo_type WHERE name = ?"
            async with other.execute(sql, (name,)) as cur:
                return (await cur.fetchone())[0]
        finally:
            await other.close()

    async def host_begin():
        async with host.execute("BEGIN IMMEDIATE"):
            pass

    async def host_open():
        return bool(host.in_transaction)

    async def host_commit():
        async with host.execute("COMMIT"):
            pass

    async def teardown():
        for conn in opened:
            try:
                await conn.close()
            except Exception:  # noqa: BLE001 - teardown must not mask an assertion
                pass

    async def idle_adapter():
        # A connection with NO transaction on it -- the state C0-13 is about.
        idle = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
        opened.append(idle)
        return await AsyncSQLiteAdapter.open(path, connection=idle, owns_schema=False)

    return _support.BorrowedHarness(
        guest,
        outsider,
        host_begin,
        host_open,
        host_commit,
        teardown,
        idle_adapter=idle_adapter,
    )


async def _borrowed_postgres():
    import psycopg

    from open_ontology.aio.backends.postgres import AsyncPostgresAdapter

    schema = "oo_borrow_" + uuid.uuid4().hex[:12]
    owner = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema)
    await owner.migrate()  # the HOST's schema, committed before we borrow

    # autocommit stays FALSE: a host that manages its own transaction, which is the
    # shape beacon's AsyncSession has and the shape U1 was wrong for.
    host = await psycopg.AsyncConnection.connect(POSTGRES_DSN)
    async with host.cursor() as cur:
        await cur.execute('SET search_path TO "' + schema + '"')
    guest = await AsyncPostgresAdapter.open(
        connection=host, schema=schema, owns_schema=False
    )

    async def outsider(name):
        other = await psycopg.AsyncConnection.connect(POSTGRES_DSN, autocommit=True)
        try:
            async with other.cursor() as cur:
                await cur.execute('SET search_path TO "' + schema + '"')
                await cur.execute("SELECT count(*) FROM oo_type WHERE name = %s", (name,))
                return (await cur.fetchone())[0]
        finally:
            await other.close()

    async def host_begin():
        # psycopg3 with autocommit=False begins implicitly on the first statement, and
        # the SET search_path above already was one. Assert it, do not assume it.
        assert host.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS

    async def host_open():
        return host.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS

    async def host_commit():
        await host.commit()

    made = [host]

    async def teardown():
        for conn in made:
            try:
                await conn.close()
            except Exception:  # noqa: BLE001 - teardown must not mask an assertion
                pass
        await owner._execute('DROP SCHEMA IF EXISTS "' + schema + '" CASCADE')
        await owner.close()

    async def idle_adapter():
        # autocommit=True leaves the connection IDLE: in no transaction at all.
        idle = await psycopg.AsyncConnection.connect(POSTGRES_DSN, autocommit=True)
        made.append(idle)
        return await AsyncPostgresAdapter.open(connection=idle, owns_schema=False)

    async def aborted_adapter():
        # A transaction the HOST has already broken: in a transaction, and nothing this
        # adapter does inside it can succeed -- SAVEPOINT included.
        broken = await psycopg.AsyncConnection.connect(POSTGRES_DSN)
        made.append(broken)
        async with broken.cursor() as cur:
            try:
                await cur.execute("SELECT no_such_column_at_all")
            except Exception:  # noqa: BLE001 - breaking it IS the setup
                pass
        return await AsyncPostgresAdapter.open(connection=broken, owns_schema=False)

    return _support.BorrowedHarness(
        guest,
        outsider,
        host_begin,
        host_open,
        host_commit,
        teardown,
        idle_adapter=idle_adapter,
        aborted_adapter=aborted_adapter,
    )


async def test_c0_12_a_borrowed_connection_uses_savepoints_and_never_commits(
    backend, tmp_path
):
    """C0-12's async twin, hand-written for the same reason C0-08's and C0-09's are:
    it builds backends directly, with ``await Adapter.open(...)`` (D-A1).

    **U1 / ruling R5 -- and the async leg is the one the defect was found in.**
    ``AsyncPostgresAdapter.open(connection=...)`` accepted a borrowed connection and
    then called ``set_autocommit(True)`` on it, and ``transaction()`` committed at depth
    0: the host shared a connection and did not share a transaction. beacon 21.2 builds
    its ``AsyncSession`` seam against exactly this call.

    Asserted: (1) an exception inside ``transaction()`` leaves the host's transaction
    OPEN with only the savepoint rolled back; (2) a clean exit is not durable until the
    host commits; (3) re-entrant calls join the outermost savepoint (R5 point 3).
    """
    if backend == "sqlite":
        harness = await _borrowed_sqlite(tmp_path)
    elif backend == "sqlite_minimal":
        harness = await _borrowed_minimal(tmp_path)
    elif backend == "postgres":
        if not POSTGRES_DSN:
            pytest.skip("PENDING -- no local Postgres; set OO_POSTGRES_DSN")
        pytest.importorskip("psycopg", reason="PENDING -- psycopg is not installed")
        harness = await _borrowed_postgres()
    elif _support.EXTERNAL_BORROWED is not None:
        harness = await _support.EXTERNAL_BORROWED()
    else:
        pytest.skip(
            "PENDING -- this adapter supplied no BorrowedHarness, so its "
            "transaction_scope declaration cannot be verified here. Pass "
            "run_async_contract_suite(borrowed_factory=...) to verify it; until then "
            "the run reports the declaration as NOT VERIFIED (PACKAGE.md 6.4)."
        )
    guest = harness.adapter
    outsider, host_begin = harness.outsider, harness.host_begin
    host_open, host_commit, teardown = harness.host_open, harness.host_commit, harness.teardown

    try:
        caps = await guest.capabilities()
        assert caps.transaction_scope == "savepoint", "borrowed DECLARES; it is not silent"
        assert caps.transactional is True, (
            "R5 point 2: a savepoint adapter is still transactional -- G2 atomicity "
            "holds inside the host's transaction"
        )
        assert caps.why.get("transaction_scope", "").strip()
        assert caps.missing_why() == ()

        await host_begin()
        assert await guest.migrate() >= 1  # verify-only; the host owns this schema

        # The host's own work, done through the borrowed handle, before anything fails.
        await guest.put_type(_type("host_row"), expect_absent=True)

        # 1. An exception rolls the SAVEPOINT back and leaves the host transaction open.
        with pytest.raises(_Boom):
            async with guest.transaction():
                await guest.put_type(_type("doomed"), expect_absent=True)
                raise _Boom("the adapter's failure is not the host's")
        assert await guest.get_type("default", "doomed", kind="entity") is None
        assert await guest.get_type("default", "host_row", kind="entity") is not None
        assert await host_open(), (
            "the host's outer transaction must still be OPEN -- ending it is the defect "
            "U1 names: sharing a connection is not sharing a transaction"
        )

        # 2. Re-entrant calls join the outermost savepoint (R5 point 3).
        with pytest.raises(_Boom):
            async with guest.transaction():
                await guest.put_type(_type("outer"), expect_absent=True)
                async with guest.transaction():
                    await guest.put_type(_type("inner"), expect_absent=True)
                    raise _Boom("joined, so both go")
        assert await guest.get_type("default", "outer", kind="entity") is None
        assert await guest.get_type("default", "inner", kind="entity") is None
        assert await host_open()

        # ...and the REGISTRY says so on the result, not only in capabilities().
        # Ruling R5 point 2 and PACKAGE.md 3 item 3 both promise a why-style sentence
        # in any result that would otherwise imply durability; nothing implemented it
        # until row 3d's second adversarial round.
        registry = await AsyncRegistry.open(
            guest, clock=FixedClock(), policy=NamespacePolicy(approval_policy="auto")
        )
        surfaced = await registry.propose_type(
            "durability_probe", "a word whose durability belongs to the host", [], "user:sd"
        )
        assert surfaced.status == "active", "the auto path completed -- atomically"
        assert any(w.startswith("not_durable_until_host_commits") for w in surfaced.warnings), (
            "and the result says the host has not committed yet"
        )
        assert (await guest.capabilities()).why["transaction_scope"] in " ".join(
            surfaced.warnings
        ), "and the sentence is the backend's own, verbatim"

        # 3. A clean exit RELEASEs -- and is NOT durable until the host commits.
        async with guest.transaction():
            await guest.put_type(_type("clean"), expect_absent=True)
        assert await guest.get_type("default", "clean", kind="entity") is not None
        assert await host_open(), "RELEASE is not COMMIT"
        assert await outsider("clean") == 0, (
            "the adapter must never commit a connection it does not own: durability at "
            "clean exit is the host's, and until the host commits nobody else sees it"
        )
        assert await outsider("host_row") == 0

        await host_commit()
        assert await outsider("clean") == 1 and await outsider("host_row") == 1
        assert await outsider("doomed") == 0 and await outsider("outer") == 0
    finally:
        await teardown()


async def test_c0_13_a_borrowed_connection_with_no_usable_transaction_is_refused(
    backend, tmp_path
):
    """C0-13's async twin. PACKAGE.md 3 item 3 consequence 1.

    A borrowed connection must already be inside the host's transaction, and there are
    two ways it can fail to be: none at all, and one that has already failed. Both are
    refused with ``HostTransactionRequired`` so the two backends fail the same
    documented way -- Postgres would otherwise raise a raw driver error and SQLite would
    silently start a transaction and commit it on RELEASE.

    Its own id because [Observed, row 3d third round] every harness in the suite called
    ``host_begin()`` first, so an adapter omitting the check passed everything.
    """
    if backend == "sqlite":
        harness = await _borrowed_sqlite(tmp_path)
    elif backend == "sqlite_minimal":
        harness = await _borrowed_minimal(tmp_path)
    elif backend == "postgres":
        if not POSTGRES_DSN:
            pytest.skip("PENDING -- no local Postgres; set OO_POSTGRES_DSN")
        pytest.importorskip("psycopg", reason="PENDING -- psycopg is not installed")
        harness = await _borrowed_postgres()
    elif _support.EXTERNAL_BORROWED is not None:
        harness = await _support.EXTERNAL_BORROWED()
    else:
        pytest.skip(
            "PENDING -- this adapter supplied no BorrowedHarness, so the "
            "host-transaction precondition cannot be driven here."
        )
    if harness.idle_adapter is None and harness.aborted_adapter is None:
        await harness.teardown()
        pytest.skip(
            "PENDING -- this BorrowedHarness supplies neither an idle_adapter nor an "
            "aborted_adapter, so PACKAGE.md 3 item 3 consequence 1 cannot be checked."
        )
    try:
        if harness.idle_adapter is not None:
            idle = await harness.idle_adapter()
            with pytest.raises(HostTransactionRequired) as raised:
                async with idle.transaction():
                    await idle.put_type(_type("never_written"), expect_absent=True)
            assert "transaction" in str(raised.value).lower()
            assert await harness.outsider("never_written") == 0

        if harness.aborted_adapter is not None:
            aborted = await harness.aborted_adapter()
            with pytest.raises(HostTransactionRequired) as raised:
                async with aborted.transaction():
                    await aborted.put_type(_type("never_written_either"), expect_absent=True)
            assert "already failed" in str(raised.value).lower()
            assert await harness.outsider("never_written_either") == 0
    finally:
        await harness.teardown()
