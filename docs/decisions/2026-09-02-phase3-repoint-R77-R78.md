# The Phase 3 re-point — rulings R77 and R78, and the critical-path scope

**Date:** 2026-09-02. **Author:** the ontoloche program supervisor. **Occasion:** a founder
directive re-pointing this programme at the ingestion / mapping layer (Phase 3), because it is
simultaneously the venture wedge and the foundation the design partner's rebuild needs. The
factual half of that directive is already on `main` — [`ROADMAP.md`](../../ROADMAP.md) row 7's
cell was **false on this document set's own record** and was corrected at `7ee1eb5`.

Claims are tagged **[Observed] / [Inferred] / [Assumed]**. Numbering continues the register:
R1–R76 exist, next question is **Q79**.

---

## 1. The convergence claim, confirmed — against this repository, not against the argument that proposed it

**The claim:** *the design partner's missing middle — landing raw input into typed entities and
relationships with propose-approve at the point of ingest — **is** this project's Phase 3
ingestion wedge.*

**CONFIRMED. [Observed]**, on three citations that were all written before anyone proposed the
re-point:

1. [`VISION.md`](../../VISION.md) §4b: *"the product is neither ETL nor an ontology store. It is
   **the mapping layer between them**: landed rows to typed entities and relationships, with
   curation and provenance applied **at the point of ingest**."*
2. [`ROADMAP.md`](../../ROADMAP.md) Phase 3 already **homes instance resolution** — the
   walkthrough's *"I already know 38 of these"* — with the reason *"it is the mapping layer's
   problem (rows → entities), not the type registry's."* Filing captured work into the wrong
   existing container **is** instance resolution failing.
3. [`VISION.md`](../../VISION.md) §5: *"You cannot do automated ingestion into an ontology without
   answering 'what type is this, and does it already exist?' — which **is** the anti-rot
   problem."*

**And the sequencing objection has expired, which matters more than the directive.**
`ROADMAP.md` gave exactly one reason Phase 3 sat later: *ingestion without a curation engine builds
the pollution machine before the filter.* The filter is built — propose→approve with provenance,
`resolve_type` with `not_a_type`, `merge_types` behind the kill row's twelve trips, `consumers()`,
identity re-verified at the read (R54/R55), typed relationships, governed actions; **346 contract
ids on three reference backends, sync and async.** The re-point is that judgment's own precondition
being satisfied, not a reversal of it. **Had the curation engine not been built, this document
would be arguing against the re-point on the roadmap's own grounds.**

---

## 2. R77 — instance resolution is homed in Phase 3. **Ruled by the founder**, and it closes an item this interface has carried open since v0

[`INTERFACE.md`](../specs/INTERFACE.md) §11, "Also open", reads:

> **Instance resolution** (§10.3) has no home in any current deliverable. **[Inferred]** it
> belongs with Phase 3 ingestion, but nothing says so yet. **Founder ruling wanted.**

**The re-point answers it.** §1's non-goal (*"No instance resolution"*) and §10.3's resolution
(*"state it as a gap rather than stretch the call"*) both stand **for this interface** — nothing
here becomes a second thing. What changes is that the gap now has an owner and a phase.

**R77:** *instance resolution is Phase 3's; it is the mapping layer's problem and not the type
registry's; and `resolve_type` is never extended to cover it.* The reason §10.3 gave for refusing
the stretch is the reason it keeps being refused: *adding instance resolution to a type registry
would make `resolve_type` mean two different things — which is 0.1's Cause B, semantic collision,
committed by the spec itself.* §11's open item is closed by pointer; §1's non-goal gains the
pointer rather than being deleted.

---

## 3. The gap in one sentence, and it is the whole scope

**This project resolves WORDS. The design partner's capture produces INSTANCES.**

`resolve_type` resolves the word `project`; it does not resolve *"Q3 platform migration"* against
the forty projects that already exist — exactly as it does not resolve *"BURNS NURSING HOME, INC."*
against 14,627 CCNs (§10.3, **[Observed]**: 104 distinct provider names are shared by more than one
CCN, so resolving on name merges genuinely different facilities).

