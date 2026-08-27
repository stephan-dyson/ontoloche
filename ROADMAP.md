# Roadmap — open-ontology

**Status:** Draft v0.1, 2026-08-27
**Priority:** **Top priority, behind CASA/compliance only.** See §0.
**Companion:** [`VISION.md`](VISION.md) — the thesis, the evidence, and what is not validated.

---

## 0. Priority position, stated exactly

**Ahead of this work:** CASA / Google OAuth verification, in the Beacon repo. Those rows are external-deadline-bound and gate Tenshen's ability to operate at all. Open at time of writing:

| Row | State | Blocked on |
|---|---|---|
| 5.23 Task 5 | Azure light-tier fallback | operator (Foundry slug + price) |
| 5.23 Task 7 | `terms.md` repairs | counsel |
| 17.50 | Limited Use privity + DPAs (`p:casa-privity`) | operator sends/signs; drafting done |
| 17.59 | Per-environment provider keys | founder mints keys |
| 17.61 | DAST scan sidecar (`p:zapscan-spec`) | founder approves the spec |

**Behind this work:** everything else — Tenshen feature rows, the v3 page wave, commercial surfaces.

**A note on what "behind CASA" means in practice.** Most open CASA items are *operator-blocked*, not agent-blocked — they wait on the founder minting a key, sending an email, or approving a spec. That means this roadmap's Phase 0 and Phase 1 can proceed in the gaps without delaying CASA at all, because they need a terminal and a conversation, not a compliance decision. **Do not use that as licence to start Phase 2 while CASA rows sit unclosed.**

---

## Phase 0 — Discovery. No code. No spec.

**Why this phase exists:** the interface is determined by *which* pollution mechanism it must prevent, and there are at least four candidates that produce materially different designs:

| If the cause was… | The interface needs… | `merge_types` is… |
|---|---|---|
| Anyone could add a type, no review | approval workflow, proposal queue | secondary |
| Nobody could *find* existing types | excellent `resolve_type` — fuzzy match, embeddings | cleanup, not prevention |
| Types added once, never retired | lifecycle, deprecation, orphan detection | irrelevant |
| Teams meant different things by one word | namespacing / scoping | **actively wrong** — merging destroys meaning |

That last row is why this phase is not optional. If the cause is semantic collision, the "merge duplicates" operation currently at the centre of the design is the *opposite* of correct.

### 0.1 — Tenshen archaeology — ✅ **COMPLETE 2026-08-27**

**Finding:** [`docs/FINDINGS-0.1-tenshen-archaeology.md`](docs/FINDINGS-0.1-tenshen-archaeology.md)

**Headline:** the four-mechanism table below is the wrong frame. Of the seven vocabularies, **five are not pollution at all** — they are *capability predicates* ("what is commentable", "what is searchable"), each locally correct, and **merging them would destroy true information**. **Two** are genuine semantic collision (mechanism 4 — present, inside one codebase, with no teams involved). And the only *documented production incident* was caused by a **fifth mechanism the table does not name**: a producer emitted a new type, every consumer gates on its own private allowlist, and the feature died **silently** in the consumer that had not been updated.

**Consequence:** `merge_types` is demoted and needs a guard; **`consumers(type)` — "who gates on this?" — becomes the centre of Phase 1**, and `predicate` becomes a first-class concept. See §1.

**Not a kill criterion trip:** collision is present but not dominant (2 of 7) and not across teams.

<details>
<summary>Original task definition (kept for provenance)</summary>

Seven disagreeing entity-type vocabularies exist in a codebase under full control, each locally correct:

- `architecture/event-spine.md`
- `assistant/actions/search_audit.py`
- `services/aura_render.py`
- `services/comment_service.py`
- `services/user_progress_service.py`
- `services/view_query_spec.py`
- `services/collab_membership_service.py` (`ENTITY_MODEL`)

**Do:** `git log -S` each one. Record, verbatim, *why each was created* and *whether its author could have found an existing list*.

**Exit criterion:** a written answer to "which of the four mechanisms above produced these seven?" — with evidence per vocabulary.

**Why it matters most:** this is the pollution mechanism, observed, with complete history, in a system fully understood. No external cooperation required, and it can be done today.

</details>

### 0.2 — The HHS pollution question *(one conversation)*

**Re-prioritised by finding 0.1.** Ask in this order — the original pollution question is now third, because 0.1 showed it was not the mechanism that caused harm:

1. **"When someone adds a new object type, how do they find out what breaks?"** — tests Cause C (silent per-consumer drop), the mechanism that actually shipped a bug in Tenshen and the one no existing tool answers.
2. **"Do two teams use the same word for different things?"** — tests Cause B (semantic collision). Present in Tenshen *without* teams, so multi-team HHS is the harder case and this is the kill-criterion probe.
3. `VISION.md` §11 Q3, verbatim: **why did the ontology get polluted, who could edit it, and what was missing?**

