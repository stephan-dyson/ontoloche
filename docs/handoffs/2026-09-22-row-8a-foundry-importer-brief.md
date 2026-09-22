# Row 8a brief — the Foundry metadata importer

**Drafted 2026-09-22 for the founder to open.** The row is not open. Evidence: [`findings/FOUNDRY-PARITY.md`](../findings/FOUNDRY-PARITY.md). Rulings in force: [R105–R107](../decisions/2026-09-22-founder-rulings-R105-R107.md).

---

## 1. What the row delivers

A way for a Foundry customer to bring their ontology definitions into ontoloche in one step, **dry run first**. This serves the founder's goal 1 directly, and under R107 it is the front door of a full replacement.

1. **`import_foundry(full_metadata, *, namespace, dry_run=True)`.** It reads one `OntologyFullMetadata` document, the response shape of `GET /api/v2/ontologies/{ontology}/fullMetadata` (https://github.com/palantir/foundry-platform-python/blob/develop/docs/v2/Ontologies/models/OntologyFullMetadata.md).
2. **A dry-run report that writes nothing.** It lists what maps cleanly, what is carried but not modelled, what is refused and why, and, through `resolve_type`, which incoming names look like words the vocabulary already has.
3. **The four `import_types` defects fixed**, because they sit on the same door (`FOUNDRY-PARITY.md` §2):
   1. `ENDORSED` becomes `active` plus an `endorsed` predicate, following the `experimental` precedent.
   2. Foundry's Example status is skipped by default and reported.
   3. A name that does not fit `^[a-z][a-z0-9_]{0,63}$` is converted, or refused with an `import_refused` reason. It never raises a backend exception.
   4. An empty description imports as `proposed` with a warning, never as `active` with a placeholder definition.

Field mapping: `FOUNDRY-PARITY.md` §3.1. Properties follow **R105's interim `carry`**: verbatim in `attributes`, marked not validated, until `Q102` is ruled.

## 2. Out of scope

- A round trip back into Foundry (R107: one-way).
- Instance data, action execution, Functions and apps. R107 records these as gaps for later rows.
- Governed properties. That waits on `Q102`.
- The Ontology Manager JSON export. Palantir: *"You should not depend on the exported JSON schema as it may change over time."* (https://www.palantir.com/docs/foundry/ontology-manager/export-import/)

## 3. Fixtures (R106: no customer export)

1. **Generate** `fullMetadata` documents from Palantir's `@osdk/faux` `FauxOntology` with Palantir's own test ontologies, both under Apache 2.0 in https://github.com/palantir/osdk-ts. Commit the generated JSON with the commit and command that produced it.
2. **Shape-check** every fixture by parsing it with `foundry-platform-sdk`'s `OntologyFullMetadata` model. Use it as a test-only dependency, never a runtime one.
3. **Hand-built edge cases** the test ontologies may lack: `ENDORSED`, Example, an empty description, a colliding name, a many-to-many link, a function-backed action. Each is shape-checked the same way.
4. **Optional, and the founder's call:** a real `fullMetadata` from a free AIP Developer Tier account. Whether that tier exposes the endpoint and allows the use is unverified.

State fixture fidelity honestly in the run record. Routes 1 to 3 prove the shape. They do not prove that a real customer ontology looks like Palantir's test ontologies.

## 4. How the row runs (the project's standing process)

- **§0 is pre-registered and committed first,** before any code. It holds the predicted dry-run counts for each fixture and the falsifier for each of the four defect fixes.
- **Design tests on all three use cases** (standing constraint 7). For UC2 and UC3, a fixture that re-expresses the CMS and NYC types as Foundry object types must import to the same vocabulary those design tests already reproduce. For UC1, the row records whether Tenshen has any Foundry-shaped input at all.
- **Tests are written red first** and added to the contract suite, so every backend is held to the importer, not just SQLite.
- **All five gates exit 0** (`check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, `check_skip_census`).
- **The async mirror is regenerated,** not hand-written.
- **The adversarial loop runs to the stopping rule ruled in row 6j (its `Q5`, `6J-RUN.md` §5 item 10):** it ends when a full round finds no in-scope MAJOR reachable by a shape a contributor would plausibly write.
- **The import door is a known kill-row door** (group `C12`, the "fourth door"). The row pre-registers which guards the new entry point inherits, and checks that `import_foundry` cannot reach a merge, retire or collapse that `import_types` refuses.

## 5. Questions the row must raise rather than assume

1. How a Foundry `apiName` converts to an ontoloche name when two convert to the same string.
2. Whether one Foundry ontology maps to one ontoloche namespace, or whether object type groups or projects should split it.
3. How Foundry link cardinality is carried until `EDGES.md` has a key for it.
4. Which Foundry action logic rules map to `Effect.op`, and which fall to `host_state` with a `why`.
