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
#: ``createInterfaceLink`` / ``deleteInterfaceLink`` are published by the SDK as
#: ``CreateInterfaceLinkLogicRule`` / ``DeleteInterfaceLinkLogicRule`` (round 1).
# The link rule types `foundry_sdk.v2.ontologies.models` defines, in both `operations`
# (`CreateLinkRule`, `DeleteLinkRule`) and `fullLogicRules` (`*LinkLogicRule`). The
# pre-registration also named `addLink` / `removeLink`, which the SDK does not define
# (round 4, checked), so a rule of that type is `host_state` like any unknown rule.
LINK_ADD_RULES = frozenset({"createLink", "createInterfaceLink"})
LINK_REMOVE_RULES = frozenset({"deleteLink", "deleteInterfaceLink"})

#: Object type keys mapped to a field of their own. Every other key is carried in
#: ``attributes["foundry_object_type"]``, so nothing Foundry said is dropped.
_OBJECT_TYPE_MAPPED = frozenset(
    {"apiName", "rid", "description", "status", "visibility", "properties",
     "primaryKey", "titleProperty"}
)

_NOT_IMPORTED = ("queryTypes", "sharedPropertyTypes", "valueTypes")
_TYPE_MAPS = ("objectTypes", "interfaceTypes", "actionTypes", "actionTypesFullMetadata")


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

    No scoring of its own (``FOUNDRY-PARITY.md`` §3.1): ``resolve_type``'s match, or an
    alternative at or above the namespace's ``near_duplicate_threshold``."""

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
    #: ``names=`` and ``definitions=`` keys that matched no item (round 1). A key that
    #: matches nothing lifts nothing, and used to say nothing.
    unmatched: dict = field(default_factory=lambda: {"names": [], "definitions": []})

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
    #: ``(label, kind, apiName, name)`` of each row this one points at (round 1).
    refs: list = field(default_factory=list)


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


