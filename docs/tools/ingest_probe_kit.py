# -*- coding: utf-8 -*-
"""The throwaway kit `docs/specs/INGEST.md`'s design tests run against.

**Why a kit and not four probes.** Round 1's kill-row lens found that the row's two
probes ordered ONE rule (`INGEST.md` 3.4) opposite ways -- the condition probe checked
its uncertainty absorber **before** scoring and the seam probe checked its absorber
**only when nothing scored** -- and the second ordering is the defect that let a
truncated scan answer ``existing`` at 1.0 on a label twelve facilities answer to. Two
implementations of one rule is how that happens, so there is now **one** resolver and
every design test imports it. That is `EDGES.md` 7.1's own lesson (*a rule fixed in the
kit alone is row 4b's recorded failure*) applied to this row's own artefacts.

**And it carries its own mutation harness.** Round 1's public-data lens moved the Rule-U
block after the branches -- deleting the load-bearing sentence of 3.4 -- and the probe
still printed ``16/16 checks pass``. ``_mutate="rule_u_last"`` reproduces exactly that
defect on demand, so every design test can prove its checks go **red** when the rule is
removed. A check that cannot go red is a decoration.

Nothing here is product code. `INGEST.md` ships none.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "InstanceRecord", "CandidateQuery", "CandidatePage", "Capabilities",
    "InstanceContext", "InstanceCandidate", "InstanceResolution", "CandidateRef",
    "Condition", "ConditionResult", "DeclarationRefused", "MatchPolicy",
    "EntryDeclaration", "Vocabulary", "HostTable", "Refusal",
    "evaluate", "resolve_instance", "norm", "similar", "OUTCOMES",
    "VALUE_OPS", "COMBINATORS", "assert_adapter_boundary", "flat_form_ok",
]

#: INGEST.md 3.1, rule 3-1. Closed at five.
OUTCOMES = ("existing", "ambiguous", "proposal", "not_an_instance", "unknowable")

#: INGEST.md 6. Ten operators over one record's attribute values, plus two combinators.
VALUE_OPS = ("eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte",
             "is_null", "is_not_null")
COMBINATORS = ("all_of", "any_of")


class DeclarationRefused(Exception):
    """Refused at DECLARATION, never at evaluation. ACTIONS 2.4-6's door."""


@dataclass(frozen=True)
class Refusal:
    reason: str
    detail: dict = field(default_factory=dict)


# --------------------------------------------------------------------------------
# The HOST side -- flat records, no facade shape, deciding nothing
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class InstanceRecord:
    namespace: str
    kind: str
    type_name: str
    instance_id: str
    label: str
    attributes: dict
    source_version: str | None = None


@dataclass(frozen=True)
class CandidateQuery:
    namespace: str
    kind: str
    type_name: str
    label: str | None = None
    #: INGEST 2.1 rule 2-12: a mapping of DECLARED KEYS to opaque values, never a
    #: free-form expression -- a set of names cannot govern one, and round 1 measured
    #: that it did not (finding M8).
    host_filter: Mapping[str, Any] | None = None
    limit: int | None = None
    after: str | None = None


@dataclass(frozen=True)
class CandidatePage:
    records: tuple[InstanceRecord, ...]
    known: int | None
    complete: bool
    why_incomplete: str | None
    next_after: str | None


@dataclass(frozen=True)
class Capabilities:
    """The two flags INGEST 2.3 mints, and nothing else."""

    resolves_instances: bool = False
    instance_filters: frozenset[str] = frozenset()
    why: dict = field(default_factory=dict)


class NotSupported(Exception):
    """Primitive 22/23 against `resolves_instances=False`. INGEST 2, rule 1-3."""


