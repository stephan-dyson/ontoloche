# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/contract/doubles.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

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
import dataclasses
from datetime import datetime
from typing import Any
from open_ontology.aio.adapter import (
    CAPABILITY_FLAGS,
    Capabilities,
    ConsumerRecord,
    EdgePage,
    EdgeQuery,
    EdgeRecord,
    EventRecord,
    ProposalPage,
    ProposalQuery,
    ProposalRecord,
    TypePage,
    TypeQuery,
    TypeRecord,
    UsageRecord,
)
from open_ontology.errors import NotSupported


__all__ = ["AsyncDegradedAdapter", "READ_ONLY_CONSUMERS"]

READ_ONLY_CONSUMERS = "read_only_consumers"

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
        page_cap: int | None = None,
        page_cursor: bool = False,
        transaction_scope: str | None = None,
        edge_transaction_scope: str | None = None,
        edge_store_shares_connection: bool | None = None,
        read_only_consumers: bool = False,
        attribute_projections: frozenset[str] | tuple[str, ...] | None = None,
        edge_attribute_projections: frozenset[str] | tuple[str, ...] | None = None,
        edge_page_cap: int | None = None,
        drops_edge_limit: bool = False,
        stale_edge_cursor: bool = False,
        **flags: bool,
    ):
        unknown = set(flags) - set(CAPABILITY_FLAGS)
        if unknown:
            raise ValueError(f"not capability flags: {sorted(unknown)}")
        self.inner = inner
        self._flags = flags
        self._pages_countable = pages_countable
        #: PACKAGE.md 3.3's other honest page: a backend that caps an unlimited query
        #: and SAYS SO (``complete=False`` plus a ``why``). Not a capability flag --
        #: nothing is declined, the answer is simply partial. Added by row 3e's first
        #: adversarial round, which found `resolve_type` ignoring the flag entirely and
        #: reporting `complete=True` over a page the backend had truncated.
        self._page_cap = page_cap
        #: With ``page_cursor``, the cap is an honest PAGE -- partial, with a cursor to
        #: the rest -- rather than a hard truncation. The suite needs both shapes: one
        #: proves a caller pages to exhaustion, the other proves it says so when it
        #: cannot. Row 3e, third adversarial round.
        self._page_cursor = page_cursor
        #: Ruling R5's declaration, forced rather than inherited. Not a capability --
        #: nothing is declined -- but a wrapper that can only ever carry ``"owned"``
        #: through cannot exercise the durability warning that every WRITE result is
        #: supposed to gain over a borrowed connection, and row 3e's second adversarial
        #: round found `reinstate` unchecked for it: a mutation dropping ``_written``
        #: from the fourteenth call ran the whole suite green.
        self._transaction_scope = transaction_scope
        #: EDGES.md 6.2's own declaration, carried separately so a double can be
        #: built with the two scopes DISAGREEING on one connection -- the shape 6.2
        #: calls non-conformant, which nothing could construct while the wrapper
        #: only ever copied one scope through.
        self._edge_transaction_scope = edge_transaction_scope
        self._edge_store_shares_connection = edge_store_shares_connection
        #: EDGES.md 6.3 -- U3's shape, for edge payloads.
        self._edge_attribute_projections = (
            None
            if edge_attribute_projections is None
            else frozenset(edge_attribute_projections)
        )
        #: The three BROKEN-edge-backend shapes, in the style of C0-10/C0-11: a
        #: store that silently drops `limit`, one that hands back a cursor pointing
        #: at rows it has already returned, and one that pages so small the registry
        #: must loop to assemble a level. They exist so the suite can answer *can a
        #: broken edge backend PASS?* -- the question that found C0-10 in the first
        #: place, asked of the surface this row adds.
        self._edge_page_cap = edge_page_cap
        self._drops_edge_limit = drops_edge_limit
        self._stale_edge_cursor = stale_edge_cursor
        self._read_only_consumers = read_only_consumers
        # U3: not a flag -- a declared set of keys this backend owns as typed columns.
        self._attribute_projections = (
            None if attribute_projections is None else frozenset(attribute_projections)
        )
        self._why = dict(why or {})
        for flag, value in flags.items():
            if not value:
                self._why.setdefault(flag, f"this backend does not support {flag}")

    # ------------------------------------------------------------------- 1 and 2
    async def capabilities(self) -> Capabilities:
        base = await self.inner.capabilities()
        values = {flag: getattr(base, flag) for flag in CAPABILITY_FLAGS}
        values.update(self._flags)
        # ``transaction_scope`` is carried through, never re-decided: this wrapper takes
        # capabilities AWAY from a backend and who owns the commit is not one of them.
        # Dropping it here would have made a wrapped borrowed adapter claim to own a
        # connection it does not (ruling R5).
        return Capabilities(
            **values,
            why={**base.why, **self._why},
            transaction_scope=self._transaction_scope or base.transaction_scope,
            attribute_projections=(
                base.attribute_projections
                if self._attribute_projections is None
                else self._attribute_projections
            ),
            # Defaults to whatever the TYPE scope was forced to, because EDGES.md
            # 6.2 binds them on one connection -- a double that forced
            # `transaction_scope` and left the edge scope at `owned` would be
            # non-conformant by construction, and every existing caller of this
            # wrapper forces exactly one of the two.
            edge_transaction_scope=(
                self._edge_transaction_scope
                or self._transaction_scope
                or base.edge_transaction_scope
            ),
            edge_attribute_projections=(
                base.edge_attribute_projections
                if self._edge_attribute_projections is None
                else self._edge_attribute_projections
            ),
            edge_store_shares_connection=(
                base.edge_store_shares_connection
                if self._edge_store_shares_connection is None
                else self._edge_store_shares_connection
            ),
        )

    async def migrate(self) -> int:
        return await self.inner.migrate()

    def transaction(self):
        return self.inner.transaction()

    # ------------------------------------------------------------------- 4 and 5
    async def _degrade_type(self, rec: TypeRecord | None) -> TypeRecord | None:
        if rec is None:
            return None
        caps = await self.capabilities()
        changes: dict[str, Any] = {}
        if not caps.stores_attributes:
            # U3: a projected key lives in its own typed column and survives; everything
            # else comes back ABSENT rather than wrong.
            changes["attributes"] = caps.surviving_attributes(rec.attributes or {})
        if not caps.stores_aliases:
            changes["aliases"] = ()
        if not caps.indexes_membership:
            changes["predicates"] = ()
        if not changes:
            return rec
        return TypeRecord(**{**rec.__dict__, **changes})

    async def put_type(self, rec: TypeRecord, *, expect_absent: bool = False) -> TypeRecord:
        return await self._degrade_type(await self.inner.put_type(rec, expect_absent=expect_absent))

    async def get_type(self, namespace: str, name: str, *, kind: str | None = None):
        return await self._degrade_type(await self.inner.get_type(namespace, name, kind=kind))

    # ------------------------------------------------------------------------- 6
    async def find_types(self, q: TypeQuery) -> TypePage:
        caps = await self.capabilities()
        if q.predicate is not None and not caps.indexes_membership:
            # Never known=0 -- that reads as "nothing is commentable".
            return TypePage(
                records=(),
                known=None,
                complete=False,
                why_incomplete=caps.reason("indexes_membership"),
            )
        # With ``page_cursor`` the cursor is this double's own, not the inner
        # backend's, so the inner query is asked without it and the window is taken
        # here.
        inner_query = dataclasses.replace(q, after=None) if self._page_cursor else q
        page = await self.inner.find_types(inner_query)
        records = tuple([await self._degrade_type(r) for r in page.records])
        if not self._pages_countable:
            return TypePage(
                records=records,
                known=None,
                complete=False,
                why_incomplete="this backend cannot count a result set",
            )
        if self._page_cap is not None and len(records) > self._page_cap:
            if self._page_cursor:
                # **The honest paging shape**: partial, and here is how to get the rest.
                # PACKAGE.md 3.3 permits it and UC3's scale produces it, and the suite
                # had no double for it -- so `_active_page`'s and
                # `_name_level_schemas`' "read to exhaustion" loops were asserted by
                # nothing, and deleting them ran the whole suite green. Row 3e, third
                # adversarial round.
                start = 0 if q.after is None else int(q.after)
                window = records[start : start + self._page_cap]
                nxt = start + self._page_cap
                return TypePage(
                    records=window,
                    known=len(window),
                    complete=nxt >= len(records),
                    why_incomplete=(
                        None
                        if nxt >= len(records)
                        else f"this backend pages at {self._page_cap} rows"
                    ),
                    next_after=None if nxt >= len(records) else str(nxt),
                )
            return TypePage(
                records=records[: self._page_cap],
                known=self._page_cap,
                complete=False,
                why_incomplete=(
                    f"this backend caps an unlimited query at {self._page_cap} rows"
                ),
                # No cursor: this double is the shape where the rest CANNOT be read,
                # which is the residual case after a caller pages to exhaustion.
                next_after=None,
            )
        return TypePage(
            records=records,
            known=page.known,
            complete=page.complete,
            why_incomplete=page.why_incomplete,
            next_after=page.next_after,
        )

    # --------------------------------------------------------------------- 7 to 9
    async def _need_proposals(self) -> None:
        if not (await self.capabilities()).stores_proposals:
            raise NotSupported((await self.capabilities()).reason("stores_proposals"))

    async def put_proposal(self, rec: ProposalRecord, *, expect_absent: bool = False):
        await self._need_proposals()
        return await self.inner.put_proposal(rec, expect_absent=expect_absent)

    async def get_proposal(self, proposal_id: str):
        await self._need_proposals()
        return await self.inner.get_proposal(proposal_id)

    async def find_proposals(self, q: ProposalQuery) -> ProposalPage:
        await self._need_proposals()
        return await self.inner.find_proposals(q)

    # ------------------------------------------------------------------ 10 and 11
    async def put_consumer(self, rec: ConsumerRecord) -> ConsumerRecord:
        if self._read_only_consumers:
            raise NotSupported(
                "this consumer source is a checked-in config file and cannot be written"
            )
        return await self.inner.put_consumer(rec)

    async def find_consumers(self, namespace: str, *, gate=None, consumer_id=None):
        return await self.inner.find_consumers(namespace, gate=gate, consumer_id=consumer_id)

    # ----------------------------------------------------------------- 12 and 13
    async def bump_usage(self, namespace, kind, name, *, at, by) -> None:
        if not (await self.capabilities()).counts_usage:
            return None  # explicitly allowed to be a no-op
        return await self.inner.bump_usage(namespace, kind, name, at=at, by=by)

    async def get_usage(self, namespace: str, kind: str, name: str) -> UsageRecord | None:
        caps = await self.capabilities()
        row = await self.inner.get_usage(namespace, kind, name)
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
    async def append_event(self, rec: EventRecord) -> None:
        if not (await self.capabilities()).stores_events:
            raise NotSupported((await self.capabilities()).reason("stores_events"))
        return await self.inner.append_event(rec)

    async def read_events(
        self, namespace: str, *, kind=None, name=None, proposal_id=None, edge_id=None
    ):
        if not (await self.capabilities()).stores_events:
            raise NotSupported((await self.capabilities()).reason("stores_events"))
        return await self.inner.read_events(
            namespace, kind=kind, name=name, proposal_id=proposal_id, edge_id=edge_id
        )

    # ------------------------------------------------------------------ 16 to 18
    async def _need_edges(self) -> None:
        if not (await self.capabilities()).stores_edges:
            raise NotSupported((await self.capabilities()).reason("stores_edges"))

    async def _degrade_edge(self, rec: EdgeRecord | None) -> EdgeRecord | None:
        if rec is None:
            return None
        caps = await self.capabilities()
        if caps.stores_edge_attributes:
            return rec
        # EDGES.md 6: an edge payload comes back reduced to `edge_attribute_projections`
        # and no warning value is minted for the loss -- PACKAGE.md 3.4 primitive 4's
        # mechanism is that the RETURNED RECORD is the signal, and the type side has no
        # warning for it either. Reporting one fact two ways is what 6 declined.
        return dataclasses.replace(
            rec, attributes=caps.surviving_edge_attributes(rec.attributes or {})
        )

    async def put_edge(self, rec: EdgeRecord, *, expect_absent: bool = False) -> EdgeRecord:
        await self._need_edges()
        return await self._degrade_edge(
            await self.inner.put_edge(await self._degrade_edge(rec), expect_absent=expect_absent)
        )

    async def get_edge(self, edge_id: str) -> EdgeRecord | None:
        await self._need_edges()
        return await self._degrade_edge(await self.inner.get_edge(edge_id))

    async def find_edges(self, q: EdgeQuery) -> EdgePage:
        await self._need_edges()
        caps = await self.capabilities()
        inner = q
        if not caps.indexes_edges_by_family and q.families is not None:
            # EDGES.md 7.1's DELIBERATE deviation from `find_types`' rule: this query is
            # already bounded by `incident_to`, so the store returns the frontier's
            # edges UNFILTERED and COMPLETE for what it was asked, and the registry
            # narrows above. `find_types`' answer -- an empty page with a why -- would
            # be wrong here, because the backend genuinely can answer the wider
            # question.
            inner = dataclasses.replace(inner, families=None)
        if self._drops_edge_limit:
            # The broken backend C0-10 found on the type side, transposed: `limit` and
            # `after` silently ignored, which is a duplicate-forever loop in any keyset
            # consumer.
            inner = dataclasses.replace(inner, limit=None, after=None)
        elif self._edge_page_cap is not None:
            inner = dataclasses.replace(
                inner, limit=min(self._edge_page_cap, q.limit or self._edge_page_cap)
            )
        page = await self.inner.find_edges(inner)
        records = tuple([await self._degrade_edge(r) for r in page.records])
        next_after = page.next_after
        if self._stale_edge_cursor and next_after is not None and q.after is not None:
            # A backend whose cursor points at rows it has ALREADY returned. Honest
            # pagination is not something a caller may infer from `next_after` being
            # non-None, and a loop that trusts it never terminates.
            next_after = q.after
        if not self._pages_countable:
            return EdgePage(
                records=records,
                known=None,
                complete=False,
                why_incomplete="this backend cannot count a result set",
                next_after=next_after,
            )
        return EdgePage(
            records=records,
            known=page.known,
            complete=page.complete,
            why_incomplete=page.why_incomplete,
            next_after=next_after,
        )

