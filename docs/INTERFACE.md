# INTERFACE — the type-registry contract

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a deprecation path. Standing constraint 4: an interface labelled unstable is cheap to replace; one two codebases quietly assume is permanent is not.
**Status:** Draft, 2026-08-28. Satisfies `ROADMAP.md` Phase 1. Deliverable #1 of the Tenshen-rebuild ordering.
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md), assumption **A1**. If A1 is wrong, this document is wrong in the way §11 describes.
**Evidence inputs:** [`FINDINGS-0.1-tenshen-archaeology.md`](FINDINGS-0.1-tenshen-archaeology.md) (forced `consumers` and `predicate`) · [`0.5-RESULTS.md`](0.5-RESULTS.md) (forced model tier and external-doc evidence) · [`0.3-prior-art.md`](0.3-prior-art.md) (forced the status vocabulary and the refusal to copy `register_*`) · [`WALKTHROUGH.md`](WALKTHROUGH.md) (the flow this must serve).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

---

## 0. What this is, in three sentences

A registry of **types** — the vocabulary a system uses to say what things *are* — with a proposal→approval loop around every addition, a lifecycle for every entry, and a mechanical answer to *"if I add this, what will silently ignore it?"*

It is not a schema store and it is not a graph. It holds names, definitions, provenance, lifecycle and consumer registrations; **it does not hold instances, edges, storage, or transport.**

**No single call is the centre.** Per A1, the centre is the **proposal→approval loop**: `resolve_type` → `propose_type` → `approve`/`reject`, with `consumers`, `usage`/`retire` and `provenance` all first-class around it.

---

## 1. Non-goals — one line each

- **No storage.** No tables, no SQL, no migrations, no adapter protocol. → deliverable **#2, `docs/PACKAGE.md`**.
- **No HTTP.** No routes, no auth, no pagination-over-the-wire. → **#2**.
- **No package layout.** No module names, no `pip` name, no conformance test suite. → **#2**.
- **No relationships or edges.** No `neighbors()`, no traversal, no edge storage — a *relationship type* can be registered here as a type, but the edges themselves are → deliverable **#4, `docs/EDGES.md`**.
- **No actions.** Action types are deliverable **#6** and Tenshen's actions stay in code (beacon spec §10.7).
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
| `created_by` | `"seed" \| "ai" \| "user"` | yes | Where the vocabulary came from. Field name and values taken deliberately from Tenshen's `work_link_types` (§9) |
| `provenance` | `Provenance` | yes | §2.4 |
| `status` | `"proposed" \| "active" \| "retired"` | yes | §2.5 |
| `usage` | `UsageReport` | yes | §5.7 — may be entirely unknown, never fabricated |
| `consumers` | `ConsumerReport` | yes | §5.1 — **always** carries `complete: false` in v0 |
| `predicates` | `list[str]` | yes | Names of `kind="predicate"` entries this type satisfies. May be empty |
| `attributes` | `dict[str, Any]` | yes | Kind-specific payload, **opaque to v0**. Defaults `{}`. The escape hatch that keeps v0 from pretending to know what an edge needs |
| `aliases` | `list[str]` | no | Prior names, and identifiers imported from elsewhere (a Foundry `apiName`/`rid` lands here or in `provenance.imported_from`, per 0.3 consequence 3) |

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
- **`merge_types` refuses predicate merges outright** unless the two extents are byte-identical (§5.10).

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
    history:           list[ProvenanceEvent]   # append-only; nothing here is ever rewritten
```

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

### 2.9 `Consumer` — a registered code path that gates on a predicate

```
Consumer:
    id:          str         # "aura_render.referent_link", "comment_service.can_comment"
    gate:        str         # the predicate name it gates on
    on_unknown:  "drop" | "error" | "passthrough"
    owner:       str | None
    registered_at: datetime
    locator:     str | None  # file:line, so a human can go look
