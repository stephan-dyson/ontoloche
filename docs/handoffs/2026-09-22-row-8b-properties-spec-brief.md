# Row 8b brief — the properties spec row

**Drafted 2026-09-22 under founder ruling [R108](../decisions/2026-09-22-founder-ruling-R108.md) (`adopt B`).** A SPEC row, and it ships no product code, the way row 7a did for `INGEST.md`. Evidence: [`findings/PROPERTIES-OPTIONS.md`](../findings/PROPERTIES-OPTIONS.md).

---

## 1. What the row delivers

1. **An `INTERFACE.md` amendment specifying entity properties under option B.**
   - **Local properties** are declared on the owning `kind="entity"` entry: name, base type, description (required, non-empty), required flag, optional `value_set` reference. The entry also names its **primary key** and **title property**.
   - **Shared properties** are `kind="property"` entries, and an entity declares which shared properties it uses.
   - **Values are never stored or checked.** R78 is unchanged.
2. **`INTERFACE.md` §0 amended first, as its own commit,** before any other section changes. The superseded sentence (*"It is not a schema store"*) is struck through and kept, not deleted, following the precedent of 5.3.2-3 under R99.
3. **Answers, in spec, to the four questions R108 left open:** how an approved entity is amended; base-type mapping; which guards the `kind="property"` door inherits; and whether retiring a shared property still in use is refused. Any of these that decides **what the registry refuses** goes to the founder as a question, not into the spec as a default. Q56, Q99 and Q101 are the precedent.
4. **Contortion 10 closed in spec.** `resolve_type("latitude", ...)` resolves to a property, and `not_a_type`'s closed reason set is not touched.
5. **Rules numbered and pinned for a later build row,** the way `INGEST.md` numbered `C20-01`…`C20-90`.

## 2. Out of scope

- Any code. The build is a later row.
- The Foundry importer's property mapping. Row 8a carries properties until this spec lands.
- Validating data against declarations. That would be option C, which was rejected.

## 3. Design tests (standing constraint 7), expected outcomes committed in §0 before any run

- **UC2 CMS:** the file's 23 columns classified as local property, shared property, `value_set` or `not_a_type`. The known traps must stay caught: the severity scale keeps its external evidence, and `Location` stays `redundant_projection`.
- **UC3 NYC:** `status` stays three separate things across three agencies, `latitude` and `longitude` resolve as properties, and no cross-namespace merge succeeds.
- **UC1 Tenshen:** whether option B costs Tenshen anything. The **[Assumed]** answer is no, because its entities live in its own code, and the row confirms or refutes that.
- **Foundry:** every property and shared property type in the fixture from R106's routes (Palantir's `@osdk/faux` test ontologies, shape-checked by `foundry-platform-sdk`) has a home under the amended spec, or is named as a recorded contortion.

## 4. How the row runs

- **§0 is pre-registered and is the first commit touching the record.** It holds the predicted outcome for every design test and a falsifier for the amendment-mechanism choice.
- **Every contortion is recorded, and none is designed away.**
- **The adversarial loop runs to row 6j's stopping rule** (its `Q5`, `6J-RUN.md` §5 item 10). The reviewer brief names the three use cases and the Foundry fixture.
- **`check_links` and `check_spec_drift` exit 0.** The drift checker has to learn any new printed shape the amendment adds.
- **The row pre-registers which kill-row doors `kind="property"` opens.** It opens a new `kind`, and new doors are where rows 6b and 6d produced trips.
