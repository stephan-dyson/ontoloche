"""INGEST.md v0, the read side -- shapes, the ``Condition`` language, the gate's scorer.

Row 7b. **This module stores nothing and calls nothing.** It holds the printed shapes of
``INGEST.md`` §2, §3, §5, §6 and §8 as frozen dataclasses, the twelve-term ``Condition``
vocabulary with its three-valued evaluator, and the declaration validators the registry
calls at ``propose_type``, ``approve`` and ``import_types``. It imports nothing from
``registry.py``, the way ``edges.py``, ``actions.py`` and ``properties.py`` stand.

**Written from the throwaway kit** (``docs/tools/ingest_probe_kit.py``) rather than from
the prose alone, because the kit is what the spec's design tests ran. Where the build
departs from the kit, the departure is named at the line and in ``7B-RUN.md`` §0.2.

**The host holds the instances** (R78, ``INGEST.md`` §1). Nothing here mints an
instance id: an ``InstanceRecord``'s ``instance_id`` is the host's, opaque, and an
``InstanceRef`` built from it names a host row or nothing.
"""

from __future__ import annotations

import cmath
import decimal
import difflib
import math
import numbers
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .adapter import CandidatePage, CandidateQuery, InstanceRecord
from .edges import InstanceRef, TypeRef

__all__ = [
    "INSTANCE_OUTCOMES",
    "CONDITION_OPERATORS",
    "CONDITION_COMBINATORS",
    "CONDITION_TERMS",
    "INSTANCE_CHAIN_CAP",
    "MATCH_POLICY_KEY",
    "INSTANCE_CONDITION_KEY",
    "InstanceRecord",
    "CandidateQuery",
    "CandidatePage",
    "InstanceContext",
    "CandidateRef",
    "InstanceCandidate",
    "InstanceResolution",
    "InstanceLookup",
    "INGEST_LANDINGS",
    "IngestLanding",
    "MatchPolicy",
    "Condition",
    "ConditionResult",
    "condition_problem",
    "condition_from_mapping",
    "match_policy_problem",
    "match_policy_from_mapping",
    "entry_declaration_problem",
    "evaluate",
    "norm",
    "similar",
    "names_a_class",
    "record_ref",
]

#: INGEST.md 3.1, rule 3-1 (`C20-15`). Closed at five; a sixth is a §-row change.
INSTANCE_OUTCOMES = ("existing", "ambiguous", "proposal", "not_an_instance", "unknowable")

#: INGEST.md 6, rule 6-1 (`C20-42`). Ten operators over ONE record's attribute values...
CONDITION_OPERATORS = (
    "eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte", "is_null", "is_not_null",
)
#: ...and two combinators. There is no `not` and no `matches` (rule 6-13, `C20-54`).
CONDITION_COMBINATORS = ("all_of", "any_of")
CONDITION_TERMS = CONDITION_OPERATORS + CONDITION_COMBINATORS

#: The six comparisons that refuse a null operand at declaration (rule 6-6, `C20-47`).
_COMPARISONS = ("eq", "ne", "lt", "lte", "gt", "gte")

#: INGEST.md 3.4a rule 3-16 (`C20-77`). The hop cap ADOPTED from `registry.py`'s
#: `_IDENTITY_CHAIN_CAP`, at its shipped value -- R87's adopt/decline enumeration
#: (ING12). Held equal to the registry's constant by a contract test rather than by an
#: import, because this module imports nothing from the registry.
INSTANCE_CHAIN_CAP = 16

#: Where the two governed facts live on a `kind="entity"` entry's `attributes`. Row 7b's
#: choice (7B-RUN §0.2 item 6): `attributes` is the shipped carrier of every other
#: governed declaration, and it rides propose -> approve unchanged.
MATCH_POLICY_KEY = "match_policy"
INSTANCE_CONDITION_KEY = "instance_condition"


# ------------------------------------------------------------------------- §8 shapes


