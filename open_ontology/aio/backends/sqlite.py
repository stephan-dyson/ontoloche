"""Async SQLite backend -- the async mirror of ``backends/sqlite.py``.

**Why ``aiosqlite`` rather than something written here.** SQLite has no asynchronous C
API: every statement is a blocking call into the library, and every async SQLite story
in Python is therefore a thread offload -- there is no third option to choose. Given
that, the choice is between the maintained single-purpose wrapper that everyone else
uses and a private reimplementation of the same design with fewer eyes on it.
``aiosqlite`` pins each connection to one dedicated worker thread, which preserves
``sqlite3``'s connection affinity for free; a hand-rolled ``run_in_executor`` wrapper
over a shared thread pool would not, and that is exactly the "driving a sync adapter
from a thread is not safe" failure ruling R1 exists to avoid. It is an **extra**
(``pip install -e ".[aio]"``), so the base install stays at zero runtime dependencies.

What the offload does *not* change is the thing that matters for R1: the contract above
this line is `await`-able all the way down and shares the caller's event loop, so an
``AsyncSession`` can hold the registry's transaction. Whether the bytes reach the disk
from this thread or another is the driver's business, not the protocol's.

Every connection setting below is the sync backend's, verbatim and for its reasons:
``isolation_level=None`` plus an explicit ``BEGIN IMMEDIATE`` (guarantee G2 -- a
DEFERRED transaction that reads then writes turns a routine approval into a spurious
SQLITE_BUSY), WAL for file-backed stores, ``foreign_keys=ON`` for the predicate
cascade, and a 5s busy timeout so a queued writer waits rather than failing.
"""

from __future__ import annotations

from typing import Any

from open_ontology.aio.backends._sql import AsyncBaseSqlAdapter
from open_ontology.backends._sql import SqliteDialect

__all__ = ["AsyncSQLiteAdapter"]


class AsyncSQLiteAdapter(AsyncBaseSqlAdapter):
    backend_name = "sqlite"

    def __init__(self, conn: Any, path: str, *, owns_schema: bool = True):
        """Takes an already-open connection. Use :meth:`open`; a constructor cannot await."""
        super().__init__(SqliteDialect())
        self.path = path
        self._owns_schema = owns_schema
        self.conn = conn

    @classmethod
    async def open(
        cls,
        path: str = ":memory:",
        *,
        connection: Any | None = None,
        owns_schema: bool = True,
    ) -> "AsyncSQLiteAdapter":
        if connection is not None:
            # BORROWED -- ruling R5 / U1. SQLite supports SAVEPOINT, so the borrowed
            # case is not Postgres-only: 2B's harness can prove the seam on either
            # backend. Every connection setting below is the HOST's to choose; we set
            # none of them, exactly as we set no autocommit on a borrowed psycopg one.
            self = cls(connection, path, owns_schema=owns_schema)
            self._borrowed = True
            return self

        import aiosqlite  # an extra, so the base install stays dependency-free

        conn = await aiosqlite.connect(path, isolation_level=None, check_same_thread=False)
        if path != ":memory:":
            async with conn.execute("PRAGMA journal_mode = WAL"):
                pass
        async with conn.execute("PRAGMA foreign_keys = ON"):
            pass
        async with conn.execute("PRAGMA busy_timeout = 5000"):
            pass
        return cls(conn, path, owns_schema=owns_schema)

    # ------------------------------------------------------------------ connection
    async def _execute(self, sql: str, params: tuple | list = ()) -> Any:
        # ``async with`` rather than a bare ``await``: aiosqlite's cursors live on the
        # worker thread and are not garbage-collected there. No caller uses the return
        # value -- the sync backend's cursor is dead by the time it is handed back too.
        async with self.conn.execute(sql, tuple(params)):
            return None

    async def _fetchall(self, sql: str, params: tuple | list = ()) -> list[tuple]:
        async with self.conn.execute(sql, tuple(params)) as cursor:
            return list(await cursor.fetchall())

    async def _fetchone(self, sql: str, params: tuple | list = ()) -> tuple | None:
        async with self.conn.execute(sql, tuple(params)) as cursor:
            return await cursor.fetchone()

    def _host_transaction_state(self) -> str | None:
        # aiosqlite proxies the driver connection's attribute; no await needed.
        return "open" if self.conn.in_transaction else "none"

    async def _begin(self) -> None:
        async with self.conn.execute("BEGIN IMMEDIATE"):
            pass

    async def _commit(self) -> None:
        async with self.conn.execute("COMMIT"):
            pass

    async def _rollback(self) -> None:
        async with self.conn.execute("ROLLBACK"):
            pass

    @property
    def _integrity_errors(self) -> tuple[type[BaseException], ...]:
        import sqlite3

        # aiosqlite re-raises the driver's own exceptions across the thread boundary.
        return (sqlite3.IntegrityError,)

    async def _columns_of(self, table: str) -> tuple[str, ...]:
        rows = await self._fetchall(f"PRAGMA table_info({table})")
        return tuple(r[1] for r in rows)

    async def close(self) -> None:
        """Closes only what this adapter opened. There is no AsyncRegistry.close().

        A borrowed connection is the host's; closing it here would be the same class of
        mistake as committing it (ruling R5).
        """
        if self._borrowed:
            return
        await self.conn.close()