def _effects(action_api_name: str, doc: dict, action: dict) -> list[dict]:
    """The ``Effect.op`` each rule WOULD map to. ``fullLogicRules`` wins when present.

    ``action`` is the merged ``ActionTypeV2`` (round 4): an action found only in
    ``actionTypesFullMetadata`` has its ``operations`` in that map's ``actionType``,
    and reading ``actionTypes`` alone reported ``effects: []`` for it."""
    full = (doc.get("actionTypesFullMetadata") or {}).get(action_api_name) or {}
    rules = full.get("fullLogicRules")
    source = "fullLogicRules"
    if not rules:
        rules = action.get("operations") or []
        source = "operations"
    out = []
    for rule in rules:
        rule_type = rule.get("type")
        link = rule.get("linkTypeApiName") or rule.get("linkTypeApiNameAtoB")
        if link is None and rule.get("interfaceLinkTypeApiName"):
            link = f"{rule.get('interfaceTypeApiName')}.{rule['interfaceLinkTypeApiName']}"
        # `CreateLinkRule` / `DeleteLinkRule` name both directions; the family's
        # forward side may be either (round 3).
        inverse = {"inverse_link": rule["linkTypeApiNameBtoA"]} if rule.get("linkTypeApiNameBtoA") else {}
        if rule_type in LINK_ADD_RULES:
            out.append({"op": "add_edge", "rule": rule_type, "link": link, "source": source, **inverse})
        elif rule_type in LINK_REMOVE_RULES:
            out.append({"op": "retract_edge", "rule": rule_type, "link": link, "source": source, **inverse})
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

    Returns ``(planned, not_imported, unmatched)``. A held item carries ``reason`` and no row is
    sent for it.
    """
    # **Not a full-metadata document** (round 3). A dict with none of the type maps
    # (a pydantic `model_dump()` without `by_alias=True` gives `object_types`) read as
    # an empty ontology: a clean dry run, and a real run that wrote nothing.
    if not isinstance(doc, dict):
        raise TypeError(
            f"import_foundry takes an OntologyFullMetadata dict, got {type(doc).__name__}"
        )
    if not any(k in doc for k in _TYPE_MAPS):
        raise ValueError(
            "not an OntologyFullMetadata document: none of "
            f"{', '.join(_TYPE_MAPS)} is present (an SDK model needs "
            "model_dump(by_alias=True))"
        )
    names = dict(names or {})
    definitions = dict(definitions or {})
    # A caller's type error, not a hold: ``names={"Foo": 5}`` raised a bare
    # ``TypeError`` from inside the regex (round 1). Said here, naming the key.
    for label, mapping in (("names", names), ("definitions", definitions)):
        for key, value in mapping.items():
            if not isinstance(value, str):
                raise TypeError(f"{label}[{key!r}] must be a str, got {type(value).__name__}")
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
        # The published `ObjectTypeFullMetadata` carries both the list and the map
        # (`implementsInterfaces2`, "implements and how"), and only the list was read
        # (round 1). The union, in the list's order first.
        # A repeated list entry was written twice into `predicates` (round 4).
        declared = list(dict.fromkeys(full.get("implementsInterfaces") or ()))
        declared += [i for i in (full.get("implementsInterfaces2") or {}) if i not in declared]
        predicates = [iface_names.get(i, _named(i, names)) for i in declared]
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
            # **How this object type implements its interfaces** (round 2). The values
            # of `implementsInterfaces2` (which local property or link implements which
            # interface property or link) and `sharedPropertyTypeMapping` sit BESIDE
            # `objectType`, not inside it, so the carry above never reached them and
            # the only record of that mapping was dropped. Every sibling except
            # `objectType` itself and `linkTypes` (carried on the edge families),
            # verbatim and not validated, as R105's `carry`.
            "foundry_object_type_metadata": {
                "validated": False,
                **{k: v for k, v in full.items() if k not in ("objectType", "linkTypes")},
            },
        }
        # `model_dump(by_alias=True)` emits an unset field as None (round 4).
        if ot.get("visibility") is not None:
            attributes["visibility"] = ot["visibility"]
        planned.append(
            _Planned(
                kind="entity", api_name=api, key=api, name=name,
                row={
                    "definition": _definition(ot.get("description"), api, definitions),
                    "status": ot.get("status"),
                    # A predicate word that is not a legal name has no row and never
                    # will under that word, so it is not written into the entity: it
                    # stays in `detail` and is reported `unresolved` (round 2).
                    "predicates": [w for w in predicates if NAME_RE.fullmatch(w)],
                    "apiName": api,
                    **({"rid": ot["rid"]} if "rid" in ot else {}),
                    "attributes": attributes,
                },
                detail={"predicates": predicates},
                refs=[("predicate", "interface", i, n) for i, n in zip(declared, predicates)],
                carried=len(properties),
            )
        )

    for family in _links(doc, entity_names):
        ot_api, side = family["forward"]
        key = f"{ot_api}.{side['apiName']}"
        inverse = family["inverse"]
        inverse_key = f"{inverse[0]}.{inverse[1]['apiName']}" if inverse else None
        inverse_label = _named(inverse_key, names) if inverse else None
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
                detail={
                    "inverse_label": inverse_label,
                    # The `names=` key for the inverse label (round 2): it is not an
                    # item's key, and `unmatched` reported it as matching nothing.
                    "inverse_key": inverse_key,
                    "sides": len(sides),
                },
                refs=[
                    ("src", "entity", ot_api, family["src"]),
                    ("dst", "entity", side.get("objectTypeApiName", ""), family["dst"]),
                ],
            )
        )

    # **Both action maps** (round 3). `actionTypesFullMetadata[x].actionType` is a
    # whole `ActionTypeV2`, so an action in that map alone is an action; it was
    # dropped with no count. And its `fullLogicRules` hold the rule variants
    # `operations` cannot (`function`, interface rules), so they are carried.
    full_actions = doc.get("actionTypesFullMetadata") or {}
    actions = {
        api: (entry.get("actionType") or {"apiName": api})
        for api, entry in full_actions.items()
    }
    actions.update(doc.get("actionTypes") or {})
    for api, action in sorted(actions.items()):
        carried = {k: v for k, v in action.items() if k not in ("rid", "description", "status")}
        logic = (full_actions.get(api) or {}).get("fullLogicRules")
        if logic:
            carried["fullLogicRules"] = logic
        effects = _effects(api, doc, action)
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
        # The exact key `names=` and `definitions=` take for this item. For a link it
        # is `"<objectType>.<side>"`, which no other field carried (round 1).
        p.detail["key"] = p.key
    # `refs` are resolved by `Registry.import_foundry`, against the store and, on a
    # real run, against what was actually written (round 2).
    planned.sort(key=lambda p: KIND_ORDER.index(p.kind))
    not_imported = {k: len(doc.get(k) or {}) for k in _NOT_IMPORTED}
    keys = {p.key for p in planned}
    # An inverse key takes a name (the label), never a definition (round 3).
    name_keys = keys | {
        p.detail["inverse_key"] for p in planned if p.detail.get("inverse_key")
    }
    unmatched = {
        "names": sorted(k for k in names if k not in name_keys),
        "definitions": sorted(k for k in definitions if k not in keys),
    }
    return planned, not_imported, unmatched


def _hold(planned: list[_Planned]) -> None:
    """Apply the four holds. First reason wins, in the order a caller has to fix them."""
    for p in planned:
        # `fullmatch`: `$` matches before a final newline, so `.match` let
        # `"person\n"` through (round 1).
        if not NAME_RE.fullmatch(p.name):
            p.reason = "name_invalid"
        # An inverse label is a word too, from the conversion or from `names=`, and it
        # was written unchecked (round 2).
        label = p.detail.get("inverse_label")
        if p.reason is None and label is not None and not NAME_RE.fullmatch(label):
            p.reason = "name_invalid"
            p.detail["invalid"] = "inverse_label"
    by_word: dict[tuple[str, str], list[_Planned]] = {}
    for p in planned:
        if p.reason is None:
            by_word.setdefault((p.kind, p.name), []).append(p)
    for members in by_word.values():
        if len(members) > 1:
            for p in members:
                p.reason = "name_collision_after_conversion"
                # Keys, not apiNames: two link sides named `owner` on two object
                # types gave `["owner", "owner"]`, which no map can address (round 1).
                p.detail["colliding"] = sorted(m.key for m in members)
    for p in planned:
        status = p.row.get("status")
        if p.reason is None and status is not None and str(status).upper() not in KNOWN_STATUSES:
            p.reason = "status_not_imported"
            p.detail["foundry_status"] = status
    for p in planned:
        if p.reason is None and p.row.get("definition") is None:
            p.reason = "definition_missing"
            p.detail["definitions_key"] = p.key


#: The approver ``import_types`` writes on every imported row (``INTERFACE.md`` 2.5).
IMPORTED_APPROVER = "unknown:imported"


def replaces(stored: Any, row: dict) -> dict | None:
    """What writing ``row`` over the live ``stored`` row would lose (round 4).

    ``import_types`` replaces a standing row's predicates, aliases and attributes, and
    its definition when one is supplied (``INTERFACE.md`` 2.5). Row 8a makes that door
    routine, and a dry run said only ``standing: True``. Reported, never held: whether
    to refuse overwriting a row this system did not import is the founder's
    (``DECISIONS-OPEN.md``). ``None`` when nothing would be lost, so an idempotent
    re-run reports nothing.

    **The row is compared with what ``import_types`` will WRITE, not with what it is
    handed** (round 6). ``import_types`` appends ``experimental`` or ``endorsed`` to the
    predicates for those statuses, so reading the row alone reported the stored marker
    as dropped on every idempotent re-run. ``retires`` is a live row a ``DEPRECATED``
    import would retire, and ``approved_by_replaced`` is a human approver the import's
    ``unknown:imported`` would overwrite: the two largest losses, and round 5 found
    neither was said."""
    status = str(row.get("status") or "active").lower()
    incoming_predicates = set(row.get("predicates") or ())
    if status in ("experimental", "endorsed"):
        incoming_predicates.add(status)
    incoming_attributes = set(row.get("attributes") or {})
    definition = row.get("definition")
    lost = {
        "predicates_dropped": sorted(set(stored.predicates or ()) - incoming_predicates),
        "aliases_dropped": sorted(set(stored.aliases or ()) - set(row.get("aliases") or ())),
        "attributes_dropped": sorted(set(stored.attributes or {}) - incoming_attributes),
        "definition_replaced": bool(
            isinstance(definition, str) and definition.strip()
            and definition != stored.definition
        ),
        "retires": status == "deprecated" and stored.status != "retired",
    }
    approved_by = (stored.provenance or {}).get("approved_by")
    if approved_by and approved_by != IMPORTED_APPROVER:
        lost["approved_by_replaced"] = approved_by
    lost = {k: v for k, v in lost.items() if v}
    if not lost:
        return None
    source = ((stored.provenance or {}).get("imported_from") or {}).get("system")
    return {"imported_from": source, **lost}


def to_row(p: _Planned) -> dict:
    """The ``import_types`` row for a planned item that is not held."""
    row = {k: v for k, v in p.row.items() if v is not None}
    row["name"] = p.name
    row["kind"] = p.kind
    if "status" in row:
        row["status"] = str(row["status"]).lower()
    return row
