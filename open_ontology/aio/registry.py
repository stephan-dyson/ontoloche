# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit open_ontology/registry.py and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------

"""``AsyncRegistry`` -- the facade. The INTERFACE.md 5 calls, as methods.

Everything that refuses, warns, scores or decides lives here. The adapter below stores
records and knows nothing of any of it, which is what lets two unlike backends both be
correct.

One facade object rather than module-level functions, because every call needs an
adapter, a policy, a clock and a resolver, and the contract suite must hold a SQLite
adapter and a Postgres adapter **in one process at once** to parametrise over both. A
process-global registry makes that impossible.
"""

from __future__ import annotations
import logging
import re
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any, Iterable, Sequence
from open_ontology._clock import Clock, SystemClock
from open_ontology._resolve import DeterministicResolver, Resolver
from open_ontology.aio.adapter import (
    AttrObservedRecord,
    AttrSchemaRecord,
    AsyncAttributeStore,
    Capabilities,
    ConsumerRecord,
    EdgeQuery,
    EdgeRecord,
    EventRecord,
    ProposalQuery,
    ProposalRecord,
    AsyncStorageAdapter,
    TypeQuery,
    TypeRecord,
)
from open_ontology.attributes import (
    ADDITIONAL,
    MODES,
    AttributeCensus,
    AttributeSchema,
    CensusEntry,
    FieldSpec,
    strictest,
    validate_attributes,
)
from open_ontology.edges import (
    DEFAULT_MAX_EDGES,
    DEPTH_CAP,
    DIRECTIONS,
    EDGE_LEVELS,
    EDGE_PAYLOAD_KIND,
    UNCHANGED,
    EQUIVALENT_TO,
    EQUIVALENT_TO_ATTRIBUTES,
    EQUIVALENT_TO_DEFINITION,
    Edge,
    EdgeFamily,
    EdgeProvenance,
    InstanceRef,
    NeighborEdge,
    NeighborReport,
    NodeRef,
    TypeRef,
    family_declaration_problem,
    level_of,
    node_key,
    node_ref,
    type_of,
)
from open_ontology.errors import NotSupported, UnknownType
from open_ontology.policy import NamespacePolicy
from open_ontology.types import (
    Alternative,
    Citation,
    Consumer,
    ConsumerReport,
    Evidence,
    MergeResult,
    PredicateEntry,
    PredicateListing,
    Proposal,
    Provenance,
    ProvenanceEvent,
    Refusal,
    Rejection,
    Resolution,
    ResolveContext,
    TypeEntry,
    TypeListing,
    UsageReport,
)

__all__ = ["AsyncRegistry"]

# Pure module-level helpers with no I/O in them, borrowed not copied.
from open_ontology.registry import (
    CONSUMERS_WHY_INCOMPLETE,
    NAME_RE,
    _DefinitionProbe,
    _EDGE_HISTORY_WHY,
    _EDGE_PAGE_SIZE,
    _NEAR_MISS_CAP,
    _asserts_domain_semantic,
    _created_by,
    _edge_from_record,
    _edge_to_record,
    _evidence_from_dict,
    _evidence_to_dict,
    _has_external_doc,
    _iso,
    _prov_from_dict,
    _prov_to_dict,
    _ts,
    _uuid,
)


