"""``Registry`` -- the facade. The INTERFACE.md 5 calls, as methods.

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

from ._clock import Clock, SystemClock
from ._resolve import DeterministicResolver, Resolver
from .adapter import (
    AttrObservedRecord,
    AttrSchemaRecord,
    AttributeStore,
    Capabilities,
    ConsumerRecord,
    EventRecord,
    ProposalQuery,
    ProposalRecord,
    StorageAdapter,
    TypeQuery,
    TypeRecord,
)
from .attributes import (
    AttributeCensus,
    AttributeSchema,
    CensusEntry,
    FieldSpec,
    validate_attributes,
)
from .errors import NotSupported, UnknownType
from .policy import NamespacePolicy
from .types import (
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

log = logging.getLogger("open_ontology")

__all__ = ["Registry", "NAME_RE", "CONSUMERS_WHY_INCOMPLETE"]

#: INTERFACE.md 2.1. Enforced above the adapter on both backends so the two behave
#: identically; each backend also carries whatever CHECK its dialect can express.
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

#: INTERFACE.md 5.1 -- the sentence a caller must be able to print. `complete` is
#: always False in v0, even when every consumer in a system is registered, because the
#: registry cannot know that it is.
CONSUMERS_WHY_INCOMPLETE = (
    "consumers are registered, not discovered; unregistered code paths are invisible"
)

# INTERFACE.md 2.8 / 10 -- a definition that asserts an ordering, a severity scale, a
# regulatory meaning or a threshold *should* carry an external_doc citation. 2.8 says
# v0 does not attempt to detect this automatically and leaves it to the proposer; 10's
# worked example and PACKAGE.md C4-06 both require the warning to fall out of the call
# alone. Resolved with a conservative keyword rule and recorded as deviation D-6: it
# over-warns rather than under-warns, because the cost of a spurious
# `unverified_semantics` is an enumerable entry and the cost of a missed one is the
# 0.5 severity inversion going unlabelled.
_DOMAIN_SEMANTIC_WORDS = (
    "ordered",
    "ordering",
    "order of",
    "severity",
    "scale",
    "ranked",
    "ranking",
    "precedence",
    "threshold",
    "regulatory",
    "regulation",
    "statute",
    "cfr",
    "compliance",
    "immediate jeopardy",
    "more serious",
    "less serious",
    "most serious",
    "least serious",
    "higher letters",
    "lower letters",
    "greater than",
    "at least",
    "at most",
    "must be",
    "required by",
    "graded",
)


@dataclass(frozen=True)
class _DefinitionProbe:
    """A stand-in entry whose ``name`` is a definition, so ``Resolver.score`` can be
    asked "how alike are these two sentences?" without widening the protocol."""

    name: str
    definition: str
    aliases: tuple[str, ...] = ()


def _uuid() -> str:
    return uuid.uuid4().hex


def _created_by(actor: str) -> str:
    if actor.startswith("ai:"):
        return "ai"
    if actor.startswith("import:"):
        return "seed"
    if actor == "seed" or actor.startswith("seed:"):
        return "seed"
    return "user"


def _asserts_domain_semantic(definition: str, kind: str, attributes: dict) -> bool:
    text = (definition or "").lower()
    if any(word in text for word in _DOMAIN_SEMANTIC_WORDS):
        return True
    return bool(kind == "value_set" and attributes.get("ordered"))


def _has_external_doc(evidence: Iterable[Evidence]) -> bool:
    return any(e.kind == "external_doc" and e.citation is not None for e in evidence)


# ------------------------------------------------------------------ (de)serialisation


def _citation_to_dict(c: Citation) -> dict:
    return {
        "url": c.url,
        "title": c.title,
        "retrieved_at": c.retrieved_at.isoformat() if c.retrieved_at else None,
        "quote": c.quote,
        "publisher": c.publisher,
    }


def _citation_from_dict(d: dict | None) -> Citation | None:
    if not d:
        return None
    return Citation(
        url=d["url"],
        title=d["title"],
        retrieved_at=_ts(d.get("retrieved_at")),
        quote=d.get("quote"),
        publisher=d.get("publisher"),
    )


def _evidence_to_dict(e: Evidence) -> dict:
    return {
        "kind": e.kind,
        "summary": e.summary,
        "citation": _citation_to_dict(e.citation) if e.citation else None,
        "locator": e.locator,
    }


def _evidence_from_dict(d: dict) -> Evidence:
    return Evidence(
        kind=d["kind"],
        summary=d["summary"],
        citation=_citation_from_dict(d.get("citation")),
        locator=d.get("locator"),
    )


def _ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _prov_to_dict(p: Provenance) -> dict:
    return {
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "created_by_actor": p.created_by_actor,
        "proposed_by": p.proposed_by,
        "approved_by": p.approved_by,
        "approved_at": p.approved_at.isoformat() if p.approved_at else None,
        "model_tier": p.model_tier,
        "evidence": [_evidence_to_dict(e) for e in p.evidence],
        "imported_from": p.imported_from,
    }


def _prov_from_dict(
    d: dict, history: tuple[ProvenanceEvent, ...], history_why: str | None
) -> Provenance:
    return Provenance(
        created_at=_ts(d.get("created_at")),
        created_by_actor=d.get("created_by_actor") or "unknown",
        proposed_by=d.get("proposed_by"),
        approved_by=d.get("approved_by"),
        approved_at=_ts(d.get("approved_at")),
        model_tier=d.get("model_tier"),
        evidence=tuple(_evidence_from_dict(e) for e in (d.get("evidence") or [])),
        imported_from=d.get("imported_from"),
        history=history,
        history_why=history_why,
    )


class Registry:
    """The thirteen calls of INTERFACE.md 5, plus three package-local helpers.

    The counting note from PACKAGE.md 2.2 stands: INTERFACE.md says *twelve calls* and
    enumerating 5.1-5.11 yields thirteen functions. Nothing here depends on which
    number is right.
    """

    def __init__(
        self,
        adapter: StorageAdapter,
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
        self.caps: Capabilities = adapter.capabilities()
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
        if migrate:
            # PACKAGE.md 9.2 -- a store from the future raises rather than being read
            # under old assumptions. The failure mode is a loud refusal at startup.
            adapter.migrate()

    # ------------------------------------------------------------------- internals
    def policy(self, namespace: str) -> NamespacePolicy:
        return self._policies.get(namespace, self._default_policy)

    def _now(self) -> datetime:
        return self.clock.now()

    def _require(self, namespace: str, name: str, *, kind: str | None = None) -> TypeRecord:
        rec = self.adapter.get_type(namespace, name, kind=kind)
        if rec is None:
            raise UnknownType(name, namespace=namespace, kind=kind)
        return rec

    def _events(self, namespace: str, kind: str, name: str) -> tuple[tuple[ProvenanceEvent, ...], str | None]:
        if not self.caps.stores_events:
            return (), self.caps.reason("stores_events")
        rows = self.adapter.read_events(namespace, kind=kind, name=name)
        return (
            tuple(
                ProvenanceEvent(at=r.at, actor=r.actor, event=r.event, detail=dict(r.detail or {}))
                for r in rows
            ),
            None,
        )

    def _append_event(
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
        self.adapter.append_event(
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

    def _write_warnings(self) -> tuple[str, ...]:
        """The warnings every successful WRITE result carries. Empty on an owned store.

        Row 3d, third adversarial round: the first pass attached the durability sentence
        in ``_entry`` and ``_proposal`` only, and ``register_consumer`` and ``reject``
        build their results directly -- so a consumer registration or a rejection made
        over a borrowed connection came back looking exactly as done as a durable write
        and then vanished on host rollback with no trace. A consumer registration that
        silently does not stick is mechanism **C** itself.
        """
        return (self._durability_warning,) if self._durability_warning else ()

    # ------------------------------------------------------------------ projections
    def _consumer_report(
        self,
        rec: TypeRecord,
        consumers: Sequence[ConsumerRecord] | None = None,
        *,
        include_would_drop: bool = True,
    ) -> ConsumerReport:
        rows = (
            list(consumers)
            if consumers is not None
            else self.adapter.find_consumers(rec.namespace)
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
            warnings=self._gate_warnings(rec.namespace, rows),
        )

    def _gate_warnings(
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
        page = self.adapter.find_types(
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

    def _usage_report(self, rec: TypeRecord) -> UsageReport:
        policy = self.policy(rec.namespace)
        window = policy.orphan_window
        row = self.adapter.get_usage(rec.namespace, rec.kind, rec.name)

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

    def _entry(
        self,
        rec: TypeRecord,
        *,
        consumers: Sequence[ConsumerRecord] | None = None,
        extra_warnings: Sequence[str] = (),
    ) -> TypeEntry:
        history, history_why = self._events(rec.namespace, rec.kind, rec.name)
        warnings = list(rec.warnings)
        for w in extra_warnings:
            if w not in warnings:
                warnings.append(w)
        if self._durability_warning and self._durability_warning not in warnings:
            warnings.append(self._durability_warning)
        return TypeEntry(
            name=rec.name,
            kind=rec.kind,
            namespace=rec.namespace,
            definition=rec.definition,
            created_by=rec.created_by,
            provenance=_prov_from_dict(rec.provenance or {}, history, history_why),
            status=rec.status,
            usage=self._usage_report(rec),
            consumers=self._consumer_report(rec, consumers),
            predicates=tuple(rec.predicates),
            attributes=dict(rec.attributes or {}),
            aliases=tuple(rec.aliases),
            warnings=tuple(warnings),
            attr_schema_version=rec.attr_schema_version,
        )

    def _proposal(self, rec: ProposalRecord) -> Proposal:
        warnings = list(rec.warnings)
        if self._durability_warning and self._durability_warning not in warnings:
            warnings.append(self._durability_warning)
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
            warnings=tuple(warnings),
            near_matches=tuple((n[0], n[1]) for n in (rec.near_matches or [])),
        )

    # ============================================================== 5.1 consumers
    def consumers(
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
        rec = self._require(namespace, type)
        return self._consumer_report(rec, include_would_drop=include_would_drop)

    # ============================================================= 5.2 predicates
    def predicates(
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
            member = self._require(namespace, of)
            wanted = set(member.predicates)

        page = self.adapter.find_types(
            TypeQuery(namespace=namespace, kind="predicate", include_retired=include_retired)
        )
        consumer_rows = self.adapter.find_consumers(namespace)
        out: list[PredicateEntry] = []
        for rec in page.records:
            if wanted is not None and rec.name not in wanted:
                continue
            extent, extent_size, why = self._extent(namespace, rec.name, include_retired)
            history, history_why = self._events(namespace, rec.kind, rec.name)
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

    def _extent(
        self, namespace: str, predicate: str, include_retired: bool
    ) -> tuple[tuple[str, ...], int | None, str | None]:
        if not self.caps.indexes_membership:
            # Never extent_size=0 -- that reads as "nothing is commentable", which is
            # INTERFACE.md 5.2's named failure.
            return (), None, self.caps.reason("indexes_membership")
        page = self.adapter.find_types(
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
    def resolve_type(
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

        exact = self.adapter.get_type(namespace, candidate, kind=kind)
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
                live = self.adapter.get_type(namespace, successor)
                if live is not None and live.status != "retired":
                    return Resolution(
                        outcome="existing",
                        reason=(
                            f"{candidate!r} was retired with {successor!r} as its "
                            f"successor; the old word resolves to the successor and is "
                            f"itself not reusable (INTERFACE.md 5.9, 5.10)"
                        ),
                        tier=tier,
                        scoped_to=namespace,
                        type=self._entry(live),
                        confidence=1.0,
                        alternatives=((exact.name, None),),
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
                reason=f"{candidate!r} is already in the vocabulary",
                tier=tier,
                scoped_to=namespace,
                type=self._entry(exact),
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
                alternatives=self._prior_rejections(namespace, candidate)[0] + retired_alt,
            )

        page = self.adapter.find_types(TypeQuery(namespace=namespace, kind=kind, status="active"))
        known = page.records
        scored = self.resolver.score(candidate, context, known, tier=tier) if known else []
        alternatives: list[Alternative] = [(n, s) for n, s in scored[:5]]
        rejections, rejection_note = self._prior_rejections(namespace, candidate)
        alternatives.extend(rejections)
        alternatives.extend(retired_alt)

        best_name, best_score = (scored[0] if scored else (None, None))
        reason_bits: list[str] = []
        if retired_note:
            reason_bits.append(retired_note)
        if rejection_note:
            reason_bits.append(rejection_note)

        if best_score is not None and best_score >= policy.existing_threshold and best_score >= min_confidence:
            entry = self.adapter.get_type(namespace, best_name, kind=kind)
            reason_bits.insert(0, f"{best_name!r} matches at {best_score}")
            return Resolution(
                outcome="existing",
                reason="; ".join(reason_bits),
                tier=tier,
                scoped_to=namespace,
                type=self._entry(entry) if entry else None,
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
        )

    def _prior_rejections(
        self, namespace: str, candidate: str
    ) -> tuple[tuple[Alternative, ...], str | None]:
        """A retained rejection is the cheapest record of "we already decided against
        this word". Surfacing it is what stops a re-proposal in six months."""
        if not self.caps.stores_proposals:
            return (), (
                "prior rejections are omitted from alternatives: "
                + self.caps.reason("stores_proposals")
            )
        page = self.adapter.find_proposals(
            ProposalQuery(namespace=namespace, name=candidate, status="rejected")
        )
        if not page.records:
            return (), None
        # Score is None, not 0.0: nothing scored these, and Rule U forbids a zero
        # standing in for "we did not look".
        alts: tuple[Alternative, ...] = tuple((r.name, None) for r in page.records)
        return alts, f"{candidate!r} was proposed and rejected before"

    # =========================================================== 5.4 propose_type
    def propose_type(
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

        existing = self.adapter.get_type(namespace, name, kind=kind)
        if existing is not None:
            if existing.status == "retired":
                # A retired name is not reusable. Silently reusing a retired word is
                # mechanism 4 with a time delay.
                return self._entry(existing, extra_warnings=("name_previously_retired",))
            return self._entry(existing)

        schema, violations = self._check_attributes(namespace, kind, attributes)
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

        page = self.adapter.find_types(TypeQuery(namespace=namespace, kind=kind, status="active"))
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
            return self._write_approved(
                rec, approved_by=f"auto:{policy.auto_policy_name}", note=None, store_proposal=False
            )

        with self.adapter.transaction():
            self.adapter.put_proposal(rec, expect_absent=True)
            self._append_event(
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
                pending = self.adapter.get_proposal(rec.proposal_id)
                return self._proposal(
                    ProposalRecord(
                        **{
                            **pending.__dict__,
                            "warnings": tuple(pending.warnings)
                            + ("auto_approval_refused:tier_below_auto_approve_policy",),
                        }
                    )
                )
            return self.approve(
                rec.proposal_id, f"auto:{policy.auto_policy_name}", mode="auto"
            )

        return self._proposal(self.adapter.get_proposal(rec.proposal_id))

    # ==================================================== 5.5 approve  /  reject
    def approve(
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

        with self.adapter.transaction():
            rec = self.adapter.get_proposal(proposal_id)
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
            schema, violations = self._check_attributes(
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

            return self._write_approved(
                amended,
                approved_by=approved_by,
                note=note,
                store_proposal=True,
                amendment=amendment,
            )

    def _write_approved(
        self,
        rec: ProposalRecord,
        *,
        approved_by: str,
        note: str | None,
        store_proposal: bool,
        amendment: dict | None = None,
    ) -> TypeEntry:
        now = self._now()
        schema, _ = self._check_attributes(rec.namespace, rec.kind, rec.attributes)
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
        with self.adapter.transaction():
            stored = self.adapter.put_type(type_rec, expect_absent=True)
            if store_proposal:
                self.adapter.put_proposal(
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
            self._observe(stored)
            self._append_event(
                rec.namespace,
                "approved",
                approved_by,
                kind=rec.kind,
                name=rec.name,
                proposal_id=rec.proposal_id,
                detail={"tier": rec.tier, **(amendment or {})},
            )
        return self._entry(stored)

    def reject(
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

        with self.adapter.transaction():
            rec = self.adapter.get_proposal(proposal_id)
            if rec is None:
                return Refusal("unknown_proposal", {"proposal_id": proposal_id})
            if rec.status != "pending":
                return Refusal(
                    "already_decided", {"proposal_id": proposal_id, "status": rec.status}
                )
            now = self._now()
            self.adapter.put_proposal(
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
            self._append_event(
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
    def list_types(
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

        page = self.adapter.find_types(
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
                consumer_rows_by_ns[rec.namespace] = self.adapter.find_consumers(rec.namespace)
            entry = self._entry(rec, consumers=consumer_rows_by_ns[rec.namespace])
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
    def usage(self, type: str, *, namespace: str = "default") -> UsageReport:
        return self._usage_report(self._require(namespace, type))

    # ============================================================ 5.8 provenance
    def provenance(self, type: str, *, namespace: str = "default") -> Provenance:
        """Missing evidence is ``[]`` -- never a reconstructed narrative."""
        rec = self._require(namespace, type)
        history, history_why = self._events(namespace, rec.kind, rec.name)
        return _prov_from_dict(rec.provenance or {}, history, history_why)

    # ================================================================ 5.9 retire
    def retire(
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
        rec = self._require(namespace, type)
        report = self._consumer_report(rec)

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


        usage = self._usage_report(rec)
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
        with self.adapter.transaction():
            stored = self.adapter.put_type(retired)
            self._append_event(
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
        return self._entry(stored)

    # =========================================================== 5.10 merge_types
    def merge_types(
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

        left = self._require(namespace, from_)
        right = self._require(target_ns, into)

        left_report = self._consumer_report(left)
        right_report = self._consumer_report(right)
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
            knowable = self.caps.indexes_membership
            left_extent = set(self._extent(namespace, left.name, True)[0])
            right_extent = set(self._extent(target_ns, right.name, True)[0])
            if (
                not knowable
                or left.kind != "predicate"
                or right.kind != "predicate"
                or left_extent != right_extent
            ):
                return Refusal(
                    "predicate_merge",
                    {
                        "from_extent": sorted(left_extent),
                        "into_extent": sorted(right_extent),
                        "extents_knowable": knowable,
                        "why": (
                            None
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
        with self.adapter.transaction():
            merged = self.adapter.put_type(
                TypeRecord(**{**right.__dict__, "aliases": aliases, "updated_at": now})
            )
            self.adapter.put_type(
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
            self._append_event(
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
            self._append_event(
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
            entry=self._entry(merged),
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
    def register_consumer(
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
            stored = self.adapter.put_consumer(rec)
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

    def record_use(
        self,
        type: str,
        *,
        by: str | None = None,
        at: datetime | None = None,
        namespace: str = "default",
    ) -> None:
        """Explicitly allowed to be a no-op on a backend that does not count -- in
        which case ``usage()`` says so rather than reporting zero."""
        rec = self._require(namespace, type)
        if not self.caps.counts_usage:
            return
        self.adapter.bump_usage(
            rec.namespace, rec.kind, rec.name, at=at or self._now(), by=by
        )

    # ============================================ beyond 5: package-local helpers
    def import_types(
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
            with self.adapter.transaction():
                stored = self.adapter.put_type(rec)
                self._observe(stored)
                self._append_event(
                    namespace,
                    "imported",
                    imported_by,
                    kind=rec.kind,
                    name=name,
                    detail={"system": system, "foundry_status": foundry_status},
                )
            out.append(self._entry(stored))
        return out

    # ------------------------------------------------------------------ attributes
    def register_attribute_schema(self, schema: AttributeSchema) -> AttributeSchema:
        """Deployment configuration, not vocabulary. Package-local (ruling R2)."""
        store = self._attribute_store()
        if store is None:
            raise NotSupported("this backend has no attribute-schema storage")
        rec = store.put_attr_schema(
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

    def attribute_census(
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
        rows: list[AttrObservedRecord] = store.read_attr_observed(namespace, kind=kind)
        entries = []
        for row in rows:
            schema = self._schema_for(namespace, row.kind)
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
        return AttributeCensus(
            namespace=namespace, entries=tuple(entries), known=len(entries), complete=True
        )

    def _attribute_store(self) -> AttributeStore | None:
        return self.adapter if isinstance(self.adapter, AttributeStore) else None

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

    def _schema_for(self, namespace: str, kind: str) -> AttributeSchema | None:
        store = self._attribute_store()
        if store is None:
            return None
        return self._schema_from_record(store.get_attr_schema(namespace, kind))

    def _check_attributes(
        self, namespace: str, kind: str, attributes: dict
    ) -> tuple[AttributeSchema | None, list[str]]:
        schema = self._schema_for(namespace, kind)
        if schema is None or schema.mode == "off":
            return schema, []
        return schema, validate_attributes(schema, attributes)

    def _observe(self, rec: TypeRecord) -> None:
        store = self._attribute_store()
        # U3: a backend that stores no arbitrary attributes may still own some keys as
        # typed columns, and those keys ARE written -- so the census must see them. The
        # gate used to be `not stores_attributes`, which made a projected key invisible
        # to the one call whose job is enumerating what got written (5.5).
        observed = self.caps.surviving_attributes(rec.attributes or {})
        if store is None or not observed:
            return
        store.observe_attributes(
            rec.namespace,
            rec.kind,
            observed,
            at=self._now(),
            schema_version=rec.attr_schema_version,
        )
