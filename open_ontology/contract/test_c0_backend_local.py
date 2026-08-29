"""C0-08 and C0-09 -- the two contract tests that build backends directly.

Both construct adapter objects rather than taking the ``adapter`` fixture, so neither
survives mechanical async translation: the async backends are built with
``await AsyncSQLiteAdapter.open(path)`` (3B-ASYNC.md D-A1), not by calling the class.

**C0-08 -- G1 and G2 raced by two real concurrent writers. PACKAGE.md 3.5.**

A thread race has no mechanical async form either: the async equivalent of two threads
is ``asyncio.gather`` over two coroutines, which is a different mechanism, not a token
substitution.

**C0-09 -- ``owns_schema=False`` makes ``migrate()`` verify-only. PACKAGE.md 9.3.**

So this file is excluded from ``tools/unasync.py``'s ``CONTRACT_TESTS`` and its async
counterpart -- ``open_ontology/aio/contract/test_c0_backend_local.py`` -- is
**hand-written**, the way the driver-level ``close()`` methods are (3B-ASYNC.md D-A12).
Both claim the same contract ids and both are binding.
"""

from __future__ import annotations

import os
import threading
import uuid
from datetime import UTC, datetime

import pytest

from .._clock import FixedClock
from ..adapter import TypeQuery, TypeRecord
from ..errors import AlreadyExists, SchemaMismatch
from ..registry import Registry
from ..types import Refusal, TypeEntry
from . import _support

NOW = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


def _type(name="facility", **kw) -> TypeRecord:
    base = dict(
        namespace="default",
        kind="entity",
        name=name,
        definition="a Medicare/Medicaid-certified nursing home, identified by its CCN",
        created_by="ai",
        status="active",
        predicates=(),
        aliases=(),
        attributes={},
        attr_schema_version=None,
        provenance={},
        warnings=(),
        created_at=NOW,
        updated_at=NOW,
    )
    base.update(kw)
    return TypeRecord(**base)

def _shared_store_pair(backend, tmp_path):
    """Two adapter instances over ONE store, so two writers can actually race.

    ``:memory:`` gives every SQLite connection its own database, so a shared store has
    to be a file -- which is also how anyone deploys it. Postgres gets two adapters on
    one schema.
    """
    if backend == "sqlite":
        from ..backends.sqlite import SQLiteAdapter

        path = str(tmp_path / "race.sqlite")
        first = SQLiteAdapter(path)
        first.migrate()
        return first, SQLiteAdapter(path)

    if backend == "postgres":
        dsn = os.environ.get("OO_POSTGRES_DSN")
        if not dsn:
            pytest.skip("PENDING -- no local Postgres; set OO_POSTGRES_DSN")
        from ..backends.postgres import PostgresAdapter

        schema = "oo_race_" + uuid.uuid4().hex[:12]
        first = PostgresAdapter(dsn, schema=schema)
        first.migrate()
        return first, PostgresAdapter(dsn, schema=schema)

    if backend == "sqlite_minimal":
        # The natively-degraded leg races the SAME G1 constraint -- its oo_type has the
        # same composite PRIMARY KEY -- so the G1 half is real here and the G2 half runs
        # over a registry with no proposal store. Both are worth having: nothing about
        # this store makes concurrent writers less likely.
        from ..backends.sqlite_minimal import MinimalSQLiteAdapter

        path = str(tmp_path / "race_minimal.sqlite")
        MinimalSQLiteAdapter.create_host_schema(path)
        first = MinimalSQLiteAdapter(path)
        first.migrate()
        return first, MinimalSQLiteAdapter(path)

    # A third-party backend under `python -m open_ontology.contract --adapter ...`.
    # Two calls to the factory may or may not reach the same store; if they do not,
    # the race is unobservable here and the test says so rather than passing hollowly.
    factory = _support.EXTERNAL_FACTORY
    if factory is None:  # pragma: no cover - defensive
        pytest.skip(
            f"PENDING -- no adapter factory for leg {backend!r}, so two handles on one "
            "store cannot be obtained and G1/G2 cannot be raced here."
        )
    first, second = factory(), factory()
    first.migrate()
    second.migrate()
    probe = _type(name="race_probe")
    first.put_type(probe)
    if second.get_type("default", "race_probe", kind="entity") is None:
        pytest.skip(
            "PENDING -- this adapter factory does not hand out two handles on one "
            "store, so G1/G2 cannot be raced here. Point the runner at a factory "
            "that shares a store to claim conformance on C0-08."
        )
    return first, second


