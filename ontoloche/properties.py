"""Property declarations -- INTERFACE.md 2.10, ruling R108, built by row 8c.

**What a property *is*, never what it holds.** An entity's properties are governed
vocabulary: a ``kind="entity"`` entry may declare its slots, which of them identify a
row (``primary_key``) and which one names it (``title_property``), and a property used
by several entities in one namespace may be registered once as a ``kind="property"``
entry. **No value is ever stored or checked** (rule 2.10-13, ruling R78).

**Pure.** Nothing here touches a registry or an adapter, so nothing here can write, and
nothing here needs mirroring into ``ontoloche/aio``: the precedent is ``edges.py`` and
``actions.py``. Rule 2.10-11's reader needs the store, so it lives in ``registry.py``
(``Registry._property_reference``), which ``tools/unasync.py`` mirrors.

What is *stored* is plain JSON under the reserved keys, so, like ``edges`` and unlike
``actions.action_attributes``, there is no writer helper: the caller writes the dict.
What a reader gets back is the typed view this module builds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ._resolve import identity_key

__all__ = [
    "BASE_TYPES",
    "ENTITY_KEYS",
    "PROPERTY_KEYS",
    "SLOT_FIELDS",
    "PropertySpec",
    "EntityDeclaration",
    "SharedPropertyDeclaration",
    "entity_declaration",
    "shared_property_declaration",
    "declaration_problem",
    "missing_descriptions",
    "references",
]

#: INTERFACE.md 2.10. Closed. Seven are ``FieldSpec``'s own (``ontoloche/attributes.py``),
#: so a property and an attribute schema share one type vocabulary; ``date``,
#: ``decimal`` and ``opaque`` are added, and ``opaque`` means *this registry cannot
#: type it*, with ``source_type`` saying what it is.
BASE_TYPES = (
    "str", "int", "float", "decimal", "bool", "date", "datetime", "list", "dict", "opaque",
)

#: Rule 2.10-7: the types an enumeration may be declared on.
VALUE_SET_TYPES = frozenset({"str", "int", "decimal", "date"})

#: Rule 2.10-1: the reserved keys of each kind's ``attributes``.
ENTITY_KEYS = ("properties", "primary_key", "title_property")
PROPERTY_KEYS = ("base_type", "display_name", "item_type", "value_set", "source_type")

#: Rule 2.10-3: a slot's keys are ``PropertySpec``'s nine fields and no others.
SLOT_FIELDS = (
    "name", "required", "shared", "base_type", "description", "display_name",
    "item_type", "value_set", "source_type",
)
#: The fields a shared slot may not carry, because each has one home: the property's
#: own entry (rule 2.10-3).
_SHARED_FORBIDS = ("base_type", "description", "item_type", "value_set", "source_type")

#: Rule 2.10-4. Mixed case, because a slot carries the source's identifier.
SLOT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
#: Rule 2.10-8: a reference is a bare word in INTERFACE.md 2.1's pattern.
WORD_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True)
class PropertySpec:
    """One slot, as the view returns it (INTERFACE.md 2.10)."""

    name: str
    #: The view returns True for a slot named in ``primary_key`` (rule 2.10-5).
    required: bool = False
    shared: str | None = None
    base_type: str | None = None
    description: str | None = None
    display_name: str | None = None
    item_type: str | None = None
    value_set: str | None = None
    source_type: str | None = None


@dataclass(frozen=True)
class EntityDeclaration:
    """A ``kind="entity"`` entry's declaration, read as a view."""

    properties: tuple[PropertySpec, ...] | None
    primary_key: tuple[str, ...] | None
    title_property: str | None
    #: reserved key -> why that key is None: ``"not_stored"`` (rule 2.10-16) or
    #: ``"breaches:2.10-N"``. Empty when nothing is absent for a reason.
    why_absent: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SharedPropertyDeclaration:
    """A ``kind="property"`` entry's declaration, read as a view."""

    base_type: str | None
    display_name: str | None
    item_type: str | None
    value_set: str | None
    source_type: str | None
    why_absent: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------- helpers


def _present(attributes: dict, key: str) -> bool:
    """Rule 2.10-3: a JSON ``null`` reads as absent."""
    return attributes.get(key) is not None


def _blank(value: Any) -> bool:
    """Rule 2.10-3: an empty or whitespace-only description is a missing one."""
    return value is None or (isinstance(value, str) and not value.strip())


def _word_ok(word: Any) -> bool:
    """Rule 2.10-8: pattern-legal and its own ``identity_key``."""
    return isinstance(word, str) and bool(WORD_RE.fullmatch(word)) and identity_key(word) == word


