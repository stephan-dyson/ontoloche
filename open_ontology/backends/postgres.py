"""Postgres backend -- PACKAGE.md 4.4. The reference deployment.

``psycopg`` v3 only. ``psycopg2`` is a different driver with a different parameter
style, and supporting both doubles the SQL layer for no gain.

The two things that differ from SQLite and matter:

* ``jsonb`` rather than TEXT, and ``timestamptz`` rather than ISO text. Both handled in
  ``PostgresDialect``, not scattered through the queries.
* ``SELECT ... FOR UPDATE`` on the proposal read inside a transaction, which is what
  turns ``already_decided`` into an idempotent refusal rather than a double-approve.
  SQLite gets the same guarantee from the BEGIN IMMEDIATE write lock.
"""

from __future__ import annotations

from typing import Any, Callable

from ._sql import BaseSqlAdapter, PostgresDialect

__all__ = ["PostgresAdapter"]


class PostgresAdapter(BaseSqlAdapter):
    backend_name = "postgres"

    def __init__(
        self,
        conninfo: str | None = None,
        *,
        connection_factory: Callable[[], Any] | None = None,
        schema: str | None = None,
        owns_schema: bool = True,
    ):
        import psycopg  # imported here so the base install stays dependency-free

        super().__init__(PostgresDialect())
        self._psycopg = psycopg
        self._owns_schema = owns_schema
        if connection_factory is not None:
            self.conn = connection_factory()
        elif conninfo is not None:
            self.conn = psycopg.connect(conninfo, autocommit=True)
        else:
            raise ValueError("PostgresAdapter needs a conninfo or a connection_factory")
        self.conn.autocommit = True
        self.schema = schema
        if schema:
            # One schema per store keeps two adapters in one process (which the suite
            # requires) from sharing a table name.
            with self.conn.cursor() as cur:
                cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                cur.execute(f'SET search_path TO "{schema}"')

    # ------------------------------------------------------------------ connection
    def _execute(self, sql: str, params: tuple | list = ()) -> Any:
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(params) or None)
            return cur

    def _fetchall(self, sql: str, params: tuple | list = ()) -> list[tuple]:
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(params) or None)
            return list(cur.fetchall())

    def _fetchone(self, sql: str, params: tuple | list = ()) -> tuple | None:
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(params) or None)
            return cur.fetchone()

    def _begin(self) -> None:
        self._execute("BEGIN")

    def _commit(self) -> None:
        self._execute("COMMIT")

    def _rollback(self) -> None:
        self._execute("ROLLBACK")

    def _lock_clause(self) -> str:
        return " FOR UPDATE"

    @property
    def _integrity_errors(self) -> tuple[type[BaseException], ...]:
        return (self._psycopg.errors.IntegrityError,)

    def _recover_from_failed_probe(self) -> None:
        status = self.conn.info.transaction_status
        if status == self._psycopg.pq.TransactionStatus.INERROR:
            self._rollback()

    def _columns_of(self, table: str) -> tuple[str, ...]:
        rows = self._fetchall(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND table_schema = COALESCE(%s, current_schema())",
            (table, self.schema),
        )
        return tuple(r[0] for r in rows)

    def close(self) -> None:
        self.conn.close()
