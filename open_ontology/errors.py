"""Exceptions that are part of the public contract.

``UnknownType`` is a specified behaviour (INTERFACE.md 5.1), so it is API, not an
implementation detail. The rest are raised by the storage layer and named here so a
third-party adapter can raise the same things the reference backends do.
"""

from __future__ import annotations

__all__ = [
    "OpenOntologyError",
    "UnknownType",
    "AlreadyExists",
    "AmbiguousKind",
    "SchemaMismatch",
    "StoreVersionUnknown",
    "NotSupported",
]


class OpenOntologyError(Exception):
    """Base for everything this package raises deliberately."""


class UnknownType(OpenOntologyError, KeyError):
    """The named type is not in the store.

    INTERFACE.md 5.1: raised rather than returning an empty report, because an empty
    report reads as "nothing gates on this".
    """

    def __init__(self, name: str, *, namespace: str = "default", kind: str | None = None):
        self.name = name
        self.namespace = namespace
        self.kind = kind
        where = f"{namespace}:{kind}:{name}" if kind else f"{namespace}:{name}"
        super().__init__(f"no type {where}")

    def __str__(self) -> str:  # KeyError would repr() the message otherwise
        return self.args[0]


class AlreadyExists(OpenOntologyError):
    """``put_type(expect_absent=True)`` hit an existing key.

    Guarantee G1 (PACKAGE.md 3.5): this must come from a database constraint, never
    from a read-then-write check.
    """


class AmbiguousKind(OpenOntologyError):
    """``get_type(kind=None)`` matched the same name under two kinds.

    Legal: uniqueness is per ``(namespace, kind)``.
    """


class SchemaMismatch(OpenOntologyError):
    """A store whose schema this package does not own is missing columns it needs.

    PACKAGE.md 9.3 -- ``migrate()`` is verify-only when ``owns_schema`` is False.
    """


class StoreVersionUnknown(OpenOntologyError):
    """The store's schema version is higher than this package knows.

    PACKAGE.md 9.2: refused, never silently downgraded.
    """


class NotSupported(OpenOntologyError):
    """The adapter declares it cannot do this at all.

    Distinct from an uncertain answer: a primitive that *can* be asked but cannot
    answer returns ``None`` plus a ``why``. This is for primitives that have no
    backing store at all (``stores_proposals=False`` and friends).
    """
