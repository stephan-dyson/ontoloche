"""The two async reference backends. A third-party backend implements the same protocol."""

from __future__ import annotations

__all__ = ["AsyncSQLiteAdapter", "AsyncPostgresAdapter"]


def __getattr__(name: str):
    # aiosqlite and psycopg are both extras; importing either eagerly would make the
    # base install need it, and the base install has zero runtime dependencies.
    if name == "AsyncSQLiteAdapter":
        from .sqlite import AsyncSQLiteAdapter

        return AsyncSQLiteAdapter
    if name == "AsyncPostgresAdapter":
        from .postgres import AsyncPostgresAdapter

        return AsyncPostgresAdapter
    raise AttributeError(name)