```

`on_unknown="drop"` is the dangerous value and it is the **[Observed]** default behaviour of every one of Tenshen's seven allowlists. It is what makes a new type die silently.

---

## 3. Two global rules that apply to every call

**Rule U — uncertainty is a value, never a default.** No call returns a confident answer in place of an unknown one. Unknown is `None` plus a `why: str`. Never `False`, never `0`, never an empty list standing in for "we did not look".

**Rule K — every list result carries `complete: bool` and a `known: int`.** Per `WALKTHROUGH.md`'s risk row: *"Only claim consumers the registry can enumerate mechanically. Never infer one. Show '3 known, may be others' rather than '3'."* In v0, `ConsumerReport.complete` is **always `false`** — see §5.1.

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
```

**Designed against: mechanism C.** This is the call that would have prevented the only documented Tenshen incident — `capture` began being emitted, `aura_render` gated on a list that excluded it, `on_unknown` was effectively `drop`, and the feature was dead for exactly the watch kind that had just started working.

**Behaviour when uncertain.** `complete` is **always `false` in v0**, unconditionally, even when every consumer in a system is registered — because the registry cannot know that it is. A caller rendering `WALKTHROUGH.md` step 5 must therefore print *"3 known, there may be others"* and has no way to print *"3"*. **This is deliberate friction.** An impact list that misses a consumer is more dangerous than no list, because it promises safety it cannot deliver.

**Unknown type:** raises `UnknownType`, never returns an empty report — an empty report reads as *"nothing gates on this"*, which is the exact false reassurance this call exists to prevent.

---

### 5.2 `predicates` — the named capability sets

```python
def predicates(
    *,
    of: str | None = None,          # if given, only predicates this type satisfies
    namespace: str = "default",
    include_retired: bool = False,
) -> list[PredicateEntry]: ...
```

```
PredicateEntry:
    name:        str
    definition:  str
    extent:      list[str]       # type names satisfying it — DERIVED, never stored twice
    extent_size: int
    consumers:   list[Consumer]  # consumers gating on this predicate
    status:      "proposed" | "active" | "retired"
    provenance:  Provenance
```

**Designed against: mechanism 4, defensively — and the kill-criterion row.** Predicates are the structure that stops five locally-correct lists from being read as five duplicates.

**Behaviour when uncertain.** If a predicate's extent cannot be computed (a backend that cannot index membership), return `extent: []` **with `extent_size: None`** and a `why` — never `extent_size: 0`, which reads as *"nothing is commentable"*.

---

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
```

**Designed against: mechanism 2** (nobody could find the existing types), and **mechanism 1** as the gate in front of `propose_type`.

**The four outcomes:**

- **`existing`** — a registered type fits. `confidence` is set.
- **`proposal`** — nothing fits and the candidate looks like a real type. Returns an un-persisted `Proposal`; nothing is written.
- **`not_a_type`** — the candidate is real but is **not a type**: a redundant projection of an existing one, a derived value, an export artefact. `reason` names which. **This outcome was forced by the CMS data; see §10.1.**
- **`none`** — cannot tell. Not "no match" — *cannot tell*.

**Behaviour when uncertain — the rule this call exists for.** Below `min_confidence`, return `none` with `alternatives` populated. **Never** return the best of a bad set as `existing`. Tenshen's classifier already does the caller-side version of this — a low `fit_score` on an existing type means the classifier was shoehorning, so it falls back rather than mislabel — and that policy is **[Observed]** to be correct. v0 puts the *detection* in the registry and leaves the *fallback* to the caller (§9, contortion 7).

**`confidence: None` ≠ `confidence: 0.0`.** `None` means no scorer ran. Rule U.

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
    warnings:      list[str]          # "unverified_semantics", "no_evidence", "near_duplicate:<name>"
    near_matches:  list[tuple[str, float]]
```

**Designed against: mechanism 1** (no review). This is the call that makes an addition a *request* rather than a fact — and it is precisely why 0.3 says **do not copy `foundry-ontology-open`'s `register_object_type`**: a declaration API cannot return a proposal, because it has already decided.

**Returns `TypeEntry` instead of `Proposal`** only when the namespace policy is `approval_policy="auto"` — in which case `provenance.approved_by == "auto:<policy>"`, never blank. See §9 contortion 4.