@dataclass(frozen=True)
class InstanceContext:
    """The ``ResolveContext`` analogue, and deliberately NOT that object. INGEST.md §8.

    ``row_attributes`` is carried and **not read** by v0: that is Q92, recorded and not
    fixed on this row (brief §2).
    """

    label_source: str | None = None
    row_attributes: dict = field(default_factory=dict)
    siblings: tuple[tuple[str, str], ...] = ()
    act_id: str = ""
    proposed_by: str | None = None


@dataclass(frozen=True)
class CandidateRef:
    """INGEST.md §4.1. A thing that does NOT exist yet, and never acquires an id.

    Built on row 7b only as ``InstanceResolution.candidate``'s carrier (7B-RUN §0.2
    item 2). Its rules -- 4-9 and the act around it -- are row 7c's.
    """

    type: TypeRef
    label: str
    resolution: str
    act_id: str


@dataclass(frozen=True)
class InstanceCandidate:
    ref: InstanceRef
    label: str
    score: float
    discriminators: dict


@dataclass(frozen=True)
class InstanceResolution:
    """``resolve_instance``'s answer. INGEST.md §3 and §8."""

    outcome: str
    ref: InstanceRef | None
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
    governed_by: str


@dataclass(frozen=True)
class InstanceLookup:
    """``get_instance_checked``'s answer. Row 7b, ``INGEST.md`` §8 (finding 2).

    Rule 2-15 says a record the predicate fails is *"`None` with a why"*, and a bare
    ``None`` has nowhere to put the why. ``record`` is the host row or ``None``;
    ``ref`` is its reference under the name the closure resolves to; ``why`` is empty
    when ``record`` is present. ``governed_by`` names the entry whose predicate judged
    it (rule 5-11's carrier, at primitive 22's door).
    """

    record: InstanceRecord | None
    ref: InstanceRef | None
    why: str
    governed_by: str
    warnings: tuple[str, ...]


#: Row 7c. What one ``IngestAct.land`` did, closed. ``existing``: the gate named a host
#: row. ``proposed``: a propose invocation was recorded. ``pending``: one was recorded
#: carrying ``instance_proposal_pending`` because an earlier proposal for the identity
#: is unwritten (rule 4-11), so it holds no permission. ``reused``: rule 4-10's per-act
#: memory answered and nothing was read or recorded. ``unknowable`` / ``not_an_instance``:
#: rule 4-7, nothing recorded. ``refused``: a refusal (the resolution's, the gate's or
#: the ledger's) and nothing recorded.
INGEST_LANDINGS = (
    "existing", "proposed", "pending", "reused", "unknowable", "not_an_instance", "refused",
)


@dataclass(frozen=True)
class IngestLanding:
    """``IngestAct.land``'s answer. INGEST.md §8, row 7c.

    ``resolution`` is ``None`` for ``reused`` (the memory answered, nothing was
    resolved) and for a ``refused`` that ``resolve_instance`` itself refused. ``ref`` is
    set for ``existing`` and for a ``reused`` that recalled one; ``candidate`` for
    ``proposed``, ``pending``, a ``reused`` that recalled one, and a ``refused`` after
    the resolution (at preflight, at A4's read or at the record);
    ``invocation`` for ``proposed`` and ``pending`` only. ``refusal`` carries the refusal
    behind a ``refused`` landing. ``why`` is never empty.
    """

    outcome: str
    resolution: InstanceResolution | None
    ref: InstanceRef | None
    candidate: CandidateRef | None
    invocation: Any
    why: str
    refusal: Any = None


# ----------------------------------------------------------------------- §5 the gate