**Half of the seam already exists and it landed last week.** `InstanceRef` is a real shape, and
ruling **R72** (row 6c) published `parse_ref` as the inverse of `ref_key`, so
`"beacon:entity:project#p-8123"` round-trips. **This project can already NAME an instance and
carry it through the invocation ledger. It cannot RESOLVE one.** That is the seam Layer B is built
on, and it is narrower than *"build an instance store."*

---

## 4. R78 — the instance seam. **Supervisor ruling, and deliberately falsifiable**

**The question Layer B's spec must answer before anything else:** does this project become an
instance store, or does it define resolution *over instances the host already holds*?

**R78: the host holds the instances; this project defines the resolution protocol over them
through adapter primitives, and stores no instance rows of its own.** **[Assumed]**, with the
reasoning below, and **the Layer B spec's first design test may overturn it** — that is what a
default is for.

**Why.** This repository has established the same pattern three times and named it each time:
*a family is a row of the vocabulary and its instances live in a store beside the registry.* Edge
families are `kind="edge"` `TypeEntry` rows while edges live in the edge store; action families
are `kind="action"` rows while invocations live in the ledger. Entity instances are the third
instance of that pattern, not an exception to it. Applying it:

- the registry holds `kind="entity"` vocabulary rows (`task`, `project`, `person`) exactly as
  today, propose→approve and provenance unchanged;
- the host holds its own instance rows and stays their system of record;
- this project adds **adapter primitives** for candidate retrieval plus a **resolution call** with
  the four-outcome shape `resolve_type` already proved, and **curation and provenance at the point
  of ingest** — `VISION.md` §4b's sentence, implemented.

**Three consequences, and they are the reasons to prefer it:**

1. **Layer B adds primitives, not a copy of anybody's data.** A mapping layer that ingests its
   design partner's tables into its own store is a migration, not a product.
2. **It keeps the venture claim true rather than asserted.** The same primitives that resolve
   forty projects resolve 14,627 CCNs. A resolution protocol shaped around one partner's schema
   serves one partner.
3. **It inherits the guards instead of re-deriving them.** Twelve kill-row trips bought a
   discipline about identity; a separate instance store would restart that count at zero.

---

## 5. The critical path — what the design partner's rebuild needs from this project, in dependency order

**Correction first, because it changes what "next" means.** An earlier draft of this section
listed Phase 3's paging and tenancy decisions as *open* — reading `ROADMAP.md`'s Phase 3 prose,
which still says *"Two decisions this phase MUST take before its wedge is built (rulings R25 /
R13)."* **That prose is stale. [Observed]** All three were ruled ahead of the row on 2026-08-30 in
[`2026-08-30-phase3-decisions-R58-R60.md`](2026-08-30-phase3-decisions-R58-R60.md): **R58** the
façade pages under one rule for `known`, with *a guard never reads a page*; **R59** the protocol
stays tenant-blind and tenancy is the host's predicate; **R60** one three-valued `Condition`
language, the ingestion loop its first consumer, nothing built before the spec row.

**So Phase 3 is not blocked on decisions — it is blocked on a slot.** That file's own closing
section already said what the next row is:

> Phase 3's first row is a **spec** row whose brief cites R58–R60 as constraints, with
> `erm2-nwe9`'s 9.7M-degree node and a two-tenant fixture as pre-registered design tests.
> **Opening it is the founder's** (Q48, `VISION.md` §7).

**The founder has now opened it.** The Layer B spec row's constraint set, its pre-registered design
tests and its shape were all decided three days ago; its brief is writable today.

