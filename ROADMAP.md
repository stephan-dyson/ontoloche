# Roadmap — open-ontology

**Status:** Draft v0.4, 2026-08-28 — Phase 0 closed (0.3 done on evidence), **Phase 1 v0 shipped**, **ordering deliverable #2 (`docs/specs/PACKAGE.md` v0) shipped**; **rebuild-on-top confirmed by the founder 2026-08-28**. Assumptions and what would revise each: [`docs/decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](docs/decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md).
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

**Finding:** [`docs/findings/FINDINGS-0.1-tenshen-archaeology.md`](docs/findings/FINDINGS-0.1-tenshen-archaeology.md)

**Scope, stated first:** this examined **Tenshen**, not Foundry. The four mechanisms below are hypotheses about *HHS*; a single-owner codebase with no teams cannot test them, and **nothing in this finding challenges them.** They are tested at §0.2.

**Headline:** Tenshen's disease is not the one the table describes. Of the seven vocabularies, **five are not pollution at all** — they are *capability predicates* ("what is commentable", "what is searchable"), each locally correct, and **merging them would destroy true information**. **Two** are genuine semantic collision (mechanism 4 — present, inside one codebase, with no teams involved). And the only *documented production incident* was caused by a **fifth mechanism the table does not name**: a producer emitted a new type, every consumer gates on its own private allowlist, and the feature died **silently** in the consumer that had not been updated.

**Consequence:** `consumers(type)` — "who gates on this?" — and `predicate` are **added**; the evidence forced both, and HHS cannot make them unnecessary. `merge_types` is guarded. **But which call is the *centre* is NOT settled by this finding** — that is Tenshen's disease, and 0.2 may contest it. See §1.

**The more important structural result:** if 0.2 finds HHS has a *different* disease, Phase 2's "two implementations against one interface" stops being a nice-to-have and becomes the load-bearing part of the plan — an interface forced to serve two genuinely unlike consumers is exactly the N=1 cure §2 exists for. **Two different diseases is a good outcome, not a problem.**

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

### 0.2 — The HHS pollution question *(one conversation)* — **ANSWERED BY ASSUMPTION A1, 2026-08-28**

**[Assumed]** no-review + never-retired dominant (contractor rotation), collision minor, silent-drop present. Phase 1 is written against this; the office visit refines it. Kill criterion not tripped by assumption.

**Re-prioritised by finding 0.1.** Ask in this order — the original pollution question is now third, because 0.1 showed it was not the mechanism that caused harm:

1. **"When someone adds a new object type, how do they find out what breaks?"** — tests Cause C (silent per-consumer drop), the mechanism that actually shipped a bug in Tenshen and the one no existing tool answers.
2. **"Do two teams use the same word for different things?"** — tests Cause B (semantic collision). Present in Tenshen *without* teams, so multi-team HHS is the harder case and this is the kill-criterion probe.
3. `VISION.md` §11 Q3, verbatim: **why did the ontology get polluted, who could edit it, and what was missing?**

**Exit criterion:** either it confirms 0.1's causes, or it names a different one. Both outcomes are useful; only the *absence* of an answer blocks Phase 1.

**Watch for the disconfirming answer:** if HHS reports plain duplicate-type sprawl with no predicate structure and no silent-drop problem, then Tenshen was **not** representative and Phase 1 should be re-centred *back* toward `resolve_type`/`merge_types`. 0.1 is N=1; it earns a re-centering, not a certainty.

**Settle first:** employment terms, conflict-of-interest rules, and procurement ethics if that office could ever be a customer. Be straight that the questions are orientation, because they are.

### 0.2b — What are the contractors actually doing? *(one conversation, highest value in Phase 0)* — **ANSWERED BY ASSUMPTION A2, 2026-08-28**

**[Assumed]** all four produced; ontology mapping is the largest share, roughly half. Venture thesis holds provisionally.

**[Observed]** the organisation relies on Palantir-sourced contractors to build ingest, pipelines and transforms. **[Inferred]** that most of those hours go to *mapping raw data into the ontology* rather than to moving bytes — which is the layer Airbyte and dbt do not cover (`VISION.md` §4b).

**Ask:** what does a contractor engagement actually produce — connectors, transforms, ontology definitions, actions, or all four? **Roughly what share is the ontology mapping?**

**Exit criterion:** a rough split of contractor effort across those four.

**Why it is the highest-value question here:** it either confirms the product is the mapping layer — small, complementary to the ETL incumbents, and aimed at an existing budget line — or it reveals the hours go to plumbing, in which case Airbyte already solves it and **the venture thesis narrows sharply**.

### 0.3 — Prior art — ✅ **COMPLETE 2026-08-28**

**Finding:** [`docs/findings/0.3-prior-art.md`](docs/findings/0.3-prior-art.md)