**Behaviour when uncertain:**
- Empty `definition` → **reject**, `ValueError`. A type without a definition is how collision starts.
- Name already taken in `(namespace, kind)` → return the **existing** `TypeEntry`. Not an error; the proposer's question is answered.
- `near_matches` above a threshold → still returns a `Proposal`, with `warnings: ["near_duplicate:<name>"]`. **v0 does not refuse on near-duplicate** — refusing is how you flatten a capability predicate (§2.3).
- `evidence == []` → `warnings: ["no_evidence"]`, proposal still created. An honest empty is better than a fabricated citation.
- `proposed_by` starts with `"ai:"` and `tier` is `None` → **reject**, `ValueError`. Per §2.7 an unattributed machine proposal is not acceptable.

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
```

**Designed against: mechanism 1.** Approval is the review that A1 says HHS never had.

**Why `reject` requires a non-empty `reason`, and why rejections are kept.** A rejected proposal is the cheapest record of *"we already considered this word and decided against it"*. Discard it and the next proposer re-proposes it in six months — which is mechanism 2 wearing mechanism 1's clothes. `resolve_type` **should** surface a matching prior rejection in `alternatives`.

**Behaviour when uncertain:**
- `mode="auto"` and the proposal's `tier` is below the namespace's `min_auto_approve_tier` → **`Refusal`**, not an exception. The caller may escalate to a human. This is 0.5 consequence 2 made operational.
- Proposal already decided → `Refusal(reason="already_decided")`. Idempotent, not an error.
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
    known:    int
    complete: bool
    why_incomplete: str | None
```

**Designed against: mechanism 2** — this is the call whose absence means "nobody could find the existing types". The `predicate=` filter is how a caller reads a capability set without flattening it.

**Behaviour when uncertain.** `include_retired=False` is the default *and hides things*, so `TypeListing` always reports `known` over the returned set and `complete: false` whenever any filter suppressed rows. A caller that wants a true census passes `include_retired=True, status=None, namespace=None`.

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

**Designed against: mechanism 3.** A1 assumes never-retired is co-dominant at HHS; this is the call whose absence is that mechanism.

**Behaviour when uncertain — retirement is guarded by `consumers`, not by usage.**

- If `consumers(type).gates_on` is non-empty → **`Refusal(reason="live_consumers", detail={"gates_on": [...]})`**. `force=True` overrides and records the override in `history`.
- If `usage(type).orphaned is None` — i.e. we cannot tell whether it is dead → retirement **still proceeds**, because retiring is reversible-ish and reason is recorded. But the returned entry carries `warnings: ["retired_without_usage_evidence"]`.
- **A retired name is not reusable.** `propose_type` with a retired name returns the retired entry with `warnings: ["name_previously_retired"]` and requires an explicit `reinstate` decision by the approver. Silently reusing a retired word is mechanism 4 with a time delay.

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
    acknowledge: list[str] = (),      # explicit acknowledgement of named guard warnings
) -> MergeResult | Refusal: ...
```

**Designed against: mechanism 4 — and constrained by 0.1 to the point of near-uselessness, deliberately.**

**It MUST refuse when the two have different consumer sets.** Verbatim from `ROADMAP.md` Phase 1. If `consumers(from_)` and `consumers(into)` differ in their `gates_on` sets, merging asserts that every consumer of one accepts the other — which is exactly the false claim 0.1 describes.

**Full refusal list, in order:**

| # | Refusal | `reason` | Overridable? |
|---|---|---|---|
| 1 | Consumer sets differ | `different_consumer_sets` | **No.** Not by `force`, not by `acknowledge` |
| 2 | Either side has `kind="predicate"` and extents are not byte-identical | `predicate_merge` | **No.** This is the `ROADMAP.md` kill row |
| 3 | Different `kind` | `kind_mismatch` | No |
| 4 | Different `namespace` | `cross_namespace_merge` | No — cross-namespace collision is what namespaces exist to *preserve*, not resolve |
| 5 | Either side `retired` | `retired_operand` | Via `acknowledge=["retired_operand"]` |
| 6 | Definitions are not near-synonymous by the resolver | `definitions_diverge` | Via `acknowledge=["definitions_diverge"]`, recorded in history |

**Behaviour when uncertain.** If `consumers()` cannot be computed for either side — which, since `complete` is always false (§5.1), means *always* in the strict reading — v0 takes the weaker rule: refuse when the **known** consumer sets differ, and when both are empty, return `Refusal(reason="no_consumer_evidence")` with `acknowledge=["no_consumer_evidence"]` available. **Merging two types about which nothing is known is the single most destructive thing this interface can do**, so it is the one place where "we do not know" blocks rather than warns.

**Kill-criterion note.** `merge_types` is 1 of 12 calls, refuses by default, and has four non-overridable refusals. **This is not a merge-centred design.** See §12.

---

### 5.11 Two calls the surface implies but did not name

`usage` and `consumers` cannot answer anything unless something writes to them. Naming these is not scope creep — omitting them would make §5.1 and §5.7 unimplementable.

```python
def register_consumer(consumer: Consumer, *, namespace: str = "default") -> Consumer: ...
def record_use(type: str, *, by: str | None = None, at: datetime | None = None,
               namespace: str = "default") -> None: ...
