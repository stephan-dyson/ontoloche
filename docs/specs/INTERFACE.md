# INTERFACE — the type-registry contract

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a deprecation path. Standing constraint 4: an interface labelled unstable is cheap to replace; one two codebases quietly assume is permanent is not.
**Status:** Draft, 2026-08-28. Satisfies `ROADMAP.md` Phase 1. Deliverable #1 of the Tenshen-rebuild ordering.
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md), assumption **A1**. If A1 is wrong, this document is wrong in the way §11 describes.
**Evidence inputs:** [`FINDINGS-0.1-tenshen-archaeology.md`](../findings/FINDINGS-0.1-tenshen-archaeology.md) (forced `consumers` and `predicate`) · [`0.5-RESULTS.md`](../findings/0.5-RESULTS.md) (forced model tier and external-doc evidence) · [`0.3-prior-art.md`](../findings/0.3-prior-art.md) (forced the status vocabulary and the refusal to copy `register_*`) · [`WALKTHROUGH.md`](../WALKTHROUGH.md) (the flow this must serve).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## 0. What this is, in three sentences

A registry of **types** — the vocabulary a system uses to say what things *are* — with a proposal→approval loop around every addition, a lifecycle for every entry, and a mechanical answer to *"if I add this, what will silently ignore it?"*

It is not a schema store and it is not a graph. It holds names, definitions, provenance, lifecycle and consumer registrations; **it does not hold instances, edges, storage, or transport.**

**No single call is the centre.** Per A1, the centre is the **proposal→approval loop**: `resolve_type` → `propose_type` → `approve`/`reject`, with `consumers`, `usage`/`retire` and `provenance` all first-class around it.

---

## 1. Non-goals — one line each

- **No storage.** No tables, no SQL, no migrations, no adapter protocol. → deliverable **#2, `docs/specs/PACKAGE.md`**.
- **No HTTP.** No routes, no auth, no pagination-over-the-wire. → **#2**.
- **No package layout.** No module names, no `pip` name, no conformance test suite. → **#2**.
- **No relationships or edges.** No `neighbors()`, no traversal, no edge storage — a *relationship type* can be registered here as a type, but the edges themselves are → deliverable **#4, [`docs/specs/EDGES.md`](EDGES.md)** — **landed 2026-08-29**.
- **No actions.** Action families are registered here as `kind="action"` entries; their shape, their invocations and their gate are → deliverable **#6, [`docs/specs/ACTIONS.md`](ACTIONS.md)** — **landed 2026-08-29**. Tenshen's actions stay in code (beacon spec §10.7) and ACTIONS is written so that they can.
- **No instance resolution.** *"I already know 38 of these facilities"* (`WALKTHROUGH.md` step 2) is **entity** resolution, not **type** resolution. `resolve_type` resolves the word *facility*; it does not resolve `"BURNS NURSING HOME, INC."` against 14,627 CCNs. See §10.3 — this is a named gap, not an oversight.

---

## 2. The data model

### 2.1 `TypeEntry` — one row of the vocabulary

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | `str` | yes | Stable identifier. Unique within `(namespace, kind)`. `^[a-z][a-z0-9_]{0,63}$` |
| `kind` | `str` | yes | Open vocabulary. v0 defines four: `entity`, `predicate`, `edge`, `value_set`. See §2.2 |
| `namespace` | `str` | yes | Defaults to `"default"`. The answer to mechanism 4 that is **not** merging. See §2.6 |
| `definition` | `str` | yes | Prose, non-empty. What this word means *here*. Rejected if empty — a type without a definition is how collision starts |
| `created_by` | `"seed" \| "ai" \| "user" \| "derived"` | yes | Where the vocabulary came from. Field name and the **first three** values taken deliberately from Tenshen's `work_link_types` (§9). `derived` added by ruling **R17**, row 3e — see below |
| `provenance` | `Provenance` | yes | §2.4 |
| `status` | `"proposed" \| "active" \| "retired"` | yes | §2.5 |
| `usage` | `UsageReport` | yes | §5.7 — may be entirely unknown, never fabricated |
| `consumers` | `ConsumerReport` | yes | §5.1 — **always** carries `complete: false` in v0 |
| `predicates` | `list[str]` | yes | Names of `kind="predicate"` entries this type satisfies. May be empty |
| `attributes` | `dict[str, Any]` | yes | Kind-specific payload, **opaque to v0**. Defaults `{}`. The escape hatch that keeps v0 from pretending to know what an edge needs |
| `aliases` | `list[str]` | no | Prior names, and identifiers imported from elsewhere (a Foundry `apiName`/`rid` lands here or in `provenance.imported_from`, per 0.3 consequence 3) |
| `warnings` | `list[str]` | yes | Defaults `[]`. The values of §5.4's table (thirty-three, and the table is held against `types.WARNING_VALUES` by [`check_spec_drift.py`](../tools/check_spec_drift.py) so this sentence cannot go stale again); two of them (`name_previously_retired`, `retired_without_usage_evidence`) reach a caller **only** here. *(Added by row 3c — implemented at 2A as deviation D-3 and described by §5.4, §5.5 and §5.9, but never listed in this table)* |
| `attr_schema_version` | `int \| None` | yes | The attribute schema in force **when this entry was written** — `None` means it was written with validation off. Owned by `PACKAGE.md` §5.4, which is why it is opaque here: v0 never reads it, and it is carried so a reader can tell *which generation* of `attributes` they are looking at without the registry pretending to interpret them. §5.4 there: entries written under an older schema are never rewritten and never retroactively invalidated. *(Added by row 3c after a sixth adversarial review round — it is populated on every `TypeEntry` the registry returns and appeared in neither this table nor the deviation ledger)* |

**`derived` — the fourth `created_by`, and the first change to this vocabulary** *(ruling **R17**, row 3e, 2026-08-29)*. `derived` means **produced by a deterministic rule, with no human and no model in the loop**. The registry reads it off the actor, the way it already reads `ai:` and `seed:`: an actor of `derived:<rule>` lands `created_by="derived"`.

**Two unrelated fixtures reached for the same missing value**, which is why this is the only one of [`EDGES.md`](EDGES.md) §14's vocabulary questions that was taken:

- **[Observed, beacon spec]** `EntityMention.match` carries exactly the three-way distinction this field needs and does not have — *derived by a rule* / *inferred by a model* / *asserted by a person* — and its first value is literally `deterministic`.
- **[Observed, UC3]** the BBL join that relates a tree to a service request is a deterministic rule over a shared key. Before R17 it had to claim `created_by="user"`, which says a person decided something no person touched, or hide the truth in a `created_by_actor` string convention that nothing validates.

**The vocabulary is closed and the suite now holds it to that** *(row 3e, second adversarial round)*. `Refusal.reason`, `Evidence.kind`, `Consumer.on_unknown` and `NotAType.reason` all raise on an unknown value; `created_by` did not, and no invariant checked it, so a third-party backend's garbage flowed straight out to a caller through `list_types`. `C16-05` asserts that every returned `created_by` is one of these four and every `status` one of §2.5's three. `kind` is deliberately **not** checked: §2.2 says it is an **open** vocabulary.

**`import:` still maps to `seed`, on purpose.** An import is a vocabulary arriving from elsewhere *already decided* (§2.5) — the decision was made by whoever ran the source system — where `derived` is a decision this system's rule made just now. Collapsing them would lose which of those two happened, which is the distinction the value exists for. Counted in [`EDGES.md`](EDGES.md) §9.2 T1.5b as one of six `created_by`-shaped vocabularies in the two codebases, none of which agreed.

**What a REFERENCE to one of these rows means after a merge** *(ruling **R38**, row 4c; founder-visible)*. `merge_types` and `retire(successor=)` both retire one word naming another as its successor (§5.10, §5.9), and **nothing in this registry rewrites a reference that was already written**. So a stored reference to `assignee` keeps saying `assignee` after `assignee` is merged into `owner` — and the question *"whose row is this reference about now?"* has an answer this document had only ever given for one call.

> **A reference to a type resolves to the identity that type now belongs to.** `resolve_type` has done this since row 3c and §5.3 calls the confidence-1.0 redirect a **guarantee**; [`EDGES.md`](EDGES.md) §4.3's `neighbors` did not, and resolved to the reference as written. One identity model per call is a defect rather than a choice, and R38 rules it here for both documents.