| # | what | state | why here |
|---|---|---|---|
| 0 | type registry, propose→approve, provenance, `resolve_type`, `merge_types`, `consumers`, lifecycle | **DONE [Observed]** | rows #1–#3, 3b–3e |
| 0b | typed relationships — families as vocabulary rows, edges beside them | **DONE [Observed]** | rows #4, 4b, 4c, 4d |
| 0c | governed actions — families, preflight, the invocation ledger, `parse_ref` | **DONE at v0.1 when row 6c lands** | rows #6, 6b, 6c |
| 0d | **the partner registers its own entity vocabulary** — `task`, `project`, `person`, `org`, `meeting`, `briefing`, `decision` as `kind="entity"` rows | **NOT STARTED — and it needs NO work from this project [Observed]** | `propose_type`/`approve` are shipped. **This part of the rebuild is a host act, not a build row** — separated out so it is not waiting on us |
| 0e | Phase 3's paging / tenancy / conditions decisions | **RULED 2026-08-30 [Observed]** — R58, R59, R60, all founder-visible with defaults he may reverse | not a row; they are the *constraints* the next row cites |
| **1** | **the Layer B spec row** — Phase 3's first row, a SPEC row, citing R58–R60, co-owned with the host programme | **NEXT. Unblocked except for the worker slot** | its constraints, its design tests (`erm2-nwe9`'s 9.7M-degree node; a two-tenant fixture) and its "spec before build" rule are already ruled |
| 2 | **R78's seam confirmed or overturned** by that spec's first design test | inside row 1 | it decides whether the rest is primitives or a store |
| 3 | **candidate-retrieval primitives** + **`resolve_instance`** with the four-outcome shape | **[Inferred]** the smallest thing that closes §10.3 | this is *"I already know 38 of these"* |
| 4 | **the propose-at-ingest contract** — what an ingest proposal *is*, what approves it, what provenance it carries | **[Inferred]** | the partner's capture emits no `create_project` verb at all; in this project's terms that is a missing **propose** path for the instance, beside the one that exists for the vocabulary. `Provenance` already carries `created_by`, model tier (§2.7) and `source_version` (R21) — **[Observed]**, so this row inherits rather than invents |
| 5 | **the match-vs-propose confidence gate** | **[Inferred]** | `resolve_type` already has four outcomes and a confidence; the instance analogue needs its own threshold policy, and R70 (row 6c) is the most recent worked example of narrowing exactly this kind of judgement to the right scope |
| 6 | **the host's consumer-registration obligation, stated in the spec** | **[Observed] as a gap** | §5.11 says in terms: *"v0 does not specify how a consumer gets registered (decorator, config, lint, manual)."* **Ingest curation cannot be safe while `consumers()` returns nothing** — proposing a merge into a store with no registered consumers is proposing blind. **Nothing in this project can fix it: registering consumers is a host act.** The spec states the obligation; meeting it belongs to the host |

**What Layer B does NOT need from this project**, stated so nobody waits on it: no executor and no
scheduler (`ACTIONS.md` §4 — the gate is advisory by construction); no `Condition` implementation
before its spec row (R60); no HTTP; no tenancy dimension in the protocol unless R59 is reversed.

---

## 6. One risk, named before it is designed in — **the founder's to rule**

`ROADMAP.md`'s **Rule of the ordering** — *"nothing in **#1–#4** may take a shape because the
design partner has it; if a partner need and a public-data need conflict, the public-data need
wins and the conflict is recorded"* — is scoped to rows #1–#4. **[Observed]** **It does not reach
Phase 3.** Nothing structural stops the mapping layer taking its shape *because the partner has
it*, at precisely the row where the partner is the one waiting.

**Recommended: extend the rule to Phase 3** — every Layer B shape is exercised against the public
data (CMS Montana; NYC `uvpi-gqnh` / `erm2-nwe9` / `693u-uax6`) as well as against the partner's
capture, and a conflict is **recorded** rather than resolved silently toward the partner. That is
the discipline that produced `value_set` and `not_a_type`, two shapes the partner did not need and
the public data did — and it is the cheapest available guarantee that §1's convergence stays a
finding rather than becoming a slogan.

---

## 7. Two corrections to documents this row will be read against

1. **`ROADMAP.md`'s Phase 3 prose is stale**: it still names paging and tenancy as *"two decisions
   this phase MUST take before its wedge is built (rulings R25 / R13)"*, and R58/R59/R60 took all
   three on 2026-08-30. **[Observed]** Corrected in the same change that carries this file.
2. **`INTERFACE.md` §11's open list is stale on one row**: it lists *"`Provenance` has no
   `source_version`"* among the things v1 must answer, and ruling **R21** landed it in row 3e —
   `types.py` carries the field on both shapes. **[Observed]** Noted here rather than edited,
   because §11 is a historical record of what each review round found, and the register is where
   its corrections belong.