```

`record_use` is explicitly allowed to be a no-op in a backend that does not count — in which case `usage()` returns `count: None`, per Rule U. **v0 does not specify how a consumer gets registered** (decorator, config, lint, manual). That is #2's problem, and beacon's Q7a lint (assumption A4) is one candidate mechanism.

---

## 6. Which mechanism this is designed against

**Against A1** ([`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md)): *HHS's dominant mechanism is **1 + 3 together** — anyone could add a type with no review, and nothing was ever retired — with contractor rotation as the named cause. Collision (4) is present but not dominant. Silent per-consumer drop (C) is present but unobserved by the office, because no existing tool surfaces it.*

| Mechanism | Status under A1 | The calls that answer it |
|---|---|---|
| **1** no review | **Dominant** | `propose_type` → `approve`/`reject`; `Provenance.approved_by`; the tier gate on auto-approval |
| **3** never retired | **Dominant** | `usage` (count / last_seen / orphaned), `retire`, `list_types(orphaned=True)` |
| **2** could not find | Enabling condition | `resolve_type`, `list_types`, retained rejections |
| **C** silent drop | **Present, unobserved — and forced into the design by direct evidence** | `consumers`, `predicates`, `Consumer.on_unknown` |
| **4** collision | Present, not dominant | `namespace` (preserve), `merge_types` (refuse), predicate protection |

**None of these is "the centre".** A1 states it plainly: *"No single call is 'the centre'; the centre is the proposal→approval loop."* This document is built that way — `resolve_type` → `propose_type` → `approve`/`reject` is the spine, and `consumers`, lifecycle and provenance hang off it as equals.

**Two of these stand regardless of what the office says.** Finding 0.1 §"What this changes": `consumers` was forced by a real production incident and `predicate` by five real vocabularies. **HHS cannot make them unnecessary.** Everything else in the table is contingent on A1.

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

**CMS wins any conflict with Tenshen** (brief; `ROADMAP.md` "Rule of the ordering"). The entities are the pre-registered ground truth from [`0.5-ground-truth-PREREGISTERED.md`](0.5-ground-truth-PREREGISTERED.md) plus the fourth entity the Opus run added and [`0.5-RESULTS.md`](0.5-RESULTS.md) recorded as **better than the ground truth**.

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

## 11. What would change this

The office visits that A1–A3 stand in for. Each row names what arrives and what it re-opens.

