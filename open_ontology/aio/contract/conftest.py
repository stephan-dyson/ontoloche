"""The async adapter factory, parametrised over backends.

The same rule as the sync suite (PACKAGE.md 6.1): *both reference backends, in one
process, in one run*, and when there is no Postgres to talk to its leg **skips with a
reason** rather than vanishing -- a leg that disappears from the run is a leg nobody
notices is missing.

Three things here are async-specific and none of them is in the generated tree:

the event loop policy
    ``psycopg`` refuses to run async on Windows' default ``ProactorEventLoop`` and
    raises ``InterfaceError`` saying so. On ``win32`` this module selects a selector
    loop at import, before any loop exists; on every other platform it changes
    nothing. Deviation D-A3.

auto mode
    the suite is plain ``async def test_*`` functions with no ``@pytest.mark.asyncio``
    on them, because the marker is not in the sync source and the ids must stay
    identical. ``asyncio_mode = "auto"`` is in ``pyproject.toml`` for a repository run,
    and ``run_async_contract_suite`` passes ``--asyncio-mode=auto`` for an installed
    one. Deviation D-A2.

the fixtures themselves
    are async, and ``make_registry`` hands back an async builder, because
    ``AsyncRegistry`` is constructed with ``await AsyncRegistry.open(...)``
    (deviation D-A1).

Point it at a Postgres with::

    OO_POSTGRES_DSN=postgresql://user:pw@localhost:5432/postgres pytest --pyargs open_ontology.aio.contract
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

import pytest

if sys.platform == "win32":
    # Not a preference and not a Windows nicety: psycopg raises
    # InterfaceError("Psycopg cannot use the 'ProactorEventLoop' to run in async mode")
    # on the platform default. Set before any loop is created, so every runner the
    # asyncio plugin builds for this session inherits it.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from open_ontology._clock import FixedClock
from open_ontology.aio.backends.sqlite import AsyncSQLiteAdapter
from open_ontology.aio.registry import AsyncRegistry
from open_ontology.policy import NamespacePolicy

from . import _support

POSTGRES_DSN = os.environ.get("OO_POSTGRES_DSN")
BACKENDS = ("sqlite", "postgres")


def pytest_configure(config):
    config.addinivalue_line("markers", "cms: the CMS design test (PACKAGE.md 8)")
    config.addinivalue_line("markers", "nonbinding: outside the conformance definition")


def pytest_generate_tests(metafunc):
    if "backend" not in metafunc.fixturenames:
        return
    if _support.EXTERNAL_FACTORY is not None:
        metafunc.parametrize("backend", ["external"])
        return
    metafunc.parametrize("backend", list(BACKENDS))


@pytest.fixture
async def adapter_factory(backend):
    """An async callable returning a fresh, migrated, empty store."""
    made = []

    if backend == "external":
        factory = _support.EXTERNAL_FACTORY

        async def build():
            adapter = await factory()
            await adapter.migrate()
            made.append(adapter)
            return adapter

    elif backend == "sqlite":

        async def build():
            adapter = await AsyncSQLiteAdapter.open(":memory:")
            await adapter.migrate()
            made.append(adapter)
            return adapter

    elif backend == "postgres":
        if not POSTGRES_DSN:
            pytest.skip(
                "PENDING -- no local Postgres. Set OO_POSTGRES_DSN to run this leg; "
                "the 2B gate is not claimable until it is green."
            )
        try:
            import psycopg  # noqa: F401
        except ImportError:  # pragma: no cover - environment-dependent
            pytest.skip("PENDING -- psycopg is not installed (pip install -e '.[postgres]')")

        from open_ontology.aio.backends.postgres import AsyncPostgresAdapter

        async def build():
            schema = "oo_" + uuid.uuid4().hex[:12]
            adapter = await AsyncPostgresAdapter.open(POSTGRES_DSN, schema=schema)
            await adapter.migrate()
            made.append(adapter)
            return adapter

    else:  # pragma: no cover
        raise AssertionError(backend)

    yield build

    for adapter in made:
        try:
            if getattr(adapter, "schema", None):
                await adapter._execute(f'DROP SCHEMA IF EXISTS "{adapter.schema}" CASCADE')
            close = getattr(adapter, "close", None)
            if close:
                await close()
        except Exception:  # pragma: no cover - teardown must not mask a failure
            pass


@pytest.fixture
async def adapter(adapter_factory):
    return await adapter_factory()


@pytest.fixture
def clock():
    return FixedClock()


@pytest.fixture
def make_registry(clock):
    """``await make_registry(adapter, **policy_kwargs)`` -- one clock across the test."""

    async def build(adapter, **policy_kwargs):
        policies = policy_kwargs.pop("policies", None)
        return await AsyncRegistry.open(
            adapter,
            clock=clock,
            policy=NamespacePolicy(**policy_kwargs),
            policies=policies,
        )

    return build


@pytest.fixture
async def registry(adapter, make_registry):
    return await make_registry(adapter)
