"""The two reference backends. A third-party backend implements the same protocol."""

from .sqlite import SQLiteAdapter

__all__ = ["SQLiteAdapter", "PostgresAdapter"]


def __getattr__(name: str):
    # psycopg is an extra; importing it eagerly would make the base install need it.
    if name == "PostgresAdapter":
        from .postgres import PostgresAdapter

        return PostgresAdapter
    raise AttributeError(name)
