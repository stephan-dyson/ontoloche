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
    "WARNING_VALUES",
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
# INTERFACE.md 2.1. The first three are Tenshen's own `work_link_types` vocabulary,
# taken deliberately (2.1, 9). `derived` is ruling **R17** (row 3e): produced by a
# DETERMINISTIC RULE with no human and no model in the loop. Two unrelated fixtures
# reached for the same missing value -- beacon's `EntityMention.match =
# "deterministic" and UC3's BBL join, which had to claim `user` for a join no user
# performed -- and the alternative was a string convention inside `created_by_actor`
# that nothing validates. EDGES.md 14 Q12.
CREATED_BY = ("seed", "ai", "user", "derived")
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

# INTERFACE.md 5.12, rulings R3, R4 and R11 -- CLOSED. A project
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
    # Round #4 adversarial round 3 -- the nineteenth. retract_edge on an edge_id
    # that does not exist reused `edge_family_unknown`, which names a different
    # failure. That is 2.3's Cause B: one word, two meanings.
    "unknown_edge",             # EDGES 2.6 -- no such edge
    # R11, row 3e -- the twentieth, and the SIXTEENTH that any v0 code path returns
    # (the four above are introduced by a spec and returned by nothing yet).
    # `reinstate` on a retirement whose successor is itself active: reinstating a word
    # whose replacement is in use is mechanism 4 arriving through the lifecycle.
    "successor_active",
    # R11 again, after row 3e's first adversarial round -- the twenty-first, and the
    # SEVENTEENTH any v0 code path returns. `reinstate` on a name that a LIVE type holds
    # as an alias, or on a type holding a live name as one of its own aliases. Two active
    # entries with one word between them is mechanism 4, and it was reachable in three
    # ordinary calls: merge A into B, retire B, reinstate A, reinstate B. `merge_types`
    # refuses by default and `propose_type` on a live type's alias returns the tombstone;
    # `reinstate` was the one door left open, in the registry whose thesis is detecting
    # exactly this.
    "alias_collision",
)

