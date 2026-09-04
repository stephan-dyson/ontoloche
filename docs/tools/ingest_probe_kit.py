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
    "type_closure", "act_key", "Invocation", "Ledger", "IngestAct",
    "CHAIN_CAP", "ACT_RULES",
]

#: INGEST.md 3.4a rule 3-16 -- the successor closure's hop cap, the way
#: `ontoloche/registry.py`'s `_identity_closure` caps its own walk. R84's second
#: clause: the specification cites the shipped implementation rather than restating
#: the ruling it was derived from.
CHAIN_CAP = 16

#: INGEST.md 4.3. The act rules a construction may switch OFF, so every one of them
#: has a check that goes red. Standing rule (e)'s doors, named.
ACT_RULES = frozenset({"4-10", "4-11", "4-10-key", "4-10-relation", "4-11-written",
                       "4-7-nai", "4-3-eff"})

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
    #: INGEST 3.4a rule 3-21. `merge_types` writes BOTH a successor and an alias for
    #: one absorption, and a hand-written alias is one the successor scan would miss
    #: -- `registry.py`'s `_identity_closure` says so in terms, and `I-8` is what
    #: happens when a document cites that function and takes one of its relations.
    aliases: frozenset[str] = frozenset()


class Vocabulary:
    """The registry's entries, keyed the way `PACKAGE.md` 3.3 keys identity."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], EntryDeclaration] = {}

    def declare(self, namespace: str, type_name: str, entry: EntryDeclaration) -> None:
        self._entries[(namespace, type_name)] = entry

    def entry(self, namespace: str, type_name: str) -> EntryDeclaration | None:
        return self._entries.get((namespace, type_name))

    def predecessors(self, namespace: str, type_name: str) -> list[str]:
        """Every name retired TOWARD this one. INGEST 3.4a rule 3-20.

        The backward relation, which `registry.py`'s `_identity_closure` calls *the
        direction `merge_types` actually produces and the one a caller reaches after
        doing the right thing* -- i.e. the ORDINARY post-retirement path.
        """
        return sorted(t for (n, t), e in self._entries.items()
                      if n == namespace and e.successor == type_name)

    def alias_holders(self, namespace: str, alias: str) -> list[str]:
        """Every name declaring this alias. INGEST 3.4a rule 3-21."""
        return sorted(t for (n, t), e in self._entries.items()
                      if n == namespace and alias in e.aliases)


@dataclass(frozen=True)
class Closure:
    """The successor closure of one type name. INGEST 3.4a, rules 3-14 … 3-17."""

    effective: str
    entry: EntryDeclaration | None
    complete: bool
    why: str
    hops: tuple[str, ...]
    #: Every written name that now denotes ONE identity: the forward chain, the
    #: backward chain, and the aliases of both. `members[0]` is the name the caller
    #: gave, exactly as `_identity_closure` promises. **This is the extent rule 3-19
    #: is about** -- `I-8` was reading `hops` alone.
    members: tuple[str, ...] = ()
    #: Which of the shipped function's three relations this walk ADOPTED. R87: a
    #: normative citation must enumerate what it takes and what it leaves.
    relations: tuple[str, ...] = ()


def type_closure(vocab: Vocabulary, namespace: str, type_name: str,
                 *, cap: int = CHAIN_CAP, one_hop: bool = False,
                 keep_predecessor: bool = False, forward_only: bool = False,
                 no_aliases: bool = False, no_cap: bool = False,
                 no_cycle_guard: bool = False) -> Closure:
    """The CHAIN, not one hop -- and it stops honestly when it cannot finish.

    This is the one implementation of `INGEST.md` 3.4a, and every door that reads,
    writes, keys, gates or counts an identity calls it (**standing rule (e)**). It
    does what `ontoloche/registry.py`'s `_identity_closure` does and is written from
    that code rather than from **R38**'s words, per **R84**'s second clause: a visited
    set, a hop cap, and ``complete=False`` **with a why** when the walk stops early.

    **Three relations, per R87.** `_identity_closure` walks the chain **forward**, walks
    it **backward** (*"the direction `merge_types` actually produces and the one a caller
    reaches after doing the right thing"*), and consults **aliases**. `I-8` is what
    happened when this document cited that function as normative and implemented its
    three *termination* rules with one of its three *relations*: a caller naming the
    SURVIVOR of a retirement read a strict subset of the identity, and the act wrote a
    second row for it in ``auto`` mode with no human. **All three are adopted here and
    named in ``Closure.relations``**; each has its OWN mutation, because one mutation over
    "the closure" would leave the fix unfalsifiable in the direction it just added.

    ``one_hop``, ``keep_predecessor``, ``forward_only`` and ``no_aliases`` are the MUTATION
    harness for `I-2`, its rider, and `I-8`'s two relations. They are not designs.
    """
    entry = vocab.entry(namespace, type_name)
    effective = type_name
    seen = {type_name}
    hops: list[str] = []
    while entry is not None and entry.successor:
        nxt = entry.successor
        if nxt in seen and not no_cycle_guard:            # rule 3-17: cycle
            return Closure(effective, entry, False,
                           f"the successor chain from {type_name!r} cycles at "
                           f"{nxt!r}; this identity cannot be resolved to one type",
                           tuple(hops), (type_name,), ("forward",))
        if len(hops) >= cap and not no_cap:               # rule 3-16: the cap
            return Closure(effective, entry, False,
                           f"the successor chain from {type_name!r} passed the cap "
                           f"of {cap} hops without reaching a live type",
                           tuple(hops), (type_name,), ("forward",))
        # rule 3-22 (K8): the successor NAME reaches the flat form by the WRITE
        # door -- `effective_type` becomes `CandidateRef.type_name`, then
        # `Invocation.type_name`, then `minted_ref` -- WITHOUT ever being a record,
        # so rule 2-14's guard over records never sees it. The shipped `parse_ref`
        # then reads the minted string back as a DIFFERENT reference.
        if any(sep in nxt for sep in (":", "#")):
            return Closure(effective, entry, False,
                           f"{type_name!r} was retired toward {nxt!r}, which "
                           f"contains ':' or '#': `ref_key` would write a string "
                           f"`parse_ref` reads back as a different reference",
                           tuple(hops), (type_name,), ("forward",))
        nxt_entry = vocab.entry(namespace, nxt)
        if nxt_entry is None:                             # rule 3-15: dangling
            if keep_predecessor:                          # MUTATION: the rider
                return Closure(nxt, entry, True, "", tuple(hops + [nxt]),
                               tuple([type_name] + hops + [nxt]), ("forward",))
            return Closure(effective, entry, False,
                           f"{type_name!r} was retired toward {nxt!r} and no entry "
                           f"declares {nxt!r} in {namespace!r}: the extent this "
                           f"identity would be decided over is not readable",
                           tuple(hops), (type_name,), ("forward",))
        if no_cycle_guard and len(hops) > 64:
            break                    # the harness's own stop, not a rule
        hops.append(nxt)
        seen.add(nxt)
        effective, entry = nxt, nxt_entry
        if one_hop:                                       # MUTATION: I-2 itself
            break
    # --- rule 3-20: the BACKWARD relation, and rule 3-21: ALIASES ----------
    # Every written name that now denotes this identity. The forward walk above
    # answers "what is this name now"; this answers "what else is this identity",
    # and `I-8` is the second question going unasked.
    relations = ["forward"]
    members = [type_name] + [h for h in hops if h != type_name]
    if not forward_only:
        relations.append("backward")
        frontier = list(members)
        seen_b = set(members)
        while frontier and len(members) <= cap * 4:
            name = frontier.pop()
            for pred in vocab.predecessors(namespace, name):
                if pred not in seen_b:
                    seen_b.add(pred)
                    members.append(pred)
                    frontier.append(pred)
    if not no_aliases:
        relations.append("aliases")
        for name in list(members):
            e = vocab.entry(namespace, name)
            for al in sorted(e.aliases if e else ()):
                if al not in members:
                    members.append(al)
            for holder in vocab.alias_holders(namespace, name):
                if holder not in members:
                    members.append(holder)
    return Closure(effective, entry, True, "", tuple(hops),
                   tuple(members), tuple(relations))


def act_key(vocab: Vocabulary, namespace: str, kind: str, type_name: str,
            label: str, *, raw: bool = False) -> tuple[str, str, str, str]:
    """INGEST 4.3, rule 4-10. The key an ACT scopes on, and it is the key the GATE
    decides on -- one function, because `I-4` is what happens when there are two.

    The type half runs through `type_closure`, so a `retire(successor=)` between two
    acts cannot make one identity answer to two keys (`I-3`). The label half runs
    through `norm`, the scorer's own identity function (`I-4`). ``raw`` is the
    mutation.
    """
    if raw:                                               # MUTATION: I-4
        return (namespace, kind, type_name, label)
    return (namespace, kind,
            type_closure(vocab, namespace, type_name).effective, norm(label))


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
    #: INGEST 5.3 rule 5-11 -- `I-7`'s carrier, and rule 5-7's. The `(namespace,
    #: type_name)` whose entry supplied the `MatchPolicy` and the predicate this
    #: answer was judged by. R86 verified that rule 5-7 had NO carrier: the printed
    #: shape contained no `policy` and the shipped `Invocation.declared_policy` holds
    #: `approval_mode` / `min_auto_tier` / `reversibility`, not the three thresholds.
    #: A rule about which policy governed an answer cannot be checked while the answer
    #: cannot say which policy governed it.
    governed_by: str = ""


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

    # --- rules 3-14 … 3-18: the successor CLOSURE, before querying ---------
    # `I-2`/`I-3`/D3. One implementation, shared with `act_key`, so the door that
    # reads and the doors that write and key an identity resolve the SAME set --
    # standing rule (e). R84: written from `_identity_closure`, not from R38's words.
    declared = entry
    closure = type_closure(vocab, namespace, type_name,
                           one_hop=(_mutate == "chain_one_hop"),
                           keep_predecessor=(_mutate == "chain_keeps_predecessor"),
                           forward_only=(_mutate == "closure_forward_only"),
                           no_aliases=(_mutate == "closure_no_aliases"),
                           no_cap=(_mutate == "chain_no_cap"),
                           no_cycle_guard=(_mutate == "chain_no_cycle"))
    effective_type = closure.effective
    for hop in closure.hops:
        warnings.append(f"instance_type_succeeded:{hop}")
    chain_complete, chain_why = closure.complete, closure.why
    if closure.entry is not None:
        entry = closure.entry

    # --- rule 3-18: the successor's GOVERNED FACTS are not the caller's ------
    # D3: one `retire(successor=)` swapped the tenancy predicate and the MatchPolicy
    # in under a caller who declared neither. The extent is then a different set and
    # this door cannot prove otherwise, so it does not decide.
    # rule 5-11: the entry whose governed facts judged this answer, named.
    governed_by = f"{namespace}:{effective_type}"

    governed_why = ""
    if _mutate != "governed_facts_ignored" and declared is not None:
        # rule 3-18 (K1): EVERY member of the closure, not the two endpoints. Round
        # 2 compared the declared entry with the endpoint's, so ONE extra `retire()`
        # to an endpoint declaring what the caller declared silenced the guard --
        # while rule 3-19 admits the intermediate's rows into the extent, making the
        # entry whose rows are being judged the one entry never consulted. Rules 5-10
        # and 6-18 said "a closure HOP" all along; only 3-18 said "the successor's".
        for member in closure.members:
            if member == type_name:
                continue
            m_entry = vocab.entry(namespace, member)
            if m_entry is None:
                continue
            changed = [name for name, a, b in (
                ("MatchPolicy", declared.policy, m_entry.policy),
                ("the tenancy predicate", declared.predicate, m_entry.predicate),
            ) if a != b]
            if changed:
                governed_why = (
                    f"{type_name!r} resolves through {member!r}, which declares a "
                    f"different {' and a different '.join(changed)}: the extent this "
                    f"resolution would be decided over is not the extent the caller "
                    f"declared")
                break
    assert entry is not None

    # --- rule 3-8: is this an instance at all? No host read ----------------
    key = norm(candidate)
    if not key or key in _CLASS_WORDS:
        return InstanceResolution(
            "not_an_instance", None, None, None,
            f"{candidate!r} names a class or a column, not one thing of that class",
            (), 0, True, "", 0, tuple(warnings), ("" if _mutate == "tier_dropped" else tier), governed_by)

    # --- rules 2-3/2-11/3-19: the identity read exhausts, over the WHOLE closure --
    # `I-3`. The endpoint alone is a SMALLER SET than the identity's extent: a row
    # written under a name that has since been retired is still one of this identity's
    # rows until the host migrates it, and a read that cannot see it proposes a
    # duplicate for a facility the same store already holds. Standing rule (e) is
    # exactly this -- the same set at every door -- so the read spans the declared name
    # and every hop of the closure.
    read_types = list(closure.members) or [type_name]
    if _mutate == "extent_endpoint_only":                # MUTATION: `I-3`
        read_types = [effective_type]
    scanned = 0
    records: list[InstanceRecord] = []
    complete = chain_complete
    why_incomplete = "" if chain_complete else chain_why
    for read_type in (read_types if chain_complete else []):
        after: str | None = None
        while True:
            page = host.find_instance_candidates(
                CandidateQuery(namespace=namespace, kind="entity",
                               type_name=read_type, label=candidate,
                               host_filter=host_filter, limit=page_size, after=after))
            scanned += len(page.records)
            records.extend(page.records)
            if not page.complete and page.next_after is None:
                complete = False
                why_incomplete = (page.why_incomplete
                                  or "the identity read did not finish")
                break
            if page.next_after is None:
                break
            after = page.next_after
        if not complete:
            break

    # --- rule 2-14: the flat-form guard, at the surface handing out refs ---
    for rec in records:
        problem = None if _mutate == "flat_form_off" else flat_form_ok(rec)
        if problem:
            return Refusal("instance_source_absent",
                           {"why": f"unfaithful reference: {problem}"})

    # --- rule 2-16: two DIFFERENT rows under ONE name and one id -> unknowable --
    # (`I-6`. Not K2: two names of ONE closure holding ONE row is one identity and
    #  collapses at rule 2-17 below, which is why this key carries `type_name`.)
    # `I-6`. Two host records under one id collapse to one candidate in a set test
    # that dedupes on the flat key, and the second row vanishes from `candidates`
    # entirely -- so the extent is not countable and this door does not decide.
    dup_why = ""
    if _mutate != "dup_ids_ignored":
        by_id: dict[tuple, int] = {}
        for rec in records:
            k = (rec.namespace, rec.kind, rec.type_name, rec.instance_id)
            by_id[k] = by_id.get(k, 0) + 1
        dups = sorted(k[3] for k, n in by_id.items() if n > 1)
        if dups:
            dup_why = (
                f"the identity read returned {len(dups)} instance_id(s) more than once "
                f"({', '.join(dups[:3])}): the host's ids do not distinguish its own "
                f"rows, so the extent of this identity cannot be counted")

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

    # rule 2-17 (K2): within ONE closure read the same host row can appear under two
    # names of one identity -- the migration window rule 3-19's own justification
    # names. They are ONE thing, so they collapse to ONE candidate under the name the
    # closure resolves to; rule 2-16's distinctness question is about two DIFFERENT
    # rows sharing an id under ONE name, which is a different question and stays.
    if _mutate != "closure_dupes_kept":
        by_identity: dict[tuple, InstanceRecord] = {}
        for rec in survivors:
            k = (rec.namespace, rec.kind, rec.instance_id)
            prev = by_identity.get(k)
            if prev is None or rec.type_name == effective_type:
                by_identity[k] = rec
        survivors = [by_identity[k] for k in
                     dict.fromkeys((r.namespace, r.kind, r.instance_id)
                                   for r in survivors)]

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
            len(scored[:5]), False, why, scanned, tuple(warnings), ("" if _mutate == "tier_dropped" else tier), governed_by)

    def _rule_u() -> InstanceResolution | None:
        """3.4, and the ORDER is the rule: before the candidate set is interpreted.

        Six absorbers now, one per row of the instance-surface table (R85). Each asks
        the same question -- *is the set this door is about to decide over provably the
        identity's extent?* -- and each answers `unknowable` rather than deciding.
        """
        if not complete:                                     # `I-1`, `I-2`
            return _unknowable(
                f"the identity read did not finish: {why_incomplete}", why_incomplete)
        if governed_why:                                     # D3
            return _unknowable(f"the governed facts changed under the caller: "
                               f"{governed_why}", governed_why)
        if dup_why:                                          # `I-6`
            return _unknowable(f"the extent is not countable: {dup_why}", dup_why)
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

    if _mutate == "one_of_tied" and len(tied) > 1:
        # rule 3-4 / `C20-18`: EVERY tied candidate is returned. Returning one while
        # still reporting `known` is the shape trips 11 and 12 took.
        tied = tied[:1] + tied[1:]
        return _mutated_guard(InstanceResolution(
            "ambiguous", None,
            CandidateRef(namespace, "entity", effective_type, candidate, "ambiguous",
                         context.act_id),
            tied[0].score, "one of the tied set", (tied[0],), 2, complete,
            why_incomplete, scanned, tuple(warnings), tier, governed_by))

    if len(tied) > 1:
        return _mutated_guard(InstanceResolution(
            "ambiguous", None,
            CandidateRef(namespace, "entity", effective_type, candidate, "ambiguous",
                         context.act_id),
            tied[0].score,
            f"{len(tied)} host rows answer to {candidate!r} and nothing here separates "
            "them", tuple(tied), len(tied), complete, why_incomplete, scanned,
            tuple(warnings), ("" if _mutate == "tier_dropped" else tier), governed_by))
    if tied and tied[0].score >= policy.match_at:
        return _mutated_guard(InstanceResolution(
            "existing", tied[0].ref_key, None, tied[0].score,
            f"exactly one host row answers to {candidate!r}", tuple(tied), 1, complete,
            why_incomplete, scanned, tuple(warnings), ("" if _mutate == "tier_dropped" else tier), governed_by))
    if scored and scored[0].score >= policy.propose_below:
        return _mutated_guard(InstanceResolution(          # rule 5-9: the band
            "ambiguous", None,
            CandidateRef(namespace, "entity", effective_type, candidate, "ambiguous",
                         context.act_id),
            scored[0].score,
            f"the best candidate scored {scored[0].score}, between propose_below "
            f"{policy.propose_below} and match_at {policy.match_at}: not confident "
            "enough to be the same thing", tuple(scored[:5]), len(scored[:5]), complete,
            why_incomplete, scanned, tuple(warnings), ("" if _mutate == "tier_dropped" else tier), governed_by))
    if _mutate == "registry_mints":
        # rule 1-1 / `C20-01`: this project stores no instance rows and MINTS NO
        # INSTANCE IDENTIFIERS. It is the rule the whole R78 verdict rests on, and
        # round 3's P1 found it assertable-and-undetectable.
        return _mutated_guard(InstanceResolution(
            "existing", f"{namespace}:entity:{effective_type}#minted-by-registry",
            None, 1.0, "the registry minted an identifier", (), 1, complete,
            why_incomplete, scanned, tuple(warnings), tier, governed_by))

    return _mutated_guard(InstanceResolution(
        "proposal", None,
        CandidateRef(namespace, "entity", effective_type, candidate, "proposal",
                     context.act_id),
        (scored[0].score if scored else None),
        f"nothing in {scanned} scanned host rows answers to {candidate!r}",
        tuple(scored[:5]), len(scored[:5]), complete, why_incomplete, scanned,
        tuple(warnings), ("" if _mutate == "tier_dropped" else tier), governed_by))


# --------------------------------------------------------------------------------
# The ingest ACT and the LEDGER -- INGEST 4.3
#
# These lived in `ingest_act_probe.py` until round 2. They are here now for the same
# reason the resolver is: round 2 found that the act keyed identity on the raw label
# while the gate keyed it on `norm` (`I-4`), that the act's ledger key did not follow
# the successor chain the read follows (`I-3`), and that the guard's window closed
# when a proposal DRAINED rather than when its identity was WRITTEN (`I-5`). Three
# doors, one question, three answers -- which is exactly what one implementation is
# for. **Standing rule (e)**, in the artefact rather than in the prose.
# --------------------------------------------------------------------------------


@dataclass
class Invocation:
    invocation_id: str
    family: str
    namespace: str
    type_name: str
    label: str
    outcome: str
    approval_mode: str
    warnings: tuple[str, ...]
    kind: str = "entity"
    reviewed_by: str | None = None
    minted_ref: str | None = None          # the `results` slot amendment A2 asks for


@dataclass
class Ledger:
    """`ACTIONS.md`'s ledger, modelled only as far as INGEST 4 needs it."""

    rows: list[Invocation] = field(default_factory=list)

    def record(self, inv: Invocation) -> Invocation:
        self.rows.append(inv)
        return inv

    def unreviewed(self, *, namespace: str | None = None, type_name: str | None = None,
                   label: str | None = None) -> list[Invocation]:
        """What rule 4-11 asked until round 2, kept so `I-5`'s check can go red.

        **This is not rule 4-11's question any more.** It is also not the shipped
        `Registry.invocations`, which takes no `label`, `type_name` or `kind` filter,
        does not page, and returns the OLDEST 100 -- finding B2, and the fourth
        amendment `INGEST.md` 4.4 asks of `ACTIONS.md`.
        """
        out = [i for i in self.rows if i.reviewed_by is None]
        if namespace is not None:
            out = [i for i in out if i.namespace == namespace]
        if type_name is not None:
            out = [i for i in out if i.type_name == type_name]
        if label is not None:
            out = [i for i in out if i.label == label]
        return out

    def open_proposals(self, vocab: Vocabulary, namespace: str, kind: str,
                       type_name: str, label: str, *,
                       raw: bool = False,
                       unreviewed_only: bool = False) -> list[Invocation]:
        """Rule 4-11's question, and `I-5` is the reason it is worded this way.

        *Who already holds a proposal for this identity whose row has NOT been
        written?* -- not *who holds an UNREVIEWED one*. Draining a proposal is the
        right thing to do and it used to stand the guard down at exactly the moment
        the permission was live and unconsumed (standing rule (c)).

        The key runs through `act_key`, so the question follows the successor closure
        (`I-3`) and the scorer's normaliser (`I-4`). ``raw`` and ``unreviewed_only``
        are the mutations.
        """
        want = act_key(vocab, namespace, kind, type_name, label, raw=raw)
        out = []
        for i in self.rows:
            if unreviewed_only:                              # MUTATION: `I-5`
                if i.reviewed_by is not None:
                    continue
            elif i.minted_ref is not None:
                continue                                     # the identity EXISTS now
            if act_key(vocab, i.namespace, i.kind, i.type_name, i.label,
                       raw=raw) == want:
                out.append(i)
        return out


class IngestAct:
    """One ingest act. INGEST 4.3, rules 4-7 and 4-10 … 4-13.

    ``enforce`` is the MUTATION harness: switch a rule off and the check that closes
    it must go red. The ids are `ACT_RULES`.
    """

    def __init__(self, act_id: str, *, host: HostTable, vocab: Vocabulary,
                 ledger: Ledger, namespace: str, type_name: str,
                 enforce: frozenset[str] = ACT_RULES) -> None:
        self.act_id = act_id
        self.host, self.vocab, self.ledger = host, vocab, ledger
        self.namespace, self.type_name = namespace, type_name
        self.enforce = enforce
        self._minted: dict[tuple, CandidateRef] = {}   # rule 4-10's per-act memory
        #: the same memory, carrying the LABEL, so rule 4-10 can ask the gate's
        #: relation rather than compare keys (B1). Rule 4-13 writes both.
        self._seen: dict[tuple, tuple[str, object]] = {}
        self.host_writes: list[str] = []

    def _key(self, type_name: str, label: str) -> tuple:
        return act_key(self.vocab, self.namespace, "entity", type_name, label,
                       raw=("4-10-key" not in self.enforce))

    def _recall(self, type_name: str, label: str):
        """Rule 4-10's lookup, and B1 is why it is a RELATION and not a key.

        The gate's identity relation is ``similar(norm(a), norm(b)) >= match_at``.
        Round 2 keyed the act on ``norm`` **equality** -- the gate's *pre-processor*,
        not the gate -- so an ordinary typo split one identity into two proposals
        while the gate itself called them ``existing``, and ``norm``'s ASCII collapse
        merged two genuinely different non-Latin labels into one. A relation that is
        not an equivalence cannot be a dict key, so the act asks the same question
        the gate asks, over its own (small) per-act memory.
        """
        key = self._key(type_name, label)
        if key in self._minted:
            return key, self._minted[key]
        if "4-10-relation" not in self.enforce:
            return key, None
        entry = self.vocab.entry(self.namespace, type_name)
        if entry is None:
            return key, None
        at = entry.policy.match_at
        want = norm(label)
        for seen_k, (seen_label, ref) in self._seen.items():
            if seen_k[:3] != key[:3]:
                continue
            if similar(want, norm(seen_label)) >= at:
                return key, ref
        return key, None

    def land(self, label: str, *, type_name: str | None = None,
             tier: str = "sonnet") -> tuple[str, object]:
        """Resolve one landed row and, where the rules allow, record a proposal.

        ``type_name`` is per-LAND, not per-act: finding B1 constructed one act
        carrying a `project` and a `task` that share a label, and rule 4-10 without
        the type in its key handed the task the project's `CandidateRef`.
        """
        tname = type_name or self.type_name
        key, recalled = self._recall(tname, label)

        # --- rule 4-10: within one act, an IDENTITY is resolved once -----------
        if "4-10" in self.enforce and recalled is not None:
            return "reused", recalled

        res = resolve_instance(
            label, InstanceContext(act_id=self.act_id, proposed_by="ai:ingest"),
            host=self.host, vocab=self.vocab, namespace=self.namespace,
            type_name=tname, tier=tier)
        if isinstance(res, Refusal):
            return "refused", res

        if res.outcome == "existing":
            # rule 4-13 (B7): `existing` answers with an `InstanceRef`, not a
            # `CandidateRef`, and round 2 worded the memory around the CandidateRef --
            # so the branch that resolves an identity most cheaply-provably was the one
            # branch rule 4-10's scope never reached. On the partner's shape (a note
            # naming one project eight times) that is the COMMON case: eight resolutions
            # and sixteen host reads for one identity.
            if "4-3-eff" in self.enforce:
                self._minted[key] = res.ref
                self._seen[key + (label,)] = (label, res.ref)
            return "existing", res.ref
        if res.outcome == "unknowable":
            return "unknowable", None            # rule 4-7: no proposal, ever
        if res.outcome == "not_an_instance" and "4-7-nai" in self.enforce:
            # rule 4-7's SECOND outcome, finding Z6. The classifier SUCCEEDED and
            # said this is not a thing; proposing over that answer in `auto` mode is
            # how a column header becomes a host row.
            return "not_an_instance", None

        # rule 4-3: the type the host writes under is the EFFECTIVE one the
        # resolution reports, never the declared one (`I-3`).
        eff = (res.candidate.type_name if (res.candidate is not None
                                           and "4-3-eff" in self.enforce) else tname)

        warnings: list[str] = []
        mode = "auto"
        if res.outcome == "ambiguous":
            warnings.append(f"instance_ambiguous_at_proposal:{eff}:{res.known}")
            mode = "review"

        # --- rule 4-11: who already holds an UNWRITTEN proposal for this key? --
        pending = self.ledger.open_proposals(
            self.vocab, self.namespace, "entity", tname, label,
            raw=("4-10-key" not in self.enforce),
            unreviewed_only=("4-11-written" not in self.enforce))
        inv = Invocation(f"inv-{len(self.ledger.rows) + 1}", "propose_instance",
                         self.namespace, eff, label, res.outcome, mode, (),
                         kind="entity")
        if pending and "4-11" in self.enforce:
            warnings.append(f"instance_proposal_pending:{pending[0].invocation_id}")
            inv.warnings = tuple(warnings)
            self.ledger.record(inv)
            # rule 4-13: the memory is written on EVERY branch that answers with a
            # CandidateRef, not only on the one that mints (`I-3`'s rider, finding B5).
            if res.candidate is not None:
                self._minted[key] = res.candidate
                self._seen[key + (label,)] = (label, res.candidate)
            return "pending", inv

        inv.warnings = tuple(warnings)
        self.ledger.record(inv)
        if res.candidate is not None:
            self._minted[key] = res.candidate
            self._seen[key + (label,)] = (label, res.candidate)
        return "proposed", inv

    def host_writes_for(self, inv: Invocation, instance_id: str) -> InstanceRecord:
        """The HOST mints the identifier and the ledger records it. Rules 4-2, 4-3.

        `I-5`: recording `minted_ref` is what closes rule 4-11's window, so the guard
        stands down when the identity EXISTS rather than when a human drained a queue.
        """
        inv.minted_ref = f"{inv.namespace}:{inv.kind}:{inv.type_name}#{instance_id}"
        self.host_writes.append(inv.minted_ref)
        return InstanceRecord(inv.namespace, inv.kind, inv.type_name, instance_id,
                              inv.label, {})
