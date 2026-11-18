"""The two reference backends. A third-party backend implements the same protocol."""

from ._sql import HostInstanceTable
from .sqlite import SQLiteAdapter

#: ``HostInstanceTable`` is how a host points primitives 22 and 23 at a table it owns
#: (INGEST.md 2, row 7b). Public because the host, not this package, calls it.
__all__ = ["HostInstanceTable", "SQLiteAdapter", "PostgresAdapter"]


def __getattr__(name: str):
    # psycopg is an extra; importing it eagerly would make the base install need it.
    if name == "PostgresAdapter":
        from .postgres import PostgresAdapter

        return PostgresAdapter
    raise AttributeError(name)