def _key_shape_problem(attributes: dict) -> list[tuple[str, str, str | None, str]]:
    """Rule 2.10-1's shape check of ``primary_key`` and ``title_property``."""
    out = []
    if _present(attributes, "primary_key"):
        pk = attributes["primary_key"]
        if (
            not isinstance(pk, list)
            or not pk
            or not all(isinstance(n, str) and n for n in pk)
            or len(set(pk)) != len(pk)
        ):
            out.append((
                "2.10-1", "primary_key", None,
                "primary_key must be a non-empty list of distinct non-empty strings",
            ))
    if _present(attributes, "title_property"):
        title = attributes["title_property"]
        if not isinstance(title, str) or not title:
            out.append((
                "2.10-1", "title_property", None,
                "title_property must be one non-empty string",
            ))
    return out


def _type_problem(
    spec: dict, *, slot: str | None, key: str, rule_for_base: str
) -> tuple[str, str, str | None, str] | None:
    """Rules 2.10-6, 2.10-7, 2.10-8 over one local slot or one property entry.

    On a slot every breach names ``properties`` (the reserved key that holds it) and the
    slot. On a property entry it names the offending key itself, ``item_type``,
    ``source_type`` or ``value_set`` (row 8c round 1, lens A finding 4).
    """
    def at(own: str) -> str:
        return key if slot is not None else own

    base = spec.get("base_type")
    if base not in BASE_TYPES:
        return (
            rule_for_base, at("base_type"), slot,
            f"base_type must be one of {', '.join(BASE_TYPES)}; got {base!r}",
        )
    item = spec.get("item_type")
    if base == "list":
        if item is None:
            return ("2.10-6", at("item_type"), slot, "a list declares an item_type")
        if item not in BASE_TYPES or item == "list":
            return ("2.10-6", at("item_type"), slot, f"item_type must be a BASE_TYPES value other than list; got {item!r}")
    elif item is not None:
        return ("2.10-6", at("item_type"), slot, "item_type is present exactly when base_type is list")
    if "opaque" in (base, item) and _blank(spec.get("source_type")):
        return ("2.10-6", at("source_type"), slot, "opaque requires a non-empty source_type")
    if spec.get("value_set") is not None:
        typed = item if base == "list" else base
        if typed not in VALUE_SET_TYPES:
            return (
                "2.10-7", at("value_set"), slot,
                f"a value_set may be declared on str, int, decimal or date; got {typed!r}",
            )
        if not _word_ok(spec["value_set"]):
            return (
                "2.10-8", at("value_set"), slot,
                f"value_set must be a bare word that is its own identity_key; got {spec['value_set']!r}",
            )
    return None


def _slot_problems(slots: Any) -> list[tuple[str, str, str | None, str]]:
    """Rules 2.10-3, 2.10-4, 2.10-6, 2.10-7 and 2.10-8 over ``properties``."""
    if not isinstance(slots, list):
        return [("2.10-3", "properties", None, "properties must be a list")]
    out = []
    seen: set[str] = set()
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict):
            out.append(("2.10-3", "properties", f"#{index}", "each slot is a dict"))
            continue
        name = slot.get("name")
        label = name if isinstance(name, str) and name else f"#{index}"
        unknown = sorted(str(k) for k in slot if k not in SLOT_FIELDS)
        if unknown:
            out.append(("2.10-3", "properties", label, f"unknown slot key(s): {', '.join(unknown)}"))
            continue
        if not isinstance(name, str) or not name:
            out.append(("2.10-3", "properties", label, "every slot declares a non-empty name"))
            continue
        if slot.get("required") is not None and not isinstance(slot["required"], bool):
            out.append(("2.10-3", "properties", label, "required is a bool"))
            continue
        bad = [
            k for k in SLOT_FIELDS
            if k not in ("name", "required") and slot.get(k) is not None
            and not isinstance(slot[k], str)
        ]
        if bad:
            out.append(("2.10-3", "properties", label, f"{', '.join(bad)} must be a string"))
            continue
        if not SLOT_NAME_RE.fullmatch(name):
            out.append(("2.10-4", "properties", label, f"slot name must match {SLOT_NAME_RE.pattern}"))
            continue
        if name in seen:
            out.append(("2.10-4", "properties", label, "slot names are unique within one entity"))
            continue
        seen.add(name)
        if slot.get("shared") is not None:
            # A blank description is a MISSING one at every door (rule 2.10-3), so a
            # shared slot carrying "" or whitespace carries nothing (round 1, A3).
            carried = [
                k for k in _SHARED_FORBIDS
                if slot.get(k) is not None and not (k == "description" and _blank(slot[k]))
            ]
            if carried:
                out.append((
                    "2.10-3", "properties", label,
                    f"a shared slot declares none of {', '.join(_SHARED_FORBIDS)}; "
                    f"it carries {', '.join(carried)}",
                ))
                continue
            if not _word_ok(slot["shared"]):
                out.append((
                    "2.10-8", "properties", label,
                    f"shared must be a bare word that is its own identity_key; got {slot['shared']!r}",
                ))
            continue
        problem = _type_problem(slot, slot=label, key="properties", rule_for_base="2.10-3")
        if problem is not None:
            out.append(problem)
    return out