# INTERFACE.md 5.4 -- CLOSED, the same rule R3 gives for REFUSAL_REASONS and for the
# same reason. A value carrying a `:<detail>` suffix is listed by its prefix.
#
# Enumerated here because it was NOT, and the document drifted: 5.4's table said
# "eighteen values" while omitting `gate_unregistered`, which ruling R8 added in row 3d,
# which v0 code emits on every ConsumerReport with an unregistered gate, and which
# C11-05 tests -- an omission the table's own last row referred to by name. Found by a
# reviewer reading two files side by side, which is exactly what check_spec_drift.py
# exists to make unnecessary; it now holds 5.4 against this tuple the way it already
# holds 5.12. Row 3e, third adversarial round.
WARNING_VALUES = (
    "unverified_semantics",
    "no_evidence",
    "near_duplicate",
    "auto_approval_refused",
    "attributes_invalid",
    "name_previously_retired",
    "retired_without_usage_evidence",
    "reinstate_no_op",
    "reinstate_alias_check_unavailable",
    "import_refused",
    "not_durable_until_host_commits",
    "gate_unregistered",
    "definitions_similarity",
    "definitions_uncertified",
    "definitions_threshold",
    "endpoint_type_unregistered",
    "retracted_without_event_trail",
    "edge_family_retired",
    "origin_type_unregistered",
    "no_edge_gate_registered",
    # Row 4b, the IMPLEMENTATION of EDGES.md v0 -- the twenty-first, and the first
    # warning value this project has added because writing the code found a case the
    # specification had not. There is deliberately no foreign key from an edge to its
    # family (EDGES.md 2.7's argument, and beacon's `work_links` has none to
    # `work_link_types` either -- its own documentation calls the registry "advisory
    # rather than enforced"), so an edge whose family nobody registered is REACHABLE by
    # `neighbors`. Dropping it would be the silent per-consumer drop EDGES.md 12 names
    # as its dominant mechanism, committed by the read seam on exactly the host EDGES.md
    # 7.2 maps. It is returned, and this is what says so -- and it also says the
    # `direction` filter could not be applied to it, because an unregistered family's
    # `symmetric` is unknown and Rule U forbids guessing.
    "edge_family_unregistered",
    # Row 4b, adversarial round 3 -- the twenty-second, and the second value this
    # project has minted because running the code found a case a specification had
    # not. `merge_types` is the registry's sanctioned answer to mechanism 4, which
    # EDGES.md 12 calls co-dominant for the edge row; it retires one word with the
    # other as its successor and rewrites no edge, because an edge's endpoints are
    # references by identity triple. So a caller who does the CORRECT thing after a
    # merge -- resolve to the canonical type, then walk -- got `known=0`,
    # **`complete=True`** and an empty `warnings` about edges sitting in the store
    # under the other name. That contradicts EDGES.md 4.4's own argument for why
    # `complete` may ever be True: *there is no edge that exists in the store and is
    # invisible to a query over it*. Across a merge there is, and now the report says
    # so and stops claiming completeness.
    "endpoint_type_merged",
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
    #: Ruling **R21**, row 3e -- the SOURCE's own version, never ours.
    #:
    #: INTERFACE.md 10b.5, contortion 12: a UC3 type is derived from a dataset that has
    #: its own ``data_updated_at`` -- 2017-10-04 for one agency, 2026-08-28 for another
    #: -- and a type proposed from a 2017 snapshot of a "Historical data" set is a
    #: different claim from one proposed off a daily feed. None of the ten fields had a
    #: home for it: ``Citation.retrieved_at`` is when *we* fetched, and ``imported_from``
    #: is foreign SYSTEM identifiers. EDGES.md gave ``EdgeProvenance`` the field first,
    #: which left two shapes for one concept with one of them missing it -- the drift
    #: this repo has caught six times, so it is closed here (EDGES.md 14, Q16).
    source_version: str | None = None
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
    #: R21. Carried here as well as on ``Provenance`` so a proposer can read back what
    #: they supplied before anything is approved -- a value accepted and invisible until
    #: approval is a value a caller cannot check.
    source_version: str | None = None


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
    ``known`` and ``complete``.

    **``complete`` was unconditionally False until ruling R6 (row 3e).** The reason it
    was is still the reason it usually is: the near misses are scored inside one
    namespace and nothing searched the others, so an empty ``alternatives`` never
    stands in for "there is nothing like this anywhere" -- it means "nothing like this
    in the namespace you asked in, and we did not look outside it", which is
    INTERFACE.md 10b.1, contortion 8, reported instead of implied.

    R6 adds ``resolve_type(search_namespaces=...)``, and with it the one condition under
    which the claim can honestly be True: **the caller named every namespace that
    exists and every one of them was searched.** ``searched_namespaces`` is a required
    companion of that claim rather than an echo of the argument, for the reason
    EDGES.md gives about ``families_searched`` and ruling R12 gives about a coverage
    line -- *a completeness claim without its scope line is not a claim*. Constructing a
    ``complete=True`` resolution without one raises.
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
    #: Every namespace whose active types were actually scored, ``scoped_to`` included.
    #: Empty means the default v0 behaviour -- one namespace, and it is ``scoped_to``.
    #: Ruling R6, row 3e.
    searched_namespaces: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "known", len(self.alternatives))
        object.__setattr__(self, "searched_namespaces", tuple(self.searched_namespaces))
        if self.complete:
            if not self.searched_namespaces:
                raise ValueError(
                    "Resolution.complete=True requires searched_namespaces "
                    "(INTERFACE.md 5.3, ruling R6): a completeness claim without the "
                    "list of what was searched is not a claim"
                )
            object.__setattr__(self, "why_incomplete", "")
            return
        if self.why_incomplete:
            return
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