def _race(fn_a, fn_b):
    """Run two callables on two threads, released together. Returns (a, b) where each
    is the return value or the exception raised."""
    out: dict[str, object] = {}
    start = threading.Barrier(2)

    def run(key, fn):
        start.wait(timeout=10)
        try:
            out[key] = fn()
        except BaseException as exc:  # noqa: BLE001 - the exception IS the result
            out[key] = exc

    threads = [
        threading.Thread(target=run, args=("a", fn_a)),
        threading.Thread(target=run, args=("b", fn_b)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
        assert not t.is_alive(), "a racing writer hung -- that is a lock bug, not a pass"
    return out["a"], out["b"]


def test_c0_08_g1_and_g2_hold_against_two_real_concurrent_writers(backend, tmp_path):
    """**G1 and G2, raced.** PACKAGE.md 3.5: G1 must come from a real constraint, "not
    from a read-then-write check", and G2 is what turns ``already_decided`` into an
    idempotent refusal rather than a double-approve.

    C0-02 and C0-07 call the primitives sequentially on one thread, which a
    check-then-insert implementation passes just as happily as a real constraint does.
    So until this test existed, **a backend whose "uniqueness" was a Python-level
    check could be blessed conformant and then corrupt itself the moment two ingestion
    workers hit one store** -- which is the deployment shape UC3 (dozens of agencies
    publishing independently) is the fixture for. Added by row 3c after an adversarial
    review round; see docs/findings/3C-VALIDATION.md.

    The two backends reach the guarantee by different mechanisms -- SQLite by
    ``BEGIN IMMEDIATE`` taking the write lock up front, Postgres by ``SELECT ... FOR
    UPDATE`` on the proposal read -- and the observable answer must be the same, which
    is the claim worth having.
    """
    first, second = _shared_store_pair(backend, tmp_path)

    # --- G1: two writers, one absent name. Exactly one insert may win.
    rec = _type(name="facility")
    a, b = _race(
        lambda: first.put_type(rec, expect_absent=True),
        lambda: second.put_type(rec, expect_absent=True),
    )
    winners = [r for r in (a, b) if isinstance(r, TypeRecord)]
    losers = [r for r in (a, b) if isinstance(r, AlreadyExists)]
    other = [r for r in (a, b) if not isinstance(r, (TypeRecord, AlreadyExists))]
    assert not other, f"a racing put_type failed in an unspecified way: {other}"
    assert len(winners) == 1 and len(losers) == 1, (
        "exactly one writer may create the name. Two winners means G1 is a "
        "read-then-write check, not a constraint"
    )
    page = first.find_types(TypeQuery(namespace="default", name_in=("facility",)))
    assert len(page.records) == 1, "and the store holds one row, not two"

    # --- G2: two approvals, one proposal. Exactly one may decide it.
    if not first.capabilities().stores_proposals:
        # There is no proposal to race for: PACKAGE.md 7.3 B4 says `propose_type` on
        # such a backend returns a TypeEntry, so there is no two-step decision and
        # `already_decided` has no subject. G1 was raced above and held. Skipped with a
        # reason rather than returned from, so the coverage report (R12) can see it.
        pytest.skip(
            "PACKAGE.md 7.3 B4 -- this backend declares stores_proposals=False, so "
            "propose_type returns a TypeEntry and there is no proposal for two "
            "approvals to race. The G1 half above ran and held on this store."
        )

    left = Registry(first, clock=FixedClock())
    right = Registry(second, clock=FixedClock())
    proposal = left.propose_type(
        "survey", "an inspection visit", [], "user:sd", namespace="raced"
    )
    a, b = _race(
        lambda: left.approve(proposal.id, "user:one"),
        lambda: right.approve(proposal.id, "user:two"),
    )
    entries = [r for r in (a, b) if isinstance(r, TypeEntry)]
    refusals = [r for r in (a, b) if isinstance(r, Refusal)]
    assert not [r for r in (a, b) if isinstance(r, BaseException)], (
        f"a racing approve raised instead of refusing: {[r for r in (a, b) if isinstance(r, BaseException)]}"
    )
    assert len(entries) == 1, "never two entries -- that is a double-approve"
    assert len(refusals) == 1 and refusals[0].reason == "already_decided", (
        "the loser is an idempotent refusal, not an exception and not a second approval"
    )
    stored = first.get_type("raced", "survey", kind="entity")
    assert stored is not None and stored.status == "active"


def test_c0_09_owns_schema_false_makes_migrate_verify_only(backend, tmp_path):
    """**B1, tested.** PACKAGE.md 9.3: when the schema belongs to the host application
    -- beacon's Alembic, or an enterprise Postgres where the DBA owns DDL and the
    application role has no CREATE right -- ``migrate()`` is **verify-only**. It checks
    the columns it needs and raises ``SchemaMismatch`` naming what is missing, and it
    **never issues DDL against a schema it does not own.**

    Both reference backends implement this and nothing asserted it. It is one of the
    two capabilities PACKAGE.md 7 (the Tenshen design test) most depends on -- B1 is
    the first contortion in that section -- so the suite was silent about exactly the
    path its own flagship worked example takes. Added by row 3c after an adversarial
    review round; see docs/findings/3C-VALIDATION.md.
    """
    if backend == "sqlite_minimal":
        # This leg IS the owns_schema=False case, so it is the one leg where skipping
        # C0-09 would have been absurd -- and the first version of this test skipped it,
        # with the reason "owns_schema is a property of the reference backends". Caught
        # by the coverage report (ruling R12) on its first run. Row 3d.
        from ..backends.sqlite_minimal import MinimalSQLiteAdapter

        path = str(tmp_path / "host_owned_minimal.sqlite")
        guest = MinimalSQLiteAdapter(path)

        assert guest.capabilities().owns_schema is False
        assert guest.capabilities().why.get("owns_schema", "").strip()
        with pytest.raises(SchemaMismatch) as raised:
            guest.migrate()
        assert "oo_type" in str(raised.value)
        with pytest.raises(SchemaMismatch):
            guest.migrate()  # nothing was created behind our back

        MinimalSQLiteAdapter.create_host_schema(path)
        version = MinimalSQLiteAdapter(path).migrate()
        assert isinstance(version, int) and version >= 1
        guest.put_type(_type(name="facility"), expect_absent=True)
        assert guest.get_type("default", "facility", kind="entity") is not None
        return

    if backend == "sqlite":
        from ..backends.sqlite import SQLiteAdapter

        path = str(tmp_path / "host_owned.sqlite")
        guest = SQLiteAdapter(path, owns_schema=False)
    elif backend == "postgres":
        import os

        dsn = os.environ.get("OO_POSTGRES_DSN")
        if not dsn:
            pytest.skip("PENDING -- no local Postgres; set OO_POSTGRES_DSN")
        from ..backends.postgres import PostgresAdapter

        schema = "oo_guest_" + uuid.uuid4().hex[:12]
        owner = PostgresAdapter(dsn, schema=schema)
        owner._execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        guest = PostgresAdapter(dsn, schema=schema, owns_schema=False)
    else:
        pytest.skip("PENDING -- owns_schema is a property of the reference backends")

    assert guest.capabilities().owns_schema is False
    # C0-01's invariant, held to properly. This line used to read
    # ``assert ... .why.get("owns_schema") or True``, which asserts nothing -- and both
    # reference backends did in fact return an empty `why` here, because every fixture
    # backend is owns_schema=True and nothing else ever built one. Row 3d.
    assert guest.capabilities().why.get("owns_schema", "").strip()
    assert guest.capabilities().missing_why() == ()

    # 1. An empty store: verify-only must REFUSE, and must not fix it by issuing DDL.
    with pytest.raises(SchemaMismatch) as raised:
        guest.migrate()
    assert "oo_type" in str(raised.value), "the refusal names what is missing"
    with pytest.raises(SchemaMismatch):
        guest.migrate()  # still missing -- nothing was created behind our back

    # 2. Once the owner has created the schema, the guest verifies and returns.
    if backend == "sqlite":
        from ..backends.sqlite import SQLiteAdapter

        SQLiteAdapter(path).migrate()
    else:
        owner.migrate()
    version = guest.migrate()
    assert isinstance(version, int) and version >= 1

    # 3. And it is usable: verify-only is not read-only.
    guest.put_type(_type(name="facility"), expect_absent=True)
    assert guest.get_type("default", "facility", kind="entity") is not None
    if backend == "postgres":
        owner._execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


class _Boom(RuntimeError):
    """The host's work must survive this; the adapter's must not."""


def _borrowed_pair(backend, tmp_path):
    """A connection the HOST owns, and an adapter opened over it.

    Returns ``(guest, outsider, host_begin, host_open, host_commit, teardown)``.
    ``outsider(name)`` counts rows from an INDEPENDENT connection, which is how "the
    host has not committed yet" is observed from outside rather than asserted.
    """
    if backend == "sqlite":
        import sqlite3

        from ..backends.sqlite import SQLiteAdapter

        path = str(tmp_path / "borrowed.sqlite")
        owner = SQLiteAdapter(path)
        owner.migrate()  # the HOST's schema, created and committed before we borrow
        owner.close()

        host = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        host.execute("PRAGMA foreign_keys = ON")
        host.execute("PRAGMA busy_timeout = 5000")
        guest = SQLiteAdapter.open(connection=host, owns_schema=False)

        def outsider(name):
            other = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
            other.execute("PRAGMA busy_timeout = 2000")
            try:
                sql = "SELECT count(*) FROM oo_type WHERE name = ?"
                return other.execute(sql, (name,)).fetchone()[0]
            finally:
                other.close()

        def host_begin():
            host.execute("BEGIN IMMEDIATE")

        def host_open():
            return bool(host.in_transaction)

        def host_commit():
            host.execute("COMMIT")

        def teardown():
            host.close()

        return guest, outsider, host_begin, host_open, host_commit, teardown

    if backend == "postgres":
        dsn = os.environ.get("OO_POSTGRES_DSN")
        if not dsn:
            pytest.skip("PENDING -- no local Postgres; set OO_POSTGRES_DSN")
        psycopg = pytest.importorskip("psycopg", reason="PENDING -- psycopg not installed")

        from ..backends.postgres import PostgresAdapter

        schema = "oo_borrow_" + uuid.uuid4().hex[:12]
        owner = PostgresAdapter(dsn, schema=schema)
        owner.migrate()  # the HOST's schema, committed before we borrow

        # autocommit stays FALSE: a host that manages its own transaction, which is the
        # shape beacon's AsyncSession has and the shape U1 was wrong for.
        host = psycopg.connect(dsn)
        with host.cursor() as cur:
            cur.execute('SET search_path TO "' + schema + '"')
        guest = PostgresAdapter.open(connection=host, schema=schema, owns_schema=False)

        def outsider(name):
            other = psycopg.connect(dsn, autocommit=True)
            try:
                with other.cursor() as cur:
                    cur.execute('SET search_path TO "' + schema + '"')
                    cur.execute("SELECT count(*) FROM oo_type WHERE name = %s", (name,))
                    return cur.fetchone()[0]
            finally:
                other.close()

        def host_begin():
            # psycopg3 with autocommit=False begins implicitly on the first statement,
            # and the SET search_path above already was one. Assert it, do not assume it.
            assert host.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS

        def host_open():
            return host.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS

        def host_commit():
            host.commit()

        def teardown():
            host.close()
            owner._execute('DROP SCHEMA IF EXISTS "' + schema + '" CASCADE')
            owner.close()

        return guest, outsider, host_begin, host_open, host_commit, teardown

    pytest.skip(
        "PENDING -- a borrowed connection is a property of the reference backends' "
        "drivers; a foreign adapter declares its own transaction_scope."
    )


def test_c0_12_a_borrowed_connection_uses_savepoints_and_never_commits(backend, tmp_path):
    """**U1 / ruling R5 -- the transaction seam beacon 21.2 builds against.**

    PACKAGE.md 3 item 3 and 3.5: an adapter handed a connection it does not own declares
    ``transaction_scope="savepoint"``, and ``transaction()`` then brackets its writes in
    a SAVEPOINT -- RELEASE on clean exit, ROLLBACK TO on exception -- and **never
    commits**. The outer commit belongs to the host.

    **What this is a regression test for.** ``AsyncPostgresAdapter.open(connection=...)``
    accepted a borrowed connection and then called ``set_autocommit(True)`` on it, and
    ``transaction()`` committed at depth 0. The host shared a connection and did *not*
    share a transaction: the adapter silently ended -- or forbade -- the caller's
    transaction, and an adapter-side failure could not be rolled back without discarding
    the host's own work. Found by beacon 21.1 (U1), ruled in R5, fixed by row 3d.

    Three things are asserted, and they are the three that make the seam usable:

    1. an exception inside ``transaction()`` leaves the **host's** transaction OPEN with
       only the savepoint rolled back -- the host's earlier work is still there;
    2. a clean exit is **not durable** until the host commits: an independent connection
       sees nothing;
    3. re-entrant calls **join** the outermost savepoint (R5 point 3).

    SQLite is here for the same reason Postgres is: 2B's harness must not be
    Postgres-only, and SQLite has SAVEPOINT.
    """
    guest, outsider, host_begin, host_open, host_commit, teardown = _borrowed_pair(
        backend, tmp_path
    )
    try:
        caps = guest.capabilities()
        assert caps.transaction_scope == "savepoint", "borrowed DECLARES; it is not silent"
        assert caps.transactional is True, (
            "R5 point 2: a savepoint adapter is still transactional -- G2 atomicity "
            "holds inside the host's transaction"
        )
        assert caps.why.get("transaction_scope", "").strip(), (
            "and it carries the sentence that stops a clean return reading as durable"
        )
        assert caps.missing_why() == ()

        host_begin()
        assert guest.migrate() >= 1  # verify-only; the host owns this schema

        # The host's own work, done through the borrowed handle, before anything fails.
        guest.put_type(_type(name="host_row"), expect_absent=True)

        # 1. An exception rolls the SAVEPOINT back and leaves the host transaction open.
        with pytest.raises(_Boom):
            with guest.transaction():
                guest.put_type(_type(name="doomed"), expect_absent=True)
                raise _Boom("the adapter's failure is not the host's")
        assert guest.get_type("default", "doomed", kind="entity") is None
        assert guest.get_type("default", "host_row", kind="entity") is not None, (
            "the host's earlier work is in the same transaction and must survive"
        )
        assert host_open(), (
            "the host's outer transaction must still be OPEN -- ending it is the defect "
            "U1 names: sharing a connection is not sharing a transaction"
        )

        # 2. Re-entrant calls join the outermost savepoint (R5 point 3): a failure in the
        #    inner call discards the outer call's write too, and still not the host's.
        with pytest.raises(_Boom):
            with guest.transaction():
                guest.put_type(_type(name="outer"), expect_absent=True)
                with guest.transaction():
                    guest.put_type(_type(name="inner"), expect_absent=True)
                    raise _Boom("joined, so both go")
        assert guest.get_type("default", "outer", kind="entity") is None
        assert guest.get_type("default", "inner", kind="entity") is None
        assert host_open()

        # 3. A clean exit RELEASEs -- and is NOT durable until the host commits.
        with guest.transaction():
            guest.put_type(_type(name="clean"), expect_absent=True)
        assert guest.get_type("default", "clean", kind="entity") is not None
        assert host_open(), "RELEASE is not COMMIT"
        assert outsider("clean") == 0, (
            "the adapter must never commit a connection it does not own: durability at "
            "clean exit is the host's, and until the host commits nobody else sees it"
        )
        assert outsider("host_row") == 0

        # ...and the host's commit makes all of it durable, in one transaction.
        host_commit()
        assert outsider("clean") == 1 and outsider("host_row") == 1
        assert outsider("doomed") == 0 and outsider("outer") == 0
    finally:
        teardown()
