"""Backends that declare they cannot do something -- test infrastructure, not shipped
behaviour.

PACKAGE.md 6.1's first rule is capability honesty: *a test whose subject is a
declared-False capability asserts the honest unknown, not a value.* Both reference
backends declare every flag True, so those tests need a backend that says no. That is
what these are: thin wrappers that declare a flag False and then behave as a backend
with that gap actually would -- ``bump_usage`` really is a no-op, ``read_events`` really
raises, membership really is unindexed.

They are also the cheapest available check on PACKAGE.md 7's claim that a one-table
registry can be conformant without weakening conformance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..adapter import (
    CAPABILITY_FLAGS,
    Capabilities,
    ConsumerRecord,
    EventRecord,
    ProposalPage,
    ProposalQuery,
    ProposalRecord,
    TypePage,
    TypeQuery,
    TypeRecord,
    UsageRecord,
)
from ..errors import NotSupported

__all__ = ["DegradedAdapter", "READ_ONLY_CONSUMERS"]

#: A sentinel for the one gap that is not a Capabilities flag: a consumer source that
#: can be read but not written (a checked-in config file -- PACKAGE.md 7.3).
READ_ONLY_CONSUMERS = "read_only_consumers"


#: The optional ``AttributeStore`` extension (PACKAGE.md 5.5, ruling R2). Outside the
#: fifteen primitives and outside conformance.
_ATTRIBUTE_STORE_METHODS = frozenset(
    {"put_attr_schema", "get_attr_schema", "observe_attributes", "read_attr_observed"}
)


class _DegradedBase:
    """Wraps a conformant adapter and takes capabilities away from it.

    ``pages_countable=False`` is not a capability flag; it is the ``TypePage.known is
    None`` case from PACKAGE.md 3.3, which no flag names.
    """

    def __init__(
        self,
        inner,
        *,
        why: dict[str, str] | None = None,
        pages_countable: bool = True,
        read_only_consumers: bool = False,
        **flags: bool,
    ):
        unknown = set(flags) - set(CAPABILITY_FLAGS)
        if unknown:
            raise ValueError(f"not capability flags: {sorted(unknown)}")
        self.inner = inner
        self._flags = flags
        self._pages_countable = pages_countable
        self._read_only_consumers = read_only_consumers
        self._why = dict(why or {})
        for flag, value in flags.items():
            if not value:
                self._why.setdefault(flag, f"this backend does not support {flag}")

    # ------------------------------------------------------------------- 1 and 2
    def capabilities(self) -> Capabilities:
        base = self.inner.capabilities()
        values = {flag: getattr(base, flag) for flag in CAPABILITY_FLAGS}
        values.update(self._flags)
        return Capabilities(**values, why={**base.why, **self._why})

    def migrate(self) -> int:
        return self.inner.migrate()

    def transaction(self):
        return self.inner.transaction()

    # ------------------------------------------------------------------- 4 and 5
    def _degrade_type(self, rec: TypeRecord | None) -> TypeRecord | None:
        if rec is None:
            return None
        caps = self.capabilities()
        changes: dict[str, Any] = {}
        if not caps.stores_attributes:
            changes["attributes"] = {}
        if not caps.stores_aliases:
            changes["aliases"] = ()
        if not caps.indexes_membership:
            changes["predicates"] = ()
        if not changes:
            return rec
        return TypeRecord(**{**rec.__dict__, **changes})

    def put_type(self, rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord:
        return self._degrade_type(self.inner.put_type(rec, expect_absent=expect_absent))

    def get_type(self, namespace: str, name: str, *, kind: str | None = None):
        return self._degrade_type(self.inner.get_type(namespace, name, kind=kind))

    # ------------------------------------------------------------------------- 6
    def find_types(self, q: TypeQuery) -> TypePage:
        caps = self.capabilities()
        if q.predicate is not None and not caps.indexes_membership:
            # Never known=0 -- that reads as "nothing is commentable".
            return TypePage(
                records=(),
                known=None,
                complete=False,
                why_incomplete=caps.reason("indexes_membership"),
            )
        page = self.inner.find_types(q)
        records = tuple(self._degrade_type(r) for r in page.records)
        if not self._pages_countable:
            return TypePage(
                records=records,
                known=None,
                complete=False,
                why_incomplete="this backend cannot count a result set",
            )
        return TypePage(
            records=records,
            known=page.known,
            complete=page.complete,
            why_incomplete=page.why_incomplete,
            next_after=page.next_after,
        )

    # --------------------------------------------------------------------- 7 to 9
    def _need_proposals(self) -> None:
        if not self.capabilities().stores_proposals:
            raise NotSupported(self.capabilities().reason("stores_proposals"))

    def put_proposal(self, rec: ProposalRecord, *, expect_absent: bool = False):
        self._need_proposals()
        return self.inner.put_proposal(rec, expect_absent=expect_absent)

    def get_proposal(self, proposal_id: str):
        self._need_proposals()
        return self.inner.get_proposal(proposal_id)

    def find_proposals(self, q: ProposalQuery) -> ProposalPage:
        self._need_proposals()
        return self.inner.find_proposals(q)

    # ------------------------------------------------------------------ 10 and 11
    def put_consumer(self, rec: ConsumerRecord) -> ConsumerRecord:
        if self._read_only_consumers:
            raise NotSupported(
                "this consumer source is a checked-in config file and cannot be written"
            )
        return self.inner.put_consumer(rec)

    def find_consumers(self, namespace: str, *, gate=None, consumer_id=None):
        return self.inner.find_consumers(namespace, gate=gate, consumer_id=consumer_id)

    # ----------------------------------------------------------------- 12 and 13
    def bump_usage(self, namespace, kind, name, *, at, by) -> None:
        if not self.capabilities().counts_usage:
            return None  # explicitly allowed to be a no-op
        return self.inner.bump_usage(namespace, kind, name, at=at, by=by)

    def get_usage(self, namespace: str, kind: str, name: str) -> UsageRecord | None:
        caps = self.capabilities()
        row = self.inner.get_usage(namespace, kind, name)
        if row is None:
            return None
        if not caps.counts_usage:
            # count=None means "we did not look", which is a different fact from
            # get_usage returning None ("nothing has happened").
            return UsageRecord(
                namespace=row.namespace,
                kind=row.kind,
                name=row.name,
                count=None,
                first_seen=None,
                last_seen=None,
            )
        if not caps.timestamps_usage:
            return UsageRecord(
                namespace=row.namespace,
                kind=row.kind,
                name=row.name,
                count=row.count,
                first_seen=None,
                last_seen=None,
            )
        return row

    # ----------------------------------------------------------------- 14 and 15
    def append_event(self, rec: EventRecord) -> None:
        if not self.capabilities().stores_events:
            raise NotSupported(self.capabilities().reason("stores_events"))
        return self.inner.append_event(rec)

    def read_events(self, namespace: str, *, kind=None, name=None, proposal_id=None):
        if not self.capabilities().stores_events:
            raise NotSupported(self.capabilities().reason("stores_events"))
        return self.inner.read_events(namespace, kind=kind, name=name, proposal_id=proposal_id)


class _DegradedWithAttributes(_DegradedBase):
    """The same double, plus the optional ``AttributeStore`` extension."""

    def put_attr_schema(self, rec):
        return self.inner.put_attr_schema(rec)

    def get_attr_schema(self, namespace: str, kind: str, *, version: int | None = None):
        return self.inner.get_attr_schema(namespace, kind, version=version)

    def observe_attributes(
        self, namespace: str, kind: str, attributes: dict, *, at: datetime, schema_version
    ) -> None:
        return self.inner.observe_attributes(
            namespace, kind, attributes, at=at, schema_version=schema_version
        )

    def read_attr_observed(self, namespace: str, *, kind: str | None = None):
        return self.inner.read_attr_observed(namespace, kind=kind)


def DegradedAdapter(inner, **kwargs):
    """Wrap ``inner`` and take capabilities away from it.

    A **factory**, not a class, and that is the point: the optional ``AttributeStore``
    extension is a *protocol*, not a ``Capabilities`` flag, so a wrapper either has the
    four methods or it does not -- it cannot declare them absent. Until row 3c this was
    one class that always defined them, so **wrapping a backend that declined the
    extension silently gave it back**, and the tool built to construct degraded backends
    could not construct that one. The class is chosen from what ``inner`` actually is.
    """
    from ..adapter import AttributeStore

    cls = _DegradedWithAttributes if isinstance(inner, AttributeStore) else _DegradedBase
    return cls(inner, **kwargs)


class WithoutAttributeStore:
    """A conformant adapter that declines the optional ``AttributeStore`` extension.

    PACKAGE.md 5.5 and ``2A-RUN.md`` deviation D-2 both say a backend that does not
    implement `AttributeStore` *"is still fully conformant"* and that
    ``attribute_census`` then reports ``complete=False`` with a `why`. **Until row 3c
    that was untrue and untestable at once**: four C15 tests called
    ``register_attribute_schema`` with no guard, which raises ``NotSupported`` on such a
    backend -- and `DegradedAdapter` forwarded the four extension methods
    unconditionally, so the tool built to construct "a backend declines an optional
    capability" could not construct **the one optional capability that is a protocol
    rather than a `Capabilities` flag**.

    ``__getattr__`` rather than ``__getattribute__``: the four names are simply absent
    from this class, so ``hasattr`` is False and the ``runtime_checkable`` Protocol's
    ``isinstance`` check answers correctly.
    """

    def __init__(self, inner):
        object.__setattr__(self, "inner", inner)

    def __getattr__(self, name):
        if name in _ATTRIBUTE_STORE_METHODS:
            raise AttributeError(
                f"{name} -- this backend declines the optional AttributeStore extension"
            )
        return getattr(self.inner, name)

    def __setattr__(self, name, value):
        # A write goes to the wrapped adapter, so this proxy behaves like the backend it
        # stands in for -- `C0-05` monkeypatches `_migration_sql` on the adapter it is
        # handed, and a proxy that kept the attribute for itself would silently make the
        # test pass against the untouched inner migrations.
        setattr(self.inner, name, value)
