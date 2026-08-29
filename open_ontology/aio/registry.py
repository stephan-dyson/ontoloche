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
from dataclasses import dataclass
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
    EventRecord,
    ProposalQuery,
    ProposalRecord,
    AsyncStorageAdapter,
    TypeQuery,
    TypeRecord,
)
from open_ontology.attributes import (
    AttributeCensus,
    AttributeSchema,
    CensusEntry,
    FieldSpec,
    validate_attributes,
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
    _asserts_domain_semantic,
    _created_by,
    _evidence_from_dict,
    _evidence_to_dict,
    _has_external_doc,
    _prov_from_dict,
    _prov_to_dict,
    _ts,
    _uuid,
)


class AsyncRegistry:
    """The thirteen calls of INTERFACE.md 5, plus three package-local helpers.

    The counting note from PACKAGE.md 2.2 stands: INTERFACE.md says *twelve calls* and
    enumerating 5.1-5.11 yields thirteen functions. Nothing here depends on which
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
    ):
        self.adapter = adapter
        self.resolver = resolver or DeterministicResolver()
        self.clock = clock or SystemClock()
        self._default_policy = policy or NamespacePolicy()
        self._policies = dict(policies or {})
        self.caps: Capabilities = await adapter.capabilities()
        if migrate:
            # PACKAGE.md 9.2 -- a store from the future raises rather than being read
            # under old assumptions. The failure mode is a loud refusal at startup.
            await adapter.migrate()

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
                detail=dict(detail or {}),
            )
        )

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
        member_of = set(rec.predicates)
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
            if consumer.gate in member_of:
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
        )

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
    ) -> Resolution:
        """existing / proposal / not_a_type / none. **Persists nothing.**

        ``tier`` is required, not defaulted (INTERFACE.md 2.7): omitting it is a
        TypeError, so an unattributed machine call cannot be made by accident.
        """
        policy = self.policy(namespace)

        exact = await self.adapter.get_type(namespace, candidate, kind=kind)
        if exact is not None and exact.status != "retired":
            return Resolution(
                outcome="existing",
                reason=f"{candidate!r} is already in the vocabulary",
                tier=tier,
                scoped_to=namespace,
                type=await self._entry(exact),
                confidence=1.0,
            )

        not_a_type = self.resolver.classify(candidate, context, tier=tier)
        if not_a_type is not None:
            return Resolution(
                outcome="not_a_type",
                reason=not_a_type.reason,
                tier=tier,
                scoped_to=namespace,
                confidence=None,
                alternatives=(await self._prior_rejections(namespace, candidate))[0],
            )

        page = await self.adapter.find_types(TypeQuery(namespace=namespace, kind=kind, status="active"))
        known = page.records
        scored = self.resolver.score(candidate, context, known, tier=tier) if known else []
        alternatives: list[Alternative] = [(n, s) for n, s in scored[:5]]
        rejections, rejection_note = await self._prior_rejections(namespace, candidate)
        alternatives.extend(rejections)

        best_name, best_score = (scored[0] if scored else (None, None))
        reason_bits: list[str] = []
        if rejection_note:
            reason_bits.append(rejection_note)

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
        reason_bits.insert(0, f"nothing in the vocabulary fits {candidate!r}")
        return Resolution(
            outcome="proposal",
            reason="; ".join(reason_bits),
            tier=tier,
            scoped_to=namespace,
            proposal=proposal,
            confidence=best_score,
            alternatives=tuple(alternatives),
        )

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

        existing = await self.adapter.get_type(namespace, name, kind=kind)
        if existing is not None:
            if existing.status == "retired":
                # A retired name is not reusable. Silently reusing a retired word is
                # mechanism 4 with a time delay.
                return await self._entry(existing, extra_warnings=("name_previously_retired",))
            return await self._entry(existing)

        schema, violations = await self._check_attributes(namespace, kind, attributes)
        warnings: list[str] = []
        if violations:
            if schema and schema.mode == "enforce":
                return Refusal(
                    "attributes_schema_violation",
                    {"kind": kind, "violations": violations, "schema_version": schema.version},
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

        return self._proposal(await self.adapter.get_proposal(rec.proposal_id))

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
            schema, violations = await self._check_attributes(
                amended.namespace, amended.kind, amended.attributes
            )
            if violations and schema and schema.mode == "enforce":
                return Refusal(
                    "attributes_schema_violation",
                    {
                        "kind": amended.kind,
                        "violations": violations,
                        "schema_version": schema.version,
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
        schema, _ = await self._check_attributes(rec.namespace, rec.kind, rec.attributes)
        provenance = Provenance(
            created_at=rec.proposed_at,
            created_by_actor=rec.proposed_by,
            proposed_by=rec.proposed_by,
            approved_by=approved_by,
            approved_at=now,
            model_tier=rec.tier,
            evidence=tuple(_evidence_from_dict(e) for e in (rec.evidence or [])),
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
        return await self._entry(stored)

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
        if report.gates_on and force and not self.caps.stores_events:
            # A destructive override that cannot be recorded is refused. An
            # unrecorded, unattributable change is precisely what this registry
            # exists to prevent.
            return Refusal(
                "cannot_record_override",
                {
                    "why": self.caps.reason("stores_events"),
                    "would_override": [c.id for c in report.gates_on],
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
        return await self._entry(stored)

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

        if acknowledge and not self.caps.stores_events:
            return Refusal(
                "cannot_record_override",
                {"why": self.caps.reason("stores_events"), "acknowledge": list(acknowledge)},
            )

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
            left_extent = set((await self._extent(namespace, left.name, True))[0])
            right_extent = set((await self._extent(target_ns, right.name, True))[0])
            if left.kind != "predicate" or right.kind != "predicate" or left_extent != right_extent:
                return Refusal(
                    "predicate_merge",
                    {
                        "from_extent": sorted(left_extent),
                        "into_extent": sorted(right_extent),
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
            entry=await self._entry(merged),
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
            out.append(await self._entry(stored))
        return out

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
        if store is None or not self.caps.stores_attributes:
            why = (
                self.caps.reason("stores_attributes")
                if not self.caps.stores_attributes
                else "this backend has no attribute census storage"
            )
            return AttributeCensus(
                namespace=namespace, entries=(), known=None, complete=False, why_incomplete=why
            )
        rows: list[AttrObservedRecord] = await store.read_attr_observed(namespace, kind=kind)
        entries = []
        for row in rows:
            schema = await self._schema_for(namespace, row.kind)
            entries.append(
                CensusEntry(
                    kind=row.kind,
                    key=row.key,
                    n=row.n,
                    first_seen=row.first_seen,
                    last_seen=row.last_seen,
                    example=row.example,
                    declared=bool(schema and row.key in schema.fields),
                    schema_versions=tuple(row.schema_versions),
                )
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

    async def _schema_for(self, namespace: str, kind: str) -> AttributeSchema | None:
        store = self._attribute_store()
        if store is None:
            return None
        return self._schema_from_record(await store.get_attr_schema(namespace, kind))

    async def _check_attributes(
        self, namespace: str, kind: str, attributes: dict
    ) -> tuple[AttributeSchema | None, list[str]]:
        schema = await self._schema_for(namespace, kind)
        if schema is None or schema.mode == "off":
            return schema, []
        return schema, validate_attributes(schema, attributes)

    async def _observe(self, rec: TypeRecord) -> None:
        store = self._attribute_store()
        if store is None or not self.caps.stores_attributes or not rec.attributes:
            return
        await store.observe_attributes(
            rec.namespace,
            rec.kind,
            dict(rec.attributes),
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