| If the office says… | Then | What changes here |
|---|---|---|
| **"Two teams mean different things by one word"** *is the main complaint* | **A1 is wrong and the `ROADMAP.md` kill row trips** | Stop. Re-centre on namespacing/scoping. `namespace` stops being an unused field and becomes required, with resolution scoped by default. `merge_types` should probably be **deleted**, not guarded |
| **"Plain duplicate sprawl, no predicate structure, no silent-drop problem"** | Tenshen was **not** representative | `resolve_type` reclaims the centre; §2.3's predicate machinery becomes Tenshen-specific weight the CMS consumer does not need. `consumers` still stands — 0.1's incident is real regardless |
| **"When someone adds a type, nothing tells you what breaks"** (i.e. C is confirmed at HHS) | A1's C clause is upgraded **[Assumed] → [Observed]** | Nothing changes structurally; `consumers` gains a second consumer of evidence, and §5.1's `complete: false` friction is confirmed as necessary rather than merely honest |
| **"There was an approval process and it did not help"** | Mechanism 1 is not the dominant one | The proposal→approval loop stops being the spine. Weight moves to `usage`/`retire` and to `consumers` |
| **"Types were retired, they just were not findable"** | Mechanism 3 out, mechanism 2 in | `resolve_type` and `list_types` become the spine; `retire`/`usage` demote to bookkeeping |
| **Q7a ruled *do-not-file*** (A4) | Tenshen's rot sensor is gone | `usage()` becomes the **only** evidence path for the venture's core bet — which contortion 2 says Tenshen currently cannot supply. `last_used_at` in beacon becomes load-bearing |
| **A5's relaxation is not confirmed** by the founder | 2A cannot gate 2B | Ordering changes, not this interface |
| **A domain expert says the proposals are organised wrongly** even when factually correct | 0.5's unmeasured Score 3 lands badly | The `Evidence`/`warnings` machinery is insufficient — the gap is in the *proposal*, not the registry, and Phase 3 is affected more than Phase 1 |

**Also open, independent of the office:**

- **Instance resolution** (§10.3) has no home in any current deliverable. **[Inferred]** it belongs with Phase 3 ingestion, but nothing says so yet. **Founder ruling wanted.**
- **`attributes` is unversioned.** Everything v0 cannot type goes there. Without a schema-per-kind mechanism in #2, it will accumulate. **Named now so it is not discovered later.**
- **Tier ordering** (§2.7) assumes a total order per deployment. Mixed vendors may break it.

---

## 12. Kill-criterion check — required, and not skipped

**The brief's stop condition:** *"if while writing you find the design only makes sense if semantic collision across teams is the dominant mechanism, stop and report — do not ship a merge-centred shape."*

**Not tripped.** [Observed, from the shape of this document]

- `merge_types` is **1 of 12 calls**, refuses by default, and carries **four non-overridable refusals** (§5.10). Deleting it entirely would leave the rest of the interface intact and coherent — which is the operational test of whether a design is merge-centred.
- The mechanism-4 answer here is **`namespace`** — *preserve* the distinction — not merge. §2.6.
- Nothing in §5 requires collision to be dominant. The spine is `resolve_type` → `propose_type` → `approve`/`reject`, which is mechanisms 1 and 2; the lifecycle half is mechanism 3; `consumers` is C.

**`ROADMAP.md`'s own kill row — "A capability predicate gets merged as a duplicate" — is structurally blocked**, not merely discouraged: refusal #2 in §5.10 is non-overridable, and `propose_type` deliberately does *not* refuse on near-duplicate (§5.4) precisely so that a locally-correct new predicate can be created rather than folded into an existing one.

---

## 13. Exit criteria — `ROADMAP.md` Phase 1, checked

| Criterion (verbatim) | Where |
|---|---|
| *Every call has a signature, a data shape, and a stated behaviour when uncertain* | §5.1–§5.11. Twelve calls; each has all three, plus a named mechanism |
| *The document names which of Phase 0's mechanisms it is designed against* | §6, against **A1** (1 + 3 dominant, 4 minor, C present-unobserved), with per-call labels throughout §5 |
| *`v0` and "unstable" appear in the header* | Header, line 3 |
| *Tenshen's `work_link_types` can be expressed in it without contortion — or the contortion is recorded* | §9. **Expressible with seven recorded contortions**, two structural. None designed away |

**Additionally, beyond the criteria:** §10 records **two CMS-forced changes to the surface as briefed** (`value_set`, `not_a_type`), both resolved in CMS's favour over Tenshen's needs — Phase 2's exit criterion ("the interface changed at least once") arriving in Phase 1.
