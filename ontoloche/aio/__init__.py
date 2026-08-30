"""``ontoloche.aio`` -- the async mirror. Deliverable 3b, ruling R1.

Beacon is ``AsyncSession`` throughout. A sync adapter cannot share beacon's
transaction, and driving one from a thread is not safe, so ROADMAP #5 needs an
``AsyncStorageAdapter``. This package is it.

**Almost nothing here was written by hand.** ``adapter.py``, ``registry.py`` and
``backends/_sql.py`` are generated from their sync originals by ``tools/unasync.py``
and checked in; the sync package stays the single source of truth and
``ontoloche/aio/contract/test_generated_matches_source.py`` fails if the two have
drifted apart. What *is* hand-written is the part that genuinely differs: the two
drivers (``aiosqlite`` and ``psycopg``'s ``AsyncConnection``), because a driver's
connection layer is the one thing a mechanical transformation cannot invent.

The one shape difference, and why -- deviation D-A1 in ``docs/runs/3B-ASYNC.md``::

    registry = await AsyncRegistry.open(adapter)     # not AsyncRegistry(adapter)

``Registry.__init__`` calls ``capabilities()`` and ``migrate()``; ``__init__`` cannot
be a coroutine, so construction moved to a classmethod. Everything else is the same
call with the same arguments, returning the same shapes, awaited.
"""

from __future__ import annotations

from .adapter import AsyncAttributeStore, AsyncStorageAdapter
from .registry import AsyncRegistry

__all__ = ["AsyncRegistry", "AsyncStorageAdapter", "AsyncAttributeStore"]
