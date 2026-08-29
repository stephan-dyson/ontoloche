"""The interface data shapes -- INTERFACE.md 2 and 5.

Every shape a caller constructs or reads. Frozen dataclasses throughout: a report the
registry handed you is a statement about a moment, and letting a caller mutate one is
how a "3 known, may be others" turns into a "3" somewhere downstream.

Two rules from INTERFACE.md 3 are load-bearing here and are enforced by the shapes
rather than by discipline:

* **Rule U** -- unknown is ``None`` plus a ``why``. Fields that may be unknown are
  typed ``| None`` and there is nowhere to put a ``0`` or a ``False`` instead.
* **Rule K** -- every list result carries ``complete: bool`` and ``known: int``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Any

__all__ = [
    "KINDS",
    "STATUSES",
    "CREATED_BY",
    "ON_UNKNOWN",
    "EVIDENCE_KINDS",
    "PROPOSAL_STATUSES",
    "NOT_A_TYPE_REASONS",
    "REFUSAL_REASONS",
    "Citation",
    "Evidence",
    "ProvenanceEvent",
    "Provenance",
    "Consumer",
    "ConsumerReport",
    "UsageReport",
    "TypeEntry",
    "Proposal",
    "Rejection",
    "Refusal",
    "Resolution",
    "ResolveContext",
    "NotAType",
    "PredicateEntry",
    "PredicateListing",
    "TypeListing",
    "MergeResult",
]

# INTERFACE.md 2.2 -- an open vocabulary; v0 defines four. `value_set` was added
# because the CMS data forced it (10.1).
KINDS = ("entity", "predicate", "edge", "value_set")

STATUSES = ("proposed", "active", "retired")
CREATED_BY = ("seed", "ai", "user")
ON_UNKNOWN = ("drop", "error", "passthrough")
EVIDENCE_KINDS = ("data", "external_doc", "human", "code")
PROPOSAL_STATUSES = ("pending", "approved", "rejected", "superseded")

# INTERFACE.md 10.2 -- the fourth resolve outcome the CMS data forced.
NOT_A_TYPE_REASONS = (
    "redundant_projection",
    "derived_value",
    "export_artefact",
    "instance_not_type",
)

# INTERFACE.md 5.12, rulings R3 and R4 -- CLOSED. Eighteen values, no more. A project
# whose thesis is that governed vocabularies resist rot does not ship an open-ended
# reason string in its own contract. Adding a value requires amending INTERFACE.md 5.12
# in the same change -- which is how the fifteenth got here (R4, row 3c) and how the
# last three did (EDGES.md v0, row #4).
REFUSAL_REASONS = (
    "different_consumer_sets",
    "predicate_merge",
    "kind_mismatch",
    "cross_namespace_merge",
    "retired_operand",
    "definitions_diverge",
    "no_consumer_evidence",
    "live_consumers",
    "tier_below_auto_approve_policy",
    "already_decided",
    "unknown_proposal",
    "proposals_not_stored",
    "cannot_record_override",
    "attributes_schema_violation",
    # R4, 2026-08-28 -- the fifteenth. register_consumer against a read-only consumer
    # source. Deviation D-1 wanted a reason that says this honestly; none of the
    # fourteen did, and reusing one would be the confident wrong answer Rule U forbids.
    "consumer_source_read_only",
    # EDGES.md v0, row #4, 2026-08-29 -- sixteen, seventeen, eighteen. Introduced by a
    # SPEC, not by code: row #4 ships no edge implementation, so nothing in this package
    # returns any of the three yet. They are enumerated here anyway because R3's rule is
    # that the vocabulary is closed and amended in the change that introduces a value --
    # a reason specified in a spec and absent from this tuple is the same drift the
    # spec-drift checker exists to catch, pointing the other way.
    "edge_family_unknown",      # EDGES 4.3 -- a named family is not a registered kind="edge"
    "endpoint_kind_mismatch",   # EDGES 2.4.1 -- wrong endpoint kind, or wrong level
    "edge_store_absent",        # EDGES 6 -- the adapter declares stores_edges=False
)

# INTERFACE.md 5.3 -- a near miss and its score. The score is ``None`` when the
# alternative did not come from the scorer (a retained prior rejection), because
# Rule U forbids standing 0.0 in for "we did not score this".
Alternative = tuple[str, float | None]


@dataclass(frozen=True)
class Citation:
    """INTERFACE.md 2.8 -- required when ``Evidence.kind == "external_doc"``."""

    url: str
    title: str
    retrieved_at: datetime
    quote: str | None = None
    publisher: str | None = None


@dataclass(frozen=True)
class Evidence:
    kind: str
    summary: str
    citation: Citation | None = None
    locator: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in EVIDENCE_KINDS:
            raise ValueError(f"Evidence.kind must be one of {EVIDENCE_KINDS}, got {self.kind!r}")
        if self.kind == "external_doc" and self.citation is None:
            raise ValueError("Evidence(kind='external_doc') requires a citation")


@dataclass(frozen=True)
class ProvenanceEvent:
    at: datetime
    actor: str
    event: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Provenance:
    """INTERFACE.md 2.4 -- who, when, on what evidence.

    ``approved_by`` is never null on an ``active`` type. If nothing human approved it
    the value is ``"auto:<policy>"``; a blank field invites a reader to assume a human
    signed off, which is the rubber-stamping failure arriving through the data model.
    """

    created_at: datetime
    created_by_actor: str
    proposed_by: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    model_tier: str | None = None
    evidence: tuple[Evidence, ...] = ()
    imported_from: dict[str, Any] | None = None
    history: tuple[ProvenanceEvent, ...] = ()
    # Rule U applied to the history itself: a backend with stores_events=False returns
    # an empty history, and this says so rather than letting [] read as "nothing
    # happened". PACKAGE.md 3.4 primitive 15 requires it; INTERFACE.md 2.4 does not
    # list it -- recorded as deviation D-4 in docs/runs/2A-RUN.md.
    history_why: str | None = None


@dataclass(frozen=True)
class Consumer:
    """INTERFACE.md 2.9 -- a registered code path that gates on a predicate."""

    id: str
    gate: str
    on_unknown: str = "drop"
    owner: str | None = None
    registered_at: datetime | None = None
    locator: str | None = None
    #: Row 3d, third adversarial round. Populated only on the ``Consumer``
    #: ``register_consumer`` hands back -- a registration made over a borrowed
    #: connection is not durable until the host commits, and this object looked exactly
    #: as done as a durable one. Reproduced: the registration vanished on host rollback
    #: with nothing on the returned object to say it might. Empty on the copies inside a
    #: ``ConsumerReport``, which are reads, not writes.
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.on_unknown not in ON_UNKNOWN:
            raise ValueError(f"on_unknown must be one of {ON_UNKNOWN}, got {self.on_unknown!r}")


@dataclass(frozen=True)
class ConsumerReport:
    """INTERFACE.md 5.1. ``complete`` is always False in v0, unconditionally."""

    type: str
    gates_on: tuple[Consumer, ...]
    would_drop: tuple[Consumer, ...]
    would_error: tuple[Consumer, ...]
    known: int
    complete: bool
    why_incomplete: str
    #: Ruling R8, row 3d. ``gate_unregistered:<gate>`` for every consumer whose gate
    #: names no registered ``kind="predicate"`` entry -- so ``would_drop`` is not read
    #: as a fact about a live gate when the gate is a word nobody has registered.
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class UsageReport:
    """INTERFACE.md 5.7. ``count=None`` is not zero and ``last_seen=None`` is not never."""

    type: str
    count: int | None
    last_seen: datetime | None
    first_seen: datetime | None
    orphaned: bool | None
    window: timedelta | None
    why: str | None
    complete: bool


@dataclass(frozen=True)
class TypeEntry:
    """INTERFACE.md 2.1 -- one row of the vocabulary."""

    name: str
    kind: str
    namespace: str
    definition: str
    created_by: str
    provenance: Provenance
    status: str
    usage: UsageReport
    consumers: ConsumerReport
    predicates: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    aliases: tuple[str, ...] = ()
    # PACKAGE.md 3.3 stores these on TypeRecord; INTERFACE.md 2.1's table omits the
    # field while 5.9 and 5.5 both describe returned entries carrying warnings.
    # Recorded as deviation D-3 in docs/runs/2A-RUN.md.
    warnings: tuple[str, ...] = ()
    attr_schema_version: int | None = None

    def with_warnings(self, *extra: str) -> "TypeEntry":
        seen = list(self.warnings)
        for w in extra:
            if w not in seen:
                seen.append(w)
        return replace(self, warnings=tuple(seen))


@dataclass(frozen=True)
class Proposal:
    """INTERFACE.md 5.4 -- an addition, not yet a fact."""

    id: str
    name: str
    kind: str
    namespace: str
    definition: str
    predicates: tuple[str, ...]
    attributes: dict[str, Any]
    evidence: tuple[Evidence, ...]
    proposed_by: str
    proposed_at: datetime
    tier: str | None
    status: str
    warnings: tuple[str, ...] = ()
    near_matches: tuple[Alternative, ...] = ()


@dataclass(frozen=True)
class Rejection:
    proposal_id: str
    rejected_by: str
    rejected_at: datetime
    reason: str
    superseded_by: str | None = None
    #: Row 3d, third adversarial round -- the same hole as ``Consumer.warnings``:
    #: a rejection recorded over a borrowed connection vanishes on host rollback and
    #: the returned object said nothing about it.
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Refusal:
    """INTERFACE.md 5.5 and 5.12.

    ``reason`` is drawn from a CLOSED vocabulary -- ``REFUSAL_REASONS`` above is
    the single authority, and INTERFACE.md 5.12 is its prose. Constructing a
    Refusal with anything else raises; the contract suite asserts it
    (INTERFACE.md 5.12: "a Refusal whose reason is not in this list is a
    conformance failure").

    The count is deliberately NOT written here. It was ("fifteen"), and the
    tuple grew to eighteen in the change that added EDGES.md v0's three values
    while this sentence and the error message below both still said fifteen --
    found by an adversarial reviewer, not by check_spec_drift.py, which diffed
    field NAMES and never enum CONTENTS. The checker now compares this tuple
    against INTERFACE.md 5.12's enumerated list, and a number in prose that the
    code does not derive is exactly the thing that goes stale.
    """

    reason: str
    detail: dict[str, Any] = field(default_factory=dict)
    refused: bool = True

    def __post_init__(self) -> None:
        if self.reason not in REFUSAL_REASONS:
            raise ValueError(
                f"Refusal.reason is a closed vocabulary (INTERFACE.md 5.12); "
                f"{self.reason!r} is not one of the {len(REFUSAL_REASONS)}"
            )
        if self.refused is not True:
            raise ValueError("Refusal.refused is always True")


@dataclass(frozen=True)
class NotAType:
    """What a resolver returns from ``classify`` -- INTERFACE.md 10.2."""

    reason: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.reason not in NOT_A_TYPE_REASONS:
            raise ValueError(f"not_a_type reason must be one of {NOT_A_TYPE_REASONS}")


@dataclass(frozen=True)
class ResolveContext:
    """INTERFACE.md 5.3. ``sibling_columns`` carries most of the signal."""

    definition_hint: str | None = None
    sample_values: tuple[Any, ...] = ()
    source: str | None = None
    sibling_columns: tuple[str, ...] = ()
    proposed_by: str | None = None

    def __post_init__(self) -> None:
        # Callers pass lists; freeze them so a context cannot be edited after the
        # resolution that quoted it was returned.
        object.__setattr__(self, "sample_values", tuple(self.sample_values))
        object.__setattr__(self, "sibling_columns", tuple(self.sibling_columns))


@dataclass(frozen=True)
class Resolution:
    """INTERFACE.md 5.3.

    ``alternatives`` is a list result, so Rule K (5.3 / 3) binds it: it carries
    ``known`` and ``complete``. **``complete`` is always False in v0**, for the same
    reason ``ConsumerReport.complete`` is (5.1): the near misses are scored inside one
    namespace, and nothing searched the others. An empty ``alternatives`` therefore
    never stands in for "there is nothing like this anywhere" -- it means "nothing like
    this in the namespace you asked in, and we did not look outside it", which is
    INTERFACE.md 10b.1, contortion 8, reported instead of implied.
    """

    outcome: str
    reason: str
    tier: str
    type: TypeEntry | None = None
    proposal: Proposal | None = None
    confidence: float | None = None
    alternatives: tuple[Alternative, ...] = ()
    scoped_to: str = "default"
    known: int = 0
    complete: bool = False
    why_incomplete: str = ""

    def __post_init__(self) -> None:
        if self.complete is not False:
            raise ValueError(
                "Resolution.complete is always False in v0 (INTERFACE.md 5.3): "
                "alternatives are scored within one namespace and the others are "
                "not searched"
            )
        object.__setattr__(self, "known", len(self.alternatives))
        object.__setattr__(
            self,
            "why_incomplete",
            f"alternatives are scored within namespace {self.scoped_to!r} only; other "
            f"namespaces were not searched (INTERFACE.md 10b.1, contortion 8)",
        )


@dataclass(frozen=True)
class PredicateEntry:
    """INTERFACE.md 5.2. ``extent`` is derived, never stored twice."""

    name: str
    definition: str
    extent: tuple[str, ...]
    extent_size: int | None
    consumers: tuple[Consumer, ...]
    status: str
    provenance: Provenance
    why_extent_incomplete: str | None = None


@dataclass(frozen=True)
class PredicateListing:
    """INTERFACE.md 5.2. Rule K: a list result carries ``known`` and ``complete``.

    ``predicates()`` hides retired predicates by default and may be handed a page the
    backend could not fully answer. Returning a bare list made both invisible -- an
    empty list reading as "this type satisfies nothing" is the failure 5.2 names for
    ``extent_size``, one level up.
    """

    predicates: tuple[PredicateEntry, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None

    def __iter__(self):
        return iter(self.predicates)

    def __len__(self) -> int:
        return len(self.predicates)

    def __getitem__(self, index):
        return self.predicates[index]


@dataclass(frozen=True)
class TypeListing:
    types: tuple[TypeEntry, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None = None
    # C6-05 -- when orphaned=True filters, the types whose orphan state is unknown are
    # excluded, and how many were excluded is reported rather than folded into the
    # answer. Beyond INTERFACE.md 5.6's four fields; deviation D-5.
    excluded_unknown: int | None = None


@dataclass(frozen=True)
class MergeResult:
    """INTERFACE.md 5.10. ``from_`` is retired with ``into`` as its successor and its
    name added to ``into``'s aliases; nothing is deleted."""

    from_: str
    into: str
    namespace: str
    merged_by: str
    merged_at: datetime
    reason: str
    entry: TypeEntry
    acknowledged: tuple[str, ...] = ()
    aliases_added: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