@dataclass(frozen=True)
class MatchPolicy:
    """INGEST.md §5. Declared on the entry; ``resolve_instance`` takes no threshold."""

    match_at: float
    propose_below: float
    ambiguity_margin: float
    why: str


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def match_policy_problem(declared: Any) -> str | None:
    """Why ``declared`` is not a valid ``MatchPolicy`` mapping, or ``None``.

    Rules 5-2 (`C20-36`, ``propose_below <= match_at``) and 5-3 (`C20-37`, ``why``
    required and non-empty), plus the closed shape: three thresholds in ``[0, 1]`` and
    nothing else.
    """
    if not isinstance(declared, Mapping):
        return f"{MATCH_POLICY_KEY} must be a mapping, got {type(declared).__name__}"
    expected = {"match_at", "propose_below", "ambiguity_margin", "why"}
    extra = sorted(set(declared) - expected)
    if extra:
        return f"{MATCH_POLICY_KEY} carries keys MatchPolicy does not have: {extra}"
    for key in ("match_at", "propose_below", "ambiguity_margin"):
        if key not in declared:
            return f"{MATCH_POLICY_KEY}.{key} is required"
        value = declared[key]
        if not _is_number(value) or not 0.0 <= float(value) <= 1.0:
            return f"{MATCH_POLICY_KEY}.{key} must be a number in [0, 1], got {value!r}"
    if float(declared["propose_below"]) > float(declared["match_at"]):
        return (
            f"{MATCH_POLICY_KEY}.propose_below ({declared['propose_below']}) exceeds "
            f"match_at ({declared['match_at']}): rule 5-2"
        )
    why = declared.get("why")
    if not isinstance(why, str) or not why.strip():
        return f"{MATCH_POLICY_KEY}.why is required and non-empty: rule 5-3"
    return None


def match_policy_from_mapping(declared: Mapping[str, Any]) -> MatchPolicy:
    """Assumes ``match_policy_problem(declared) is None``."""
    return MatchPolicy(
        match_at=float(declared["match_at"]),
        propose_below=float(declared["propose_below"]),
        ambiguity_margin=float(declared["ambiguity_margin"]),
        why=str(declared["why"]),
    )


# ---------------------------------------------------------------------- §6 Condition


@dataclass(frozen=True)
class Condition:
    """INGEST.md §6, R60. One language, twelve terms, three-valued.

    The dataclass is permissive; **declaration** is where a malformed one is refused
    (``condition_problem``, called by the registry at its three write doors, refusing
    ``attributes_schema_violation`` -- §9: *a malformed `Condition` mints nothing*).
    """

    op: str
    attribute: str | None = None
    value: Any | None = None
    terms: tuple["Condition", ...] = ()
    why: str = ""


@dataclass(frozen=True)
class ConditionResult:
    holds: bool | None
    why: str
    unreadable: tuple[str, ...] = ()


def condition_problem(declared: Any, *, _path: str = INSTANCE_CONDITION_KEY) -> str | None:
    """Why ``declared`` is not a valid ``Condition`` mapping, or ``None``.

    Rules 6-1 and 6-6 to 6-11 (`C20-42`, `C20-47` to `C20-52`), recursively.
    """
    if not isinstance(declared, Mapping):
        return f"{_path} must be a mapping, got {type(declared).__name__}"
    extra = sorted(set(declared) - {"op", "attribute", "value", "terms", "why"})
    if extra:
        return f"{_path} carries keys Condition does not have: {extra}"
    op = declared.get("op")
    if op not in CONDITION_TERMS:
        return (
            f"{_path}.op={op!r} is not one of the twelve terms "
            f"({', '.join(CONDITION_TERMS)}): rule 6-1"
        )
    why = declared.get("why")
    if not isinstance(why, str) or not why.strip():
        return f"{_path}.why is required and non-empty: rule 6-11"
    attribute = declared.get("attribute")
    value = declared.get("value")
    terms = declared.get("terms")
    if op in CONDITION_COMBINATORS:
        if attribute is not None or value is not None:
            return f"{_path}: {op} takes terms, never an attribute or a value: rule 6-9"
        if not isinstance(terms, (list, tuple)) or not terms:
            return f"{_path}: {op} with no terms: rule 6-8"
        for i, term in enumerate(terms):
            problem = condition_problem(term, _path=f"{_path}.terms[{i}]")
            if problem:
                return problem
        return None
    if terms not in (None, (), []):
        return f"{_path}: {op} is an operator and takes no terms: rule 6-10"
    if not isinstance(attribute, str) or not attribute.strip():
        return f"{_path}: {op} needs a non-empty attribute"
    if op in ("is_null", "is_not_null"):
        if value is not None:
            return f"{_path}: {op} takes no value"
        return None
    if value is None:
        return (
            f"{_path}: {op} may not take a null operand -- use is_null / is_not_null: "
            "rule 6-6"
        )
    if op in ("in", "not_in"):
        if not isinstance(value, (list, tuple)):
            return f"{_path}: {op} takes a sequence, got {type(value).__name__}: rule 6-7"
        if any(v is None for v in value):
            return f"{_path}: {op} may not carry a null member: rule 6-6"
    if _non_finite(value):
        # NaN equals nothing, itself included, so a predicate carrying it could never
        # be compared with its own copy (rule 3-18) and `eq NaN` holds for no row.
        return f"{_path}: {op} may not carry a non-finite number"
    return None


