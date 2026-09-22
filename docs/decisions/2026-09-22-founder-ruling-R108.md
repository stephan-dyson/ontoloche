# R108 — `Q102` ruled `adopt B`: entity properties are governed as vocabulary

**Founder ruling, 2026-09-22. His word: `adopt B`.**

The item, as it stood on the decision page (item 18):

> Declare local properties on the entity that owns them, make shared properties a new `kind="property"`, and never store or check property values. [...] **Ask: `adopt B`, `adopt A`, or `discuss`.** Default in force: `carry` (R105's interim).

Full option analysis: [`findings/PROPERTIES-OPTIONS.md`](../findings/PROPERTIES-OPTIONS.md).

---

## 1. What is ruled

1. **Entity properties come into scope as definitions, never as values.** The registry governs what a property *is* (name, base type, description, required flag, optional `value_set` reference) and which property is an entity's primary key and title. It never stores a property value and never checks a row against a declaration. **R78 is unchanged:** the host holds the instances.
2. **Two tiers, mirroring Foundry.** Local properties are declared on the entity that owns them and governed through that entity. Shared properties are registry entries of a new `kind="property"`, governed one by one.
3. **`INTERFACE.md` §0 will change.** *"It is not a schema store"* becomes a statement that the registry holds no *values*. **The amendment is made by the spec row, before any code, and is not made by this record.** That is the same order row 6f used for R99.

## 2. What is NOT ruled, and the spec row must raise

These are `PROPERTIES-OPTIONS.md` §3's open design questions. None of them is decided by this ruling.

1. **How an approved entity is amended.** No call does this today; `amend_edge` is the only amend call (`ontoloche/registry.py:7036`). The options are a new governed amendment call or supersede-and-retire. This is the largest question, and it probably needs the founder, because it decides what the registry lets change after approval.
2. Which Foundry base types map to `FieldSpec` types, and which are carried opaque.
3. Which guards the `kind="property"` door inherits, pre-registered before code.
4. Whether retiring a shared property that an active entity still declares is refused, by analogy with `retire`'s `live_consumers`.

## 3. What changes now

- **Row 8b opens as a SPEC row**, the way row 7a did for INGEST: an amendment to `INTERFACE.md` with design tests on the three use cases plus the Foundry fixture, and the adversarial loop, with no product code. Brief: [`handoffs/2026-09-22-row-8b-properties-spec-brief.md`](../handoffs/2026-09-22-row-8b-properties-spec-brief.md).
- **Row 8a (the importer) keeps R105's `carry` for properties** until row 8b's spec lands. Carrying is lossless, and 8a's dry run reports every carried property, so nothing imported under `carry` is lost when 8b's shape arrives. Once 8b lands, 8a or a follow-on maps properties into the governed shape.
- **R105's interim `carry` stays in force only until row 8b's spec lands.** It is no longer the default for the long run.

**Kill row and governance register:** unchanged. A ruling is not a trip.