class _DegradedWithAttributes(_DegradedBase):
    """The same double, plus the optional ``AsyncAttributeStore`` extension."""

    async def put_attr_schema(self, rec):
        return await self.inner.put_attr_schema(rec)

    async def get_attr_schema(
        self,
        namespace: str,
        kind: str,
        *,
        name: str | None = None,
        version: int | None = None,
    ):
        return await self.inner.get_attr_schema(namespace, kind, name=name, version=version)

    async def observe_attributes(
        self, namespace: str, kind: str, attributes: dict, *, at: datetime, schema_version
    ) -> None:
        return await self.inner.observe_attributes(
            namespace, kind, attributes, at=at, schema_version=schema_version
        )

    async def read_attr_observed(self, namespace: str, *, kind: str | None = None):
        return await self.inner.read_attr_observed(namespace, kind=kind)

def AsyncDegradedAdapter(inner, **kwargs):
    """Wrap ``inner`` and take capabilities away from it.

    A **factory**, not a class, and that is the point: the optional ``AsyncAttributeStore``
    extension is a *protocol*, not a ``Capabilities`` flag, so a wrapper either has the
    four methods or it does not -- it cannot declare them absent. Until row 3c this was
    one class that always defined them, so **wrapping a backend that declined the
    extension silently gave it back**, and the tool built to construct degraded backends
    could not construct that one. The class is chosen from what ``inner`` actually is.
    """
    from open_ontology.aio.adapter import AsyncAttributeStore

    cls = _DegradedWithAttributes if isinstance(inner, AsyncAttributeStore) else _DegradedBase
    return cls(inner, **kwargs)

class WithoutAttributeStore:
    """A conformant adapter that declines the optional ``AsyncAttributeStore`` extension.

    PACKAGE.md 5.5 and ``2A-RUN.md`` deviation D-2 both say a backend that does not
    implement `AsyncAttributeStore` *"is still fully conformant"* and that
    ``attribute_census`` then reports ``complete=False`` with a `why`. **Until row 3c
    that was untrue and untestable at once**: four C15 tests called
    ``register_attribute_schema`` with no guard, which raises ``NotSupported`` on such a
    backend -- and `AsyncDegradedAdapter` forwarded the four extension methods
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
                f"{name} -- this backend declines the optional AsyncAttributeStore extension"
            )
        return getattr(self.inner, name)

    def __setattr__(self, name, value):
        # A write goes to the wrapped adapter, so this proxy behaves like the backend it
        # stands in for -- `C0-05` monkeypatches `_migration_sql` on the adapter it is
        # handed, and a proxy that kept the attribute for itself would silently make the
        # test pass against the untouched inner migrations.
        setattr(self.inner, name, value)