def _key_membership_problem(attributes: dict) -> list[tuple[str, str, str | None, str]]:
    """Rule 2.10-5, only when ``properties`` is present and itself well formed."""
    slots = {s["name"]: s for s in attributes["properties"]}
    out = []
    pk = attributes.get("primary_key")
    if pk is not None:
        missing = [n for n in pk if n not in slots]
        if missing:
            out.append(("2.10-5", "primary_key", missing[0], "primary_key names a slot properties does not declare"))
        else:
            loose = [n for n in pk if slots[n].get("required") is False]
            if loose:
                out.append(("2.10-5", "primary_key", loose[0], "a key slot is required by being in the key"))
    title = attributes.get("title_property")
    if title is not None and title not in slots:
        out.append(("2.10-5", "title_property", title, "title_property names a slot properties does not declare"))
    return out


# ------------------------------------------------------------------- the checks


def entity_problems(attributes: dict) -> list[tuple[str, str, str | None, str]]:
    """Every breach of a ``kind="entity"`` declaration, as ``(rule, key, slot, why)``.

    Rule 2.10-1's shape check first, then the slots, then rule 2.10-5. Rule 2.10-5 is
    checked only when ``properties`` is present and well formed: with no slots, an
    entity declaring ``primary_key`` or ``title_property`` alone is the shape written
    before the amendment and its names are not checked against slots (rule 2.10-1).
    """
    out = _key_shape_problem(attributes)
    if _present(attributes, "properties"):
        slot_problems = _slot_problems(attributes["properties"])
        out.extend(slot_problems)
        if not slot_problems:
            shaped = {k for _, k, _, _ in out}
            membership = [
                p for p in _key_membership_problem(attributes) if p[1] not in shaped
            ]
            out.extend(membership)
    return out


def property_problem(attributes: dict) -> tuple[str, str, str | None, str] | None:
    """The breach of a ``kind="property"`` entry's declaration, rule 2.10-9."""
    if attributes.get("required") is not None:
        return ("2.10-9", "required", None, "required belongs to the slot, never to the shared property")
    if not any(_present(attributes, k) for k in PROPERTY_KEYS):
        return None  # declares nothing: legal, ACTIONS.md 2.2-1's decision
    bad = [k for k in PROPERTY_KEYS if _present(attributes, k) and not isinstance(attributes[k], str)]
    if bad:
        return ("2.10-9", bad[0], None, f"{', '.join(bad)} must be a string")
    return _type_problem(attributes, slot=None, key="base_type", rule_for_base="2.10-9")


def declaration_problem(kind: str, attributes: dict) -> tuple[str, str, str | None, str] | None:
    """The first breach of rules 2.10-1 and 2.10-3 to 2.10-9, or None. Rule 2.10-2.

    ``(rule, key, slot, why)``. A missing description is **not** a breach here: it is
    refused at ``propose_type`` and ``approve`` through :func:`missing_descriptions`,
    and ``import_types`` is rule 2.10-21's, reserved.
    """
    attributes = attributes or {}
    if kind == "entity":
        problems = entity_problems(attributes)
        return problems[0] if problems else None
    if kind == "property":
        return property_problem(attributes)
    return None


def missing_descriptions(attributes: dict) -> list[str]:
    """The local slots with no description (absent, null, empty or whitespace)."""
    slots = (attributes or {}).get("properties")
    if not isinstance(slots, list):
        return []
    return [
        s["name"] for s in slots
        if isinstance(s, dict) and s.get("shared") is None and _blank(s.get("description"))
    ]


