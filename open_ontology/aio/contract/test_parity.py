"""Surface parity between the sync facade and its async mirror -- not one of the 115.

The byte-for-byte check in ``test_generated_matches_source.py`` proves the *generated*
files are current. It cannot prove the generator was asked to generate the right
things: a method dropped from a spec's ``extract`` list, or a primitive that quietly
stayed synchronous, would leave a mirror that is stale in a way regeneration agrees
with. So this reads the two classes and compares them.

Three claims, and they are the ones ruling R1 turns on:

1. the async facade has **every** call the sync facade has, and no extra ones beyond
   the documented construction pair (``open``/``_open``, deviation D-A1);
2. every call takes the **same parameters** -- same names, same kinds, same defaults;
3. every call that does I/O is a **coroutine**, and ``transaction()`` is not -- it is
   called and its result is used with ``async with``, which is the one place a
   mechanical sync-to-async translation most often gets wrong.
"""

from __future__ import annotations

import inspect

import pytest

from open_ontology.adapter import AttributeStore, StorageAdapter
from open_ontology.aio.adapter import AsyncAttributeStore, AsyncStorageAdapter
from open_ontology.aio.registry import AsyncRegistry
from open_ontology.registry import Registry

pytestmark = pytest.mark.nonbinding

#: PACKAGE.md 3.4. ``transaction`` is deliberately absent: it stays a plain call whose
#: result is an async context manager.
AWAITABLE_PRIMITIVES = (
    "capabilities",
    "migrate",
    "put_type",
    "get_type",
    "find_types",
    "put_proposal",
    "get_proposal",
    "find_proposals",
    "put_consumer",
    "find_consumers",
    "bump_usage",
    "get_usage",
    "append_event",
    "read_events",
    # EDGES.md 7.1's three, row 4b.
    "put_edge",
    "get_edge",
    "find_edges",
)

#: INTERFACE.md 5 -- the thirteen the facade exposes, plus the three package-local ones.
FACADE_CALLS = (
    "consumers",
    "predicates",
    "resolve_type",
    "propose_type",
    "approve",
    "reject",
    "list_types",
    "usage",
    "provenance",
    "retire",
    "merge_types",
    "register_consumer",
    "record_use",
    "import_types",
    "register_attribute_schema",
    "attribute_census",
)

#: The only names the async facade is allowed to add. ``__init__`` cannot await, so
#: construction is ``await AsyncRegistry.open(adapter)`` (deviation D-A1).
CONSTRUCTION_ONLY = {"open", "_open"}


def _callables(cls) -> set[str]:
    return {
        name
        for name, value in vars(cls).items()
        if callable(value) or isinstance(value, (classmethod, staticmethod))
    }


def _shape(function) -> list[tuple[str, object, object]]:
    """Parameter names, kinds and defaults. Annotations are excluded on purpose --
    they differ by exactly the rename table, and the byte comparison already covers
    them."""
    return [
        (p.name, p.kind, p.default)
        for p in inspect.signature(function).parameters.values()
    ]


def test_the_async_facade_has_every_sync_call_and_no_others():
    sync, asynchronous = _callables(Registry), _callables(AsyncRegistry)
    assert sorted(sync - asynchronous) == [], "calls missing from the async facade"
    assert asynchronous - sync == CONSTRUCTION_ONLY, (
        "the async facade has grown a call the sync one does not have; the only "
        f"permitted additions are {sorted(CONSTRUCTION_ONLY)}"
    )


def test_every_call_takes_the_same_parameters():
    mismatched = []
    for name in sorted(_callables(Registry)):
        if name == "__init__":
            continue  # D-A1: the constructor is the documented exception
        if _shape(getattr(Registry, name)) != _shape(getattr(AsyncRegistry, name)):
            mismatched.append(name)
    assert mismatched == [], f"signature drift between the two facades: {mismatched}"


@pytest.mark.parametrize("name", FACADE_CALLS)
def test_every_facade_call_is_a_coroutine(name):
    assert not inspect.iscoroutinefunction(getattr(Registry, name))
    assert inspect.iscoroutinefunction(getattr(AsyncRegistry, name)), (
        f"{name} is not awaitable on the async facade"
    )


def test_the_async_protocol_is_the_same_eighteen_primitives():
    """Fifteen until row 4b, which added EDGES.md 7.1's three.

    The number is asserted rather than derived on purpose: this test's job is to notice
    that the protocol GREW, and a count computed from the thing it is counting notices
    nothing. It is the one place in this repository where a hard-coded number is the
    check rather than the liability -- and it is held against
    `AWAITABLE_PRIMITIVES` + `transaction`, so the two cannot drift apart either.
    """
    sync = {n for n in vars(StorageAdapter) if not n.startswith("_")}
    asynchronous = {n for n in vars(AsyncStorageAdapter) if not n.startswith("_")}
    assert sync == asynchronous
    assert len(sync) == 18
    assert sync == set(AWAITABLE_PRIMITIVES) | {"transaction"}

    sync_attrs = {n for n in vars(AttributeStore) if not n.startswith("_")}
    async_attrs = {n for n in vars(AsyncAttributeStore) if not n.startswith("_")}
    assert sync_attrs == async_attrs


@pytest.mark.parametrize("name", AWAITABLE_PRIMITIVES)
def test_every_primitive_but_transaction_is_a_coroutine(name):
    assert inspect.iscoroutinefunction(getattr(AsyncStorageAdapter, name))
    assert _shape(getattr(StorageAdapter, name)) == _shape(getattr(AsyncStorageAdapter, name))


def test_transaction_is_called_not_awaited():
    """``async with adapter.transaction():`` -- awaiting it would be the mistranslation.

    The primitive returns an async context manager. A translation that made it a
    coroutine would still typecheck at the call site and would silently stop rolling
    anything back, which is guarantee G2 gone.
    """
    assert not inspect.iscoroutinefunction(AsyncStorageAdapter.transaction)
    assert "AbstractAsyncContextManager" in str(
        inspect.signature(AsyncStorageAdapter.transaction).return_annotation
    )