**Two things follow, and the second is why this is a rule and not an implementation note.** A caller must still be able to read *what was written* — so the written reference is never edited and never hidden, and any surface that follows a chain says which edges it reached that way ([`EDGES.md`](EDGES.md)'s `NeighborEdge.via_successor`, Rule K). And a surface that **cannot** finish resolving a chain — a cycle, a length cap, a backend that cannot read its retired rows — says so rather than answering as if it had: Rule U, on the resolution itself.

**Why it matters beyond edges:** this is what makes `merge_types` safe on a store that has anything pointing at its vocabulary. Without it, the sanctioned answer to mechanism 4 silently orphans every reference written against the word it absorbed, and the caller who does the correct thing — resolve to the canonical type, then look — gets the emptiest possible true-looking answer.

**Why `attributes` is deliberately dumb.** Tenshen's relationship types carry `is_symmetric` and `inverse_label`; CMS's value sets carry an ordering. Neither belongs in a v0 type registry, and inventing homes for both would be designing #4 and #2 here. They go in `attributes` and the registry never reads them. **Recorded as a known weakness, not a solved problem** — `attributes` is where an unversioned schema will accumulate if nobody watches it.

### 2.2 The four kinds, and why `predicate` is not just another kind

- **`entity`** — a thing that exists. `facility`, `survey`, `citation`, `person`.
- **`predicate`** — *a named capability set.* `commentable`, `searchable`, `linkable`, `shareable`. Its members are the types that satisfy it.
- **`edge`** — a relationship type. Registered here (name, definition, provenance, lifecycle); its shape and its instances live in **#4**.
- **`value_set`** — an enumerated set of *property values* with optional ordering. `deficiency_corrected_status`, `scope_severity_code`. **Added because the CMS data forced it** — see §10.1, the first recorded CMS-vs-Tenshen conflict.

### 2.3 `predicate` is first-class, and it is not the type list — read this before implementing anything

**[Observed], finding 0.1:** five of Tenshen's seven "disagreeing vocabularies" were not vocabularies. `CLOSED_ENTITY_TYPES` carries its own comment — *"The two entity types that resolve to a page a user can read back."* That is not a claim about what a thing **is**. It is a claim about **which types support one capability**.

A registry that cannot hold that distinction will see five overlapping lists, call them duplicates, merge them, and thereby assert that anything commentable is searchable. **That assertion is false, and making it is the kill-criterion row in `ROADMAP.md` ("A capability predicate gets merged as a duplicate").**

So:

- A predicate is a `TypeEntry` with `kind="predicate"`. It has a name, a definition, provenance and a lifecycle like anything else.
- **Membership lives on the member**, in `TypeEntry.predicates`. The predicate's *extent* is derived: `list_types(predicate="commentable")`.
- A predicate is **not** a supertype, **not** an interface, and **not** a parent in a hierarchy. `commentable` does not mean "a kind of thing"; it means "this code path will accept it".
- **`merge_types` refuses predicate merges outright** unless the two extents are byte-identical **and non-empty** (§5.10). *(The second clause was added by row #6's second adversarial round, which merged two live predicates through the shipped registry because `set() == set()`.)*

**The structural result that ties 0.1's Cause A to its Cause C:**

> A predicate's extent and a consumer's allowlist are **the same shape**. `comment_service.ENTITY_TYPES = {task, project}` is simultaneously the predicate *commentable* and the allowlist that silently dropped `capture`. Registering it once answers both `predicates()` and `consumers()`.

**[Inferred]** That is why both calls arrived from one finding, and it is the single most load-bearing idea in this document. If an implementation stores predicates and consumers as two unrelated tables, it has missed the point.

### 2.4 `Provenance` — who, when, on what evidence

```
Provenance:
    created_at:        datetime
    created_by_actor:  str            # "user:sd", "ai:classifier", "seed", "import:foundry"
    proposed_by:       str | None
    approved_by:       str | None     # "auto:<policy>" when no human approved — never blank-implying-human
    approved_at:       datetime | None
    model_tier:        str | None     # §2.7 — the tier that produced the proposal
    evidence:          list[Evidence]
    imported_from:     dict | None    # opaque foreign identifiers: {"system": "foundry", "apiName": ..., "rid": ...}
    source_version:    str | None     # the SOURCE's own version — never ours. R21, §2.4a
    history:           list[ProvenanceEvent]   # append-only; nothing here is ever rewritten
    history_why:       str | None     # why `history` is empty, when it is. Rule U:
                                      #   an empty history must not read as "nothing
                                      #   happened" on a backend that cannot store events
```

*(`history_why` added to this shape by row 3c. It was implemented at 2A as deviation D-4 — `PACKAGE.md` §3.4 primitive 15 requires an empty `history` to carry a `why` — and §11 recorded it, but the shape above never gained the field.)*

#### 2.4a `source_version` — the source's own version, never ours *(ruling **R21**, row 3e, 2026-08-29)*

Everything else in `Provenance` is a fact about **us**: when we created the entry, who proposed it, when we approved it, when we fetched a citation. `source_version` is the one field that is a fact about the **thing the entry was derived from**, and it is `None` unless a caller supplies one.

**The finding is §10b.5, contortion 12.** A UC3 type is derived from a dataset carrying its own `data_updated_at` — **[Observed]** 2017-10-04 for one agency, 2026-08-28 for another, 2026-08-24 for a third — and *a type proposed from a 2017 snapshot of a "Historical data" dataset is a different claim from one proposed off a daily feed.* None of the ten fields had a home for it: `Evidence.locator` takes the resource URL, `Citation.retrieved_at` takes **our** fetch time, and `imported_from` is documented as foreign **system** identifiers (a Foundry `apiName`/`rid`). Using `imported_from` for a dataset version is the stretch §10b.5 declined to make, and the field was left `None`.

**What actually forced it now** is not that finding on its own — it was collected for v1 like the rest — but that [`EDGES.md`](EDGES.md) §5.3 gave `EdgeProvenance` the field first, because a cross-agency edge is *entirely* a claim about two source snapshots. That left **two shapes for one concept with one of them missing the field**, which is precisely the drift [`check_spec_drift.py`](../tools/check_spec_drift.py) exists to catch, pointing inward. [`EDGES.md`](EDGES.md) §14 Q16; ruled **R21**.

**Where it comes from.** `propose_type(..., source_version=…)` carries it on the `Proposal`, and `approve` writes it into the `Provenance` — so it is supplied once, by the proposer who knows what they read, and is never invented by the registry. `import_types` reads a `source_version` key off the imported row. **Opaque to v0**: a string, never parsed, never compared, never ordered — the same posture as `model_tier` (§2.7), and for the same reason.

**Rule:** `approved_by` is never null on an `active` type. If nothing human approved it, the value is `"auto:<policy-name>"`. **A registry that leaves the field blank invites a reader to assume a human signed off** — that is the rubber-stamping failure `WALKTHROUGH.md` names, arriving through the data model rather than through the UI.

### 2.5 `status` — and how it reads a Foundry dump

`proposed` → awaiting a decision, not yet usable. `active` → in the vocabulary. `retired` → was in the vocabulary, is not now, and the name is **not** reusable.

Per **0.3 consequence 2**, the migration mapping from Foundry's `status ∈ {active, experimental, deprecated}` is stated here, not left to an importer:

| Foundry | Ours | Why |
|---|---|---|
| `active` | `active` | direct |
| `deprecated` | `retired`, with `retire_reason: "imported: foundry deprecated"` | direct |
| `experimental` | **`active`, plus predicate `experimental`** | **Not `proposed`.** `proposed` here means *no one has approved it*; a Foundry `experimental` type has been approved and is in use. Collapsing them would silently un-approve a customer's live vocabulary |

`visibility` and `groups` from Foundry land in `attributes`; `apiName` and `rid` land in `provenance.imported_from`.

### 2.6 `namespace` — present, unused, and deliberately so

**[Assumed], A1:** semantic collision is present but not dominant. So `namespace` exists, defaults to `"default"`, and **v0 requires nobody to use it.** It is here for one reason: when two teams turn out to mean different things by one word, the answer must be *scoping*, and it must **not** be `merge_types`. Having the field costs nothing; not having it means the only available move is the destructive one.

**[Observed], 0.1 Cause B:** `view_query_spec` means *subject noun* by "entity" and `comment_service` means *task-or-project* — one line apart, one codebase, no teams. So the field earns its place even under A1.

### 2.7 Model tier is a parameter, not an implementation detail

**[Observed], 0.5 consequence 2.** Four agents, four tiers, on the same CMS slice. Structure correct 4/4. **The cheapest tier inverted the CMS scope-and-severity scale** — reported "higher letters appear less serious" when J/K/L are Immediate Jeopardy — while every number it produced stayed correct. Nothing errored. The user could not have detected it from the output.

Therefore:

1. `resolve_type` and `propose_type` **take** `tier: str`.
2. The tier is **recorded** in `Provenance.model_tier` and is never overwritten.
3. `approve(..., mode="auto")` **refuses** when `provenance.model_tier` is below the namespace's `min_auto_approve_tier` policy, returning `Refusal(reason="tier_below_auto_approve_policy")`.
4. `usage`/`provenance` reporting can therefore answer *"which of our types were proposed by a cheap model and never seen by a human?"* — the query the 0.5 result makes necessary.

**v0 does not define the tier vocabulary or the ordering.** It defines the *slot*, requires the value to be an opaque string, and requires the policy comparison to be supplied by the deployment. **[Assumed]** that a total order over tiers exists per deployment; this is untested and may be wrong for mixed vendors.

### 2.8 `Evidence` — and the external-documentation citation slot

**[Observed], 0.5 consequence 3:** the severity inversion was caught by reading CMS documentation, **not** by inspecting data. A tool that maps domain data and never consults domain documentation reproduces that failure class for every user.

```
Evidence:
    kind:      "data" | "external_doc" | "human" | "code"
    summary:   str                    # what this evidence shows, in one sentence
    citation:  Citation | None        # required when kind == "external_doc"
    locator:   str | None             # file+line, column name, row range — where to look again

Citation:
    url:          str
    title:        str
    retrieved_at: datetime
    quote:        str | None          # the sentence relied on, verbatim
    publisher:    str | None
```

**The rule that makes this bite:** a proposal whose `definition` asserts a **domain semantic** — an ordering, a severity scale, a regulatory meaning, a threshold — **should** carry at least one `kind="external_doc"` item. When it does not, `approve()` still succeeds but returns `warnings: ["unverified_semantics"]`, and the type carries `provenance.evidence == []`, which `list_types(unverified_semantics=True)` can enumerate later.

**v0 does not attempt to detect automatically whether a definition asserts a domain semantic.** That is a model judgement and belongs to the proposer. **[Assumed]** that proposers will flag it honestly; §11 lists what would change this.

> **Recorded by deliverable #3, 2026-08-28 — this sentence and §10's worked example disagree.** §10 shows `propose_type(...)` producing `p.warnings == ["no_evidence", "unverified_semantics"]` from a call that carries no such flag, and `PACKAGE.md` test `C4-06` asserts the detection half of it. *(Corrected by row 3c, 2026-08-28: `C4-06` passes **non-empty** evidence and asserts `unverified_semantics` present with `no_evidence` **absent** — "there IS evidence; it is just not a citation". The combination §10 prints comes from `C4-05` plus `C4-06`, not from `C4-06` alone. The tension this box records is unaffected; the citation was wrong and would have misled anyone checking it against the suite.)* A flag-only design cannot satisfy §10; a detection-only design contradicts this sentence. Phase 2A implements a **conservative keyword rule** that deliberately over-warns — a spurious `unverified_semantics` costs one enumerable entry, a missed one is the 0.5 severity inversion going unlabelled. If this sentence is meant literally, the fix is an explicit proposer-supplied flag on `propose_type`, which is a change to §5.4. See [`2A-RUN.md`](../runs/2A-RUN.md) §4.5, deviation D-6.

### 2.9 `Consumer` — a registered code path that gates on a predicate

```
Consumer:
    id:          str         # "aura_render.referent_link", "comment_service.can_comment"
    gate:        str         # the predicate name it gates on
    on_unknown:  "drop" | "error" | "passthrough"
    owner:       str | None
    registered_at: datetime
    locator:     str | None  # file:line, so a human can go look
    warnings:    list[str]   # on the one `register_consumer` returns; empty in a report
```

`on_unknown="drop"` is the dangerous value and it is the **[Observed]** default behaviour of every one of Tenshen's seven allowlists. It is what makes a new type die silently.

---

## 3. Two global rules that apply to every call

**Rule U — uncertainty is a value, never a default.** No call returns a confident answer in place of an unknown one. Unknown is `None` plus a `why: str`. Never `False`, never `0`, never an empty list standing in for "we did not look".

**Rule K — every list result carries `complete: bool` and a `known: int | None`.** Per `WALKTHROUGH.md`'s risk row: *"Only claim consumers the registry can enumerate mechanically. Never infer one. Show '3 known, may be others' rather than '3'."* In v0, `ConsumerReport.complete` is **always `false`** — see §5.1.

**Every** means every. *(Amended by roadmap row 3c, 2026-08-28, after an adversarial review round found the rule stated globally and applied selectively.)* Rule K binds four shapes, and two of them acquired it in this amendment:

| List result | Carrier | `complete` |
|---|---|---|
| `ConsumerReport.gates_on`/`would_drop`/`would_error` | §5.1 | **always `false`** |
| `TypeListing.types` | §5.6 | `false` whenever a filter suppressed rows |
| **`Resolution.alternatives`** | §5.3 | `false` **unless the caller named every namespace that has a type in it** — §5.3.1, ruling R6 |
| **`predicates()`'s return** | §5.2 | `false` whenever a filter suppressed rows — new |

**`known` is `int | None`, and Rule U is why** *(corrected by row 3c, 2026-08-28, after a second adversarial review round; the rule read `known: int` from the first draft and two of the four shapes never matched it)*. A backend that cannot count is entitled to say so: `TypeListing.known` and `PredicateListing.known` are `int | None`, and `None` means *we did not count*, which is the honest answer Rule U requires and which `0` would falsify. `ConsumerReport.known` and `Resolution.known` are plain `int` because both are lengths of lists this document has already materialised — there is nothing there to fail to count. **Where the two rules meet, Rule U wins**, and a caller must treat `known` as nullable on any listing.

**Why `Resolution` needed it, and why it is the sharpest case in the document.** §10b.1 records that `resolve_type` scores only inside the namespace it was asked in. Before this amendment, the second publisher of a word got `alternatives: []` — **an empty list standing in for "we did not look", which is the one thing Rule U forbids by name.** The caller had no field with which to even ask whether the search had been scoped. It carries `complete` and a `why_incomplete` naming what was not searched. **Row 3c made it `false` unconditionally, which stopped contortion 8 being *silent* without fixing it; row 3e's ruling R6 fixed it** — `search_namespaces` (§5.3.1) lets a caller search the others, and `complete` becomes `true` in the one case where it is honest: every namespace that has a type in it was named.

> **Keep the distinction the two rows make.** A `false` here is *"we did not look everywhere, and here is where we did not look"* — a gap, reported. A `true` is a positive claim this surface did not make before ruling R6, and §5.3.1's rules 6-8 exist to keep it from ever being made loosely: an unnamed namespace, a page the backend truncated, or a backend that cannot enumerate the store all force it back to `false` with a `why` naming which of the three happened. **`ConsumerReport.complete` is untouched and is still always `false`** (§5.1) — nothing about R6 makes consumers discoverable.

---

## 4. Mechanism labels used throughout

From `ROADMAP.md` Phase 0's table, plus the fifth that finding 0.1 added:

| Label | Mechanism |
|---|---|
| **1** | Anyone could add a type, **no review** |
| **2** | **Nobody could find** the existing types |
| **3** | Types added once, **never retired** |
| **4** | Teams meant different things by one word — **semantic collision** |
| **C** | A producer emits a type; each consumer gates on its own private allowlist; the feature dies **silently** in the consumer that was not updated — **silent per-consumer drop** (0.1 Cause C; absent from the original table) |

---

## 5. The calls

Signatures are Python-shaped because deliverable #2 is a Python package. They are **not** a module layout.

---

### 5.1 `consumers` — who gates on this type, and who would silently drop it

```python
def consumers(
    type: str,
    *,
    namespace: str = "default",
    include_would_drop: bool = True,
) -> ConsumerReport: ...
```

```
ConsumerReport:
    type:        str
    gates_on:    list[Consumer]      # consumers whose gate predicate INCLUDES this type
    would_drop:  list[Consumer]      # gate EXCLUDES it AND on_unknown == "drop"
    would_error: list[Consumer]      # gate excludes it AND on_unknown == "error"
    known:       int                 # len(gates_on) + len(would_drop) + len(would_error)
    complete:    bool                # ALWAYS False in v0
    why_incomplete: str              # "consumers are registered, not discovered; unregistered code paths are invisible"
    warnings:    list[str]           # "gate_unregistered:<gate>" — see below. Ruling R8
```

**Designed against: mechanism C.** This is the call that would have prevented the only documented Tenshen incident — `capture` began being emitted, `aura_render` gated on a list that excluded it, `on_unknown` was effectively `drop`, and the feature was dead for exactly the watch kind that had just started working.

**Behaviour when uncertain.** `complete` is **always `false` in v0**, unconditionally, even when every consumer in a system is registered — because the registry cannot know that it is. A caller rendering `WALKTHROUGH.md` step 5 must therefore print *"3 known, there may be others"* and has no way to print *"3"*. **This is deliberate friction.** An impact list that misses a consumer is more dangerous than no list, because it promises safety it cannot deliver.

**Two ways a consumer gates, and v0 computed one** *(corrected by row 3c, 2026-08-29, after an adversarial review round)*. For an `entity`, a consumer gates on it when the consumer's `gate` predicate **includes** it. **For a `kind="predicate"` entry, a consumer gates on it when the `gate` IS it** — and a predicate is essentially never a member of itself, so the membership test alone never matched. **[Observed]**, on a fully capable backend with nothing unknowable: `consumers("commentable")` returned `gates_on: []` and filed the consumer of `commentable` under **`would_drop`** — the exact opposite of the truth — and `retire("commentable")` then succeeded with no refusal. `predicates()` had the right query all along; this call did not, and §5.9 guards retirement with `consumers` and carves out no exception for predicates. That is mechanism **C** inside §2.3's *"single most load-bearing idea in this document"*. `C1-09`.

**A gate nobody registered is warned about, not hidden and not refused** *(ruling **R8**, row 3d — routed here from the UC3 walk-through)*. A consumer's `gate` **may** name a predicate that does not exist; `register_consumer` accepts it deliberately, because a consumer gating on a word nobody registered **is** mechanism **C**, and refusing the registration would hide the very thing this call exists to surface (`C11-02`).

But the report then says `would_drop: [aura_render.referent_link]` about that consumer, and a reader takes that as a fact about a live gate: *this consumer gates on `commentable`, and this type is not in `commentable`'s extent.* The truth is weaker and worse. **There is no `commentable`.** The extent is not "excludes this type" — it is undefined, and *every* type in the namespace would drop, not just this one. One line of the report, two very different situations.

So the report carries `warnings: ["gate_unregistered:commentable"]` — the same `<name>:<subject>` shape as `attributes_invalid:<field>`. `would_drop` still lists the consumer, unchanged: dropping it would delete mechanism-C visibility, which is `C11-02`'s subject.

Two things this deliberately is **not**:

- it is **not** `gate_values` (ruling R8's option 1, deferred to Phase 3): letting a gate name a *value* would make the registry know what a value is, which §2.1 refuses on purpose. That refusal is a product boundary and it moves by decision, not by drift.
- it is **not** a refusal, and it is not a rule about *retired* predicates. A retired predicate is a **registered** entry — the tombstone is there and `resolve_type` reads it (`C3-10`) — so it raises no warning. Only a gate with no entry at all does.

**Rule U applies to the warning too.** "This gate is unregistered" is a positive claim about an absence, and the registry only makes it when the lookup came back `complete`. On a backend whose page is incomplete, no warning is emitted — the report does not guess in either direction. `C11-05`.

**Unknown type:** raises `UnknownType`, never returns an empty report — an empty report reads as *"nothing gates on this"*, which is the exact false reassurance this call exists to prevent.

---

### 5.2 `predicates` — the named capability sets

```python
def predicates(
    *,
    of: str | None = None,          # if given, only predicates this type satisfies
    namespace: str = "default",
    include_retired: bool = False,
) -> PredicateListing: ...
```

```
PredicateListing:                # Rule K. Added by row 3c, 2026-08-28
    predicates:     list[PredicateEntry]
    known:          int | None   # None = the backend cannot count. NOT 0
    complete:       bool         # false whenever a filter suppressed rows
    why_incomplete: str | None
```

**Why it is not a bare list.** `include_retired=False` is the default *and hides things*, and a backend that could not fully answer the underlying page had that swallowed. A bare list of one predicate reads as *"there is one predicate"*; it may mean *"there is one we are willing to show you"*. That is §5.2's own `extent_size` failure — an empty answer reading as a confident zero — one level up, and Rule K already had the answer.

```
PredicateEntry:
    name:        str
    definition:  str
    extent:      list[str]       # type names satisfying it — DERIVED, never stored twice
    extent_size: int | None      # None = the extent could not be computed. NEVER 0
    consumers:   list[Consumer]  # consumers gating on this predicate
    status:      "proposed" | "active" | "retired"
    provenance:  Provenance
    why_extent_incomplete: str | None    # the `why` the paragraph below requires
```

*(`extent_size` and `why_extent_incomplete` corrected by row 3c, 2026-08-28, after a fourth adversarial review round. The table typed `extent_size: int` while the paragraph below it required `None`, and declared no home for the `why` — **Rule U's marquee example contradicting its own data shape**, three lines apart. An implementer coding from the table would have coerced the unknown to `0`, which is the exact "nothing is commentable" false reading the paragraph forbids. `types.py` and `PACKAGE.md` `C2-02` both had it right.)*

**Designed against: mechanism 4, defensively — and the kill-criterion row.** Predicates are the structure that stops five locally-correct lists from being read as five duplicates.

**Behaviour when uncertain.** If a predicate's extent cannot be computed (a backend that cannot index membership), return `extent: []` **with `extent_size: None`** and a `why` — never `extent_size: 0`, which reads as *"nothing is commentable"*.

**`extent` and `of=` resolve the IDENTITY, not the written word** *(ruling **R54**, row 4d, 2026-08-30)*. A predicate absorbed by a merge and its survivor are one identity, so the survivor's `extent` holds every type that declared **either** word and `predicates(of=type)` finds the predicate whichever of its names that type happened to declare. It used to do neither: a type declaring the absorbed word was compared by written string against a page holding only the survivor's name, so `predicates(of=it)` answered **`known=0`** — *"this type satisfies no predicates"* about a member the registry can see, which is **this section's own named failure mode, in this section's own call**. A closure that could not be followed to the end returns `extent_size: None` with the closure's `why`, never a count over an unfinished question. `C2-06`.

> **The identity guards deliberately do NOT ask this question, and the reason is circularity rather than cost.** Every guard in §5.10 compares two extents to decide whether collapsing two words asserts something false. If that comparison resolved identities, the merge under examination would be exactly what joined the two names — so the two closures would be equal **by construction**, the guard would agree with itself and refuse nothing, and `ROADMAP.md`'s kill row would reopen through the fix meant to close a different hole. The guards ask whether two words denote the same set **of their own accord**; this call asks what satisfies a capability. `check_merge_guard.py`'s **stale** axis is the mechanical form of that distinction, and it is why ruling R54 was sequenced behind it: `_extent` is the expression all six kill-row trips run through.


#### 5.2.1 The identity reading — rules *(ruling **R54**, row 4d)*

Standing constraint 8 / ruling **R31**: every numbered rule ships with a contract id that exercises it or a `prose-only:` tag with a reason. **This table enumerates the rules row 4d added to §5.2 and no others** — the rest of the section predates the constraint and is not claimed here, which is the honest form of a coverage claim rather than a gap somebody has to notice.

| rule | what it says | exercised by |
|---|---|---|
| 5.2.1-1 | A predicate's `extent` holds every type that declared **any word the identity spans**, deduplicated — a type that declared both the absorbed word and the survivor is one member, not two | `C2-06` |
| 5.2.1-2 | `of=` matches through the **member's** identity: a type that declared an absorbed word satisfies the survivor, and `known` counts it. Answering `known=0` there is this section's own failure mode | `C2-06` |
| 5.2.1-3 | A closure that could not be followed to the end returns `extent_size: None` with the closure's own `why` — **never a count over an unfinished question.** Rule U, one level above the extent page it already applied to | `C2-06` |
| 5.2.1-4 | The identity guards of §5.10 keep the **written-word** reading. Resolving identities there would make the merge under examination its own justification, and the two closures equal by construction | `C10-13`, `C10-14` — *and not `C10-09`, which row 4d's third round proved by mutation still passes when the default is flipped; `C10-09`'s subject is the narrowing, not the reading* |

### 5.3 `resolve_type` — existing, proposal, none… or not a type at all

```python
def resolve_type(
    candidate: str,
    context: ResolveContext,
    *,
    kind: str | None = None,
    namespace: str = "default",
    tier: str,                       # §2.7 — REQUIRED, not defaulted
    min_confidence: float = 0.0,
    search_namespaces: Sequence[str] | None = None,   # ruling R6, row 3e. None = v0
) -> Resolution: ...
```

```
ResolveContext:
    definition_hint:  str | None      # what the caller thinks it means
    sample_values:    list[Any]       # up to N observed instances
    source:           str | None      # "NH_HealthCitations_Aug2026.csv#Location"
    sibling_columns:  list[str]       # what else arrived with it — carries most of the signal
    proposed_by:      str | None

Resolution:
    outcome:     "existing" | "proposal" | "not_a_type" | "none"
    type:        TypeEntry | None     # when "existing"
    proposal:    Proposal | None      # when "proposal"
    confidence:  float | None         # None means "did not score", NOT zero
    reason:      str
    alternatives: list[tuple[str, float]]   # near misses, so a human can overrule
    tier:        str                  # echoed back; goes into provenance
    scoped_to:     str                # the namespace the OUTCOME was decided in
    known:         int                # len(alternatives). Rule K
    complete:      bool               # Rule K. False unless every namespace that
                                      #   exists was named — see R6 below
    why_incomplete: str               # names what was not searched. "" when complete
    searched_namespaces: tuple[str, ...]   # every namespace actually scored, scoped_to
                                      #   included. Empty = the v0 default, one namespace
```

**`complete` was always `false`, for the same reason §5.1's is** *(added by row 3c, 2026-08-28)*. The near misses are scored inside one namespace and nothing searched the others (§10b.1). So an empty `alternatives` **never** means *"there is nothing like this anywhere"* — it means *"nothing like this in the namespace you asked in, and we did not look outside it"*, and the caller can read that off the result instead of having to know it.

### 5.3.1 `search_namespaces` — the cross-namespace lookup *(ruling **R6**, row 3e, 2026-08-29)*

**The finding this closes** is §10b.1, contortion 8, and it is the sharpest result the UC3 pass produced: [`3C-VALIDATION.md`](../findings/3C-VALIDATION.md) W1.3. The Department of Parks registers `status`; the 311 team asks for `status` in its own namespace and is told *"nothing in the vocabulary fits `status`"* with an empty `alternatives`, while the **same context** asked in `dpr` returns `existing` at confidence `1.0`. **The answer was decided by which namespace the caller picked before asking.** §2.6 makes `namespace` the answer to **mechanism 4**; scoping without a cross-namespace *lookup* makes every publisher re-propose every word and leaves the registry unable to say so, which is **mechanism 2 reintroduced by the answer to mechanism 4**, in the call §5.3 says is designed against mechanism 2.

**The rules, in full:**

1. **`None` is the v0 behaviour, exactly.** No namespace is enumerated, nothing extra is read, `searched_namespaces` is empty and `complete` is `false` with the sentence above. **No v0 caller changes**, and no v0 caller pays for R6.
2. **`namespace` is always searched**, whether or not the caller lists it, and it is first in `searched_namespaces`. The caller is standing in it.
3. **Hits from another namespace land in `alternatives` as `("<namespace>:<name>", score)`.** Hits from the caller's own namespace keep their bare `name`, unchanged.
4. **The outcome is still decided inside `namespace` alone.** A hit elsewhere **never** makes the outcome `existing`. Resolving across namespaces would be §2.6's answer to mechanism 4 deleting itself — two agencies meaning different things by one word is what scoping exists to *preserve*. What the hit does is put the fact in `reason` and in `alternatives`, which is what the second publisher was never told.
5. **An exact name match in another namespace is guaranteed by the registry, not by the resolver, and the probe is kind-blind.** If the name exists there it is listed, with the resolver's score when the resolver produced one and `None` when it did not — `None`, never `0.0`, because nothing scored it (Rule U). This is the same move §5.3 already makes for a live successor and for a retired name, and it is here for the same reason: [Observed, row 3c] a promise kept only because the shipped scorer happens to rate an exact name `1.0` is a promise a deployment supplying its own resolver (`PACKAGE.md` §2.6's **production path**) does not get.

   > **`kind=` narrows the scoring and must not hide the collision** *(corrected after row 3e's first adversarial round)*. The first cut passed the caller's `kind=` into the cross-namespace probe. **[Observed]** with DPR publishing `status` as a `value_set` and the 311 team asking for `status` as an `entity` — UC3's collision shape exactly — the taken word vanished, `alternatives` came back empty, and the answer was sealed `complete=true`: contortion 8's own sentence, now asserted as a *whole* search, which is worse than the behaviour R6 replaced. Uniqueness is per `(namespace, kind)` (§2.1), so an entry under another kind is not the same **entry** — but it is the same **word**, and the word is what R6 owes the caller. One name held under two kinds in one namespace is listed **once**, with the ambiguity named in `reason`, because listing it twice would double-count Rule K's `known` for a single taken word. `C3-12`.
6. **`complete` is `true` only when the caller named every namespace that has a type in it** — retired types included, because a namespace whose every word is retired is still a namespace somebody published into. Otherwise `why_incomplete` **names the ones left out**, by name. *"We searched four of the six"* without saying which two is the confident partial answer Rule U forbids, which is what the empty `alternatives` of contortion 8 already was.

   > **A word RETIRED in a searched namespace is listed, not discarded** *(added after row 3e's second adversarial round)*. The first cut read retired rows to decide *which namespaces exist* and then threw the records away, so **[Observed]** a name burned in a namespace the caller had named came back with empty `alternatives` under a `complete=true` seal — while the **identical** tombstone in the caller's own namespace is surfaced loudly, in `reason` and in `alternatives` with a `None` score, precisely because §5.3 calls discarding it *"Rule U's confident negative, in the call designed against mechanism 2"*. It is now listed the same way both sides of the namespace boundary, with its `retire_reason` and `successor` in `reason`. In UC3, one agency retiring `status` is exactly the *we already decided about this word* signal the second publisher needs.
7. **`complete=true` requires `searched_namespaces`**, and constructing a resolution that claims one without the other raises. Same rule as ruling **R12**'s coverage line and [`EDGES.md`](EDGES.md)'s `families_searched`: *a completeness claim without its scope line is not a claim.*
8. **A page the backend could not fully answer cannot support the claim either.** `TypePage` carries `complete`/`why_incomplete` precisely so a backend may cap an unlimited query and say so (`PACKAGE.md` §3.3); if it does, `complete` is `false` and `why_incomplete` carries the backend's own reason. This is reported **distinctly** from rule 6's omission, because an unnamed namespace and a truncated page are different facts and a caller acts on them differently. *(Added after row 3e's first adversarial round: the first cut read the records off the page and ignored the flag — harmless while `complete` was hard-wired `false`, not harmless once it became a claim. `Registry._extent` had honoured the same flag since v0.)* `C3-13`.

8b. **`alternatives` is fed from TWO stores, and both of them gate the claim.** §5.5's prior rejections come from the **proposal** store, and are searched in every namespace the caller named — a word proposed and rejected elsewhere is the cheapest possible record of *we already decided against this*, which is why §5.5 surfaces it at home. When the proposal store cannot answer — `stores_proposals=false`, or a page it declares partial — `complete` is `false` with a `why_incomplete` saying which. *(Added after row 3e's **second** adversarial round, and it is a defect this row's own round-1 fix left behind: rule 8 was written for `find_types` and not applied to `find_proposals`. **[Observed]** on `sqlite_minimal` — a reference leg, and **UC1 Tenshen's own declared shape** — one `Resolution` carried `complete=true` and `why_incomplete=""` while its adjacent `reason` field said prior rejections had been omitted from the very list it had just called whole. Worse, `C3-12` asserted `complete is True` on that leg, so **the suite required the wrong answer**.)* `C3-12`, `C3-13`.

8c. **`alternatives` carries at most five SCORED near misses per namespace, and the cap gates the claim.** It has done so since v0, where it was invisible because `complete` was hard-wired `false`; ruling R6 made `complete` reachable and turned it into a silent truncation underneath a positive claim. **[Observed, row 3e third adversarial round]** ten types tied at one score, five dropped, `complete=true`, `why_incomplete=""`. When the cap bites, `complete` is `false` and `why_incomplete` names the namespaces it bit in. **The registry's own guarantees are never subject to it** — an exact name match elsewhere (rule 5), a tombstone (rule 6), a prior rejection (rule 8b) are listed whatever the cap does, because they are facts the registry holds rather than scores a resolver produced. Consequence, stated plainly: in a namespace with more than five active types `complete` will usually be `false`, and that is the honest answer rather than a defect — R6's value is the cross-namespace hits and the named reason, not the flag.

9. **A completeness verdict costs what `list_types(namespace=None)` costs, and that is stated rather than hidden.** Deciding rule 6 means knowing every namespace that has a type in it, and the storage protocol has no namespace-enumeration primitive — so the registry reads the store once, with `include_retired=True`, and reuses that one page both to decide completeness and to score the named namespaces. **[Observed, row 3e first adversarial round]** the first cut issued that census **plus** one query per named namespace: 6,062 SQL round-trips for a single call over 3,000 types in 30 namespaces. Reusing the page removes the per-namespace queries; the one unbounded fetch remains, and it is the same unbounded fetch ruling **R13** declined to page in v0 and ruling **R25** routes to Phase 3 to decide together with `neighbors`. Naming namespaces also costs one rejected-proposal query per namespace named (rule 8b), which is bounded by the caller's own list. **A caller who does not ask pays nothing** (rule 1), which is why this is a stated cost on an opt-in path rather than a regression.

**What R6 does not do.** It does not merge, alias, or relate the two entries — *"the same thing, kept apart"* is `equivalent_to`, ruled **R7** and specified in [`EDGES.md`](EDGES.md). It does not make `Resolution.complete` a statement about anything but the namespaces named: the near misses inside each namespace are still the resolver's, and `ConsumerReport.complete` is untouched and still always `false`. `C3-12`.

**Designed against: mechanism 2** (nobody could find the existing types), and **mechanism 1** as the gate in front of `propose_type`.

**The four outcomes:**

- **`existing`** — a registered type fits. `confidence` is set.
- **`proposal`** — nothing fits and the candidate looks like a real type. Returns an un-persisted `Proposal`; nothing is written.
- **`not_a_type`** — the candidate is real but is **not a type**: a redundant projection of an existing one, a derived value, an export artefact. `reason` names which. **This outcome was forced by the CMS data; see §10.1.**
- **`none`** — cannot tell. Not "no match" — *cannot tell*.

**A retired name with a LIVE SUCCESSOR resolves to the successor, and the registry guarantees it** *(added by row 3c, 2026-08-29)*. `outcome="existing"` with `type` set to the **successor's** entry — never the tombstone — `confidence: 1.0`, the reason naming the succession, and the dead name still listed in `alternatives`. **This is not an exception to the rule below; it is a different act.** Resolving *through* a dead word to the live one it points at is what §5.10 promises when it says *"the old word still resolves"*; **reusing** the dead word is what §5.9 forbids, and `propose_type` still returns the tombstone.

> **Why this had to become a registry guarantee.** [Observed] the promise was previously kept **by accident**: `merge_types` writes the old name into the survivor's `aliases`, and the shipped `DeterministicResolver` happens to score an exact alias `1.0`. Nothing in the registry and nothing in the `Resolver` protocol required it — so the identical situation reached by `retire(successor=)`, which writes no alias, answered `proposal`, and a deployment supplying its own resolver (`PACKAGE.md` §2.6's **production path**) got `proposal` down both paths. **One fact, four different answers, three of them wrong.** Pinned by `C3-11`.

> **And the CHAIN, not one hop** *(row 4d, round 2)*. A word retired toward a word that is itself later retired is **two ordinary curation passes**, and this call read one successor and required it to be live — so the second pass lost the promise, and `resolve_type` answered `proposal` while `list_types(predicate=)`, `predicates(of=)` and §5.4's `declared_predicate_merged` all said the identity was live. **One store, two contradictory answers about one word**, in the call designed against mechanism 2. The walk is capped at `_IDENTITY_CHAIN_CAP` and breaks cycles, because §5.9 does not forbid constructing one. `C3-15`.

**A redirect whose identity claim has gone STALE still answers, and says so** *(the **Q56 default**, row 4d, 2026-08-30)*. When an **exact** hit is answered through an **alias** or a **successor**, and both the word asked about and the entry handed back are `kind="predicate"`, this call **re-reads both extents** — paged to exhaustion, a truncated read folded into *unknowable*, exactly as `merge_types`' own refusal #2 does — and if they no longer demonstrably agree, the returned `TypeEntry` carries `identity_stale` and `reason` says which claim went stale. **`outcome`, `type` and `confidence: 1.0` are unchanged.**

> **Why this exists, and what it deliberately does not do.** Every identity guard in this registry compares predicate extents at the moment an identity is **written** — `merge_types`, `retire(successor=)`, `import_types`, `reinstate`, `propose_type` — and this call grants confidence 1.0 at the moment it is **read**. Four things move in between: a row is created under the aliased word, a `status` flips, an extent grows, an alias is transferred by a later merge. That is `ROADMAP.md`'s kill row's **sixth trip**, and it is the first that is *different in kind*: trips 1–5 were all *the guard did not look properly*; this one is **the guard looked correctly, and then the fact changed**. **[Observed]** Door 1 needs only two individually legal merges and one new type declaring two existing predicates, after which this call answers at 1.0 over a pair §5.10 refuses **non-overridably** when asked directly. **Rule U's fourth operand: unknowable is not equal, empty is not equal, partial is not equal, and STALE is not equal.**
>
> **Refusing to answer, or answering below 1.0, would change the guarantee this section makes**, and deciding what this registry declines to serve is not an implementation call. It is **Q56**, it is the founder's, and it is open. What ships here is the cheap half — the fact is *reported*, never *suppressed* — which is what §5.4 does everywhere else it cannot refuse. The comparison is between the two **written words** and never their identity closures: after ruling **R54** `_extent` can resolve an identity, and asking whether one identity equals itself is circular, so this call asks whether the two words still denote the same set **of their own accord**. Non-predicate hits read no extent and pay nothing. `C3-14`, `C10-14`.


**A retired name with no successor is named, never silently omitted** *(added by row 3c, 2026-08-29, after an adversarial review round)*. A retired exact match is **not** an `existing` outcome — §5.9 makes the name permanently unusable. But the registry has just read the tombstone, and discarding it made this call answer *"nothing in the vocabulary fits `watch`"* about a word it knew was burned — **Rule U's confident negative, in the call designed against mechanism 2.** So a retired match is surfaced exactly the way §5.5 already surfaces a prior rejection: named in `reason`, with its `retire_reason` and `successor`, and listed in `alternatives` with a `None` score because nothing scored it. **[Observed]** a classifier that trusted the clean answer went on to call `propose_type` and got the old retired `TypeEntry` back, distinguishable from a fresh success only by inspecting `.status` — which is **UC1's own shape**, an auto-approving classifier one step earlier in the pipeline than Q6. `C3-10`.

> **This is the third time this loop found the same error** — a confident answer standing in for a fact the system had or could not have. The other two: `resolve_type`'s empty `alternatives` for a cross-namespace word (round 1), and `retire` reading an unknowable `gates_on` as *"nothing gates on this"* (§5.9). **Rule U is the rule this project keeps breaking in its own implementation**, and that is worth knowing when the next call is written.

**Behaviour when uncertain — the rule this call exists for.** Below `min_confidence`, return `none` with `alternatives` populated. **Never** return the best of a bad set as `existing`. Tenshen's classifier already does the caller-side version of this — a low `fit_score` on an existing type means the classifier was shoehorning, so it falls back rather than mislabel — and that policy is **[Inferred]** to be correct — the fallback behaviour is [Observed] in the code; that it is the *right* policy is a judgement. *(Retagged by row 3c, 2026-08-28.)* v0 puts the *detection* in the registry and leaves the *fallback* to the caller (§9, contortion 7).

**`confidence: None` ≠ `confidence: 0.0`.** `None` means no scorer ran. Rule U.

#### 5.3.2 Staleness at the read — rules *(the **Q56 default**, row 4d)*

Standing constraint 8 / ruling **R31**. **This table enumerates the rules row 4d added to §5.3 and no others**; §5.3.1's nine rules are ruling R6's and predate the constraint.

| rule | what it says | exercised by |
|---|---|---|
| 5.3.2-1 | An **exact** hit answered through an **alias** or a **successor**, where the word asked about and the entry handed back are both `kind="predicate"`, re-reads both extents — paged to exhaustion, a truncated read folded into *unknowable*, exactly as §5.10's refusal #2 does | `C3-14`, `C10-14` |
| 5.3.2-2 | Extents that no longer demonstrably agree — **or cannot be known to agree** — make the returned entry carry `identity_stale`, with `reason` naming which claim went stale | `C3-14`, `C10-14` |
| 5.3.2-3 | `outcome`, `type` and `confidence: 1.0` are **unchanged**. The fact is reported, never suppressed; refusing or lowering the confidence is **Q56**'s open half | `C3-14`, `C10-14` |
| 5.3.2-4 | A still-agreeing pair carries **no** warning, and a hit where either side is not a predicate reads **no** extent at all | `C3-14`, `C10-14` |
| 5.3.2-5 | A **near miss** is not an identity claim and is not re-verified — nobody wrote that the two words denote one thing. Only an exact alias, or a successor, counts | `prose-only:` the branch is unreachable by construction rather than merely untested — the gate requires a matched alias, and a near miss has none, so there is no state in which a near miss could carry the warning and no observable difference for a test to pin. `C3-14` carried a conditional assertion whose body never ran, which is worse than a tag because it reads as coverage; row 4d's third round found it by mutation |
| 5.3.2-6 | The comparison is between the two **written words**, never their identity closures — after **R54** the closures of two merged names are equal by construction, so asking that question could never answer `stale` | `C10-14` |
| 5.3.2-7 | The alias match is `identity_key`'s, not the candidate string's, and the left-hand row is the one the **matched alias** names — under a variant spelling the candidate names no row, and comparing nothing answers `False` for the wrong reason | `C10-16` |
| 5.3.2-8 | The left-hand lookup is **paged to exhaustion**, and a page the backend declared partial carries `alias_check_incomplete:<why>` rather than an absent `identity_stale` — Rule U's third operand, at the read | `C10-16` |

> **`identity_stale` is permanent by construction once a merged identity accretes members, and a consumer should read it that way** *(row 4d, round 2)*. The absorbed word is retired, so its own written extent can never grow again; the survivor's can. So the first ordinary type declared against the survivor after a merge makes the two written extents unequal **for good**, and no call in this document amends a live type's `predicates` to undo it. That is not a bug in the comparison — it is the write-time guard's own strictness read at the read, and **weakening it to containment would make the warning miss Door 1**, the sixth trip's own walk, where the absorbed word's extent is a subset of the survivor's and the pair is refused non-overridably anyway. What it means is that the value says *this identity has grown apart from the equality that justified it*, not *act on this now*. Whether that is the right shape for a consumer is **Q66**.

---


### 5.4 `propose_type` — an addition, not yet a fact

```python
def propose_type(
    name: str,
    definition: str,
    evidence: list[Evidence],
    proposed_by: str,
    *,
    kind: str = "entity",
    namespace: str = "default",
    predicates: list[str] = (),
    attributes: dict | None = None,
    tier: str | None = None,          # required when proposed_by starts with "ai:"
    source_version: str | None = None,   # §2.4a — the SOURCE's own version. R21
) -> Proposal | TypeEntry: ...
```

```
Proposal:
    id:            str
    name:          str
    kind:          str
    namespace:     str
    definition:    str
    predicates:    list[str]
    attributes:    dict
    evidence:      list[Evidence]
    proposed_by:   str
    proposed_at:   datetime
    tier:          str | None
    status:        "pending" | "approved" | "rejected" | "superseded"
    source_version: str | None        # §2.4a -- carried to Provenance at approval. R21
    warnings:      list[str]          # "unverified_semantics", "no_evidence", "near_duplicate:<name>"
    near_matches:  list[tuple[str, float]]
```

**Designed against: mechanism 1** (no review). This is the call that makes an addition a *request* rather than a fact — and it is precisely why 0.3 says **do not copy `foundry-ontology-open`'s `register_object_type`**: a declaration API cannot return a proposal, because it has already decided.

**Returns `TypeEntry` instead of `Proposal`** only when the namespace policy is `approval_policy="auto"` **and the tier gate passes** — in which case `provenance.approved_by == "auto:<policy>"`, never blank. See §9 contortion 4, and the tier-gate bullet above for what happens when it does not.

**Behaviour when uncertain:**
- Empty `definition` → **reject**, `ValueError`. A type without a definition is how collision starts.
- Name already taken in `(namespace, kind)` → return the **existing** `TypeEntry`. Not an error; the proposer's question is answered.
- `near_matches` above a threshold → still returns a `Proposal`, with `warnings: ["near_duplicate:<name>"]`. **v0 does not refuse on near-duplicate** — refusing is how you flatten a capability predicate (§2.3).
- `evidence == []` → `warnings: ["no_evidence"]`, proposal still created. An honest empty is better than a fabricated citation.
- `proposed_by` starts with `"ai:"` and `tier` is `None` → **reject**, `ValueError`. Per §2.7 an unattributed machine proposal is not acceptable.
- **`kind="predicate"` → the proposal stays `pending` and comes back as a `Proposal` carrying `warnings: ["predicate_requires_review"]`, whatever the namespace's `approval_policy` says** *(ruling **R40**, row 4c)*. A capability predicate is the one kind where an auto policy approving is the kill row, and §2.3 is the reason: a predicate is not just another kind. **The one place this cannot be honoured is a backend with `stores_proposals=False`** — there is no table to hold a pending proposal, so the entry is written and carries the warning, which is what makes *"a predicate went live without the review R40 requires"* enumerable rather than silent. Whether such a backend should instead be refused `kind="predicate"` outright is a product decision about what this registry declines to serve, raised rather than taken. `C10-10`
- **`approval_policy="auto"` and the tier is below `min_auto_approve_tier` → the proposal stays `pending` and comes back as a `Proposal` carrying `warnings: ["auto_approval_refused:tier_below_auto_approve_policy"]`.** Not a `TypeEntry` — the auto path did not complete. Not a `Refusal` — a valid proposal would be discarded. It **falls back to review**, which is the outcome §2.7's gate exists to produce. On a backend with `stores_proposals=False` there is nowhere to hold it, so that case alone is `Refusal(reason="tier_below_auto_approve_policy")`.

> **Added by row 3c, 2026-08-28, after a third adversarial review round — this was a hole in §13's own exit criterion.** Two sentences in this document were false for exactly this case: the paragraph below says a `TypeEntry` comes back *"only when the namespace policy is `approval_policy=\"auto\"`"*, and §2.7 point 3 says the tier gate shows up as `Refusal(reason="tier_below_auto_approve_policy")` — which is true of `approve()` and **not** of `propose_type`'s internal auto-approval attempt. `2A-RUN.md` §4 deviation **D-11** recorded the gap in the words *"Neither document says what happens when the auto path meets the tier gate"*, and §11's list of deviations touching this document then failed to carry it forward. **It is UC1's own scenario:** Tenshen auto-approves and its classifier's tier is named as Haiku (§9, contortion 4), so this is the first thing a beacon migration hits.

**`warnings` vocabulary, complete — thirty-three values across ten carriers** *(eleven at row 3c/3d; five added by [`EDGES.md`](EDGES.md) v0, row #4, 2026-08-29; three by ruling **R11** and one by **R17**/**R21**'s import guard, row 3e; **two** by row 4b, which IMPLEMENTED EDGES v0 and found two cases the specification had not — one by writing the read seam, one by an adversarial reviewer walking a merge through it; **three** by [`ACTIONS.md`](ACTIONS.md) v0, row #6; **two** by row 4c — ruling **R34**, which gave `payload_schema` a mechanism and needed a way to say a family names a schema nobody registered, and ruling **R40**, which took the auto-approval path away from `kind="predicate"`; **two more by that row's SECOND adversarial round**, which found ruling R38 followed the successor chain for endpoint *types* and not for family *names*, and found that a deliberately retired origin type had no carrier at all; **two by row 4d** — the **Q56 default**, the first value this project has minted for a fact that was *true when it was written*, and ruling **R55**, its write-door half; **one more by that row's FIRST adversarial round**, which found Rule U's third operand missing from a guard the sixth trip's own commit shipped; **one by row 6b's FIRST adversarial round**, which found that omitting `record_invocation`'s optional `judged=` silently drops the guarantee rule 3-7 exists for)*. **Held against `types.WARNING_VALUES` by [`check_spec_drift.py`](../tools/check_spec_drift.py), contents and count** — this table said *eighteen* while omitting `gate_unregistered:<gate>`, a value ruling R8 added in row 3d, that v0 code emits, that `C11-05` tests, and that **the table's own last row referred to by name**; a closed vocabulary nothing derives is one that quietly opens *(row 3e, third adversarial round)*:

| value | lands on | from |
|---|---|---|
| `unverified_semantics` | `Proposal`, and the `TypeEntry` keeps it after approval | §2.8 |
| `no_evidence` | `Proposal` | §5.4 |
| `near_duplicate:<name>` | `Proposal` | §5.4 |
| `auto_approval_refused:tier_below_auto_approve_policy` | `Proposal` (still pending) | the bullet above |
| `attributes_invalid:<field>:<why>` | `Proposal` | `PACKAGE.md` §5.3, `warn` mode |
| `name_previously_retired` | **`TypeEntry` only** — the retired entry `propose_type` hands back; no proposal is created (§5.9) | §5.4 |
| `retired_without_usage_evidence` | **`TypeEntry` only** — the retired entry `retire` returns | §5.9 |
| `reinstate_no_op:not_retired` | **`TypeEntry` only** — `reinstate` on a type that is not retired. Nothing was prevented, so it is not a `Refusal`; a call that quietly did nothing is the shape ruling **R4** forbade for `register_consumer` | §5.9b |
| `gate_unregistered:<gate>` | **`ConsumerReport`** — one per consumer whose `gate` names no registered `kind="predicate"` entry, so `would_drop` is not read as a fact about a live gate | §5.1, ruling **R8** |
| `import_refused:<reason>` | **`TypeEntry` only** — the standing entry (or, when there is none, the row as it would have looked) that `import_types` hands back instead of writing. Four causes: a row would have retired a type something still gates on; it would have written a word a live entry already answers to (`alias_collision`); or — **row 4c** — its alias would have made one word resolve to an entry of another `kind` (`kind_mismatch`) or to a predicate whose extent differs (`predicate_merge`, the kill row's fourth trip). Nothing is written; the `<reason>` is the `Refusal.reason` the equivalent §5 call would have given, and the entry carries the **row's** `kind` rather than a hard-coded `entity` *(also row 4c, first adversarial round: the reason said `predicate` and the shape said `entity`)* | §2.5, `C12-06`, `C12-08`, `C12-10` |
| `reinstate_alias_check_unavailable:<why>` | **`TypeEntry` only** — `reinstate` on a backend with `stores_aliases=False`, where every alias list is empty and §5.9b's collision check therefore means *we could not look* rather than *there is none*. Rule U, warned rather than refused because nothing is destroyed by proceeding | §5.9b |
| `not_durable_until_host_commits:<why>` | **every write result** — `TypeEntry`, `Proposal`, the `Consumer` from `register_consumer`, the `Rejection` from `reject` — when the adapter declares `transaction_scope="savepoint"` | `PACKAGE.md` §3 item 3, ruling R5. *(Row 3d. The adapter is running inside a transaction **the host owns**: the write is atomic and becomes durable only when the host commits. `status="active"` with nothing else on the object is a durable-sounding answer to a question whose answer is not yet durable, which is the failure Rule U is named after. The `<why>` is the backend's own sentence, verbatim. Added after an adversarial reviewer found the document promising this and the code not doing it — `transaction_scope` appeared nowhere in `registry.py`. **Widened one round later**: the first pass attached it in the two helpers that build `TypeEntry` and `Proposal`, and `register_consumer` and `reject` construct their results directly — so a consumer registration made over a borrowed connection came back looking exactly as done as a durable one and then vanished on host rollback, which is mechanism **C** arriving through the transaction seam.)* |

| `definitions_similarity:<score>` | **`MergeResult`** — every merge | §5.10 |
| `definitions_uncertified` | **`MergeResult`** — no divergence threshold was configured, so nothing certified the comparison | §5.10 |
| `definitions_threshold:<value>` | **`MergeResult`** — the threshold the comparison was judged against | §5.10 |

*(The three `MergeResult` values were added to this table by row 3d's third adversarial round. They had been produced by `merge_types` since row 3c's round 7 and appeared in neither this list nor §5.10, which still said the field was always empty — the code changed and two paragraphs did not. Found by running a merge, not by reading.)*

> **Five values added by `EDGES.md` v0** *(row #4, 2026-08-29)*. Ruling **R3** closes `Refusal.reason` and requires a value to be added in the change that introduces it; **that discipline belongs to this vocabulary too, and EDGES v0's first draft did not apply it** — five warnings were minted in its prose while its `Edge.warnings` field claimed to carry *"the same values"* as this table. Found by an adversarial reviewer, and corrected here rather than in a later row, because the failure mode is the one this project is named for. **No v0 code path emits any of the five**: row #4 is a spec and ships no edge store. See [`EDGES.md`](EDGES.md) §2.8.

| value | lands on | from |
|---|---|---|
| `endpoint_type_unregistered:<namespace>:<kind>:<name>` | **`Edge`** | `EDGES.md` §2.7. A dangling endpoint is written, not refused — the same argument that makes `put_consumer` accept an unregistered `gate`. The registry does **not** claim a kind mismatch it could not check, which is Rule U |
| `retracted_without_event_trail:<why>` | **`Edge`** | `EDGES.md` §2.6. Retraction is not refused on `stores_edge_events=False` — unlike `retire(force=True)` — because the retraction tombstone is columns on the edge row itself, so the record survives; what is lost is the *sequence*, and that is what this says |
| `edge_family_retired:<name>` | **`NeighborReport`** | `EDGES.md` §4.3. A retired family's edges were never deleted, so it is still searched |
| `origin_type_unregistered:<ref>` | **`NeighborReport`** | `EDGES.md` §4.3 |
| `no_edge_gate_registered` | **`ConsumerReport`** | `EDGES.md` §8. Without it, a system where nobody has registered an edge-traversing consumer returns `would_drop: []` for every new family — which reads as *"nothing will drop this"* when the truth is *"nobody has told us what traverses edges"*. Emitted only when the underlying lookup came back `complete`, exactly as `gate_unregistered` is (`C11-05`'s rule) |

> **One value added by row 4b, and it is the first this project has minted because *writing the code* found a case the specification had not** *(2026-08-29)*. The five above were minted by `EDGES.md` v0's prose; this one was minted by implementing `neighbors` against a real store and asking what happens to an edge whose family is not registered. `EDGES.md` §2.7 makes that reachable on purpose — there is no foreign key from an edge to its family, and §7.2 observes that beacon's `work_links` has none to `work_link_types` either, its own documentation calling the registry *"advisory rather than enforced"*. The spec says the registry must check the family; it does not say what the READ does with an edge that fails the check. Dropping it is mechanism **C** committed by the read seam, on exactly the host §7.2 maps. `C17-13` binds it.

| value | lands on | from |
|---|---|---|
| `endpoint_type_merged:<ref>` | **`NeighborReport`** | row 4b, third adversarial round; **its meaning changed by ruling R38, row 4c**, in the same change that changed the behaviour. It says the reference's identity spans more than one written name, joined by a **merge** or a retirement with a `successor`. It used to add that edges under the other name were **not searched**, with `complete=False`; the walk now **follows the chain** and each edge reached that way carries `via_successor`, so the report is complete and this is context rather than a shortfall. *(Before row 4b it returned `known=0`, `complete=True` and nothing at all — the confident, complete false negative `EDGES.md` §2.2 calls unacceptable; before row 4c it was honest and empty, which is a merge silently orphaning every edge written against the merged-away name.)* `C17-33`, `C17-44`, `C17-46` |
| `edge_family_unregistered:<namespace>:<name>` | **`NeighborReport`** | row 4b. `neighbors` returned an edge whose `(namespace, family)` names no registered `kind="edge"` entry. The edge is **returned, not dropped** — and because an unregistered family's `symmetric` is unknown, the `direction` filter could not be applied to it either, which is the second thing this value says. Rule U on both halves |

> **Three values added by `ACTIONS.md` v0** *(row #6, 2026-08-29 — one in the first draft, one in each of its two adversarial rounds)*. The brief for that row offered `effect_undeclared` as a candidate **`Refusal.reason`**; its UC1 design test moved it here instead, and the move is the finding rather than a tidy-up. Refusing to *record* an invocation because the host reported an effect the family had not declared destroys the only evidence that the undeclared effect happened — the shape ruling **R4** forbade for `register_consumer`, one layer up. **Row 6b makes all three reachable**: `record_invocation` emits `effect_undeclared` per surplus effect, `approval_unrecorded` when an `applied` invocation has no approver the gate granted, and `declaration_amended:<from>:<to>` when the host passes back a `Preflight` the family has moved past. Pinned on all three legs by `C19-11`, `C19-31` and `C19-56`. See [`ACTIONS.md`](ACTIONS.md) §2.5.

| value | lands on | from |
|---|---|---|
| `declaration_amended:<from>:<to>` | **`Invocation`** — when the host passes back the `Preflight` it acted on and the family has been re-declared since | `ACTIONS.md` §3.1, added by row #6's second adversarial round. Rule 3-1 copies the declaration *"so amending the family does not re-describe an existing invocation's blast radius"* — and the copy was taken at **record** time from the **current** family, which does exactly what the rule forbids. A reviewer widened a family between `preflight` and `record_invocation` and an undeclared `retract_edge` entered the ledger with no warning at all |
| `approval_unrecorded` | **`Invocation`** — when `outcome="applied"` and the gate was not asked, or refused | `ACTIONS.md` §3.2, added by row #6's first adversarial round. The first draft **fabricated** `approved_by="auto:<policy>"` in that case, so an `irreversible`/`human` family recorded an `applied` invocation by `ai:reaper` with a policy approval nobody performed — which is exactly why [`EDGES.md`](EDGES.md) §5.1 dropped the field from `EdgeProvenance` (*"a field whose only honest value is a lie"*). §2.4's never-null rule now binds only where the gate actually decided; everywhere else the value is `None` and this says so |
| `payload_schema_unregistered:<name>` | **`Edge`** — the family declares a `payload_schema` and no schema of that name is in force in its namespace | [`EDGES.md`](EDGES.md) §2.5, ruling **R34**, row 4c. The edge is **written**: refusing would put the ordering of two deployment acts — register the family, register the schema — inside a data path, and would make a family declared before its schema permanently unusable. Writing it silently is the inert `payload_schema` R34 exists to end, because a caller could not then tell a validated payload from an unvalidated one. `attr_schema_version` is `None`, which already means *"written with validation off"* (§2.1). Rule U in one value |
| `predicate_requires_review` | **`Proposal`** — on every `kind="predicate"` proposal; and on the **`TypeEntry`** of one nobody could review: a write on a backend with `stores_proposals=False`, or an `import_types` row. **Never on an entry a human approved** | §5.4, ruling **R40**, row 4c. **A capability predicate is the one kind where an auto-approval policy approving is `ROADMAP.md`'s kill row**, and two of the three kill-row trips began with a predicate that went live without a human. `propose_type(kind="predicate")` returns a **pending `Proposal` regardless of the namespace's auto policy** — the same outcome §2.7's tier gate already produces, so no caller learns a new shape. It is a warning and not a refusal because the proposal is perfectly valid: §5.4 refuses two things and warns about everything else, *because refusing a near-duplicate is how you flatten a capability predicate*. **The value's job is to mark the UNREVIEWED, and only them** — it rode onto every approved predicate and stayed, so a reviewed entry and an unreviewed one read identically, which is the whole signal *(row 4c, first adversarial round; the same shape as row 3d's durability warning — a signal that never turns off is noise)*. `C10-10`, `C10-12` |
| `edge_family_merged:<namespace>:<name>` | **`NeighborReport`** — a named `edge_families` entry is joined to another family by a merge or a retirement-with-successor, and the walk searched the other name too | [`EDGES.md`](EDGES.md) §4.3, ruling **R38**, row 4c's second adversarial round. **R38 followed the chain for endpoint TYPES and not for family NAMES**, and `EDGES.md` §2.3's architectural bet is that a family **is** a `TypeEntry` — so it inherits `merge_types` for free, and what that inheritance did was orphan every edge written under an absorbed family name, silently, under `complete=True`. **[Observed]** a steward merging two duplicate families and a consumer asking for the *surviving* name lost a real neighbour with no warning. Deliberately **not** `endpoint_type_merged`: one is about the node a walk started from and the other about the relation it asked for, and §2.3's Cause B says a value that means two things means neither. `C17-51` |
| `origin_type_retired:<ref>` | **`NeighborReport`** — the walk's origin names a type that has been **retired** | [`EDGES.md`](EDGES.md) §4.3, row 4c's second adversarial round. §4.3-3 warns for a retired **family** and §4.3-10 for an **unregistered** origin type; a deliberately retired origin — mechanism **3**, a steward's explicit *"stop using this word"* — had no carrier at all, so the one act the vocabulary performs to discourage a word was invisible in the call a consumer runs against it. Not a refusal: its edges were not deleted, which is `edge_family_retired`'s own argument one object along. `C17-52` |
| `identity_stale` | **`Resolution.type`** — the entry `resolve_type` hands back when an **exact** hit is answered through an **alias** or a **successor**, both sides are `kind="predicate"`, and the two extents that identity claim stands on no longer demonstrably agree (or cannot be known to agree) | §5.3, the **Q56 default**, row 4d. **The kill row's sixth trip, and the only fix in this project that is not another guard.** Every identity guard compares predicate extents at **write** time — `merge_types`, `retire(successor=)`, `import_types`, `reinstate`, `propose_type` — and this call grants confidence 1.0 at **read** time; four things move in between. Row 4c closed all four doors (`C10-13`) and the trip is the record that closing doors does not close the **gap**. **Rule U's fourth operand: unknowable is not equal, empty is not equal, partial is not equal, and STALE is not equal.** A **warning**, with the confidence untouched at **1.0**: refusing to answer, or answering below 1.0, changes what this registry declines to serve under §5.3's shipped guarantee, and that half of Q56 is the founder's. The comparison is between the two **written words**, never their identity closures — asking whether one identity equals itself is circular. Non-predicate hits pay nothing. `C3-14`, `C10-14` |
| `declared_predicate_merged:<declared>:<identity>` | **`Proposal`**, and the **`TypeEntry`** of a row written without one — an auto-approval, a `stores_proposals=False` write, or an `import_types` row | §5.4, ruling **R55**, row 4d. A name in `predicates` is a word whose identity has **moved**: merged away, retired with a live successor, or held as another live entry's alias. **Neither write door validated its `predicates` list against anything**, so declaring an absorbed word was legal, silent, and indistinguishable at the door from declaring the survivor — ruling **R54** makes it visible in the survivor's extent, and this makes it *announced*, to the caller who can still act on it. A warning and never a refusal: §5.4 refuses two things and warns about everything else, and declaring a predicate under a word that still resolves is **correct** behaviour (§5.10). The alias half is a scan of the namespace's active rows, so a page the backend could not finish leaves the warning **absent** — an absent warning, never a claim that the word did not move. `C4-11`, `C12-11` |
| `alias_check_incomplete:<why>` | **`Proposal`**, and the **`TypeEntry`** an approval or an import writes; **`reinstate`**'s returned entry | §5.4, row 4d's first adversarial round. The scan that asks *"does a live entry already answer to this word?"* read a page the backend had **already said was partial**, and the guard discarded that sentence — so a truncated look read as *"the word is free"* and a second live entry was created for one word. **[Observed]** on `DegradedAdapter(page_cap=3)` over ten active rows, where the full read refuses `alias_collision` non-overridably. **Rule U's third operand — *partial is not equal*, the FIFTH trip — missing from a guard the SIXTH trip's own commit shipped.** A **warning** and not a refusal, and the first cut got that wrong: refusing there does not narrow the guard, it **bans `propose_type` on every paging backend**, at exactly the scale (UC3) where paging happens — `C10-09`'s lesson one call along, and `C3-13`, whose whole subject is that backend, is what caught it. `C4-12` |
| `declaration_unjudged` | `Invocation` | `record_invocation` reported a `gate_verdict` of `allowed` or `refused` and did **not** hand back the `Preflight` it acted on, so the declaration and policy on the record are the family's CURRENT ones and the registry cannot tell whether they moved. [`ACTIONS.md`](ACTIONS.md) §3.1 rule 3-7. *(Row 6b's first adversarial round: the same invocation filed `declaration_amended` plus an `effect_undeclared` with `judged=` and a **clean row** without it. A host that never asked the gate is not warned — there was no judgement to hand back.)* |
| `effect_undeclared:<op>:<target>` | **`Invocation`** — one per surplus effect | `ACTIONS.md` §2.5, §3.3. The invocation **is** recorded and `invocations(effect_undeclared=True)` enumerates every one, which is the move `list_types(unverified_semantics=True)` makes for a proposal nobody cited. The converse — an action doing *less* than it was permitted — is deliberately **not** warned: a permission is not a promise, and warning on an unused one trains hosts to declare narrowly and amend often |

*(Enumerated by row 3c; §5.4 previously listed three inline and the rest arrived scattered across the document. The carrier column was added after a fourth review round pointed out that one flat list invites reading all of them as `Proposal.warnings`.)*

#### 5.4.1 The declared-predicate warning — rules *(ruling **R55**, row 4d)*

Standing constraint 8 / ruling **R31**. **This table enumerates the rules row 4d added to §5.4 and no others.**

| rule | what it says | exercised by |
|---|---|---|
| 5.4.1-1 | A name in `predicates` whose identity has **moved** — merged away, retired with a live successor, or held as another live entry's alias — produces `declared_predicate_merged:<declared>:<identity>`, one per moved word | `C4-11`, `C12-11` |
| 5.4.1-2 | It is a **warning and never a refusal**: the declaration stands and is written. §5.10 promises the old word still resolves, so declaring under it is correct behaviour, and §5.4's own rule is that this call refuses two things and warns about everything else | `C4-11`, `C12-11` |
| 5.4.1-3 | A live, unmerged predicate carries nothing — and so does one naming **no row at all**, because a dangling declaration is a fact rather than an error (`EDGES.md` §2.7) and nothing about it has moved | `C4-11`, `C12-11` |
| 5.4.1-4 | `import_types` carries the same value for the same reason, on the entry it writes | `C12-11` |
| 5.4.1-5 | The alias half is a scan of the namespace's active rows, so a page the backend could not finish leaves the warning **absent** — an absent warning, never a claim that the word did not move | `prose-only:` an absent warning asserts nothing, so there is no observable difference for a test to pin; the rule is recorded so that a later row cannot read the absence as a guarantee, which is the confident negative Rule U forbids |

---

### 5.5 `approve` / `reject` — the other half of the loop

```python
def approve(
    proposal_id: str,
    approved_by: str,
    *,
    mode: "human" | "auto" = "human",
    note: str | None = None,
    predicates: list[str] | None = None,     # approver may amend membership
    definition: str | None = None,           # approver may amend wording; original kept in history
) -> TypeEntry | Refusal: ...

def reject(
    proposal_id: str,
    rejected_by: str,
    reason: str,                              # REQUIRED, non-empty
    *,
    superseded_by: str | None = None,         # the existing type the proposer should have used
) -> Rejection: ...
```

```
Refusal:
    refused:  True
    reason:   str            # "tier_below_auto_approve_policy" | "already_decided" | "unknown_proposal"
    detail:   dict

Rejection:
    proposal_id:   str
    rejected_by:   str
    rejected_at:   datetime
    reason:        str
    superseded_by: str | None
    warnings:      list[str]   # §5.4's vocabulary; see `not_durable_until_host_commits`
```

**Designed against: mechanism 1.** Approval is the review that A1 says the partner agency never had.

**Why `reject` requires a non-empty `reason`, and why rejections are kept.** A rejected proposal is the cheapest record of *"we already considered this word and decided against it"*. Discard it and the next proposer re-proposes it in six months — which is mechanism 2 wearing mechanism 1's clothes. `resolve_type` **should** surface a matching prior rejection in `alternatives`.

**Behaviour when uncertain:**
- `mode="auto"` and the proposal's `tier` is below the namespace's `min_auto_approve_tier` → **`Refusal`**, not an exception. The caller may escalate to a human. This is 0.5 consequence 2 made operational.
- Proposal already decided → `Refusal(reason="already_decided")`. Idempotent, not an error. *(The value has a **second** subject as of ruling **R39**, row 4c: a second `retract_edge` on one edge ([`EDGES.md`](EDGES.md) §2.6). That is deliberately **not** idempotent — an edge's retraction reason, actor and timestamp are columns on the row, so a second retraction overwrites the first, and idempotency would hide a real double decision. Same word, same meaning — *this was already decided, and here is what was decided* — on two objects, which is why no value was minted.)*
- Approving a proposal whose `warnings` include `unverified_semantics` **succeeds**, and the resulting `TypeEntry` keeps the warning on `provenance`. v0 does **not** block on it — blocking would be a claim that the registry can tell when a definition needs a citation, which it cannot.

---

### 5.6 `list_types`

```python
def list_types(
    kind: str | None = None,
    *,
    include_retired: bool = False,
    namespace: str | None = None,        # None = all namespaces
    status: str | None = None,
    predicate: str | None = None,        # members of this predicate — the extent
    created_by: str | None = None,
    unverified_semantics: bool | None = None,
    orphaned: bool | None = None,
) -> TypeListing: ...
```

```
TypeListing:
    types:    list[TypeEntry]
    known:    int | None          # None = the backend cannot count. NOT 0
    complete: bool
    why_incomplete: str | None
    excluded_unknown: int | None  # under `orphaned=`, how many rows were excluded
                                  #   BECAUSE their orphan state is unknown — never
                                  #   folded into either answer. None when not filtering
```

*(`excluded_unknown` added to this shape, and `known` corrected to `int | None`, by row 3c. Both were implemented at 2A — deviations D-5 and Rule K's nullability — and §11 recorded the first, but the shape above never gained either.)*

**Designed against: mechanism 2** — this is the call whose absence means "nobody could find the existing types". The `predicate=` filter is how a caller reads a capability set without flattening it.

**`predicate=` names an IDENTITY, not a written word** *(ruling **R54**, row 4d, 2026-08-30)*. After `merge_types(commentable → searchable)` the two words are one identity — §2.1's rule, and §5.10's own promise that *"the old word still resolves"* — so `list_types(predicate="searchable")` returns every type that declared **either**, and asking by the absorbed word returns the same set. It used to return neither: a type declaring `commentable` disappeared from the survivor's listing **silently**, under a `known` that counted only what it happened to see, which is §5.2's *empty answer read as a confident zero* in the call whose absence means nobody could find the existing types. Reached by two ordinary acts — a legal merge, and somebody declaring a type against a word that still resolves.

> **The closure is resolved INSIDE a namespace and never across one.** An identity is per `(namespace, kind)` (§2.1, §2.6), so a second agency's `commentable` is a different identity and is left alone; collapsing the two would be §2.6's answer to mechanism 4 deleting itself, which is the trap §5.3.1 rule 4 avoids one call along. The default `namespace=None` is answered by asking which namespaces hold a `kind="predicate"` row of that name and resolving each identity there — **one bounded `name_in` lookup**, at most one row per namespace, not the unbounded census ruling **R13** declined to page in v0. The written word is always queried too, so a type declaring a predicate that names no row at all is still found: the identity only ever **adds**. `C6-08`.


**Behaviour when uncertain.** `include_retired=False` is the default *and hides things*, so `TypeListing` always reports `known` over the returned set and `complete: false` whenever any filter suppressed rows. A caller that wants a true census passes `include_retired=True, status=None, namespace=None`.

#### 5.6.1 The identity filter — rules *(ruling **R54**, row 4d)*

Standing constraint 8 / ruling **R31**. **This table enumerates the rules row 4d added to §5.6 and no others.**

| rule | what it says | exercised by |
|---|---|---|
| 5.6.1-1 | `predicate=` returns every type declaring **any word the identity spans**, and asking by the absorbed word or by the survivor gives the same set — they are one identity and this call may not have an opinion about which name the caller used | `C6-08` |
| 5.6.1-2 | The closure is resolved **inside** a namespace and never across one. A second namespace's identical word is a different identity and is untouched; collapsing them would be §2.6's answer to mechanism 4 deleting itself | `C6-08` |
| 5.6.1-3 | The default `namespace=None` gets the same answer, resolved per namespace through **one bounded `name_in` lookup** — at most one row per namespace — rather than the unbounded census ruling **R13** declined to page in v0 | `C6-08` |
| 5.6.1-4 | The written word is always queried in whatever scope the caller asked for, so a type declaring a predicate that names no row at all is still found. **The identity only ever adds** | `C6-08` |

---

### 5.7 `usage`

```python
def usage(type: str, *, namespace: str = "default") -> UsageReport: ...
```

```
UsageReport:
    type:        str
    count:       int | None        # None = not counted here. NOT zero
    last_seen:   datetime | None   # None = unknown. NOT "never"
    first_seen:  datetime | None
    orphaned:    bool | None       # None = cannot tell
    window:      timedelta | None  # the orphan window this was judged against
    why:         str | None
    complete:    bool
```

**Designed against: mechanism 3** (added once, never retired). Also the sensor for the venture's core bet — `ROADMAP.md`'s kill row *"Tenshen's own curated vocabulary rots anyway"* is measured with this call, and A4 says it may be the **only** sensor if Q7a is ruled *do-not-file*.

**Behaviour when uncertain — the important one.**

`orphaned` is defined as: `status == "active"` **and** `count == 0 or last_seen < now - window`.

**When `last_seen` is unknown, `orphaned` is `None`, never `False`.** A bare usage counter — which is exactly what Tenshen has (§9, contortion 2) — cannot distinguish a type used once in April from one used yesterday. Returning `False` there is a claim the data does not support, and it is the claim that lets a dead type sit in a vocabulary forever.

---

### 5.8 `provenance`

```python
def provenance(type: str, *, namespace: str = "default") -> Provenance: ...
```

**Designed against: mechanisms 1 and 3.** Who added this, when, on what evidence, and did anybody actually approve it.

**Behaviour when uncertain.** Missing evidence is `evidence: []` — **never** a reconstructed narrative. `approved_by` is `"auto:<policy>"` or `"unknown:imported"` for migrated rows; it is never null on an `active` type (§2.4). `history` is append-only: a correction is a new `ProvenanceEvent`, never an edit.

---

### 5.9 `retire`

> **`retire(successor=…)` carries `merge_types`' two IDENTITY guards, and it did not until row #6's third adversarial round** *(2026-08-29)*. `resolve_type` on a retired name returns its successor at **confidence 1.0** (§5.3, which this document calls a guarantee), so a retirement that names a successor performs the same collapse a merge performs — and a reviewer used it to reach `ROADMAP.md`'s **kill row**: the predicate pair `merge_types` had just refused **non-overridably under all five acknowledgements** collapsed through `retire` with **no refusal, no acknowledgement and no warning**, and did so across kinds as well. **The two guards that transfer are §5.10's refusals #2 (`predicate_merge`) and #3 (`kind_mismatch`)** — the two that are about *identity* rather than about *evidence*. They are non-overridable here as they are there, **`force=True` included**: `force` overrides the consumer guards, which are about what could be seen, never the identity guards, which are about what would become true. The guard is narrow — a plain retirement still works, and so does one whose successor shares a **non-empty identical** extent. `C9-18`.

```python
def retire(
    type: str,
    reason: str,                      # REQUIRED, non-empty
    *,
    retired_by: str,
    namespace: str = "default",
    successor: str | None = None,
    force: bool = False,
) -> TypeEntry | Refusal: ...
```

**Designed against: mechanism 3.** A1 assumes never-retired is co-dominant at the partner agency; this is the call whose absence is that mechanism.

**Behaviour when uncertain — retirement is guarded by `consumers`, not by usage.**

- If `consumers(type).gates_on` is non-empty → **`Refusal(reason="live_consumers", detail={"gates_on": [...]})`**. `force=True` overrides and records the override in `history`.
- **If `gates_on` is EMPTY and the backend cannot compute an extent → `Refusal(reason="no_consumer_evidence")`, overridable by `force=True`.** An empty `gates_on` means *"nothing gates on this"* only when the registry was able to look. On a backend with `indexes_membership=False` every extent is empty, so an empty `gates_on` means **we could not look** — and retiring on that is Rule U's forbidden empty list, in the call that exists to prevent mechanism C.

> **Added by row 3c, 2026-08-29, after an adversarial review round reproduced the silent retirement.** [Observed] with a real, registered, gating consumer in place: a fully capable backend returns `Refusal("live_consumers")`, and the identical registry on a backend declaring `indexes_membership=False` **retired the type, with no refusal and no warning.** §5.10 had already taken the honest line for exactly this uncertainty — *"the one place we do not know blocks rather than warns"* — and `retire` had not. It is the sharper of the two, because a wrong merge is at least recorded and a wrong retirement was silent. Note what this is **not**: `indexes_membership=False` is a declared, conformant capability (`PACKAGE.md` §3.2), and nothing here says otherwise. The registry simply may not convert its own blindness into a confident answer. Pinned by `C9-07`.
- If `usage(type).orphaned is None` — i.e. we cannot tell whether it is dead → retirement **still proceeds**, and the returned entry carries `warnings: ["retired_without_usage_evidence"]`.
- **A retired name is not reusable, and in v0 that is permanent.** `propose_type` with a retired name returns the retired entry with `warnings: ["name_previously_retired"]` and creates nothing. Silently reusing a retired word is mechanism 4 with a time delay.

> **Correction, row 3c, 2026-08-28, after a second adversarial review round.** The first draft justified the bullet above with *"because retiring is reversible-ish"*, and said reuse *"requires an explicit `reinstate` decision by the approver"*. **There is no `reinstate` call.** It appears nowhere in §5, nowhere in the reference implementation, and in no deviation record — it was a call this document invented in a subordinate clause and never specified. `propose_type` on a retired name returns the retired entry and stops (`C4-08`), so **there is nothing for an approver to act on and a retired name is dead for good.**
>
> **The justification is corrected rather than deleted, because the behaviour is still right.** Retirement may proceed under an unknown orphan state not because it is cheap to undo — it is not — but because (a) it is *guarded by `consumers`*, so nothing that anything known still gates on can be retired without an explicit `force` (which is itself refused when it cannot be recorded), (b) the reason and the actor are recorded permanently, and (c) **retirement destroys no instances and no history: the cost of a wrong retirement is that the vocabulary needs a new word, not that anything is lost.** That is a real argument for proceeding; "reversible-ish" was not, and it was load-bearing for the wrong reason.
>
> **This bites in UC1 and UC3.** A Tenshen relationship type retired by a classifier-drift correction and later wanted back, or one agency's admin retiring a shared word in a registry dozens of agencies publish into, both end with a permanently burned name. **Specifying `reinstate` is a v1 surface addition, so it is not taken here — it is ruling Q6** in [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6. **Taken by ruling R11 in row 3e, 2026-08-29: §5.9b.** The paragraph above stands as written — it is the record of a document inventing a call in a subordinate clause — and the burned name it describes now has a specified way back.

---

> **What row 4d added to `retire`, and §5.12 points here for the first of them** *(2026-08-30)*.
>
> 1. **`successor_unregistered`** — the successor names **no entry at all**. Every one of §5.10's identity guards is evaluated against the successor's *row*, so naming a word before it is registered skipped all three, and the word was then created by an ordinary `propose_type` + `approve`, after which the redirect was cashed at 1.0 with nothing ever having compared the two. **A guard that could not be EVALUATED has not said the collapse is safe.** Non-overridable, `force` included. When the word exists in **another** namespace the refusal says so and points at `equivalent_to`, because *"register it here"* would be mechanism 4. `C9-22`.
> 2. **`successor_is_self`** — a word cannot be its own successor. `C9-24`.
> 3. **`retired_operand`** — a successor that is itself retired leaves the old word resolving to **nothing**, which §5.10 promises it does not. **Overridable by `force`**, exactly as §5.10's is: the outcome is a loss rather than a false claim, and a steward may mean it. `C9-25`.
> 4. **Refusal #2 over the aliases the successor inherits**, non-overridable — §5.10's guard, on this call, for the reason recorded there. `C10-17`.
> 5. **A retired name is not reusable under another SPELLING either.** `commentable_` and `commentable` are one word; §5.4 hands back the tombstone. The kill row's **eighth** trip. `C10-19`.

### 5.9b `reinstate` — the other end of the retirement story *(ruling **R11**, row 3e, 2026-08-29)*

```python
def reinstate(
    type: str,
    reason: str,                      # REQUIRED, non-empty
    *,
    reinstated_by: str,
    namespace: str = "default",
) -> TypeEntry | Refusal: ...
```

**Why this call exists, in one paragraph.** §5.9's first draft justified proceeding with a retirement under an unknown orphan state on the grounds that *"retiring is reversible-ish"*, and said that reusing a retired name *"requires an explicit `reinstate` decision by the approver"*. **There was no such call.** It appeared exactly once in the whole repository — in that subordinate clause — with no signature, no test, no implementation and no deviation record, while `propose_type` on a retired name returns the tombstone and creates nothing (`C4-08`). So a retired name was burned for everyone, permanently, by one actor, with **no recorded path back**. Row 3c corrected the false justification (the true one is that retirement destroys no instances and no history) and left the governance defect standing as Q6. This is the call, and it is a *governance* addition rather than a convenience: UC1 has a classifier proposing types at runtime, and UC3 has dozens of agencies publishing into one registry — in both, one actor's wrong retirement removes a word from everybody.

**Ruling R19 — this covers edge FAMILIES and never edge instances.** An edge family **is** a `kind="edge"` `TypeEntry` ([`EDGES.md`](EDGES.md) §2.3), so it arrives here through the ordinary lifecycle with no second mechanism and no special case. An edge **instance** is never reinstated: a retracted edge is *no claim* ([`EDGES.md`](EDGES.md) §3.2), and re-asserting it is a **new** edge whose provenance cites the retracted one. The two are different acts on different objects, and giving them one verb would make `reinstate` mean *"restore a word"* in one paragraph and *"re-assert a fact"* in the next — §2.3's Cause B.

**What it does.** `status` returns to `active`; the four retirement facts (`retire_reason`, `retired_by`, `retired_at`, `successor`) come **off the live row** and into a `reinstated` provenance event that carries every one of them, along with the reason and the actor. `retired_without_usage_evidence` and `name_previously_retired` are dropped from `warnings`, because they are statements about a retirement that is no longer in force. **A reinstated name resolves again** — `resolve_type` returns `outcome="existing"` at confidence `1.0`, which is row 3c round 8's classifier shape pointing the other way: a name that still read as burned after it had been brought back would be the same confident wrong answer.

> **Why the retirement is cleared rather than kept.** §5.8's rule is that provenance is append-only and *a correction is a new event, never an edit* — the history is where the retirement now lives. A `retire_reason` sitting on an `active` row is a statement about a retirement that is not in force, and a stale `successor` on a live entry is a pointer §5.3 would read as current. **This is the one call in §5 that removes a lifecycle fact from the live row**, and the consequence is the refusal below.

**Behaviour when uncertain, and the three refusals — listed in the order the code evaluates them, which is load-bearing:** the event store has to be known present before the collision guard can read the succession graph out of it.

| # | Refusal | `reason` | Overridable? |
|---|---|---|---|
| 1 | The retirement's `successor` is itself **active** | **`successor_active`** | **No** — and it does not need to be |
| 2 | The backend cannot store events | `cannot_record_override` | No |
| 3 | Reinstating would leave **two active entries with one word between them**, down an alias or a chain of successions | **`alias_collision`** | **No** |

- **`successor_active`** is the **twentieth** `Refusal.reason` (§5.12), and the sixteenth that any v0 code path returned **when this sentence was written** — §5.12 records that row 4b made the four EDGES values returnable and calls the old count *"a false sentence for one whole row"*, so the ordinal is kept only as the value's place in the vocabulary. A retirement that named a successor is a statement that the successor took the word's job; bringing the old word back while the new one is live puts **two live words on one meaning**, which is mechanism **4** arriving through the lifecycle, in the registry whose thesis is detecting exactly that. **Not overridable, because it does not have to be:** the path back is to retire the successor first, which is an ordinary call that records who did it, and the refusal's `detail` names that path so a caller is not left guessing whether one exists. A retirement whose successor is *itself retired* reinstates normally.
- **`alias_collision`** is the **twenty-first** `Refusal.reason`, added after row 3e's first adversarial round found that **this call opened a door into mechanism 4**. `merge_types` refuses by default and carries four non-overridable refusals; `propose_type` on a name a live type holds as an alias returns the tombstone. But **[Observed, reproduced on the UC3 fixture]** four ordinary calls — *merge `bike_lane` into `cycle_track`; retire `cycle_track`; reinstate `bike_lane`; reinstate `cycle_track`* — ended with **both active and `cycle_track` still carrying `bike_lane` as an alias**, with no refusal and no warning: a consumer's alias map saying `bike_lane → cycle_track` while the registry's own `resolve_type` answered `bike_lane → bike_lane` at confidence `1.0`. Retiring the successor first walks straight around refusal #1. Both directions are checked — the name being reinstated held as an alias by a live type, and the reinstated type holding a live name as one of its own aliases — because either side of a merge can be the one coming back. **Refused rather than warned:** this is not an uncertainty, it is a collision the registry can see, *inside one namespace*, which is the case §2.6 says scoping exists to **prevent** rather than preserve — and it is scoped to one namespace on purpose, because two agencies holding one word is the state namespaces exist to *preserve*. The path back is named in `detail` and is real: retire the other word. `C9-12`, `C9-14`.

  > **The relation is aliases AND successions, transitively** *(widened after row 3e's **second** adversarial round)*. The first cut checked aliases only — and an alias is written by `merge_types`, while `retire(type, successor=…)` writes **none**. Worse, this call **clears `successor` off the live row**, so a one-hop check on that column is a check on a fact `reinstate` itself deletes. **[Observed]** following the path back that `successor_active`'s own `detail["path_back"]` instructs the caller to take — *retire the successor, then reinstate* — ended in exactly the state refusal #1 exists to forbid, and `C9-10` stopped one call short of finding it. A transitive version needs no second retirement at all: `retire a→b; retire b→c; reinstate a` leaves `a` and `c` both live. The guard now walks the succession graph **out of the `retired` events**, in both directions — *this word was replaced by something live*, and *something live was replaced by this word* — which is why the order of the two refusals below is load-bearing: the event store has to be there before the guard can read it. `detail` names `collides_with` and which `relation` it was. `C9-13`, `C9-14`.
- **Where the check cannot be made, the entry says so — twice over.** On a backend that cannot store aliases every alias list is empty, so finding no collision means *we could not look*; and a backend that **pages** may hand back a list it has already declared partial. The scan reads to exhaustion through `next_after` first, so the second case is what is left when a backend caps a query and offers no way to read the rest. Both are §5.9's unknowable `gates_on`, one call along, and both **warn** rather than refuse (`reinstate_alias_check_unavailable:<why>`, §5.4): unlike the event record below, nothing is destroyed by proceeding, and refusing would make the call unreachable on a backend whose only failing is that it pages or does not keep prior names. *(The paging half was added by row 3e's second adversarial round, which reproduced the exact end state `C9-12` asserts is refused, reached over a paging adapter with **no refusal and no warning** — Rule U in the one call whose whole job is to refuse on a collision. UC3 is the scale where a backend pages.)* `C9-15`.
- **`cannot_record_override`** applies here for `PACKAGE.md` §3.6's stated rule — *a destructive override that cannot be recorded is refused* — and this is the third call to take it after `retire(force=True)` and `merge_types(acknowledge=…)`. Every other call in this surface only ever **appends**: `retire` adds a tombstone, `merge_types` adds an alias and a tombstone, and nothing is deleted anywhere. This one clears four fields, so the event **is** the record; on a store that cannot write one, a name would come back to life with nothing anywhere saying it had ever been retired or by whom. **The cost is stated and it is not a new one:** a `stores_events=False` store cannot un-burn a name, which is the world exactly as it was before this row, and it is consistent — `retire(force=True)` is already refused on such a store for the same reason.
- **The type is not retired.** Nothing was prevented, so this is not a refusal: the entry comes back as it stands, carrying `warnings: ["reinstate_no_op:not_retired"]`. A call that quietly did nothing is the shape ruling **R4** forbade for `register_consumer` — *a registration that quietly did not happen is mechanism C committed by the registry that exists to detect it* — and the same reasoning applies to a reinstatement that quietly was not one.
- **The type does not exist** → `UnknownType`, as everywhere else. An empty answer would read as *"there is nothing to reinstate"* about a word the registry never had.
- **Empty `reason`** → `ValueError`, exactly as `retire`. An unexplained reversal of a recorded governance decision is worse than an unexplained retirement, not better.

> **`import_types` was a fourth door, and this section used to claim there were none** *(corrected by row 3e's second adversarial round, and again by its third)*. The paragraphs above said mechanism 4 *"was unreachable through the surface"* and that `reinstate` was *"the one door left open"*. **[Observed]** `import_types` (§2.5, the Foundry migration mapping) wrote a fresh record per row, so a name this deployment had **retired** came back `active` with `retire_reason`, `retired_by`, `retired_at` and `successor` all wiped, `created_by` reset to `seed`, definition and provenance overwritten — in one call, with none of the three guards and no `reinstated` event. It also falsified the stated cost below, since a `stores_events=False` store could un-burn a name that way. **Fixed rather than documented:** an import no longer reverses a local retirement. A retired row is a governance decision this deployment made, and a foreign dump saying the word is active is not a reversal of it — so the behaviour is now `propose_type`'s, verbatim (§5.9, `C4-08`): the retired entry comes back carrying `name_previously_retired` and nothing is written. `reinstate` is the call that reverses a retirement, and it is the call that carries the guards. `C12-05`.
>
> **The third round found two more of the same door and one claim that had to go.** An import also **retired** a live, consumer-gated type with no refusal, no warning and no `retired` event — the mirror of the case above, and a bypass of `PACKAGE.md` §3.6 — and it **wrote `aliases`**, reaching the exact state `alias_collision` was minted to refuse in **one ordinary call** while also erasing the alias a merge had written, which was the collision guard's only evidence for a merge until the graph learned to read `merged` events. Both are guarded now (`import_refused:<reason>`, §5.4), and `C16-06` asserts the whole-store invariant those guards approximate: *no two active entries in one namespace hold one word between them*. **The sentence claiming mechanism 4 "was unreachable through the surface" is withdrawn.** It was true of no version of this package; three adversarial rounds found three different walks into that state, each closed at whichever call the reviewer came in through, and the invariant is the answer that does not depend on guessing the next entrance.

**What `reinstate` does NOT do.** It does not restore anything a merge did, and it does not remove an alias a merge wrote. *(This paragraph previously claimed that reinstating `from_` left the merged word "still resolving to the survivor as well". **That was false** — row 3e's first adversarial round drove it: after reinstatement `resolve_type` returns the reinstated word alone, at confidence `1.0`, with the survivor not mentioned. The claim is deleted rather than softened, and the state it was quietly tolerating is now refusal #2.)* Removing another type's alias would be a second destructive act hidden inside this one, so the answer is to refuse while the collision stands rather than to tidy it away. It also does not resurrect anything outside the registry: v0 holds no instances, so there is nothing else to bring back (§1).

`C9-09` … `C9-15`, and `C12-05`.

---

### 5.10 `merge_types` — the guarded one

```python
def merge_types(
    from_: str,
    into: str,
    reason: str,                      # REQUIRED
    *,
    merged_by: str,
    namespace: str = "default",
    into_namespace: str | None = None,   # None = same namespace. Refusal #4 is
                                         #   unreachable without it — see D-7 below
    acknowledge: list[str] = (),      # explicit acknowledgement of named guard warnings
) -> MergeResult | Refusal: ...
```

```
MergeResult:
    from_:        str            # the type that was retired
    into:         str            # the survivor
    namespace:    str
    merged_by:    str
    merged_at:    datetime
    reason:       str
    entry:        TypeEntry      # `into` as it now stands
    acknowledged: list[str]      # the guard warnings the caller named, recorded in history
    aliases_added: list[str]     # `from_`'s name and aliases, now on `into`
    warnings:     list[str]      # RESERVED — always empty in v0. See below
```

**`MergeResult.warnings` records what the divergence check said, on every merge.** *(Corrected by row 3d, third adversarial round.)* This paragraph said the field was *"reserved and always empty in v0"* and that *"[Observed] `merge_types` never populates it"*. **Both sentences stopped being true within row 3c itself** — its round-7 fix made every merge carry `definitions_similarity:<score>` plus either `definitions_uncertified` (no threshold was configured, so nobody's resolver vouched for the comparison) or `definitions_threshold:<value>` — and the paragraph describing the field was never updated. A reviewer building from the document found it by running a merge. **The rule the old paragraph was protecting still holds and is worth keeping:** a caller must not read `warnings` as a verdict on whether the merge was *safe*. The guards either refused or were explicitly acknowledged, and `acknowledged` is where that record is; these three values say how close the definitions were and whether anything certified that, which is an auditor's question, not a safety flag.

**What a merge does, and what it does not.** `from_` is **retired** with `into` as its `successor`, and `from_`'s name joins `into`'s `aliases` — so the old word still resolves (**§5.3 makes that a registry guarantee, not a resolver accident** — row 3c) and §5.9's rule that a retired name is not reusable still holds. **Nothing is deleted.** A merge is two lifecycle writes and an alias, not a destruction, which is what makes the guard list below a defence rather than a formality.

*(This shape was missing until row 3c, 2026-08-28 — a fifth adversarial review round found `merge_types` was the **one call in §5 with no printed data shape**, which made §13's exit criterion "every call has a signature, a data shape, and a stated behaviour when uncertain" false for it. Four earlier rounds and the whole UC3 pass had walked past it.)*

**Designed against: mechanism 4 — and constrained by 0.1 to the point of near-uselessness, deliberately.**

**It MUST refuse when the two have different consumer sets.** Verbatim from `ROADMAP.md` Phase 1. If `consumers(from_)` and `consumers(into)` differ in their `gates_on` sets, merging asserts that every consumer of one accepts the other — which is exactly the false claim 0.1 describes.

**Full refusal list, in order:**

| # | Refusal | `reason` | Overridable? |
|---|---|---|---|
| 1 | Consumer sets differ | `different_consumer_sets` | **No.** Not by `force`, not by `acknowledge` |
| 2 | Either side has `kind="predicate"` and the two extents are not **both non-empty and byte-identical** — **and the same test is applied to every alias the write TRANSFERS**, not only to the two named operands *(row 4c, `C10-13`; extended to `retire(successor=)` by row 4d, `C10-17`)* | `predicate_merge`, with `detail["transferred_aliases"]` naming the words when that is what refused | **No.** This is the `ROADMAP.md` kill row |
| 3 | Different `kind` | `kind_mismatch` | No |
| 4 | Different `namespace` | `cross_namespace_merge` | No — cross-namespace collision is what namespaces exist to *preserve*, not resolve |
| 5 | Either side `retired` | `retired_operand` | Via `acknowledge=["retired_operand"]` |
| 6 | Definitions are not near-synonymous by the resolver | `definitions_diverge` | Via `acknowledge=["definitions_diverge"]`, recorded in history |

**Behaviour when uncertain.** If `consumers()` cannot be computed for either side — which, since `complete` is always false (§5.1), means *always* in the strict reading — v0 takes the weaker rule: refuse when the **known** consumer sets differ, and when both are empty, return `Refusal(reason="no_consumer_evidence")` with `acknowledge=["no_consumer_evidence"]` available. **Merging two types about which nothing is known is the single most destructive thing this interface can do**, so it is the one place where "we do not know" blocks rather than warns.

**Kill-criterion note.** `merge_types` is 1 of 14 calls *(13 until ruling R11 added `reinstate` in row 3e)*, refuses by default, and has four non-overridable refusals. **This is not a merge-centred design.** See §12.

---

> **What row 4d changed about this call, recorded here rather than only in the kill row** *(2026-08-30)*.
>
> 1. **The aliases a merge transfers are compared, not just its two operands.** `merge_types` re-points `from_`'s aliases at `into` in the same write, and nothing compared *those* — the kill row's **sixth** trip, reachable in two individually legal merges and one new type. Refusal #2 above now covers them, and `detail["transferred_aliases"]` says which words. `C10-13`.
> 2. **That check answers ABOVE the overridable guards and above `cannot_record_override`.** It is the fifth non-overridable identity guard and it belongs with the other four: a caller asking without acknowledgements must be told `predicate_merge`, non-overridable, not `no_consumer_evidence` and not that the audit log is missing. *(Row 4d's rounds 1 and 2; the second half was `C9-19`'s defect class inside the fix for `C9-19`'s defect class.)* `C10-18`.
> 3. **Every word comparison in the identity guards is `identity_key`'s, not the byte string's** — `'Commentable'` is the same word as `commentable`, and the shipped resolver has always scored it 1.0. The kill row's **seventh** trip. `C10-15`, `C10-16`.
> 4. **`retire(successor=)` carries refusal #2 over the aliases its successor inherits**, for the same reason and by the same test. `C10-17`.

### 5.11 Two calls the surface implies but did not name

`usage` and `consumers` cannot answer anything unless something writes to them. Naming these is not scope creep — omitting them would make §5.1 and §5.7 unimplementable.

```python
def register_consumer(consumer: Consumer, *, namespace: str = "default") -> Consumer | Refusal: ...
def record_use(type: str, *, by: str | None = None, at: datetime | None = None,
               namespace: str = "default") -> None: ...
```

*(Signature corrected by row 3c, 2026-08-28: `register_consumer` returns `Consumer | Refusal` — ruling R4 (§5.12) added `consumer_source_read_only` and changed the return everywhere except here, which is the one place the signature is actually declared. An implementer working from this section alone would have built the exact silent no-op R4 exists to forbid.)*

`record_use` is explicitly allowed to be a no-op in a backend that does not count — in which case `usage()` returns `count: None`, per Rule U. **v0 does not specify how a consumer gets registered** (decorator, config, lint, manual). That is #2's problem, and beacon's Q7a lint (assumption A4) is one candidate mechanism.

---

### 5.12 `Refusal.reason` is a closed vocabulary *(added by ruling R3, 2026-08-28; fifteenth value added by ruling R4, row 3c, 2026-08-28; four EDGES values added by row #4, 2026-08-29; **twentieth and twenty-first** added by ruling R11, row 3e, 2026-08-29; **six ACTIONS values added by row #6**, 2026-08-29; **a seventh by that row's first adversarial round**)*

A project whose thesis is that governed vocabularies resist rot does not ship an open-ended `reason` string in its own contract. `Refusal.reason` takes exactly these **thirty** values — eleven defined in this document, three introduced by [`PACKAGE.md`](PACKAGE.md) v0 and adopted here, one added by ruling **R4**, four by [`EDGES.md`](EDGES.md) v0, two by ruling **R11**, seven by [`ACTIONS.md`](ACTIONS.md) v0, one by row 4d's first adversarial round, and **one by its third**:

`different_consumer_sets` · `predicate_merge` · `kind_mismatch` · `cross_namespace_merge` · `retired_operand` · `definitions_diverge` · `no_consumer_evidence` · `live_consumers` · `tier_below_auto_approve_policy` · `already_decided` · `unknown_proposal` · `proposals_not_stored` · `cannot_record_override` · `attributes_schema_violation` · **`consumer_source_read_only`** · **`edge_family_unknown`** · **`endpoint_kind_mismatch`** · **`edge_store_absent`** · **`unknown_edge`** · **`successor_active`** · **`alias_collision`** · **`action_family_unknown`** · **`precondition_unmet`** · **`human_approval_required`** · **`tier_below_action_policy`** · **`effect_not_permitted`** · **`action_store_absent`** · **`input_kind_mismatch`** · **`successor_unregistered`** · **`successor_is_self`**

**`successor_is_self` — the thirtieth.** Returned by `retire` (§5.9) when `successor` names the type being retired. Not `successor_unregistered`, which says *the successor names no entry, register it first* — a sentence that is **false here and that a caller would act on**, since the word is registered, live, and is the type itself. A tombstone redirecting to its own word is a claim nobody made, and a cycle `_identity_closure` would have to keep guarding for nothing. *(Row 4d's third adversarial round: a closed vocabulary earns its keep by each value naming exactly one fact, and reusing a near-enough one is how a caller is told the wrong thing confidently.)* `C9-24`.

**`successor_unregistered` — the twenty-ninth, and the kill row's seventh trip is why.** Returned by `retire` (§5.9) when `successor` names **no entry at all** in the namespace. Not `successor_active` (that is `reinstate`'s refusal about a successor that exists and is live), not `unknown_proposal` (a different object), not `kind_mismatch` (there is no entry, so there is no kind to mismatch). It says the one thing none of the twenty-eight said: *you have named a word that does not exist, so nothing could be checked about it.*

> **Why a refusal rather than a fact recorded.** [`EDGES.md`](EDGES.md) §2.7's rule is that a dangling reference is *a fact, not an error* — and that rule is about a **read-path** endpoint, not about a governance act. A `successor` is an identity claim: it makes every `resolve_type` for the retired word answer with the successor **at confidence 1.0**, which §5.3 calls a guarantee. Every one of §5.10's identity guards on this call is evaluated against the successor's row, so naming a word that does not exist skipped **all three** — and the word was then created by an ordinary `propose_type` + `approve`, after which the redirect was cashed at 1.0 with nothing ever having compared the two. **[Observed]**, row 4d's first adversarial round, on both fully-capable legs and the async mirror: a `predicate` retired toward a word that arrived later as an **entity** answered a question about one kind with an entry of another at 1.0 — refusal #3, non-overridable, walked past entirely.
>
> **A guard that could not be EVALUATED has not said the collapse is safe.** That is Rule U at the one call §5.3 calls a guarantee, and it is the sixth trip's own shape — *the guard looked, and then the fact changed* — applied to the guards the sixth trip's commit shipped. Non-overridable, `force=True` included, exactly as the guards it stands in for are: `force` overrides what could be **seen**, never what would become **true**. The path forward is one reordering, and the refusal says it: register the successor first, then retire toward it. `C9-22`.

**`successor_unregistered` also refuses a word naming ITSELF** *(row 4d, round 2)*: a tombstone that redirects to its own word is a claim nobody made, and a cycle `_identity_closure` would have to keep guarding for nothing. And **`retire(successor=)` validates the aliases its successor inherits** — the guard `merge_types` has carried since `C10-13`. It was out of reach while §5.3 followed a single hop (the absorbed word resolved to a retired row and fell back to `proposal`); the moment the chain is followed, every alias the retired row carries is re-pointed at the successor, and **Door 1 reopens with a different second act**. The difference between the two calls was never the identity claim, only which write made it. `C9-24`, `C10-17`.

**`successor_active` — the twentieth, and the sixteenth any code path returns.** Returned by `reinstate` (§5.9b) when the retirement being undone named a successor that is itself active. Not `retired_operand` (that is `merge_types`' refusal about an operand's *status*, and here the operand is retired on purpose — being retired is the precondition, not the problem), not `cross_namespace_merge`, not `already_decided` (a proposal object, one lifecycle along). It says the one thing none of the nineteen said: *the word you want back has a live replacement.*

> **This paragraph ended with a false sentence for one whole row, and row #6 found it by needing the number.** It read *“The four EDGES values remain returned by no v0 code path, so the count of values any implementation can actually produce is **seventeen**.”* That was true when row 3e wrote it and stopped being true the day row 4b **implemented** [`EDGES.md`](EDGES.md) v0: `ontoloche/registry.py` returns `edge_family_unknown`, `endpoint_kind_mismatch`, `edge_store_absent` and `unknown_edge` today. **[Observed]** by `grep -n` over the package, 2026-08-29. So all twenty-one values a code path could return are returned, and **the count is now twenty-one**. Nothing checked it, because [`check_spec_drift.py`](../tools/check_spec_drift.py) holds the *enumerated list* and the *count word* against `types.REFUSAL_REASONS` and has no way to know which values any code path reaches — the third side of R31's own recorded blind spot, in the section that carries R3.

**`alias_collision` — the twenty-first, added in the same change as the guard.** Returned by `reinstate` (§5.9b) when bringing a name back would leave two **active** entries with one word between them — the name held as an alias by a live type, or the reinstated type holding a live name as one of its own. Not `successor_active` (that is about the retirement's declared successor, and this collision is reached precisely by retiring that successor first), not `cross_namespace_merge` (this is inside **one** namespace, which is the case §2.6 exists to prevent rather than preserve), not `retired_operand` (nothing here is an operand of a merge). It says the one thing none of the twenty said: *the word you want back is already spoken for by something alive.* Added by row 3e's first adversarial round, which reproduced the four-call walk into mechanism 4.

**The four EDGES values — what each means and why none of the fifteen said it** *(row #4, 2026-08-29; added here in the same change that introduces them, per R3's own rule)*. All four are returned by calls specified in [`EDGES.md`](EDGES.md); **no call in this document returns any of them, and no v0 code path does either**, because row #4 is a spec and ships no implementation. They are enumerated now rather than later because R3's rule is about the *vocabulary* being closed, and a spec that introduces a refusal without amending the list is how a closed vocabulary quietly opens.

- **`edge_family_unknown`** — `add_edge`, or `neighbors(edge_families=…)`, naming a family that is not a registered `kind="edge"` entry ([`EDGES.md`](EDGES.md) §4.3). Not `unknown_proposal` (a different object), not `kind_mismatch` (the entry does not exist at all, so there is no kind to mismatch). The alternative — returning a clean empty `NeighborReport` for a typo'd family — is mechanism **C** committed by the read seam, which is why this is a refusal and not a warning.
- **`endpoint_kind_mismatch`** — an edge whose `src`/`dst` is not one of the `kind`s its family declared, **or** is at the wrong level (an `InstanceRef` for a `level="type"` family, or the reverse) ([`EDGES.md`](EDGES.md) §2.4.1). **One value covers both**, with `detail` naming which, and that is a deliberate economy rather than an oversight: the two are the same failure — *this endpoint is not what the family declared* — and a closed vocabulary that grows a value per variant of one failure is not closed for long. `kind_mismatch` is **not** reused: it is `merge_types`' refusal about two *operands of a merge*, and overloading it would make one word mean two things one section apart, which is §2.3's Cause B.
- **`unknown_edge`** — `retract_edge` (or any edge call) naming an `edge_id` the store does not hold ([`EDGES.md`](EDGES.md) §2.6). The exact shape of `unknown_proposal`, one object along. *(Added by row #4's third adversarial round: the specification had reused `edge_family_unknown` for it, which names a different failure — §2.3's Cause B, committed inside the section that argues against reusing `kind_mismatch` for two things.)*
- **`edge_store_absent`** — any edge call against a registry whose adapter declares `stores_edges=False` ([`EDGES.md`](EDGES.md) §6). A capability refusal, the fourth of that shape after `proposals_not_stored`, `cannot_record_override` and `consumer_source_read_only` — and it exists for the same reason the first of those does: an empty `NeighborReport` would read as *"this node has no neighbours"*, which is Rule U's forbidden empty in the one call a caller would believe.

**The six ACTIONS values — what each means and why none of the twenty-one said it** *(row #6, 2026-08-29; added here in the same change that introduces them, per R3's own rule)*. All six are returned by calls specified in [`ACTIONS.md`](ACTIONS.md) and **no call in this document returns any of them**; they were enumerated in row #6 rather than in the build row for the reason the EDGES four were, because R3's rule is about the *vocabulary* being closed and a spec that introduces a refusal without amending the list is how a closed vocabulary quietly opens. **Row 6b ships the calls, so all seven (the six plus round 1's `input_kind_mismatch`) are now returned by v0 code** and each is pinned by a `C19` id on all three legs — which is R3's other half: a value specified and returned by nothing is a promise, and the build row is where it becomes a contract.

- **`action_family_unknown`** — `preflight`, `record_invocation` or `projection` naming a family that is not a registered `kind="action"` entry ([`ACTIONS.md`](ACTIONS.md) §7). The exact shape of `edge_family_unknown` one kind along, and a **separate value for the same reason `unknown_edge` is separate from `edge_family_unknown`**: reusing the edge value would make one word mean two things, which is §2.3's Cause B. The alternative — an empty `Preflight` for a typo'd family — is mechanism **C** committed by the gate.
- **`precondition_unmet`** — a declared precondition does not hold, **or cannot be evaluated** ([`ACTIONS.md`](ACTIONS.md) §2.4). **The first value in this vocabulary about a runtime state of the world** rather than about the vocabulary itself; the other twenty-six are all about words, proposals, entries or capabilities. `detail` carries the failing condition's `kind` and `subject` and whether it was **false** or **unknown** — one value, two states, the states in `detail`, per `endpoint_kind_mismatch`'s recorded economy.
- **`human_approval_required`** — an `irreversible` family declaring `approval_mode != "human"` (at declaration), or a `human`-mode family invoked with no human approver (at `preflight`) ([`ACTIONS.md`](ACTIONS.md) §2.2, §5.2). **One value, two doors**, `detail` naming which — the same deliberate economy `endpoint_kind_mismatch` makes, and for the reason [`EDGES.md`](EDGES.md) states there: a closed vocabulary that grows a value per variant of one failure is not closed for long. Not `tier_below_auto_approve_policy`, which is about a *type proposal*'s tier and not about an invocation's approver.
- **`tier_below_action_policy`** — the invoking actor's tier is below the family's `min_auto_tier` ([`ACTIONS.md`](ACTIONS.md) §5.2). **`tier_below_auto_approve_policy` is deliberately NOT reused**, and the temptation to reuse it is exactly Cause B: that value is about **approving a proposed type**, this one about **invoking an approved action**. A deployment may auto-approve Haiku's *proposals* and refuse Haiku's *invocations*, and one word could not express that.
- **`effect_not_permitted`** — a family whose `effects` name an operation outside [`ACTIONS.md`](ACTIONS.md) §2.5's four, or one of the six governance calls that may never be an effect (`approve`, `reject`, `retire`, `reinstate`, `merge_types`, `register_consumer`). Refused **at declaration**, not at invocation. `attributes_schema_violation` is about a schema's field *types*; this is a rule about the closed vocabulary of one field's *values*, and `merge_types` appearing in it is `ROADMAP.md`'s kill row wearing a verb.
- **`action_store_absent`** — any invocation call against an adapter declaring `stores_invocations=False` ([`ACTIONS.md`](ACTIONS.md) §8). A capability refusal, the **fifth** of that shape after `proposals_not_stored`, `cannot_record_override`, `consumer_source_read_only` and `edge_store_absent`, and it exists for the reason the first of those does: an empty `InvocationReport` would read as *"nothing has ever run"*, which is Rule U's forbidden empty in the one call a caller would believe.

- **`input_kind_mismatch`** — a supplied input is not one of the `kind`s (or, for an edge ref, one of the families) its `InputSpec` declared, **or is a `kind="predicate"` at any door regardless of what the family declared** ([`ACTIONS.md`](ACTIONS.md) §2.3). **Added by row #6's first adversarial round, and it closes the kill row.** `InputSpec.kinds` was enforced at declaration and by nothing at invocation, so a reviewer declared a family with `kinds=None`, handed `preflight` two `kind="predicate"` refs and got `verdict="allowed"`, then recorded it `applied` — `merge_capabilities(commentable, searchable)`, constructed end to end through the one door [`ACTIONS.md`](ACTIONS.md) §2.3 names as unconstructible. [`EDGES.md`](EDGES.md) §2.4.1 binds at **both** layers and §17.4 of that document records the round it cost to learn; ACTIONS claimed to inherit the rule *unchanged* and inherited half of it. **`endpoint_kind_mismatch` is deliberately not reused**: that value is about an *edge's* endpoint, and one word for two objects is §2.3's Cause B — the same argument that made `unknown_edge` separate from `edge_family_unknown`.

**A seventh was considered and NOT taken: `unknown_invocation`.** [`EDGES.md`](EDGES.md) needed `unknown_edge` because `retract_edge` names an existing edge by id; **no ACTIONS call names an existing invocation by id**. `compensates` points at one, and a `compensates` pointing at nothing is recorded with a warning rather than refused — refusing would discard the compensation record itself — while `invocations(...)` is a filter, where an empty result is honest rather than a silent drop. Recorded so the absence reads as a decision.

> **Ruling R11's reservation, now spent.** This paragraph read *"`successor_active` is specified by R11 and lands with `reinstate` in row 3e, which will make twenty. It is named here so the count is reconcilable, and it is deliberately not in the list above, because R3's rule is that a value is added in the change that introduces it — and nothing introduces it yet."* Row 3e introduces it, so it is in the list above, added in the same change that made `reinstate` return it. **That is R3's rule working as designed rather than an amendment to it**, and it is worth leaving the record: the reservation was written precisely so the twentieth value could not arrive unannounced.

**Adding a value requires amending this section in the same change that introduces it.** A `Refusal` whose `reason` is not in this list is a conformance failure, and the contract suite (`PACKAGE.md` §6) should assert it. Ruling record: [`decisions/2026-08-28-package-v0-rulings.md`](../decisions/2026-08-28-package-v0-rulings.md).

**`consumer_source_read_only` — what it means and where it comes from.** `register_consumer` against a consumer *source* that cannot be written to — a checked-in config file, the shape `PACKAGE.md` §7.3 shows beacon using — returns `Refusal(reason="consumer_source_read_only")`. It is not a policy refusal like the other fourteen; it is a **capability** refusal, the third of that shape after `proposals_not_stored` and `cannot_record_override`. `register_consumer` therefore returns `Consumer | Refusal`, and never a silent no-op: a registration that quietly did not happen is mechanism **C** committed by the registry that exists to detect it.

> **Deviation D-1, resolved.** `PACKAGE.md` §3.4 primitive 10 and contract test `C11-04` required a `Refusal` here; none of R3's fourteen said it honestly, so Phase 2A raised `NotSupported` and recorded the conflict instead of adding a value unilaterally ([`2A-RUN.md`](../runs/2A-RUN.md) §4.1, inherited by [`3B-ASYNC.md`](../runs/3B-ASYNC.md) §5). **Ruling R4 added the fifteenth value**, amending this section in the same change that made the registry return it, per R3's own rule. `C11-04` now asserts the reason in both the sync and the async suite.

## 6. Which mechanism this is designed against

**Against A1** ([`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md)): *The partner agency's dominant mechanism is **1 + 3 together** — anyone could add a type with no review, and nothing was ever retired — with contractor rotation as the named cause. Collision (4) is present but not dominant. Silent per-consumer drop (C) is present but unobserved by the partner agency, because no existing tool surfaces it.*

| Mechanism | Status under A1 | The calls that answer it |
|---|---|---|
| **1** no review | **Dominant** | `propose_type` → `approve`/`reject`; `Provenance.approved_by`; the tier gate on auto-approval |
| **3** never retired | **Dominant** | `usage` (count / last_seen / orphaned), `retire`, `list_types(orphaned=True)` |
| **2** could not find | Enabling condition | `resolve_type`, `list_types`, retained rejections |
| **C** silent drop | **Present, unobserved — and forced into the design by direct evidence** | `consumers`, `predicates`, `Consumer.on_unknown` |
| **4** collision | Present, not dominant | `namespace` (preserve), `merge_types` (refuse), predicate protection |

**None of these is "the centre".** A1 states it plainly: *"No single call is 'the centre'; the centre is the proposal→approval loop."* This document is built that way — `resolve_type` → `propose_type` → `approve`/`reject` is the spine, and `consumers`, lifecycle and provenance hang off it as equals.

**Two of these stand regardless of what the partner agency says.** Finding 0.1 §"What this changes": `consumers` was forced by a real production incident and `predicate` by five real vocabularies. **The partner agency cannot make them unnecessary.** Everything else in the table is contingent on A1.

---

## 7. Model tier and external evidence, summarised

Because these two are easy to lose in the call list, and both are 0.5 consequences rather than 0.1 ones:

| 0.5 consequence | Where it lives in this interface |
|---|---|
| **(2)** Model tier is a product parameter | `resolve_type(tier=)` **required** · `propose_type(tier=)` required for `ai:` proposers · `Provenance.model_tier` · `approve(mode="auto")` refuses below `min_auto_approve_tier` · `list_types` can enumerate cheap-tier-never-reviewed types |
| **(3)** Verification against external documentation must be in the product | `Evidence.kind == "external_doc"` with a required `Citation{url, title, retrieved_at, quote}` · `warnings: ["unverified_semantics"]` on approval · `list_types(unverified_semantics=True)` |
| **(1)** Walkthrough step 5 is load-bearing | `consumers()` **is** step 5's screen. `complete: false` is the honesty requirement that screen carries |

**The concrete failure this is aimed at:** a cheap-tier proposal defining `scope_severity_code` as *"higher letters are less serious"*, with zero citations, auto-approved, and thereafter authoritative. Under this interface that proposal carries `model_tier: "haiku"`, `evidence: []`, is **refused** for auto-approval by tier policy, and if a human approves it anyway the type carries `unverified_semantics` forever and is enumerable.

---

## 8. Worked shape — one entry, fully populated

```python
TypeEntry(
    name="facility",
    kind="entity",
    namespace="default",
    definition=(
        "A Medicare/Medicaid-certified nursing home, identified by its CMS "
        "Certification Number (CCN). Provider Name is a label, not an identifier: "
        "104 distinct names are shared by more than one CCN in the August 2026 file."
    ),
    created_by="ai",
    status="active",
    predicates=["searchable", "addressable"],
    consumers=ConsumerReport(known=2, complete=False, ...),
    usage=UsageReport(count=14627, last_seen=..., orphaned=False, complete=True),
    attributes={"primary_key": ["ccn"]},
    aliases=["nursing_home", "provider"],
    provenance=Provenance(
        created_at=...,
        created_by_actor="ai:proposer",
        proposed_by="ai:proposer",
        approved_by="user:sd",
        model_tier="opus",
        evidence=[
            Evidence(kind="data",
                     summary="14,627 distinct CCNs over 419,479 rows; CCN->name is 1:1 (0 CCNs carry more than one name).",
                     locator="NH_HealthCitations_Aug2026.csv"),
            Evidence(kind="external_doc",
                     summary="CMS describes the row subject as the nursing home that received the citation.",
                     citation=Citation(url="https://data.cms.gov/provider-data/dataset/r5ix-sfxw",
                                       title="Nursing home health citations — CMS Provider Data Catalog",
                                       retrieved_at=...)),
        ],
    ),
)
```

---

## 9. The Tenshen design test — `work_link_types`, field by field

**A design *test*, not a design *input*** (`ROADMAP.md`, "Rule of the ordering"). Read read-only from `C:\Users\steph\projects\beacon\src\beacon\models\work_link_type.py` and `.../services/work_link_service.py` on 2026-08-28. Nothing in beacon was edited. **[Observed]** unless marked.

**The subject:** a registry of relationship labels for `WorkLink` rows, seeded with five (`blocks`, `related_to`, `part_of`, `duplicates`, `follows`), grown at runtime by an AI classifier that proposes a new type only when confident none of the existing ones fit.

| Tenshen field / behaviour | Expressed as | Contortion? |
|---|---|---|
| `id: int` primary key | *not represented* — `name` is the identity in v0 | **No.** Surrogate keys are storage (#2) |
| `name: String(64), unique` | `TypeEntry.name`, unique within `(namespace, kind)` | **No.** Tenshen has one implicit namespace |
| `definition: Text, not null` | `TypeEntry.definition`, required non-empty | **No.** Exact match, including the non-empty rule — `_create_type_from_ai` rejects empty definitions today |
| `created_by: String(20)` = `seed \| ai \| user` | `TypeEntry.created_by` — **same field name, same three values** | **No.** v0 took the vocabulary from here deliberately |
| `created_at` | `Provenance.created_at` | **No** |
| `usage_count: int` | `UsageReport.count` | **Partial — see contortion 2** |
| `is_symmetric: bool` | `attributes["is_symmetric"]` | **CONTORTION 1** |
| `inverse_label: String(64) \| None` | `attributes["inverse_label"]` | **CONTORTION 1** |
| *(no `status` column)* | `status` — all rows migrate as `active` | **CONTORTION 3** |
| *(AI types persist immediately)* | `approval_policy="auto"`, `approved_by="auto:classifier"` | **CONTORTION 4** |
| `fit_score` (returned by classifier, **not stored**) | `Resolution.confidence` on the call; **nothing** in `Provenance.evidence` | **CONTORTION 5** |
| *(nothing registers a consumer)* | `consumers("blocks") → known: 0, complete: False` | **Not a contortion — a null result. See below** |
| *(no predicate concept)* | `predicates: []` | **No.** `work_link_types` is genuinely a type list, not a predicate — the one Tenshen vocabulary of the eight that is not |
| `_TYPE_NAME_RE` snake_case validation; name collision returns the existing row | `propose_type` name rule; collision returns the existing `TypeEntry` | **No.** Exact match |
| low `fit_score` → fall back to `related_to` | `resolve_type(min_confidence=)` → `outcome="none"`; the fallback itself is caller-side | **CONTORTION 7** |

### The seven contortions, recorded and **not** designed away

**Contortion 1 — `is_symmetric` and `inverse_label` have no home.** They are edge-shape fields, and edges are deliverable **#4**. In v0 they survive only in `attributes`, which the registry never reads. **Consequence:** a v0-only implementation cannot validate them, cannot enforce that a symmetric type has no inverse label, and cannot stop two types disagreeing about direction. **Not fixed here.** This is the strongest argument that #4 must follow #1 closely, and it is why the ordering table puts `EDGES.md` at #4 rather than #6.

**Contortion 2 — `usage_count` is a bare counter, so `usage()` is half-blind.** v0's `UsageReport` wants `count`, `last_seen`, `first_seen` and `orphaned`. Tenshen has `count` and nothing else. So `usage("blocks")` on a Tenshen backend must return `last_seen: None`, `orphaned: **None**`, `complete: False`. **This is the interface exposing a real defect, not a mismatch to paper over:** the venture's core-bet sensor (`ROADMAP.md` kill row, *"Tenshen's own curated vocabulary rots anyway"*) **cannot currently fire**, because a counter cannot distinguish a type used once in April from one used yesterday. **[Inferred]** that adding a `last_used_at` column to `work_link_types` is the cheapest thing beacon could do to make the experiment measurable — recorded as a *finding for the beacon program*, not as a change to this interface.

**Contortion 3 — no `status`.** Tenshen types are born live and never retired. Migration sets every row `active`; `retire` becomes newly available, which is a gain, but there is no historical retirement to import and no way to know whether any of the five seeds is dead.

**Contortion 4 — there is no approval step, and this is the structural one.** `_create_type_from_ai` validates shape (snake_case name, non-empty definition, no collision) and then persists. There is no queue, no reviewer, no `proposed` state. The AI's proposal **is** the decision.

Expressing that in v0 requires `approval_policy="auto"` at the namespace, with `Provenance.approved_by = "auto:classifier"` — and the value of doing so is precisely that it stops being invisible. **[Inferred]** this is the highest-value thing the interface does for Tenshen: not a new capability, but making an existing silent auto-approval legible and enumerable.

Note the collision with **§2.7**: auto-approval is refused below `min_auto_approve_tier`, and the code comment in `_create_type_from_ai` names **Haiku** as the model whose output it normalises. Under a strict tier policy, Tenshen's current classifier tier would **fail** auto-approval. **The interface is not bent to accommodate this.** Beacon's options are to raise the tier, set `min_auto_approve_tier` low and accept the recorded risk, or add a review step. That is a beacon decision, and 0.5 says the third is the one that catches confident wrongness.

**Contortion 5 — the evidence slot is empty for every AI-created type.** `fit_score` justifies creation and is then discarded; the user's free text is persisted **separately, on the link**, not on the type. So `provenance("some_ai_type").evidence == []` and every AI-created Tenshen type carries `warnings: ["no_evidence"]` after migration. Honest, and unflattering.

**Contortion 6 — `consumers()` returns zero, and that is the finding.** Nothing in beacon registers a consumer of a work-link type, so `consumers("blocks")` is `known: 0, complete: False`. That is not a defect of the interface; **it is the interface reporting that Tenshen has exactly the blind spot finding 0.1 diagnosed.** The `capture` incident happened in a neighbouring vocabulary for want of this call, and a migration to v0 that registers no consumers gains nothing on mechanism C. **The registration is the work; the call is trivial.**

**Contortion 7 — the `related_to` fallback is caller policy, and v0 keeps it there.** Tenshen falls back to a stock type on low fit or AI failure. v0's registry returns `outcome="none"` and does not know what a default is. **Deliberate:** a registry that ships a default type is a registry that quietly labels things wrong at scale. Recorded so nobody adds `default_type` to v0 in a later pass thinking it was an oversight.

### Tenshen verdict

**Expressible, with seven recorded contortions, two of them structural (1 and 4). Nothing was bent to remove them.** Per `ROADMAP.md`'s "Rule of the ordering", a recorded conflict is a good outcome — and contortions 2 and 6 are the more valuable half, because both are the interface **telling beacon something true about its own instrumentation** rather than complaining about a field.

---

## 10. The CMS design test — facility, citation, tag

**CMS wins any conflict with Tenshen** (brief; `ROADMAP.md` "Rule of the ordering"). The entities are the pre-registered ground truth from [`0.5-ground-truth-PREREGISTERED.md`](../findings/0.5-ground-truth-PREREGISTERED.md) plus the fourth entity the Opus run added and [`0.5-RESULTS.md`](../findings/0.5-RESULTS.md) recorded as **better than the ground truth**.

| Entity | `kind` | `name` | Key (in `attributes`) | Notable evidence |
|---|---|---|---|---|
| Nursing home | `entity` | `facility` | `ccn` | 14,627 distinct CCNs; CCN→name 1:1; **104 names shared across CCNs** |
| Survey | `entity` | `survey` | `(ccn, survey_date, survey_type)` | 69 in the 400-row sample |
| Citation | `entity` | `citation` | one per row | 400 in sample; 419,479 in the full file |
| Deficiency tag | `entity` | `deficiency_tag` | `tag_number` | 267 tags full-file, **0 with more than one description** — description belongs to the tag, not the citation (T5) |
| Correction status | **`value_set`** | `deficiency_corrected_status` | 6 values | T1 — six status strings, **no yes/no** |
| Severity scale | **`value_set`** | `scope_severity_code` | A–L, **ordered** | The field that inverted at the cheap tier |

Relationships (`citation → issued during → survey → conducted at → facility`) are registered as `kind="edge"` entries — names, definitions, provenance, lifecycle — and **nothing more**, because edges are **#4**.

### CMS conflict 1 — `value_set` had to be added as a kind. **Resolved for CMS.**

The two most dangerous fields in this file are not types: they are **property value sets**. `Deficiency Corrected` looks like a boolean and holds six status strings with no yes/no among them. `Scope Severity Code` is an **ordered** A–L scale where J/K/L mean Immediate Jeopardy — and it is the field the cheapest tier read backwards.

If v0 registers only entities, predicates and edges, then neither of those value sets has provenance, neither has an evidence slot, and **the severity ordering — the single most consequential domain semantic in the dataset — is unversioned free text inside somebody's transform.**

**Tenshen needed no such kind.** `work_link_types` has no value sets. So this is a direct CMS-vs-Tenshen divergence, and per the rule **CMS wins**: `value_set` is in v0.

> **This is `ROADMAP.md` Phase 2's exit criterion arriving early** — *"the interface changed at least once because of a conflict between them"*. Recorded here rather than discovered later.

### CMS conflict 2 — `resolve_type` needed a fourth outcome, `not_a_type`. **Resolved for CMS.**

The brief's surface says `resolve_type(candidate, context) -> existing | proposal | None`. The CMS `Location` column breaks it. **[Observed]** `Location` is **99.988% redundant** — exactly rebuilt from Provider Address + City/Town + State + ZIP Code in 419,428 of 419,479 rows, and 400 of 400 in the sample.

Under the three-outcome surface, `resolve_type("location", ...)` returns `None`, and `None` reads to any caller as *"nothing matched — go propose it"*. That is **exactly** the T3 failure the ground truth predicted: inventing a second entity from a duplicate projection. The registry would have handed the pollution machine its first type.

So v0 adds **`not_a_type`**, with `reason ∈ {redundant_projection, derived_value, export_artefact, instance_not_type}`. `Processing Date` (T7, single-valued export stamp) is `export_artefact`; `Location` is `redundant_projection`.

**Tenshen never needed this** — its candidates arrive from a classifier already committed to *"this is a relationship"*, so the "not a type at all" case cannot occur there. Again a direct divergence, again **CMS wins**.

### CMS conflict 3 — instance resolution is not in this interface, and saying so is the resolution

**[Observed], T4:** 104 distinct provider names are shared by more than one CCN. Resolving facilities on name merges genuinely different facilities.

`resolve_type` cannot help. It resolves the *word* `facility`; it does not resolve `"BURNS NURSING HOME, INC."` against 14,627 instances. The walkthrough's *"I already know 38 of these"* (step 2) is therefore **not served by this document at all**.

**Resolution: state it as a gap rather than stretch the call.** Adding instance resolution to a type registry would make `resolve_type` mean two different things — which is 0.1's Cause B, semantic collision, committed by the spec itself. Recorded in §1 non-goals and in §11.

### The severity case, end to end — the interface catching 0.5's worst result

```python
p = propose_type(
    name="scope_severity_code", kind="value_set",
    definition="Ordered severity scale A-L. Higher letters are LESS serious.",   # WRONG
    evidence=[], proposed_by="ai:proposer", tier="haiku",
)
# p.warnings == ["no_evidence", "unverified_semantics"]

approve(p.id, approved_by="ai:proposer", mode="auto")
# -> Refusal(reason="tier_below_auto_approve_policy",
#            detail={"tier": "haiku", "min_auto_approve_tier": "sonnet"})
```

The correct proposal carries the citation and passes:

```python
Evidence(
    kind="external_doc",
    summary="CMS scope-and-severity grid runs A (least serious) to L (most serious); J, K and L are Immediate Jeopardy.",
    citation=Citation(url="https://www.cms.gov/files/document/qso-23-01-nh-revised-2026-01-28.pdf",
                      title="CMS QSO-23-01", retrieved_at=...,
                      quote="..."),
)
```

**What this does and does not claim.** It **does** claim the wrong proposal is stopped from being auto-approved and, if a human approves it anyway, stays permanently enumerable as `unverified_semantics`. It **does not** claim the interface detects the inversion — nothing here reads the definition. **[Assumed]** that a human reviewing a `value_set` proposal with `evidence: []` and an assertion about ordering will go look. That assumption is the same rubber-stamping risk `WALKTHROUGH.md` names and 0.5 explicitly did not test.

### CMS verdict

**Expressible — after two changes to the surface as briefed, both taken in CMS's favour, plus one refusal to stretch.** `value_set` added as a kind; `not_a_type` added as a fourth `resolve_type` outcome; instance resolution declined and recorded as a gap. **Both conflicts were with Tenshen's needs, and CMS won both.**

---

## 10b. The NYC Open Data design test — three agencies, one word

*Added by roadmap row 3c, 2026-08-28 — the third use-case fixture (`docs/USE-CASES.md` UC3), run against v0 retroactively per standing constraint 7. Nothing in §§0–10 was rewritten to make this section come out better; every finding below is recorded, not designed away.*

**The subject [Observed 2026-08-28].** Three datasets from three publishing agencies on `data.cityofnewyork.us`, chosen because they share four column words. Full evidence, counts and reproduction commands: [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md).

| | dataset | agency | rows | `status` means |
|---|---|---|---|---|
| **A** | `uvpi-gqnh` | Department of Parks and Recreation (DPR) | 683,788 | `Alive` · `Stump` · `Dead` — the physical condition of an organism |
| **B** | `erm2-nwe9` | Office of Technology and Innovation (OTI), attributed `311` | 22,283,935 | `Closed` · `In Progress` · `Open` · `Pending` · `Assigned` · `Started` · `Unspecified` · `Cancel` — a workflow state |
| **C** | `693u-uax6` | Department of Transportation (DOT) | 15,598 | `Active` · `Inactive` · null · `active` — the service state of a fixed asset |

**No value appears in more than one of the three sets.** This is mechanism **4** — the `ROADMAP.md` kill row, the one **A1 assumes non-dominant** — exercised on real data for the first time.

**What v0 got right, and it is the load-bearing half.**

| | Behaviour | Result |
|---|---|---|
| §2.1, §2.6 | Three `status` entries coexist, scoped by `namespace`, unique per `(namespace, kind)` | **Pass.** Not one of the three had to give up its word |
| §5.10 #4 | `merge_types(namespace="dpr", into_namespace="oti_311")` | **Pass** — `Refusal(reason="cross_namespace_merge")`, and still refused with `acknowledge=["cross_namespace_merge", "definitions_diverge"]`. Non-overridable means non-overridable |
| §5.1 | `consumers(...)` reports `complete: False` with the registered-not-discovered `why` | **Pass** |
| §5.6 | `list_types(namespace=None, include_retired=True, status=None)` spans namespaces, `complete: True` | **Pass** — and it is the **only** call in §5 that can |
| §2.2 | `value_set` carries a per-agency value list | **Pass** — the kind CMS forced is what UC3 needs |

**The mechanism-4 answer §2.6 promised — *scope, do not merge* — holds.** The kill row does not trip. What UC3 found is one level in from there.

### 10b.1 CONTORTION 8 — `resolve_type` cannot see across namespaces, so the second publisher is never told the word is taken

**[Observed]**, against the reference implementation. With `dpr:status` already active:

```python
resolve_type("status", ctx_311, namespace="oti_311", tier="opus")
# -> outcome="proposal", confidence=None, alternatives=()
#    reason="nothing in the vocabulary fits 'status'"

resolve_type("status", ctx_311, namespace="dpr", tier="opus")     # same context
# -> outcome="existing", confidence=1.0
```

**The same question, the same evidence, two opposite answers — and the caller chose which one by picking a namespace before asking.** `resolve_type` takes `namespace: str` and scores against `find_types(namespace=<that one>)`. `alternatives` is drawn from the same scoped set, so the second publisher does not even get a near miss.

The `borough` case makes it sharper. With `dpr:borough` and `oti_311:borough` both active and **byte-identical in definition**:

```python
resolve_type("borough", ctx_dot, namespace="dot", tier="opus")
# -> outcome="proposal", alternatives=(("status", 0.1538),)
```

The one alternative offered is a same-namespace word at a 0.15 score — noise — while two exact matches sit one namespace away, unmentioned.

**This is mechanism 2 (nobody could find the existing types), reintroduced by the answer to mechanism 4.** §2.6 says the answer to collision is scoping. Scoping without a cross-namespace *lookup* means every publisher re-proposes every word, and the registry cannot say so.

> **FIXED by ruling R6, row 3e, 2026-08-29 — §5.3.1.** This paragraph used to end *"not fixed in v0, because the fix is a signature change to §5.3 … and v0 is not amended on a design test's say-so. Recorded as the first thing INTERFACE v1 must answer."* The ruling reversed the deferral rather than the reasoning: the fix is exactly the `search_namespaces: Sequence[str] | None` argument the deferral names, it is **additive and default-off**, and `v0` is labelled unstable so that additive amendments are cheap — waiting for v1 would have left the venture's kill-criterion fixture with its central finding open for a signature change nobody has to take. What did not change: the outcome is still decided inside one namespace, because resolving *across* them would be §2.6's answer to mechanism 4 deleting itself. `C3-12` drives this exact `status` case in both suites.

### 10b.2 CONTORTION 9 — nothing can say *these two mean the same thing, kept apart*

`borough` denotes the same five county-level divisions in all three datasets. The encodings differ (`Queens` / `QUEENS` / `Queens`, and B carries **two** spellings of unknown: the literal `Unspecified` and an absent field). The correct model is one concept, three scoped value sets.

v0 cannot express it. **[Observed]** the façade has seventeen public methods and `TypeEntry` fourteen fields; the relations available between two entries are:

- `merge_types` — destructive, and refused across namespaces by design (§5.10 #4);
- `aliases` — prior names **of the same entry**, not a pointer to another;
- `predicates` — capability membership, and §2.3 forbids reading it as a supertype;
- `retire(successor=…)` — one entry replacing another, which asserts the first is dead.

**Every cross-type relation v0 has asserts something stronger than equivalence.** So three identical `borough` definitions sit in three namespaces with nothing recording that a reader may join them, and the only enumerable trace is that `list_types(namespace=None)` returns three rows with the same word.

**Not fixed here, and the shape of the fix is not obvious**, which is why it is recorded rather than invented: an `equivalent_to` edge between scoped types is a *relationship between types*, and relationships between types are deliverable **#4** (`EDGES.md`). **UC3 is therefore evidence that #4 must carry type-to-type edges and not only instance-level ones** — a finding for #4's brief, delivered by a design test on #1.

### 10b.3 CONTORTION 10 — `not_a_type` has four reasons and a property column matches none of them

`latitude` is a column in all three datasets. It is not an entity, not a predicate, not an edge, and not an enumerated set.

```python
resolve_type("latitude", ctx, namespace="dot", tier="opus")
# -> outcome="proposal", confidence=0.4286
```

**[Observed]** a bare property becomes a proposal, and an approver who is not paying attention gets `latitude` in the vocabulary. §5.3's four `not_a_type` reasons — `redundant_projection`, `derived_value`, `export_artefact`, `instance_not_type` — describe **things derived from other columns**; none of them says *this is a property of a type, not a type*. `property_not_type` is the missing fifth value, and adding one would be a change to §5.3's closed reason set, so it is **recorded, not taken**.

Note what this is not: it is not the resolver being weak. A perfect resolver still has nowhere honest to put the answer.

### 10b.4 CONTORTION 11 — a consumer that gates on *values* has no representation, and the nearest expressible thing reports backwards

The UC3-shaped consumer is an operations dashboard that accepts only `Closed` and `In Progress` from B's `status`. §2.9's `Consumer.gate` is **a predicate name**, and a predicate's extent (§2.3) is a set of **types**. There is no value-level gate.

**[Observed]** what happens when a caller does the obvious thing and names the type:

```python
register_consumer(Consumer(id="ops_dashboard.open_requests", gate="status",
                           on_unknown="drop"), namespace="oti_311")
consumers("status", namespace="oti_311")
# -> known=1, complete=False, gates_on=[], would_drop=["ops_dashboard.open_requests"]
```

The registry reports that the consumer **would silently drop the very type it was registered to gate on**. That is internally correct — `status` names a predicate whose extent is empty, so the type is excluded and `on_unknown="drop"` puts it in `would_drop` — and it is exactly backwards to the reader. `C11-02` blesses gating on a predicate that does not exist *because that is mechanism C made visible*; here the same behaviour produces a confident wrong-looking answer.

**Recorded, not fixed.** The honest options are a value-level gate on `Consumer` (a change to §2.9, and it starts to make the registry know what a value is) or a documented rule that `gate` must name a registered `kind="predicate"` entry — which would break `C11-02`. **Neither is taken on a design test's authority. Ruling wanted; the recommendation is in [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.**

### 10b.5 CONTORTION 12 — the source's own version has no home in `Provenance`

`Provenance` (§2.4) records when **we** wrote the entry. A UC3 type is derived from a dataset that has its own `data_updated_at` — 2017-10-04 for A, 2026-08-28 for B, 2026-08-24 for C — and a type proposed from a 2017 snapshot of a "Historical data" dataset is a different claim from one proposed off a daily feed.

**[Observed]** the ten `Provenance` fields have nowhere for it. `Evidence.locator` takes the resource URL and `Citation.retrieved_at` takes *our* fetch time, which is close but is a fact about us. `imported_from` is documented as foreign *system* identifiers (Foundry `apiName`/`rid`). Using it for a dataset version is a stretch, and it was left `None`.

**Recorded.** The one-line fix — a `source_version: str | None` on `Provenance` — is additive and cheap, and is **not** taken here for the same reason as the rest: §11 collects it for v1.

### 10b.6 The two findings that are not contortions

**A. Value-level pollution inside one publisher is invisible, by design, and UC3 shows what that costs.** C's own `status` holds `Active`, `Inactive`, `active` and null — a case collision and an unencoded unknown, **inside one agency**. §2.1 says `attributes` is opaque and the registry never reads it, so **[Observed]** the value list round-trips verbatim with zero warnings. This is not a defect of §2.1; it is `PACKAGE.md` §5's job, and §5's `enforce` mode does catch the *shape* (a `value_set` with no declared values). It cannot catch `Active` vs `active`, and nothing in v0 claims to.

**B. Mechanism 2 arrives before the registry does.** **[Observed]** the catalogue's `columns_name` and the SODA API's field names disagree for all three datasets — A publishes `borough` in the catalogue and `boroname` in the API; C publishes `latitude` and serves `lat`. **The candidate word a proposer brings to `resolve_type` depends on which surface it read.** No registry call can fix that, and it is the strongest available argument that Phase 3's ingestion layer must record *which surface* a column name came from. Recorded here so #1 is not blamed for it later.

### 10b.7 NYC verdict

> **Expressible, with five recorded contortions (8–12), none designed away, and the mechanism-4 answer intact.** Scoping holds; the non-overridable `cross_namespace_merge` refusal holds; three publishers keep their word. **What UC3 broke is not collision handling — it is everything around it:** finding a scoped type (contortion 8), relating two of them (9), refusing a property (10), gating on a value (11), and dating a source (12).
>
> **The kill-criterion row does not trip.** §12's test — *would deleting `merge_types` leave the rest coherent?* — is if anything more true after UC3: the merge was refused three times out of three and nothing needed it.
>
> **UC3 conflicts with neither UC1 nor UC2.** Nothing recorded here contradicts the Tenshen or CMS design tests; every finding is an *absence* rather than a disagreement. Per `USE-CASES.md`'s conflict rule there is therefore nothing for the supervisor to resolve between fixtures — the four items wanting a ruling are all "amend v0 now, or collect for v1", and they are listed in [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.

---

## 11. What would change this

The partner conversations that A1–A3 stand in for. Each row names what arrives and what it re-opens.

| If the partner agency says… | Then | What changes here |
|---|---|---|
| **"Two teams mean different things by one word"** *is the main complaint* | **A1 is wrong and the `ROADMAP.md` kill row trips** | Stop. Re-centre on namespacing/scoping. `namespace` stops being an unused field and becomes required, with resolution scoped by default. `merge_types` should probably be **deleted**, not guarded |
| **"Plain duplicate sprawl, no predicate structure, no silent-drop problem"** | Tenshen was **not** representative | `resolve_type` reclaims the centre; §2.3's predicate machinery becomes Tenshen-specific weight the CMS consumer does not need. `consumers` still stands — 0.1's incident is real regardless |
| **"When someone adds a type, nothing tells you what breaks"** (i.e. C is confirmed at the partner agency) | A1's C clause is upgraded **[Assumed] → [Observed]** | Nothing changes structurally; `consumers` gains a second consumer of evidence, and §5.1's `complete: false` friction is confirmed as necessary rather than merely honest |
| **"There was an approval process and it did not help"** | Mechanism 1 is not the dominant one | The proposal→approval loop stops being the spine. Weight moves to `usage`/`retire` and to `consumers` |
| **"Types were retired, they just were not findable"** | Mechanism 3 out, mechanism 2 in | `resolve_type` and `list_types` become the spine; `retire`/`usage` demote to bookkeeping |
| **Q7a ruled *do-not-file*** (A4) | Tenshen's rot sensor is gone | `usage()` becomes the **only** evidence path for the venture's core bet — which contortion 2 says Tenshen currently cannot supply. `last_used_at` in beacon becomes load-bearing |
| **A5's relaxation is not confirmed** by the founder | 2A cannot gate 2B | Ordering changes, not this interface |
| **A domain expert says the proposals are organised wrongly** even when factually correct | 0.5's unmeasured Score 3 lands badly | The `Evidence`/`warnings` machinery is insufficient — the gap is in the *proposal*, not the registry, and Phase 3 is affected more than Phase 1 |

**Recorded by deliverable #3 (Phase 2A), 2026-08-28.** The reference implementation landed with **fourteen deviations, all in [`2A-RUN.md`](../runs/2A-RUN.md) §4** rather than silently resolved. Those that touch *this* document, for its next revision:

- **`TypeEntry.warnings` is not in §2.1's field table**, yet §5.4, §5.5 and §5.9 all describe returned entries carrying warnings and `PACKAGE.md` stores them. Implemented as a top-level field (D-3).
- **`Provenance` needs a `history_why`** — `PACKAGE.md` §3.4 primitive 15 requires an empty `history` to carry a `why`, and §2.4 has nowhere to put it (D-4).
- **`TypeListing` needs `excluded_unknown`** — `C6-05` requires the count of types excluded from an `orphaned=` filter *because their orphan state is unknown* to be reported, and §5.6's four fields cannot (D-5).
- **`Resolution.alternatives` is typed `tuple[str, float]`**, but §5.5 asks for a prior rejection to surface there and nothing scored it. Implemented as `tuple[str, float | None]`; `0.0` would be Rule U's forbidden zero (D-12).
- **`merge_types` takes one `namespace`**, which makes a cross-namespace merge unexpressible and refusal #4 unreachable. One additive keyword, `into_namespace` (D-7).
- **§2.5 states the Foundry status mapping but no §5 call performs it**, while `PACKAGE.md`'s C12 group tests it. Landed as `Registry.import_types`, a method beyond the fourteen (D-8).
- **`propose_type` and `reject` can return a `Refusal`** — required by `PACKAGE.md` §3.6 and §5.3, absent from §5.4 and §5.5's signatures (D-10).
- **The call count is corrected** *(row 3c, 2026-08-28)*. §5.10, §12 and §13 said *twelve*; enumerating §5.1–§5.11 gives **thirteen** — `consumers`, `predicates`, `resolve_type`, `propose_type`, `approve`, `reject`, `list_types`, `usage`, `provenance`, `retire`, `merge_types`, `register_consumer`, `record_use`. All three now say thirteen, and `PACKAGE.md` §2.2's counting note is resolved rather than carried forward. *(A fifth review round also found that §11 had been misciting itself: the twelve appeared in §5.10, §12 and §13, never in §0.)* **Row 3e makes it fourteen** — ruling **R11** adds `reinstate` (§5.9b), the first call added to this surface since v0 was written. Every place that carries the number was found with [`check_spec_drift.py`](../tools/check_spec_drift.py) and `grep`, not by eye, which is the lesson of the two rounds it took to get *thirteen* right.
- **D-11 — `propose_type` under `approval_policy="auto"` meeting the tier gate** returns a still-`pending` `Proposal` warning `auto_approval_refused:tier_below_auto_approve_policy`, which is neither of the two outcomes §5.4 and §2.7 describe. **Now documented in §5.4** *(added by row 3c after a third adversarial review round; it was recorded in `2A-RUN.md` and this list had failed to carry it forward, leaving §13's "a stated behaviour when uncertain" false for this call)*.

> **The drift this section keeps recording is now checked mechanically** *(row 3c, 2026-08-28)*. Six consecutive adversarial review rounds each found a printed shape or signature that had drifted from the reference implementation — `Resolution`, `predicates()`, `register_consumer`, `PredicateEntry.extent_size`, `MergeResult` (absent entirely), `merge_types`' `into_namespace`, `TypeEntry`'s last two fields. Every one was caught by a reader comparing two files by eye, and every one had survived earlier readers doing the same. [`docs/tools/check_spec_drift.py`](../tools/check_spec_drift.py) compares all fifteen printed shapes and all fourteen signatures against `types.py` and `registry.py`, and **found two more the moment it was written** — `Provenance.history_why` and `TypeListing.excluded_unknown`, both recorded as deviations below and both missing from the shapes above. The contract suite runs it, so this document cannot drift from the code again without the suite saying so.

**Recorded by roadmap row 3c (the UC3 validation pass), 2026-08-28.** §10b runs the NYC Open Data fixture — three agencies, one word, three meanings — against this document and records **five contortions (8–12), none designed away.** Those that this document must answer in v1, in the order they cost the most:

- **`resolve_type` cannot see across namespaces** (§10b.1). It takes `namespace: str` and scores against that namespace alone, so the second publisher of a word is never told the first exists — mechanism **2**, reintroduced by §2.6's answer to mechanism **4**. The smallest honest fix is an additive `search_namespaces: Sequence[str] | None` on §5.3 whose hits land in `alternatives` as `("<namespace>:<name>", score)`. **This is the first thing v1 must answer.**
- **Nothing says *equivalent, kept apart*** (§10b.2). Every cross-type relation v0 has — `merge_types`, `aliases`, `predicates`, `retire(successor=)` — asserts something stronger than equivalence. The fix is a type-to-type edge, which is **#4**, so UC3 is evidence that `EDGES.md` must carry edges *between types* and not only between instances.
- **`not_a_type` has no reason for a property** (§10b.3). `latitude` returns `outcome="proposal"`. `property_not_type` is the missing fifth value of §5.3's reason set.
- **`Consumer.gate` is a predicate name, so a consumer that gates on *values* cannot be expressed** (§10b.4) — and the nearest expressible thing reports that the consumer would drop the type it gates on. **Ruling wanted**; see [`findings/3C-VALIDATION.md`](../findings/3C-VALIDATION.md) §6.
- **`Provenance` has no `source_version`** (§10b.5). A type derived from a 2017 snapshot and one derived from a daily feed are different claims and record identically.

**Also open, independent of the partner agency:**

- **Instance resolution** (§10.3) has no home in any current deliverable. **[Inferred]** it belongs with Phase 3 ingestion, but nothing says so yet. **Founder ruling wanted.**
- **`attributes` is unversioned.** Everything v0 cannot type goes there. Without a schema-per-kind mechanism in #2, it will accumulate. **Named now so it is not discovered later.**
- **Tier ordering** (§2.7) assumes a total order per deployment. Mixed vendors may break it.

---

## 12. Kill-criterion check — required, and not skipped

**The brief's stop condition:** *"if while writing you find the design only makes sense if semantic collision across teams is the dominant mechanism, stop and report — do not ship a merge-centred shape."*

**Not tripped.** [Observed, from the shape of this document]

- `merge_types` is **1 of 14 calls** *(13 until row 3e)*, refuses by default, and carries **four non-overridable refusals** (§5.10). Deleting it entirely would leave the rest of the interface intact and coherent — which is the operational test of whether a design is merge-centred.
- The mechanism-4 answer here is **`namespace`** — *preserve* the distinction — not merge. §2.6.
- Nothing in §5 requires collision to be dominant. The spine is `resolve_type` → `propose_type` → `approve`/`reject`, which is mechanisms 1 and 2; the lifecycle half is mechanism 3; `consumers` is C.

**`ROADMAP.md`'s own kill row — "A capability predicate gets merged as a duplicate" — is structurally blocked**, not merely discouraged: refusal #2 in §5.10 is non-overridable, and `propose_type` deliberately does *not* refuse on near-duplicate (§5.4) precisely so that a locally-correct new predicate can be created rather than folded into an existing one.

---

## 13. Exit criteria — `ROADMAP.md` Phase 1, checked

| Criterion (verbatim) | Where |
|---|---|
| *Every call has a signature, a data shape, and a stated behaviour when uncertain* | §5.1–§5.11. **Thirteen** calls; each has all three, plus a named mechanism. `MergeResult`'s shape was added by row 3c — it was the one missing |
| *The document names which of Phase 0's mechanisms it is designed against* | §6, against **A1** (1 + 3 dominant, 4 minor, C present-unobserved), with per-call labels throughout §5 |
| *`v0` and "unstable" appear in the header* | Header, line 3 |
| *Tenshen's `work_link_types` can be expressed in it without contortion — or the contortion is recorded* | §9. **Expressible with seven recorded contortions**, two structural. None designed away |

**Additionally, beyond the criteria:** §10 records **two CMS-forced changes to the surface as briefed** (`value_set`, `not_a_type`), both resolved in CMS's favour over Tenshen's needs — Phase 2's exit criterion ("the interface changed at least once") arriving in Phase 1.