def references(kind: str, attributes: dict) -> list[tuple[str, str, str]]:
    """``(slot label, word, referenced kind)`` for each ``shared`` and ``value_set``.

    ``*`` labels a ``kind="property"`` entry's own ``value_set`` (rule 2.10-10), and
    matches no slot name. Call only on a declaration with no breach.
    """
    attributes = attributes or {}
    out: list[tuple[str, str, str]] = []
    if kind == "entity" and isinstance(attributes.get("properties"), list):
        for slot in attributes["properties"]:
            if slot.get("shared") is not None:
                out.append((slot["name"], slot["shared"], "property"))
            if slot.get("value_set") is not None:
                out.append((slot["name"], slot["value_set"], "value_set"))
    elif kind == "property" and attributes.get("value_set") is not None:
        out.append(("*", attributes["value_set"], "value_set"))
    return out


# ---------------------------------------------------------------------- the views


def _kind_of(entry: Any) -> str:
    return getattr(entry, "kind", None)


def entity_declaration(entry: Any, caps: Any) -> EntityDeclaration:
    """The view of a ``kind="entity"`` entry's declaration. INTERFACE.md 2.10.

    Raises ``ValueError`` on an entry of another kind, the way a caller's mistake is
    reported. **Never raises on stored data**: a stored key that breaks a rule comes
    back ``None`` with ``why_absent[key]`` naming it. A key ``caps`` cannot store comes
    back ``None`` with ``why_absent[key] == "not_stored"`` (rule 2.10-16).
    """
    if _kind_of(entry) != "entity":
        raise ValueError(f"entity_declaration reads a kind='entity' entry, got {_kind_of(entry)!r}")
    attributes = dict(getattr(entry, "attributes", None) or {})
    why: dict[str, str] = {}
    held: dict[str, Any] = {}
    for key in ENTITY_KEYS:
        if not caps.stores_attribute(key):
            why[key] = "not_stored"
        elif _present(attributes, key):
            held[key] = attributes[key]
    # Rule 2.10-1's shape check, key by key.
    for rule, key, _slot, _why in _key_shape_problem(held):
        held.pop(key, None)
        why.setdefault(key, f"breaches:{rule}")
    if "properties" in held:
        problems = _slot_problems(held["properties"])
        if problems:
            held.pop("properties")
            why["properties"] = f"breaches:{problems[0][0]}"
        else:
            # Rule 2.10-5 nulls the key or the title, never properties.
            for rule, key, _slot, _why in _key_membership_problem(held):
                if key in held:
                    held.pop(key)
                    why.setdefault(key, f"breaches:{rule}")
    properties = None
    if "properties" in held:
        pk = set(held.get("primary_key") or ())
        properties = tuple(
            PropertySpec(
                name=s["name"],
                required=True if (s["name"] in pk and s.get("required") is None)
                else bool(s.get("required") or False),
                shared=s.get("shared"),
                base_type=s.get("base_type"),
                description=None if _blank(s.get("description")) else s.get("description"),
                display_name=s.get("display_name"),
                item_type=s.get("item_type"),
                value_set=s.get("value_set"),
                source_type=s.get("source_type"),
            )
            for s in held["properties"]
        )
    pk = held.get("primary_key")
    return EntityDeclaration(
        properties=properties,
        primary_key=tuple(pk) if pk is not None else None,
        title_property=held.get("title_property"),
        why_absent=why,
    )


def shared_property_declaration(entry: Any, caps: Any) -> SharedPropertyDeclaration:
    """The view of a ``kind="property"`` entry's declaration. INTERFACE.md 2.10.

    A breach of rule 2.10-9 (or of 2.10-6 to 2.10-8 through it) nulls **every**
    reserved key, recorded once under ``why_absent["base_type"]`` naming the rule.
    """
    if _kind_of(entry) != "property":
        raise ValueError(
            f"shared_property_declaration reads a kind='property' entry, got {_kind_of(entry)!r}"
        )
    attributes = dict(getattr(entry, "attributes", None) or {})
    why: dict[str, str] = {}
    held: dict[str, Any] = {}
    for key in PROPERTY_KEYS:
        if not caps.stores_attribute(key):
            why[key] = "not_stored"
        elif _present(attributes, key):
            held[key] = attributes[key]
    if caps.stores_attribute("required") and attributes.get("required") is not None:
        held["required"] = attributes["required"]
    problem = property_problem(held)
    held.pop("required", None)
    if problem is not None:
        held = {}
        why["base_type"] = f"breaches:{problem[0]}"
    return SharedPropertyDeclaration(
        base_type=held.get("base_type"),
        display_name=held.get("display_name"),
        item_type=held.get("item_type"),
        value_set=held.get("value_set"),
        source_type=held.get("source_type"),
        why_absent=why,
    )
