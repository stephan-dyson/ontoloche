"""Read a Foundry ``OntologyFullMetadata`` document and plan what it imports as. Row 8a.

**Pure.** Nothing here touches a registry or an adapter, so nothing here can write.
``Registry.import_foundry`` calls :func:`plan`, asks the store what it already holds,
and only then, when ``dry_run=False``, hands the planned rows to **one**
``import_types`` call (``8A-RUN.md`` §0.5 item 1). This module is a planner in front of
the existing import door, not a new door.

The mapping is ``8A-RUN.md`` §0.2, fixed before the code:

* interface type -> ``kind="predicate"``
* object type -> ``kind="entity"``, its implemented interfaces as predicates, and its
  properties carried verbatim and marked not validated (R105's interim ``carry``)
* link type -> ``kind="edge"``, one family per ``linkTypeRid``, both sides paired
* action type -> ``kind="action"`` declaring **none** of ``ACTIONS.md`` §2.2's keys,
  with the ``Effect.op`` each logic rule *would* map to reported, not declared
* query types, shared property types and value types -> counted, not imported

Four holds happen here and write nothing: ``definition_missing`` (R109),
``name_collision_after_conversion`` (R110), ``name_invalid`` and
``status_not_imported``. The caller lifts the first two with ``definitions=`` and
``names=``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

#: INTERFACE.md 2.1's name rule. Restated rather than imported from ``registry`` so this
#: module stays importable on its own. ``C12-37`` holds the two to the same answers.
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

#: The statuses ``import_types`` maps (INTERFACE.md 2.5 plus row 8a's ``endorsed``).
#: The published ``ReleaseStatus`` has exactly these four. Anything else is held here,
#: not guessed, and ``import_types`` refuses it as well if it is called directly.
KNOWN_STATUSES = ("ACTIVE", "ENDORSED", "EXPERIMENTAL", "DEPRECATED")

#: The four reasons a row is held before ``import_types`` is called.
HOLD_REASONS = (
    "definition_missing",
    "name_collision_after_conversion",
    "name_invalid",
    "status_not_imported",
)

#: The order rows are handed to ``import_types``: a predicate exists before the entity
#: declaring it, and an entity before the edge family naming it as an endpoint.
KIND_ORDER = ("predicate", "entity", "edge", "action")

#: Brief question 4, interim and REPORTED ONLY (``8A-RUN.md`` §0.7). Imported action
#: families declare no effects, so nothing in this row refuses on this table.
LINK_ADD_RULES = frozenset({"createLink", "addLink"})
LINK_REMOVE_RULES = frozenset({"deleteLink", "removeLink"})

#: Object type keys mapped to a field of their own. Every other key is carried in
#: ``attributes["foundry_object_type"]``, so nothing Foundry said is dropped.
_OBJECT_TYPE_MAPPED = frozenset(
    {"apiName", "rid", "description", "status", "visibility", "properties",
     "primaryKey", "titleProperty"}
)

_NOT_IMPORTED = ("queryTypes", "sharedPropertyTypes", "valueTypes")


def convert_name(api_name: str) -> str:
    """``"NursingHome"`` -> ``"nursing_home"``. The result may still be illegal.

    Insert ``_`` before an upper-case letter that follows a lower-case letter or digit,
    and before the last capital of an acronym run followed by a lower-case letter.
    Lower-case. Replace each run outside ``[a-z0-9]`` with one ``_``. Strip ``_`` from
    both ends. The caller checks the result against :data:`NAME_RE`.
    """
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", api_name)
    text = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", text)
    text = re.sub(r"[^a-z0-9]+", "_", text.lower())
    return text.strip("_")


@dataclass(frozen=True)
class FoundryItem:
    """One Foundry type and what became of it.

    ``outcome`` is ``would_write`` or ``held`` on a dry run, and ``written``,
    ``refused`` or ``held`` on a real one. ``reason`` is the hold reason, or the
    ``import_types`` refusal reason. ``warnings`` are the returned entry's, on a real
    run. ``detail`` is per kind: ``predicates`` for an entity, ``inverse_label`` and
    ``sides`` for an edge, ``effects`` for an action, and ``standing`` (does the store
    already hold this name, so importing it replaces that row) for every kind.
    """

    kind: str
    api_name: str
    name: str
    outcome: str
    reason: str | None = None
    warnings: tuple[str, ...] = ()
    detail: dict = field(default_factory=dict)
    carried_properties: int = 0


@dataclass(frozen=True)
class LookAlike:
    """``resolve_type``'s answer for one planned name, when it names a different word.

    Unmodified: this row adds no scoring of its own (``FOUNDRY-PARITY.md`` §3.1)."""

    kind: str
    name: str
    matched: str
    score: float | None


@dataclass(frozen=True)
class FoundryImportReport:
    """What ``Registry.import_foundry`` planned, and on a real run what it wrote.

    **What a dry run cannot say** (``8A-RUN.md`` §0.5 item 5). It reports the planner's
    holds and ``resolve_type``'s look-alikes. It does **not** predict a guard refusal
    inside ``import_types`` (``name_previously_retired``, ``live_consumers``,
    ``alias_collision``, a family declaration refusal), because evaluating those means
    running the write path. A row listed ``would_write`` can still come back
    ``refused`` from the real run.
    """

    dry_run: bool
    namespace: str
    ontology: dict
    items: tuple[FoundryItem, ...]
    looks_like: tuple[LookAlike, ...] = ()
    not_imported: dict = field(default_factory=dict)
    #: ``import_types``' own return value, in call order. Empty on a dry run.
    entries: tuple = ()

    def count(self, **match: Any) -> int:
        """``report.count(outcome="held", kind="edge")``."""
        return sum(
            1
            for item in self.items
            if all(getattr(item, key) == value for key, value in match.items())
        )


@dataclass
class _Planned:
    """A planned item and, unless it is held, the ``import_types`` row it becomes."""

    kind: str
    api_name: str
    key: str
    name: str
    row: dict
    detail: dict
    carried: int = 0
    reason: str | None = None


def _named(key: str, names: dict[str, str]) -> str:
    mapped = names.get(key)
    return mapped if mapped is not None else convert_name(key.rsplit(".", 1)[-1])


def _definition(source: Any, key: str, definitions: dict[str, str]) -> str | None:
    supplied = definitions.get(key)
    if isinstance(supplied, str) and supplied.strip():
        return supplied
    if isinstance(source, str) and source.strip():
        return source
    return None


def _effects(action_api_name: str, doc: dict) -> list[dict]:
    """The ``Effect.op`` each rule WOULD map to. ``fullLogicRules`` wins when present."""
    full = (doc.get("actionTypesFullMetadata") or {}).get(action_api_name) or {}
    rules = full.get("fullLogicRules")
    source = "fullLogicRules"
    if not rules:
        rules = (doc.get("actionTypes") or {}).get(action_api_name, {}).get("operations") or []
        source = "operations"
    out = []
    for rule in rules:
        rule_type = rule.get("type")
        link = rule.get("linkTypeApiName") or rule.get("linkTypeApiNameAtoB")
        if rule_type in LINK_ADD_RULES:
            out.append({"op": "add_edge", "rule": rule_type, "link": link, "source": source})
        elif rule_type in LINK_REMOVE_RULES:
            out.append({"op": "retract_edge", "rule": rule_type, "link": link, "source": source})
        else:
            out.append(
                {
                    "op": "host_state",
                    "rule": rule_type,
                    "source": source,
                    "why": (
                        f"Foundry {rule_type!r} rule: it changes state the registry does "
                        "not hold, so it can only be the host's (brief question 4)"
                    ),
                }
            )
    return out


def _links(doc: dict, entity_names: dict[str, str]) -> list[dict]:
    """Pair link sides into families by ``linkTypeRid``.

    Forward side: the one carrying ``foreignKeyPropertyApiName``, else the first by
    ``(objectType apiName, side apiName)``. A side whose RID nothing else carries is a
    family with no inverse.
    """
    by_rid: dict[str, list[tuple[str, dict]]] = {}
    for ot_api, full in sorted((doc.get("objectTypes") or {}).items()):
        for side in full.get("linkTypes") or ():
            by_rid.setdefault(side.get("linkTypeRid") or f"{ot_api}.{side['apiName']}", []).append(
                (ot_api, side)
            )
    families = []
    for rid, sides in by_rid.items():
        sides = sorted(sides, key=lambda pair: (pair[0], pair[1]["apiName"]))
        keyed = [pair for pair in sides if pair[1].get("foreignKeyPropertyApiName")]
        forward = keyed[0] if keyed else sides[0]
        others = [pair for pair in sides if pair is not forward]
        inverse = others[0] if others else None
        families.append(
            {
                "rid": rid,
                "forward": forward,
                "inverse": inverse,
                "src": entity_names.get(forward[0], convert_name(forward[0])),
                "dst": entity_names.get(
                    forward[1].get("objectTypeApiName", ""),
                    convert_name(forward[1].get("objectTypeApiName", "")),
                ),
                "extra_sides": others[1:],
            }
        )
    return families


def plan(
    doc: dict,
    *,
    names: dict[str, str] | None = None,
    definitions: dict[str, str] | None = None,
) -> tuple[list[_Planned], dict]:
    """Every Foundry type in ``doc`` as a planned item, holds applied, in KIND_ORDER.

    Returns ``(planned, not_imported)``. A held item carries ``reason`` and no row is
    sent for it.
    """
    names = dict(names or {})
    definitions = dict(definitions or {})
    planned: list[_Planned] = []

    for api, iface in sorted((doc.get("interfaceTypes") or {}).items()):
        carried = {k: v for k, v in iface.items() if k not in ("apiName", "rid", "description")}
        planned.append(
            _Planned(
                kind="predicate", api_name=api, key=api, name=_named(api, names),
                row={
                    "definition": _definition(iface.get("description"), api, definitions),
                    "apiName": api,
                    **({"rid": iface["rid"]} if "rid" in iface else {}),
                    "attributes": {"foundry_interface": carried},
                },
                detail={},
            )
        )

    iface_names = {p.api_name: p.name for p in planned}
    entity_names: dict[str, str] = {}
    for api, full in sorted((doc.get("objectTypes") or {}).items()):
        ot = full.get("objectType") or {}
        name = _named(api, names)
        entity_names[api] = name
        predicates = [
            iface_names.get(i, _named(i, names)) for i in full.get("implementsInterfaces") or ()
        ]
        properties = ot.get("properties") or {}
        attributes = {
            "foundry_properties": {
                "validated": False,
                "primaryKey": ot.get("primaryKey"),
                "titleProperty": ot.get("titleProperty"),
                "properties": properties,
            },
            "foundry_object_type": {
                k: v for k, v in ot.items() if k not in _OBJECT_TYPE_MAPPED
            },
        }
        if "visibility" in ot:
            attributes["visibility"] = ot["visibility"]
        planned.append(
            _Planned(
                kind="entity", api_name=api, key=api, name=name,
                row={
                    "definition": _definition(ot.get("description"), api, definitions),
                    "status": ot.get("status"),
                    "predicates": predicates,
                    "apiName": api,
                    **({"rid": ot["rid"]} if "rid" in ot else {}),
                    "attributes": attributes,
                },
                detail={"predicates": predicates},
                carried=len(properties),
            )
        )

    for family in _links(doc, entity_names):
        ot_api, side = family["forward"]
        key = f"{ot_api}.{side['apiName']}"
        inverse = family["inverse"]
        inverse_label = (
            _named(f"{inverse[0]}.{inverse[1]['apiName']}", names) if inverse else None
        )
        sides = [
            {"objectType": o, **s}
            for o, s in [family["forward"]] + ([inverse] if inverse else []) + family["extra_sides"]
        ]
        planned.append(
            _Planned(
                kind="edge", api_name=side["apiName"], key=key, name=_named(key, names),
                row={
                    "definition": _definition(None, key, definitions),
                    "status": side.get("status"),
                    "apiName": key,
                    "rid": family["rid"],
                    "attributes": {
                        "level": "instance",
                        "symmetric": False,
                        "inverse_label": inverse_label,
                        "endpoint_kinds": {"src": ["entity"], "dst": ["entity"]},
                        "payload_schema": None,
                        # Brief question 3: EDGES.md has no cardinality key, so it is
                        # carried per side and listed as a contortion.
                        "foundry_link": {
                            "src_type": family["src"],
                            "dst_type": family["dst"],
                            "sides": sides,
                        },
                    },
                },
                detail={"inverse_label": inverse_label, "sides": len(sides)},
            )
        )

    for api, action in sorted((doc.get("actionTypes") or {}).items()):
        carried = {k: v for k, v in action.items() if k not in ("rid", "description", "status")}
        effects = _effects(api, doc)
        planned.append(
            _Planned(
                kind="action", api_name=api, key=api, name=_named(api, names),
                row={
                    "definition": _definition(action.get("description"), api, definitions),
                    "status": action.get("status"),
                    "apiName": api,
                    **({"rid": action["rid"]} if "rid" in action else {}),
                    # ACTIONS.md rule 2.2-1: declaring none of the eight keys is legal,
                    # and Foundry gives no reversibility or approval mode to declare.
                    "attributes": {"foundry_action": carried},
                },
                detail={"effects": effects},
            )
        )

    _hold(planned)
    for p in planned:
        p.detail.setdefault("standing", False)
    planned.sort(key=lambda p: KIND_ORDER.index(p.kind))
    not_imported = {k: len(doc.get(k) or {}) for k in _NOT_IMPORTED}
    return planned, not_imported


def _hold(planned: list[_Planned]) -> None:
    """Apply the four holds. First reason wins, in the order a caller has to fix them."""
    for p in planned:
        if not NAME_RE.match(p.name):
            p.reason = "name_invalid"
    by_word: dict[tuple[str, str], list[_Planned]] = {}
    for p in planned:
        if p.reason is None:
            by_word.setdefault((p.kind, p.name), []).append(p)
    for members in by_word.values():
        if len(members) > 1:
            for p in members:
                p.reason = "name_collision_after_conversion"
                p.detail["colliding"] = sorted(m.api_name for m in members)
    for p in planned:
        status = p.row.get("status")
        if p.reason is None and status is not None and str(status).upper() not in KNOWN_STATUSES:
            p.reason = "status_not_imported"
            p.detail["foundry_status"] = status
    for p in planned:
        if p.reason is None and p.row.get("definition") is None:
            p.reason = "definition_missing"
            p.detail["definitions_key"] = p.key


def to_row(p: _Planned) -> dict:
    """The ``import_types`` row for a planned item that is not held."""
    row = {k: v for k, v in p.row.items() if v is not None}
    row["name"] = p.name
    row["kind"] = p.kind
    if "status" in row:
        row["status"] = str(row["status"]).lower()
    return row