class HostTable:
    """A host-owned instance table behind primitives 22 and 23.

    ``scan_cap`` is *a store that capped* -- R58's third state. ``unsupported_filters``
    are keys this host does NOT declare, so rule 2-7 can be exercised.
    """

    def __init__(self, rows: Iterable[InstanceRecord], *, scan_cap: int | None = None,
                 can_count: bool = True,
                 capabilities: Capabilities | None = None) -> None:
        self._rows = sorted(rows, key=lambda r: r.instance_id)
        self._scan_cap = scan_cap
        self._can_count = can_count
        self.capabilities = capabilities or Capabilities(
            resolves_instances=True,
            instance_filters=frozenset({"state", "tenant", "city", "agency",
                                        "complaint_type", "incident_zip"}),
        )
        self.reads = 0

    # --- primitive 22 -------------------------------------------------------
    def get_instance(self, namespace: str, kind: str, type_name: str,
                     instance_id: str) -> InstanceRecord | None:
        if not self.capabilities.resolves_instances:
            raise NotSupported("this adapter answers no instance queries")
        for rec in self._rows:
            if (rec.namespace, rec.kind, rec.type_name, rec.instance_id) == (
                namespace, kind, type_name, instance_id
            ):
                return rec
        return None

    # --- primitive 23 -------------------------------------------------------
    def find_instance_candidates(self, q: CandidateQuery) -> CandidatePage:
        if not self.capabilities.resolves_instances:
            raise NotSupported("this adapter answers no instance queries")
        self.reads += 1
        pool = [r for r in self._rows
                if (r.namespace, r.kind, r.type_name) == (q.namespace, q.kind,
                                                          q.type_name)]
        undeclared: list[str] = []
        for key, value in (q.host_filter or {}).items():
            if key not in self.capabilities.instance_filters:
                undeclared.append(key)          # rule 2-7: report, never ignore silently
                continue
            pool = [r for r in pool if r.attributes.get(key) == value]
        # `label` may ORDER and may never omit -- rule 2-8, round 1 finding P2. **This
        # host IGNORES it, and that is the blessed case rather than a shortcut**: a
        # backend that ordered by *similarity* would be scoring, which rule 2-6 forbids
        # (`C0-04`'s boundary, and this kit's own first run tripped it). A real backend
        # orders by an index it already has -- exact match, prefix, trigram -- which is
        # its own business and not this project's.
        start = 0
        if q.after is not None:
            ids = [r.instance_id for r in pool]
            start = ids.index(q.after) + 1 if q.after in ids else len(pool)
        window = pool[start:]
        capped = False
        if self._scan_cap is not None:
            allowed = max(self._scan_cap - start, 0)
            if len(window) > allowed:
                window, capped = window[:allowed], True
        page = window if q.limit is None else window[: q.limit]
        more = q.limit is not None and len(window) > q.limit
        why = None
        if undeclared:
            why = ("host_filter keys this backend does not declare: "
                   + ", ".join(sorted(undeclared)))
        elif capped and not more:
            why = (f"host scan cap of {self._scan_cap} rows reached; the rest of this "
                   "table cannot be read from this surface")
        return CandidatePage(
            records=tuple(page),
            known=len(page) if self._can_count else None,
            complete=not capped and not more and not undeclared,
            why_incomplete=why,
            next_after=page[-1].instance_id if more and page else None,
        )


def assert_adapter_boundary() -> None:
    """PACKAGE 3.1 / C0-04's rule, applied to this kit's host table."""
    import inspect

    src = inspect.getsource(HostTable)
    for forbidden in ("InstanceResolution", "Refusal", "CandidateRef", "MatchPolicy",
                      "resolve_instance", "confidence", "ambiguous", "unknowable"):
        if forbidden in src:
            raise AssertionError(
                f"HostTable mentions {forbidden!r} -- the host stores records and "
                "decides nothing (PACKAGE 3.1)"
            )


