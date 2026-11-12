"""Write row 8a's hand-built Foundry fixtures (R106 route 3) and the two use-case fixtures.

The generated fixtures (`foundry_faux_employee.json`, `foundry_faux_legacy.json`) come
from Palantir's own fake Foundry and prove the published shape. They do not contain the
cases the importer has to get right, so this script writes three more documents in the
same `OntologyFullMetadata` shape:

* ``foundry_edge_cases.json`` -- ENDORSED, EXAMPLE, DEPRECATED, a missing description, two
  apiNames that convert to one name, an apiName that converts to nothing legal, a
  many-to-many link, and an action whose full logic rules include a link rule and a
  function rule.
* ``foundry_uc2_cms.json`` -- the CMS vocabulary of `cms_vocabulary()` and `C18`,
  re-expressed as Foundry object types and link types (design test UC2).
* ``foundry_uc3_nyc.json`` -- UC3's `street_tree` / `service_request` / `same_tax_lot`
  as ONE Foundry ontology, which is the only way Foundry can hold a link between them
  (design test UC3).

Every RID here conforms to the SDK's RID pattern, so the shape check holds these to a
stricter standard than Palantir's own fixtures meet (`8A-RUN.md` §0.1 item 2). The one
deliberate violation is EXAMPLE, which the published `ReleaseStatus` enum does not have.

Run: ``python docs/tools/foundry_faux/build_hand_fixtures.py`` -- rewrites the three
files under ``ontoloche/contract/fixtures/``. Deterministic: no clock, no randomness.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "ontoloche" / "contract" / "fixtures"


def _rid(kind: str, n: int) -> str:
    return f"ri.ontology.main.{kind}.{n:08d}-0000-4000-8000-000000000000"


def _prop(data_type: str, n: int, description: str | None = None) -> dict:
    out = {"dataType": {"type": data_type}, "rid": _rid("property", n), "typeClasses": []}
    if description is not None:
        out["description"] = description
    return out


def object_type(
    api_name: str,
    n: int,
    *,
    status: str = "ACTIVE",
    description: str | None,
    primary_key: str = "id",
    links: list[dict] | None = None,
    implements: list[str] | None = None,
    extra_properties: dict | None = None,
) -> dict:
    properties = {primary_key: _prop("string", n * 100)}
    properties.update(extra_properties or {})
    ot = {
        "apiName": api_name,
        "displayName": api_name,
        "pluralDisplayName": api_name + "s",
        "status": status,
        "primaryKey": primary_key,
        "titleProperty": primary_key,
        "properties": properties,
        "rid": _rid("object-type", n),
        "visibility": "NORMAL",
        "icon": {"type": "blueprint", "name": "cube", "color": "blue"},
        "aliases": [],
        "datasources": [],
    }
    if description is not None:
        ot["description"] = description
    return {
        "objectType": ot,
        "linkTypes": links or [],
        "implementsInterfaces": implements or [],
        "implementsInterfaces2": {},
        "sharedPropertyTypeMapping": {},
    }


def side(
    api_name: str, to: str, cardinality: str, rid_n: int, *, fk: str | None = None
) -> dict:
    out = {
        "apiName": api_name,
        "displayName": api_name,
        "status": "ACTIVE",
        "objectTypeApiName": to,
        "cardinality": cardinality,
        "linkTypeRid": _rid("link-type", rid_n),
    }
    if fk is not None:
        out["foreignKeyPropertyApiName"] = fk
    return out


def ontology(api_name: str, n: int, description: str) -> dict:
    return {
        "apiName": api_name,
        "displayName": api_name,
        "description": description,
        "rid": _rid("ontology", n),
    }


def document(onto: dict, object_types: dict, **rest) -> dict:
    return {
        "ontology": onto,
        "objectTypes": object_types,
        "actionTypes": rest.get("actionTypes", {}),
        "actionTypesFullMetadata": rest.get("actionTypesFullMetadata", {}),
        "queryTypes": {},
        "interfaceTypes": rest.get("interfaceTypes", {}),
        "sharedPropertyTypes": {},
        "valueTypes": {},
    }


def edge_cases() -> dict:
    assign = {
        "apiName": "assignDoctor",
        "description": "Assign a doctor to a patient and notify the ward.",
        "parameters": {
            "doctor": {
                "displayName": "Doctor",
                "dataType": {"type": "object", "objectApiName": "Doctor",
                             "objectTypeApiName": "Doctor"},
                "required": True,
                "typeClasses": [],
            },
            "patient": {
                "displayName": "Patient",
                "dataType": {"type": "object", "objectApiName": "Patient",
                             "objectTypeApiName": "Patient"},
                "required": True,
                "typeClasses": [],
            },
        },
        "rid": _rid("action-type", 1),
        "operations": [
            {"type": "createLink", "aSideObjectTypeApiName": "Doctor",
             "bSideObjectTypeApiName": "Patient", "linkTypeApiNameAtoB": "treats",
             "linkTypeApiNameBtoA": "treatedBy"},
        ],
        "status": "ACTIVE",
    }
    return document(
        ontology("edge-cases", 1, "Hand-built cases the generated fixtures do not carry"),
        {
            "EndorsedThing": object_type(
                "EndorsedThing", 1, status="ENDORSED",
                description="A type an ontology owner has vetted and promoted.",
            ),
            "ExampleThing": object_type(
                "ExampleThing", 2, status="EXAMPLE",
                description="A demo type that ships with a template.",
            ),
            "NoDescription": object_type("NoDescription", 3, description=None),
            "NursingHome": object_type(
                "NursingHome", 4, description="A licensed long-term care facility.",
            ),
            "Nursing_Home": object_type(
                "Nursing_Home", 5, description="A care home, from a second team.",
            ),
            "Ward3D": object_type(
                "Ward3D", 6, description="A hospital ward, named with a digit run.",
            ),
            "_9Lives": object_type(
                "_9Lives", 7, description="An apiName that converts to a leading digit.",
            ),
            "LegacyWard": object_type(
                "LegacyWard", 8, status="DEPRECATED",
                description="The pre-2025 ward model.",
            ),
            "Doctor": object_type(
                "Doctor", 9, description="A licensed physician.",
                links=[side("treats", "Patient", "MANY", 1)],
            ),
            "Patient": object_type(
                "Patient", 10, description="A person receiving care.",
                links=[side("treatedBy", "Doctor", "MANY", 1)],
            ),
        },
        actionTypes={"assignDoctor": assign},
        actionTypesFullMetadata={
            "assignDoctor": {
                "actionType": assign,
                "fullLogicRules": [
                    {"type": "createLink", "linkTypeApiName": "treats",
                     "sourceObject": "doctor", "targetObject": "patient"},
                    {"type": "function", "functionRid": _rid("function", 1),
                     "functionVersion": "1.0.0", "functionInputValues": {}},
                ],
            }
        },
    )


# UC2. Descriptions are `cms_vocabulary()`'s definitions verbatim, so a name match is a
# match on the vocabulary the CMS design test already reproduces, not on a paraphrase.
CMS_DEFINITIONS = {
    "Facility": (
        "A Medicare/Medicaid-certified nursing home, identified by its CMS "
        "Certification Number (CCN). Provider Name is a label, not an identifier: "
        "104 distinct names are shared by more than one CCN in the August 2026 file."
    ),
    "Survey": (
        "One inspection visit to a facility, keyed by (CCN, Survey Date, Survey "
        "Type). Several citations are issued during one survey."
    ),
    "Citation": (
        "One deficiency cited against a facility during a survey. The file's grain: "
        "one citation per row."
    ),
    "DeficiencyTag": (
        "A regulatory tag (an F-tag) a citation is written under. Deficiency "
        "Description is a lookup on the tag, not per-citation free text: no tag in "
        "the sample carries more than one description."
    ),
}


def uc2_cms() -> dict:
    return document(
        ontology("cms-health-citations", 2, "UC2 re-expressed as a Foundry ontology"),
        {
            "Facility": object_type(
                "Facility", 21, description=CMS_DEFINITIONS["Facility"],
                primary_key="ccn",
                links=[side("surveys", "Survey", "MANY", 22)],
            ),
            "Survey": object_type(
                "Survey", 22, description=CMS_DEFINITIONS["Survey"],
                primary_key="surveyKey",
                links=[
                    side("conductedAt", "Facility", "ONE", 22, fk="ccn"),
                    side("citations", "Citation", "MANY", 21),
                ],
            ),
            "Citation": object_type(
                "Citation", 23, description=CMS_DEFINITIONS["Citation"],
                primary_key="citationId",
                links=[
                    side("issuedDuring", "Survey", "ONE", 21, fk="surveyKey"),
                    side("cites", "DeficiencyTag", "ONE", 23, fk="tagNumber"),
                ],
            ),
            "DeficiencyTag": object_type(
                "DeficiencyTag", 24, description=CMS_DEFINITIONS["DeficiencyTag"],
                primary_key="tagNumber",
                links=[side("citedBy", "Citation", "MANY", 23)],
            ),
        },
    )


def uc3_nyc() -> dict:
    return document(
        ontology("nyc-open-data", 3, "UC3 re-expressed as ONE Foundry ontology"),
        {
            "StreetTree": object_type(
                "StreetTree", 31, description="a NYC census street tree",
                primary_key="treeId",
                links=[side("sharesTaxLotWith", "ServiceRequest", "MANY", 31)],
            ),
            "ServiceRequest": object_type(
                "ServiceRequest", 32, description="a 311 request",
                primary_key="uniqueKey",
                links=[side("sameTaxLot", "StreetTree", "MANY", 31)],
            ),
        },
    )


def main() -> None:
    for name, doc in (
        ("foundry_edge_cases.json", edge_cases()),
        ("foundry_uc2_cms.json", uc2_cms()),
        ("foundry_uc3_nyc.json", uc3_nyc()),
    ):
        (OUT / name).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
