"""The two async reference backends. A third-party backend implements the same protocol."""

from __future__ import annotations

#: ``HostInstanceTable`` is the host's binding for primitives 22 and 23 (INGEST.md 2,
#: row 7b). One dataclass for both surfaces: it holds names, not a connection.
__all__ = ["HostInstanceTable", "AsyncSQLiteAdapter", "AsyncPostgresAdapter"]


def __getattr__(name: str):
    # aiosqlite and psycopg are both extras; importing either eagerly would make the
    # base install need it, and the base install has zero runtime dependencies.
    if name == "HostInstanceTable":
        from ._sql import HostInstanceTable

        return HostInstanceTable
    if name == "AsyncSQLiteAdapter":
        from .sqlite import AsyncSQLiteAdapter

        return AsyncSQLiteAdapter
    if name == "AsyncPostgresAdapter":
        from .postgres import AsyncPostgresAdapter

        return AsyncPostgresAdapter
    raise AttributeError(name)