**Exit criterion:** either it confirms 0.1's causes, or it names a different one. Both outcomes are useful; only the *absence* of an answer blocks Phase 1.

**Watch for the disconfirming answer:** if HHS reports plain duplicate-type sprawl with no predicate structure and no silent-drop problem, then Tenshen was **not** representative and Phase 1 should be re-centred *back* toward `resolve_type`/`merge_types`. 0.1 is N=1; it earns a re-centering, not a certainty.

**Settle first:** employment terms, conflict-of-interest rules, and procurement ethics if that office could ever be a customer. Be straight that the questions are orientation, because they are.

### 0.2b — What are the contractors actually doing? *(one conversation, highest value in Phase 0)*

**[Observed]** the organisation relies on Palantir-sourced contractors to build ingest, pipelines and transforms. **[Inferred]** that most of those hours go to *mapping raw data into the ontology* rather than to moving bytes — which is the layer Airbyte and dbt do not cover (`VISION.md` §4b).

**Ask:** what does a contractor engagement actually produce — connectors, transforms, ontology definitions, actions, or all four? **Roughly what share is the ontology mapping?**

**Exit criterion:** a rough split of contractor effort across those four.

**Why it is the highest-value question here:** it either confirms the product is the mapping layer — small, complementary to the ETL incumbents, and aimed at an existing budget line — or it reveals the hours go to plumbing, in which case Airbyte already solves it and **the venture thesis narrows sharply**.

### 0.3 — Prior art *(thirty minutes)*