def _non_finite(value: Any, _seen: frozenset = frozenset()) -> bool:
    """A NaN or an infinity anywhere in an operand (round 4: a mapping member, a nested
    sequence, and `Decimal("NaN")` were let through; round 5: a complex number, any
    `numbers.Real` that is not a float, a set member, a mapping key, and a sequence
    that contains itself, which raised `RecursionError`)."""
    if isinstance(value, numbers.Integral):
        return False             # bool included; float(10**400) would overflow
    if isinstance(value, decimal.Decimal):
        return not value.is_finite()
    if isinstance(value, numbers.Real):
        return not math.isfinite(float(value))
    if isinstance(value, numbers.Complex):
        return not cmath.isfinite(complex(value))
    if isinstance(value, (Mapping, list, tuple, set, frozenset)):
        if id(value) in _seen:
            return True          # a self-containing operand is no comparable value
        seen = _seen | {id(value)}
        members = (list(value.keys()) + list(value.values())
                   if isinstance(value, Mapping) else list(value))
        return any(_non_finite(v, seen) for v in members)
    return False


def condition_from_mapping(declared: Mapping[str, Any]) -> Condition:
    """Assumes ``condition_problem(declared) is None``."""
    terms = tuple(condition_from_mapping(t) for t in (declared.get("terms") or ()))
    value = declared.get("value")
    if isinstance(value, list):
        value = tuple(value)
    return Condition(
        op=declared["op"],
        attribute=declared.get("attribute"),
        value=value,
        terms=terms,
        why=declared["why"],
    )


def entry_declaration_problem(kind: str, attributes: Mapping[str, Any] | None) -> str | None:
    """The first breach in an entry's governed instance facts, or ``None``.

    Called by the registry at ``propose_type``, ``approve`` and ``import_types``. Only a
    ``kind="entity"`` entry may declare either key: an ``InstanceRef``'s type MUST be an
    entity (``EDGES.md`` §2.1), so a policy on any other kind governs nothing.
    """
    attributes = attributes or {}
    present = [k for k in (MATCH_POLICY_KEY, INSTANCE_CONDITION_KEY) if k in attributes]
    if not present:
        return None
    if kind != "entity":
        return (
            f"{present[0]} is declared on a kind={kind!r} entry; only a kind='entity' "
            "entry has instances (EDGES.md 2.1)"
        )
    if MATCH_POLICY_KEY in attributes:
        problem = match_policy_problem(attributes[MATCH_POLICY_KEY])
        if problem:
            return problem
    if INSTANCE_CONDITION_KEY in attributes:
        problem = condition_problem(attributes[INSTANCE_CONDITION_KEY])
        if problem:
            return problem
    return None