**Verdict:** **no interface worth matching call-for-call; one vocabulary worth matching field-for-field.** Both candidates are pure *declaration* registries. `foundry-ontology-open`'s `Ontology` class is five `register_*` methods plus `get_linked_types` / `validate_ontology` / `summary` / `to_dict`, with **no** proposal, approval, retirement, usage, provenance or consumer concept. Foundry's public Ontology API is **read-only for type metadata** — `GET .../objectTypes` and `GET .../fullMetadata` exist; creating an object type via API does not, and the open request for it is [palantir/foundry-platform-python#318](https://github.com/palantir/foundry-platform-python/issues/318) (2026-01-19). **The proposal→approval loop has no prior art in either.**

**Three consequences carried into Phase 1:** (1) do **not** copy the `register_*` shape — `propose_type` may return a proposal, which a declaration API cannot express; (2) **do** round-trip Foundry's `status ∈ {active, experimental, deprecated}` against our `proposed | active | retired`, and say how `experimental` reads; (3) carry Foundry's `apiName` / `rid` / `primaryKey` as opaque **provenance**, not as our own fields.

**The practical asymmetry:** a customer can be migrated *off* Foundry through the read API today and *onto* it through no public API at all — so "match Foundry so we can hand data back" is not a real requirement.

<details>
<summary>Original task definition (kept for provenance)</summary>

Read [`foundry-ontology-open`](https://github.com/cloudbadal007/foundry-ontology-open)'s ObjectType / LinkType / ActionType shapes, and Foundry's own type-registry API surface if reachable.

**Exit criterion:** a one-paragraph note on whether any existing interface is worth matching for migration purposes. Cheap insurance against reinventing a shape someone already got right.

</details>

### 0.4 — The ingestion question *(one conversation, same visit as 0.2)* — **ANSWERED BY ASSUMPTION A3, 2026-08-28**

**[Assumed]** "a pipeline means a contractor engagement, and the queue is long." Phase 3 is self-serve mapping.

**"Has anyone tried to automate the CSV uploads, and what happened?"**

- *"Six-month queue for a pipeline"* → the wedge is a self-serve connector; reasons 1 and 2 are the operational cause. **A business.**
- *"Source system won't allow it"* → a narrow engineering problem.
- *"Nobody has asked"* → an organisation that has not noticed 500 hours. A different sale.

**Exit criterion:** which of the three. This decides Phase 3's shape, not Phase 1's — recorded now because the conversation is free while standing there.

### 0.5 — The proposal-quality test — ✅ **RUN 2026-08-28**

**Results:** [`docs/findings/0.5-RESULTS.md`](docs/findings/0.5-RESULTS.md) · ground truth pre-registered first in [`docs/findings/0.5-ground-truth-PREREGISTERED.md`](docs/findings/0.5-ground-truth-PREREGISTERED.md)

**Verdict: the bet survives at the top model tier, and dies at the cheap one.** Four blind agents, four tiers. Structure correct 4/4. Opus made **zero factual errors in 12 checked claims** and recomputed a poisoned metric correctly unprompted; one Sonnet also caught the temporal anomaly and asked the user rather than asserting. **Haiku inverted the CMS severity scale** — turning a worst-violations report into its opposite while every number stayed correct and nothing errored.

**Three consequences:** (1) walkthrough step 5 (impact analysis) is confirmed **load-bearing** — it is the only proposed mechanism that catches a confident wrong answer; (2) **model tier is a product parameter**, not an implementation detail, and belongs in the cost model; (3) **verification against external domain documentation must be in the product**, since the severity inversion was caught by reading CMS, not by inspecting data.

**Not measured, despite being pre-registered:** the correction rate *as a domain expert would judge it*. Factual accuracy was measured instead. The rubber-stamping risk is untouched and still needs a human.

<details>
<summary>Original task definition (kept for provenance)</summary>

**Tests the single weakest assumption in the whole venture:** that step 2 of [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md) — the system *proposing* a reading of a file rather than handing the user a schema editor — is right often enough that a domain expert keeps reviewing instead of rubber-stamping. **If the correction rate is high, the product does not work, and no amount of engineering fixes it.**

**No office file can ever be used for this.** Federal data does not leave the building, and a venture resting on the founder's day-job access is compromised regardless of care taken. **The public equivalent is better anyway** — same domain, same agency family, reproducible by any reader, zero conflict-of-interest surface.

**Data, counted over all 419,479 rows 2026-08-28:** [`NH_HealthCitations_Aug2026.csv`](https://data.cms.gov/provider-data/dataset/r5ix-sfxw) — CMS nursing-home health citations. 165,336,194 bytes, 23 columns, **14,627 facilities**, updated 2026-08-01. Confirmed pathologies: a boolean-sounding column holding **six** status strings with no yes/no among them; **1.28%** of rows (5,338 of 416,948) with a correction date *preceding* the survey date; a `Location` column **99.988% redundant** with four others; and 104 facility names shared across multiple CCNs, so name-based resolution merges distinct facilities. Ground truth is pre-registered in [`docs/findings/0.5-ground-truth-PREREGISTERED.md`](docs/findings/0.5-ground-truth-PREREGISTERED.md).

**Do:** hand the file (or a slice) to a capable model cold and ask it to produce step 2's proposal. Score it against the ground truth a human establishes separately. **Measure, do not eyeball.**

**Exit criterion:** a correction rate, with the scoring method written down. Plus a specific answer to: **does it notice the correction-date anomaly, or does it confidently propose an "overdue" metric that is silently wrong for 1% of rows?**

**Why this belongs in Phase 0:** it is the cheapest possible disconfirmation of the core usability bet, it costs nothing, it needs no cooperation from anyone, and — like 0.1 — an agent can run it today.

**Known gap:** the file has no `Inspector` column, so this tests entity resolution on **Facilities** but not on **People**, and the walkthrough's step-4 action has no counterpart. Find a second public source for the person half, or leave it untested and say so.

</details>

**PHASE 0 EXIT — PASSED BY ASSUMPTION 2026-08-28.** 0.1, 0.3 and 0.5 done on evidence; 0.2, 0.2b, 0.4 assumed (A1–A3) pending the office visits. **0.3 closed 2026-08-28** — its verdict is Phase 1's first prior-art input. Two 0.5 gaps also remain open and are scheduled below: T4 entity resolution on the name-collision slice, and the People half.

---

## Phase 1 — The interface. One document, no implementation. — ✅ **v0 SHIPPED 2026-08-28**

**Deliverable:** [`docs/specs/INTERFACE.md`](docs/specs/INTERFACE.md) — the vocabulary/type registry contract, versioned **`v0` and explicitly labelled unstable**. **Written 2026-08-28 against assumption A1.** All four exit criteria met (checked in its §13).

**What shipped:** twelve calls — the ten the surface below names, plus `approve`/`reject` named and shaped, plus `retire`, plus `register_consumer`/`record_use` (named because `consumers()` and `usage()` are otherwise unimplementable). Data model, model tier as a parameter, and an evidence slot carrying external-documentation citations.

**Two changes to the surface below, both forced by the CMS data, both resolved against Tenshen's needs** ("Rule of the ordering"): (1) **`value_set` added as a kind** — CMS's two most dangerous fields are property value sets (the six-value `Deficiency Corrected`, the ordered A–L severity scale), and without the kind the severity ordering has no provenance and no evidence slot; Tenshen needs no such kind. (2) **`resolve_type` gained a fourth outcome, `not_a_type`** — the 99.988%-redundant `Location` column resolves to `None` under the three-outcome shape, which reads as "go propose it", handing the pollution machine its first type; Tenshen's classifier-sourced candidates cannot hit this case. **This is Phase 2's exit criterion ("the interface changed at least once") arriving in Phase 1.**

**Tenshen test result:** expressible, **seven contortions recorded, none designed away.** Two are structural — `is_symmetric`/`inverse_label` have no home until #4, and `work_link_types` has **no approval step at all** (AI proposals persist immediately), which v0 can only express as `approval_policy="auto"` with `approved_by="auto:classifier"`. Two are findings **for the beacon program**: `usage_count` is a bare counter with no `last_used_at`, so the venture's rot sensor **cannot currently fire**; and nothing registers a consumer, so `consumers()` returns `known: 0` — the very blind spot 0.1 diagnosed.

**Kill criterion checked, not tripped** (§12 of the document): `merge_types` is 1 of 12 calls with four non-overridable refusals, and the mechanism-4 answer is `namespace` — preserve, not merge.

**Next:** ~~#3, Phase 2A~~, ~~#3b, the async adapter~~, ~~#4 `docs/specs/EDGES.md`~~, ~~3e, the v0.1 amendments~~ and ~~4b, EDGES implemented~~ — **all shipped**. **Slices 1–2 and beacon 21.2 now have a shipped edge store to build against rather than a specification**, which is what 4b was sequenced ahead of #6 to deliver. Next is **#6, the actions spec** — which ruling **R31** binds as it is written — with **#5 (Phase 2B)** unblocked in parallel. Row 4b's own loop is explicit about where the next real signal comes from, and it is not a seventh review lens: **a real consumer over a real store.**

<details>
<summary>Phase 1 as briefed (kept for provenance)</summary>

**Why this component first, and not the venture's own wedge:** it is the *only* component Tenshen and open-ontology genuinely share, and Tenshen already runs a working instance of it (`work_link_types`: AI proposes a type only when confident none fit; `created_by: seed | ai | user`; usage counted). Ingestion — the venture's ROI wedge — unlocks nothing for Tenshen, which has no CSV problem.

**Surface, as corrected by finding 0.1** (was six calls; the correction is the finding's main product):

```
consumers(type)                   -> who gates on this type, and would silently drop it   [NEW — required]
predicates()                      -> named capability sets ("commentable", "searchable")  [NEW]
resolve_type(candidate, context)  -> existing | proposal | None
propose_type(name, definition, evidence, proposed_by)
list_types(kind, include_retired)
usage(type)                       -> count, last_seen, orphaned?
provenance(type)                  -> who, when, on what evidence
merge_types(from, into, reason)   -> MUST refuse when the two have different consumer sets [demoted + guarded]
```

**`consumers` is required, and provisionally carries the thesis.** Finding 0.1 showed the only documented incident was a type that existed but was silently dropped by one consumer — no duplicate, no pollution, nothing `resolve_type` or `merge_types` could have caught. **That is Tenshen's disease.** Whether it is also HHS's is unknown until §0.2; if HHS reports plain duplicate sprawl, `resolve_type` reclaims the centre and this ordering flips. ~~Do not write Phase 1 until 0.2 reports~~ **Gate lifted 2026-08-28 (founder).** Phase 1 is written against A1: **no single call is the centre — the proposal→approval loop is**, with `consumers`, `resolve_type`, lifecycle (`usage`/orphaned/retire) and `propose_type` all first-class. The document header carries *"written against the 2026-08-28 assumptions; see docs/decisions/"*.

**`predicate` is first-class because five of Tenshen's seven vocabularies are predicates, not vocabularies.** A registry that cannot represent "commentable" as distinct from "the type list" will flatten them and assert falsehoods.

**`merge_types` was previously described as carrying the thesis. It does not.** Against capability predicates it is *hazardous* — merging "commentable" into "searchable" claims something untrue. It survives only with the consumer-set guard.

**Exit criteria:**
- Every call has a signature, a data shape, and a stated behaviour when uncertain
- The document names which of Phase 0's mechanisms it is designed against
- `v0` and "unstable" appear in the header
- Tenshen's `work_link_types` can be expressed in it without contortion — a design *test*, not a design *input*

**Kill criterion:** if Phase 0 shows the dominant mechanism is semantic collision across teams, **stop and redesign** — the merge-centred shape is wrong and shipping it would destroy meaning.

</details>

---

## Ordering for the Tenshen rebuild (founder direction 2026-08-28)

**Direction:** sequence open-ontology's components by **what Tenshen's rebuild consumes first.** Tenshen's own cheap version proceeds in the beacon repo per its spec §6 and is **not waited on** (beacon `docs/specs/2026-08-27-ontology-layer-exploration-design.md` §12, commit `27a9b712`). The abstraction is still derived from CMS data first, Tenshen second — Tenshen is the *design test*, never the *design input*.

| # | open-ontology deliverable | Tenshen slice it unblocks | Session model |
|---|---|---|---|
| 1 | ~~**`docs/specs/INTERFACE.md` v0**~~ — **DONE 2026-08-28** ([`docs/specs/INTERFACE.md`](docs/specs/INTERFACE.md)) | Slice 0 (one entity-type vocabulary); `work_link_types` migration (2B) | Opus |
| 2 | ~~**`docs/specs/PACKAGE.md` v0**~~ — **DONE 2026-08-28** ([`docs/specs/PACKAGE.md`](docs/specs/PACKAGE.md)) — `open_ontology` package shape, a **fifteen-primitive** storage-adapter protocol, SQLite + Postgres table shapes, the `attributes` schema-per-kind mechanism, and **109 contract tests as the definition of conformance** *(124 since row 3c)* | 2B needs `pip install` + Tenshen's own tables behind the adapter | Opus |
| 3 | ~~**Phase 2A** reference implementation, passing the contract tests on CMS data~~ — **DONE 2026-08-28** ([`docs/runs/2A-RUN.md`](docs/runs/2A-RUN.md)). The repo's first code: 15-primitive adapter, the twelve calls, SQLite **and** Postgres, **all 109 contract tests green on both backends in one run (229 passed, 0 failed, 0 skipped)**, and the CMS design test executing against the pre-registered ground truth | **the gate for 2B** (assumption A5 — replaces §12's "real outside user") — **MET** | Opus build, Sonnet mechanical |
| 3b | ~~**AsyncStorageAdapter** — async mirror of the 15-primitive protocol + an async run of the same contract suite~~ — **DONE 2026-08-28** ([`docs/runs/3B-ASYNC.md`](docs/runs/3B-ASYNC.md)). `AsyncStorageAdapter`, `AsyncRegistry`, async SQLite **and** async Postgres, **the same 109 contract ids green on both in one run (267 passed, 0 failed, 0 skipped)**, sync suite still green (`229 passed`), 496 for both stacks in one process. **Generated from the sync source, not forked** *(ruling R1, [`docs/decisions/2026-08-28-package-v0-rulings.md`](docs/decisions/2026-08-28-package-v0-rulings.md))* | **the async gate for #5** — **MET** | Opus |
| 3c | ~~**Use-case validation pass**~~ — **DONE 2026-08-29** ([`docs/findings/3C-VALIDATION.md`](docs/findings/3C-VALIDATION.md)). UC3 (`uvpi-gqnh` DPR / `erm2-nwe9` 311-OTI / `693u-uax6` DOT) run against both specs, plus eleven adversarial rounds. **Mechanism 4's answer held** — three scoped `status` types coexist and `cross_namespace_merge` refuses non-overridably — and **seven contortions were recorded** (INTERFACE 8–12, PACKAGE B7–B8). Ruling **R4** landed; **Q1–Q7 are open for a ruling** (§6). The suite grew **109 → 124** and **nine code defects were fixed**, including **the kill row itself tripping** on Tenshen's declared capability shape. **Eighteen adversarial rounds, eighteen NOT YET verdicts — the loop did not converge and the row is closed on an escalation** (§7.5); **Q1–Q7 ruled as R6–R12** 2026-08-29 (rows 3d/3e/#4 carry them); **Q8 open** | none directly — it is the kill-criterion mechanism finally exercised; every later spec inherits the protocol | Opus |
| 3d | ~~**Upstream fixes from beacon 21.1**~~ — **DONE 2026-08-29** ([`docs/runs/3D-RUN.md`](docs/runs/3D-RUN.md), `094872f`). U1 savepoint-scoped `transaction()` over a host-owned session (ruling **R5**) — *sharing a connection is not sharing a transaction*, and the reference `AsyncPostgresAdapter` was forcing autocommit on a connection it was lent; U2 a **third** reference leg (`sqlite_minimal`) that is **natively** degraded — five tables where the reference schema has nine, five flags declined at once — because simulating degradation with a test double is a double reporting on itself; U3 `attribute_projections`; U4 §3.3 doc sync **plus** a PACKAGE drift check, because the drift had moved into the half of the specification nobody was checking; **R8**, **R12**'s coverage report, **R13**. Suite **124 → 129**; `340 passed` / `374 passed`, three legs, one run each. **Three adversarial rounds, six fresh reviewers, six NOT YET verdicts — closed at the cap with an honest convergence note (§5.1), not on a clean pass.** Five BLOCKING findings, each one a wrong adapter that had been reaching a clean `CONFORMANT`; two of them were defects introduced by the previous round's own fix | **the transaction seam beacon 21.2 builds on** | Opus |
| 4 | ~~**`docs/specs/EDGES.md` v0**~~ — **DONE 2026-08-29** ([`docs/specs/EDGES.md`](docs/specs/EDGES.md)). Typed relationship store; an edge family **is** a `kind="edge"` `TypeEntry`, not a fifth kind and not a predicate, so families inherit propose/approve, `resolve_type`, lifecycle and **`consumers`** unchanged and EDGES adds no call of its own (the surface went 13 → 14 in row 3e, for `reinstate`). `equivalent_to` closes INTERFACE contortion 9 (**R7**) — symmetric, **non-transitive**, non-merging, and the non-merging half checked against the *shipped* `merge_types`, which still refuses `cross_namespace_merge` under explicit acknowledgement. `neighbors` capped at **depth 2** (R13's consequence), three adapter primitives, four capability flags + two declarations. **Eleven contortions recorded, none designed away**; INTERFACE §5.12 **15 → 19** and §5.4 **11 → 16**, both amended in this change per **R3**. **Three adversarial rounds, six reviewers, ten BLOCKING — no clean round**, closed on the cap with a convergence note; **Q12–Q21 open for a ruling** | Slice 1 (read seam), Slice 2 (`relations`), spec §4.3 provenance | Opus |
| 4b | ~~**EDGES v0 implemented**~~ — **DONE 2026-08-29** ([`docs/runs/4B-RUN.md`](docs/runs/4B-RUN.md)). Adapter primitives **16–18** on all three reference backends, keyset-paged on `(created_at, edge_id)` with a frontier clause that treats a NULL instance id as a **value** rather than a wildcard; four edge capability flags and three declarations; store schema **3 → 4**. `add_edge` / `retract_edge` / `neighbors` / `edge_provenance`, with §2.4.1 and **R18** enforced at all three declaration doors, the assembly bound **on by default** counting DISTINCT edges, and `equivalent_to` seeded at store creation. Suite **150 → 194**: `C17` (34) holds **every BLOCKING finding of row #4's own loop — all ten of which had been fixed only in a throwaway probe kit the package does not import** — and `C18` (10) re-runs the three design tests through the shipped store, reproducing every pre-registered number (CMS 400/69/400 over 92 tags; NYC 102 edges, 18 of 25 matched, max 16 trees on one lot). Warnings **20 → 22**: `edge_family_unregistered` and `endpoint_type_merged`, **the first two values this project has minted because writing and running the code found cases a specification had not**. Ruling **R31** lands as standing constraint 8; `check_spec_drift.py` goes from two gates to **five**, and the two it gained unprompted (EDGES' printed shapes, all eighteen primitive signatures) had both already drifted. **Three adversarial rounds, six reviewers, five NOT YET — eight BLOCKING, eight MAJOR**, closed on the cap with a convergence note that says the findings did **not** shrink. **Sixteen deviations recorded, none designed away; Q27—Q34 open for a ruling** | Slices 1–2 have a shipped seam; 21.2 has an edge backend | Opus |
| 4c | **Edge semantics** — rulings R32–R39 ([`docs/decisions/2026-08-29-4b-rulings-R32-R39.md`](docs/decisions/2026-08-29-4b-rulings-R32-R39.md)): `payload_schema` validation on edges (R34), `neighbors` follows a merged type's successor chain with `via_successor` (R38 — what makes `merge_types` safe on a store with edges), second retraction refused (R39), `edge_amended` decided (R37), §2.4 sentence narrowed (R33). Sequenced after #6 and **before beacon builds slice 1 against the store**, because R38 changes what an edge endpoint means | Slice 1 correctness after any merge | Opus |
| 3e | ~~**v0.1 amendments from the 3c rulings**~~ — **DONE 2026-08-29** ([`docs/runs/3E-RUN.md`](docs/runs/3E-RUN.md)). **R6** `search_namespaces` on `resolve_type`, closing INTERFACE contortion 8 — UC3's central finding, and mechanism **2** reintroduced by §2.6's answer to mechanism **4**; **R10** name-level attribute schemas, closing `C15-07`, the limitation recorded in that mechanism's own flagship justification; **R11**/**R19** `reinstate` as the **fourteenth** call, with `successor_active` and `alias_collision` as the twentieth and twenty-first `Refusal.reason`; **R17** `created_by: derived`; **R21** `Provenance.source_version`. Store schema **1 → 3**. Warnings **16 → 20**, now checked mechanically like §5.12; §6.2's group headers checked too. Suite 129 → **150**, `388 passed` / `421 passed`, three legs `CONFORMANT`. **Three adversarial rounds, six reviewers, six NOT YET — ten BLOCKING, sixteen MAJOR**, closed on the cap with a convergence note: four of the ten BLOCKING lived inside a previous round's fix, and thirteen of the twenty-one new ids pin claims the specs already made. **Q22–Q26 open for a ruling** | none directly — UC3/Phase 3 and governance; deliberately after EDGES so Tenshen's slices are not delayed | Opus |
| 5 | **Phase 2B** — Tenshen migration, in beacon. Builds against 3d's seam (R14: a `BorrowedHarness` is required for the gate) and EDGES v0 (R24: no tenancy dimension in the protocol — the adapter filters) | — | beacon program's call |
| 6 | Actions-registry spec | none yet — Tenshen's actions stay in code (spec §10.7) | later |
| 7 | **Phase 3** ingestion / mapping | none — the venture's wedge, not Tenshen's need | later |

**Alongside, not gating:** ~~0.3 prior art~~ **done 2026-08-28, before #1** ([`docs/findings/0.3-prior-art.md`](docs/findings/0.3-prior-art.md)); 0.5's T4 rerun on the name-collision slice of the full CMS file (Opus); the People-half source hunt (Sonnet).

**Rule of the ordering:** nothing in #1–#4 may take a shape *because* Tenshen has it. If a Tenshen need and a CMS-data need conflict, the CMS need wins and the conflict is recorded in the spec — that recorded conflict is Phase 2's exit criterion ("the interface changed at least once") arriving early.

### Deliverable #2 result — `docs/specs/PACKAGE.md` v0, 2026-08-28

**What shipped:** a zero-dependency `open_ontology` package (Python 3.11 floor, stdlib + one driver per backend, **no ORM mandated** — justified in its §2.4); a **fifteen-primitive** storage adapter built on one rule — *the adapter stores records and does not know what a proposal, an approval or a refusal is*; SQLite and Postgres table shapes over nine tables; the **`attributes` schema-per-kind mechanism decided** rather than deferred (versioned per kind, three modes, default `off` so #1's "opaque to v0" contract is untouched, plus an unconditional key census so the escape hatch accumulates *visibly*); and **109 contract tests in seventeen groups**, covering every `INTERFACE.md` §5 refusal with none untested.

**The structural result:** `Capabilities` — the adapter declaring in advance what it *cannot* answer, with a sentence per gap — is what makes Rule U implementable across unlike backends, and it is what lets a one-table registry be conformant without weakening conformance. **Exactly two guarantees are non-negotiable:** uniqueness of `(namespace, kind, name)`, and transactional approve. **Zero of §5's refusals are enforced by a backend.**

**Tenshen test result:** **yes, as a third backend — nine of fifteen primitives serve as-is, six contortions recorded, none designed away.** The price is one `ALTER TABLE` adding three columns (`status`, `attributes_json`, `provenance_json`) to `work_link_types`, with `is_symmetric`/`inverse_label` projected both ways so beacon's existing reads keep working — **one table, no rewrite**, as 2B asks. `consumers()` needs **no schema change at all** (a config-backed consumer source), which is the highest-value thing available on that path. Two contortions are findings for beacon rather than complaints: no proposal table means **review costs exactly one table**, and no `last_used_at` means the rot sensor still cannot fire.

**A new rule the design test forced:** *a destructive override that cannot be recorded is refused.* On a backend with no event log, `retire(force=True)` and `merge_types(acknowledge=…)` return a refusal rather than doing the destructive thing unrecorded.

**Kill criterion checked, not tripped** (its §7.5), on four mechanical grounds: nine reference tables against Tenshen's one; 9-of-15 primitive fit rather than 15-of-15; more than half the reference schema by column count is CMS-forced weight Tenshen has no use for; and both protocol amendments made during the design tests were adopted on the reference-deployment case, not on Tenshen's.

**Blocking finding for #5, and it is on this line, not beacon's:** **the adapter protocol is synchronous and beacon's data layer is `AsyncSession` throughout.** A sync adapter cannot share beacon's transaction, and driving one from a thread is not safe. `AsyncStorageAdapter` / `AsyncRegistry` is a **prerequisite of #5** and is not yet scheduled — **founder ruling wanted: inside #3's scope, or a new row between #3 and #5?** Two smaller rulings are in `PACKAGE.md` §11.1 (`attribute_census` as a call beyond §5; three new `Refusal.reason` values).

**Known gap, recorded not papered over — ~~open~~ CLOSED by #3 on 2026-08-28:** the CMS design test was **specified, not executed** — the 400-row `sample_state.csv` 0.5 actually used was not in the repo and `docs/tools/make_sample.py` regenerates a *different* (300-row random) sample. The public 400-row sample is now checked in at `open_ontology/contract/fixtures/cms_sample_400.csv` with `tools/make_sample_state.py` to regenerate it, and the CMS test runs. The source file re-downloaded on 2026-08-28 is byte-for-byte the size the ground truth records, so the fixture is the sample 0.5 actually cut.

**Next:** ~~#3, Phase 2A~~, ~~#3b, the async adapter~~ and ~~#4, `docs/specs/EDGES.md`~~ — **all shipped**. Next is **3e, the v0.1 amendments** (R6, R10, R11 — and EDGES adds Q12's `created_by` gap and Q16's `source_version` to that row's list); **#5 (Phase 2B) is no longer blocked on an async adapter**, and slices 1–2 now have a spec to build against.

---

### Deliverable #3 result — Phase 2A, the reference implementation, 2026-08-28

**What shipped: the repo's first code, and the 2B gate is met.** [`docs/runs/2A-RUN.md`](docs/runs/2A-RUN.md) carries the run record and the exact commands.

**The result in one line:** `229 passed in 49.25s` — **all 109 contract tests green on SQLite *and* on Postgres 16.14, in one process, in one run**, plus the CMS design test executing against the pre-registered ground truth. Zero runtime dependencies in the base install; Python 3.11 floor.

**The CMS design test is no longer specified-but-not-executed.** The 400-row Montana sample is checked in as a fixture and reproduces every pre-registered number exactly: `facility` 10, `survey` 69, `citation` 400, `deficiency_tag` 92, four of the six correction statuses, 0 tags with more than one description (T5), `Location` exactly rebuilt from four sibling columns in **400 of 400** rows (T3), `Processing Date` single-valued (T7). **Eight type rows, not four hundred** — the registry stores types, not instances, and `C13-01` asserts against the reading that would have made the harness commit the T3/T6 failure itself.

**The one [Inferred] count was computed, not asserted.** `PACKAGE.md` §8.2 marks the severity-code count [Inferred] because it was quoted from run **D** — the run that got the ordering backwards — and instructs the test to compute it. Computed independently: **7 distinct codes, B C D E F G J.** That confirms the quotation rather than relying on it.

**The severity case runs end to end.** `INTERFACE.md` §10's worked example, verbatim, as test `C5-03`: a haiku-tier `value_set` proposal asserting *"higher letters are LESS serious"* with no evidence carries `no_evidence` and `unverified_semantics`, is refused for auto-approval with `tier_below_auto_approve_policy`, and if a human approves it anyway stays permanently enumerable.

**Fourteen deviations recorded, none silently resolved** ([`docs/runs/2A-RUN.md`](docs/runs/2A-RUN.md) §4). **One wants a founder ruling: D-1.** `PACKAGE.md` §3.4 and test `C11-04` require `register_consumer` against a read-only consumer source to return a `Refusal`, but ruling **R3** closed `Refusal.reason` at fourteen values and none of them says this honestly. Implemented as a raised `NotSupported` — a loud failure, which is what `C11-04` is actually about — pending a ruling to either add a fifteenth reason (amending `INTERFACE.md` §5.12 in the same change, per R3) or confirm the exception. The other thirteen are fields the docs require but do not list, methods beyond the twelve that a test demands (the Foundry import mapping; `into_namespace`, without which the `cross_namespace_merge` refusal is unreachable), and one genuine internal contradiction: **§2.8 says v0 does not detect a domain semantic automatically, while §10's worked example and `C4-06` require the warning to fall out of the call alone.** Resolved with a conservative rule that over-warns; if §2.8 is meant literally the fix is an explicit proposer flag, which is an `INTERFACE.md` change.

**What this does not establish, stated plainly.** Both reference backends are SQL and both declare every capability `True`. The interesting half of the conformance claim — *an unlike backend with real gaps is conformant without weakening conformance* — is exercised by a degraded-adapter wrapper this repo wrote, not by a third party's store. **The first real test of it is `work_link_types` behind the adapter, which is 2B.**

~~**Nothing async exists**, per ruling **R1**. Row **3b** remains the blocking prerequisite of **#5**.~~ — **closed by #3b on 2026-08-28**; see the #3b result below.

---

### Deliverable #3b result — the async mirror, 2026-08-28

**What shipped, and the #5 gate is met.** [`docs/runs/3B-ASYNC.md`](docs/runs/3B-ASYNC.md) carries the run record, the design and the exact commands.

**The result in one line:** `267 passed in 61.22s` — **the same 109 contract ids, with the same test-function names, green on async SQLite *and* async Postgres 16.14, in one process, in one run.** The sync suite is still green in the same working tree (`229 passed`), and both stacks against both backends in one process is `496 passed`. The base install still has **zero runtime dependencies**; the one new optional dependency is `aiosqlite` under an `[aio]` extra. Async Postgres needed nothing new — `psycopg` v3 already ships `AsyncConnection`, so that leg is **green, not PENDING**.

**The structural result, and it is the point of the row: the async tree is generated from the sync source, not forked.** `tools/unasync.py` transforms `registry.py`, `adapter.py`, `backends/_sql.py` and all seventeen contract test modules into `open_ontology/aio/`. It is AST-driven: which functions become `async def` is a **fixpoint** seeded with the fifteen primitives rather than a list somebody maintains; `await` wraps whole call expressions and is parenthesised exactly where precedence needs it; `with adapter.transaction()` becomes `async with` and `transaction()` is never awaited; and it **refuses to emit** code it cannot prove correct. **5,417 of the 6,320 lines** in the async tree are generated; the 903 hand-written ones are the two drivers and four async-only test modules. Everything with no I/O in it — every record and query dataclass, `Capabilities`, both dialects, the row↔record mapping, **the migration SQL itself**, `types.py`, `policy.py`, `errors.py` — is *borrowed*, not copied.

**Drift cannot happen quietly, and that was verified rather than asserted.** `test_generated_matches_source.py` regenerates the whole tree in memory on every run and compares byte for byte. Breaking it on purpose — one comment line added inside `Registry._require` — fails the suite with *"the async mirror is stale -- run `python tools/unasync.py`"*. `test_parity.py` covers what a byte comparison cannot: that the async facade has every sync call and no extras beyond the documented construction pair, that every call takes the same parameters, and that all sixteen facade calls and fourteen of the fifteen primitives are coroutines while `transaction()` is not.

**R1's assumption is confirmed, with two named exceptions, and the kill criterion was checked and not tripped.** Mirroring sync→async *is* mechanical for the registry, the protocol and the whole suite. It is not mechanical for **construction** — `Registry.__init__` awaits `capabilities()` and `migrate()` and `__init__` cannot be a coroutine, so the async facade is built with **`await AsyncRegistry.open(adapter)`** (D-A1, the only difference in the shape of the API) — nor for the **driver connection layer**, where `aiosqlite` and `psycopg` genuinely differ. Neither is a finding against #3's design; both follow from the language and the drivers.

**One thing the async run establishes that the sync run structurally could not.** `approve`'s docstring says the read and all four writes are one transaction, *which is what turns `already_decided` from a race into an idempotent refusal*. In one synchronous process that is an argument. `test_concurrency.py` makes it a test: two registries, two connections, one event loop, `asyncio.gather` over two approvals of the same proposal — **exactly one `TypeEntry`, exactly one `Refusal("already_decided")`, one `approved` event in provenance**, on both backends, which reach the guarantee by different mechanisms (`BEGIN IMMEDIATE` and `SELECT … FOR UPDATE`).

**Fourteen new deviations recorded, none silently resolved** ([`docs/runs/3B-ASYNC.md`](docs/runs/3B-ASYNC.md) §5); the fourteen of 2A are **inherited unchanged**, because the mirror is generated from the code that implements them — **D-1 still wants the same founder ruling, and now wants it in two places.** The new ones that a caller can feel: **D-A1** (construction is `await AsyncRegistry.open(...)`); **D-A3** (on Windows, `psycopg` refuses asyncio's default `ProactorEventLoop` — an embedding application must select a selector loop, as the suite does); **D-A4** (async SQLite is a thread offload because SQLite has no async C API — this is *not* R1's hazard, which is a synchronous adapter driven from a thread by an async caller); **D-A11** (`AsyncPostgresAdapter.open` takes an already-open connection where the sync one takes a factory).

**What this does not establish, stated plainly.** The async tree has never been driven by an `AsyncSession` it did not create. R1's actual requirement — an adapter that can *share beacon's transaction* — is demonstrated here only as far as "every primitive is a coroutine awaited on the caller's loop". **The first real test of it is `work_link_types` behind the async adapter, which is 2B.** Both async reference backends still declare every capability `True`.

---

## Phase 2 — Two implementations, in parallel, against one interface

This is the phase that unlocks Tenshen. **Both tracks start together.**

### 2A — open-ontology reference implementation — **DONE 2026-08-28**
Postgres-backed, built against messy CSV-shaped data. **Not** built against Tenshen's schema.

**Landed:** the `open_ontology` package — 15-primitive adapter, the twelve calls, SQLite and Postgres backends, 109 contract tests green on both in one run, the CMS design test executing. Run record: [`docs/runs/2A-RUN.md`](docs/runs/2A-RUN.md).

### 2B — Tenshen migration
`work_link_types` migrates to call the `v0` interface, backed by Tenshen's own tables. **One service, one table — not a rewrite, and not 222 actions.**

**Depends on:** Tenshen ruling **Q7a** (`docs/specs/2026-08-27-ontology-layer-exploration-design.md` §7). If Q7a is *file-it-with-the-lint*, the lint is this phase's instrumentation. If Q7a is *do-not-file*, 2B still proceeds but loses its sensor.

~~**Also depends on an async adapter protocol, which does not yet exist**~~ — **shipped 2026-08-28 as row #3b** ([`docs/runs/3B-ASYNC.md`](docs/runs/3B-ASYNC.md)). beacon's data layer is `AsyncSession` throughout and a synchronous adapter cannot share its transaction, so `AsyncStorageAdapter` / `AsyncRegistry` now exist, generated from the sync source, with the same 109 contract ids green on async SQLite and async Postgres (`267 passed`). **Still to be proved by 2B and not by 3b:** that the adapter can share an `AsyncSession` it did not create. Two notes for whoever does 2B — construction is `await AsyncRegistry.open(adapter)` (deviation D-A1), and `AsyncPostgresAdapter.open` takes an already-open connection (D-A11), which is what beacon will have. **Concrete price of 2B otherwise:** one `ALTER TABLE` on `work_link_types` adding `status`, `attributes_json` and `provenance_json`; `consumers()` needs no schema change at all.

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

**Two decisions this phase MUST take before its wedge is built (rulings R25 / R13, 2026-08-29):** (1) **paging** for `list_types` and `neighbors`, decided together — EDGES v0 measured a 9,738,128-degree node on UC3's own fixture (`erm2-nwe9`, `agency=NYPD`), so an unpaged hop is a result nobody can hold; the v0 façade does not page and the assembly bound only tells the truth about it; (2) whether **tenancy** ever becomes a protocol dimension — v0 says filtering is the host's job (R24, [Assumed]).

**Provisionally homed here (supervisor assignment 2026-08-28, under the make-assumptions ruling; founder may move it):** **instance resolution** — the walkthrough's *"I already know 38 of these"* — which `docs/specs/INTERFACE.md` §10.3 found belongs to no deliverable. It is the mapping layer's problem (rows → entities), not the type registry's, so it lives with ingestion. **[Assumed]**

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
| **A capability predicate gets merged as a duplicate** *(new, from 0.1)* | The registry is flattening true distinctions. Stop — this is the failure that destroys meaning, and it is likelier here than duplicate-type pollution. **TRIPPED IN TEST 2026-08-29** on Tenshen's declared shape (`indexes_membership=False`): unknowable extents compared equal and the merge fell through to an overridable guard — caught by 3c's adversarial loop (round 9) before any real merge, fixed `0e89037`, pinned by C9-08. Supervisor judgment: implementation defect, not design; row stays armed. Founder may rule otherwise — [`docs/decisions/2026-08-29-3c-rulings-R6-R12.md`](docs/decisions/2026-08-29-3c-rulings-R6-R12.md). **TRIPPED IN TEST A SECOND TIME 2026-08-29**, by row #6's second adversarial round and by the *other* end of the same expression: guard 2 refused unless the two extents were byte-identical, and **two EMPTY extents are byte-identical** — so two predicates proposed by an `ai:` actor at Haiku into an auto-approving namespace went live and then merged under two acknowledgements, reproduced end to end against `open_ontology.Registry`. An empty extent is *no evidence of membership*, not *evidence of identical membership*. Fixed and pinned by **`C10-09`**, suite 194 → 195; `INTERFACE.md` §2.3 and §5.10 amended in the same change. **The judgment is re-framed, and the re-framing is round 3's founder lens's condition of sign-off.** Calling this *"implementation defect, not design"* a second time would file two unrelated bugs where there is **one design defect found twice**: refusal #2's guard is a **two-valued comparison over a three-valued fact** — an extent is known-equal, known-different, or *unknown-or-empty* — and the two trips are the two ends of the same expression. Row 3c broke it on *unknowable*; row #6 broke it on *empty*; `ACTIONS.md` §2.5 states the category exactly (*"an empty extent is no evidence of membership, not evidence of identical membership"*) without noticing it had just described trip 1. **This project applies the three-valued rule everywhere else it matters** — `TierOrder.below` returns `bool | None`, `PreconditionResult.holds` is three-valued, `ConsumerReport.complete` is permanently false — **and the one guard it was not applied to is the one the kill row runs through.** *The design is not what tripped:* `namespace` is untouched across both trips and `cross_namespace_merge` still refuses under explicit acknowledgement on live NYC data. **TRIPPED IN TEST A THIRD TIME 2026-08-29**, by round 3 of the same row and through a call that is not `merge_types` at all: `retire(successor=)` redirects `resolve_type` to the successor at confidence 1.0, so it *is* the collapse — and it carried none of the merge's guards. The pair refused non-overridably under all five acknowledgements collapsed through retirement with no refusal, no acknowledgement and no warning, across kinds too. Fixed by giving `retire` §5.10's two **identity** guards (#2 and #3), non-overridable and `force=True` included, and pinned by **`C9-18`**; suite 195 → 196. **Three trips, and the third widens the diagnosis rather than repeating it: the defect is not only a two-valued guard over a three-valued fact, it is a guard written for ONE CALL over a fact that MORE THAN ONE CALL can change.** `check_merge_guard.py` (row 4c) must therefore enumerate the *callers* as well as the states. **The row stays armed, the record says one defect found three times rather than three defects, and the fix owed is a checker rather than a fourth patch** — `check_merge_guard.py`, enumerating every state an extent can be in and asserting the guard's answer for each, scoped into row 4c. Three defect classes in this project were closed by a mechanical checker; the class the kill row runs through has none |
| Tenshen's own curated vocabulary **rots anyway** under Phase 2B | **The core `[Assumed]` bet is disconfirmed.** Stop before spending capital — this is the cheapest possible disconfirmation and it is the reason 2B exists |
| Phase 0.4 returns *"nobody has asked"* | The ingestion wedge has no buyer. Phase 3 needs a different customer |
| Phase 0.2b shows contractor hours go mostly to **plumbing**, not ontology mapping | Airbyte already solves it. **The venture narrows to the registry alone** — still worth building, much smaller, and the services-substitution business case weakens |
| The interface never changes in Phase 2 | The second consumer was not different enough — N=1 problem survived, and the abstraction is Tenshen's data model with the names filed off |
| Phase 2 slips past Phase 1's estimate by a wide margin | The interface was underspecified. Return to Phase 1, do not build through it |

---

## Standing constraints

0. **No data from the founder's employer is ever used — not to test, not to demo, not to describe in detail.** Not a caution, a hard line. It protects his employment, keeps the venture's evidence base defensible, and removes any characterisation of the work as trading on his access. **Public equivalents exist and are better** (§0.5): reproducible by any reader, which an open-source project's central claims must be. A test that cannot be run on public data is a test this project does not run.
1. **Do not quit to build this.** The current job is simultaneously the research lab, the customer-discovery channel, and the funding source. What burns savings is building for a long stretch before contact with a user.
2. **Do not build the general thing before the specific thing works.** Every scaffold in `VISION.md` §8 — 79 stars, two commits — is someone who started with the framework.
3. **The arrow points from Tenshen to open-ontology as evidence, never the reverse as a dependency** — ~~until Phase 3 works for a real outside user~~ **until Phase 2A passes its contract tests with CMS public data as the primary consumer** (A5, **confirmed by the founder 2026-08-28**: Tenshen will be rebuilt on top of open-ontology). Recorded in the Tenshen spec's §12; that section's three reasons still bind.
4. **Version everything `v0` and say it is unstable.** An interface labelled unstable is cheap to replace; one two codebases quietly assume is permanent is not.
5. **Consume the ETL layer; never rebuild it.** Airbyte, dbt, Airflow and Dagster are mature, open source and self-hostable. The gap is the mapping *above* them, which is small and unowned. Rebuilding beneath is how this becomes a decade-long fight it cannot win.
6. **Tag every claim `[Observed] / [Inferred] / [Assumed]`.** This roadmap's parent document does; a project whose thesis is *provenance and curation* should hold itself to it.
7. **Every spec and design is validated against the three use cases in [`docs/USE-CASES.md`](docs/USE-CASES.md) — Tenshen, CMS citations, NYC Open Data — and survives an adversarial review loop before it is marked done** (founder direction 2026-08-28). A recorded contortion is a pass; a silent accommodation is a failure. Applies from row 3c onward; 3c applies it retroactively to INTERFACE v0 and PACKAGE v0.
8. **Every numbered rule in a spec ships executable** (ruling **R31**, 2026-08-29, [`docs/decisions/2026-08-29-3e-rulings-R27-R31.md`](docs/decisions/2026-08-29-3e-rulings-R27-R31.md)): each numbered rule in a spec section has either a contract id that exercises it or an explicit `prose-only` tag with a reason, and `check_spec_drift.py` fails on a rule with neither. Evidence: 13 of 3e's 21 new ids existed only to pin claims the documents already made; three rows of loops found nothing of substance by reading. Applies from row 4b's landing onward.
