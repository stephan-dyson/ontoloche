"""SQLite backend -- PACKAGE.md 4.3. Zero-config, stdlib only, no dependency.

Every connection setting here is load-bearing:

``isolation_level=None``
    Python's ``sqlite3`` otherwise opens implicit DEFERRED transactions.

explicit ``BEGIN IMMEDIATE``
    A deferred transaction that starts with a read upgrades to a write transaction *if
    possible*, or returns SQLITE_BUSY. Every registry transaction reads then writes
    (approve reads the proposal, then writes four rows), so DEFERRED turns a routine
    approval into a spurious SQLITE_BUSY the moment there is a second writer.
    IMMEDIATE takes the write lock up front. This is guarantee G2, and it is also how
    ``already_decided`` stops being a race.

``Connection.autocommit`` is **not** used
    It arrived in Python 3.12 and the floor is 3.11, so the portable path is
    ``isolation_level=None`` plus an explicit BEGIN, which behaves identically on 3.11
    through 3.14.

WAL, ``foreign_keys=ON``, ``busy_timeout=5000``
    Readers do not block the writer; the predicate cascade depends on foreign keys,
    which SQLite has off by default; a queued writer waits rather than failing.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from ._sql import BaseSqlAdapter, SqliteDialect

__all__ = ["SQLiteAdapter"]


class SQLiteAdapter(BaseSqlAdapter):
    backend_name = "sqlite"

    def __init__(
        self,
        path: str = ":memory:",
        *,
        connection: Any | None = None,
        owns_schema: bool = True,
    ):
        super().__init__(SqliteDialect())
        self.path = path
        self._owns_schema = owns_schema
        if connection is not None:
            # BORROWED -- ruling R5 / U1. SQLite supports SAVEPOINT, so the borrowed
            # case is not Postgres-only: 2B's harness can prove the seam on either.
            # The connection's settings are the HOST's; we set none of them, exactly as
            # we set no autocommit on a borrowed psycopg connection.
            self.conn = connection
            self._borrowed = True
            return
        self.conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        if path != ":memory:":
            self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA busy_timeout = 5000")

    @classmethod
    def open(
        cls,
        path: str = ":memory:",
        *,
        connection: Any | None = None,
        owns_schema: bool = True,
    ) -> "SQLiteAdapter":
        """The sync twin of ``AsyncSQLiteAdapter.open``; nothing here needs to await."""
        return cls(path, connection=connection, owns_schema=owns_schema)

    # ------------------------------------------------------------------ connection
    def _execute(self, sql: str, params: tuple | list = ()) -> Any:
        return self.conn.execute(sql, tuple(params))

    def _fetchall(self, sql: str, params: tuple | list = ()) -> list[tuple]:
        return list(self.conn.execute(sql, tuple(params)).fetchall())

    def _fetchone(self, sql: str, params: tuple | list = ()) -> tuple | None:
        return self.conn.execute(sql, tuple(params)).fetchone()

    def _host_transaction_state(self) -> str | None:
        # sqlite3 has no aborted-transaction state: a failed statement does not poison
        # the transaction the way Postgres does, so there are only two answers here.
        return "open" if self.conn.in_transaction else "none"

    def _begin(self) -> None:
        self.conn.execute("BEGIN IMMEDIATE")

    def _commit(self) -> None:
        self.conn.execute("COMMIT")

    def _rollback(self) -> None:
        self.conn.execute("ROLLBACK")

    @property
    def _integrity_errors(self) -> tuple[type[BaseException], ...]:
        return (sqlite3.IntegrityError,)

    def _columns_of(self, table: str) -> tuple[str, ...]:
        rows = self._fetchall(f"PRAGMA table_info({table})")
        return tuple(r[1] for r in rows)

    def close(self) -> None:
        """Closes only what this adapter opened. There is no Registry.close().

        A borrowed connection is the host's; closing it here would be the same class of
        mistake as committing it (ruling R5).
        """
        if self._borrowed:
            return
        self.conn.close()