Read [`foundry-ontology-open`](https://github.com/cloudbadal007/foundry-ontology-open)'s ObjectType / LinkType / ActionType shapes, and Foundry's own type-registry API surface if reachable.

**Exit criterion:** a one-paragraph note on whether any existing interface is worth matching for migration purposes. Cheap insurance against reinventing a shape someone already got right.

### 0.4 — The ingestion question *(one conversation, same visit as 0.2)*

**"Has anyone tried to automate the CSV uploads, and what happened?"**

- *"Six-month queue for a pipeline"* → the wedge is a self-serve connector; reasons 1 and 2 are the operational cause. **A business.**
- *"Source system won't allow it"* → a narrow engineering problem.
- *"Nobody has asked"* → an organisation that has not noticed 500 hours. A different sale.

**Exit criterion:** which of the three. This decides Phase 3's shape, not Phase 1's — recorded now because the conversation is free while standing there.

**PHASE 0 EXIT:** 0.1 and 0.2 answered. 0.3 and 0.4 are desirable, not blocking.

---

## Phase 1 — The interface. One document, no implementation.

**Deliverable:** `docs/INTERFACE.md` — the vocabulary/type registry contract, versioned **`v0` and explicitly labelled unstable**.

**Why this component first, and not the venture's own wedge:** it is the *only* component Tenshen and open-ontology genuinely share, and Tenshen already runs a working instance of it (`work_link_types`: AI proposes a type only when confident none fit; `created_by: seed | ai | user`; usage counted). Ingestion — the venture's ROI wedge — unlocks nothing for Tenshen, which has no CSV problem.

**Surface, as corrected by finding 0.1** (was six calls; the correction is the finding's main product):

```
consumers(type)                   -> who gates on this type, and would silently drop it   [NEW — the centre]
predicates()                      -> named capability sets ("commentable", "searchable")  [NEW]
resolve_type(candidate, context)  -> existing | proposal | None
propose_type(name, definition, evidence, proposed_by)
list_types(kind, include_retired)
usage(type)                       -> count, last_seen, orphaned?
provenance(type)                  -> who, when, on what evidence
merge_types(from, into, reason)   -> MUST refuse when the two have different consumer sets [demoted + guarded]
```

**`consumers` carries the thesis now.** Finding 0.1 showed the only documented incident was a type that existed but was silently dropped by one consumer — no duplicate, no pollution, nothing `resolve_type` or `merge_types` could have caught.

**`predicate` is first-class because five of Tenshen's seven vocabularies are predicates, not vocabularies.** A registry that cannot represent "commentable" as distinct from "the type list" will flatten them and assert falsehoods.

**`merge_types` was previously described as carrying the thesis. It does not.** Against capability predicates it is *hazardous* — merging "commentable" into "searchable" claims something untrue. It survives only with the consumer-set guard.

**Exit criteria:**
- Every call has a signature, a data shape, and a stated behaviour when uncertain
- The document names which of Phase 0's mechanisms it is designed against
- `v0` and "unstable" appear in the header
- Tenshen's `work_link_types` can be expressed in it without contortion — a design *test*, not a design *input*

**Kill criterion:** if Phase 0 shows the dominant mechanism is semantic collision across teams, **stop and redesign** — the merge-centred shape is wrong and shipping it would destroy meaning.

---

## Phase 2 — Two implementations, in parallel, against one interface

This is the phase that unlocks Tenshen. **Both tracks start together.**

### 2A — open-ontology reference implementation
Postgres-backed, built against messy CSV-shaped data. **Not** built against Tenshen's schema.

### 2B — Tenshen migration
`work_link_types` migrates to call the `v0` interface, backed by Tenshen's own tables. **One service, one table — not a rewrite, and not 222 actions.**

**Depends on:** Tenshen ruling **Q7a** (`docs/specs/2026-08-27-ontology-layer-exploration-design.md` §7). If Q7a is *file-it-with-the-lint*, the lint is this phase's instrumentation. If Q7a is *do-not-file*, 2B still proceeds but loses its sensor.

**Why two implementations and not one:** an interface stressed by two unlike consumers is the only cheap cure for the N=1 problem `VISION.md` §9 names. Tenshen alone reproduces it; Tenshen plus government data does not.

**Exit criteria:**
- Both implementations satisfy the same contract tests
- The interface changed at least once because of a conflict between them *(if it never changed, the second consumer was not different enough to be informative)*
- Tenshen's relationship-type vocabulary is served through `v0` in production

---

## Phase 3 — The ingestion wedge

**The mapping layer, not an ETL tool.** Landed rows to typed entities and relationships, with curation and provenance applied at the point of ingest — so what accumulates is a curated graph rather than another pile of entities.

**Consume the existing pipeline layer.** Airbyte for extraction and loading, dbt for transformation where it fits. **Building connectors or an orchestrator is out of scope** (`VISION.md` §6), and drifting there means fighting funded incumbents on their home ground.

**Shape decided by:** Phase 0.4's answer.

**Why after Phase 2, not before:** ingestion without a curation engine fills an ontology faster — building the pollution machine before the filter. `VISION.md` §5 states this directly.

**Exit criterion:** the two people lose the hour a day, and what lands is queryable rather than a pile.

---

## Phase 4 — Generalise

Only after Phase 3 works for a real outside user, and ideally after a second organisation in a different sector confirms the shape. **[Inferred]** from N=2 that generalisation exists; that is not licence to design for it yet.

---

## Kill criteria — when to stop

Written now, while it is cheap to be honest.

| Signal | Reading |
|---|---|
| ~~Phase 0 shows the pollution cause was **semantic collision**~~ | **CHECKED 2026-08-27 — not tripped.** Collision is present (2 of 7) but not dominant and not across teams. The merge-centred shape was nonetheless wrong for a *different* reason; §1 is re-centred on `consumers` |
| **A capability predicate gets merged as a duplicate** *(new, from 0.1)* | The registry is flattening true distinctions. Stop — this is the failure that destroys meaning, and it is likelier here than duplicate-type pollution |
| Tenshen's own curated vocabulary **rots anyway** under Phase 2B | **The core `[Assumed]` bet is disconfirmed.** Stop before spending capital — this is the cheapest possible disconfirmation and it is the reason 2B exists |
| Phase 0.4 returns *"nobody has asked"* | The ingestion wedge has no buyer. Phase 3 needs a different customer |
| Phase 0.2b shows contractor hours go mostly to **plumbing**, not ontology mapping | Airbyte already solves it. **The venture narrows to the registry alone** — still worth building, much smaller, and the services-substitution business case weakens |
| The interface never changes in Phase 2 | The second consumer was not different enough — N=1 problem survived, and the abstraction is Tenshen's data model with the names filed off |
| Phase 2 slips past Phase 1's estimate by a wide margin | The interface was underspecified. Return to Phase 1, do not build through it |

---

## Standing constraints

1. **Do not quit to build this.** The current job is simultaneously the research lab, the customer-discovery channel, and the funding source. What burns savings is building for a long stretch before contact with a user.
2. **Do not build the general thing before the specific thing works.** Every scaffold in `VISION.md` §8 — 79 stars, two commits — is someone who started with the framework.
3. **The arrow points from Tenshen to open-ontology as evidence, never the reverse as a dependency** — until Phase 3 works for a real outside user. Recorded in the Tenshen spec's §12.
4. **Version everything `v0` and say it is unstable.** An interface labelled unstable is cheap to replace; one two codebases quietly assume is permanent is not.
5. **Consume the ETL layer; never rebuild it.** Airbyte, dbt, Airflow and Dagster are mature, open source and self-hostable. The gap is the mapping *above* them, which is small and unowned. Rebuilding beneath is how this becomes a decade-long fight it cannot win.
6. **Tag every claim `[Observed] / [Inferred] / [Assumed]`.** This roadmap's parent document does; a project whose thesis is *provenance and curation* should hold itself to it.