def evaluate(cond: Condition, attributes: Mapping[str, Any]) -> ConditionResult:
    """Three-valued, in the REGISTRY, over ONE record's attributes. Rules 6-2 to 6-5.

    **Readable is per record** (7B-RUN §0.2 item 8): an attribute is readable when the
    record carries the key, null or not. A key the record does not carry is
    ``unknowable``, never absent-and-therefore-false (rule 6-4, `C20-45`). A readable
    null makes every comparison ``unknowable`` and ``is_null`` answers it as a fact
    (rule 6-5, `C20-46`). Composition is Kleene (rule 6-12, `C20-53`).
    """
    if cond.op in CONDITION_COMBINATORS:
        results = [evaluate(t, attributes) for t in cond.terms]
        unreadable = tuple(sorted({a for r in results for a in r.unreadable}))
        vals = [r.holds for r in results]
        if cond.op == "all_of":
            holds = False if False in vals else (None if None in vals else True)
        else:
            holds = True if True in vals else (None if None in vals else False)
        why = ""
        if holds is None:
            why = f"{cond.op}: undecidable -- " + "; ".join(
                r.why for r in results if r.holds is None
            )
        return ConditionResult(holds, why, unreadable)

    attribute = cond.attribute or ""
    if attribute not in attributes:
        return ConditionResult(
            None,
            f"{attribute!r} is not readable on this record: the host does not carry it, "
            "so this condition is unknowable rather than false",
            (attribute,),
        )
    got = attributes[attribute]
    if cond.op == "is_null":
        return ConditionResult(got is None, "")
    if cond.op == "is_not_null":
        return ConditionResult(got is not None, "")
    if got is None:
        return ConditionResult(
            None, f"{attribute!r} is null; {cond.op} against null is unknowable"
        )
    try:
        if cond.op == "eq":
            return ConditionResult(got == cond.value, "")
        if cond.op == "ne":
            return ConditionResult(got != cond.value, "")
        if cond.op == "in":
            return ConditionResult(got in tuple(cond.value), "")
        if cond.op == "not_in":
            return ConditionResult(got not in tuple(cond.value), "")
        if cond.op == "lt":
            return ConditionResult(bool(got < cond.value), "")
        if cond.op == "lte":
            return ConditionResult(bool(got <= cond.value), "")
        if cond.op == "gt":
            return ConditionResult(bool(got > cond.value), "")
        if cond.op == "gte":
            return ConditionResult(bool(got >= cond.value), "")
    except TypeError as exc:
        return ConditionResult(None, f"{attribute!r}: {exc}")
    raise AssertionError(cond.op)  # pragma: no cover - condition_problem guards it


# ------------------------------------------------------------------- §3 the scorer


#: INGEST.md 3.3's classifier, exactly the eleven words round 1 measured (M9: 0 of
#: 14,498 false positives, 22 of 23 CMS headers missed). **v0 does not define the
#: classifier**; this is the one the spec's numbers were taken against, and Q86 asks
#: whether the project should ship one at all.
_CLASS_WORDS = frozenset({
    "facility", "provider", "provider name", "nursing home", "nursing facility",
    "hospital", "organisation", "organization", "entity", "name", "id",
})


def norm(text: str) -> str:
    """The gate's normaliser. **Unicode-aware**, which is the kit's one departure.

    The kit's ``[^a-z0-9]+`` collapse refused ``'状态'`` as a class word (ING3, K10) --
    ``C4-14``'s defect in its other direction. ``[\\W_]+`` over ``casefold()`` gives the
    kit's answer on every ASCII string and keeps a non-Latin name a name.
    """
    return re.sub(r"[\W_]+", " ", (text or "").casefold()).strip()


def similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def names_a_class(candidate: str) -> bool:
    """Rule 3-8 (`C20-22`): decided without reading the host table at all."""
    key = norm(candidate)
    return not key or key in _CLASS_WORDS


def record_ref(rec: InstanceRecord) -> InstanceRef:
    """The reference a host record is named by. The id is the HOST's (rule 1-1)."""
    return InstanceRef(TypeRef(rec.namespace, rec.kind, rec.type_name), rec.instance_id)