def flat_form_ok(rec: InstanceRecord) -> str | None:
    """INGEST rule 2-14. ``ref_key``'s grammar, checked at the surface that hands out refs.

    The SHIPPED guard is `ontoloche.actions.flat_form_problem`; this mirrors its rule for
    a record the primitive is about to return, because round 1 (finding K8) constructed
    two different instances with one flat key through the fields this document does not
    declare opaque.
    """
    for field_name in ("namespace", "kind", "type_name"):
        value = getattr(rec, field_name)
        if ":" in value or "#" in value:
            return (f"{field_name}={value!r} contains ':' or '#'; `parse_ref` would read "
                    "back a different reference")
    return None


# --------------------------------------------------------------------------------
# `Condition` -- INGEST 6
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Condition:
    op: str
    why: str
    attribute: str | None = None
    value: Any = None
    terms: tuple["Condition", ...] = ()

    def __post_init__(self) -> None:
        if self.op not in VALUE_OPS + COMBINATORS:
            raise DeclarationRefused(f"{self.op!r} is not one of the twelve terms")
        if not (self.why or "").strip():
            raise DeclarationRefused("Condition.why is required and non-empty")
        if self.op in COMBINATORS:
            if self.attribute is not None or self.value is not None:
                raise DeclarationRefused(f"{self.op} takes terms, not an attribute")
            if not self.terms:
                raise DeclarationRefused(f"{self.op} with no terms")
            return
        if not self.attribute:
            raise DeclarationRefused(f"{self.op} needs an attribute")
        if self.terms:
            raise DeclarationRefused(f"{self.op} takes no terms")
        if self.op in ("is_null", "is_not_null"):
            if self.value is not None:
                raise DeclarationRefused(f"{self.op} takes no value")
            return
        if self.value is None:
            raise DeclarationRefused(
                f"{self.op} may not take a null operand; use is_null / is_not_null")
        if self.op in ("in", "not_in") and not isinstance(self.value, (tuple, list)):
            raise DeclarationRefused(f"{self.op} takes a sequence")


@dataclass(frozen=True)
class ConditionResult:
    holds: bool | None
    why: str
    unreadable: tuple[str, ...] = ()


def evaluate(cond: Condition, record: InstanceRecord,
             readable: frozenset[str]) -> ConditionResult:
    """Three-valued, in the REGISTRY, over attributes the host declared readable."""
    if cond.op in COMBINATORS:
        results = [evaluate(t, record, readable) for t in cond.terms]
        unreadable = tuple(sorted({a for r in results for a in r.unreadable}))
        vals = [r.holds for r in results]
        if cond.op == "all_of":
            holds = False if False in vals else (None if None in vals else True)
        else:
            holds = True if True in vals else (None if None in vals else False)
        why = "" if holds is not None else (
            f"{cond.op}: undecidable on " + ", ".join(unreadable))
        return ConditionResult(holds, why, unreadable)

    assert cond.attribute is not None
    if cond.attribute not in readable:
        return ConditionResult(
            None,
            f"{cond.attribute!r} is not readable on this host: the census cannot see "
            "it, so this condition is unknowable rather than false",
            (cond.attribute,))
    got = record.attributes.get(cond.attribute)
    if cond.op == "is_null":
        return ConditionResult(got is None, "")
    if cond.op == "is_not_null":
        return ConditionResult(got is not None, "")
    if got is None:
        return ConditionResult(
            None, f"{cond.attribute!r} is null; {cond.op} against null is unknowable")
    if cond.op == "eq":
        return ConditionResult(got == cond.value, "")
    if cond.op == "ne":
        return ConditionResult(got != cond.value, "")
    if cond.op == "in":
        return ConditionResult(got in tuple(cond.value), "")
    if cond.op == "not_in":
        return ConditionResult(got not in tuple(cond.value), "")
    try:
        if cond.op == "lt":
            return ConditionResult(got < cond.value, "")
        if cond.op == "lte":
            return ConditionResult(got <= cond.value, "")
        if cond.op == "gt":
            return ConditionResult(got > cond.value, "")
        return ConditionResult(got >= cond.value, "")
    except TypeError as exc:
        return ConditionResult(None, f"{cond.attribute!r}: {exc}")