class AsyncRegistry:
    """The fourteen calls of INTERFACE.md 5, plus three package-local helpers.

    The counting note from PACKAGE.md 2.2 stands: INTERFACE.md says *twelve calls* and
    enumerating 5.1-5.11 yields thirteen, and row 3e's `reinstate` (5.9b, ruling R11)
    makes fourteen. Nothing here depends on which
    number is right.
    """

    async def _open(
        self,
        adapter: AsyncStorageAdapter,
        *,
        resolver: Resolver | None = None,
        clock: Clock | None = None,
        policy: NamespacePolicy | None = None,
        policies: dict[str, NamespacePolicy] | None = None,
        migrate: bool = True,
        max_edges: int | None = DEFAULT_MAX_EDGES,
        seed_equivalent_to: bool = True,
    ):
        self.adapter = adapter
        self.resolver = resolver or DeterministicResolver()
        self.clock = clock or SystemClock()
        self._default_policy = policy or NamespacePolicy()
        self._policies = dict(policies or {})
        self.caps: Capabilities = await adapter.capabilities()
        # Ruling R5 point 2: over a borrowed connection a clean return is atomic and
        # NOT YET DURABLE, and "a why-style sentence surfaces in any result that would
        # otherwise imply durability". PACKAGE.md 3 item 3 says the same. [Observed,
        # row 3d second adversarial round] neither was implemented: `transaction_scope`
        # appeared nowhere in this file, so `approve()` over a host-owned session
        # returned TypeEntry(status="active") with nothing on it saying the host had
        # not committed -- the sentence existed only in a separate capabilities() call
        # the caller had to know to make. That is the failure Rule U is named after,
        # in the one seam beacon builds against.
        self._durability_warning: str | None = (
            f"not_durable_until_host_commits:{self.caps.reason('transaction_scope')}"
            if self.caps.transaction_scope == "savepoint"
            else None
        )
        #: EDGES.md 4.2's assembly bound, and it is a DEPLOYMENT parameter rather
        #: than a `neighbors` argument: 4.2 calls it a circuit breaker, and a
        #: circuit breaker a caller can raise per call is not one. It is ON by
        #: default -- round 3 of the spec row's loop found it opt-in, which leaves
        #: the DEFAULT behaviour as exactly the unbounded materialisation R13 exists
        #: to prevent. `max_edges=None` disables it, and a deployment that does so
        #: has chosen the unbounded fetch rather than inherited it.
        self.max_edges = max_edges
        if migrate:
            # PACKAGE.md 9.2 -- a store from the future raises rather than being read
            # under old assumptions. The failure mode is a loud refusal at startup.
            await adapter.migrate()
        # Gated on `migrate` and NOT on `stores_edges`, and the second half is a
        # decision the suite forced. Gating on the edge store made the three reference
        # legs disagree about what is in a fresh vocabulary -- `sqlite_minimal` declares
        # `stores_edges=False`, so it alone had no `equivalent_to` and five census ids
        # failed on that leg alone. The rule that falls out is the right one:
        # **`equivalent_to` is a row of the VOCABULARY, and whether this deployment
        # happens to have an edge store is not a fact about the vocabulary.** A
        # type-only backend registers the word honestly and `add_edge` on it refuses
        # `edge_store_absent` with that backend's own sentence, which is Rule U doing
        # exactly its job. Gating on `migrate` is the other half: a AsyncRegistry that
        # declines to bring the store up to date declines to write to it at all, so a
        # borrowed connection gets no surprise write at construction time.
        if seed_equivalent_to and migrate:
            await self._seed_equivalent_to()

    # ------------------------------------------------------------------- internals
    def policy(self, namespace: str) -> NamespacePolicy:
        return self._policies.get(namespace, self._default_policy)

    def _now(self) -> datetime:
        return self.clock.now()

    async def _require(self, namespace: str, name: str, *, kind: str | None = None) -> TypeRecord:
        rec = await self.adapter.get_type(namespace, name, kind=kind)
        if rec is None:
            raise UnknownType(name, namespace=namespace, kind=kind)
        return rec

    async def _events(self, namespace: str, kind: str, name: str) -> tuple[tuple[ProvenanceEvent, ...], str | None]:
        if not self.caps.stores_events:
            return (), self.caps.reason("stores_events")
        rows = await self.adapter.read_events(namespace, kind=kind, name=name)
        return (
            tuple(
                ProvenanceEvent(at=r.at, actor=r.actor, event=r.event, detail=dict(r.detail or {}))
                for r in rows
            ),
            None,
        )

    async def _append_event(
        self,
        namespace: str,
        event: str,
        actor: str,
        *,
        kind: str | None = None,
        name: str | None = None,
        proposal_id: str | None = None,
        edge_id: str | None = None,
        detail: dict | None = None,
    ) -> None:
        if not self.caps.stores_events:
            return
        await self.adapter.append_event(
            EventRecord(
                event_id=_uuid(),
                namespace=namespace,
                at=self._now(),
                actor=actor,
                event=event,
                kind=kind,
                name=name,
                proposal_id=proposal_id,
                edge_id=edge_id,
                detail=dict(detail or {}),
            )
        )

    def _written(self, result):
        """Stamp the durability sentence on the result of a WRITE. Reads never carry it.

        **Reproduced regression, row 3d third adversarial round.** The first version
        attached this inside ``_entry`` and ``_proposal`` -- which also build the results
        of ``resolve_type`` (the call PACKAGE.md 6.2 calls *"the call that must not
        write"*) and ``list_types``. So a savepoint-scoped registry stamped
        ``not_durable_until_host_commits`` on **every read, forever**, including reads of
        rows the host had committed minutes earlier: the signal degraded into permanent
        noise on the exact seam it exists to protect, and it contradicted INTERFACE.md
        5.4's own carrier column, which says *every write result*.

        A write's result is genuinely not durable at the moment it is returned. A read's
        result is a statement about what the store holds, and this registry has no way to
        know whether the host has since committed -- so it says nothing, which is Rule U
        rather than a guess in either direction.
        """
        if not self._durability_warning or result is None:
            return result
        existing = getattr(result, "warnings", None)
        if existing is None:
            return result
        if self._durability_warning in existing:
            return result
        return replace(result, warnings=(*existing, self._durability_warning))

    def _write_warnings(self) -> tuple[str, ...]:
        """The warnings a directly-constructed WRITE result carries. Empty on an owned store.

        Row 3d, third adversarial round: the first pass attached the durability sentence
        in ``_entry`` and ``_proposal`` only, and ``register_consumer`` and ``reject``
        build their results directly -- so a consumer registration or a rejection made
        over a borrowed connection came back looking exactly as done as a durable write
        and then vanished on host rollback with no trace. A consumer registration that
        silently does not stick is mechanism **C** itself.
        """
        return (self._durability_warning,) if self._durability_warning else ()

    # ------------------------------------------------------------------ projections
    async def _consumer_report(
        self,
        rec: TypeRecord,
        consumers: Sequence[ConsumerRecord] | None = None,
        *,
        include_would_drop: bool = True,
    ) -> ConsumerReport:
        rows = (
            list(consumers)
            if consumers is not None
            else await self.adapter.find_consumers(rec.namespace)
        )
        # "Which consumers gate on this?" has TWO answers, and v0 only computed one.
        # For an `entity`, a consumer gates on it when the consumer's gate predicate
        # includes it -- `consumer.gate in rec.predicates`. **For a `predicate`, a
        # consumer gates on it when the gate IS it.** A predicate is essentially never a
        # member of itself, so the membership test alone can never match a consumer that
        # names this very predicate, and [Observed] `consumers("commentable")` filed the
        # consumer of `commentable` under `would_drop` -- *the exact opposite of the
        # truth* -- while `retire("commentable")` sailed through with no refusal at all.
        # On a fully capable backend, with nothing unknowable.
        #
        # That is mechanism C in 2.3's "single most load-bearing idea in this document":
        # a predicate is a first-class TypeEntry with a lifecycle like anything else, and
        # 5.9 guards retirement with `consumers` and carves out no exception for it.
        # `predicates()` had the right query all along (`c.gate == rec.name`); this call
        # did not. Row 3c, after an adversarial review round drove it.
        member_of = set(rec.predicates)
        gates_directly = rec.kind == "predicate"
        gates_on: list[Consumer] = []
        would_drop: list[Consumer] = []
        would_error: list[Consumer] = []
        for row in rows:
            consumer = Consumer(
                id=row.consumer_id,
                gate=row.gate,
                on_unknown=row.on_unknown,
                owner=row.owner,
                registered_at=row.registered_at,
                locator=row.locator,
            )
            if consumer.gate in member_of or (gates_directly and consumer.gate == rec.name):
                gates_on.append(consumer)
            elif consumer.on_unknown == "drop":
                would_drop.append(consumer)
            elif consumer.on_unknown == "error":
                would_error.append(consumer)
            # passthrough appears in neither: it neither sees the type nor breaks on it
        if not include_would_drop:
            would_drop = []
        return ConsumerReport(
            type=rec.name,
            gates_on=tuple(gates_on),
            would_drop=tuple(would_drop),
            would_error=tuple(would_error),
            known=len(gates_on) + len(would_drop) + len(would_error),
            complete=False,
            why_incomplete=CONSUMERS_WHY_INCOMPLETE,
            warnings=await self._gate_warnings(rec.namespace, rows)
            + await self._edge_gate_warnings(rec, rows),
        )

    async def _gate_warnings(
        self, namespace: str, rows: Sequence[ConsumerRecord]
    ) -> tuple[str, ...]:
        """``gate_unregistered:<gate>`` per gate that names no registered predicate.

        **Ruling R8 (row 3d), and it is a Rule U problem wearing a product hat.**
        PACKAGE.md 3.4 primitive 10 says a consumer's ``gate`` *"may name a predicate
        that does not exist; the adapter does not check"*, and it is right that it does
        not -- a consumer gating on a word nobody registered is mechanism **C** itself,
        and refusing the registration would hide it (`C11-02`).

        But the *report* then says ``would_drop: [aura_render]`` about that consumer,
        and a reader takes that as a fact about a live gate: *this consumer gates on
        `commentable` and this type is not in it.* The truth is weaker and more
        alarming -- **there is no `commentable`**, so the extent is not "excludes this
        type", it is undefined, and every type in the namespace would drop. One word
        in the report, two very different situations.

        So the report carries a warning naming the gate. Neither of ruling R8's two
        rejected options is taken: ``gate_values`` (Phase 3 -- it makes the registry
        know what a *value* is, which INTERFACE.md 2.1 refuses on purpose) and dropping
        the consumer from ``would_drop`` (which would delete mechanism-C visibility,
        the thing `C11-02` exists for).

        **The uncertainty rule applies to the warning too.** If the backend cannot
        answer the lookup completely, no warning is emitted: "this gate is unregistered"
        is a positive claim, and a page that came back incomplete does not support one.
        """
        gates = {row.gate for row in rows if row.gate}
        if not gates:
            return ()
        page = await self.adapter.find_types(
            TypeQuery(
                namespace=namespace,
                kind="predicate",
                name_in=tuple(sorted(gates)),
                status=None,
                include_retired=True,
            )
        )
        if not page.complete:
            # Rule U: we did not look successfully, so we do not assert an absence.
            return ()
        # `include_retired=True` on purpose: a RETIRED predicate is still a registered
        # entry -- the tombstone is there, `resolve_type` reads it (C3-10), and calling
        # it unregistered would be a different and wrong claim.
        registered = {r.name for r in page.records}
        return tuple(f"gate_unregistered:{g}" for g in sorted(gates - registered))

    async def _edge_gate_warnings(
        self, rec: TypeRecord, rows: Sequence[ConsumerRecord]
    ) -> tuple[str, ...]:
        """``no_edge_gate_registered`` -- EDGES.md 8, by ruling R8's own reasoning.

        When ``consumers()`` is called on a ``kind="edge"`` entry and **no predicate's
        extent contains any edge family at all**, ``would_drop: []`` reads as *"nothing
        will drop this"* and the truth is *"nobody has told us what traverses edges"*.

        The case is not hypothetical. `deadline_cluster_service` -- live for every user
        since 2026-07-06 -- walks `work_links[blocks]` with the family name in its code,
        while `work_link_types` *"is extended by the AI classifier when it is confident
        none of the existing types fit"*. A classifier proposes `waiting_on`, it is
        auto-approved, edges start being written with it, and the one shipped producer
        that consumes edges keeps walking `blocks`. **Nothing errors.** That is finding
        0.1's Cause C with a classifier as the producer and a scheduled job as the
        consumer, on a live system.

        **Rule U applies to the warning itself**, exactly as it does to
        ``gate_unregistered`` (`C11-05`'s rule): the claim *"nobody has registered an
        edge gate"* is a positive one, and a lookup that came back incomplete does not
        support it. On a backend with ``indexes_membership=False`` every ``predicates``
        list is empty, so the question cannot be asked at all and nothing is said.
        """
        if rec.kind != "edge":
            return ()
        if not self.caps.indexes_membership:
            # Every membership list is empty here, so "no predicate's extent contains an
            # edge family" is indistinguishable from "we cannot see any extent". Silence
            # is the honest answer; the alternative is a warning that fires on every
            # family on a backend that simply cannot answer.
            return ()
        # The condition EDGES.md 8 states is about EXTENTS, not about consumers: *no
        # predicate's extent contains any edge family at all*. A registry with no
        # consumers registered satisfies it, and so does one with ten consumers none of
        # whose gates any family claims -- both are the same fact, which is that nothing
        # has been declared to traverse edges. Keying it on the consumer rows instead
        # would silence the warning in the emptiest case, which is the case it is for.
        page = await self.adapter.find_types(
            TypeQuery(namespace=rec.namespace, kind="edge", status=None, include_retired=True)
        )
        if not page.complete:
            return ()
        for family in page.records:
            if family.predicates:
                return ()
        return ("no_edge_gate_registered",)

    async def _usage_report(self, rec: TypeRecord) -> UsageReport:
        policy = self.policy(rec.namespace)
        window = policy.orphan_window
        row = await self.adapter.get_usage(rec.namespace, rec.kind, rec.name)

        if not self.caps.counts_usage:
            why = self.caps.reason("counts_usage")
            return UsageReport(
                type=rec.name,
                count=None,
                last_seen=None,
                first_seen=None,
                orphaned=None,
                window=window,
                why=why,
                complete=False,
            )

        if row is None:
            # Nothing has been recorded. Different from "we do not count", and the two
            # must not be collapsed (C7-05).
            count, first_seen, last_seen = 0, None, None
            why: str | None = "no use of this type has been recorded"
        else:
            count = row.count
            first_seen, last_seen = row.first_seen, row.last_seen
            why = None

        if not self.caps.timestamps_usage:
            first_seen = last_seen = None
            why = self.caps.reason("timestamps_usage")

        orphaned: bool | None
        if rec.status != "active":
            orphaned = False
        elif count == 0:
            orphaned = True
        elif last_seen is not None:
            orphaned = last_seen < self._now() - window
        else:
            # A bare counter cannot distinguish a type used once in April from one used
            # yesterday. False here would be a claim the data does not support.
            orphaned = None
            if why is None:
                why = "last_seen is unknown, so orphan status cannot be judged"

        return UsageReport(
            type=rec.name,
            count=count,
            last_seen=last_seen,
            first_seen=first_seen,
            orphaned=orphaned,
            window=window,
            why=why,
            complete=count is not None and (last_seen is not None or count == 0),
        )

    async def _entry(
        self,
        rec: TypeRecord,
        *,
        consumers: Sequence[ConsumerRecord] | None = None,
        extra_warnings: Sequence[str] = (),
    ) -> TypeEntry:
        history, history_why = await self._events(rec.namespace, rec.kind, rec.name)
        warnings = list(rec.warnings)
        for w in extra_warnings:
            if w not in warnings:
                warnings.append(w)
        return TypeEntry(
            name=rec.name,
            kind=rec.kind,
            namespace=rec.namespace,
            definition=rec.definition,
            created_by=rec.created_by,
            provenance=_prov_from_dict(rec.provenance or {}, history, history_why),
            status=rec.status,
            usage=await self._usage_report(rec),
            consumers=await self._consumer_report(rec, consumers),
            predicates=tuple(rec.predicates),
            attributes=dict(rec.attributes or {}),
            aliases=tuple(rec.aliases),
            warnings=tuple(warnings),
            attr_schema_version=rec.attr_schema_version,
        )

    def _proposal(self, rec: ProposalRecord) -> Proposal:
        return Proposal(
            id=rec.proposal_id,
            name=rec.name,
            kind=rec.kind,
            namespace=rec.namespace,
            definition=rec.definition,
            predicates=tuple(rec.predicates),
            attributes=dict(rec.attributes or {}),
            evidence=tuple(_evidence_from_dict(e) for e in (rec.evidence or [])),
            proposed_by=rec.proposed_by,
            proposed_at=rec.proposed_at,
            tier=rec.tier,
            status=rec.status,
            warnings=tuple(rec.warnings),
            near_matches=tuple((n[0], n[1]) for n in (rec.near_matches or [])),
            source_version=rec.source_version,
        )

    # ============================================================== 5.1 consumers
    async def consumers(
        self,
        type: str,
        *,
        namespace: str = "default",
        include_would_drop: bool = True,
    ) -> ConsumerReport:
        """Who gates on this type, and who would silently drop it.

        An unknown type raises rather than returning an empty report: an empty report
        reads as "nothing gates on this", which is the exact false reassurance this
        call exists to prevent.
        """
        rec = await self._require(namespace, type)
        return await self._consumer_report(rec, include_would_drop=include_would_drop)

    # ============================================================= 5.2 predicates
    async def predicates(
        self,
        *,
        of: str | None = None,
        namespace: str = "default",
        include_retired: bool = False,
    ) -> PredicateListing:
        """The named capability sets. A predicate is not a supertype: membership of
        ``commentable`` implies nothing about ``searchable``.

        Rule K (INTERFACE.md 3): this is a list result, so it carries ``known`` and
        ``complete``. ``include_retired=False`` is the default *and hides things*, and
        a backend that could not fully answer the page must not have that swallowed --
        an empty list reading as "this type satisfies no predicates" is 5.2's named
        failure one level up.
        """
        wanted: set[str] | None = None
        if of is not None:
            member = await self._require(namespace, of)
            wanted = set(member.predicates)

        page = await self.adapter.find_types(
            TypeQuery(namespace=namespace, kind="predicate", include_retired=include_retired)
        )
        consumer_rows = await self.adapter.find_consumers(namespace)
        out: list[PredicateEntry] = []
        for rec in page.records:
            if wanted is not None and rec.name not in wanted:
                continue
            extent, extent_size, why = await self._extent(namespace, rec.name, include_retired)
            history, history_why = await self._events(namespace, rec.kind, rec.name)
            out.append(
                PredicateEntry(
                    name=rec.name,
                    definition=rec.definition,
                    extent=extent,
                    extent_size=extent_size,
                    consumers=tuple(
                        Consumer(
                            id=c.consumer_id,
                            gate=c.gate,
                            on_unknown=c.on_unknown,
                            owner=c.owner,
                            registered_at=c.registered_at,
                            locator=c.locator,
                        )
                        for c in consumer_rows
                        if c.gate == rec.name
                    ),
                    status=rec.status,
                    provenance=_prov_from_dict(rec.provenance or {}, history, history_why),
                    why_extent_incomplete=why,
                )
            )

        applied = [
            label
            for label, used in (
                ("of", of is not None),
                ("include_retired=False", not include_retired),
            )
            if used
        ]
        why_incomplete: str | None = None
        if applied:
            why_incomplete = "filters suppressed rows: " + ", ".join(applied)
        elif not page.complete:
            why_incomplete = page.why_incomplete
        return PredicateListing(
            predicates=tuple(out),
            known=len(out) if page.known is not None else None,
            complete=bool(page.complete and not applied),
            why_incomplete=why_incomplete,
        )

    async def _extent(
        self, namespace: str, predicate: str, include_retired: bool
    ) -> tuple[tuple[str, ...], int | None, str | None]:
        if not self.caps.indexes_membership:
            # Never extent_size=0 -- that reads as "nothing is commentable", which is
            # INTERFACE.md 5.2's named failure.
            return (), None, self.caps.reason("indexes_membership")
        page = await self.adapter.find_types(
            TypeQuery(namespace=namespace, predicate=predicate, include_retired=include_retired)
        )
        if page.known is None or not page.complete:
            return (
                tuple(r.name for r in page.records),
                None,
                page.why_incomplete or self.caps.reason("indexes_membership"),
            )
        names = tuple(r.name for r in page.records)
        return names, len(names), None

    # =========================================================== 5.3 resolve_type
    async def resolve_type(
        self,
        candidate: str,
        context: ResolveContext,
        *,
        kind: str | None = None,
        namespace: str = "default",
        tier: str,
        min_confidence: float = 0.0,
        search_namespaces: Sequence[str] | None = None,
    ) -> Resolution:
        """existing / proposal / not_a_type / none. **Persists nothing.**

        ``tier`` is required, not defaulted (INTERFACE.md 2.7): omitting it is a
        TypeError, so an unattributed machine call cannot be made by accident.

        ``search_namespaces`` is ruling **R6**, row 3e. ``None`` -- the default -- is
        exactly the v0 behaviour and costs exactly what it used to: one namespace
        scored, nothing else read. Naming namespaces scores each of them too and lands
        their hits in ``alternatives`` as ``("<namespace>:<name>", score)``.

        **The outcome is still decided inside ``namespace`` alone.** A hit in another
        namespace never makes the outcome ``existing``: 2.6 makes scoping the answer to
        mechanism 4, and resolving *across* namespaces would be that answer deleting
        itself. What a hit does is tell the second publisher that the word is taken
        elsewhere -- which is the whole of UC3's W1.3, and mechanism **2** arriving
        through the answer to mechanism 4.
        """
        policy = self.policy(namespace)
        (
            cross_alts,
            searched,
            cross_complete,
            cross_why,
            cross_note,
        ) = await self._search_namespaces(
            candidate,
            context,
            kind=kind,
            namespace=namespace,
            tier=tier,
            search_namespaces=search_namespaces,
        )

        exact = await self.adapter.get_type(namespace, candidate, kind=kind)
        # A retired exact match is NOT an `existing` outcome -- 5.9 makes the name
        # permanently unusable -- but it is a fact the registry has in hand, and
        # discarding it here made `resolve_type` answer "nothing in the vocabulary fits
        # this" about a word it had just read the tombstone of. That is Rule U's
        # confident negative, in the call designed against mechanism 2. It is surfaced
        # the way 5.5 already surfaces a prior rejection: in `reason`, and in
        # `alternatives` with a `None` score because nothing scored it.
        # Row 3c, after an adversarial review round reproduced it.
        retired_note: str | None = None
        retired_alt: tuple[Alternative, ...] = ()
        if exact is not None and exact.status == "retired":
            # A retired name with a LIVE SUCCESSOR resolves to the successor, and the
            # registry says so itself. 5.10 promises "the old word still resolves" after
            # a merge, and [Observed] that promise was kept only by accident: the
            # shipped resolver happened to score the alias a merge writes at 1.0. The
            # same situation reached by `retire(successor=)` -- which writes no alias --
            # answered `proposal`, and a deployment supplying its own resolver (2.6's
            # production path) got `proposal` down both paths. Four different answers to
            # one fact. Row 3c, after an adversarial review round drove all four.
            successor = getattr(exact, "successor", None)
            if successor:
                live = await self.adapter.get_type(namespace, successor)
                if live is not None and live.status != "retired":
                    succession = (
                        f"{candidate!r} was retired with {successor!r} as its "
                        f"successor; the old word resolves to the successor and is "
                        f"itself not reusable (INTERFACE.md 5.9, 5.10)"
                    )
                    return Resolution(
                        outcome="existing",
                        reason="; ".join(
                            [succession] + ([cross_note] if cross_note else [])
                        ),
                        tier=tier,
                        scoped_to=namespace,
                        type=await self._entry(live),
                        confidence=1.0,
                        alternatives=((exact.name, None),) + cross_alts,
                        searched_namespaces=searched,
                        complete=cross_complete,
                        why_incomplete=cross_why,
                    )
            retired_alt = ((exact.name, None),)
            retired_note = (
                f"{candidate!r} was retired and the name is not reusable "
                f"({getattr(exact, 'retire_reason', None) or 'no reason recorded'}"
                + (
                    f", successor {exact.successor!r}"
                    if getattr(exact, "successor", None)
                    else ""
                )
                + "); "
                f"propose_type will return the retired entry, not create a new one"
            )
        if exact is not None and exact.status != "retired":
            return Resolution(
                outcome="existing",
                reason="; ".join(
                    [f"{candidate!r} is already in the vocabulary"]
                    + ([cross_note] if cross_note else [])
                ),
                tier=tier,
                scoped_to=namespace,
                type=await self._entry(exact),
                confidence=1.0,
                alternatives=cross_alts,
                searched_namespaces=searched,
                complete=cross_complete,
                why_incomplete=cross_why,
            )

        not_a_type = self.resolver.classify(candidate, context, tier=tier)
        if not_a_type is not None:
            return Resolution(
                outcome="not_a_type",
                reason=not_a_type.reason,
                tier=tier,
                scoped_to=namespace,
                confidence=None,
                alternatives=(await self._prior_rejections(namespace, candidate))[0]
                + retired_alt
                + cross_alts,
                searched_namespaces=searched,
                complete=cross_complete,
                why_incomplete=cross_why,
            )

        page = await self.adapter.find_types(TypeQuery(namespace=namespace, kind=kind, status="active"))
        known = page.records
        scored = self.resolver.score(candidate, context, known, tier=tier) if known else []
        alternatives: list[Alternative] = [(n, s) for n, s in scored[:_NEAR_MISS_CAP]]
        # **The cap is a fact about the list, so it gates the claim** (5.3.1 rule 8c).
        # `alternatives` has carried at most five near misses since v0; that was
        # invisible while `complete` was hard-wired False and became a silent
        # truncation under a positive claim the moment ruling R6 made `complete`
        # reachable. Row 3e, third adversarial round: ten types tied at one score, five
        # dropped, `complete=True`, `why_incomplete=""`.
        if len(scored) > _NEAR_MISS_CAP and search_namespaces is not None:
            dropped = (
                f"near misses beyond the first {_NEAR_MISS_CAP} were dropped in "
                f"{namespace!r}"
            )
            cross_complete = False
            cross_why = (
                f"{cross_why}; {dropped}"
                if cross_why
                else "the search is incomplete (INTERFACE.md 5.3.1, ruling R6): " + dropped
            )
        rejections, rejection_note = await self._prior_rejections(namespace, candidate)
        alternatives.extend(rejections)
        alternatives.extend(retired_alt)
        alternatives.extend(cross_alts)

        best_name, best_score = (scored[0] if scored else (None, None))
        reason_bits: list[str] = []
        if retired_note:
            reason_bits.append(retired_note)
        if rejection_note:
            reason_bits.append(rejection_note)
        if cross_note:
            reason_bits.append(cross_note)

        if best_score is not None and best_score >= policy.existing_threshold and best_score >= min_confidence:
            entry = await self.adapter.get_type(namespace, best_name, kind=kind)
            reason_bits.insert(0, f"{best_name!r} matches at {best_score}")
            return Resolution(
                outcome="existing",
                reason="; ".join(reason_bits),
                tier=tier,
                scoped_to=namespace,
                type=await self._entry(entry) if entry else None,
                confidence=best_score,
                alternatives=tuple(alternatives),
                searched_namespaces=searched,
                complete=cross_complete,
                why_incomplete=cross_why,
            )

        if best_score is not None and best_score < min_confidence:
            # Never the best of a bad set. `none` means cannot tell, and the near
            # misses are handed over so a human can overrule.
            reason_bits.insert(
                0,
                f"best match {best_name!r} scored {best_score}, below min_confidence "
                f"{min_confidence}",
            )
            return Resolution(
                outcome="none",
                reason="; ".join(reason_bits),
                tier=tier,
                scoped_to=namespace,
                confidence=best_score,
                alternatives=tuple(alternatives),
                searched_namespaces=searched,
                complete=cross_complete,
                why_incomplete=cross_why,
            )

        if not NAME_RE.match(candidate):
            reason_bits.insert(0, f"{candidate!r} is not a well-formed type name")
            return Resolution(
                outcome="none",
                reason="; ".join(reason_bits),
                tier=tier,
                scoped_to=namespace,
                confidence=best_score,
                alternatives=tuple(alternatives),
                searched_namespaces=searched,
                complete=cross_complete,
                why_incomplete=cross_why,
            )

        # Nothing fits and the candidate looks like a real type. An un-persisted
        # proposal: C3-02 asserts the store is byte-identical after this call.
        now = self._now()
        proposal = Proposal(
            id=_uuid(),
            name=candidate,
            kind=kind or "entity",
            namespace=namespace,
            definition=context.definition_hint or "",
            predicates=(),
            attributes={},
            evidence=(),
            proposed_by=context.proposed_by or "unknown",
            proposed_at=now,
            tier=tier,
            status="pending",
            warnings=(),
            near_matches=tuple(alternatives),
        )
        # The retirement, when there is one, is the decisive fact and leads.
        if retired_note:
            reason_bits.insert(0, f"nothing ACTIVE in the vocabulary fits {candidate!r}")
        else:
            reason_bits.insert(0, f"nothing in the vocabulary fits {candidate!r}")
        return Resolution(
            outcome="proposal",
            reason="; ".join(reason_bits),
            tier=tier,
            scoped_to=namespace,
            proposal=proposal,
            confidence=best_score,
            alternatives=tuple(alternatives),
            searched_namespaces=searched,
            complete=cross_complete,
            why_incomplete=cross_why,
        )

    async def _search_namespaces(
        self,
        candidate: str,
        context: ResolveContext,
        *,
        kind: str | None,
        namespace: str,
        tier: str,
        search_namespaces: Sequence[str] | None,
    ) -> tuple[tuple[Alternative, ...], tuple[str, ...], bool, str, str | None]:
        """Ruling **R6** -- the cross-namespace half of ``resolve_type`` (INTERFACE.md 5.3).

        Returns ``(alternatives, searched, complete, why_incomplete, note)``.

        ``search_namespaces=None`` returns the v0 answer verbatim: no alternatives, no
        namespaces searched, ``complete=False`` with 5.3's standing sentence, and no
        note. **It reads nothing** -- the census below is the only new query this row
        adds and it runs only when a caller asks for it, so no v0 caller pays for R6.

        The completeness rule is the whole point and it is deliberately strict:
        ``complete`` is True only when the caller named **every namespace that has a
        type in it**. Anything less and ``why_incomplete`` names the ones left out by
        name, because *"we searched four of the six"* with the two unnamed is the
        confident partial answer Rule U forbids -- the same failure the empty
        ``alternatives`` of contortion 8 was.
        """
        if search_namespaces is None:
            return (), (), False, "", None

        # ``namespace`` is always searched -- the caller is standing in it. Order is the
        # caller's, deduplicated, with the home namespace first so a reader of
        # ``searched_namespaces`` can see where the outcome came from.
        wanted: list[str] = [namespace]
        for name in search_namespaces:
            if name not in wanted:
                wanted.append(name)

        # **One fetch, reused.** What namespaces exist at all, and what is in the ones
        # the caller named, are the same question asked twice, so they are asked once.
        # The first cut issued this census PLUS one ``find_types`` per named namespace;
        # an adversarial round measured 6,062 SQL round-trips for a single call over
        # 3,000 types in 30 namespaces, of which ~3,000 existed only to learn 30
        # namespace names. Reusing the page removes the per-namespace queries outright.
        # The residual cost is stated in INTERFACE.md 5.3.1 rule 9 rather than hidden:
        # asking for a completeness verdict costs what ``list_types(namespace=None)``
        # costs, and that is the unbounded fetch ruling R13 declined to page in v0.
        #
        # Retired types count towards *which namespaces exist*: a namespace whose every
        # type is retired is still a namespace somebody published into, and calling the
        # search complete without it would be a claim about a place we did not look.
        census = await self.adapter.find_types(TypeQuery(namespace=None, include_retired=True))
        # **One query for every rejection of this word, everywhere.** It replaces the
        # per-namespace queries the first cut issued, and it closes rule 6's blind spot:
        # a namespace whose only trace of this candidate is a REJECTED proposal holds no
        # type, so the type census above cannot see it, and `list_types` cannot show it
        # to the caller either -- yet it holds the cheapest possible record of *we
        # already decided against this word*. Row 3e, third adversarial round.
        #
        # Scope, stated: "every namespace that could contribute an alternative for THIS
        # candidate" -- a namespace holding only unrelated proposals contributes nothing
        # to this list, so leaving it out shortens nothing.
        rejections, rejections_complete, rejections_why = await self._rejections_everywhere(
            candidate
        )
        existing = sorted(
            {rec.namespace for rec in census.records} | set(rejections)
        )
        omitted = [name for name in existing if name not in wanted]

        by_namespace: dict[str, list] = {}
        # **Retired rows are kept, not thrown away.** The first cut filtered them out
        # after using them to decide which namespaces exist -- so a word RETIRED in a
        # namespace the caller named came back invisible, under a `complete=True` seal.
        # In the caller's OWN namespace the identical tombstone is surfaced loudly
        # (5.3), because discarding it is "Rule U's confident negative, in the call
        # designed against mechanism 2". Cross-namespace it was dropped. Row 3e, second
        # adversarial round; in UC3 a retirement by DPR is exactly the *we already
        # decided about this word* signal the second publisher needs.
        retired_elsewhere: dict[str, list] = {}
        for rec in census.records:
            if rec.namespace == namespace:
                continue
            if rec.status == "active":
                by_namespace.setdefault(rec.namespace, []).append(rec)
            elif rec.status == "retired" and rec.name == candidate:
                retired_elsewhere.setdefault(rec.namespace, []).append(rec)

        alternatives: list[Alternative] = []
        seen_labels: set[str] = set()
        exact_elsewhere: list[str] = []
        ambiguous_elsewhere: list[str] = []
        burned_elsewhere: list[tuple[str, Any]] = []
        capped: list[str] = []
        # The home namespace's own rejections are added by `_prior_rejections` in
        # `resolve_type`; what is decided here is whether that list could be whole.
        proposals_complete = rejections_complete
        proposal_whys: list[str] = [rejections_why] if rejections_why else []
        for other in wanted:
            if other == namespace:
                continue
            # **An exact name match in another namespace is the registry's answer, not
            # the resolver's.** C3-11 made the same move for a retired name with a live
            # successor, and for the same reason: the promise held only because the
            # shipped scorer happens to rate an exact name 1.0, and PACKAGE.md 2.6 calls
            # a caller-supplied resolver the production path. R6 exists to tell the
            # second publisher the word is taken; a deployment whose resolver scores
            # differently must not get a different answer to *that*.
            #
            # **The probe is KIND-BLIND, and that is the whole point** *(fixed after
            # round 1 of this row's adversarial loop)*. It used to pass the caller's
            # ``kind=`` through, so DPR publishing ``status`` as a ``value_set`` was
            # invisible to the 311 team asking for ``status`` as an ``entity`` -- which
            # is UC3's collision shape exactly, answered with contortion 8's own
            # sentence under a ``complete=True`` seal. Uniqueness is per
            # ``(namespace, kind)`` (2.1), so a name taken under another kind is not the
            # same entry; it is still the same WORD, and R6 owes the caller that word.
            candidates = [
                rec for rec in by_namespace.get(other, ()) if rec.name == candidate
            ]
            if candidates:
                exact_elsewhere.append(other)
                if len({rec.kind for rec in candidates}) > 1:
                    ambiguous_elsewhere.append(other)
            for tombstone in retired_elsewhere.get(other, ()):
                burned_elsewhere.append((other, tombstone))

            pool = by_namespace.get(other, ())
            if kind is not None:
                pool = [rec for rec in pool if rec.kind == kind]
            scored = (
                self.resolver.score(candidate, context, pool, tier=tier) if pool else []
            )
            if len(scored) > _NEAR_MISS_CAP:
                capped.append(other)
            # Deduped by label: one name under two kinds in one namespace is one taken
            # word, and listing it twice double-counts Rule K's `known`.
            for name, score in scored[:_NEAR_MISS_CAP]:
                label = f"{other}:{name}"
                if label not in seen_labels:
                    seen_labels.add(label)
                    alternatives.append((label, score))
            label = f"{other}:{candidate}"
            if (
                other in exact_elsewhere or other in {n for n, _ in burned_elsewhere}
            ) and label not in seen_labels:
                # Score is None, not 0.0: nothing scored it, and Rule U forbids a zero
                # standing in for "we did not score this".
                seen_labels.add(label)
                alternatives.append((label, None))
            # **The proposal store is the OTHER source `alternatives` is fed from**, and
            # ruling R6's first cut searched it in the home namespace only. A word
            # proposed and rejected in another namespace is the cheapest possible record
            # of *we already decided against this*, which is the whole reason 5.5
            # surfaces it at home. Row 3e, second adversarial round.
            for name in rejections.get(other, ()):
                label = f"{other}:{name}"
                if label not in seen_labels:
                    seen_labels.add(label)
                    alternatives.append((label, None))

        note: str | None = None
        if exact_elsewhere:
            note = (
                f"the name {candidate!r} is ALREADY TAKEN in "
                + ", ".join(repr(name) for name in sorted(set(exact_elsewhere)))
                + " -- scoping keeps those apart (INTERFACE.md 2.6) and this call does "
                "not resolve across namespaces, so the outcome above is about "
                f"{namespace!r} alone"
            )
            if ambiguous_elsewhere:
                note += (
                    " (and under more than one kind in "
                    + ", ".join(repr(name) for name in sorted(set(ambiguous_elsewhere)))
                    + ", so `kind=` is how a caller narrows it)"
                )
        elif alternatives:
            note = (
                "near misses in other namespaces are listed in alternatives: "
                + ", ".join(sorted(name for name, _ in alternatives))
            )
        if burned_elsewhere:
            burned = "; ".join(
                f"{ns}:{rec.name} was RETIRED there ("
                + (getattr(rec, "retire_reason", None) or "no reason recorded")
                + (
                    f", successor {rec.successor!r}"
                    if getattr(rec, "successor", None)
                    else ""
                )
                + ")"
                for ns, rec in sorted(burned_elsewhere, key=lambda pair: pair[0])
            )
            note = f"{note}; {burned}" if note else burned

        # Rule U, four ways. A namespace nobody named, a page the backend could not
        # fully answer, a backend that could not enumerate the namespaces at all, and a
        # PROPOSAL store that could not answer are four different reasons the search was
        # partial, and the caller is told which.
        #
        # The fourth was added by row 3e's SECOND adversarial round, and it is the
        # defect this row's own round-1 fix left behind: rule 8 was applied to
        # `find_types` and not to `find_proposals`, which is the other store
        # `alternatives` is fed from. [Observed] on `sqlite_minimal` -- a reference leg
        # and UC1's declared shape -- one `Resolution` said `complete=True`,
        # `why_incomplete=""`, and in the adjacent `reason` field that prior rejections
        # had been omitted from the list it had just called whole.
        complete = not omitted and census.complete and proposals_complete and not capped
        # **Every reason, not the first one.** Rule U wants the reasons a list is short,
        # plural: an unnamed namespace, a truncated type page, a proposal store that
        # could not answer and a near-miss cap can all bite on one call, and an `elif`
        # chain hands the caller whichever happened to be checked first. Row 3e, third
        # adversarial round found two of them masking each other.
        reasons: list[str] = []
        if omitted:
            reasons.append(
                ", ".join(repr(name) for name in omitted)
                + " "
                + ("has" if len(omitted) == 1 else "have")
                + " a type or a prior rejection of this word and "
                + ("was" if len(omitted) == 1 else "were")
                + " not named in search_namespaces"
            )
        if not census.complete:
            reasons.append(
                "the backend could not return the whole type store in one page, so "
                "both which namespaces exist and what is in them are partial: "
                + (census.why_incomplete or "no reason given by the backend")
            )
        if not proposals_complete:
            reasons.append(
                "prior REJECTIONS could not be searched, so alternatives is short by "
                "however many there are: "
                + "; ".join(proposal_whys or ["no reason given by the backend"])
            )
        if capped:
            reasons.append(
                f"near misses beyond the first {_NEAR_MISS_CAP} were dropped in "
                + ", ".join(repr(name) for name in sorted(set(capped)))
            )
        why = ""
        if reasons:
            why = (
                "the search is incomplete (INTERFACE.md 5.3.1, ruling R6): "
                + "; ".join(reasons)
            )
        return tuple(alternatives), tuple(wanted), complete, why, note

    async def _rejections_everywhere(
        self, candidate: str
    ) -> tuple[dict[str, list[str]], bool, str | None]:
        """``({namespace: rejected names}, could we look, why not)`` for one word.

        The second store ``Resolution.alternatives`` is fed from (5.5). Added by row
        3e's second adversarial round, which found ruling R6's completeness verdict
        computed from the type store alone -- so a backend with
        ``stores_proposals=False`` returned ``complete=True`` next to a ``reason``
        saying rejections had been omitted -- and widened by its third to one query over
        every namespace at once, which is both cheaper than one per namespace and the
        only way to see a namespace that holds a rejection and no type.
        """
        if not self.caps.stores_proposals:
            return {}, False, (
                "prior rejections could not be searched: "
                + (self.caps.reason("stores_proposals") or "")
            )
        page = await self.adapter.find_proposals(
            ProposalQuery(name=candidate, status="rejected")
        )
        found: dict[str, list[str]] = {}
        for record in page.records:
            found.setdefault(record.namespace, []).append(record.name)
        if not page.complete:
            return found, False, (
                "the rejected-proposal page was partial: "
                + (page.why_incomplete or "no reason given by the backend")
            )
        return found, True, None

    async def _prior_rejections(
        self, namespace: str, candidate: str
    ) -> tuple[tuple[Alternative, ...], str | None]:
        """A retained rejection is the cheapest record of "we already decided against
        this word". Surfacing it is what stops a re-proposal in six months."""
        if not self.caps.stores_proposals:
            return (), (
                "prior rejections are omitted from alternatives: "
                + self.caps.reason("stores_proposals")
            )
        page = await self.adapter.find_proposals(
            ProposalQuery(namespace=namespace, name=candidate, status="rejected")
        )
        if not page.records:
            return (), None
        # Score is None, not 0.0: nothing scored these, and Rule U forbids a zero
        # standing in for "we did not look".
        alts: tuple[Alternative, ...] = tuple((r.name, None) for r in page.records)
        return alts, f"{candidate!r} was proposed and rejected before"

    # =========================================================== 5.4 propose_type
    def _edge_family_refusal(self, kind: str, attributes: dict) -> Refusal | None:
        """EDGES.md 2.4.1 and ruling R18, at DECLARATION time.

        Called from `propose_type`, from `approve` and from `import_types`, because a
        rule with one enforcement point is a rule with one door left open -- and the
        thing on the other side of this one is the ROADMAP.md kill row.

        **Unconditional, not schema-mode gated.** `_check_attributes` refuses only in
        `enforce` mode, and PACKAGE.md 5.3's default is `off`; a rule that only bites
        when a deployment has configured a schema is a rule a deployment can turn off.
        R18 is a rule the REGISTRY knows, and PACKAGE.md 5.6 records it as an exception
        list of length one for exactly that reason.
        """
        if kind != "edge":
            return None
        breach = family_declaration_problem(attributes)
        if breach is None:
            return None
        reason, sentence, detail = breach
        return Refusal(reason, {**detail, "why": sentence})

    async def propose_type(
        self,
        name: str,
        definition: str,
        evidence: Sequence[Evidence],
        proposed_by: str,
        *,
        kind: str = "entity",
        namespace: str = "default",
        predicates: Sequence[str] = (),
        attributes: dict | None = None,
        tier: str | None = None,
        source_version: str | None = None,
    ) -> Proposal | TypeEntry | Refusal:
        """An addition, not yet a fact.

        A declaration API cannot return a proposal, because it has already decided.
        This one refuses only two things -- an empty definition and an unattributed
        machine proposal -- and warns about everything else, because refusing a
        near-duplicate is how you flatten a capability predicate.
        """
        policy = self.policy(namespace)
        attributes = dict(attributes or {})
        evidence = tuple(evidence)

        if not definition or not definition.strip():
            raise ValueError("definition is required and must be non-empty")
        if proposed_by.startswith("ai:") and tier is None:
            raise ValueError("tier is required when proposed_by starts with 'ai:'")
        if not NAME_RE.match(name):
            raise ValueError(f"name must match {NAME_RE.pattern}; got {name!r}")

        edge_refusal = self._edge_family_refusal(kind, attributes)
        if edge_refusal is not None:
            return edge_refusal

        existing = await self.adapter.get_type(namespace, name, kind=kind)
        if existing is not None:
            if existing.status == "retired":
                # A retired name is not reusable. Silently reusing a retired word is
                # mechanism 4 with a time delay.
                return await self._entry(existing, extra_warnings=("name_previously_retired",))
            return await self._entry(existing)

        schema, violations = await self._check_attributes(namespace, kind, name, attributes)
        warnings: list[str] = []
        if violations:
            if schema and schema.mode == "enforce":
                return Refusal(
                    "attributes_schema_violation",
                    {
                        "kind": kind,
                        "violations": violations,
                        "schema_version": schema.version,
                        # R10: with name-level overrides in play, "which schema refused
                        # me" is a question the caller now has to be able to answer.
                        "schema_name": schema.name,
                    },
                )
            if schema and schema.mode == "warn":
                warnings.extend(f"attributes_invalid:{v}" for v in violations)

        if not evidence:
            warnings.append("no_evidence")
        if _asserts_domain_semantic(definition, kind, attributes) and not _has_external_doc(
            evidence
        ):
            warnings.append("unverified_semantics")

        page = await self.adapter.find_types(TypeQuery(namespace=namespace, kind=kind, status="active"))
        near = [
            (n, s)
            for n, s in self.resolver.score(
                name,
                ResolveContext(definition_hint=definition),
                page.records,
                tier=tier or "unspecified",
            )
            if s >= policy.near_duplicate_threshold
        ]
        for near_name, _ in near:
            warnings.append(f"near_duplicate:{near_name}")

        now = self._now()
        rec = ProposalRecord(
            proposal_id=_uuid(),
            namespace=namespace,
            kind=kind,
            name=name,
            definition=definition,
            predicates=tuple(predicates),
            attributes=attributes,
            evidence=[_evidence_to_dict(e) for e in evidence],
            proposed_by=proposed_by,
            proposed_at=now,
            tier=tier,
            status="pending",
            warnings=tuple(warnings),
            near_matches=[[n, s] for n, s in near],
            source_version=source_version,
        )

        auto = policy.approval_policy == "auto" or not self.caps.stores_proposals
        below = policy.tier_is_below_minimum(tier)

        if not self.caps.stores_proposals:
            # No proposal storage means no review step: the price of one is exactly one
            # table, and that price is now legible rather than invisible.
            if below is not False:
                return Refusal(
                    "tier_below_auto_approve_policy",
                    {
                        "tier": tier,
                        "min_auto_approve_tier": policy.min_auto_approve_tier,
                        "note": "this backend cannot hold the proposal for review: "
                        + self.caps.reason("stores_proposals"),
                    },
                )
            return await self._write_approved(
                rec, approved_by=f"auto:{policy.auto_policy_name}", note=None, store_proposal=False
            )

        async with self.adapter.transaction():
            await self.adapter.put_proposal(rec, expect_absent=True)
            await self._append_event(
                namespace,
                "proposed",
                proposed_by,
                kind=kind,
                name=name,
                proposal_id=rec.proposal_id,
                detail={"tier": tier, "warnings": list(warnings)},
            )

        if auto:
            if below is not False:
                # The proposal stays pending and comes back for review rather than
                # being auto-approved below the tier gate. Nothing is lost.
                pending = await self.adapter.get_proposal(rec.proposal_id)
                return self._proposal(
                    ProposalRecord(
                        **{
                            **pending.__dict__,
                            "warnings": tuple(pending.warnings)
                            + ("auto_approval_refused:tier_below_auto_approve_policy",),
                        }
                    )
                )
            return await self.approve(
                rec.proposal_id, f"auto:{policy.auto_policy_name}", mode="auto"
            )

        return self._written(self._proposal(await self.adapter.get_proposal(rec.proposal_id)))

    # ==================================================== 5.5 approve  /  reject
    async def approve(
        self,
        proposal_id: str,
        approved_by: str,
        *,
        mode: str = "human",
        note: str | None = None,
        predicates: Sequence[str] | None = None,
        definition: str | None = None,
    ) -> TypeEntry | Refusal:
        """The review that A1 says HHS never had.

        The read and all four writes happen in one transaction, which is what turns
        ``already_decided`` from a race into an idempotent refusal.
        """
        if not self.caps.stores_proposals:
            return Refusal(
                "proposals_not_stored", {"why": self.caps.reason("stores_proposals")}
            )

        async with self.adapter.transaction():
            rec = await self.adapter.get_proposal(proposal_id)
            if rec is None:
                return Refusal("unknown_proposal", {"proposal_id": proposal_id})
            if rec.status != "pending":
                return Refusal(
                    "already_decided",
                    {
                        "proposal_id": proposal_id,
                        "status": rec.status,
                        "decided_by": rec.decided_by,
                        "decided_at": rec.decided_at.isoformat() if rec.decided_at else None,
                    },
                )

            policy = self.policy(rec.namespace)
            if mode == "auto":
                below = policy.tier_is_below_minimum(rec.tier)
                if below is not False:
                    return Refusal(
                        "tier_below_auto_approve_policy",
                        {
                            "tier": rec.tier,
                            "min_auto_approve_tier": policy.min_auto_approve_tier,
                        },
                    )

            amended = ProposalRecord(
                **{
                    **rec.__dict__,
                    "definition": definition if definition is not None else rec.definition,
                    "predicates": tuple(predicates)
                    if predicates is not None
                    else rec.predicates,
                }
            )
            # Ruling **R18** names `approve()` specifically, and it is checked here
            # as well as in `propose_type` because a proposal may predate the rule,
            # and because `approve(definition=..., predicates=...)` is the one call
            # that amends a pending proposal on its way in.
            edge_refusal = self._edge_family_refusal(
                amended.kind, dict(amended.attributes or {})
            )
            if edge_refusal is not None:
                return edge_refusal
            schema, violations = await self._check_attributes(
                amended.namespace, amended.kind, amended.name, amended.attributes
            )
            if violations and schema and schema.mode == "enforce":
                return Refusal(
                    "attributes_schema_violation",
                    {
                        "kind": amended.kind,
                        "violations": violations,
                        "schema_version": schema.version,
                        "schema_name": schema.name,
                    },
                )

            amendment: dict[str, Any] = {}
            if definition is not None and definition != rec.definition:
                amendment["definition_before"] = rec.definition
            if predicates is not None and tuple(predicates) != rec.predicates:
                amendment["predicates_before"] = list(rec.predicates)
            if note:
                amendment["note"] = note

            return await self._write_approved(
                amended,
                approved_by=approved_by,
                note=note,
                store_proposal=True,
                amendment=amendment,
            )

    async def _write_approved(
        self,
        rec: ProposalRecord,
        *,
        approved_by: str,
        note: str | None,
        store_proposal: bool,
        amendment: dict | None = None,
    ) -> TypeEntry:
        now = self._now()
        schema, _ = await self._check_attributes(
            rec.namespace, rec.kind, rec.name, rec.attributes
        )
        provenance = Provenance(
            created_at=rec.proposed_at,
            created_by_actor=rec.proposed_by,
            proposed_by=rec.proposed_by,
            approved_by=approved_by,
            approved_at=now,
            model_tier=rec.tier,
            evidence=tuple(_evidence_from_dict(e) for e in (rec.evidence or [])),
            # R21 -- the SOURCE's own version, carried from the proposal. Never ours:
            # `created_at` is when we wrote it.
            source_version=rec.source_version,
        )
        type_rec = TypeRecord(
            namespace=rec.namespace,
            kind=rec.kind,
            name=rec.name,
            definition=rec.definition,
            created_by=_created_by(rec.proposed_by),
            status="active",
            predicates=tuple(rec.predicates),
            aliases=(),
            attributes=dict(rec.attributes or {}),
            attr_schema_version=schema.version if schema else None,
            provenance=_prov_to_dict(provenance),
            warnings=tuple(rec.warnings),
            created_at=rec.proposed_at,
            updated_at=now,
        )
        async with self.adapter.transaction():
            stored = await self.adapter.put_type(type_rec, expect_absent=True)
            if store_proposal:
                await self.adapter.put_proposal(
                    ProposalRecord(
                        **{
                            **rec.__dict__,
                            "status": "approved",
                            "decided_by": approved_by,
                            "decided_at": now,
                            "decision_reason": note,
                        }
                    )
                )
            await self._observe(stored)
            await self._append_event(
                rec.namespace,
                "approved",
                approved_by,
                kind=rec.kind,
                name=rec.name,
                proposal_id=rec.proposal_id,
                detail={"tier": rec.tier, **(amendment or {})},
            )
        return self._written(await self._entry(stored))

    async def reject(
        self,
        proposal_id: str,
        rejected_by: str,
        reason: str,
        *,
        superseded_by: str | None = None,
    ) -> Rejection | Refusal:
        """A rejected proposal is the cheapest record of "we already considered this
        word and decided against it". Discard it and the next proposer re-proposes it
        in six months."""
        if not reason or not reason.strip():
            raise ValueError("reject requires a non-empty reason")
        if not self.caps.stores_proposals:
            return Refusal(
                "proposals_not_stored", {"why": self.caps.reason("stores_proposals")}
            )

        async with self.adapter.transaction():
            rec = await self.adapter.get_proposal(proposal_id)
            if rec is None:
                return Refusal("unknown_proposal", {"proposal_id": proposal_id})
            if rec.status != "pending":
                return Refusal(
                    "already_decided", {"proposal_id": proposal_id, "status": rec.status}
                )
            now = self._now()
            await self.adapter.put_proposal(
                ProposalRecord(
                    **{
                        **rec.__dict__,
                        "status": "rejected",
                        "decided_by": rejected_by,
                        "decided_at": now,
                        "decision_reason": reason,
                        "superseded_by": superseded_by,
                    }
                )
            )
            await self._append_event(
                rec.namespace,
                "rejected",
                rejected_by,
                kind=rec.kind,
                name=rec.name,
                proposal_id=proposal_id,
                detail={"reason": reason, "superseded_by": superseded_by},
            )
        return Rejection(
            proposal_id=proposal_id,
            rejected_by=rejected_by,
            rejected_at=now,
            reason=reason,
            superseded_by=superseded_by,
            warnings=self._write_warnings(),
        )

    # ============================================================ 5.6 list_types
    async def list_types(
        self,
        kind: str | None = None,
        *,
        include_retired: bool = False,
        namespace: str | None = None,
        status: str | None = None,
        predicate: str | None = None,
        created_by: str | None = None,
        unverified_semantics: bool | None = None,
        orphaned: bool | None = None,
    ) -> TypeListing:
        """The call whose absence means "nobody could find the existing types".

        ``include_retired=False`` is the default *and hides things*, so the listing
        reports ``complete=False`` whenever any filter was applied. A caller that wants
        a true census passes ``include_retired=True, status=None, namespace=None``.
        """
        if predicate is not None and not self.caps.indexes_membership:
            return TypeListing(
                types=(),
                known=None,
                complete=False,
                why_incomplete=self.caps.reason("indexes_membership"),
            )

        page = await self.adapter.find_types(
            TypeQuery(
                namespace=namespace,
                kind=kind,
                status=status,
                predicate=predicate,
                created_by=created_by,
                include_retired=include_retired,
            )
        )
        consumer_rows_by_ns: dict[str, list[ConsumerRecord]] = {}
        entries: list[TypeEntry] = []
        excluded_unknown = 0
        for rec in page.records:
            if rec.namespace not in consumer_rows_by_ns:
                consumer_rows_by_ns[rec.namespace] = await self.adapter.find_consumers(rec.namespace)
            entry = await self._entry(rec, consumers=consumer_rows_by_ns[rec.namespace])
            if unverified_semantics is not None:
                has = "unverified_semantics" in entry.warnings
                if has != unverified_semantics:
                    continue
            if orphaned is not None:
                value = entry.usage.orphaned
                if value is None:
                    # An unknown orphan state is excluded from both answers and counted,
                    # rather than being folded into whichever one the caller asked for.
                    excluded_unknown += 1
                    continue
                if value != orphaned:
                    continue
            entries.append(entry)

        applied = [
            label
            for label, used in (
                ("kind", kind is not None),
                ("namespace", namespace is not None),
                ("status", status is not None),
                ("predicate", predicate is not None),
                ("created_by", created_by is not None),
                ("unverified_semantics", unverified_semantics is not None),
                ("orphaned", orphaned is not None),
                ("include_retired=False", not include_retired),
            )
            if used
        ]
        why: str | None = None
        if applied:
            why = "filters suppressed rows: " + ", ".join(applied)
        elif not page.complete:
            why = page.why_incomplete

        known = len(entries) if page.known is not None else None
        return TypeListing(
            types=tuple(entries),
            known=known,
            complete=bool(page.complete and not applied),
            why_incomplete=why,
            excluded_unknown=excluded_unknown if orphaned is not None else None,
        )

    # ================================================================= 5.7 usage
    async def usage(self, type: str, *, namespace: str = "default") -> UsageReport:
        return await self._usage_report(await self._require(namespace, type))

    # ============================================================ 5.8 provenance
    async def provenance(self, type: str, *, namespace: str = "default") -> Provenance:
        """Missing evidence is ``[]`` -- never a reconstructed narrative."""
        rec = await self._require(namespace, type)
        history, history_why = await self._events(namespace, rec.kind, rec.name)
        return _prov_from_dict(rec.provenance or {}, history, history_why)

    # ================================================================ 5.9 retire
    async def retire(
        self,
        type: str,
        reason: str,
        *,
        retired_by: str,
        namespace: str = "default",
        successor: str | None = None,
        force: bool = False,
    ) -> TypeEntry | Refusal:
        """Retirement is guarded by ``consumers``, not by usage."""
        if not reason or not reason.strip():
            raise ValueError("retire requires a non-empty reason")
        rec = await self._require(namespace, type)
        report = await self._consumer_report(rec)

        # **A destructive override that cannot be recorded is refused -- whichever guard
        # it is overriding.** This used to be checked only inside the `live_consumers`
        # branch, so on a backend that also declares `indexes_membership=False`
        # `gates_on` was always empty, the branch never ran, and `force=True` retired a
        # type with a real registered gating consumer leaving **no refusal, no warning
        # and no history**. That is Tenshen's own declared shape (PACKAGE.md 7.3 B3 and
        # B6 together), and B6 states in terms that this case returns
        # `cannot_record_override`. `merge_types` had the unconditional form since v0;
        # `retire` now matches it. Row 3c, after an adversarial review round.
        if force and not self.caps.stores_events:
            return Refusal(
                "cannot_record_override",
                {
                    "why": self.caps.reason("stores_events"),
                    "type": type,
                    "would_override": [c.id for c in report.gates_on],
                    "gates_on_knowable": self.caps.indexes_membership,
                },
            )

        if report.gates_on and not force:
            return Refusal(
                "live_consumers",
                {"gates_on": [c.id for c in report.gates_on], "type": type},
            )
        # An EMPTY gates_on means "nothing gates on this" only when we were able to
        # look. On a backend that cannot index membership, every extent is empty, so
        # `gates_on` is empty for a reason that means *we could not check* -- and
        # retiring on that is mechanism C committed by the call built to catch it.
        # 5.10 already takes this line for merge_types; retire takes it too, and
        # `force=True` is the override, recorded in history like any other.
        # Row 3c, after an adversarial review round reproduced the silent retirement.
        if not report.gates_on and not self.caps.indexes_membership and not force:
            return Refusal(
                "no_consumer_evidence",
                {
                    "why": (
                        "this backend cannot compute a predicate's extent, so an empty "
                        "`gates_on` means we could not look, not that nothing gates on "
                        "it: " + (self.caps.reason("indexes_membership") or "")
                    ),
                    "type": type,
                    "overridable": True,
                    "override_with": "force=True",
                },
            )


        # **`retire(successor=)` IS a collapse, and it gets the merge's guards.**
        # `resolve_type` on a retired name returns its successor at confidence 1.0
        # (5.3, and this registry calls that a guarantee); `related_names` calls
        # retirement-with-a-successor a *joining* in the same sentence as a merge; and
        # 5.4's `endpoint_type_merged` treats the two acts as one. So a caller who is
        # refused `merge_types("commentable", "searchable")` -- NON-OVERRIDABLY, under
        # every acknowledgement -- could reach the identical outcome by retiring one
        # with the other as its successor, with no refusal, no acknowledgement and no
        # warning. **That is `ROADMAP.md`'s kill row, and its third trip in this
        # project's life** (row 3c on an unknowable extent, row #6 round 2 on an empty
        # one, row #6 round 3 here). All three are the same category error: a guard
        # written for one call, over a fact that more than one call can change.
        #
        # The two guards that transfer are the two that are about IDENTITY rather than
        # about evidence -- 5.10's refusals #2 and #3. They are non-overridable there
        # and they are non-overridable here, `force=True` included: `force` overrides
        # the CONSUMER guards, which are about what we could see, never the identity
        # guards, which are about what would become true. Pinned by `C9-18`.
        if successor is not None:
            succ = await self.adapter.get_type(namespace, successor)
            if succ is not None:
                if succ.kind != rec.kind:
                    return Refusal(
                        "kind_mismatch",
                        {
                            "from": rec.kind,
                            "into": succ.kind,
                            "type": type,
                            "successor": successor,
                            "why": "a successor redirects `resolve_type` at confidence "
                            "1.0, so naming one of another kind makes the registry "
                            "answer a question about one kind with an entry of another",
                            "overridable": False,
                        },
                    )
                if rec.kind == "predicate":
                    knowable = self.caps.indexes_membership
                    left = set((await self._extent(namespace, rec.name, True))[0])
                    right = set((await self._extent(namespace, succ.name, True))[0])
                    if not knowable or not left or left != right:
                        return Refusal(
                            "predicate_merge",
                            {
                                "from_extent": sorted(left),
                                "into_extent": sorted(right),
                                "extents_knowable": knowable,
                                "extents_empty": not left and not right,
                                "type": type,
                                "successor": successor,
                                "why": "retiring a predicate with another as its "
                                "successor redirects every `resolve_type` for the "
                                "first to the second -- the same claim `merge_types` "
                                "refuses non-overridably unless the two extents are "
                                "non-empty and identical",
                                "overridable": False,
                            },
                        )

        usage = await self._usage_report(rec)
        warnings = list(rec.warnings)
        if usage.orphaned is None and "retired_without_usage_evidence" not in warnings:
            warnings.append("retired_without_usage_evidence")

        now = self._now()
        retired = TypeRecord(
            **{
                **rec.__dict__,
                "status": "retired",
                "retire_reason": reason,
                "retired_by": retired_by,
                "retired_at": now,
                "successor": successor,
                "warnings": tuple(warnings),
                "updated_at": now,
            }
        )
        async with self.adapter.transaction():
            stored = await self.adapter.put_type(retired)
            await self._append_event(
                namespace,
                "retired",
                retired_by,
                kind=rec.kind,
                name=rec.name,
                detail={
                    "reason": reason,
                    "successor": successor,
                    "forced": bool(force and report.gates_on),
                    "overrode": [c.id for c in report.gates_on] if force else [],
                },
            )
        return self._written(await self._entry(stored))

    # ============================================================= 5.9b reinstate
    async def reinstate(
        self,
        type: str,
        reason: str,
        *,
        reinstated_by: str,
        namespace: str = "default",
    ) -> TypeEntry | Refusal:
        """The other end of the retirement story -- ruling **R11**, row 3e.

        INTERFACE.md 5.9 used to justify proceeding with a retirement under an unknown
        orphan state on the grounds that *"retiring is reversible-ish"*, and said reuse
        *"requires an explicit ``reinstate`` decision by the approver"*. **There was no
        such call.** It appeared once, in a subordinate clause, and nowhere else in the
        repository -- so a retired name was burned for everyone, permanently, by one
        actor, with no recorded path back. Row 3c corrected the justification and left
        the governance defect standing as Q6; this is the call.

        **Ruling R19: this covers edge FAMILIES and never edge instances.** An edge
        family *is* a ``kind="edge"`` ``TypeEntry`` (EDGES.md 2.3), so it arrives here
        with no second mechanism and no special case in this method. An edge *instance*
        is never reinstated: a retracted edge is no claim (EDGES.md 3.2), and
        re-asserting it is a **new** edge whose provenance cites the retracted one.

        Refuses ``successor_active`` when the retirement named a successor and that
        successor is itself active. Not overridable, and it does not need to be: the
        path back is to retire the successor first, which is an ordinary call that
        records who did it. Reinstating a word whose replacement is in use is
        mechanism 4 arriving through the lifecycle -- two live words for one meaning,
        which is the thing this registry exists to detect.
        """
        if not reason or not reason.strip():
            raise ValueError("reinstate requires a non-empty reason")
        rec = await self._require(namespace, type)

        if rec.status != "retired":
            # Never a silent no-op. The desired state already holds, so this is not a
            # refusal -- nothing was prevented -- but a call that quietly did nothing is
            # the shape ruling R4 forbade for `register_consumer`, and the caller asked
            # a question that deserves an answer.
            return await self._entry(rec, extra_warnings=("reinstate_no_op:not_retired",))

        successor = getattr(rec, "successor", None)
        if successor:
            # ``kind=`` narrows on purpose: uniqueness is per ``(namespace, kind)``
            # (2.1), so a live entry of a DIFFERENT kind that happens to share the
            # successor's word is a different type, not this word's replacement.
            # Unnarrowed, this probe raised ``AmbiguousKind`` straight out of a call
            # documented ``-> TypeEntry | Refusal`` the moment ruling R19's edge
            # families shared a word with an entity -- row 3e, third adversarial round.
            live = await self.adapter.get_type(namespace, successor, kind=rec.kind)
            if live is not None and live.status != "retired":
                return Refusal(
                    "successor_active",
                    {
                        "type": type,
                        "namespace": namespace,
                        "successor": successor,
                        "retire_reason": getattr(rec, "retire_reason", None),
                        "why": (
                            f"{type!r} was retired with {successor!r} as its successor "
                            f"and {successor!r} is active; reinstating would put two "
                            f"live words on one meaning (INTERFACE.md 5.9b)"
                        ),
                        "overridable": False,
                        "path_back": f"retire {successor!r} first",
                    },
                )

        # **Two live words with one meaning between them is mechanism 4, and this call
        # was A door left open to it** *(row 3e, first adversarial round; "the one
        # door" was withdrawn by the third, which found two more in `import_types`.
        # `C16-06` asserts the whole-store invariant instead of guessing entrances)*.
        # `merge_types` refuses by default and `propose_type` on a name a live type
        # holds as an alias returns the tombstone -- but `merge A into B; retire B;
        # reinstate A; reinstate B` are four ordinary calls that end with A and B both
        # active and B still holding A's name as an alias. `successor_active` catches
        # the one-step version and is walked around by retiring the successor first.
        # Reproduced end to end on the UC3 fixture before it was believed.
        #
        # Refused rather than warned: this is not an uncertainty, it is a collision the
        # registry can see, inside ONE namespace -- which is the case 2.6 says scoping
        # exists to prevent rather than preserve. The path back is named in the detail,
        # and it is a real one: retire the other word, which is an ordinary recorded
        # call.
        if not self.caps.stores_events:
            return Refusal(
                "cannot_record_override",
                {
                    "type": type,
                    "namespace": namespace,
                    "why": self.caps.reason("stores_events"),
                    "would_clear": {
                        "retire_reason": getattr(rec, "retire_reason", None),
                        "retired_by": getattr(rec, "retired_by", None),
                        "successor": successor,
                    },
                },
            )

        collides_with, relation, partial_why = await self._lifecycle_collisions(namespace, rec)
        if collides_with is not None:
            explanation = {
                "alias": f"{collides_with!r} is active and one of you carries the "
                f"other's name as an alias",
                "successor": f"{type!r} was retired in favour of {collides_with!r} "
                f"(directly or through a chain of successions) and "
                f"{collides_with!r} is active",
                "predecessor": f"{collides_with!r} is active and was itself retired in "
                f"favour of {type!r} (directly or through a chain of "
                f"successions)",
            }[relation or "alias"]
            return Refusal(
                "alias_collision",
                {
                    "type": type,
                    "namespace": namespace,
                    "collides_with": collides_with,
                    "relation": relation,
                    "why": (
                        f"reinstating {type!r} would leave two ACTIVE entries with one "
                        f"word between them: " + explanation +
                        " (INTERFACE.md 5.9b; mechanism 4)"
                    ),
                    "overridable": False,
                    "path_back": (
                        f"retire {collides_with!r} first, or leave this word retired"
                    ),
                },
            )

        # Rule U on the check above, twice. On a backend that cannot store aliases every
        # alias list is empty, and on one that could not answer the scan in full the
        # absence is over rows we never read -- both mean *we could not look*, which is
        # the same shape as `retire` reading an unknowable `gates_on` as "nothing gates
        # on this" (5.9). Both WARN rather than refuse: unlike the event record below,
        # nothing is destroyed by proceeding, and refusing would make the call
        # unreachable on a backend whose only failing is that it pages or does not keep
        # prior names. The scan already pages to exhaustion, so this is what is left
        # when a backend declares a page partial and offers no way to read the rest.
        alias_warnings: list[str] = []
        if not self.caps.stores_aliases:
            alias_warnings.append(
                "reinstate_alias_check_unavailable:"
                + (self.caps.reason("stores_aliases") or "this backend stores no aliases")
            )
        if partial_why:
            alias_warnings.append("reinstate_alias_check_unavailable:" + partial_why)

        # **A lifecycle fact that is REMOVED and cannot be recorded is refused**, on the
        # rule PACKAGE.md 3.6 states for `cannot_record_override`. Every other call in
        # this surface only ever appends: `retire` adds a tombstone, `merge_types` adds
        # an alias and a tombstone, and nothing is deleted. This one clears the four
        # retirement fields off the record, so the event IS the record -- on a backend
        # that cannot store one, a name would come back to life with nothing anywhere
        # saying it had ever been retired or by whom.
        #
        # Stated cost: a `stores_events=False` store cannot un-burn a name. That is the
        # state of the world BEFORE this row, unchanged -- and it is consistent, because
        # `retire(force=True)` is already refused on such a store for the same reason.
        now = self._now()
        reinstated = TypeRecord(
            **{
                **rec.__dict__,
                "status": "active",
                # Cleared, not kept. `retire_reason` on an ACTIVE row is a statement
                # about a retirement that is no longer in force, and a stale `successor`
                # on a live entry is a pointer a later call would read as current. The
                # history is where the retirement lives now -- 5.8's append-only rule
                # says a correction is a new event, never an edit, and the event below
                # carries every field this clears.
                "retire_reason": None,
                "retired_by": None,
                "retired_at": None,
                "successor": None,
                "warnings": tuple(
                    w
                    for w in rec.warnings
                    if w not in ("retired_without_usage_evidence", "name_previously_retired")
                ),
                "updated_at": now,
            }
        )
        async with self.adapter.transaction():
            stored = await self.adapter.put_type(reinstated)
            await self._append_event(
                namespace,
                "reinstated",
                reinstated_by,
                kind=rec.kind,
                name=rec.name,
                detail={
                    "reason": reason,
                    "retire_reason": getattr(rec, "retire_reason", None),
                    "retired_by": getattr(rec, "retired_by", None),
                    "retired_at": _iso(getattr(rec, "retired_at", None)),
                    "successor": successor,
                },
            )
        return self._written(await self._entry(stored, extra_warnings=tuple(alias_warnings)))

    async def _active_page(self, namespace: str) -> tuple[list, str | None]:
        """Every ACTIVE type in a namespace, paged to exhaustion, plus a ``why`` if
        the backend still could not answer in full.

        **The page is not one page.** ``TypePage`` carries ``complete``/``next_after``
        so a backend may cap an unlimited query (PACKAGE.md 3.3, 3.4 primitive 6), and
        the first cut of the collision scan below read one page and reported "no
        collision" over it -- a confident absence built on a look the backend had
        already said was partial, in the one call where that page decides a **refusal**.
        Rule U, in the call whose whole job is to refuse on a collision. Reproduced over
        a paging adapter in row 3e's second adversarial round: the exact end state
        ``C9-12`` asserts is refused, reached with no refusal and no warning.

        UC3 is the scale where a backend pages: one namespace, dozens of agencies,
        thousands of active types.
        """
        records: list = []
        after: str | None = None
        why: str | None = None
        seen_cursors: set[str] = set()
        while True:
            page = await self.adapter.find_types(
                TypeQuery(namespace=namespace, status="active", after=after)
            )
            records.extend(page.records)
            if page.complete:
                why = None
                break
            why = page.why_incomplete or "the backend could not answer this query in full"
            cursor = page.next_after
            # No cursor, or a cursor we have already followed, means there is no way to
            # read the rest. Say so rather than loop or pretend.
            if not cursor or cursor in seen_cursors:
                break
            seen_cursors.add(cursor)
            after = cursor
        return records, why

    async def _lifecycle_collisions(
        self, namespace: str, rec: TypeRecord
    ) -> tuple[str | None, str | None, str | None]:
        """``(colliding type, which relation, why the look was partial)``.

        Two live words for one meaning can be reached down two different relations, and
        the first cut of this guard only knew one of them.

        **Aliases** -- written by ``merge_types`` onto the survivor. Checked both ways,
        because either side of a merge can be the one coming back.

        **Successors** -- written by ``retire(successor=…)``, which writes *no* alias at
        all, and **transitively**, because a word replaced by a word that was itself
        replaced is two hops from a live meaning. Read out of the ``retired`` events
        rather than off the live ``successor`` column, because **this call erases that
        column** -- so a one-hop check on it is a check on a fact ``reinstate`` itself
        deletes. [Observed, row 3e second adversarial round] following the path back
        that ``successor_active``'s own ``detail["path_back"]`` instructs a caller to
        take -- retire the successor, then reinstate -- ended in exactly the state the
        refusal exists to forbid, and ``C9-10`` stopped one call short of finding it.
        Events are always available here: ``reinstate`` has already refused
        ``cannot_record_override`` on a store that cannot keep them.
        """
        records, why = await self._active_page(namespace)
        active = {(r.name, r.kind) for r in records}

        mine = set(rec.aliases or ())
        for other in records:
            if other.name == rec.name and other.kind == rec.kind:
                continue
            if rec.name in (other.aliases or ()):
                return other.name, "alias", why
            if other.name in mine:
                return other.name, "alias", why

        # The succession graph, as RECORDED, keyed on ``(name, kind)``.
        #
        # **Keyed on the pair, because uniqueness is** (2.1). A bare-name graph made
        # this guard confuse two different words: with `holder` live as a `kind="edge"`
        # family and `owner` retired in favour of an entity called `holder`, it issued a
        # false, non-overridable refusal telling an operator to retire an edge family
        # nobody had merged. Ruling **R19** puts edge families in this call's path by
        # design -- a family *is* a `TypeEntry` -- so this is not a hypothetical.
        #
        # **Both `retired` AND `merged` events.** A merge retires `from_` with `into` as
        # its successor and writes the alias onto the survivor, and the first cut read
        # only the survivor's `aliases` column for that -- so one ordinary
        # ``import_types`` call, which rewrites a live row and wipes its aliases, erased
        # the guard's only evidence and let the four-call walk through. Row 3e, third
        # adversarial round, reproduced on 5.9b's own named fixture.
        succeeds: dict[tuple[str, str], set[tuple[str, str]]] = {}
        preceded: dict[tuple[str, str], set[tuple[str, str]]] = {}
        for event in await self.adapter.read_events(namespace):
            detail = event.detail or {}
            if event.event == "retired":
                successor = detail.get("successor")
            elif event.event == "merged":
                successor = detail.get("into")
            else:
                continue
            if not successor or not event.name or not event.kind:
                continue
            here = (event.name, event.kind)
            there = (successor, event.kind)
            succeeds.setdefault(here, set()).add(there)
            preceded.setdefault(there, set()).add(here)

        def _walk(start, graph):
            seen = {start}
            frontier = list(graph.get(start, ()))
            while frontier:
                node = frontier.pop()
                if node in seen:
                    continue
                seen.add(node)
                if node in active:
                    return node[0]
                frontier.extend(graph.get(node, ()))
            return None

        me = (rec.name, rec.kind)
        forward = _walk(me, succeeds)
        if forward is not None:
            return forward, "successor", why
        backward = _walk(me, preceded)
        if backward is not None:
            return backward, "predecessor", why
        return None, None, why

    # =========================================================== 5.10 merge_types
    async def merge_types(
        self,
        from_: str,
        into: str,
        reason: str,
        *,
        merged_by: str,
        namespace: str = "default",
        into_namespace: str | None = None,
        acknowledge: Sequence[str] = (),
    ) -> MergeResult | Refusal:
        """The guarded one. Four of its six refusals cannot be overridden at all.

        ``into_namespace`` is additive to INTERFACE.md 5.10's signature and exists so
        the cross-namespace refusal is reachable at all -- a single ``namespace``
        argument makes a cross-namespace merge unexpressible. Deviation D-7.
        """
        if not reason or not reason.strip():
            raise ValueError("merge_types requires a non-empty reason")
        acknowledge = tuple(acknowledge)
        target_ns = into_namespace or namespace

        left = await self._require(namespace, from_)
        right = await self._require(target_ns, into)

        left_report = await self._consumer_report(left)
        right_report = await self._consumer_report(right)
        left_gates = {c.id for c in left_report.gates_on}
        right_gates = {c.id for c in right_report.gates_on}

        # 1 -- non-overridable. Merging asserts every consumer of one accepts the other.
        if left_gates != right_gates:
            return Refusal(
                "different_consumer_sets",
                {
                    "from": sorted(left_gates),
                    "into": sorted(right_gates),
                    "overridable": False,
                },
            )

        # 2 -- the kill row. A predicate is not a type list; merging two whose extents
        # differ asserts that anything commentable is searchable.
        if "predicate" in (left.kind, right.kind):
            # **An extent we could not compute is not a byte-identical extent.** On a
            # backend with indexes_membership=False every extent comes back empty, so
            # two predicates with genuinely different members compared EQUAL and this
            # refusal never fired -- the merge fell through to the *overridable*
            # no_consumer_evidence guard, and `ROADMAP.md`'s kill row ("a capability
            # predicate gets merged as a duplicate") tripped on the declared capability
            # shape of Tenshen's own table (PACKAGE.md 7.3 B3). Rule U: unknown is not
            # equal. Row 3c, after an adversarial review round reproduced the merge.
            #
            # **And two EMPTY extents are not a byte-identical extent either.** Row #6's
            # second adversarial round reached the same kill row by the other end of the
            # same expression: `set() == set()`, so two predicates that NOTHING satisfies
            # compared equal, the refusal did not fire, and the merge fell through to the
            # overridable guards again -- reproduced end to end against this registry with
            # two AI-proposed predicates auto-approved at Haiku and merged under two
            # acknowledgements. An empty extent is *no evidence of membership*, not
            # *evidence of identical membership*; INTERFACE.md 5.10 says of the guard one
            # row down that "merging two types about which nothing is known is the single
            # most destructive thing this interface can do", and that is exactly this
            # case with a predicate in it. Rule U again, on the other operand: EMPTY is
            # not EQUAL. Pinned by C10-09.
            knowable = self.caps.indexes_membership
            left_extent = set((await self._extent(namespace, left.name, True))[0])
            right_extent = set((await self._extent(target_ns, right.name, True))[0])
            demonstrably_same = bool(left_extent) and left_extent == right_extent
            if (
                not knowable
                or left.kind != "predicate"
                or right.kind != "predicate"
                or not demonstrably_same
            ):
                return Refusal(
                    "predicate_merge",
                    {
                        "from_extent": sorted(left_extent),
                        "into_extent": sorted(right_extent),
                        "extents_knowable": knowable,
                        "extents_empty": not left_extent and not right_extent,
                        "why": (
                            "both extents are EMPTY, which is no evidence of membership "
                            "rather than evidence of identical membership -- two "
                            "predicates nothing satisfies are not demonstrably duplicates"
                            if knowable and not left_extent and not right_extent
                            else None
                            if knowable
                            else "this backend cannot compute a predicate's extent, so "
                            "two predicates cannot be shown to have identical members: "
                            + (self.caps.reason("indexes_membership") or "")
                        ),
                        "overridable": False,
                    },
                )

        # 3
        if left.kind != right.kind:
            return Refusal(
                "kind_mismatch",
                {"from": left.kind, "into": right.kind, "overridable": False},
            )

        # 4 -- cross-namespace collision is what namespaces exist to preserve.
        if left.namespace != right.namespace:
            return Refusal(
                "cross_namespace_merge",
                {"from": left.namespace, "into": right.namespace, "overridable": False},
            )

        # An acknowledgement that cannot be recorded is refused -- but only AFTER the
        # four non-overridable guards above. A merge those refuse is refused whether or
        # not anything could be written down, and answering `cannot_record_override`
        # there gives the wrong reason for the right outcome: a caller trying to
        # acknowledge past the kill row must be told **predicate_merge, non-overridable**,
        # not that the audit log is missing. Moved here by row 3c, after a capability
        # sweep showed the old position (before guard 1) turning three non-overridable
        # refusals into a capability complaint.
        if acknowledge and not self.caps.stores_events:
            return Refusal(
                "cannot_record_override",
                {"why": self.caps.reason("stores_events"), "acknowledge": list(acknowledge)},
            )

        # 5
        if "retired" in (left.status, right.status) and "retired_operand" not in acknowledge:
            return Refusal(
                "retired_operand",
                {
                    "from_status": left.status,
                    "into_status": right.status,
                    "overridable": True,
                    "acknowledge": "retired_operand",
                },
            )

        # 6 -- the comparison is between the two DEFINITIONS, not the two names: two
        # words that look nothing alike may mean the same thing, and two that look
        # alike often do not. The resolver is asked through its own protocol by
        # handing it the other definition as the thing to match against.
        probe = _DefinitionProbe(name=right.definition, definition=right.definition)
        score = self.resolver.score(
            left.definition,
            ResolveContext(definition_hint=left.definition),
            [probe],
            tier="unspecified",
        )
        divergence = score[0][1] if score else 0.0
        policy = self.policy(namespace)
        threshold = policy.definitions_diverge_threshold
        # Rule U. `threshold is None` means no resolver here can certify that two
        # definitions are near-synonymous, so the answer is "we cannot tell" -- and per
        # 5.10 that blocks rather than warns, exactly like `no_consumer_evidence`. The
        # score is still reported, so an acknowledging human sees what it was.
        # Identical definitions are a FACT, not a judgement, so they need no resolver
        # to certify them. Everything else does.
        identical = " ".join(left.definition.lower().split()) == " ".join(
            right.definition.lower().split()
        )
        certified = identical or (threshold is not None and divergence >= threshold)
        if not certified and "definitions_diverge" not in acknowledge:
            return Refusal(
                "definitions_diverge",
                {
                    "score": divergence,
                    "threshold": threshold,
                    "why": (
                        "no resolver here certifies that two definitions are "
                        "near-synonymous; a lexical similarity score is not that "
                        "judgement (INTERFACE.md 5.10)"
                        if threshold is None
                        else "the definitions are not near-synonymous by this resolver"
                    ),
                    "overridable": True,
                    "acknowledge": "definitions_diverge",
                },
            )

        # 7 -- the one place "we do not know" blocks rather than warns.
        if not left_gates and not right_gates and "no_consumer_evidence" not in acknowledge:
            return Refusal(
                "no_consumer_evidence",
                {
                    "why": "nothing is known to gate on either type, so nothing can be "
                    "said about what this merge would break",
                    "overridable": True,
                    "acknowledge": "no_consumer_evidence",
                },
            )

        now = self._now()
        aliases = tuple(dict.fromkeys(tuple(right.aliases) + (left.name,) + tuple(left.aliases)))
        async with self.adapter.transaction():
            merged = await self.adapter.put_type(
                TypeRecord(**{**right.__dict__, "aliases": aliases, "updated_at": now})
            )
            await self.adapter.put_type(
                TypeRecord(
                    **{
                        **left.__dict__,
                        "status": "retired",
                        "retire_reason": f"merged into {into}: {reason}",
                        "retired_by": merged_by,
                        "retired_at": now,
                        "successor": into,
                        "updated_at": now,
                    }
                )
            )
            await self._append_event(
                namespace,
                "merged",
                merged_by,
                kind=left.kind,
                name=left.name,
                detail={
                    "into": into,
                    "reason": reason,
                    "acknowledge": list(acknowledge),
                },
            )
            await self._append_event(
                target_ns,
                "merged",
                merged_by,
                kind=right.kind,
                name=right.name,
                detail={
                    "from": from_,
                    "reason": reason,
                    "acknowledge": list(acknowledge),
                    "aliases_added": [left.name],
                },
            )
        return MergeResult(
            from_=from_,
            into=into,
            namespace=namespace,
            merged_by=merged_by,
            merged_at=now,
            reason=reason,
            entry=self._written(await self._entry(merged)),
            acknowledged=acknowledge,
            aliases_added=(left.name,),
            # Every merge records what the divergence check actually said, whether it
            # certified, was acknowledged over, or was never able to judge. An auditor
            # asking "how close was this to the line?" has an answer, and a merge that
            # went through on a `None` threshold is visibly one nobody's resolver
            # vouched for. Row 3c: this field used to be permanently empty.
            warnings=(
                f"definitions_similarity:{divergence:.4f}",
                (
                    "definitions_uncertified"
                    if threshold is None
                    else f"definitions_threshold:{threshold}"
                ),
            ),
        )

    # ============================ 5.11 register_consumer / record_use
    async def register_consumer(
        self, consumer: Consumer, *, namespace: str = "default"
    ) -> Consumer | Refusal:
        """The registration is the work; the call is trivial.

        A read-only consumer source -- a checked-in config file, PACKAGE.md 7.3 --
        returns ``Refusal(reason="consumer_source_read_only")``, the fifteenth value of
        INTERFACE.md 5.12's closed vocabulary. Never a silent no-op, which is what
        C11-04 is about. This was deviation D-1: PACKAGE.md 3.4 primitive 10 asked for a
        refusal and R3's fourteen had no value that said it honestly, so 2A raised
        ``NotSupported`` and asked for a ruling. Ruling **R4** added the value.
        """
        rec = ConsumerRecord(
            namespace=namespace,
            consumer_id=consumer.id,
            gate=consumer.gate,
            on_unknown=consumer.on_unknown,
            owner=consumer.owner,
            registered_at=consumer.registered_at or self._now(),
            locator=consumer.locator,
        )
        try:
            stored = await self.adapter.put_consumer(rec)
        except NotSupported as why:
            return Refusal(
                reason="consumer_source_read_only",
                detail={
                    "namespace": namespace,
                    "consumer_id": consumer.id,
                    "why": str(why),
                },
            )
        return Consumer(
            id=stored.consumer_id,
            gate=stored.gate,
            on_unknown=stored.on_unknown,
            owner=stored.owner,
            registered_at=stored.registered_at,
            locator=stored.locator,
            warnings=self._write_warnings(),
        )

    async def record_use(
        self,
        type: str,
        *,
        by: str | None = None,
        at: datetime | None = None,
        namespace: str = "default",
    ) -> None:
        """Explicitly allowed to be a no-op on a backend that does not count -- in
        which case ``usage()`` says so rather than reporting zero."""
        rec = await self._require(namespace, type)
        if not self.caps.counts_usage:
            return
        await self.adapter.bump_usage(
            rec.namespace, rec.kind, rec.name, at=at or self._now(), by=by
        )

    # ============================================ beyond 5: package-local helpers
    async def import_types(
        self,
        rows: Iterable[dict],
        *,
        system: str = "foundry",
        namespace: str = "default",
        kind: str = "entity",
        imported_by: str = "import:foundry",
    ) -> list[TypeEntry]:
        """The Foundry migration mapping of INTERFACE.md 2.5, as a call.

        2.5 states the mapping but no 5.x call performs it, while PACKAGE.md 6.2's C12
        group tests it. Implemented here as a method beyond the twelve. Deviation D-8.

        ``experimental`` maps to **active plus the predicate ``experimental``**, not to
        ``proposed``: a Foundry experimental type has been approved and is in use, and
        collapsing them would silently un-approve a customer's live vocabulary.
        """
        out: list[TypeEntry] = []
        now = self._now()
        for row in rows:
            name = row["name"]
            foundry_status = (row.get("status") or "active").lower()
            predicates = list(row.get("predicates") or ())
            status, retire_reason = "active", None
            if foundry_status == "deprecated":
                status = "retired"
                retire_reason = "imported: foundry deprecated"
            elif foundry_status == "experimental":
                status = "active"
                if "experimental" not in predicates:
                    predicates.append("experimental")

            attributes = dict(row.get("attributes") or {})
            for key in ("visibility", "groups"):
                if key in row:
                    attributes[key] = row[key]

            # EDGES.md 2.4.1 / R18, at the third door. An import cannot return a
            # `Refusal` -- it returns entries -- so a breaching family comes back
            # the way an alias collision does: nothing written, `import_refused`
            # with the reason. Row 3e found `import_types` was a fourth unguarded
            # door into mechanism 4; leaving it as the unguarded door into the kill
            # row would be the same mistake with a different subject.
            edge_breach = self._edge_family_refusal(row.get("kind", kind), attributes)
            if edge_breach is not None:
                out.append(
                    self._refused_import(
                        namespace, name, edge_breach.detail.get("why", ""),
                        reason=edge_breach.reason,
                    )
                )
                continue

            # **An import does not un-retire a local name.** A retired row is a
            # governance decision this deployment made; a foreign dump saying the word
            # is active is not a reversal of it, and overwriting the tombstone wiped
            # `retire_reason`, `retired_by`, `retired_at` and `successor` with no
            # `reinstated` event and none of 5.9b's three guards -- so `import_types`
            # was a fourth, unguarded door into mechanism 4, and it falsified 5.9b's
            # own claim that `reinstate` was the only one. Row 3e, second adversarial
            # round. The behaviour is `propose_type`'s, verbatim (5.9, `C4-08`): the
            # retired entry comes back with `name_previously_retired` and nothing is
            # written. `reinstate` is the call that reverses a retirement, and it is
            # the call that carries the guards.
            standing = await self.adapter.get_type(namespace, name, kind=row.get("kind", kind))
            if standing is not None and standing.status == "retired" and status != "retired":
                out.append(
                    await self._entry(standing, extra_warnings=("name_previously_retired",))
                )
                continue

            # **An import does not retire a type something still gates on, either.**
            # Round 3e's second adversarial round closed the un-retire direction above
            # and left its mirror open: a Foundry `deprecated` row retired a live,
            # consumer-gated type with no refusal, no warning and no `retired` event,
            # while `retire()` refuses the identical act with `live_consumers` (5.9).
            # Row 3e, third adversarial round.
            if standing is not None and status == "retired":
                gated = (await self._consumer_report(standing)).gates_on
                if gated:
                    out.append(
                        await self._entry(standing, extra_warnings=("import_refused:live_consumers",))
                    )
                    continue

            # **And it does not create a second live word for one meaning.** An imported
            # row carries its own `aliases`, and writing one that a live entry already
            # answers to is the state `merge_types`, `propose_type` and `reinstate` all
            # refuse -- reached here in ONE ordinary call, which is why 5.9b's claim
            # that the surface could not otherwise produce it was wrong twice over.
            # Row 3e, third adversarial round. `C16-06` is the mechanical form of this.
            incoming = tuple(row.get("aliases") or ())
            if incoming and status != "retired":
                clash = await self._alias_clash(namespace, name, row.get("kind", kind), incoming)
                if clash is not None:
                    out.append(
                        await self._entry(standing, extra_warnings=("import_refused:alias_collision",))
                        if standing is not None
                        else self._refused_import(namespace, name, clash)
                    )
                    continue

            imported_from = {"system": system}
            for key in ("apiName", "rid"):
                if key in row:
                    imported_from[key] = row[key]

            provenance = Provenance(
                created_at=_ts(row.get("created_at")) or now,
                created_by_actor=imported_by,
                proposed_by=None,
                # Never null on an active type. An imported row has no approver, and
                # saying so is different from leaving the field blank.
                approved_by="unknown:imported",
                approved_at=_ts(row.get("created_at")) or now,
                imported_from=imported_from,
                # R21. A dump has a version and 10b.5's finding is that it had nowhere
                # to go; `imported_from` is foreign SYSTEM identifiers, not a version.
                source_version=row.get("source_version"),
            )
            rec = TypeRecord(
                namespace=namespace,
                kind=row.get("kind", kind),
                name=name,
                definition=row.get("definition") or f"imported from {system}",
                created_by="seed",
                status=status,
                predicates=tuple(predicates),
                aliases=tuple(row.get("aliases") or ()),
                attributes=attributes,
                provenance=_prov_to_dict(provenance),
                warnings=(),
                retire_reason=retire_reason,
                retired_by=imported_by if status == "retired" else None,
                retired_at=now if status == "retired" else None,
                created_at=provenance.created_at,
                updated_at=now,
            )
            async with self.adapter.transaction():
                stored = await self.adapter.put_type(rec)
                await self._observe(stored)
                await self._append_event(
                    namespace,
                    "imported",
                    imported_by,
                    kind=rec.kind,
                    name=name,
                    detail={"system": system, "foundry_status": foundry_status},
                )
            out.append(self._written(await self._entry(stored)))
        return out

    # ===================================================================== edges
    #
    # EDGES.md v0. Three calls -- two writes and ONE read -- plus one package-local
    # helper for an edge's history, which EDGES.md 6 names by implication and never
    # specifies (recorded as a deviation in docs/runs/4B-RUN.md).
    #
    # There is no fourth call to manage FAMILIES, and that absence is the test of
    # EDGES.md 2.3's central decision: a family is a `TypeEntry` with `kind="edge"`,
    # so `propose_type`, `approve`, `resolve_type`, `usage`, `retire`, `reinstate`,
    # `consumers` and `predicates` all serve it unchanged.

    def _edges_absent(self, detail: dict) -> Refusal | None:
        """EDGES.md 4.3's first row. Never an empty report.

        An empty ``NeighborReport`` reads as *"this node has no neighbours"*, which is
        Rule U's forbidden empty list in the one call that would be believed.
        """
        if self.caps.stores_edges:
            return None
        return Refusal(
            "edge_store_absent", {**detail, "why": self.caps.reason("stores_edges")}
        )

    def _edge_write_warnings(self) -> tuple[str, ...]:
        """EDGES.md 6.2, and the word *itself* is the finding.

        Each edge write call site stamps this on its OWN behalf. Round 3 of the spec
        row's loop [Observed] `retract_edge` carrying the warning forward from the
        edge's prior state instead of applying it, so retracting an edge the host had
        already committed came back with **no warning at all** -- a borrowed-connection
        write that looked exactly as durable as an owned one. That is PACKAGE.md 3.4
        primitive 3 note 2's own recorded bug class, one layer up.

        It reads `edge_transaction_scope`, not `transaction_scope`: EDGES.md 6.2 permits
        the two to differ when the edge store is a second connection, and a write to the
        edge store is durable when the EDGE store's owner commits.
        """
        if self.caps.edge_transaction_scope != "savepoint":
            return ()
        return (
            "not_durable_until_host_commits:"
            + self.caps.reason("edge_transaction_scope"),
        )

    async def _edge_family(self, name: str, namespace: str) -> EdgeFamily | None:
        rec = await self.adapter.get_type(namespace, name, kind="edge")
        if rec is None:
            return None
        return EdgeFamily.from_attributes(
            rec.name, rec.namespace, dict(rec.attributes or {}), rec.status
        )

    async def _edge_payload_schema(
        self, namespace: str, fam: EdgeFamily, attributes: dict
    ) -> tuple[AttributeSchema | None, list[str], bool]:
        """The schema governing one edge PAYLOAD -- ruling **R34**, EDGES.md 2.5.

        ``(schema, violations, the named schema is not in force)``.

        PACKAGE.md 5's mechanism verbatim, one kind along: a per-namespace
        ``(namespace, "edge_payload")`` schema governs every edge payload written in
        that namespace, a family's declared ``payload_schema`` name shadows it for that
        family, and R10's **enforcement floor** applies -- an override replaces the
        FIELDS and may never weaken the STRICTNESS. ``_check_attributes`` already
        implements all three, so this call is a lookup and not a second mechanism, which
        is the whole point of transposing rather than inventing.

        **The kind is ``"edge_payload"`` and not ``"edge"``, and the reason is measured
        rather than argued** -- see ``edges.EDGE_PAYLOAD_KIND``. Under 2.5's literal key
        the schema that governs a family's payload is the same schema that governs the
        family's own five declaration keys, and registering one makes the family
        unregisterable. Deviation **D-4c-1**.

        **The third element is Rule U.** A family that names a schema nobody registered
        has not been validated, and neither refusing the write nor validating against
        the per-namespace fallback in silence is honest about that. It is warned.
        """
        schema, violations = await self._check_attributes(
            namespace, EDGE_PAYLOAD_KIND, fam.payload_schema, attributes
        )
        named_missing = fam.payload_schema is not None and (
            schema is None or schema.name != fam.payload_schema
        )
        return schema, violations, named_missing

    async def _observe_edge_payload(
        self, namespace: str, payload: dict, schema_version: int | None
    ) -> None:
        """PACKAGE.md 5.5's floor, applied to edges -- every key ever written, recorded.

        5.5 calls the census *"the floor that applies even in ``off`` mode"* and argues
        it on `attributes` accumulating unwatched. `Edge.attributes` is the same escape
        hatch on the surface that has millions of rows rather than hundreds, so it gets
        the same floor: `attribute_census(kind="edge_payload")` enumerates what edge
        payloads actually carry, in every mode, on every backend that can store them.

        The projection rule (5.7) applies unchanged: only the keys that SURVIVED the
        write are counted, because the census is a report about what got written.
        """
        store = self._attribute_store()
        observed = self.caps.surviving_edge_attributes(payload)
        if store is None or not observed:
            return
        await store.observe_attributes(
            namespace,
            EDGE_PAYLOAD_KIND,
            observed,
            at=self._now(),
            schema_version=schema_version,
        )

    async def _all_edge_families(self) -> tuple[list[EdgeFamily], bool, str | None]:
        """Every registered ``kind="edge"`` entry, in EVERY namespace. EDGES.md 4.1.

        ``edge_families=None`` searches every family the store can answer across every
        namespace, so ``namespace`` is a no-op in that call shape. Scoping it silently
        dropped families registered elsewhere in the spec row's first draft -- **Cause C
        inside the read seam, on the axis UC3 exists to stress** -- and a reviewer
        reproduced it in twenty lines.

        Retired families are included: their edges were not deleted, so they are
        searched (EDGES.md 4.3).

        **Paged to exhaustion, with the same rule everything else here follows:** a
        page the backend could not fully answer makes the report incomplete with the
        backend's own sentence, never a shorter list of families that reads as whole.
        """
        families: list[EdgeFamily] = []
        cursor: str | None = None
        complete = True
        why: str | None = None
        seen_cursors: set[str] = set()
        while True:
            page = await self.adapter.find_types(
                TypeQuery(
                    namespace=None,
                    kind="edge",
                    include_retired=True,
                    limit=_EDGE_PAGE_SIZE,
                    after=cursor,
                )
            )
            if not page.complete and page.next_after is None:
                complete = False
                why = why or page.why_incomplete
            for rec in page.records:
                families.append(
                    EdgeFamily.from_attributes(
                        rec.name, rec.namespace, dict(rec.attributes or {}), rec.status
                    )
                )
            cursor = page.next_after
            if cursor is None or cursor in seen_cursors:
                break
            seen_cursors.add(cursor)
        return families, complete, why

    async def _merged_with(self, ref: TypeRef) -> tuple[tuple[str, ...], str | None]:
        """Type names this one is joined to by a MERGE or a retirement with a successor.

        ``(names, why the look was partial)`` -- and the names are what `neighbors`
        cannot see, not what it searched.

        **The gap this closes was a BLOCKING finding** (row 4b, adversarial round 3).
        `merge_types` is the registry's sanctioned, routine answer to mechanism 4, which
        `EDGES.md` 12 calls co-dominant for this row. It retires one word with the other
        as its `successor` and adds the retired name to the survivor's aliases. **Edges
        already written under the retired name keep naming it** -- `src`/`dst` are
        references by identity triple (2.1) and nothing rewrites them -- so a caller who
        does the CORRECT thing after a merge, resolving to the canonical type and then
        walking, got `known=0`, **`complete=True`** and an empty `warnings`.

        That is the confident, complete, false negative this document treats as
        unacceptable everywhere else (2.2's `direction` finding), and it contradicts
        4.4's own argument for why `complete` may be `True` at all: *"there is no edge
        that exists in the store and is invisible to a query over it."* Across a merge
        there is.

        **What this does and does not do.** It makes the report HONEST -- the walk says
        which other name holds edges it did not search, and `complete` becomes `False`.
        It does **not** follow the chain and return those edges: doing that silently
        would change what `neighbors` means, and whether an edge written under a merged
        word is an edge of its survivor is a decision above this row. Recorded as
        deviation **D-4b-15** and **Q33**.
        """
        seen: list[str] = []
        why: str | None = None

        rec = await self.adapter.get_type(ref.namespace, ref.name, kind=ref.kind)
        if rec is not None and rec.status == "retired" and rec.successor:
            seen.append(rec.successor)

        # The other direction: a RETIRED word whose successor is this one. There is no
        # `successor` filter on `TypeQuery` -- it would be registry policy inside the
        # backend (3.3's rule) -- so the retired rows are read and filtered above,
        # scoped to this namespace and paged to exhaustion, exactly as the collision
        # scan does. Retired rows are the small half of a vocabulary.
        after: str | None = None
        cursors: set[str] = set()
        while True:
            page = await self.adapter.find_types(
                TypeQuery(
                    namespace=ref.namespace,
                    status="retired",
                    include_retired=True,
                    after=after,
                )
            )
            for other in page.records:
                if other.successor == ref.name and other.name not in seen:
                    seen.append(other.name)
            if not page.complete and page.next_after is None:
                why = page.why_incomplete or "the backend could not page the retired types"
                break
            after = page.next_after
            if after is None or after in cursors:
                break
            cursors.add(after)

        # And the aliases `merge_types` writes onto the survivor, which name the words it
        # absorbed. **`stores_aliases=False` does NOT make this a partial look**, and the
        # first version of this said it did: it set a `why` off that flag, which made
        # EVERY walk on such a backend `complete=False` -- a signal that never turns off,
        # which is the exact failure row 3d recorded for the durability warning, produced
        # here by the fix for a false `complete=True`. Caught by the capability matrix
        # within the hour.
        #
        # The reason it is not a partial look: `merge_types` writes BOTH a successor and
        # an alias for the same absorption, and the retired-row scan above reads the
        # successor. Aliases are a second reading of a fact already read, so their
        # absence subtracts nothing from the merge question. They are still consulted,
        # because a hand-written alias is one this scan would otherwise miss.
        if rec is not None and rec.status == "active":
            for alias in rec.aliases:
                if alias not in seen and alias != ref.name:
                    seen.append(alias)
        return tuple(seen), why

    async def add_edge(
        self,
        family: str,
        src: NodeRef,
        dst: NodeRef,
        created_by_actor: str,
        *,
        namespace: str = "default",
        created_by: str = "user",
        confidence: float | None = None,
        evidence: Sequence[Evidence] = (),
        source_version: str | None = None,
        model_tier: str | None = None,
        attributes: dict | None = None,
    ) -> Edge | Refusal:
        """Write one edge. EDGES.md 2.2, 2.4.1, 2.6, 2.7.

        There is **no approval loop for an individual edge** and EDGES.md 2.6 argues it
        rather than assuming it: a single edge is a fact about two things, not a claim
        about the vocabulary; there are millions of them; and beacon writes them from a
        weekly scheduled job with no human in the loop. The governance lives one level
        up, on the family, where it is affordable and where it bites.

        The registry mints ``edge_id`` -- PACKAGE.md 4.2's rule for ``proposal_id`` and
        ``event_id``, unchanged -- which is why there is no uniqueness capability flag
        for an adapter to declare.
        """
        refusal = self._edges_absent({"family": family, "namespace": namespace})
        if refusal is not None:
            return refusal

        fam = await self._edge_family(family, namespace)
        if fam is None:
            # EDGES.md 4.3: a named family that is not a registered kind="edge" entry in
            # the namespace it was resolved in. `namespace`'s one job is resolving the
            # name, and a family registered elsewhere is a different family.
            return Refusal("edge_family_unknown", {"families": [family], "namespace": namespace})

        if fam.level not in EDGE_LEVELS:
            # EDGES.md 2.4: `level` is REQUIRED with no default -- "a family that does
            # not say is a family whose edges cannot be validated". The TypeEntry is
            # still perfectly legal (INTERFACE.md 2.1 requires no attributes, and
            # beacon's `work_link_types` rows carry none of the five), so the refusal is
            # here at WRITE time rather than at registration: refusing the registration
            # would make this row reject types INTERFACE.md says are legal, on the data
            # of the one real host. The door this leaves -- declare nothing, then write
            # anything -- is the one being shut right here.
            return Refusal(
                "attributes_schema_violation",
                {
                    "family": family,
                    "namespace": namespace,
                    "missing": ["level"],
                    "declared_level": fam.level,
                    "rule": "EDGES 2.4",
                    "why": (
                        f"the kind='edge' entry {namespace}:{family} declares no `level`, "
                        "so its edges cannot be validated and none may be written"
                    ),
                },
            )

        breach = family_declaration_problem(
            {
                "level": fam.level,
                "symmetric": fam.symmetric,
                "inverse_label": fam.inverse_label,
                "endpoint_kinds": {k: list(v) for k, v in fam.endpoint_kinds.items()},
            }
        )
        if breach is not None:
            # Belt and braces. `propose_type`, `approve` and `import_types` all refuse a
            # breaching declaration, so reaching this means the row was written by a
            # path that predates the rule or by a host that owns the schema -- and the
            # kill row is on the other side of it, so it is checked twice rather than
            # once.
            reason, sentence, detail = breach
            return Refusal(reason, {**detail, "family": family, "why": sentence})

        for end, node in (("src", src), ("dst", dst)):
            # **Level first, and the order is not arbitrary**: a level mismatch makes
            # the kind question meaningless. A `value_set` reached as a TypeRef where the
            # family wants an InstanceRef is refused on `level`, and the detail says so,
            # which is what UC2's T2.5 observed and what made the two enforcement layers
            # visible in the first place.
            if level_of(node) != fam.level:
                return Refusal(
                    "endpoint_kind_mismatch",
                    {
                        "endpoint": end,
                        "problem": "level",
                        "family_level": fam.level,
                        "node_level": level_of(node),
                        "node": str(node),
                    },
                )
            kind = type_of(node).kind
            if kind not in fam.endpoint_kinds[end]:
                return Refusal(
                    "endpoint_kind_mismatch",
                    {
                        "endpoint": end,
                        "problem": "kind",
                        "declared": list(fam.endpoint_kinds[end]),
                        "node_kind": kind,
                        "node": str(node),
                    },
                )

        if family == EQUIVALENT_TO and type_of(src).kind != type_of(dst).kind:
            # EDGES.md 3.1's family-specific constraint, beyond `endpoint_kinds`: an
            # `entity` is not equivalent to a `value_set`. `facility == deficiency_
            # corrected_status` is a category error, not a claim.
            #
            # Hard-coded to the one family this row ships, because 2.4.1 says plainly
            # that this is "that family's semantics and not a general mechanism". A
            # declarable `same_kind_endpoints` key would be a sixth attribute invented
            # for one family, which is how a declared shape starts growing a rule
            # language. Recorded as **Q27**.
            return Refusal(
                "endpoint_kind_mismatch",
                {
                    "problem": "family_constraint",
                    "family": EQUIVALENT_TO,
                    "src_kind": type_of(src).kind,
                    "dst_kind": type_of(dst).kind,
                    "why": (
                        "equivalent_to requires src.kind == dst.kind (EDGES.md 3.1)"
                    ),
                },
            )

        # ---- EDGES.md 2.5, ruling **R34**: the payload is VALIDATED, and this is the
        # one declared field of the edge model that had a name and no mechanism.
        #
        # PACKAGE.md 5's three modes, unchanged and not re-argued: `off` checks nothing
        # (the default, so an untouched deployment behaves exactly as row 4b shipped),
        # `warn` writes the edge and enumerates the violations, `enforce` refuses.
        # `attributes_schema_version` on the Edge records the version in force at the
        # write, so 5.4's promise -- entries written under an older schema are never
        # rewritten and never retroactively invalidated; they are OLDER ROWS -- holds
        # for edges too.
        #
        # **Validated against what the CALLER wrote, not against what survives storage**,
        # which is the type side's order (`_write_approved` checks `rec.attributes`) and
        # is the honest one: a `required` field the backend cannot store is the
        # backend's declared loss (EDGES.md 6, `stores_edge_attributes`), not the
        # caller's schema violation, and reporting it as the latter would blame a
        # writer for a column somebody else's schema does not have.
        payload_in = dict(attributes or {})
        payload_schema, violations, schema_unregistered = await self._edge_payload_schema(
            namespace, fam, payload_in
        )
        if violations and payload_schema is not None and payload_schema.mode == "enforce":
            # INTERFACE.md 5.12's existing value -- no new refusal is minted, because
            # this IS `attributes_schema_violation`: the same mechanism, one kind along.
            # `detail` names which schema refused, per PACKAGE.md 5.2b rule 4, with the
            # family added because two families in one namespace may be judged by two
            # different schemas.
            return Refusal(
                "attributes_schema_violation",
                {
                    "kind": EDGE_PAYLOAD_KIND,
                    "family": family,
                    "namespace": namespace,
                    "violations": violations,
                    "schema_version": payload_schema.version,
                    "schema_name": payload_schema.name,
                    "why": (
                        f"the payload of an edge on {namespace}:{family} is governed by "
                        f"the attribute schema {payload_schema.name or '(per-namespace)'} "
                        f"v{payload_schema.version} in enforce mode (EDGES.md 2.5, R34)"
                    ),
                },
            )

        warnings: list[str] = []
        if schema_unregistered:
            # Rule U. The family declares a payload schema and no schema of that name is
            # in force, so this edge was NOT validated against the thing its family
            # names -- and a declared field pointing at nothing, unreported, is the
            # inert `payload_schema` this ruling exists to end.
            warnings.append(f"payload_schema_unregistered:{fam.payload_schema}")
        if violations and payload_schema is not None and payload_schema.mode == "warn":
            # PACKAGE.md 5.3's `warn` row, on one more carrier: the write succeeds and
            # the entry is thereafter enumerable. Same value as the type side, because
            # it is the same fact.
            warnings.extend(f"attributes_invalid:{v}" for v in violations)
        for node in (src, dst):
            # EDGES.md 2.7. `endpoint_kind_mismatch` can only fire when the endpoint's
            # type IS registered; on an unregistered one the registry cannot know the
            # kind, so it does not guess. Rule U -- a positive claim about a mismatch
            # requires having looked -- and the same `<value>:<subject>` shape as
            # `gate_unregistered` (ruling R8), deliberately.
            t = type_of(node)
            if await self.adapter.get_type(t.namespace, t.name, kind=t.kind) is None:
                warnings.append(f"endpoint_type_unregistered:{t}")
        if fam.status == "retired":
            # EDGES.md 2.8, second carrier. Writing an edge onto a RETIRED family is
            # not refused -- retirement is a statement about the vocabulary and the
            # edge is a fact about two things -- but a caller who has just written
            # under a word somebody withdrew is entitled to know. 2.8's table listed
            # only `NeighborReport` for this value until row 4b's second adversarial
            # round found the code emitting it here as well: a carrier minted by
            # implementation, which is the closed vocabulary opening by code rather
            # than by prose. Added to 2.8 in the same change, per ruling R3.
            warnings.append(f"edge_family_retired:{family}")
        warnings.extend(self._edge_write_warnings())

        now = self._now()
        provenance = EdgeProvenance(
            created_at=now,
            created_by_actor=created_by_actor,
            created_by=created_by,
            confidence=confidence,
            evidence=tuple(evidence),
            source_version=source_version,
            model_tier=model_tier,
            history_why=_EDGE_HISTORY_WHY,
        )
        payload = self.caps.surviving_edge_attributes(payload_in)
        edge_id = _uuid()
        async with self.adapter.transaction():
            stored = await self.adapter.put_edge(
                _edge_to_record(
                    Edge(
                        edge_id=edge_id,
                        family=family,
                        namespace=namespace,
                        src=src,
                        dst=dst,
                        provenance=provenance,
                        attributes=payload,
                        warnings=tuple(warnings),
                        attr_schema_version=(
                            payload_schema.version if payload_schema else None
                        ),
                    )
                ),
                expect_absent=True,
            )
            await self._observe_edge_payload(
                namespace, payload_in, payload_schema.version if payload_schema else None
            )
            await self._append_event(
                namespace, "edge_added", created_by_actor, edge_id=edge_id,
                detail={"family": family, "src": str(src), "dst": str(dst)},
            )
        return _edge_from_record(stored, extra_warnings=tuple(warnings))

    async def retract_edge(self, edge_id: str, reason: str, *, retracted_by: str) -> Edge | Refusal:
        """EDGES.md 2.6. Nothing is deleted; the row stays and an event is appended.

        **Not refused when the store cannot record events, and that is a departure from
        PACKAGE.md 3.6 that is argued rather than assumed.** 3.6's rule is that a
        destructive override which cannot be recorded is refused. Retraction is
        different in the way that rule cares about: **the record IS the row.**
        ``status``, ``retracted_by``, ``retracted_at`` and the reason are columns on the
        edge itself, so an unrecordable retraction does not exist. What is lost without
        events is the *sequence* -- retracted, reinstated, retracted again -- and that is
        surfaced as a warning.

        There is no reinstatement, by ruling **R19**: R11's ``reinstate`` covers edge
        FAMILIES, which are ``TypeEntry``s, and never edge instances. A retracted edge
        is no claim (EDGES.md 3.2); re-asserting it is a new edge whose provenance cites
        the retracted one.
        """
        if not reason or not reason.strip():
            # INTERFACE.md 5.5's reason, unchanged: the cheapest record of "we already
            # considered this and decided against it". A caller error, not a policy
            # refusal, so the closed vocabulary does not grow a value for it.
            raise ValueError("retract_edge requires a non-empty reason (EDGES.md 2.6)")
        refusal = self._edges_absent({"edge_id": edge_id})
        if refusal is not None:
            return refusal

        async with self.adapter.transaction():
            rec = await self.adapter.get_edge(edge_id)
            if rec is None:
                # The nineteenth value of INTERFACE.md 5.12. It reused
                # `edge_family_unknown` until round 3 of the spec row's loop, which
                # names a different failure -- EDGES.md 2.3's own Cause B, committed
                # inside a document that argues at length against reusing `kind_mismatch`
                # for two things.
                return Refusal("unknown_edge", {"edge_id": edge_id})
            now = self._now()
            # The edge's own warnings are carried VERBATIM, duplicates included: two
            # `endpoint_type_unregistered` entries mean two endpoints were unregistered,
            # and collapsing them would turn "both ends" into "one end" on the one
            # shape where the two endpoints share a type.
            #
            # The two durability-and-trail values are the exception, stripped and then
            # recomputed, because they are statements about THIS call.
            warnings = [
                w
                for w in rec.warnings
                if not w.startswith("not_durable_until_host_commits:")
                and not w.startswith("retracted_without_event_trail:")
            ]
            # Stamped HERE, on this call's own behalf -- never carried forward from the
            # edge's prior state. See `_edge_write_warnings`.
            fresh_warnings = list(self._edge_write_warnings())
            if not self.caps.stores_edge_events:
                fresh_warnings.append(
                    "retracted_without_event_trail:"
                    + self.caps.reason("stores_edge_events")
                )
            warnings.extend(w for w in fresh_warnings if w not in warnings)
            provenance = dict(rec.provenance or {})
            provenance.update(
                {
                    "retracted_by": retracted_by,
                    "retracted_at": _iso(now),
                    "retract_reason": reason,
                }
            )
            stored = await self.adapter.put_edge(
                replace(
                    rec,
                    status="retracted",
                    warnings=tuple(warnings),
                    provenance=provenance,
                    retract_reason=reason,
                    retracted_by=retracted_by,
                    retracted_at=now,
                )
            )
            await self._append_event(
                rec.namespace, "edge_retracted", retracted_by, edge_id=edge_id,
                detail={"reason": reason, "family": rec.family},
            )
        return _edge_from_record(stored)

    async def amend_edge(
        self,
        edge_id: str,
        reason: str,
        *,
        amended_by: str,
        confidence: Any = UNCHANGED,
        attributes: Any = UNCHANGED,
        model_tier: Any = UNCHANGED,
        source_version: Any = UNCHANGED,
        evidence: Any = UNCHANGED,
    ) -> Edge | Refusal:
        """EDGES.md 5.2 -- **a correction is a new event, never an edit of the first.**

        Ruling **R37**, row 4c. 5.2 narrated `edge_amended` with a worked example --
        *"changing an edge's `confidence` after a re-classification is a new
        `edge_amended` event carrying the old and new values"* -- and v0 had **no amend
        call at all**; only `edge_added` and `edge_retracted` were ever appended. Row 4b
        recorded that as deviation **D-4b-13** and asked **Q32**: give edges an amend
        path, or delete the example. R34 settled which, because *"an edge whose payload
        is validated is an edge somebody will want to correct."*

        **The question this call had to answer before it could be written: is an amend
        path a second WRITE path in disguise?** That is the shape of the kill row's
        third trip -- `retire(successor=)` reaching `merge_types`' outcome with none of
        `merge_types`' guards -- so the question is not rhetorical. Three answers, and
        all three are structural rather than promised:

        1. **`family`, `src` and `dst` are not parameters.** An amend cannot move an
           endpoint, change a family or reify anything, so EDGES.md 2.4.1's declaration
           and write-time checks have nothing to be talked around. Re-pointing an edge
           is `retract_edge` plus `add_edge`, which 3.2 already names as the shape of
           re-assertion: *a retracted edge is no claim; re-asserting it is a new edge
           whose provenance cites the retracted one.*
        2. **`attributes` goes back through R34's payload validation, on the same terms
           as `add_edge`.** An amend that skipped it would be exactly the defect the
           kill row's third trip is: a guard written for one call over a fact that more
           than one call can change. `attr_schema_version` is re-stamped with the
           version in force at the amendment, so the row still says which generation of
           the payload it holds.
        3. **`status` is not a parameter either**, and a retracted edge is refused
           `already_decided`. A retracted edge is no claim (3.2); amending one asserts
           something about a claim that was withdrawn, and un-retracting through the
           back door is `retract_edge`'s guard being talked around.

        **It is REFUSED when the event cannot be recorded, and that is the one place it
        does NOT follow `retract_edge`.** 2.6 argues retraction past PACKAGE.md 3.6
        because *"the record IS the row"* -- `status`, `retracted_by`, `retracted_at`
        and the reason are columns on the edge itself. **That argument does not
        transpose**: there is no column holding an edge's PRIOR confidence, so on
        `stores_edge_events=False` an amendment erases the old value with no record
        anywhere that it ever held one. That is PACKAGE.md 3.6's rule verbatim -- *a
        destructive override that cannot be recorded is refused* -- and it is
        `reinstate`'s shape exactly (3.6's own box: it clears fields off the live row,
        which makes its event the only record). So `cannot_record_override` is the
        answer and **no new `Refusal.reason` is minted**: the fourth caller of an
        existing, argued rule rather than an exemption from it.

        Both flags are checked, per the lesson `edge_provenance` paid for: `stores_events`
        gates the same `append_event` primitive `stores_edge_events` describes, and
        nothing ties the two declarations together.
        """
        if not reason or not reason.strip():
            # INTERFACE.md 5.5's reason, as `retract_edge` takes it: the cheapest record
            # of why a decision was made. A caller error, not a policy refusal.
            raise ValueError("amend_edge requires a non-empty reason (EDGES.md 5.2)")
        fields = {
            "confidence": confidence,
            "attributes": attributes,
            "model_tier": model_tier,
            "source_version": source_version,
            "evidence": evidence,
        }
        changing = {k: v for k, v in fields.items() if v is not UNCHANGED}
        if not changing:
            # A call that quietly did nothing is the shape ruling R4 forbade for
            # `register_consumer`, and an `edge_amended` event recording no amendment is
            # a trail entry asserting a correction nobody made.
            raise ValueError(
                "amend_edge changes at least one of confidence, attributes, model_tier, "
                "source_version, evidence -- passing none of them would append an "
                "`edge_amended` event recording no amendment (EDGES.md 5.2)"
            )
        refusal = self._edges_absent({"edge_id": edge_id})
        if refusal is not None:
            return refusal
        for flag in ("stores_edge_events", "stores_events"):
            if not getattr(self.caps, flag):
                return Refusal(
                    "cannot_record_override",
                    {
                        "why": self.caps.reason(flag),
                        "edge_id": edge_id,
                        "flag": flag,
                        "amending": sorted(changing),
                        "note": (
                            "an amendment overwrites a provenance value on the row and "
                            "the event is the only record of what it was -- EDGES.md "
                            "2.6's 'the record IS the row' argument covers RETRACTION, "
                            "where status, retracted_by, retracted_at and the reason are "
                            "columns, and there is no column for a prior confidence. "
                            "Retract and re-assert instead (EDGES.md 3.2)"
                        ),
                        "overridable": False,
                    },
                )

        async with self.adapter.transaction():
            rec = await self.adapter.get_edge(edge_id)
            if rec is None:
                return Refusal("unknown_edge", {"edge_id": edge_id})
            if rec.status != "active":
                # Read inside the transaction, exactly as `approve`'s `already_decided`
                # is, and for the same reason: it is what turns a race into an
                # idempotent refusal.
                return Refusal(
                    "already_decided",
                    {
                        "edge_id": edge_id,
                        "status": rec.status,
                        "retracted_by": rec.retracted_by,
                        "retracted_at": _iso(rec.retracted_at),
                        "why": (
                            "a retracted edge is no claim (EDGES.md 3.2), so amending "
                            "one asserts something about a claim that was withdrawn; "
                            "re-assertion is a new edge whose provenance cites this one"
                        ),
                    },
                )

            fam = await self._edge_family(rec.family, rec.namespace)
            before = _edge_from_record(rec)
            payload_before = dict(before.attributes)
            payload_after = (
                dict(attributes or {}) if "attributes" in changing else payload_before
            )
            schema_version = rec.attr_schema_version
            warnings = [
                w
                for w in rec.warnings
                if not w.startswith("not_durable_until_host_commits:")
                and not w.startswith("attributes_invalid:")
                and not w.startswith("payload_schema_unregistered:")
            ]
            if "attributes" in changing:
                if fam is None:
                    # The family was there when the edge was written and is not now.
                    # 2.7's argument is about ENDPOINTS, not about the family whose
                    # rules this call has to apply, and validating a payload against a
                    # schema we cannot find is a claim we cannot make.
                    return Refusal(
                        "edge_family_unknown",
                        {
                            "families": [rec.family],
                            "namespace": rec.namespace,
                            "edge_id": edge_id,
                            "why": (
                                "this edge's family is no longer a registered "
                                "kind='edge' entry, so its payload cannot be validated "
                                "against what the family declares (EDGES.md 2.5)"
                            ),
                        },
                    )
                schema, violations, unregistered = await self._edge_payload_schema(
                    rec.namespace, fam, payload_after
                )
                if violations and schema is not None and schema.mode == "enforce":
                    # R34's guard, on the second door. An amend that skipped it would be
                    # the kill row's third trip in miniature: a guard written for one
                    # call over a fact more than one call can change.
                    return Refusal(
                        "attributes_schema_violation",
                        {
                            "kind": EDGE_PAYLOAD_KIND,
                            "family": rec.family,
                            "namespace": rec.namespace,
                            "edge_id": edge_id,
                            "violations": violations,
                            "schema_version": schema.version,
                            "schema_name": schema.name,
                            "why": (
                                "an amendment's payload is validated on exactly the "
                                "terms add_edge's is (EDGES.md 2.5, ruling R34)"
                            ),
                        },
                    )
                if unregistered:
                    warnings.append(f"payload_schema_unregistered:{fam.payload_schema}")
                if violations and schema is not None and schema.mode == "warn":
                    warnings.extend(f"attributes_invalid:{v}" for v in violations)
                schema_version = schema.version if schema else None

            provenance = dict(rec.provenance or {})
            recorded: dict[str, Any] = {}
            for key in ("confidence", "model_tier", "source_version"):
                if key in changing:
                    recorded[key] = {"before": provenance.get(key), "after": changing[key]}
                    provenance[key] = changing[key]
            if "evidence" in changing:
                after_evidence = [_evidence_to_dict(e) for e in (evidence or ())]
                recorded["evidence"] = {
                    "before": list(provenance.get("evidence") or []),
                    "after": after_evidence,
                }
                provenance["evidence"] = after_evidence
            if "attributes" in changing:
                recorded["attributes"] = {
                    "before": payload_before,
                    "after": payload_after,
                }

            payload = self.caps.surviving_edge_attributes(payload_after)
            warnings.extend(
                w for w in self._edge_write_warnings() if w not in warnings
            )
            stored = await self.adapter.put_edge(
                replace(
                    rec,
                    attributes=payload,
                    attr_schema_version=schema_version,
                    provenance=provenance,
                    warnings=tuple(warnings),
                    updated_at=self._now(),
                )
            )
            if "attributes" in changing:
                await self._observe_edge_payload(rec.namespace, payload_after, schema_version)
            # 5.2's own example, as a record: the event carries the OLD and NEW values.
            # The first event's `created_by_actor` stays whatever it was, because this is
            # an append and not an edit -- INTERFACE.md 5.8, unchanged for edges.
            await self._append_event(
                rec.namespace,
                "edge_amended",
                amended_by,
                edge_id=edge_id,
                detail={"reason": reason, "family": rec.family, "changed": recorded},
            )
        return _edge_from_record(stored)

    async def edge_provenance(self, edge_id: str) -> EdgeProvenance | Refusal:
        """One edge's provenance, with its event history. Package-local.

        EDGES.md 6's capability table promises that ``stores_edge_events=False`` gives
        ``provenance(edge).history == []`` **with the `why`** -- and EDGES.md specifies
        no such call anywhere. Supplied here rather than left as a sentence nothing
        implements, and package-local rather than a fifteenth INTERFACE.md 5 call, the
        same standing `attribute_census` and `import_types` have. Recorded as a
        deviation in docs/runs/4B-RUN.md.

        It is a separate call and not a field `neighbors` fills, because filling it
        there would be one `read_events` per edge in the report -- on the 9.7M-degree
        node EDGES.md 4.2 measures, that is the whole reason the read seam is bounded.
        """
        refusal = self._edges_absent({"edge_id": edge_id})
        if refusal is not None:
            return refusal
        rec = await self.adapter.get_edge(edge_id)
        if rec is None:
            return Refusal("unknown_edge", {"edge_id": edge_id})
        edge = _edge_from_record(rec)
        # **Both flags, and checking only one of them raised** (row 4b, adversarial
        # round 2). `read_events` is the SAME primitive `stores_events` gates, and
        # nothing in EDGES.md 6 or PACKAGE.md 3.2 ties the two declarations together
        # -- so a conformant third-party adapter may declare `stores_edges=True`,
        # `stores_edge_events=True` and `stores_events=False`, and this call went
        # straight into an uncaught `NotSupported`. Neither reference backend can
        # produce that combination, which is exactly why nothing caught it.
        #
        # A declined capability degrades to an honest empty plus a `why`; it never
        # raises. `_events()` -- the type-side twin -- has always checked
        # `stores_events` first, and this now does the same.
        for flag in ("stores_edge_events", "stores_events"):
            if not getattr(self.caps, flag):
                return replace(
                    edge.provenance,
                    history=(),
                    history_why=self.caps.reason(flag),
                )
        rows = await self.adapter.read_events(rec.namespace, edge_id=edge_id)
        return replace(
            edge.provenance,
            history=tuple(
                ProvenanceEvent(
                    at=r.at, actor=r.actor, event=r.event, detail=dict(r.detail or {})
                )
                for r in rows
            ),
            history_why=None,
        )

    # ------------------------------------------------------------- 4, the read seam
    async def neighbors(
        self,
        node: NodeRef,
        edge_families: Sequence[str] | None = None,
        depth: int = 1,
        *,
        namespace: str,
        direction: str = "both",
        include_retracted: bool = False,
    ) -> NeighborReport | Refusal:
        """EDGES.md 4. The one read call: edges and the nodes they reach, bounded at 2.

        ``namespace`` is required and keyword-only, and it names the namespace **the
        ``edge_families`` argument is resolved in** -- not the origin's, which the origin
        carries itself, and not a filter on results. Making it required rather than
        defaulting to ``"default"`` is deliberate: UC3's whole subject is that
        ``"default"`` is a wrong answer nobody notices.

        **It returns reachability. It never returns entailment.** ``equivalent_to`` is
        non-transitive, so a depth-2 result is not a depth-1 claim, and ``at_depth`` on
        every edge is what gives a consumer the means not to make that inference.
        """
        # **The shape checks come first, and their absence was a BLOCKING finding**
        # (row 4b, adversarial round 3). This is the one call the whole document is
        # built around, and it had no input validation at all: `depth=1.5` sailed past
        # the range guard below and blew up three frames later inside `range()`, a
        # `node` that was a plain string died on `.namespace` deep in the walk, and
        # `edge_families="blocks"` -- a bare `str` satisfies `Sequence[str]`, which is
        # the most natural mistake in Python -- was iterated CHARACTER BY CHARACTER and
        # refused with `detail={"families": ["b","l","o","c","k","s"]}`, actively
        # misleading the caller about what they had got wrong.
        #
        # 4.2 promises a `ValueError` for a caller's mistake, and a raw `TypeError` from
        # three frames down is not that promise kept.
        if not isinstance(node, (TypeRef, InstanceRef)):
            raise TypeError(
                f"node must be a TypeRef or an InstanceRef (EDGES.md 2.1); got "
                f"{type(node).__name__}"
            )
        if isinstance(edge_families, str):
            raise TypeError(
                "edge_families is a sequence of family names, not one name: a bare str "
                "satisfies Sequence[str] and would be read one character at a time. "
                f"Pass [{edge_families!r}]"
            )
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}; got {direction!r}")
        # `bool` is an `int` in Python, and `neighbors(node, families, True)` is a typo
        # that would otherwise read as depth 1.
        if not isinstance(depth, int) or isinstance(depth, bool):
            raise ValueError(
                f"depth is an int, 1 or {DEPTH_CAP} (EDGES.md 4.2); got "
                f"{type(depth).__name__} {depth!r}"
            )
        if depth < 1 or depth > DEPTH_CAP:
            # EDGES.md 4.2. `ValueError`, not a `Refusal`: a caller error like
            # INTERFACE.md 5.4's empty definition, and R3's closed vocabulary should not
            # grow a value for a typo. The cap and R13's no-paging rule are ONE decision.
            raise ValueError(
                f"depth must be 1 or {DEPTH_CAP} (EDGES.md 4.2, the cap is R13's "
                f"consequence); got {depth}"
            )
        refusal = self._edges_absent({"node": str(node), "namespace": namespace})
        if refusal is not None:
            return refusal

        warnings: list[str] = []
        complete = True
        why: str | None = None

        # --- which families, and the `None` case spans every namespace (EDGES.md 4.1)
        if edge_families is None:
            known, families_complete, families_why = await self._all_edge_families()
            searched = tuple(sorted({f.name for f in known}))
            symmetric = {(f.namespace, f.name) for f in known if f.symmetric}
            registered = {(f.namespace, f.name) for f in known}
            # `None` means EVERY family the store can answer, so there is no
            # searched set to narrow against -- including the families of edges
            # nobody registered, which is why this is `None` and not `registered`.
            searched_keys: set[tuple[str, str]] | None = None
            query_namespace: str | None = None
            query_families: tuple[str, ...] | None = None
            if not families_complete:
                complete = False
                why = (
                    "the backend could not enumerate every kind='edge' entry, so which "
                    "families were searched is itself partial: "
                    + (families_why or "no reason given by the backend")
                )
        else:
            resolved: list[EdgeFamily] = []
            unknown: list[str] = []
            for name in dict.fromkeys(edge_families):
                fam = await self._edge_family(name, namespace)
                if fam is None:
                    unknown.append(name)
                else:
                    resolved.append(fam)
            if unknown:
                # EDGES.md 4.3: the WHOLE call, not a partial answer. A caller that
                # names a family and gets a report back is entitled to believe the
                # family was searched, and a typo'd name returning a clean empty set is
                # mechanism C committed by the read seam.
                return Refusal(
                    "edge_family_unknown", {"families": unknown, "namespace": namespace}
                )
            searched = tuple(edge_families)
            symmetric = {(f.namespace, f.name) for f in resolved if f.symmetric}
            registered = {(f.namespace, f.name) for f in resolved}
            searched_keys = set(registered)
            query_namespace = namespace
            query_families = tuple(sorted({f.name for f in resolved}))
            for fam in resolved:
                if fam.status == "retired":
                    # Not a refusal: its edges were not deleted, so it is searched and
                    # the caller is told (EDGES.md 4.3).
                    warnings.append(f"edge_family_retired:{fam.name}")

        origin_type = type_of(node)
        # EDGES.md 4.3, rule 4.3-14. Cheap: one paged read of this namespace's retired
        # rows, and only for the origin -- a frontier node reached at depth 2 was
        # reached BY a stored edge, so its name is the name the store holds.
        merged, merged_why = await self._merged_with(origin_type)
        if merged:
            warnings.append(f"endpoint_type_merged:{origin_type}")
            complete = False
            why = why or (
                f"{origin_type} is joined by a merge or a retirement-with-successor to "
                + ", ".join(sorted(merged))
                + ", and edges written under those names are NOT searched: an edge's "
                "endpoints are references by identity triple (EDGES.md 2.1) and a merge "
                "rewrites none of them. Walk the other name too (EDGES.md 4.3, Q33)"
            )
        elif merged_why:
            # Rule U on the look itself: a backend that could not page its retired rows
            # has not told us there is no merge, only that it could not say.
            complete = False
            why = why or (
                "whether this origin's type is joined to another by a merge could not "
                "be determined: " + merged_why
            )

        if await self.adapter.get_type(
            origin_type.namespace, origin_type.name, kind=origin_type.kind
        ) is None:
            # EDGES.md 4.3. Not an error: the registry has no node store, so it cannot
            # distinguish *a node with no edges* from *a node that does not exist*, and
            # raising would require inventing a fact. `UnknownType`'s reasoning does not
            # transpose, and 4.3 says which of the two project rules wins and why.
            warnings.append(f"origin_type_unregistered:{origin_type}")

        # `direction` is pushed to the adapter ONLY when nothing in scope is symmetric.
        # For a symmetric family there is no in and no out (EDGES.md 2.2), so filtering
        # on stored src/dst would make the answer depend on which publisher happened to
        # write the edge first -- a confident, complete, FALSE negative. With any
        # symmetric family in scope the adapter is asked for both orientations and the
        # narrowing happens per family, above, which is why this is a per-family rule
        # rather than a per-call refusal: a mixed query over one symmetric and one
        # directed family is the ordinary case.
        push_direction = "both" if (symmetric or edge_families is None) else direction

        seen: dict[str, NeighborEdge] = {}
        frontier: list[NodeRef] = [node]
        visited = {str(node)}
        depth_reached = 0
        bound_hit = False

        for level in range(1, depth + 1):
            if not frontier or bound_hit:
                break
            frontier_keys = tuple(dict.fromkeys(node_key(n) for n in frontier))
            fresh: dict[str, Edge] = {}
            cursor: str | None = None
            cursors_seen: set[str] = set()
            while True:
                page = await self.adapter.find_edges(
                    EdgeQuery(
                        namespace=query_namespace,
                        families=query_families,
                        incident_to=frontier_keys,
                        direction=push_direction,
                        include_retracted=include_retracted,
                        limit=_EDGE_PAGE_SIZE,
                        after=cursor,
                    )
                )
                if not page.complete and page.next_after is None:
                    # A page that is incomplete AND has a cursor is just a page; the
                    # loop below reads the rest. A page that is incomplete with NO
                    # cursor is the residual case -- the rest cannot be read -- and that
                    # is what makes the report incomplete.
                    complete = False
                    why = why or page.why_incomplete
                for rec in page.records:
                    if rec.edge_id in seen or rec.edge_id in fresh:
                        # **Deduplicated BEFORE the bound is consulted**, and that
                        # ordering was a BLOCKING finding of the spec row's round 3: the
                        # bound was compared against each raw page, and at depth >= 2 a
                        # frontier legitimately re-finds edges already counted at depth
                        # 1 -- so a walk of 19 distinct edges under a bound of 20 stopped
                        # at depth 1, returned 15, and reported complete=False with a
                        # `why` naming a bound nothing had crossed. Two failures in one:
                        # four real edges silently dropped, and a false claim in the one
                        # field 4.2 promises will tell the truth.
                        continue
                    keep, note = self._edge_passes(
                        rec, frontier_keys, direction, searched_keys, registered, symmetric
                    )
                    if note is not None and note not in warnings:
                        warnings.append(note)
                    if not keep:
                        continue
                    fresh[rec.edge_id] = _edge_from_record(rec)
                if self.max_edges is not None and len(seen) + len(fresh) > self.max_edges:
                    # **Strictly greater, and the `=` in `>=` was a BLOCKING finding**
                    # (row 4b, adversarial round 2). A walk of exactly `max_edges`
                    # distinct edges has had NOTHING truncated -- every edge that
                    # exists was returned and the adapter's own last page came back
                    # with `next_after=None` -- and it reported `complete=False` with
                    # a `why` naming a bound nothing had crossed. That is round 3's
                    # B7 exactly, on the one axis its fix never tried: the previous
                    # test exercised 19-under-20 and 19-under-5 and never `==`.
                    #
                    # **A false claim in the field 4.2 promises will tell the truth is
                    # worse than no bound**, because the deployment reading it
                    # concludes the bound is too tight when the store had the whole
                    # answer. The per-edge guard below is still `>=` and still caps
                    # `known` at exactly `max_edges`; the two cannot disagree, because
                    # reaching the guard requires this line to have fired first.
                    bound_hit = True
                    break
                cursor = page.next_after
                if cursor is None:
                    break
                if cursor in cursors_seen:
                    # A backend whose `next_after` points at rows it has already
                    # returned. C0-10 asked "can a BROKEN backend pass?" of the type
                    # side; the answer here must not be "it hangs". The walk stops and
                    # says why, rather than looping forever on a cursor that never
                    # advances.
                    complete = False
                    why = why or (
                        "this backend returned a pagination cursor it had already "
                        "returned, so a depth level cannot be assembled to exhaustion "
                        "(PACKAGE.md 3.4 primitive 18)"
                    )
                    break
                cursors_seen.add(cursor)

            next_frontier: list[NodeRef] = []
            new_here = 0
            for edge_id, edge in fresh.items():
                if self.max_edges is not None and len(seen) >= self.max_edges:
                    bound_hit = True
                    break
                seen[edge_id] = NeighborEdge(edge=edge, at_depth=level)
                new_here += 1
                for far in (edge.src, edge.dst):
                    if str(far) not in visited:
                        visited.add(str(far))
                        next_frontier.append(far)
            if new_here:
                # EDGES.md 4.1: `depth_reached` counts levels that found something NEW.
                # Computing it from "did the scan return any records" made a genuine
                # dead end report depth_reached == depth_requested under the API's own
                # default direction="both", because the level-2 frontier contains the
                # node reached at level 1 and that node is incident on the edge the walk
                # arrived on.
                depth_reached = level
            frontier = next_frontier

        if bound_hit:
            complete = False
            why = why or (
                f"the assembly bound of {self.max_edges} distinct edges was reached; "
                "the depth cap bounds HOPS and node degree is unbounded (EDGES.md 4.2). "
                "This is not paging -- there is no cursor to ask for the rest, because "
                "ruling R13 says the facade does not page in v0"
            )
        # A dead end -- a leaf, a sink, a node with no edges at all -- is
        # `depth_reached < depth_requested` WITH `complete=True` and no `why`. It is the
        # common case in real data and it is not an incomplete answer: the walk saw
        # everything there was. Truncation is the other row of EDGES.md 4.3's table.

        # **Ordered by `(at_depth, edge_id)`, and that is a GUARANTEE rather than an
        # accident** (EDGES.md 4.1, row 4b adversarial round 3). It is a deterministic
        # traversal order and not a ranking -- 1's *"a set, not a ranked list"* is about
        # relevance and stands -- but a consumer projecting this report into a flat list
        # has to walk it in discovery order for `reached` below to mean anything, and an
        # order nobody promised is an order that can change under them.
        edges = tuple(
            sorted(seen.values(), key=lambda ne: (ne.at_depth, ne.edge.edge_id))
        )
        # `reached` is filled here, in the one place that knows: the walk. **A consumer
        # cannot compute it from the report**, and round 3 proved that by implementing
        # this document's own worked example (9.3, the grounding bundle's `relations`
        # slot -- the reason this row exists) the obvious way, comparing each edge's
        # endpoints against the ORIGIN. At depth 2 that returns the wrong answer
        # silently: the far end of a second-hop edge is compared against an origin it
        # was never incident on, so the node actually reached never appears and the
        # intermediate one appears twice. **Mechanism C, inside the example meant to
        # show a consumer how to avoid it.**
        #
        # `None` for a self-loop and for an edge whose two endpoints were both already
        # reached -- a triangle's closing edge reaches nobody new, and saying so is Rule
        # U rather than picking one of its ends.
        nodes: list[NodeRef] = []
        seen_nodes: set[str] = {str(node)}
        resolved: list[NeighborEdge] = []
        for ne in edges:
            reached: NodeRef | None = None
            for far in (ne.edge.src, ne.edge.dst):
                if str(far) not in seen_nodes:
                    seen_nodes.add(str(far))
                    nodes.append(far)
                    if reached is None:
                        reached = far
            resolved.append(replace(ne, reached=reached))
        edges = tuple(resolved)
        return NeighborReport(
            origin=node,
            depth_requested=depth,
            depth_reached=depth_reached,
            direction=direction,
            families_searched=searched,
            edges=edges,
            nodes=tuple(nodes),
            known=len(edges),
            complete=complete,
            why_incomplete=why,
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def _edge_passes(
        self,
        rec,
        frontier_keys: tuple[tuple[str, str, str, str | None], ...],
        direction: str,
        searched_keys: set[tuple[str, str]] | None,
        registered: set[tuple[str, str]],
        symmetric: set[tuple[str, str]],
    ) -> tuple[bool, str | None]:
        """Does this record belong in the report? ``(keep, warning or None)``.

        **The registry narrows, always** -- whether or not the backend could apply the
        filters. EDGES.md 7.1 makes that explicit for `indexes_edges_by_family=False`
        (the query is bounded by the frontier, so the store answers a wider question
        completely and the registry narrows), and doing it unconditionally means one
        code path decides what is in a report rather than two that must agree. The
        store-side filter is then an efficiency claim, and `C17-06` binds it directly at
        the primitive rather than through the report, which is where an efficiency claim
        belongs.

        **Two different questions live here and the first version conflated them**,
        which `C17-06` caught on its first run: *is this family one the caller asked
        for?* and *is this family registered at all?* An edge of a registered family the
        caller did not name is simply outside the query and is dropped; an edge of a
        family NOBODY registered is a fact about the store, and dropping it is the
        silent per-consumer drop EDGES.md is designed against.
        """
        key = (rec.namespace, rec.family)
        if searched_keys is not None and key not in searched_keys:
            # A named query. The caller asked for these families and no others, and an
            # edge outside them is outside the query -- there is nothing to report about
            # it, because `families_searched` already says what was consulted.
            return False, None
        if key not in registered:
            # `searched_keys is None` -- the caller asked for EVERYTHING. EDGES.md 2.7's
            # argument applies one level along: there is deliberately no foreign key from
            # an edge to its family, and beacon's `work_links` has none to
            # `work_link_types` either -- its own documentation calls the registry
            # "advisory rather than enforced". So an edge whose family nobody registered
            # is reachable, and dropping it from a query that asked for everything would
            # be the silent per-consumer drop this whole document is designed against,
            # committed by the read seam on exactly the host EDGES.md 7.2 maps.
            #
            # It is kept, and the caller is told. Twenty-first value of INTERFACE.md 5.4,
            # added in the change that introduces it, per ruling R3.
            #
            # Its `symmetric` is unknown too, so `direction` cannot be applied to it --
            # Rule U -- and that is the second thing the warning says.
            return True, f"edge_family_unregistered:{rec.namespace}:{rec.family}"
        src_k = (rec.src_namespace, rec.src_kind, rec.src_name, rec.src_instance_id)
        dst_k = (rec.dst_namespace, rec.dst_kind, rec.dst_name, rec.dst_instance_id)
        incident = src_k in frontier_keys or dst_k in frontier_keys
        if key in symmetric or direction == "both":
            # **Incidence is re-checked here too**, and the first version of this
            # returned `True` unconditionally on this branch. That made the
            # docstring's "the registry narrows, always" false for the DEFAULT
            # direction: an adapter that ignored `incident_to` and returned every
            # edge of the family was narrowed on `out` and on `in` and not on
            # `both`. It was still caught -- by four tests whose subject is
            # something else -- and "caught incidentally" is not the same claim as
            # "narrowed". Row 4b, adversarial round 1.
            return incident, None
        if direction == "out":
            return src_k in frontier_keys, None
        return dst_k in frontier_keys, None

    async def _seed_equivalent_to(self) -> None:
        """EDGES.md 3.1's family, at store creation. Ruling **R7**.

        Seeded rather than left to a caller because `equivalent_to` is the answer to
        INTERFACE.md 10b.2 contortion 9 -- *nothing can say "these two mean the same
        thing, kept apart"* -- and a registry where the answer exists only if somebody
        remembered to declare it has not answered it. `created_by="seed"` is exactly
        INTERFACE.md 2.1's value for this.

        Idempotent, and it never overwrites: a deployment that has retired or amended
        the family has made a governance decision, and a constructor that reasserted the
        seed on every start would silently reverse it -- which is the shape row 3e found
        in `import_types`. `seed_equivalent_to=False` declines it outright.
        """
        if await self.adapter.get_type("default", EQUIVALENT_TO, kind="edge") is not None:
            return
        now = self._now()
        provenance = Provenance(
            created_at=now,
            created_by_actor="seed",
            # Never null on an active type (INTERFACE.md 2.4). A seeded family has no
            # human approver and saying so is different from leaving the field blank.
            approved_by="auto:seed",
            approved_at=now,
            # A seeded family with NO evidence would carry `no_evidence` on every read
            # -- the registry warning about its own seed. The evidence is real and is
            # exactly what INTERFACE.md 2.8 wants recorded: a named human decision, with
            # the document that carries it.
            evidence=(
                Evidence(
                    kind="human",
                    summary=(
                        "ruling R7: a relation between two scoped types is a "
                        "type-to-type edge, and `equivalent_to` is its first named "
                        "family -- symmetric, non-merging, provenance-bearing"
                    ),
                    locator="docs/specs/EDGES.md 3.1",
                ),
            ),
        )
        async with self.adapter.transaction():
            await self.adapter.put_type(
                TypeRecord(
                    namespace="default",
                    kind="edge",
                    name=EQUIVALENT_TO,
                    definition=EQUIVALENT_TO_DEFINITION,
                    created_by="seed",
                    status="active",
                    attributes=dict(EQUIVALENT_TO_ATTRIBUTES),
                    provenance=_prov_to_dict(provenance),
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._append_event(
                "default", "seeded", "seed", kind="edge", name=EQUIVALENT_TO,
                detail={"why": "EDGES.md 3.1, ruling R7"},
            )

    async def _alias_clash(
        self, namespace: str, name: str, kind: str, aliases: Sequence[str]
    ) -> str | None:
        """An ACTIVE entry that already answers to one of these words, or to ``name``."""
        records, _ = await self._active_page(namespace)
        wanted = set(aliases) | {name}
        for other in records:
            if other.name == name and other.kind == kind:
                continue
            if other.name in wanted:
                return other.name
            if wanted & set(other.aliases or ()):
                return other.name
        return None

    def _refused_import(
        self, namespace: str, name: str, clash: str, *, reason: str = "alias_collision"
    ) -> TypeEntry:
        """A row an import declined to write, returned as a shape a caller can read.

        There is no standing entry to hand back, so this is the imported row as it would
        have looked, marked ``proposed`` -- nothing was written -- and carrying why.
        """
        now = self._now()
        return TypeEntry(
            name=name,
            kind="entity",
            namespace=namespace,
            definition=(
                f"not imported: {clash!r} already answers to this word"
                if reason == "alias_collision"
                else f"not imported: {clash}"
            ),
            created_by="seed",
            provenance=Provenance(created_at=now, created_by_actor="import"),
            status="proposed",
            usage=UsageReport(
                type=name, count=None, last_seen=None, first_seen=None, orphaned=None,
                window=None, why="nothing was written", complete=False,
            ),
            consumers=ConsumerReport(
                type=name, gates_on=(), would_drop=(), would_error=(), known=0,
                complete=False, why_incomplete="nothing was written",
            ),
            warnings=(f"import_refused:{reason}",),
        )

    # ------------------------------------------------------------------ attributes
    async def register_attribute_schema(self, schema: AttributeSchema) -> AttributeSchema:
        """Deployment configuration, not vocabulary. Package-local (ruling R2)."""
        store = self._attribute_store()
        if store is None:
            raise NotSupported("this backend has no attribute-schema storage")
        rec = await store.put_attr_schema(
            AttrSchemaRecord(
                namespace=schema.namespace,
                kind=schema.kind,
                name=schema.name,
                version=schema.version,
                fields_json={
                    name: {
                        "type": spec.type,
                        "description": spec.description,
                        "required": spec.required,
                        "enum": list(spec.enum) if spec.enum is not None else None,
                        "item_type": spec.item_type,
                    }
                    for name, spec in schema.fields.items()
                },
                additional=schema.additional,
                mode=schema.mode,
                registered_at=schema.registered_at or self._now(),
                registered_by=schema.registered_by,
            )
        )
        return self._schema_from_record(rec)

    async def attribute_census(
        self, namespace: str = "default", kind: str | None = None
    ) -> AttributeCensus:
        """Every distinct attribute key ever written, in every mode.

        Ruling R2 keeps this package-local and outside the conformance definition: it
        does not solve the escape hatch, it makes it enumerable.
        """
        store = self._attribute_store()
        # U3: projections are keys this backend DOES store, so a backend with
        # stores_attributes=False and a non-empty projection set has a real, if partial,
        # census. It is reported as partial below rather than refused here.
        if store is None or not (self.caps.stores_attributes or self.caps.attribute_projections):
            why = (
                self.caps.reason("stores_attributes")
                if not self.caps.stores_attributes
                else "this backend has no attribute census storage"
            )
            return AttributeCensus(
                namespace=namespace, entries=(), known=None, complete=False, why_incomplete=why
            )
        rows: list[AttrObservedRecord] = await store.read_attr_observed(namespace, kind=kind)
        # **One lookup per KIND, hoisted out of the row loop.** The first cut called
        # `_name_level_schemas` inside the loop, for every key the per-kind schema did
        # not declare -- one `find_types` plus one `get_attr_schema` per type, per key.
        # Measured at 21,043 SQL round-trips for 500 types and 21 census keys on one
        # `attribute_census()` call, each of them a network hop on the Postgres leg.
        # Row 3e, second adversarial round; the fix is the same "one fetch, reused" move
        # ruling R6's own cost finding produced one round earlier.
        per_kind_cache: dict[str, AttributeSchema | None] = {}
        name_level_cache: dict[str, list[AttributeSchema]] = {}
        partial_whys: list[str] = []
        for row in rows:
            if row.kind not in per_kind_cache:
                per_kind_cache[row.kind] = await self._schema_for(namespace, row.kind)
                found, partial = await self._name_level_schemas(namespace, row.kind)
                name_level_cache[row.kind] = found
                if partial and partial not in partial_whys:
                    partial_whys.append(partial)
        entries = []
        for row in rows:
            # A census row is (kind, key) over EVERY type of that kind, and since
            # ruling R10 a key can be declared for one name and not for the rest. Both
            # a confident `True` and a confident `False` are wrong there, and the first
            # cut fixed only one direction: it asked the per-kind schema, fell back to
            # the overrides when the answer was `False`, and returned a flat `True` when
            # the per-kind schema declared a key an override REMOVES -- while the
            # registry refused a write of that key on the overridden name with "not
            # declared in the schema". Same Rule U failure, same call, same CMS fixture,
            # pointing the other way. Row 3e, second adversarial round.
            #
            # So the rule is symmetric: `None` whenever ANY name-level schema of the
            # kind disagrees with the per-kind schema about this key, in either
            # direction, with `declared_why` naming the names it depends on.
            per_kind = per_kind_cache.get(row.kind)
            in_kind = bool(per_kind and row.key in per_kind.fields)
            disagree = sorted(
                schema.name
                for schema in name_level_cache.get(row.kind, ())
                if schema.name and (row.key in (schema.fields or {})) != in_kind
            )
            declared: bool | None = in_kind
            declared_why: str | None = None
            if disagree:
                declared = None
                declared_why = (
                    "the per-kind schema "
                    + ("declares" if in_kind else "does not declare")
                    + " this key and the name-level schema(s) for "
                    + ", ".join(repr(n) for n in disagree)
                    + (" do not" if in_kind else " do")
                    + ", so whether it is declared depends on which type "
                    "(PACKAGE.md 5.2b, ruling R10)"
                )
            entries.append(
                CensusEntry(
                    kind=row.kind,
                    key=row.key,
                    n=row.n,
                    first_seen=row.first_seen,
                    last_seen=row.last_seen,
                    example=row.example,
                    declared=declared,
                    schema_versions=tuple(row.schema_versions),
                    declared_why=declared_why,
                )
            )
        if not self.caps.stores_attributes:
            # U3 + Rule U. Only the projected keys were ever written, so this census is
            # a census of those keys and of nothing else. Saying `complete=True` here
            # would be the confident wrong answer the whole capability system exists to
            # stop -- an empty-looking census reads as "nothing was ever written".
            return AttributeCensus(
                namespace=namespace,
                entries=tuple(entries),
                known=len(entries),
                complete=False,
                why_incomplete=(
                    self.caps.reason("stores_attributes")
                    + " -- only the keys it owns as typed columns are counted: "
                    + ", ".join(sorted(self.caps.attribute_projections))
                ),
            )
        if partial_whys:
            # A census over types we could not finish reading cannot call itself whole,
            # and the keys whose `declared` depended on those types are unknown rather
            # than declared. Row 3e, third adversarial round.
            entries = [
                replace(entry, declared=None, declared_why=(
                    "the type page for this kind was partial, so whether a name-level "
                    "schema declares this key is unknown: " + "; ".join(partial_whys)
                )) if entry.declared is True else entry
                for entry in entries
            ]
            return AttributeCensus(
                namespace=namespace,
                entries=tuple(entries),
                known=len(entries),
                complete=False,
                why_incomplete="; ".join(partial_whys),
            )
        return AttributeCensus(
            namespace=namespace, entries=tuple(entries), known=len(entries), complete=True
        )

    def _attribute_store(self) -> AsyncAttributeStore | None:
        return self.adapter if isinstance(self.adapter, AsyncAttributeStore) else None

    def _schema_from_record(self, rec: AttrSchemaRecord | None) -> AttributeSchema | None:
        if rec is None:
            return None
        return AttributeSchema(
            namespace=rec.namespace,
            kind=rec.kind,
            name=rec.name,
            version=rec.version,
            fields={
                name: FieldSpec(
                    type=spec["type"],
                    description=spec["description"],
                    required=bool(spec.get("required")),
                    enum=tuple(spec["enum"]) if spec.get("enum") else None,
                    item_type=spec.get("item_type"),
                )
                for name, spec in (rec.fields_json or {}).items()
            },
            additional=rec.additional,
            mode=rec.mode,
            registered_at=rec.registered_at,
            registered_by=rec.registered_by,
        )

    async def _name_level_schemas(
        self, namespace: str, kind: str
    ) -> tuple[list[AttributeSchema], str | None]:
        """Every name-level schema of one kind -- ruling R10, for the census.

        Read through the type store rather than through a schema listing: the optional
        ``AsyncAttributeStore`` extension has no "list schemas" primitive and adding one to
        answer a census question would put a new method on the protocol for a report.
        A schema whose name matches no type governs nothing anyway.
        """
        store = self._attribute_store()
        if store is None:
            return [], None
        # **`edge_payload` is discovered through the FAMILIES, not through the types of
        # that kind, and it has to be** (ruling R34, row 4c). Every other kind's
        # name-level schemas are keyed by a type NAME, so enumerating the types of the
        # kind finds them. An edge payload schema is keyed by the name a family
        # DECLARES in `payload_schema`, and there is no `kind="edge_payload"` type for
        # the loop below to find -- so without this branch the census would answer
        # `declared=False` for a key a payload schema declares `required`, which is the
        # exact confident negative ruling R10's own census fix was made to stop, one
        # kind along and in the row that introduced the kind.
        if kind == EDGE_PAYLOAD_KIND:
            families, _, why = await self._all_edge_families()
            out: list[AttributeSchema] = []
            for declared in dict.fromkeys(
                f.payload_schema
                for f in families
                if f.namespace == namespace and f.payload_schema
            ):
                found = await store.get_attr_schema(namespace, kind, name=declared)
                if found is not None:
                    schema = self._schema_from_record(found)
                    if schema is not None:
                        out.append(schema)
            return out, why
        # Paged to exhaustion, like `_active_page` and for the same reason: an override
        # sitting past the first page turned the tri-state `declared` back into a
        # confident `True` that the write path contradicts, under `complete=True`. Row
        # 3e, third adversarial round.
        records: list = []
        after: str | None = None
        why: str | None = None
        seen: set[str] = set()
        while True:
            page = await self.adapter.find_types(
                TypeQuery(namespace=namespace, kind=kind, include_retired=True, after=after)
            )
            records.extend(page.records)
            if page.complete:
                why = None
                break
            why = page.why_incomplete or "the backend could not answer this query in full"
            cursor = page.next_after
            if not cursor or cursor in seen:
                break
            seen.add(cursor)
            after = cursor
        out: list[AttributeSchema] = []
        for rec in records:
            found = await store.get_attr_schema(namespace, kind, name=rec.name)
            if found is not None:
                schema = self._schema_from_record(found)
                if schema is not None:
                    out.append(schema)
        return out, why

    async def _schema_for(
        self, namespace: str, kind: str, name: str | None = None
    ) -> AttributeSchema | None:
        """The schema in force for one type -- ruling **R10**, row 3e.

        **A ``(namespace, kind, name)`` schema SHADOWS the ``(namespace, kind)`` one.**
        It does not merge with it, and that is the decision rather than an omission: a
        merge of two field maps produces a third schema nobody wrote and nobody
        versioned, which is the unversioned accumulation PACKAGE.md 5 exists to stop,
        one level up. A name-level schema is read as the deployment saying *this type is
        not the general case*, and the general case then does not apply to it.

        ``name=None`` asks for the per-kind schema itself, which is what
        ``attribute_census`` wants when it reports whether a key is *declared*.
        """
        store = self._attribute_store()
        if store is None:
            return None
        if name is not None:
            override = await store.get_attr_schema(namespace, kind, name=name)
            if override is not None:
                return self._schema_from_record(override)
        return self._schema_from_record(await store.get_attr_schema(namespace, kind))

    async def _check_attributes(
        self, namespace: str, kind: str, name: str | None, attributes: dict
    ) -> tuple[AttributeSchema | None, list[str]]:
        """The schema that governs one write, with R10's **enforcement floor** applied.

        **An override replaces the FIELDS and may not weaken the STRICTNESS.**
        PACKAGE.md 5.2b rule 3 says *"an override is a schema, not an exemption"*, and
        the first cut shadowed ``mode`` and ``additional`` along with ``fields`` -- so a
        name-level schema with ``fields={}``, ``additional="allow"``, ``mode="off"``
        turned a strictly enforced kind completely off for one name, with no warning and
        nothing in the census to show it. Reproduced in row 3e's first adversarial round.
        In UC3 that is one agency's one-line, unreviewed opt-out of a rule dozens publish
        under.

        The floor is applied **here and not at registration** on purpose: enforcing it
        when a schema is registered is bypassed by registering the weak override first
        and the strict per-kind schema second, and a rule whose ordering you can pick is
        not a rule.
        """
        schema = await self._schema_for(namespace, kind, name)
        if schema is None:
            return None, []
        if schema.name is not None:
            per_kind = await self._schema_for(namespace, kind)
            if per_kind is not None:
                schema = replace(
                    schema,
                    mode=strictest(schema.mode, per_kind.mode, order=MODES),
                    additional=strictest(
                        schema.additional, per_kind.additional, order=ADDITIONAL
                    ),
                )
        if schema.mode == "off":
            return schema, []
        return schema, validate_attributes(schema, attributes)

    async def _observe(self, rec: TypeRecord) -> None:
        store = self._attribute_store()
        # U3: a backend that stores no arbitrary attributes may still own some keys as
        # typed columns, and those keys ARE written -- so the census must see them. The
        # gate used to be `not stores_attributes`, which made a projected key invisible
        # to the one call whose job is enumerating what got written (5.5).
        observed = self.caps.surviving_attributes(rec.attributes or {})
        if store is None or not observed:
            return
        await store.observe_attributes(
            rec.namespace,
            rec.kind,
            observed,
            at=self._now(),
            schema_version=rec.attr_schema_version,
        )

    # ---------------------------------------------------------------- construction
    #: Deviation D-A1 (docs/runs/3B-ASYNC.md). ``__init__`` cannot be a coroutine, so the
    #: two calls the sync constructor makes -- ``capabilities()`` and ``migrate()`` --
    #: have nowhere to be awaited. The sync ``__init__`` is transformed into ``_open``
    #: and construction goes through this classmethod. It is the ONLY place the async
    #: mirror's shape differs from the sync original, and it differs because Python
    #: says so, not because the design does.
    @classmethod
    async def open(cls, adapter, **kwargs) -> "AsyncRegistry":
        self = cls.__new__(cls)
        await self._open(adapter, **kwargs)
        return self

    def __init__(self, *args, **kwargs):
        raise TypeError(
            "AsyncRegistry is constructed with `await AsyncRegistry.open(adapter, ...)`; "
            "__init__ cannot await capabilities() and migrate()"
        )
