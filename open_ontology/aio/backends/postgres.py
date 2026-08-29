"""Async Postgres backend -- the async mirror of ``backends/postgres.py``.

No new dependency: ``psycopg`` v3 ships ``AsyncConnection`` in the same package the
sync backend already uses, over the same libpq, with the same adaptation rules. So the
Postgres leg is genuinely async rather than a thread offload, and the ``[postgres]``
extra covers both backends.

**One environment note, and it is not optional on Windows.** ``psycopg`` refuses to run
async on asyncio's ``ProactorEventLoop`` -- the default event loop policy on Windows --
and says so loudly::

    InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.

The suite's ``conftest`` therefore selects a selector event loop on ``win32``. An
application embedding this backend has to do the same; recorded as D-A3 in
``docs/runs/3B-ASYNC.md``.

The two things that differ from SQLite are the sync backend's, unchanged: ``jsonb`` and
``timestamptz`` (handled in ``PostgresDialect``, borrowed from the sync package, not
copied), and ``SELECT ... FOR UPDATE`` on the proposal read inside a transaction, which
is what turns ``already_decided`` into an idempotent refusal rather than a
double-approve.
"""

from __future__ import annotations

from typing import Any

from open_ontology.aio.backends._sql import AsyncBaseSqlAdapter
from open_ontology.backends._sql import PostgresDialect

__all__ = ["AsyncPostgresAdapter"]


class AsyncPostgresAdapter(AsyncBaseSqlAdapter):
    backend_name = "postgres"

    def __init__(
        self,
        conn: Any,
        psycopg_module: Any,
        *,
        schema: str | None = None,
        owns_schema: bool = True,
    ):
        """Takes an already-open connection. Use :meth:`open`; a constructor cannot await."""
        super().__init__(PostgresDialect())
        self._psycopg = psycopg_module
        self._owns_schema = owns_schema
        self.conn = conn
        self.schema = schema

    @classmethod
    async def open(
        cls,
        conninfo: str | None = None,
        *,
        connection: Any | None = None,
        schema: str | None = None,
        owns_schema: bool = True,
    ) -> "AsyncPostgresAdapter":
        import psycopg  # an extra, so the base install stays dependency-free

        borrowed = connection is not None
        if borrowed:
            conn = connection
        elif conninfo is not None:
            conn = await psycopg.AsyncConnection.connect(conninfo, autocommit=True)
        else:
            raise ValueError("AsyncPostgresAdapter needs a conninfo or a connection")
        if not borrowed:
            # U1 / ruling R5. This line used to run unconditionally, and on a BORROWED
            # connection it was the bug beacon 21.1 found: sharing a connection is not
            # sharing a transaction. A connection we were lent keeps every setting the
            # host chose, and transaction() uses SAVEPOINTs instead of BEGIN/COMMIT.
            await conn.set_autocommit(True)
        self = cls(conn, psycopg, schema=schema, owns_schema=owns_schema)
        self._borrowed = borrowed
        if schema:
            # One schema per store keeps two adapters in one process (which the suite
            # requires) from sharing a table name. Over a borrowed connection this is a
            # write like any other, so it goes through transaction() -- i.e. a savepoint.
            async with self.transaction():
                await self._execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                await self._execute(f'SET search_path TO "{schema}"')
        return self

    # ------------------------------------------------------------------ connection
    async def _execute(self, sql: str, params: tuple | list = ()) -> Any:
        async with self.conn.cursor() as cur:
            await cur.execute(sql, tuple(params) or None)
            return None

    async def _fetchall(self, sql: str, params: tuple | list = ()) -> list[tuple]:
        async with self.conn.cursor() as cur:
            await cur.execute(sql, tuple(params) or None)
            return list(await cur.fetchall())

    async def _fetchone(self, sql: str, params: tuple | list = ()) -> tuple | None:
        async with self.conn.cursor() as cur:
            await cur.execute(sql, tuple(params) or None)
            return await cur.fetchone()

    def _host_transaction_state(self) -> str | None:
        status = self.conn.info.transaction_status
        if status == self._psycopg.pq.TransactionStatus.INERROR:
            return "aborted"
        if status == self._psycopg.pq.TransactionStatus.INTRANS:
            return "open"
        return "none"

    async def _begin(self) -> None:
        await self._execute("BEGIN")

    async def _commit(self) -> None:
        await self._execute("COMMIT")

    async def _rollback(self) -> None:
        await self._execute("ROLLBACK")

    def _lock_clause(self) -> str:
        return " FOR UPDATE"

    @property
    def _integrity_errors(self) -> tuple[type[BaseException], ...]:
        return (self._psycopg.errors.IntegrityError,)

    async def _recover_from_failed_probe(self) -> None:
        status = self.conn.info.transaction_status
        if status == self._psycopg.pq.TransactionStatus.INERROR:
            await self._rollback()

    async def _columns_of(self, table: str) -> tuple[str, ...]:
        rows = await self._fetchall(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND table_schema = COALESCE(%s, current_schema())",
            (table, self.schema),
        )
        return tuple(r[0] for r in rows)

    async def close(self) -> None:
        """A borrowed connection is the host's; closing it here would be the same class
        of mistake as committing it (ruling R5)."""
        if self._borrowed:
            return
        await self.conn.close()