# --------------------------------------------------------------------------------
# The ENTRY's governed facts -- INGEST 5 and 6.3. NEVER call parameters.
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class MatchPolicy:
    match_at: float
    propose_below: float
    ambiguity_margin: float
    why: str

    def __post_init__(self) -> None:
        if not (0.0 <= self.propose_below <= self.match_at <= 1.0):
            raise DeclarationRefused("propose_below must not exceed match_at")
        if not (self.why or "").strip():
            raise DeclarationRefused("MatchPolicy.why is required and non-empty")


@dataclass(frozen=True)
class EntryDeclaration:
    """What a `kind="entity"` entry declares. INGEST 5-1 and 6-14."""

    policy: MatchPolicy
    predicate: Condition | None = None
    readable: frozenset[str] = frozenset()
    consumers_known: int = 0
    successor: str | None = None      # the type this name was retired toward. 3-14


class Vocabulary:
    """The registry's entries, keyed the way `PACKAGE.md` 3.3 keys identity."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], EntryDeclaration] = {}

    def declare(self, namespace: str, type_name: str, entry: EntryDeclaration) -> None:
        self._entries[(namespace, type_name)] = entry

    def entry(self, namespace: str, type_name: str) -> EntryDeclaration | None:
        return self._entries.get((namespace, type_name))


# --------------------------------------------------------------------------------
# The facade shapes -- INGEST 8
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class InstanceContext:
    label_source: str | None = None
    row_attributes: dict = field(default_factory=dict)
    #: TYPED, round 1 finding F6: a flat list of labels handed a task-resolution a
    #: project name and a person name with nothing to tell them apart.
    siblings: tuple[tuple[str, str], ...] = ()
    act_id: str = ""
    proposed_by: str | None = None


@dataclass(frozen=True)
class CandidateRef:
    """INGEST 4.1. A thing that does NOT exist yet, and never acquires an id."""

    namespace: str
    kind: str
    type_name: str
    label: str
    resolution: str
    act_id: str


@dataclass(frozen=True)
class InstanceCandidate:
    ref_key: str
    label: str
    score: float
    discriminators: dict


@dataclass(frozen=True)
class InstanceResolution:
    outcome: str
    ref: str | None
    candidate: CandidateRef | None
    confidence: float | None
    reason: str
    candidates: tuple[InstanceCandidate, ...]
    known: int
    complete: bool
    why_incomplete: str
    scanned: int
    warnings: tuple[str, ...]
    tier: str


_CLASS_WORDS = {
    "facility", "provider", "provider name", "nursing home", "nursing facility",
    "hospital", "organisation", "organization", "entity", "name", "id",
}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def get_instance_checked(
    host: HostTable, vocab: Vocabulary, *, namespace: str, type_name: str,
    instance_id: str,
) -> InstanceRecord | Refusal | None:
    """INGEST rule 2-15. Primitive 22 THROUGH the entry's declared `Condition`.

    Round 1 finding M7: primitive 22 had no tenancy surface at all -- it took no
    predicate and no filter, so rule 6-15's *"the registry evaluates it"* had nothing to
    evaluate over, and a caller in one tenant could confirm another tenant's row by key.
    The registry evaluates the entry's condition over the returned record: a record the
    predicate FAILS is absent; one it cannot DECIDE is a refusal, never a silent pass.
    """
    if not host.capabilities.resolves_instances:
        return Refusal("instance_source_absent",
                       {"why": "this adapter answers no instance queries"})
    entry = vocab.entry(namespace, type_name)
    rec = host.get_instance(namespace, "entity", type_name, instance_id)
    if rec is None or entry is None or entry.predicate is None:
        return rec
    verdict = evaluate(entry.predicate, rec, entry.readable)
    if verdict.holds is True:
        return rec
    if verdict.holds is False:
        return None
    return Refusal("instance_source_absent",
                   {"why": f"the declared predicate could not be decided on this "
                           f"record: {verdict.why}"})


def resolve_instance(
    candidate: str,
    context: InstanceContext,
    *,
    host: HostTable,
    vocab: Vocabulary,
    namespace: str,
    type_name: str,
    tier: str,
    host_filter: Mapping[str, Any] | None = None,
    page_size: int | None = None,
    _mutate: str | None = None,
) -> InstanceResolution | Refusal:
    """INGEST 3. Five outcomes, and completeness is checked before ANY of them.

    **No `min_confidence` and no `predicate` parameter** -- both are the entry's
    (rules 3-10, 5-1, 6-14). Round 1 finding P3 constructed what a per-call predicate
    costs: omitting the keyword made five of five cross-tenant shared names resolve
    differently and handed one tenant another's refs.

    ``_mutate`` is the mutation harness, not a design. ``"rule_u_last"`` reproduces the
    ordering round 1 broke -- the Rule-U block after the branches -- so a design test can
    prove its own checks go red when 3.4's rule is removed.
    """
    warnings: list[str] = []

    # --- rule 1-3: the capability, before anything -------------------------
    if not host.capabilities.resolves_instances:
        return Refusal("instance_source_absent",
                       {"why": host.capabilities.why.get(
                           "resolves_instances",
                           "this adapter answers no instance queries")})

    entry = vocab.entry(namespace, type_name)
    if entry is None:
        return Refusal("instance_source_absent",
                       {"why": f"no entry declares {type_name!r} in {namespace!r}"})

    # --- rule 3-14: follow the successor chain BEFORE querying -------------
    effective_type = type_name
    seen = {type_name}
    while entry is not None and entry.successor and entry.successor not in seen:
        warnings.append(f"instance_type_succeeded:{entry.successor}")
        effective_type = entry.successor
        seen.add(effective_type)
        entry = vocab.entry(namespace, effective_type) or entry
        break
    assert entry is not None

    # --- rule 3-8: is this an instance at all? No host read ----------------
    key = norm(candidate)
    if not key or key in _CLASS_WORDS:
        return InstanceResolution(
            "not_an_instance", None, None, None,
            f"{candidate!r} names a class or a column, not one thing of that class",
            (), 0, True, "", 0, tuple(warnings), tier)

    # --- rules 2-3/2-11: the identity read exhausts or reports truncated ---
    scanned = 0
    records: list[InstanceRecord] = []
    after: str | None = None
    complete = True
    why_incomplete = ""
    while True:
        page = host.find_instance_candidates(
            CandidateQuery(namespace=namespace, kind="entity",
                           type_name=effective_type, label=candidate,
                           host_filter=host_filter, limit=page_size, after=after))
        scanned += len(page.records)
        records.extend(page.records)
        if not page.complete and page.next_after is None:
            complete = False
            why_incomplete = page.why_incomplete or "the identity read did not finish"
            break
        if page.next_after is None:
            break
        after = page.next_after

    # --- rule 2-14: the flat-form guard, at the surface handing out refs ---
    for rec in records:
        problem = flat_form_ok(rec)
        if problem:
            return Refusal("instance_source_absent",
                           {"why": f"unfaithful reference: {problem}"})

    # --- rules 6-15/6-16: the ENTRY's predicate, evaluated by the registry -
    undecided = 0
    predicate_why: list[str] = []
    survivors: list[InstanceRecord] = []
    if entry.predicate is None:
        warnings.append("no_tenancy_predicate")
        survivors = list(records)
    else:
        for rec in records:
            verdict = evaluate(entry.predicate, rec, entry.readable)
            if verdict.holds is True:
                survivors.append(rec)
            elif verdict.holds is None:
                undecided += 1
                predicate_why.append(verdict.why)

    if entry.consumers_known == 0:
        warnings.append("consumers_unregistered")           # rule 7-1
    if host_filter:
        warnings.append("instance_narrowed_proposal:" + ",".join(sorted(host_filter)))

    scored = sorted(
        (InstanceCandidate(
            ref_key=f"{rec.namespace}:{rec.kind}:{rec.type_name}#{rec.instance_id}",
            label=rec.label,
            score=round(similar(key, norm(rec.label)), 4),
            discriminators=rec.attributes)
         for rec in survivors),
        key=lambda c: (-c.score, c.ref_key))

    def _unknowable(reason: str, why: str) -> InstanceResolution:
        return InstanceResolution(
            "unknowable", None, None, None, reason, tuple(scored[:5]),
            len(scored[:5]), False, why, scanned, tuple(warnings), tier)

    def _rule_u() -> InstanceResolution | None:
        """3.4, and the ORDER is the rule: before the candidate set is interpreted."""
        if not complete:
            return _unknowable(
                f"the identity read did not finish: {why_incomplete}", why_incomplete)
        if undecided:
            why = predicate_why[0] if predicate_why else "the predicate was undecidable"
            return _unknowable(
                f"the host predicate was undecidable on {undecided} of {len(records)} "
                f"candidates", why)
        if scanned == 0:
            return _unknowable(                              # rule 3-13
                "the candidate space was empty: this read saw no rows at all, which is "
                "not evidence that nothing like this exists",
                "scanned=0")
        return None

    if _mutate != "rule_u_last":
        blocked = _rule_u()
        if blocked is not None:
            return blocked

    # --- rules 3-3 / 5-8 / 5-9: the tied SET, then the bands ---------------
    policy = entry.policy
    tied_keys: set[str] = set()
    tied: list[InstanceCandidate] = []
    for c in scored:
        at_or_above = c.score >= policy.match_at
        near_top = (scored[0].score - c.score) <= policy.ambiguity_margin and (
            c.score >= policy.propose_below)
        if (at_or_above or near_top) and c.ref_key not in tied_keys:
            tied_keys.add(c.ref_key)
            tied.append(c)
    tied.sort(key=lambda c: (-c.score, c.ref_key))

    def _mutated_guard(result: InstanceResolution) -> InstanceResolution:
        """The broken ordering: Rule U consulted only when nothing scored."""
        if _mutate == "rule_u_last" and result.outcome == "proposal":
            blocked = _rule_u()
            if blocked is not None:
                return blocked
        return result

    if len(tied) > 1:
        return _mutated_guard(InstanceResolution(
            "ambiguous", None,
            CandidateRef(namespace, "entity", effective_type, candidate, "ambiguous",
                         context.act_id),
            tied[0].score,
            f"{len(tied)} host rows answer to {candidate!r} and nothing here separates "
            "them", tuple(tied), len(tied), complete, why_incomplete, scanned,
            tuple(warnings), tier))
    if tied and tied[0].score >= policy.match_at:
        return _mutated_guard(InstanceResolution(
            "existing", tied[0].ref_key, None, tied[0].score,
            f"exactly one host row answers to {candidate!r}", tuple(tied), 1, complete,
            why_incomplete, scanned, tuple(warnings), tier))
    if scored and scored[0].score >= policy.propose_below:
        return _mutated_guard(InstanceResolution(          # rule 5-9: the band
            "ambiguous", None,
            CandidateRef(namespace, "entity", effective_type, candidate, "ambiguous",
                         context.act_id),
            scored[0].score,
            f"the best candidate scored {scored[0].score}, between propose_below "
            f"{policy.propose_below} and match_at {policy.match_at}: not confident "
            "enough to be the same thing", tuple(scored[:5]), len(scored[:5]), complete,
            why_incomplete, scanned, tuple(warnings), tier))
    return _mutated_guard(InstanceResolution(
        "proposal", None,
        CandidateRef(namespace, "entity", effective_type, candidate, "proposal",
                     context.act_id),
        (scored[0].score if scored else None),
        f"nothing in {scanned} scanned host rows answers to {candidate!r}",
        tuple(scored[:5]), len(scored[:5]), complete, why_incomplete, scanned,
        tuple(warnings), tier))
