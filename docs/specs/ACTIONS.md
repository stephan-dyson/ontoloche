# ACTIONS — governed actions over the registry and the edge store

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a deprecation path. Standing constraint 4.
**Status:** Draft, 2026-08-29. Satisfies `ROADMAP.md` row **#6**. Unblocks nothing in the Tenshen rebuild — beacon's actions stay in code (beacon spec §10.7) and this document is deliberately written so that they can stay there.
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md).
**Rulings this document carries:** **R20** (`model_tier` on provenance; no tier gate in *storage* — the gate here is a declared product parameter, §5.2) · **R24** (no tenancy dimension in the protocol) · **R25** (paging is Phase 3's, decided for every listing together) · **R18** (exactly one cross-field attribute rule per kind, and this document takes exactly one) · **R31** (every numbered rule ships executable — standing constraint 8, §14) · **R3** (`Refusal.reason` is closed — **seven** values added to [`INTERFACE.md`](INTERFACE.md) §5.12 by this change, and **three** warning values to §5.4; the header said *six* and *one* until round 2 counted it, which is the self-accounting failure §19.2 records twice).
**Claim tags:** **[Observed]** seen directly · **[Inferred]** a reasonable read · **[Assumed]** believed, untested.

**This row is a spec and ships no action store.** The design tests in §11–§13 are driven through real beacon, CMS and NYC data by four throwaway probes in [`docs/tools/`](../tools/), the way row #4's were — not read. The build row owns the contract ids §14 plans.

---

## 0. What this is, in three sentences

A registry of **action families** — the governed verbs a system exposes, the way [`INTERFACE.md`](INTERFACE.md) holds the governed nouns and [`EDGES.md`](EDGES.md) the governed relationships — each declaring its inputs, what must be true before it runs, what it is permitted to change, and whether it can be undone.

It is not an executor and not a scheduler. **The registry records and gates; the host runs.** Nothing here dispatches a call, retries one, orders two, or holds a queue.

**No single call is the centre.** The centre is the same proposal→approval loop `INTERFACE.md` §0 names, applied one level up: a new *verb* is a request, resolved against the verbs that already exist, approved by a human — and then every *use* of it leaves an append-only record saying who invoked it, on what tier, what it declared it would change, and what it actually changed.

---

## 1. Non-goals — one line each

- **No executor.** Nothing here calls a function, spawns a job or owns a thread. `preflight` answers a question and `record_invocation` files a report; between them the host does the work.
- **No scheduler.** No queue, no retry policy, no ordering, no idempotency key, no saga. An action that must run after another is the host's sequencing problem, and inventing a dependency graph here would be building the pipeline orchestration engine `VISION.md` §6 names as a non-goal.
- **No rollback engine.** `reversibility` is a **declaration**, not a mechanism: this document records that an action was compensable and that a compensating invocation ran. It does not run one.
- **No query language.** Preconditions are evaluated through `resolve_type`, `predicates` and `neighbors` — three calls that already exist — and §2.4 closes the vocabulary rather than opening a predicate grammar. Same boundary `INTERFACE.md` §10b.4 and ruling **R22** hold for `Consumer.gate`.
- **No permissions model.** *Who may* invoke an action is authorization, it is the host's, and **R24** already says the protocol carries no tenancy dimension. What this document holds is *what the action is allowed to change*, which is a different question and the one a registry can actually answer.
- **No tool transport.** No MCP, no JSON-Schema emission, no function-calling wire format. §10 specifies how a host *projects* families into a bounded tool array and stops there.
- **No instance resolution.** Unchanged from `INTERFACE.md` §1: an `InstanceRef` names an id the host already has. Resolving *"the Burns nursing home"* to a CCN is Phase 3's.

---

## 2. The action model

### 2.1 The action family **is** a `TypeEntry` with `kind="action"` — a fifth kind, not a sixth, and not a predicate

[`EDGES.md`](EDGES.md) §2.3 argued that an edge family is the `kind="edge"` that `INTERFACE.md` §2.2 *already defined*. **The parallel argument here is weaker in one specific way, and it has to be said first: `action` is not one of §2.2's four kinds.** This document adds a kind value. `INTERFACE.md` §2.1 types `kind` an **open vocabulary** — *"Open vocabulary. v0 defines four"* — and §2.1 records that `C16-05` checks `created_by` and `status` while **`kind` is deliberately not checked**. So adding `action` costs no amendment and trips no gate.

**That cheapness is the problem, not the licence.** A vocabulary anything may extend for free is mechanism **1** — *anyone could add a type, no review* — and this project's thesis is that a free-for-all is how a vocabulary rots. So the argument is made on the shape of the thing rather than on the absence of a gate.

**Why `action` is a kind at all.** [`EDGES.md`](EDGES.md) established a pattern this is the third instance of: **a family is a row of the vocabulary; its instances live in a store beside the registry.** An `entity` family's instances are the host's rows and are not stored here at all (`INTERFACE.md` §1). An `edge` family's instances are edges and live in the edge store (`EDGES.md` §7). An `action` family's instances are **invocations** and live in an invocation store (§8). One pattern, three kinds, and the third needs no new machinery to be understood by anyone who has read the second.

**Why not `predicate`.** `INTERFACE.md` §2.3 is explicit: a predicate is *a named capability set* whose **members are types** and whose extent is `list_types(predicate=…)`. `delete_person` has no extent of that shape — its instances are events, not types. And `merge_types` refuses predicate merges non-overridably (§5.10 refusal #2), which would make two genuinely duplicate action families unmergeable for a reason having nothing to do with actions. Both halves are `EDGES.md` §2.3's argument unchanged, and they are unchanged because the objection is the same objection.

**Why not `entity`.** An action is not a thing that exists; it is a thing that happens. Registering `delete_person` as an `entity` puts a verb in the noun list, and `resolve_type("person")` then has to score a verb against a noun. That is `INTERFACE.md` §2.3's **Cause B** — one container meaning two things — arriving in the call whose entire job is telling a proposer what already exists.

**Why not a SIXTH kind — the question the brief asks by name.** Two candidates, both refused:

- **`invocation` as a kind.** An invocation is a *record*, not a word in the vocabulary. `PACKAGE.md` §5.2 made this exact call about `AttributeSchema` and rejected the dogfooding option for exactly this reason: putting a non-vocabulary object in `oo_type` means `list_types()` mixes records with words and `merge_types` can be pointed at one. An `Edge` is not a kind either. **Consistency here is not tidiness; it is the difference between `list_types()` answering *"what words do we use?"* and answering *"what happened lately?"***
- **`action_family` beside `action`.** Two words in the registry's own `kind` vocabulary for one concept — the Cause B objection `EDGES.md` §2.3 makes against `edge_family`, no better one row later.

**What this buys, free and unchanged** — and this table is the whole architectural bet, exactly as it was for edges:

| From INTERFACE | What it means for an action family |
|---|---|
| `propose_type` → `approve`/`reject` | **a new verb is a request, not a fact** — mechanism **1**, at the layer where the blast radius is largest |
| `resolve_type` | a proposer is told `flag_facility_for_review` exists before inventing `mark_facility_for_review` — mechanism **2** |
| `usage` / `retire` / `list_types(orphaned=True)` | a verb nobody has invoked in a year is enumerable, and retiring one is a lifecycle event rather than a deletion — mechanism **3** |
| `namespace` | two agencies may both have `close` and mean different things — mechanism **4** |
| **`consumers` / `predicates`** | **which surfaces expose this family, and which would silently drop a new one — mechanism C, and §10 is where that becomes the tool-slot answer** |
| `Provenance`, `Evidence`, `model_tier` | *which model proposed this verb, on what evidence, and did a human approve it* |
| `reinstate` (**R11**/**R19**) | a retired verb has a specified way back, and by R19's own reasoning it covers families, because a family is a `TypeEntry` |

**No new call in `INTERFACE.md` §5 is required to manage families, and this document adds none.** That is the test `EDGES.md` §2.3 set for itself and it passes for the same reason. The four calls in §6 are this document's own, about *invocations*, exactly as `neighbors` and `add_edge` are `EDGES.md`'s own and about edges.

**What would change this.** If a family ever needs a field the registry itself must **read** — not store, not validate, but read in order to decide what to do — then `kind="action"` has stopped being a word and wants its own table. §2.5's `effects` is the field closest to that line, and §2.5 stays on the near side of it deliberately: the registry reads `effects` to *refuse a declaration* and to *compare against what the host reports*, never to decide what to run.

### 2.2 The family's declared shape

Eight keys, all in `TypeEntry.attributes`, all governed by one `AttributeSchema` keyed `(namespace, kind="action")` — `PACKAGE.md` §5.2's mechanism, with **R10**'s name-level shadowing (§5.2b) available for a family whose inputs need their own schema.

| key | type | meaning |
|---|---|---|
| `inputs` | `list[InputSpec]` | the typed references the action takes. **Required**, may be empty. §2.3 |
| `preconditions` | `list[Precondition]` | what must be true before it runs, in a closed four-kind vocabulary. **Required**, may be empty. §2.4 |
| `effects` | `list[Effect]` | the registry and edge operations it is permitted to perform. **Required**, may be empty. §2.5 |
| `reversibility` | `"reversible" \| "compensable" \| "irreversible"` | **Required.** No default: a family that does not say is a family whose gate cannot be set. §2.6 |
| `approval_mode` | `"auto" \| "review" \| "human"` | **Required.** Who must sign off on an *invocation*. §5.2 |
| `min_auto_tier` | `str \| None` | the lowest model tier whose invocations may be auto-approved. Opaque string, `INTERFACE.md` §2.7's posture. §5.2 |
| `reachability` | `list[str]` | the host surfaces that expose this family. Opaque strings. **Required**, and an **empty list is a positive declaration** — *this host exposes me on no named surface* — not a forgotten field. §10 |
| `payload_schema` | `str \| None` | the name of an `AttributeSchema` governing `Invocation.inputs`. §2.7 |

**`created_by` is not in this list** and neither is `namespace`: both are `TypeEntry`'s, already required by `INTERFACE.md` §2.1. Restating either in `attributes` would be a second home for one fact — `EDGES.md` §2.4's rule, repeated here rather than the mistake.

**Why eight and not five.** [`EDGES.md`](EDGES.md) §2.4 took five and treated the restraint as evidence its §2.3 decision was right. Eight is more, and three of the eight are the reason:

- `approval_mode` and `min_auto_tier` are **policy**, and `INTERFACE.md` §2.7 puts the type-side equivalent (`min_auto_approve_tier`) on the **namespace**, not the entry. They are per-family here because **an action's blast radius does not vary by namespace, it varies by action**: `search_tasks` and `delete_person` sit in one namespace **[Observed, beacon]** and share nothing a namespace-level tier gate could express. This is a deliberate departure from §2.7's shape; §5.2 argues it and §16 carries the question.
- `reachability` exists because §10's ceiling is real arithmetic on a real product **[Observed]** rather than a hypothetical, and there is nowhere else for it to live.

**Cross-field rules: one, in the shape R18 licensed.** Ruling **R18** accepted `symmetric ⇒ inverse_label is None` as *"the single cross-field rule `approve()` knows about `kind="edge"` attributes"* — explicitly narrowly, explicitly because a rule language is not v0's problem. This document takes exactly one for `kind="action"`:

> **`reversibility="irreversible"` ⇒ `approval_mode` MUST be `"human"`.** A family declaring that it cannot be undone *and* that a model may run it unattended has written the failure mode this project exists to prevent into its own configuration. Refused at declaration with **`attributes_schema_violation`**, not with a value of its own.

> **The refusal value is R18's own, and the first draft got it wrong.** `PACKAGE.md` §5.6 records R18 as *an exception list of length one inside the attribute-schema mechanism*, and the shipped `edges.family_declaration_problem` returns `attributes_schema_violation` for exactly this shape — *"neither needed a new value; `INTERFACE.md` §5.12 stays at twenty-one"*. This document minted `human_approval_required` for it, which would have made two instances of one ruling return two different reasons. **Found by round 1's integrator lens** (§19); `PACKAGE.md` §5.6's exception list goes to **length two**, one rule per kind, which is the shape R18 licensed. `human_approval_required` survives for the *invocation* door only (§5.2), where it is about an approver rather than about a declaration.

Two candidate second rules were considered and **not** taken, because two is where an exception list becomes a grammar:

- *`effects == []` ⇒ `reversibility` must be `reversible`.* Tempting and wrong: an action with no declared **protocol** effects may still change host state (§2.5's `host_state`), so the antecedent does not imply the consequent. The real check is at record time and it is `effect_undeclared` (§7).
- *`approval_mode="auto"` ⇒ `min_auto_tier is not None`.* Almost right, and left out deliberately: a deployment running a single model tier has nothing to compare against, and forcing it to invent a tier string is how `model_tier`'s opaque-string posture (`INTERFACE.md` §2.7) gets quietly turned into a required ordering nobody defined. It is a **warning**, not a rule — §5.2.

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 2.2-1 | **A `kind="action"` entry that declares none of the eight keys is a legal `TypeEntry` and is NOT refused.** It is simply not yet usable as an action family, and `preflight` / `record_invocation` refuse on it with `attributes_schema_violation`. Refusing the *registration* would reject entries `INTERFACE.md` §2.1 says are legal — `edges.family_declaration_problem`'s own recorded decision for the identical case one kind along | `C19-26` |
| 2.2-2 | A family that declares **some** of the eight must declare `reversibility` and `approval_mode`, and each must be a value of its closed vocabulary; a fourth `approval_mode` or a fifth `reversibility` is `attributes_schema_violation`, never a bare exception | `C19-27` |
| 2.2-3 | The one cross-field rule, in **R18**'s shape: `reversibility="irreversible"` ⇒ `approval_mode` MUST be `"human"`, refused at declaration with **`attributes_schema_violation`** — R18's own value, not a new one | `C19-28` |
| 2.2-4 | Every declaration rule binds at **all three** shipped doors — `propose_type`, `approve` and `import_types` — because *a rule with one enforcement point is a rule with one door left open*. On the `import_types` path a `Refusal` is not returnable, so the entry is not written and the caller gets `import_refused:<reason>` | `C19-44` |
| 2.2-5 | `created_by` and `namespace` are `TypeEntry`'s and are **not** restated in `attributes` | `prose-only:` an absence cannot be exercised by a test that does not know what to look for; the gate that catches a second home for one fact is `check_spec_drift.py` holding the printed shape against the code, which the build row extends |


### 2.3 `inputs` — three reference shapes, and the third is this document's

[`EDGES.md`](EDGES.md) §2.1 defines two. An action takes a third.

```
TypeRef:                        # EDGES 2.1, unchanged. A row of the vocabulary
    namespace:  str
    kind:       str
    name:       str

InstanceRef:                    # EDGES 2.1, unchanged. One thing of that type
    type:       TypeRef         # kind MUST be "entity"
    id:         str             # opaque. The host's identifier

EdgeRef:                        # NEW, this document
    edge_id:    str             # EDGES 2.2's opaque id, generated above the store
    family:     str             # the NAME of the kind="edge" TypeEntry. Carried so the
                                #   reference can be READ without a store round trip
    namespace:  str             # the FAMILY's namespace. EDGES 2.2's rule, verbatim

InputRef = TypeRef | InstanceRef | EdgeRef

InputSpec:
    name:       str             # the argument name, as the host's tool schema spells it
    ref:        "type" | "instance" | "edge"
    kinds:      tuple[str, ...] | None   # for ref="type"/"instance": which registry kinds
                                         #   are acceptable. None = any but `predicate`
    families:   tuple[str, ...] | None   # for ref="edge": which families are acceptable
    required:   bool
```

**Why `EdgeRef` carries `family` and `namespace` when `edge_id` alone identifies the edge.** Because an invocation record is read long after the edge store has moved on, and an `edge_id` on its own is unreadable without a join — the objection `EDGES.md` §2.1 raises against a surrogate endpoint. A retracted edge still has a family and a namespace; a bare id has nothing. **[Inferred]** this is what a reader of a year-old invocation actually wants, and it costs two strings.

**`predicate` is excluded as an input kind at every ref level, and it is the general rule again.** `EDGES.md` §2.4.1 forbids `kind="predicate"` in any family's `endpoint_kinds`, at either level, because *two predicates being equivalent is a claim about extents* and `ROADMAP.md`'s kill row is one indirection away. **An action taking two predicates as inputs is the same indirection with a verb in front of it** — `merge_capabilities(commentable, searchable)` is the kill row spelled as a tool call. The exclusion is inherited unchanged and stated here so nobody has to derive it: **no `InputSpec` may name `predicate` in `kinds`**, and a family that does is refused at declaration.

> **The rule binds at BOTH layers, and round 1 constructed the kill row through the layer that was missing.** `EDGES.md` §2.4.1 spent an adversarial round establishing that its endpoint rule binds *at declaration and at write*, and this document said it inherited that rule *unchanged* — while enforcing only the declaration half. A reviewer declared a family with `kinds=None`, handed `preflight` two `kind="predicate"` refs, got `verdict="allowed"`, and recorded it `applied`: **`merge_capabilities(commentable, searchable)`, end to end, through the one door this section calls unconstructible.** §17 audited it as shut.
>
> **So `preflight` and `record_invocation` both validate every supplied `InputRef` against its `InputSpec`** — ref shape, `kinds`, `families`, and required-but-missing — and refuse with **`input_kind_mismatch`** (§7, the twenty-eighth value, added in this change per **R3**). **A `kind="predicate"` ref is refused whatever the family declared**, exactly as `EDGES.md` §2.4.1 excludes it at both levels: the exclusion is general or it is nothing.

> **Not a back door for gating on predicates, either.** §2.4's `predicate_holds` precondition asks *"does this input's type satisfy predicate P?"* — a question about **one** type's membership, answered by reading `TypeEntry.predicates`, which is `INTERFACE.md` §2.3's own derivation. It never compares two extents, and comparing two extents is what refusal #2 exists to prevent.

### 2.4 `preconditions` — four kinds, each one existing call, and no query language

> **The rule this section is built on.** A precondition is a question the registry can already answer with a call it already has. There are four kinds; there is no fifth; and *"anything else"* is not a precondition in v0 — it is the action's own code, and the registry does not pretend to know it.

| kind | asks | answered by |
|---|---|---|
| `type_active` | this `TypeRef` is a registered entry with `status="active"` | `list_types` — **and it can answer `True` but not always `False`**; see below |
| `predicate_holds` | this input's type carries predicate `P` in `TypeEntry.predicates` | `predicates()` / `list_types(predicate=…)` |
| `edge_exists` | an `active` edge of family `F` links these two inputs | `neighbors(src, [F], depth=1)` |
| `edge_absent` | **no** such edge exists | the same call, negated |

```
Precondition:
    kind:       "type_active" | "predicate_holds" | "edge_exists" | "edge_absent"
    subject:    str                 # the InputSpec.name this is about, or a literal ref
    predicate:  str | None          # for predicate_holds
    family:     str | None          # for edge_exists / edge_absent
    object:     str | None          # for edge_exists / edge_absent: the other input's name
    namespace:  str                 # the FAMILY's namespace, for the edge kinds. Defaults
                                    #   "default", and MUST be supplied when it is not
    why:        str                 # REQUIRED, non-empty. What this condition protects
```

**`namespace` is on the shape because `neighbors` requires it and has no default.** `Registry.neighbors(node, families, depth, *, namespace)` makes it keyword-only **without** a default *"precisely because `"default"` is a wrong answer nobody notices"* — UC3's whole subject. **The printed shape omitted it until round 1**, while the probe kit had silently added it: *"fixed only in the throwaway probe kit"*, which is the failure row 4b names and this row reproduced inside the same document that quotes it. Two readings of the missing field gave **opposite verdicts** on UC3's own fixture — one found the edge, the other returned `edge_family_unknown`.

**`edge_exists` and `edge_absent` search `direction="both"`, and that is a decision.** `EDGES.md` §2.2 records a confident, complete **false negative** produced by filtering a symmetric family on direction, so a precondition that filtered would inherit it. The cost is stated: for a *directed* family, `edge_absent(a, b)` is false when the edge runs `b → a`. That is the conservative answer — it refuses more than it must, never less — and no fixture needs the sharper one. There is deliberately no `direction` key: it is a fifth field on a shape whose whole argument is that it is not a query language.

> **`type_active` cannot use `resolve_type`, and the negative case is Rule U's — contortion ACT6.** `resolve_type` requires a `tier` and a column-shaped `ResolveContext` (§5.1's **ACT2**), and `preflight` has neither. `list_types` has no `name` filter on the façade at all, so the check is a **listing plus a scan above the call** — and `INTERFACE.md` §5.6 makes a filtered `TypeListing` **incomplete**. Therefore: a **hit** is a fact (`holds=True`); a **miss** off an incomplete listing is `holds=None` plus a `why`, because *"we did not find it in the rows we were shown"* is not *"it is not there"*. **[Observed]** by round 1's integrator lens, which asked which of the planned ids it could write and could not write this one. **Q41** asks for a `name` filter on `list_types`, which would make the negative cheap and complete; nothing here takes it.

**`why` is required and non-empty**, on exactly the reasoning `PACKAGE.md` §5.2 gives for `FieldSpec.description` and `INTERFACE.md` §2.1 for a non-empty `definition`: an undescribed condition is how an escape hatch re-forms one level down. A precondition nobody can read is a precondition nobody will ever delete when it stops being true.

**`edge_absent` is not symmetry, it is a fixture.** **[Observed]** beacon's `add_task_stakeholder` returns `Failure(message="Couldn't link stakeholder — task not yours or already linked", code="mutation_failed")` — **one opaque code covering two unrelated causes**, ownership and duplication, which the model receiving it cannot tell apart. The duplication half is exactly `edge_absent`, and that is why the negated form is in the vocabulary rather than left to the action's code.

**What is deliberately NOT expressible, and it is the most important paragraph in this section.** A condition over a **value** — *"the facility has a citation whose `Scope Severity Code` is in `{J, K, L}`"* — has no kind here and cannot be given one in v0. That is not an oversight; it is `INTERFACE.md` §10b.4's **contortion 11** and ruling **R22**, arriving at a third surface:

- `Consumer.gate` cannot express a value-level gate (contortion 11, `INTERFACE.md` §10b.4).
- An endpoint-kind gate on edges cannot either (`EDGES.md` **Q17**, ruled **R22** — *deferred to Phase 3 with contortion 11, because both would make `Consumer.gate` a query language*).
- **And now a precondition cannot** (§12, contortion **ACT4**).

Three unrelated surfaces reaching for one missing mechanism is the shape that earned `created_by: derived` its ruling (**R17**, on two fixtures). This one has three and is still **not** taken here, because R22 routed it to Phase 3 and taking it in a spec row would be a query language arriving through the side door this section exists to keep shut. §16 carries it as **Q35** with the count attached.

> **The modelling escape hatch is closed too, and it is closed by a rule CMS itself motivated.** The obvious way to make severity checkable is to make it an edge — `citation:42 --has_severity--> value_set:scope_severity_code` — and `EDGES.md` §2.4.1 **refuses that at two layers**, at declaration and at write, because an instance-level family takes only `entity` endpoints. So the value test has no edge to stand on either, and §12 shows the refusal firing on the fixture that motivated the rule. **This document did not have to invent a boundary; it inherited one and found that it holds.**

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 2.4-1 | The precondition vocabulary is closed at four kinds; a family declaring a fifth is refused at declaration | `C19-01` |
| 2.4-2 | Each kind is answered by a call that already exists — `list_types` / `predicates` / `neighbors` — and this document adds no call to `INTERFACE.md` §5 | `C19-02` |
| 2.4-3 | `Precondition.why` is required and non-empty | `C19-03` |
| 2.4-4 | A precondition that does not hold returns `Refusal(reason="precondition_unmet")` naming the failing condition's `subject` and `kind` in `detail`, never a bare `False` | `C19-04` |
| 2.4-5 | A precondition whose answer is **unknown** — the backend cannot answer it, e.g. `stores_edges=False` under an `edge_exists` — is `None` plus a `why`, and `preflight` refuses rather than treating unknown as satisfied | `C19-05` |
| 2.4-6 | A `Precondition` whose `subject` or `object` names neither an `InputSpec` nor a literal identity ref is refused **at declaration** with `attributes_schema_violation`, as is a `predicate_holds` with no `predicate` and an edge condition with no `family` — the precondition door is shut where the effect door is | `C19-45` |
| 2.4-7 | `Precondition.namespace` is the **family's**, and the edge kinds pass it to `neighbors`, which has no default for it | `C19-46` |
| 2.4-8 | The edge kinds search `direction="both"`; a directed family's `edge_absent` is therefore conservative rather than exact | `C19-47` |
| 2.4-9 | A value-level condition is not expressible in v0 | `prose-only:` the mechanism has no slot for it, and ruling **R22** routed exactly this question to Phase 3 with contortion 11. Recorded as contortion **ACT4** rather than designed away |

### 2.5 `effects` — a closed operation vocabulary, and the six calls it excludes

An `Effect` names an operation the family is **permitted** to perform, so an invocation's blast radius is knowable *before* it runs rather than reconstructible afterwards.

```
Effect:
    op:         "add_edge" | "retract_edge" | "propose_type" | "host_state"
    family:     str | None      # for add_edge / retract_edge: the edge family
    namespace:  str | None      # for propose_type
    kind:       str | None      # for propose_type. May NOT be "predicate"
    why:        str             # REQUIRED for op="host_state", non-empty. Rule U
```

**`namespace` is carried by the edge ops too, not only by `propose_type`.** `Registry` resolves an edge family by `(name, namespace)`, so an effect that names a family without one cannot be checked against the registry — the same hole as §2.4's missing `Precondition.namespace`, one field along, and found in the same round.

**And `namespace=None` on an edge op is a DECLARATION, not an omission: *the namespace comes from this invocation's inputs*.** Round 2's ingestion lens measured what the alternative costs. A catalogue ingester serves **84 publishing agencies** through one `ingest_dataset` family **[Observed, the pinned Socrata catalog: 2,399 datasets, 84 agencies]**, and the namespace it writes into is a property of the row being ingested. With a fixed namespace on the effect, **2,394 of 2,399 correct invocations carried `effect_undeclared`** — and the one invocation that ingested a dataset into the *wrong* agency's namespace carried the identical warning. A detector that fires on 99.8% of a correct run is not a detector.

**The rule that makes it a detector again:** an input-determined effect is satisfied only when the observed namespace is one the invocation's **own inputs** carry. The correct ingest stops warning; the wrong-publisher one still warns. All three escapes the reviewer measured are refused by this: declaring 84 effects copies 201,516 effect rows per run and turns the declaration into *"may write anywhere"* (the maximal-list twin of the empty list §2.5 forbids by name); one family per namespace is 84 propose→approve cycles and smuggles tenancy through `namespace`, which **R24** says scopes a vocabulary; and leaving `namespace` simply absent warns on everything.

**Effect identity is defined, because §3.3's whole mechanism is set containment over these.** Two effects are the same effect when `(op, namespace, family, kind)` match; **`why` is not part of identity** for the three protocol ops, so amending a sentence does not turn one declared effect into two. **`host_state` has no target at all, so its `why` IS its identity** — which means two `host_state` admissions with different prose are two effects, and that cost is stated rather than hidden. Round 1 found `effect_undeclared:host_state:None:None` being printed and the spec's `<op>:<target>` format having no reading for an op with no target.

**`propose_type` may not name `kind="predicate"`, and that is the third predicate door.** A predicate's extent is a set of **types**, and an action permitted to propose one — on a namespace whose policy auto-approves, which **[Observed]** is exactly UC1's deployment (`INTERFACE.md` §9 contortion 4) — mints a **live capability set** unattended, at the tier `0.5-RESULTS.md` caught inverting a scale. A reviewer did it against the shipped `Registry` in round 1.

> **And round 2 showed why the guard downstream does not catch it, which is the more important half.** This document asserted four times that `INTERFACE.md` §5.10's refusal #2 is *"non-overridable"*, flat. **It is not.** §5.10 reads *"either side has `kind="predicate"` **and extents are not byte-identical**"*, and `registry.py` implemented exactly that — so **two freshly minted predicates, whose extents are both EMPTY, were byte-identical, the guard did not fire, and the merge went through under two acknowledgements.** `ROADMAP.md`'s kill row, reproduced end to end against the shipped registry. `EDGES.md` §2.4.1 states the qualifier correctly; this document dropped it, and dropping it is why nobody looked. **Fixed in the same change**: an empty extent is *no evidence of membership*, not *evidence of identical membership*; `INTERFACE.md` §2.3 and §5.10 are amended, `C10-09` pins it, and `ROADMAP.md`'s kill-criteria row records the second trip in this project's life.

**So the effect rule is an ALLOWLIST, not a blocklist.** A `propose_type` effect **must name a `kind`**, and it must be one of `entity`, `edge`, `value_set`. Round 2 reached the kill row through the blocklist by simply **omitting** `kind` — the round-1 rule tested `kind == "predicate"` and `kind` is `str | None` — and reached it a second way with `kind="action"`, which mints a live **verb** unattended, the case §15.1 ranks *above* the noun. Refused at declaration with `effect_not_permitted`.

> **The allowlist is necessary and it is not sufficient, and saying so is the point.** A reviewer asked to break it and did: a family declaring `kind="entity"` passes the allowlist and its *code* mints predicates anyway, because §2.5's own rule 2.5-6 makes an observed effect outside the declared set a **warning** by design (*"refusing to record what already occurred is the worst available answer"*). **A permission is not the act.** What closes the run-time route is the guard fix above, in the registry, and that is where it belongs: the action layer governs what a family may *declare*, and only the call being made can refuse the call. **Q45** carries the reviewer's stronger proposal — that `propose_type(kind="predicate")` never auto-approve at all — which is `INTERFACE.md`'s to rule on, not this document's.

**Four operations, and the fourth is an admission rather than a capability.** `host_state` means *this action changes something this protocol does not model*, and it carries a mandatory sentence saying what. It exists because the alternative is worse: a family that mutates the host's database and declares `effects: []` is claiming a blast radius of zero, and **an empty list standing in for "we did not look" is what Rule U forbids by name**. `host_state` turns a silent zero into a stated unknown, which is the only honest thing available to a registry that does not own the host's schema.

**The six calls that may NOT be an effect, as a general rule rather than a family's opt-in:**

`approve` · `reject` · `retire` · `reinstate` · `merge_types` · `register_consumer`

> **Those six are the governance loop itself.** An action that can `approve` closes the proposal→approval loop with no human in it — mechanism **1** restored through the very layer this document adds. An action that can `merge_types` is `ROADMAP.md`'s kill row wearing a verb. An action that can `register_consumer` can make itself look gated. **An action may PROPOSE; only a human, or an auto-policy a deployment set deliberately, may APPROVE.** That sentence is the line, and `propose_type` is in the vocabulary precisely so the line has a legal side: an ingestion action meeting a new word may say so, and what it says is a request.

A family declaring any of the six is refused **at declaration**: `Refusal(reason="effect_not_permitted")`. Not at invocation. `EDGES.md` §2.4.1 spent a whole adversarial round learning that a rule checked only at write time is a rule a family author opts out of by declaring something permissive, and the lesson transfers without modification: **the door is the declaration.**

> **And "the declaration" is THREE call sites, not one — a round-1 finding that had made §17's kill-row audit false.** The shipped `Registry._edge_family_refusal` is called from `propose_type`, from `approve` **and from `import_types`**, and says why in its own docstring: *"because a rule with one enforcement point is a rule with one door left open — and the thing on the other side of this one is the `ROADMAP.md` kill row."* This document said *"at declaration"* eleven times and named no call, and `import_types` appears nowhere in it. A reviewer imported an **active** `kind="action"` family declaring `merge_types` as an effect *and* breaching §2.2's cross-field rule, through the shipped registry, with no warning at all. **`import_types` returns entries and cannot return a `Refusal`**, so on that path the entry is not written and the caller gets the existing `import_refused:<reason>` warning (`INTERFACE.md` §5.4) — the same treatment the edge path already gives.

**Declared versus observed, and why the record-time failure is a warning rather than a refusal.** The brief for this row offered `effect_undeclared` as a candidate `Refusal.reason`. Driving UC1 through the model moved it (§11):

> **[Observed]** `delete_person` in beacon deletes one row, and **fifteen foreign keys reference `people.id` — 7 `ON DELETE CASCADE`, 6 `SET NULL`, and 2 with no `ondelete` clause at all** (method: `grep -rn "people\.id" src/beacon/models/*.py`, 2026-08-29). Four of the seven cascades belong to three edge families of the kind [`EDGES.md`](EDGES.md) §9 maps (`person_links` twice — both legs — plus `task_stakeholders` and `project_stakeholders`). Its `prompt_docs` says *"Not reversible via undo."*, and its declared surface says nothing at all about the other fourteen tables.

If `record_invocation` **refused** a report because the host observed an effect the family had not declared, the registry would be destroying the only evidence that the undeclared effect happened. **Refusing to record what already occurred is the worst available answer**, and it is the failure shape of a `register_consumer` that quietly no-ops (`INTERFACE.md` §5.12). So:

- **Declaration time** — an op outside the four, or one of the six governance calls → `Refusal(reason="effect_not_permitted")`.
- **Record time** — an observed effect not in the declared set → the invocation **is recorded**, `outcome` is whatever the host reports, and the record carries `warnings: ["effect_undeclared:<op>:<target>"]`. `invocations(effect_undeclared=True)` enumerates every one, which is the move `list_types(unverified_semantics=True)` makes for a proposal nobody cited (`INTERFACE.md` §2.8).

**That is a deliberate departure from the brief's candidate list, recorded rather than quietly taken.** The brief's own instruction is *"add only what a design test forces"*; the design test forced the value into a different vocabulary, not out of existence. §7 carries both halves, and `INTERFACE.md` §5.4 gains the warning in this change per **R3**'s rule as `EDGES.md` §2.8 extended it to warnings.

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 2.5-1 | The effect vocabulary is closed at four operations; a fifth is refused at declaration with `effect_not_permitted` | `C19-06` |
| 2.5-2 | `approve`, `reject`, `retire`, `reinstate`, `merge_types` and `register_consumer` may never be an effect, as a general rule and not a family's opt-in | `C19-07` |
| 2.5-3 | `propose_type` **may** be an effect — an action may propose, and only a human or a deployment's auto-policy may approve | `C19-08` |
| 2.5-4 | `op="host_state"` requires a non-empty `why`; a family declaring it without one is refused | `C19-09` |
| 2.5-5 | The exclusion binds at **declaration** time, not only at invocation time | `C19-10` |
| 2.5-6 | An observed effect outside the declared set is a **warning** on a recorded invocation, never a refusal that discards the record | `C19-11` |
| 2.5-7 | An effect naming an edge family that is not a registered `kind="edge"` entry is refused at declaration with `edge_family_unknown` — `EDGES.md` §4.3's existing value, not a new one | `C19-12` |
| 2.5-8 | A `propose_type` effect **must name a `kind`**, and it must be one of `entity` / `edge` / `value_set` — an **allowlist**. `predicate` is excluded because an auto-approving namespace would mint live capability sets unattended and §5.10's guard does **not** fire on two empty extents; `action` because §15.1 ranks a verb above a noun. Round 2 reached the kill row by *omitting* the key a blocklist tested | `C19-48` |
| 2.5-9 | Effect identity is `(op, namespace, family, kind)`, with `why` excluded — except for `host_state`, which has no target and whose `why` is its identity | `C19-49` |
| 2.5-10 | `namespace=None` on an edge op **declares** an input-determined namespace, and is satisfied only by an observed effect whose namespace one of the invocation's own inputs carries | `C19-55` |

### 2.6 `reversibility` — a declaration, and the honest thing it is not

| value | means | what the registry does with it |
|---|---|---|
| `reversible` | the effects can be undone by the same protocol that made them — an `add_edge` answered by `retract_edge` | records it |
| `compensable` | undoing requires a **different** action, which the host must run | `Invocation.compensated_by` may name the compensating invocation, and `outcome="compensated"` exists for it |
| `irreversible` | there is no undo and no compensation | **forces `approval_mode="human"`** (§2.2's one cross-field rule) |

**A declaration, not a mechanism, and the distinction is load-bearing.** Nothing here rolls anything back. What the registry provides is that *"can this be undone?"* becomes a **governed, approved, enumerable property of the verb** instead of a sentence in a docstring — and **[Observed]** in beacon it is a sentence in a docstring: `delete_person`'s `prompt_docs` reads *"Delete a Person from the CRM. Not reversible via undo."*, while `undoable=False` on the same SPEC is the machine-readable half and says nothing about compensation.

**The three-value split is beacon's two-value split with the middle filled in.** **[Observed]** `ActionSpec.undoable: bool` plus a hand-written `undo` payload — `add_task_stakeholder` returns `undo={"kind": "add_task_stakeholder", "task_id": …, "person_id": …}`, replayed later by a dispatch path. That is `compensable` precisely: not a rollback, a second action. A boolean cannot tell *"the protocol can undo this"* from *"somebody wrote a compensating handler"*, and the difference is who is on the hook when the handler is missing.

### 2.7 `payload_schema` — R10's key, and this one is not inert

[`EDGES.md`](EDGES.md) §2.5 specified `payload_schema` and had to declare it **inert**, because `PACKAGE.md` §5.2 keyed an `AttributeSchema` by `(namespace, kind, version)` and every edge family shares `kind="edge"`. **Ruling R10 landed in row 3e** and `PACKAGE.md` §5.2b now carries name-level schemas that shadow the per-kind one; ruling **R34** takes it for edges in row 4c.

**So this document declares it live from the start**, keyed `(namespace, "action", <family name>)`, governing `Invocation.inputs`:

1. The per-kind `(namespace, "action")` schema governs the **eight keys of §2.2** — the family's own declaration. That is the case `PACKAGE.md` §5.2's mechanism was designed for: every entry of the kind has the same shape.
2. A name-level schema keyed by the family name governs **that family's `Invocation.inputs`** — the case R10 exists for: every family's inputs have a *different* shape.
3. `Invocation.attr_schema_version` records which generation validated it, as `TypeEntry.attr_schema_version` does (`INTERFACE.md` §2.1) and `Edge.attr_schema_version` does (`EDGES.md` §2.2).
4. **Shadowing is replacement, never merge** — `PACKAGE.md` §5.2b rule 1, inherited without restating its argument.

**The one thing to notice, because it is a real narrowing.** The two schemas govern two different objects living in two different tables. A per-kind schema on `kind="action"` validating the *family's* eight keys, and a name-level schema validating an *invocation's* inputs, is one mechanism doing two jobs — and `PACKAGE.md` §5.2's key has no field that says which. It works because the objects are never mixed in one store, and it is recorded as contortion **ACT1** rather than smoothed, because *"it works because of a fact outside the mechanism"* is the shape of every drift this repo has caught.

---

## 3. Invocations

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 3-1 | `declared_effects` is **copied** from the family at invocation time, so amending the family does not re-describe an existing invocation's blast radius | `C19-29` |
| 3-2 | `gate_verdict` has three values and `not_asked` is one of them; `False` would assert a refusal that never happened | `C19-30` |
| 3-3 | `approved_by` is never null on an `applied` invocation **that the gate decided**, and is **never fabricated** anywhere else: when the gate was not asked, or refused, the field is `None` and the record carries `approval_unrecorded`. *(This row still specified the fabrication round 1 removed, until round 2 read it — the numbered rule is the thing that ships executable, so a build row would have transposed the defect.)* | `C19-31` |
| 3-4 | `outcome="refused"` REQUIRES a `refusal`, whose `reason` is `INTERFACE.md` §5.12's closed vocabulary | `C19-32` |
| 3-5 | An observed effect outside the declared set warns and the record is kept; an observed effect that is a **subset** of the declared set warns nothing | `C19-33` |
| 3-6 | There is no `pending` outcome | `prose-only:` a value that does not exist cannot be asserted present; what a test could check is that the vocabulary has exactly four members, which is the closed-vocabulary assertion in rule 3-4 doing the same work under another name |
| 3-7 | The copy is taken from **what the gate judged**: `family_version` is stamped on `Preflight` and `Invocation`, `record_invocation(judged=…)` records that declaration and that policy, and a version mismatch is `declaration_amended:<from>:<to>` | `C19-56` |
| 3-8 | `declared_policy` carries `approval_mode`, `min_auto_tier`, `reversibility` and the precondition kinds, for the reason rule 3-1 carries the effects | `C19-57` |

### 3.1 `Invocation` — one use of one verb

```
Invocation:
    invocation_id:      str                   # opaque, generated ABOVE the store. PACKAGE 4.2
    family:             str                   # the NAME of a kind="action" TypeEntry
    namespace:          str                   # the FAMILY's namespace. EDGES 2.2's rule
    inputs:             dict[str, InputRef]   # keyed by InputSpec.name. 2.3
    declared_effects:   tuple[Effect, ...]    # COPIED from the family at invocation time
    observed_effects:   tuple[Effect, ...]    # what the host reports it actually did
    outcome:            "applied" | "refused" | "failed" | "compensated"
    refusal:            Refusal | None        # REQUIRED when outcome == "refused"
    gate_verdict:       "allowed" | "refused" | "not_asked"
    compensates:        str | None            # the invocation_id this one compensates
    compensated_by:     str | None            # the invocation_id that compensated this one
                                              #   -- DERIVED by the facade; the store holds
                                              #   only the forward pointer (9)
    reviewed_at:        datetime | None       # set by an `invocation_reviewed` event. 5.2
    provenance:         InvocationProvenance  # 3.2
    warnings:           list[str]             # INTERFACE 5.4's vocabulary, which this change amends
    attr_schema_version: int | None           # the inputs schema in force when this was written
```

**`declared_effects` is copied, not referenced, and that is the field to read twice.** A family's declaration may be amended after an invocation ran. An invocation that pointed at the *current* declaration would silently re-describe its own blast radius every time somebody edited the family — so the record carries the declaration **it was judged against**, the same way `attr_schema_version` carries *which generation* of a schema validated an entry (`INTERFACE.md` §2.1, `PACKAGE.md` §5.4: *entries written under an older schema are never rewritten and never retroactively invalidated*). Without the copy, `invocations(effect_undeclared=True)` would answer a different question each time the vocabulary moved.

**`gate_verdict` is a third value and not a bool**, because `not_asked` is a real and common state: a host may record an invocation it ran without consulting `preflight` at all, and `False` would say *the gate refused*, which is a different and much worse claim. Rule U, on a three-state field.

### 3.2 `InvocationProvenance` — a narrowing of `Provenance`, and the narrowing runs the *other* way from EDGES'

```
InvocationProvenance:
    created_at:        datetime
    created_by_actor:  str                    # "user:sd", "ai:classifier", "auto:nightly",
                                              #   "derived:<rule>". INTERFACE 2.4's field, verbatim
    created_by:        "seed"|"ai"|"user"|"derived"   # INTERFACE 2.1's, incl. R17
    model_tier:        str | None             # R20. The tier of the ACTOR that invoked
    confidence:        float | None           # None = nothing scored it. NOT 0.0 -- Rule U
    approved_by:       str | None             # "auto:<policy>" when the gate approved.
                                              #   NEVER blank-implying-human -- 3.2's rule
    approved_at:       datetime | None
    evidence:          list[Evidence]         # INTERFACE 2.8, unchanged
    source_version:    str | None             # R21's field, the SOURCE's own version
    history:           list[ProvenanceEvent]  # append-only. INTERFACE 5.8
    history_why:       str | None             # why `history` is empty, when it is. Rule U
```

**The field names are `INTERFACE.md` §2.4's and `EDGES.md` §5.1's, character for character**, including `created_at` and `created_by_actor` for a thing that reads more naturally as *invoked at* and *invoked by*. **The nicer names were considered and refused**: three shapes for one concept with three different spellings of *when* is precisely the drift `check_spec_drift.py` was written to catch, and `EDGES.md` §5.1 records the one time this repo let a printed shape disagree with its code. A better word is not worth a fourth vocabulary.

**`approved_by` comes BACK, and that is the interesting half of the narrowing.** `EDGES.md` §5.1 *dropped* `approved_by` with a sharp argument: edge instances have no approval loop, so the field's only honest values are `None` (breaking `INTERFACE.md` §2.4's rule) or a manufactured `"auto:…"` asserting an approval nobody performed — *"a field whose only honest value is a lie should not be on the shape."*

**Invocations are the case where that argument runs the other way.** An invocation *does* have an approval decision, taken by `approval_mode` (§5.2), and the decision has a real subject: either a human approved this use of this verb, or a policy did. So `INTERFACE.md` §2.4's rule is inherited verbatim rather than dropped:

> **`approved_by` is never null on an `applied` invocation *that the gate decided*, and it is NEVER FABRICATED.** When `gate_verdict="allowed"` the value is whatever `preflight` returned — a human's actor id, or `"auto:<policy-name>"`. When the gate was **not asked**, or asked and **refused**, the registry has no approval to record: the field is `None` and the record carries `warnings: ["approval_unrecorded"]`.
>
> **The first draft got this exactly backwards and round 1 caught it.** It filled `"auto:<policy>"` on every `applied` invocation, so an `irreversible` / `human` family — the class §2.2's cross-field rule exists to make un-auto-approvable — recorded `outcome="applied"`, `gate_verdict="not_asked"`, `approved_by="auto:action_policy"`, actor `ai:reaper`, **no human and no warning**. That is an approval nobody performed, written into `delete_person`'s ledger: precisely the field `EDGES.md` §5.1 dropped from `EdgeProvenance` because *"a field whose only honest value is a lie should not be on the shape."* A null plus a named warning is the honest third answer the first draft did not look for.

**`created_by` is DERIVED from `created_by_actor`, never passed.** `INTERFACE.md` §2.1: *"The registry reads it off the actor, the way it already reads `ai:` and `seed:`"*, and `derived:<rule>` lands `created_by="derived"` — which is how §13's T3.6 produces its result. Round 1 found `record_invocation`'s printed signature carrying no `created_by` while `InvocationProvenance` required one, and the probe kit inventing a parameter to bridge them.

**Dropped from `Provenance`, each with its reason:** `proposed_by` (the *family* is proposed; an invocation is not), and `imported_from` (an invocation is never imported in v0 — though a host with a year of undo records is exactly the migration this omission blocks, and that is **Q37**).

**`model_tier` is present by R20** and it means *the tier of the actor that invoked*, not the tier that proposed the family. Those are two different facts about two different objects and both matter: a family proposed by Haiku and invoked by Opus is not the same risk as the reverse. The family's tier is `TypeEntry.provenance.model_tier`, unchanged.

### 3.3 Declared versus observed effects — the mechanism, in one paragraph

`declared_effects` says what the family was permitted to do. `observed_effects` says what the host reports it did. **The registry compares the two and reports, and does not adjudicate.** Three outcomes:

| relation | what it means | what the registry does |
|---|---|---|
| observed ⊆ declared | the action stayed inside its declaration | nothing; the record is clean |
| observed ⊄ declared | the action did something it never declared | `warnings: ["effect_undeclared:<op>:<target>"]` per surplus effect, and the record is **kept** (§2.5) |
| observed ⊊ declared | the action did less than it was permitted to | **nothing, deliberately.** A permission is not a promise, and warning on an unused permission would train hosts to declare narrowly and amend often, which is worse than declaring broadly and being measured |

**`observed_effects` is the host's claim and the registry cannot verify it.** Said plainly because the alternative reading — that this document detects what an action really did — is the reading that would make the mechanism worthless the first time someone relied on it. What the registry supplies is that the claim is *recorded, typed and enumerable*: a host that reports honestly gets a blast-radius ledger, and a host that reports nothing is visible as a family whose invocations all carry `observed_effects: ()` against a non-empty declaration.

### 3.4 `outcome`, and the vocabulary is closed at four

`applied` — the host performed the action. `refused` — it did not, and `refusal` says why. `failed` — it tried and something broke; **not** a refusal, because a refusal is a decision and a failure is an accident, and collapsing them loses the only distinction an operator cares about at 3am. `compensated` — a previously `applied` invocation has been undone by a compensating invocation, which names it in `compensates` and is itself recorded.

**`refusal` is REQUIRED when `outcome="refused"`**, and its `reason` is `INTERFACE.md` §5.12's closed vocabulary. A refused invocation with no reason is an unexplained *"no"* in the ledger whose whole purpose is explaining.

**There is deliberately no `pending` value.** A `review`-mode or `human`-mode invocation awaiting a decision is not an invocation yet — it is a `preflight` the host has not acted on, and `preflight` records nothing (§6.1). Inventing `pending` would make this document own a queue, which §1 rules out in the first line.

### 3.5 Append-only, and what a correction is

`INTERFACE.md` §5.8: *"`history` is append-only: a correction is a new `ProvenanceEvent`, never an edit."* Unchanged, with the same one-field amendment `EDGES.md` §5.2 needed:

```python
@dataclass(frozen=True)
class EventRecord:
    ...
    edge_id:       str | None = None    # EDGES 5.2
    invocation_id: str | None = None    # the invocation this concerns, if any. ACTIONS 3.5
```

with three new `event` values — `invocation_recorded`, `invocation_reviewed`, `invocation_compensated` — and the same rule as everything else in that vocabulary: the adapter **stores** the string and never judges the transition (`PACKAGE.md` §3.1).

**A correction is a new event, and a compensation is a new *invocation*.** Those are two different things and the distinction is the point:

- *"the tier we recorded was wrong"* → an `invocation_recorded` event carrying the correction. The original record is untouched.
- *"the thing the action did has been undone"* → a **second invocation**, of a compensating family, whose `compensates` names the first. The first's `outcome` becomes `compensated`; its `observed_effects` stay exactly what they were, because they happened.

**[Observed]** beacon already has the second shape and not the first: `add_task_stakeholder` returns `undo={"kind": "add_task_stakeholder", …}` which `/api/messages/{id}/undo` replays through the same dispatch path — a compensating call, recorded nowhere as a governed event.



---

## 4. The registry does not execute, and what the gate is worth without an executor

**Stated in the strongest form available, because a weaker statement would be a lie of omission.** `preflight` can be skipped. A host may run an action the gate would have refused, then call `record_invocation` with `gate_verdict="not_asked"`, or with `gate_verdict="refused"` and `outcome="applied"`. Nothing in this document stops it, and nothing could: **a protocol with no executor cannot enforce, and pretending otherwise is exactly the rubber-stamping failure `WALKTHROUGH.md` names.**

**Two things make it not-nothing, and both are countable rather than rhetorical:**

1. **The refusal is typed and recorded.** `Refusal.reason` is closed (§7), so *"the gate said no"* is a value from a twenty-seven-word vocabulary rather than a free-text log line, and every refusal of every family is one query away.
2. **Every override is enumerable — as a floor, not a total.** `invocations(gate_verdict="refused", outcome="applied")` returns the cases where a host ran something the gate refused, and because it is a **filtered** listing it comes back `complete=False` with a `why` (§6.3, Rule K, `INTERFACE.md` §5.6's rule for `TypeListing`). *(The first draft's implementation stamped it `complete=True` through a dead sub-expression — `(not filtered or True)` — in the one query this section asks an operator to act on. Round 1.)*

> **And a floor is only worth something if the store can compute it, which round 2 found it could not.** `gate_verdict`, `effect_undeclared` and `unreviewed` were on `invocations()` and on **no primitive**, so §8's *"the registry filters above the store"* meant the façade read a `limit`-bounded page and filtered it afterwards. On the ingestion lens's own fixture — **2,399 datasets, one invocation each, one override at row 1,200** — the query returned **zero rows**, `complete=False`. **A floor of zero is not a conservative measurement; it is the wrong one, and it is indistinguishable from a clean deployment.** The three filters with no push-down were exactly the three governance reads: this section's override query, §2.5's blast-radius query, and §5.2's review queue. They are on primitive 21 now (§9), which is why this section's claim is a claim rather than a hope. That is the same move `INTERFACE.md` §2.8 makes with `list_types(unverified_semantics=True)`: **the registry cannot stop the thing; it can make the thing countable, and a count is what turns a policy discussion into a measurement.**

**The corollary is uncomfortable and is stated rather than buried:** in a deployment where nobody ever runs that query, this layer's governance value is zero. Its recording value is not — the ledger still exists — but the gate is advisory by construction. **[Assumed]** that an operator who can see the override count will act on it; that assumption is untested, it is the same one `consumers`' `complete: false` friction rests on, and §15 names what would revise it.

> **The TOCTOU gap, named rather than closed.** Between `preflight` returning `allowed` and `record_invocation` filing a report, the world may change: an edge the precondition required may be retracted, a type may be retired. `record_invocation` does **not** re-evaluate the preconditions, and that is deliberate — re-evaluating would mean refusing to record something that already happened (§2.5's argument), and recording a stale `allowed` is at least *true about what the host was told*. What closes the gap is not a lock; it is that the invocation carries the gate verdict it acted on and the timestamp it acted at, so a divergence is reconstructible after the fact. A locking protocol would require the registry to sit in the execution path, which is §1's first non-goal.

---

## 5. Gating

### 5.1 The family goes through the proposal→approval loop unchanged

A new action family is proposed, resolved against existing ones, approved or rejected — `INTERFACE.md` §5.3, §5.4, §5.5, with `kind="action"` and no new call. That is §2.1's whole claim, and the design tests exercise it rather than assert it.

**One contortion, recorded here because it is a fact about `resolve_type` and not about actions.** `ResolveContext` (`INTERFACE.md` §5.3) is **column-shaped**: `sample_values` is *"up to N observed instances"*, `sibling_columns` is *"what else arrived with it — carries most of the signal"*, and `source` is spelled `"NH_HealthCitations_Aug2026.csv#Location"`. For a verb, `sample_values` has no natural filler — past invocations are not instances of the word — and `sibling_columns` is empty, which removes the field the documentation says carries most of the signal. So resolution of an action family runs on `candidate` and `definition_hint` alone. **It works, and it works with less signal than the mechanism was built for.** Recorded as contortion **ACT2**; not designed away, because inventing an action-shaped `ResolveContext` would be a second context object for one call.

### 5.2 `approval_mode` and `min_auto_tier`

| `approval_mode` | what `preflight` does | `approved_by` on an `applied` invocation |
|---|---|---|
| `auto` | approves, **if** the actor's tier passes `min_auto_tier` and every precondition holds | `"auto:<policy>"` |
| `review` | approves, and the record is enumerable by `invocations(unreviewed=True)` until an `invocation_reviewed` event is appended | `"auto:<policy>"` |
| `human` | **refuses** unless `approved_by` names an actor whose derived `created_by` is `"user"` | that human's actor id |

> **An ALLOWLIST off `created_by`, not a prefix blocklist — round 1 walked through the blocklist four ways.** The first draft refused ids prefixed `ai:`, `auto:` or `derived:`; a reviewer got `bot:reaper`, `svc:cleanup`, `AI:bot` and `nobody` past it, on an `irreversible`/`human` family. `INTERFACE.md` line 58 names the failure by name — *"a `created_by_actor` string convention that nothing validates"* — and the record already carries the derived value, so the honest test is `created_by == "user"` and everything else is refused. A three-item blocklist is the wrong shape for a rule whose whole job is mechanism 1.

**`min_auto_tier` is a product parameter, and the registry compares two opaque strings it did not order.** `INTERFACE.md` §2.7 is explicit — *"v0 does not define the tier vocabulary or the ordering… requires the policy comparison to be supplied by the deployment"* — and this document inherits that posture without softening it. **The registry does not know that `haiku` is below `sonnet`.** A deployment supplies the order; without one, `min_auto_tier` cannot be evaluated and `preflight` reports `tier_floor_why` saying so rather than guessing. **[Assumed], inherited from §2.7:** that a total order over tiers exists per deployment. Untested, and possibly wrong for mixed vendors.

**`min_auto_tier=None` under `approval_mode="auto"` means there is no floor, and it is a legitimate configuration** — a single-tier deployment has nothing to compare. It is **not** a warning value, deliberately: minting one would put a vocabulary entry on a correct configuration. What the caller gets instead is Rule U on the report: `Preflight.tier_floor=None` with `tier_floor_why="the family declares no floor; every tier auto-approves"`. **The honest surface is a stated absence, not an alarm.**

**Below the floor, `preflight` returns `Refusal(reason="tier_below_action_policy")`** — a new value, and §7 argues why `tier_below_auto_approve_policy` is not reused.

**Three states, not two, and the third is `None`.** The comparison is the shipped `TierOrder.below(tier, minimum) -> bool | None`, and the deployment's order is the shipped `NamespacePolicy.tier_order`. `None` — *cannot be told* — has **three** causes and `detail["state"] == "unknown"` with a `why` naming which:

| cause | `why` |
|---|---|
| the deployment supplied no order | *"no deployment tier order supplied; the registry does not order tiers (INTERFACE 2.7)"* |
| no tier was supplied for the actor | *"no tier was supplied for the invoking actor"* |
| the actor's tier is not in the order | *"tier `<x>` is not in this deployment's order"* |

**All three refuse, and none of them says `false`.** The shipped comment on `TierOrder.below` gives the reason for the second: returning `False` would *"auto-approve an unknown model on the strength of not recognising its name"*. Round 1 found the first draft returning a confident below-the-floor refusal for a tier nobody supplied, and **raising an uncaught `ValueError`** for a tier outside the order — in the one place §5.2 flags mixed vendors as **[Assumed]** and possibly wrong.

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 5.2-1 | `approval_mode` is closed at three values; a family declaring a fourth is refused at declaration | `C19-13` |
| 5.2-2 | `approval_mode="human"` refuses a `preflight` whose `approved_by` is absent or whose **derived `created_by` is not `"user"`** — an allowlist, not a prefix blocklist | `C19-14` |
| 5.2-3 | An actor tier below `min_auto_tier` returns `tier_below_action_policy` with `detail["state"] == "false"`, the family's floor and the actor's tier | `C19-15` |
| 5.2-4 | `min_auto_tier=None` under `approval_mode="auto"` is a legal configuration reported as `tier_floor=None` plus a `why`, never a warning and never a refusal | `C19-16` |
| 5.2-5 | The comparison is `bool \| None`, and **all three** unknown causes — no order, no tier, a tier outside the order — refuse with `detail["state"] == "unknown"` and a `why` naming which. None of them raises, and none says `false` | `C19-17` |
| 5.2-6 | `model_tier` on `InvocationProvenance` is the tier of the **invoking** actor, distinct from the family's own `provenance.model_tier` | `C19-18` |
| 5.2-7 | `approval_mode="review"` records `approved_by="auto:<policy>"` and the invocation is enumerable by `invocations(unreviewed=True)` until an `invocation_reviewed` event sets `reviewed_at` | `C19-50` |

### 5.3 What `min_auto_tier` does NOT decide — ruling R20, restated because it is easy to over-read

**R20 ruled: `model_tier` on provenance — YES. A tier gate on AI-written edges — NO in v0**, because *"gating a weekly batch job is a product decision about beacon's behaviour, not a storage shape"*, relayed to the beacon program as an observation rather than a requirement.

**Nothing here reverses that, and the difference is worth being exact about.** R20 declined to put a gate *in the storage layer*, where it would have applied to every host whether or not the host wanted one. `min_auto_tier` is not in the storage layer: it is a **field a deployment declares on a family it approved**, evaluated against an order the same deployment supplied. The registry ships no default floor, no tier vocabulary and no ordering.

So, concretely, for the one host that exists:

- **[Observed, beacon spec §2.5]** `infer_person_relationships` classifies person pairs with **Haiku** and auto-applies at **≥ 0.7 confidence**. That threshold is **beacon's**, it stays beacon's, and this document does not move it. If beacon registered that job as an action family it would choose its own `min_auto_tier`, and if it chose `None` the registry would record every invocation at `haiku` and refuse nothing.
- What the registry adds is that the choice is **written down, approved and enumerable** instead of living in a service module. `invocations(family="infer_person_relationships")` answers *"how many edges did the cheap tier write unattended last month?"* — the query `0.5-RESULTS.md` makes necessary and which nothing in beacon can answer today.

**The 0.5 finding is what makes the parameter a product parameter rather than a knob.** **[Observed]** four agents, four tiers, one CMS slice: the cheapest tier **inverted the scope-and-severity scale** — reported that higher letters are less serious when J/K/L are Immediate Jeopardy — while every number it produced stayed correct and nothing errored. An action whose precondition depends on that scale, invoked by that tier, unattended, is that failure with a write attached. §12 is that scenario, end to end.


---

## 6. The calls — four, and none of them in `INTERFACE.md` §5

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 6-1 | `preflight` **records nothing** and is idempotent: calling it N times leaves the invocation store unchanged | `C19-34` |
| 6-2 | Every `PreconditionResult` carries `evaluated_by` naming the existing call that answered it, from the closed set `list_types` / `predicates` / `neighbors` — §2.4's no-query-language claim, made mechanical | `C19-35` |
| 6-3 | `holds=None` is refused, and the refusal's `detail` says **unknown** rather than **false**; unknown is never treated as satisfied | `C19-36` |
| 6-4 | `record_invocation` does **not** re-evaluate preconditions, and an invocation whose gate refused is recorded rather than discarded | `C19-37` |
| 6-5 | `InvocationReport.known` is `int | None` and `complete` is `False` whenever a filter suppressed rows or `limit` truncated the answer | `C19-38` |
| 6-6 | `preflight` and `record_invocation` validate every supplied input against its `InputSpec`, and refuse a `kind="predicate"` ref whatever the family declared | `C19-51` |
| 6-7 | A shipped call that **raises** for an unregistered subject (`predicates`, `consumers`) is caught and becomes `holds=None` plus a `why`; nothing escapes the return type | `C19-52` |
| 6-8 | `invocations` does not page | `prose-only:` ruling **R25** routed paging for every listing to Phase 3 *together*; a test asserting the absence of a cursor would pin a decision this document is explicitly not making |

Signatures are Python-shaped because deliverable #2 is a Python package. They are **not** a module layout.

### 6.1 `preflight` — may this run, and what does it declare?

```python
def preflight(
    family: str,
    inputs: dict[str, InputRef],
    *,
    namespace: str = "default",
    actor: str,
    tier: str | None = None,
    approved_by: str | None = None,
) -> Preflight | Refusal: ...
```

```
Preflight:
    family:            str
    namespace:         str
    verdict:           "allowed" | "refused"
    refusal:           Refusal | None            # REQUIRED when verdict == "refused"
    declared_effects:  tuple[Effect, ...]        # the blast radius, before anything runs
    preconditions:     tuple[PreconditionResult, ...]
    approval_mode:     "auto" | "review" | "human"
    approved_by:       str | None                # "auto:<policy>" when the gate approves
    tier_floor:        str | None                # the family's min_auto_tier
    tier_floor_why:    str | None                # required when tier_floor is None. Rule U
    known:             int                       # len(preconditions). Rule K
    complete:          bool                      # False when ANY condition is unknown
    why_incomplete:    str | None

PreconditionResult:
    condition:     Precondition
    holds:         bool | None    # None = could not be evaluated. Rule U -- NOT False
    why:           str | None     # REQUIRED when holds is None
    evaluated_by:  str            # "list_types" | "predicates" | "neighbors"
                                  #   NOT `resolve_type` -- it needs a tier and a
                                  #   column-shaped context preflight does not have
```

**`preflight` validates its inputs before it evaluates anything.** Every supplied `InputRef` is checked against its `InputSpec` — ref shape, `kinds`, `families`, required-but-missing — and a `kind="predicate"` ref is refused whatever the family declared. `Refusal(reason="input_kind_mismatch")`, §2.3. **This is the layer round 1 walked the kill row through**, and `record_invocation` runs the same check for the same reason.

**`preflight` never raises where it could return.** The shipped `Registry.predicates(of=…)` and `consumers(…)` raise `UnknownType` for an unregistered subject; a `predicate_holds` condition naming one would escape the return type entirely. It is **caught** and becomes `holds=None` plus a `why` — Rule U's unknown, which the verdict then refuses. Round 1 found the escape.

**`preflight` records nothing.** It is a question, it is idempotent, and it may be called a hundred times. A host that wants the question answered *and* the answer recorded calls `record_invocation` with the verdict it received.

**`evaluated_by` is not decoration — it is §2.4's no-query-language claim made checkable.** Every `PreconditionResult` names the existing call that produced it, so a reviewer can confirm mechanically that nothing evaluated a condition by some fifth route. **[Inferred]** this is the field a later reader will use to notice that a query language grew.

**`holds=None` is not `False`, and `preflight` refuses on it.** A precondition the backend cannot evaluate — an `edge_exists` against an adapter declaring `stores_edges=False` — is unknown, and Rule U forbids substituting a confident answer. Treating unknown as *satisfied* would let a degraded backend approve everything; treating it as *unsatisfied* would be a confident `False` the document did not earn. So the condition carries `None` plus the adapter's own `why`, `complete` goes `False`, and the verdict is `refused` with `precondition_unmet` whose `detail` says **unknown**, not **false**.

### 6.2 `record_invocation` — what happened

```python
def record_invocation(
    family: str,
    inputs: dict[str, InputRef],
    *,
    namespace: str = "default",
    actor: str,
    outcome: str,                                   # 3.4's four values
    tier: str | None = None,
    observed_effects: Sequence[Effect] = (),
    gate_verdict: str = "not_asked",
    approved_by: str | None = None,
    confidence: float | None = None,
    evidence: Sequence[Evidence] = (),
    source_version: str | None = None,
    refusal: Refusal | None = None,
    compensates: str | None = None,
) -> Invocation | Refusal: ...
```

Refuses with `action_family_unknown` (no such family), `action_store_absent` (`stores_invocations=False`), or `attributes_schema_violation` (the inputs fail the family's `payload_schema` in `enforce` mode — `PACKAGE.md` §5.3's existing value, not a new one).

**It does not refuse on `effect_undeclared`, on a stale precondition, or on a `gate_verdict` of `refused`.** All three are recorded, warned where §2.5 says to warn, and enumerable. §4 is the argument.

### 6.3 `invocations` — the read

```python
def invocations(
    *,
    family: str | None = None,
    namespace: str | None = None,
    actor: str | None = None,
    outcome: str | None = None,
    gate_verdict: str | None = None,
    effect_undeclared: bool | None = None,
    unreviewed: bool | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> InvocationReport | Refusal: ...   # 8: action_store_absent
```

```
InvocationReport:
    invocations:     tuple[Invocation, ...]
    known:           int | None      # None = the backend cannot count. Rule U beats Rule K
    complete:        bool            # False whenever a filter suppressed rows or the
                                     #   limit truncated the answer -- so EVERY filtered
                                     #   answer, including 4's override query, is a floor
    why_incomplete:  str | None
    warnings:        list[str]
```

**`known: int | None` and not `int`**, because `INTERFACE.md` §3's amendment settled that a backend entitled to say *"we did not count"* must have somewhere to say it, and `0` would falsify it. This is the fifth carrier of Rule K and it takes the `TypeListing` shape rather than the `ConsumerReport` one, because the rows are not a list this document has already materialised.

**It does not page, and this document ROUTED that to R25 — which is a decision this document took, not one the ruling took.** R25's text names **`list_types` and `neighbors`**, and its reasoning is a 9,738,128-degree node plus Rule K's unanswered question about `known` on a page. Neither reason is the ledger's. Round 2's ingestion lens put the difference plainly and it is worth carrying:

| | what R25 ruled on | the invocation ledger |
|---|---|---|
| what bounds the size | curation — the product's own thesis bounds a vocabulary | one row per action per data row, **forever**; §15.2 and **Q40** admit nothing sizes it |
| what blocks a page | a semantic question (`known` on a page) | until round 2, three filters with no push-down — which a cursor would **not** have fixed |
| whether the cursor exists | no | **yes**, on primitive 21 (§9), and §6.3 declines to expose it |

**So the widening is recorded rather than left implicit, and the question is Q-numbered.** `limit` bounds the answer, `complete=False` says the bound was hit, and the push-down (§9) is what stops the bound from silently changing the answer. Whether the **ledger** should page is **Q43** — routed to the same Phase 3 decision R25 names, with the argument that it is a *third* object rather than a third listing.

### 6.4 `projection` — §10's call, listed here for completeness

```python
def projection(
    surface: str,
    *,
    budget: int,
    reserved: int = 0,
    order: Sequence[str] | None = None,
    namespace: str | None = None,
) -> ProjectionReport | Refusal: ...
```

Shape and rules in §10, because the argument for it is the tool-slot ceiling and not the call list.



---

## 7. Refusals — through `INTERFACE.md` §5.12, amended in this change

**Ruling R3's rule:** a value is added by amending §5.12 **in the change that introduces it**. This document adds **seven** — six in the first draft and a seventh from its first adversarial round — taking the closed vocabulary from twenty-one to **twenty-eight**. As with `EDGES.md` v0's four, **no v0 code path returns any of them** — row #6 is a spec and ships no action store — and they are enumerated in `INTERFACE.md` §5.12 and in `types.REFUSAL_REASONS` anyway, because a reason specified in a spec and absent from the tuple is the same drift the checker exists to catch, pointing the other way.

| value | returned by | why none of the twenty-one said it |
|---|---|---|
| **`action_family_unknown`** | `preflight`, `record_invocation`, `projection` naming a family that is not a registered `kind="action"` entry | The exact shape of `edge_family_unknown`, one kind along, and it is a **separate value for the same reason `unknown_edge` is separate from `edge_family_unknown`**: reusing the edge value would make one word mean two things (`INTERFACE.md` §2.3's Cause B), and the alternative — an empty `Preflight` for a typo'd family — is mechanism **C** committed by the gate |
| **`precondition_unmet`** | `preflight` when a declared condition does not hold, **or cannot be evaluated** | Nothing in the vocabulary is about a *runtime state of the world*. The fourteen policy refusals are about the vocabulary; `precondition_unmet` is the first about the data. `detail` carries the failing condition's `kind`, `subject` and whether it was **false** or **unknown** — one value, two states, and the states are in `detail` rather than in two words, per `endpoint_kind_mismatch`'s precedent |
| **`human_approval_required`** | **`preflight` and `record_invocation`**: a `human`-mode family with no *recognisable* human approver | The brief for this row named it `irreversible_requires_human`. **It is widened deliberately** — *this needs a person and does not have one*, at both invocation calls, and `EDGES.md` §5.12 records the economy: *"a closed vocabulary that grows a value per variant of one failure is not closed for long."* **The DECLARATION case is no longer here**: §2.2's cross-field rule returns `attributes_schema_violation`, R18's own value, and round 1 moved it while this row went on describing the old behaviour until round 2 read the two side by side. Not `tier_below_auto_approve_policy`: that is about a *type proposal*'s tier, not an invocation's approver |
| **`tier_below_action_policy`** | `preflight` when the actor's tier is below the family's `min_auto_tier` | **`tier_below_auto_approve_policy` is NOT reused**, and the temptation to reuse it is exactly `INTERFACE.md` §2.3's Cause B. That value is about **approving a proposed type**; this one is about **invoking an approved action**. Two policies, two objects, two lifecycles: a deployment may auto-approve Haiku's *proposals* and refuse Haiku's *invocations*, and one word could not express that |
| **`effect_not_permitted`** | **declaration** of a family whose `effects` name an operation outside §2.5's four, or one of the six governance calls | The brief named `effect_undeclared` as a refusal; the design tests moved it to a **warning** at record time (§2.5) and left this door with no value at all. Nothing said *"you may not declare that"* — `attributes_schema_violation` is about a schema's field types, and this is a rule about the vocabulary of one field's values |
| **`input_kind_mismatch`** | `preflight` and `record_invocation`, when a supplied `InputRef` is not what the `InputSpec` declared — wrong ref shape, wrong kind, wrong family, or missing — **and whenever any input is a `kind="predicate"`, whatever the family declared** | **Added by round 1, and it closes the kill row.** `InputSpec.kinds` bound at declaration and at nothing else, so a family declared with `kinds=None` accepted two predicates and the gate said `allowed`: `merge_capabilities(commentable, searchable)`, end to end. **`endpoint_kind_mismatch` is not reused** — that value is about an *edge's* endpoint, and one word for two objects is `INTERFACE.md` §2.3's Cause B, the same argument that keeps `unknown_edge` separate from `edge_family_unknown` |
| **`action_store_absent`** | any invocation call against an adapter declaring `stores_invocations=False` | A capability refusal, the **fifth** of that shape after `proposals_not_stored`, `cannot_record_override`, `consumer_source_read_only` and `edge_store_absent` — and it exists for the reason the first of those does: an empty `InvocationReport` would read as *"nothing has ever run"*, which is Rule U's forbidden empty in the one call a caller would believe |

**A seventh was considered and NOT taken: `unknown_invocation`.** `EDGES.md` needed `unknown_edge` because `retract_edge` names an existing edge by id. **No call in this document names an existing invocation by id** — `compensates` names one, and a `compensates` pointing at nothing is recorded with a warning rather than refused, because refusing would discard the compensation record itself (§2.5's argument again) — and `invocations(...)` is a *filter*, where an empty result is the honest answer rather than a silent drop. **Stated so that the absence is a decision rather than an oversight.**

**Two warning values, added to `INTERFACE.md` §5.4 in this change** — the same rule, extended to warnings by `EDGES.md` §2.8:

| value | carrier | from |
|---|---|---|
| `effect_undeclared:<op>:<target>` | **`Invocation`** | §2.5 — the host reported an effect the family did not declare. One per surplus effect. The record is **kept**; refusing it would destroy the only evidence the undeclared effect happened. `<target>` is the effect's identity (§2.5); for `host_state`, which has no target, it is the `why` |
| `approval_unrecorded` | **`Invocation`** | §3.2 — `outcome="applied"` and the gate was not asked, or was asked and refused, so there is no approval to record. **Added by round 1**, which found the first draft fabricating `approved_by="auto:<policy>"` in exactly that case, on an `irreversible`/`human` family invoked by `ai:reaper` |

§5.4 goes to **twenty-four** values across nine carriers. *(This sentence said *"twenty-three… across **five** carriers"* until round 1 — the count of carriers contradicting `INTERFACE.md` §5.4's own header and this document's own §18, two screens apart. `check_spec_drift.py` holds the value list and the count word and has never held the carrier count; §14 records that the printed shapes here are held by nothing at all.)*

---

## 8. Capability flags for an action store

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 8-1 | `stores_invocations=False` makes every call that **reads or writes the invocation store** — `record_invocation` and `invocations` — return `Refusal(reason="action_store_absent")`, never an empty report. `preflight` and `projection` touch no invocation and are unaffected; *"every invocation call"* was undefined until round 1 asked which four | `C19-39` |
| 8-2 | Every `False` action flag carries a non-empty `Capabilities.why`, and when `stores_invocations` is `False` the other two are **vacuous rather than declined** — `C0-01`'s carve-out shape | `C19-40` |
| 8-3 | With `action_store_shares_connection=True`, `action_transaction_scope` MUST equal `transaction_scope`; declaring two scopes on one connection is non-conformant | `C19-41` |
| 8-4 | Under `action_transaction_scope="savepoint"`, `record_invocation` stamps `not_durable_until_host_commits` **itself**, and `invocations` does not | `C19-42` |
| 8-5 | The action flags default `False`, so an adapter written against the eighteen-primitive protocol claims no invocation store | `C19-43` |

In `PACKAGE.md` §3.2's style: every `False` flag carries a sentence in `Capabilities.why`, surfaced verbatim wherever a result would otherwise imply a fact. **Three flags and two declarations**, added to the existing `Capabilities` — the same split `EDGES.md` §6 draws, for the same reason: a flag is something a backend *declines*; a declaration says *how* it does something it can do.

```python
    stores_invocations:            bool = False   # the store holds invocations at all
    stores_invocation_events:      bool = False   # append_event with an invocation_id is durable
    indexes_invocations_by_family: bool = False   # a family-filtered read need not scan
    action_transaction_scope: Literal["owned", "savepoint"] = "owned"   # R5, 8.2
    action_store_shares_connection: bool = True                         # 8.2's premise
```

| Flag | `False` means | `why` example | What the registry does |
|---|---|---|---|
| `stores_invocations` | there is no invocation store behind this adapter | *"this backend is a type registry only; no table holds invocations"* | **every** invocation call returns `Refusal(reason="action_store_absent")`. Never an empty report — §7 |
| `stores_invocation_events` | an invocation event cannot be persisted | *"the host owns the schema and has no event table"* | `record_invocation` **succeeds** and the returned record carries `history == []` with a `history_why`. No new warning value is minted: `EDGES.md` §2.6's `retracted_without_event_trail` exists because a *retraction* is a decision whose sequence is lost; an invocation record **is** its own event, so there is no second fact to lose |
| `indexes_invocations_by_family` | a family filter costs a scan | *"invocations live in the host's audit table with no family column"* | correctness is unchanged — the registry filters above the store. But a scan may hit `limit`, and then `complete=False` with `why_incomplete` = this sentence |

**Three flags NOT added, deliberately.**

- **No `stores_invocation_attributes`.** `EDGES.md` §6 needed `stores_edge_attributes` because an edge payload is *optional* — an edge is a complete fact without one. **`Invocation.inputs` is not optional**: an invocation without its inputs is not a degraded record, it is not a record. A backend that cannot store the inputs cannot store invocations, and `stores_invocations=False` is the honest declaration. **One flag, not two, because there is no partial case.**
- **No `enforces_unique_invocation`.** `invocation_id` is generated **above** the store — `PACKAGE.md` §4.2's rule, already applied to `proposal_id`, `event_id` and `edge_id`, none of which has a flag either. A key the registry mints is unique by construction, so a flag would assert nothing.
- **No `stores_invocation_effects`.** Both effect lists are structural: an invocation whose `declared_effects` did not round-trip cannot answer §3.3's comparison, which is the mechanism. Same argument as the inputs.

**And no tenancy dimension, per R24 — stated because the action layer is where a reader will most expect one.** R24 ruled that *the protocol carries no tenancy dimension in v0; filtering is the host's job*, on the reasoning that `namespace` scopes a **vocabulary**, not a tenant. Actions do not change that and they sharpen it: **[Observed, beacon spec §10.7]** the blocker on customer-defined action surfaces is that `all_actions()` caches a process-global snapshot, so *"the action surface cannot vary per user or per tenant"* — and that is a fact about `registry.py`'s caching, one function's contract, not about this protocol. **This document is tenant-blind and says so**; §11 names the consequence for the enterprise story rather than pretending the omission is free.

### 8.1 What `stores_invocations=False` costs, and why the flag exists at all

An adapter written against the eighteen-primitive protocol has no invocation store, so the flag defaults `False` for the same load-bearing reason `EDGES.md`'s four do (`PACKAGE.md` §3.2): defaulting `True` would make every pre-existing adapter claim a store it does not have, and the registry would call `put_invocation` on an object without the method.

**And the three action flags inherit `C0-01`'s carve-out shape.** When `stores_invocations` is `False` the other two are **vacuous, not declined** — there is no invocation store, so *"why do you not index invocations by family?"* has no answer beyond the first sentence. Requiring two more `why` entries teaches an adapter author to write sentences nobody reads, which is how a `why` dict stops being a mechanism. This is `PACKAGE.md` §3.2's existing rule applied to a third group, not a new rule.

### 8.2 `action_transaction_scope` — R5 again, and the same binding rule

Ruling **R5** gives `transaction_scope: "owned" | "savepoint"`. The invocation store may be a different store from the type store — a host-owned audit table beside a package-owned registry is the obvious shape — so it gets its own declaration, with the rule `EDGES.md` §6.2 states and row 4b's second adversarial round found missing from its own printed block:

> **When the invocation store and the type store share a connection, `action_transaction_scope` MUST equal `transaction_scope`. A `Capabilities` declaring two different scopes on one connection is non-conformant.**

**`Capabilities.scope_conflict()` RETURNS the sentence; it does not raise** — the shipped method's own contract, *"so a `Capabilities` stays a plain frozen record that a test can construct in any shape it likes"*. Round 1 found the probe kit raising instead, which would have made the rule testable two incompatible ways. **With a third store there are now two independent pairs and `scope_conflict()` returns one sentence**; which one it names when both conflict is unspecified, and is recorded as **Q42** rather than decided here.

`action_store_shares_connection` is the **premise** of that rule and is declared up front rather than discovered. **[Observed]** `EDGES.md` §6's printed block omitted `edge_store_shares_connection` while `PACKAGE.md` §3.2 printed it and the code carried it — *a rule whose premise is unstated is a rule an adapter author can miss by reading* — and that omission cost an adversarial round. Repeating the finding one row later would be worse than the original.

Under `"savepoint"`, a `record_invocation` result carries `not_durable_until_host_commits:<why>` — `INTERFACE.md` §5.4's existing value, unchanged, on one more carrier. **No new warning value**, and the row-3d lesson applies verbatim: it is stamped at the **write** call site and **not** on `invocations`, because a signal that never turns off is noise. And it is stamped by `record_invocation` **itself**, not carried forward from anywhere — `EDGES.md` §6.2 records `retract_edge` getting exactly that wrong, and it is the second time this repo has seen the bug.



---

## 9. Adapter primitives — three, numbered 19–21

`PACKAGE.md` §3.4 has eighteen. This document adds **three**, and — as in `EDGES.md` §7.1 — that number is the strongest available evidence that §2.1's decision was right: **families need no new primitive, because `put_type` / `get_type` / `find_types` already serve them.**

```python
@dataclass(frozen=True)
class InvocationRecord:
    invocation_id:       str
    family:              str
    namespace:           str
    inputs:              dict            # JSON-serialisable. InputRef, 2.3
    declared_effects:    tuple           # JSON-serialisable. Effect, 2.5
    observed_effects:    tuple
    outcome:             str
    refusal_reason:      str | None
    gate_verdict:        str
    compensates:         str | None
    created_at:          datetime
    created_by_actor:    str
    created_by:          str
    model_tier:          str | None
    confidence:          float | None
    approved_by:         str | None
    approved_at:         datetime | None
    source_version:      str | None
    attr_schema_version: int | None
    warnings:            tuple[str, ...]

# 19
def put_invocation(self, record: InvocationRecord) -> None: ...

# 20
def get_invocation(self, invocation_id: str) -> InvocationRecord | None: ...

# 21
def find_invocations(
    self,
    *,
    family: str | None = None,
    namespace: str | None = None,
    actor: str | None = None,
    outcome: str | None = None,
    since: datetime | None = None,
    gate_verdict: str | None = None,             # 4's override query
    effect_undeclared: bool | None = None,       # 2.5's blast-radius query
    unreviewed: bool | None = None,              # 5.2's review queue
    after: tuple[datetime, str] | None = None,   # keyset: (created_at, invocation_id)
    limit: int = 100,
) -> InvocationPage: ...

@dataclass(frozen=True)
class InvocationPage:
    records:        tuple[InvocationRecord, ...]
    known:          int | None      # None = the BACKEND cannot count. Rule U
    complete:       bool
    why_incomplete: str | None
    next_after:     tuple[datetime, str] | None
```

**A `Page`, not a 2-tuple, and the reason is `known`.** §6.3 requires `InvocationReport.known` to be `int | None` because *a backend entitled to say "we did not count" must have somewhere to say it*. A `(page, truncated)` tuple gives the backend nowhere, so the façade could only ever report `len(rows)` — the falsification §6.3 forbids — or `None` by fiat regardless of what the backend knew. **Every other paging primitive in the package already returns this shape** (`EdgePage`, `TypePage`, `ProposalPage`, all with the same five fields); the 2-tuple was a round-1 finding and the fix is to stop being different.

> **The last three filters are round 2's, and the omission was §4's whole argument failing quietly.** They are the three reads a governance layer exists to serve, they were on the façade and on no primitive, and §8's *"the registry filters above the store"* therefore meant *read a page, then filter it* — which returned **zero overrides from a 2,399-row ledger that had one**. `unreviewed` pushes down as far as `reviewed_at IS NULL`; the half that asks whether the family is in `review` mode stays above the store, over a set of families the registry has already materialised, and the report says `complete=False` either way.

**Keyset-paged on `(created_at, invocation_id)`, the same key row 4b used for edges** — and for the same reason: an offset page over an append-only table shifts under a concurrent write, and an invocation ledger is append-only by construction. The registry does not expose the cursor (R25); the primitive has one so the façade can bound its own reads honestly.

**`compensates` is on the primitive and `compensated_by` is on the surface**, which is one fact stored one way and read the other. The store holds the forward pointer because the compensating invocation is written *after* the one it compensates and a store never rewrites a row (`INTERFACE.md` §5.8); the façade derives the backward pointer. **Stated because the asymmetry is real and a reader who saw only the surface would look for a field the store does not have.**

**`Evidence` and `history` are not on the record.** Evidence goes through `append_event`'s existing path with `invocation_id` set (§3.5), which is where `Provenance.history` already lives (`PACKAGE.md` §3.4 primitive 15). Putting them on `InvocationRecord` would give one concept two homes and would make a backend that stores invocations but not events undescribable.

### 9.1 One amendment to an existing primitive, and it is not free

**Primitive 15 gains an `invocation_id` filter**, and `EventRecord` gains the field it filters on:

```python
# 15, amended
def read_events(
    self, namespace: str, *, kind=None, name=None,
    proposal_id=None, edge_id=None, invocation_id=None,
) -> list[EventRecord]: ...
```

**This is not a fourth primitive and it is not a free change either.** `StorageAdapter` is `runtime_checkable`, and ruling **R30** records that `runtime_checkable` matches on method *names*: adding a **method** silently un-implements the protocol for a third-party backend, while adding a **keyword** to an existing one breaks any backend that implemented the old signature positionally or without `**kwargs`. `EDGES.md`'s `edge_id` made exactly this amendment in row 4b and `PACKAGE.md` §3.4 records what it cost — *"this line was stale for two adversarial rounds… a third-party author implementing `read_events` literally from this block hit a `TypeError` on the first `edge_provenance` call."*

**Round 1 found this document specifying `InvocationProvenance.history`, a `review` mode that reads it, and `read_events` as the way to read it — in a change that never touched `adapter.py`.** Both halves landed in the fix, with `PACKAGE.md` §3.3 and §3.4 amended in the same change and the async mirror regenerated.

### 9.2 The store — table, version and migration

**[Not specified by row #4 either, and that is not a defence.]** `EDGES.md` the spec printed `EdgeRecord` column for column and left the DDL to row 4b; this document does the same for `InvocationRecord`, and states the three things a build row must decide so they are decisions rather than discoveries:

| what | this row's position |
|---|---|
| table | `oo_invocation`, the ninth. `oo_event` gains `invocation_id`, which is an `ALTER`, not a recreate |
| store version | **5**. `PACKAGE.md` §9.2's rule stands: a store from the future is refused, never downgraded |
| `owns_schema=False` | `oo_invocation`'s column list joins the derived required-columns set that `_sql.py` verifies, exactly as `oo_edge`'s did — a check `PACKAGE.md` §9.3 records as having been added *after* a host store passed `migrate()` and then died on a raw driver error |

**Three fields need a serialisation decision the build row owns:** `inputs` (a dict of refs), the two effect tuples, and `warnings`. `PACKAGE.md` §4.5's `attributes` treatment is the obvious precedent and this row does not pre-empt it.

---

## 10. The tool-slot ceiling is a first-class design input

> **The rules of this section, numbered and each exercised or tagged** — ruling **R31**, standing constraint 8. The ids are *planned*; §14 says why the checker is not pointed here yet.

| # | rule | exercised by |
|---|---|---|
| 10-1 | `reachability` values are opaque strings in the host's vocabulary; the registry never interprets one | `C19-19` |
| 10-2 | The registry never chooses which families reach a surface — with `order=None` the report carries `counts` only, and **`order_source is None` is the marker**, not `complete`, which is `False` on every projection for the independent reason in rule 10-5 | `C19-20` |
| 10-3 | `counts` is rule-independent — a family declaring two ordered groups is counted in **both** and charged to **one** (`admitted`), and `counts` is identical under every permutation of `order` | `C19-21` |
| 10-4 | `rule="greedy_whole_group"` admits groups whole, in the caller's order, until `budget − reserved` is exhausted | `C19-22` |
| 10-5 | `consumers_at_risk` inherits `ConsumerReport.complete == False` and can never be a complete casualty list | `C19-23` |
| 10-6 | A projection whose `order` names only groups no family carries is refused with `action_family_unknown`, not answered with an empty report | `C19-24` |
| 10-7 | The 128 ceiling is a provider's and the registry neither enforces nor assumes it — `budget` is a caller's argument with no default | `C19-25` |
| 10-8 | `known` is the number of families this report **selected**, not the size of the registry | `C19-53` |
| 10-9 | An `order` naming groups no registered family carries **is a typo only when some family somewhere declares a surface at all**; a host whose families all declare `reachability=()` gets an answer with zeroes, and a `namespace` that happens to hold no such family is a legitimate scope | `C19-54` |
| 10-10 | A group repeated in `order` is charged **once**, so `fits` and `would_evict` can never intersect | `C19-58` |

### 10.1 The measurement, re-derived rather than cited

**[Observed 2026-08-29**, re-measured from `C:\Users\steph\projects\beacon` at this row's start; method published so a reader can re-run it.**]**

| fact | value | method |
|---|---|---|
| provider cap | `MAX_TOOLS_PER_REQUEST = 128` | `src/beacon/assistant/modes/multi_tool.py:2481` |
| effective budget | **127** | `budget = MAX_TOOLS_PER_REQUEST - 1`, twice (`multi_tool.py:2600`, `:2813`) — the array also carries `finalize_reply` |
| action modules | **222** | `ls src/beacon/assistant/actions/*.py`, excluding `_`-prefixed |
| categories | **19**, all of them used | `ALL_CATEGORIES` in `assistant/_base.py:355`; per-module first `category="…"`, defaulting to `common` |
| `task_detail`'s sum | common **45** + task **48** + project **21** + person **13** = **127** | the per-module count above; 45 = 14 explicit + 31 defaulted |
| read-only actions | **27** | `grep -rl 'reads_only=True'` |

The full per-category count, which sums to 222: task 48 · common 45 · calendar 23 · project 21 · shape 19 · person 13 · intake 10 · org 7 · report_source 6 · recurrence 6 · thing 4 · reminder 4 · aura 4 · goal 3 · connect_suggestion 3 · decision 2 · billing 2 · snooze 1 · pin 1.

**So the busiest page sits at exactly the budget, and beacon's own source says what that costs**: *"a 49th `task` tool evicts `person` outright, so shipping a `reorder_subtasks` ActionSpec would trade 'chat can reorder sub-tasks' for 'chat can no longer add a person to this task' — a bad trade, and a silent one"* (`assistant/coverage.py`, the sub-task drag-reorder exclusion). **[Observed]** two routes are excluded from the product on that arithmetic alone.

**This is mechanism C with a number attached.** A new action family is invisible on a surface that had no room for it, and the invisibility is silent — which is `FINDINGS-0.1`'s incident shape (*a producer emits a type; a consumer gates on its own private allowlist; the feature dies silently in the consumer that was not updated*) with a provider cap playing the allowlist. `INTERFACE.md` §5.1 exists because that failure was real; this section is the same failure, measured.

### 10.2 `reachability`, and the rule about who decides

`reachability: list[str]` on the family (§2.2) names the **surfaces** on which a host may expose it. The values are opaque strings in the host's own vocabulary — `INTERFACE.md` §2.7's posture for `model_tier`, and for the same reason: *the registry does not know what a surface is.* **[Observed]** beacon's `ActionSpec.category` is exactly this field, already present, already validated against a closed list, and already the unit its selector drops.

> **The rule, and it is not negotiable by a later revision: the registry never decides which families reach a surface.** That is the host's, always. What the registry can do is arithmetic the host is currently doing in a comment — count the families per group, apply an admission rule the caller supplies, and name what falls off the end. **Cause C, made visible, exactly as `consumers` makes it visible for types.**

### 10.3 `projection` — the call, and what it refuses to answer

```python
def projection(
    surface: str,                        # a LABEL for the report: the context being assembled
    *,
    budget: int,
    order: Sequence[str] | None = None,  # reachability groups, in the HOST's own drop order
    reserved: int = 0,                   # slots the host reserves for non-action tools
    namespace: str | None = None,
) -> ProjectionReport | Refusal: ...
```

```
ProjectionReport:
    surface:          str
    budget:           int
    reserved:         int
    counts:           dict[str, int]        # families DECLARING each group. RULE-INDEPENDENT:
                                            #   a family in two groups is counted in both
    admitted:         dict[str, int]        # families CHARGED to each group by `rule` --
                                            #   one slot each, in the first group they match
    rule:             str                   # "greedy_whole_group" -- 10.4
    order_source:     "caller" | None       # None = no order supplied. Rule U
    fits:             tuple[str, ...]       # groups admitted, in order
    would_evict:      tuple[str, ...]       # groups that do not fit, in order
    over_by:          int                   # 0 when everything fits
    consumers_at_risk: tuple[str, ...]      # consumer ids gating on an evicted family
    known:            int | None            # families this report SELECTED, not the
                                            #   whole registry. None = cannot count
    complete:         bool                  # Rule K
    why_incomplete:   str | None
```

**`counts` and `admitted` are two numbers because `reachability` is a `list`.** A family may declare two groups, and then *"how many families declare `alpha`?"* and *"how many slots does `alpha` cost under this order?"* are different questions with different answers. **Round 1 found `counts` changing with the order** — `{alpha: 2, beta: 2}` unordered, `{alpha: 2, beta: 1}` under one order and the mirror image under the other — which made §10.4's *"the useful half of this call is the counting"* rest on a guarantee that did not hold. No design test found it because **[Observed]** beacon's `ActionSpec.category` is a single string, so the fixture the section was built from cannot exercise it.

**Selection:** every registered, `active`, `kind="action"` family whose `reachability` intersects `order`. `surface` is a label recorded on the report, not a filter — a family does not know which *page* a host assembles, and asking it to would put the host's routing table in the registry.

**With `order=None` the call answers `counts` and nothing else.** `fits` and `would_evict` are empty, `order_source` is `None`, `complete` is `False`, and `why_incomplete` reads *"no order supplied; the registry does not choose which families reach a surface"*. **That is §10.2's rule made structural rather than promised.** The one question this document most obviously *could* have answered — *which 128?* — is the one it is built to be unable to answer.

**Refuses with `action_family_unknown`** when `order` names a group **no registered family anywhere carries** — a projection over an entirely unknown vocabulary is a typo, and an empty report for a typo is mechanism C committed by the call that exists to surface it. **The judgement is made against every registered family, not against the `namespace`-filtered pool**: an empty *namespace* is a legitimate scope and answers with zeroes, where an unknown *group* is a misspelling. Round 1 found the filtered version refusing a real projection over an empty namespace. When `order` names a mix of known and unknown groups, the unknown ones appear in `counts` with `0` and `complete` goes `False` with a `why`, because a host legitimately assembles a context from groups that happen to be empty today.

### 10.4 The admission rule is the host's convention, and the registry does one of them

`rule="greedy_whole_group"`: groups are admitted **whole**, in the caller's order, while `used + len(group) ≤ budget − reserved`. The first group that does not fit, and every group after it, is `would_evict`.

**Whole groups, because that is what the only observed host does.** **[Observed]** `_select_categories_for_context` *"bounds it by dropping whole categories"*, and the exclusions in `coverage.py` are written in exactly those terms (*"evicts `person` outright"*). A report computed under a rule the host does not use would be worse than no report.

**And it is still a policy, which is why `counts` is separate.** `counts` is rule-independent: it is *how many families carry each group*, which is true whatever the host does with them. A host that admits partial groups, or re-orders by usage, or reserves per-group, computes its own answer from `counts` and ignores `fits`/`would_evict`. **The split is deliberate — the useful half of this call is the counting, and the opinionated half is labelled `rule` so a caller can see that it is one.** §16 carries **Q36**: whether a second admission rule is worth having in v1, and the recommendation there is no until a second host exists.

### 10.5 `consumers_at_risk` — Cause C, one level along, and it is never complete

For every family in `would_evict`, the registry reads the family's `TypeEntry.predicates` and asks `consumers` who gates on them — `EDGES.md` §8's move, with no new mechanism and no new call. The answer names the code paths that will stop being reached when that group is dropped.

> **It is never complete, and the report says so.** `INTERFACE.md` §5.1: `ConsumerReport.complete` is **always `false`** in v0. So `consumers_at_risk` is a list of *known* casualties and never the list of *all* of them, `complete` on the `ProjectionReport` inherits the `false`, and a caller printing this number without the caveat is making a claim this document did not authorise. **That sentence is `EDGES.md` §13's first named weakness, and it applies here verbatim rather than being rediscovered.**

### 10.6 What this section does NOT do

- **It does not move the ceiling.** 128 is a provider's, and **[Observed, beacon spec §10.7]** the comment above the constant names OpenAI and Gemini's OpenAI-compat endpoint as both rejecting a larger array. Beacon's own document is careful that *"binds every live route"* is an inference with one unverified link (Azure Foundry's own cap is asserted by no source in that repo); this document inherits the caution rather than restating the claim more confidently than its source.
- **It does not subsume tools.** **[Observed]** 27 of 222 actions are `reads_only=True`, and beacon's §5.6 reads that as *"a typed traversal tool is the one kind of new tool that could subsume several narrow reads"*. That is a beacon product decision, it is Q3 in beacon's own §7, and nothing here takes it.
- **It does not rank.** No `priority`, no usage-weighted ordering, no *"drop the least-used"*. `usage()` exists and a host may order by it; the registry supplying an order would be deciding which 128.
- **It does not bound a RUN.** `limit` in §6.3 bounds a *read*. What an ingestion host actually wants bounded — datasets per run, rows, model spend, proposals minted — has no shape anywhere in this document, and §10 is not it. Named because round 2's ingestion lens looked here for it and the section's title invites that.

> **And §10 is the part of this document the venture's own customer deletes, which is worth saying in §10 rather than only in §17.5.** An ingestion pipeline has no chat surface, no tool array and no provider cap: `fits`, `would_evict`, `over_by`, `consumers_at_risk` and `rule` are five fields with no meaning for it, and `counts` is the only half that survives. **[Observed, round 2]** four ingestion families declared with `reachability=()` produced `counts={}` and a projection over the host's own surface name **refused** as a typo — rule 10-9 misfiring on a host that simply has no surfaces. That is fixed (the typo judgement now requires that *some* family somewhere declares a surface), and the larger fact is recorded rather than argued away: **the field §2.2 makes required on every family exists for the section its own customer does not use.** It stays required because an empty list is a *statement* — Rule U's standard, applied to §10's own field — and because §17.5's separability test is what makes that honest rather than costly.


---

## 11. Design test 1 — UC1 Tenshen: three of the 222 actions, expressed without moving one of them

**The subject [Observed 2026-08-29].** `beacon`'s assistant action registry: 222 modules, 19 categories, a `MAX_TOOLS_PER_REQUEST` of 128 and a busiest page at 127 (§10.1). Read-only; nothing in beacon is edited by this row, and **the test is whether three of its actions can be *described* as families while the code stays exactly where it is** — beacon spec §10.7's position, which this document is written to preserve rather than to overturn.

**Three actions, three categories, one of them `task`**, chosen so no two share a shape:

| action | category | `reads_only` | `undoable` | why this one |
|---|---|---|---|---|
| `add_task_stakeholder` | **`task`** | False | **True**, with an `undo` payload | writes an edge in a family `EDGES.md` §9 already maps, and its failure path collapses two causes into one code |
| `delete_person` | `person` | False | False — *"Not reversible via undo."* | the largest undeclared blast radius in the repo: **15** foreign keys reference `people.id` |
| `search_tasks` | `common` (defaulted) | **True** | False | the empty-effects case, and the one that tests whether `effects: []` can ever be honest |

### 11.1 Expected outcomes — **stated before the walk-through**

| # | Prediction | Expected |
|---|---|---|
| **T1.1** | All three express as `kind="action"` `TypeEntry` rows with the eight keys of §2.2, and **no beacon file changes** | **PASS.** If any of the three needs a field §2.2 does not have, §2.1's decision is wrong and this row should stop |
| **T1.2** | `add_task_stakeholder`'s failure path — *"task not yours or already linked"*, **one `code="mutation_failed"` for two unrelated causes** — splits under §2.4 | **PREDICTED PARTIAL, and the partiality is the finding.** *Already linked* is `edge_absent` and becomes a typed `precondition_unmet`. *Not yours* is **authorization**, which §1 rules out as the host's, so it stays inside the action. Expect one of two causes typed, and expect the other to be named as out of scope rather than quietly absorbed |
| **T1.3** | `delete_person` declares `reversibility="irreversible"`; declaring `approval_mode="auto"` alongside it is refused | **PASS**, `Refusal(reason="human_approval_required")` at **declaration**, per §2.2's one cross-field rule. Expect the refusal to fire at the declaration door and not only at `preflight` |
| **T1.4** | `delete_person`'s blast radius becomes partly declarable | **PREDICTED: 3 edge families declarable, the rest admitted unknown.** 15 FKs reference `people.id` — 7 `CASCADE`, 6 `SET NULL`, 2 with no `ondelete`. Expect **4 of the 7 cascades** to belong to three edge families (`person_links` twice — both legs — `task_stakeholders`, `project_stakeholders`) and to become three `retract_edge` effects; expect the remaining **11** FKs to be expressible only as `host_state` with a `why`. **From 0 declared to 3 declared plus a stated unknown** |
| **T1.5** | `delete_person` has a second effect nobody would guess from its SPEC | **PREDICTED YES.** `person_service.delete_person` calls `connection_service.unlink` when the person is a verified pair-binding, **and that call commits** before the delete. Expect a second `host_state` effect, and expect the design test to record that a mid-action commit is invisible to `reversibility` |
| **T1.6** | `search_tasks` declares `effects: []` honestly | **PASS.** `reads_only=True` and `covers_routes=[]` **[Observed]**. Expect `reversibility="reversible"`, `approval_mode="auto"`, `min_auto_tier=None`, and expect `preflight` to report `tier_floor=None` with a `why` rather than warning |
| **T1.7** | The 127/128 arithmetic reproduces through `projection` | **PASS, to the number.** `projection("task_detail", budget=127, order=("common","task","project","person"))` over beacon's real counts → `counts` = 45/48/21/13, all four in `fits`, `over_by=0`. Then a **49th** `task` family → `would_evict=("person",)`, `over_by=1`. Expect beacon's own comment reproduced arithmetically rather than quoted |
| **T1.8** | `projection(order=None)` answers `counts` and nothing else | **PASS**, `order_source=None`, `fits=()`, `would_evict=()`, `complete=False`, and a `why_incomplete` naming that the registry does not choose |
| **T1.9** | `consumers_at_risk` on the eviction | **PREDICTED EMPTY, AND THE EMPTY IS THE POINT.** Beacon registers no consumers in this registry, so the list is empty — and an empty list here reads as *"no casualties"*. Expect `complete=False` to ride with it, and expect the walk-through to say plainly that an empty `consumers_at_risk` is `ConsumerReport.complete == False` wearing a different name |
| **T1.10** | **The enterprise blocker.** §10.7: *"the action surface cannot vary per user or per tenant"* — `all_actions()` caches a process-global snapshot | **PREDICTED: OUT OF SCOPE BY R24, and expressing 222 actions as families does NOT unblock it.** R24 ruled the protocol tenant-blind; the blocker is `registry.py`'s caching, one function's contract. Expect the design test to name the consequence — *a customer-defined action surface needs a change in beacon **and** a tenancy dimension this protocol declines to have* — rather than to claim a fix |
| **T1.11** | **The household blocker.** §10.3's multi-actor access | **PREDICTED: UNTOUCHED.** Same reason. Expect no claim |
| **T1.12** | Nothing in beacon moves | **PASS expected.** The three families are declared in a registry *beside* beacon, about beacon's actions. Zero beacon files edited; the probe parses them read-only |

### 11.2 What a failure would mean

**T1.1 failing** would mean §2.2's eight keys are the wrong eight, and the honest response is to fix §2.2 rather than to contort beacon. **T1.7 failing** would mean §10's arithmetic does not describe the one product that has the problem, which would make §10 a hypothesis rather than a design input. **T1.10 producing a claimed fix** would be the worse failure: a spec that quietly acquires a tenancy dimension in a design test is a spec that overturned a ruling in a walk-through.


### 11.3 The walk-through — expected vs observed

**Method.** [`docs/tools/actions_beacon_probe.py`](../tools/actions_beacon_probe.py), **read-only** over `beacon`: the action modules and the model files are parsed as **text**, nothing in that repo is imported, executed or written, and the three families are declared in a registry *beside* it. `py docs/tools/actions_beacon_probe.py` → `ALL 22 CHECKS PASSED`.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T1.1 | all three express | three `ActionFamily` rows, eight keys each, no key missing and none added | **PASS** |
| T1.2 | one of two causes typed | `edge_absent(task, person, family="task_stakeholders")` carries the *"already linked"* half; the *"not yours"* half has **no** precondition kind and stays in the action | **PASS — partial, as pre-registered.** See contortion **ACT3** |
| T1.3 | refused at declaration | `Refusal(reason="attributes_schema_violation", detail={"door": "propose_type", "reversibility": "irreversible", "approval_mode": "auto"})` — **the value changed in round 1**, to R18's own (§2.2) | **PASS** |
| T1.4 | 3 declarable, the rest admitted | 15 FKs on `people.id` — **7 CASCADE / 6 SET NULL / 2 unspecified**, reproduced by the probe. **3 `retract_edge`** effects (`person_links`, `task_stakeholders`, `project_stakeholders`) + **2 `host_state`**, both carrying a `why` | **PASS — every number as pre-registered** |
| T1.5 | a second, unguessable effect | `person_service.delete_person` calls `connection_service.unlink`, and **that call commits** before the delete. Declared as the second `host_state` | **PASS — and it is the finding of this fixture** |
| T1.6 | `effects: ()` honestly | `search_tasks`: `reads_only=True`, `covers_routes=[]`, `effects=()`, `reversibility="reversible"`, `tier_floor=None` with a `why` | **PASS** |
| T1.7 | the arithmetic reproduces | cap **128**; `budget = MAX_TOOLS_PER_REQUEST - 1` appears **twice** in the source; **222** modules; **27** `reads_only`; **19** categories, all used, summing to 222 *(re-measured at 15:45 the same day: **223** and **20** — see §11.6)*; `counts` = common **45**, task **48**, project **21**, person **13** = **127**, `fits` all four, `over_by=0`. Then a 49th `task` family → `would_evict=("person",)`, `over_by=1` | **PASS — beacon's own comment, reproduced arithmetically** |
| T1.8 | counts only | `order_source=None`, `fits=()`, `would_evict=()`, `complete=False`, `why_incomplete="no order supplied; the registry does not choose which families reach a surface"` | **PASS** |
| T1.9 | empty, and the empty is the point | `consumers_at_risk=()` **and** `complete=False` with `why_incomplete` naming `ConsumerReport.complete == False` | **PASS** |
| T1.10 | out of scope by R24 | see below — **no fix claimed** | **PASS** |
| T1.11 | untouched | see below | **PASS** |
| T1.12 | nothing moves | module files parsed as text; zero beacon files edited | **PASS** |

**T1.5 is what this fixture contributed and no other could.** `delete_person`'s SPEC declares `undoable=False` and `covers_routes=["DELETE /api/people/{person_id}"]`. **[Observed]** the service beneath it does something neither field can express:

```
# beacon/src/beacon/services/person_service.py, delete_person
if person.linked_user_id is not None and person.link_verified_at is not None:
    await connection_service.unlink(...)     # <- this COMMITS
    person = await get_person(...)            # re-fetch, because unlink committed
await session.delete(person)
await session.commit()
```

**A mid-action commit is invisible to `reversibility`.** The family declares `irreversible`, which is true of the whole; it cannot say *"and the first half is already durable when the second half runs"*. Under `action_transaction_scope="savepoint"` (§8.2) the invocation record would carry `not_durable_until_host_commits` — which would be **false for the unlink and true for the delete**, one warning covering two different truths. Recorded as contortion **ACT5**, not designed away: expressing it would need per-effect durability, which is a field on `Effect` and a mechanism this row has no second fixture for.

### 11.4 T1.10 and T1.11 — the two blockers, restated as out of scope by **R24**, with the consequence named

**[Observed, beacon spec §10.7]:** *"`all_actions()` caches a **process-global snapshot** in `_REGISTRY`… **The action surface cannot vary per user or per tenant.** That, not hand-authorship, is what blocks customer-defined entity types — and it is a change to one function's contract, not a rewrite of 222 files."*

**[Observed, beacon spec §10.3]:** the household future's open question is **multi-actor access**.

**Ruling R24 is what this document obeys:** *the edge protocol carries **no tenancy dimension** in v0; filtering is the host's job… `namespace` scopes a vocabulary, not a tenant.* §8 applies it to invocations without softening it.

**So the honest statement is two sentences and neither of them is a fix:**

1. **Expressing beacon's 222 actions as families does not unblock a customer-defined action surface.** Two independent things are missing and this document supplies neither: beacon must change `all_actions()`'s contract (its own call, one function), **and** something must carry a tenant dimension, which R24 says is not the protocol. A reader who takes *"actions are now governed vocabulary"* to mean *"actions can now vary per tenant"* has read a claim this document does not make.
2. **The household blocker is untouched for the same reason.** Multi-actor access is *who may invoke*, which is authorization, which is §1's non-goal and R24's ruling in the same breath.

> **What this document *does* buy the enterprise story, stated so the section is not purely negative.** The blocker is one function's contract **plus** a vocabulary. This row supplies the vocabulary half — a customer-defined action is a `TypeEntry` proposed, resolved against the existing verbs, approved, and carrying declared effects and a tier gate — which is the half that had no shape at all. **[Inferred]** that the remaining half is smaller than it looks, on beacon's own reading that it is *"a change to one function's contract"*. **[Assumed]** that a tenancy dimension can stay outside the protocol when actions are involved; R24 is explicitly provisional on exactly this, and §16 carries it as **Q38** because *actions* are a stronger test of R24 than *edges* were: an edge written for the wrong tenant is a wrong row, and an action invoked for the wrong tenant is a wrong **effect**.

### 11.5 UC1 verdict

> **Expressible, with three contortions recorded and none designed away, and every pre-registered number reproduced.** The three families declare cleanly under §2.2's eight keys; the 127/128 arithmetic comes out of `projection` exactly as beacon's own source comment states it, including which category a 49th `task` tool evicts; and **nothing in beacon moved.**
>
> **What UC1 contributed that no other fixture could:** the mid-action commit (**ACT5**), the two-causes-one-code failure path (**ACT3**), and the largest real blast radius in the corpus — **15 foreign keys, of which this document can declare 4 and must admit 11.** *From nothing declared to three families declared plus a stated unknown* is the entire value proposition of `effects`, measured on the only host that exists.
>
> **What it did not exercise:** a `review`-mode family — beacon has no such state. `compensated` as an outcome is not exercised here either, and **it is exercised by UC3's probe as of round 1**. *(This sentence said it was "shown by UC3" while UC3's probe contained no compensation at all — a false claim in a walk-through, which `USE-CASES.md` calls a silent accommodation rather than a pass. Found by round 1's real-data lens; the probe now runs it, and the sentence names the round in which it became true.)*

### 11.6 The fixture moved under the design test, and that is a finding rather than an accident

**[Observed 2026-08-29]** the measurement in §10.1 was taken at **13:05** and re-taken at **15:45** on the same day. Between them beacon gained `src/beacon/assistant/actions/manage_life_event.py`:

| | pinned 13:05 | observed 15:45 |
|---|---|---|
| action modules | 222 | **223** |
| categories | 19 | **20** — a new `life_event` |
| `reads_only` | 27 | 27 |
| **`task_detail`'s sum** | **127** | **127** |

**The load-bearing number did not move, and the reason is the mechanism §10 describes.** The new action did not go into `task`, `common`, `project` or `person`; it went into a **new keyword-gated category**, which is exactly what `snooze`, `shape`, `pin` and `connect_suggestion` are — **[Observed]** each of them split out of a full category with a comment naming the cap (*"shipping it in `task` took task 48→49 and tipped common+task+project+person to 128"*). So the pressure §10 measures was live during this row and beacon's own release valve was used, without anybody involved knowing that a specification was being written about it.

**What the probe does about it.** `actions_beacon_probe.py` carries the 13:05 measurement as a **pinned observation** and prints a `FIXTURE DRIFT` line when it moves, while **asserting** the two things that are invariants rather than observations: *the categories sum to the module count*, and *`task_detail` still sums to the budget*.

> **And the pin is a commit SHA, not a clock reading — round 3's founder lens called the first version's excuse and was right.** It read *"this fixture is somebody else's live codebase and cannot be pinned"*, which is **false**: beacon is a git repository, `git -C … rev-parse HEAD` pins it exactly, and read-only access is all that takes. Row #4's rule — *a design test whose numbers move between runs is not a design test* — was written about a query that could be pinned with an `order` clause, and this one can be pinned with a SHA. The probe records **`a895a872`**, so a reader can check out the exact tree the 13:05 numbers came from. **Recorded as contortion ACT7, with its excuse removed rather than left in**: the *finding* — that the fixture moved and the ceiling held — is unaffected and is the half worth keeping.

---

## 12. Design test 2 — UC2 CMS: `flag_facility_for_review`, and the value the precondition cannot see

**CMS wins any conflict with Tenshen** (`ROADMAP.md`, rule of the ordering). Data: the checked-in 400-row Montana sample, `open_ontology/contract/fixtures/cms_sample_400.csv`, cut from the public CMS file by [`make_sample.py`](../tools/make_sample.py). Counts pre-registered in [`0.5-ground-truth-PREREGISTERED.md`](../findings/0.5-ground-truth-PREREGISTERED.md).

**The action.** `flag_facility_for_review(facility)` — one input, an `InstanceRef` to a `cms:entity:facility`; the intended precondition is *"this facility has at least one citation whose `Scope Severity Code` is in the Immediate-Jeopardy band `{J, K, L}`"*; the intended effect is an edge, not a property.

**Why this action and not another.** `scope_severity_code` is the value set **[Observed, `0.5-RESULTS.md`]** that the cheapest model tier **inverted** — reported that higher letters are less serious, when J/K/L are Immediate Jeopardy — with every number it produced still correct and nothing erroring. An action gated on that scale, invoked by that tier, unattended, is 0.5's failure with a write attached.

### 12.1 Expected outcomes — **stated before the walk-through**

| # | Prediction | Expected |
|---|---|---|
| **T2.1** | The family expresses under §2.2 | **PASS.** One `InstanceRef` input, `reversibility="reversible"` (a flag is an edge, and an edge retracts), `approval_mode="auto"`, `min_auto_tier` set |
| **T2.2** | **The severity precondition is expressible** | **PREDICTED NO — the central finding of this fixture.** §2.4's four kinds are about types, predicates and edges; *"a value of a column of a row"* is none of them. Expect contortion **ACT4**, and expect it to be recorded as the **third** surface reaching for `INTERFACE.md` contortion 11 / ruling **R22**, after `Consumer.gate` and `EDGES.md` Q17 |
| **T2.3** | The obvious modelling escape hatch — make severity an edge, `citation:42 --has_severity--> value_set:scope_severity_code` — is available | **PREDICTED REFUSED, at two layers**, by `EDGES.md` §2.4.1: the permissive family is refused **at declaration**, and a correctly declared family refuses the write with `endpoint_kind_mismatch` on `level`. Expect the refusal that CMS itself motivated to close the door CMS now wants open — and expect that to be recorded as consistency, not as a new hole |
| **T2.4** | What *is* expressible instead | **PREDICTED: `type_active` on the value set, and `edge_exists` on `cites`.** Both are conditions about the **vocabulary**, not about the data. Expect the walk-through to say so plainly rather than presenting them as a substitute |
| **T2.5** | `min_auto_tier="sonnet"`; an invocation by `ai:haiku_classifier` at tier `haiku` | **REFUSED**, `Refusal(reason="tier_below_action_policy")`, `detail` carrying both the actor's tier and the family's floor. **Nothing is recorded by `preflight`**; the host may record the refusal itself with `outcome="refused"` |
| **T2.6** | The same invocation at tier `opus` | **ALLOWED**, `approved_by="auto:<policy>"`, `approved_at` set — and `approved_by` is **never null** on the resulting `applied` invocation (§3.2) |
| **T2.7** | The floor with **no deployment-supplied tier order** | **PREDICTED REFUSED, and this is a pre-registered choice rather than a discovered one.** The registry does not know that `haiku` is below `sonnet` (`INTERFACE.md` §2.7). With no order, the floor cannot be evaluated; treating unknown as *satisfied* would let a mis-configured deployment auto-approve everything. Expect `precondition_unmet`-shaped honesty: a refusal whose `detail` says **unknown**, not **false** |
| **T2.8** | The fixture's numbers reproduce | 400 citations · 10 facilities · severity histogram **B 2 · C 5 · D 235 · E 82 · F 41 · G 31 · J 4** · **3 of 10** facilities carry an Immediate-Jeopardy (`J`) citation · **8 of 10** carry actual harm (`G` or above) |
| **T2.9** | The effect names an edge family that must already be registered | **PASS.** `add_edge` on `flagged_for_review`; declaring it before that family is registered as `kind="edge"` is refused at **declaration** with `edge_family_unknown` — `EDGES.md`'s existing value, not a new one (rule 2.5-7) |
| **T2.10** | 0.5's inversion is caught **twice**, by two independent gates | **PASS expected.** A Haiku-proposed *family* whose definition asserts the ordering carries `unverified_semantics` and is refused for auto-approval by `tier_below_auto_approve_policy` (`INTERFACE.md` §2.7); a Haiku *invocation* of the approved family is refused by `tier_below_action_policy` (§5.2). **Two different values, two different objects, one failure** — and if they turn out to be the same gate twice, §7's argument for a separate value is wrong |

### 12.2 What a failure would mean

**T2.2 coming out PASS** would mean this document grew a value-level query language without noticing, which is §2.4's stated boundary breached inside its own design test. **T2.3 coming out permitted** would mean `EDGES.md` §2.4.1's rule is not general after all, one row after that document spent an adversarial round making it general. **T2.10 collapsing to one gate** would mean §7's `tier_below_action_policy` is a duplicate and should be withdrawn.

### 12.3 The walk-through — expected vs observed

**Method.** [`docs/tools/actions_cms_probe.py`](../tools/actions_cms_probe.py) reads the checked-in 400-row sample, builds the `cites` edges through `edges_probe_kit`, declares the family through `actions_probe_kit`, and compares every count against the frozen ground truth. `py docs/tools/actions_cms_probe.py` → `ALL 21 CHECKS PASSED`.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T2.1 | expresses | one `InstanceRef` input, `reversible`, `approval_mode="auto"`, `min_auto_tier="sonnet"` | **PASS** |
| T2.2 | **NOT expressible** | `Precondition(kind="value_in_set", …)` raises *"is not one of ('type_active', 'predicate_holds', 'edge_exists', 'edge_absent') — the vocabulary is closed at four"* | **PASS — the pre-registered failure, and the central finding** |
| T2.3 | refused at two layers | the permissive family `has_severity` with `dst=("entity","value_set")` **raises at declaration**; the correctly declared family refuses the write with `Refusal(reason="endpoint_kind_mismatch", detail={... "problem": "level" ...})` | **PASS — both layers, on the fixture that motivated the rule** |
| T2.4 | vocabulary, not data | the one expressible precondition is `type_active("cms:value_set:scope_severity_code")` — *is the scale still in the vocabulary*, not *what does this facility score* | **PASS, and it is a weak substitute, which is the point** |
| T2.5 | refused | `Refusal(reason="tier_below_action_policy", detail={"state": "false", "tier": "haiku", "min_auto_tier": "sonnet"})` — `state` added in round 1, so a real below-the-floor refusal is distinguishable from the three unknown ones (§5.2) | **PASS** |
| T2.6 | allowed | `verdict="allowed"`, `approved_by="auto:action_policy"` | **PASS** |
| T2.7 | refused as **unknown** | `Refusal(reason="tier_below_action_policy", detail={"state": "unknown", "why": "no deployment tier order supplied; the registry does not order tiers (INTERFACE 2.7)"})` — **and round 1 added the other two unknowns**: no tier supplied, and a tier outside the order, which had been returning a confident refusal and an uncaught `ValueError` respectively | **PASS — the pre-registered choice, and `state` distinguishes it from a false** |
| T2.8 | the numbers | 400 citations · 10 facilities · **B 2 · C 5 · D 235 · E 82 · F 41 · G 31 · J 4** · Immediate Jeopardy at CCNs **275020, 275025, 275029** (3 of 10) · actual harm at **8** of 10 | **PASS — every pre-registered number** |
| T2.9 | refused at declaration | `Refusal(reason="edge_family_unknown", detail={"door": "declaration", "family": "not_registered"})` — `EDGES.md`'s value, no new one | **PASS** |
| T2.10 | two gates, two values | the invocation gate returns `tier_below_action_policy`; `INTERFACE.md` §2.7's proposal gate returns `tier_below_auto_approve_policy`. Different objects, different lifecycles, different values | **PASS — §7's argument for a separate value holds** |

**T2.2, stated without softening, because it is the finding.** The action this fixture exists to express is *"flag a facility that has an Immediate-Jeopardy citation"*, and **§2.4 cannot say the condition.** What it can say is that the scale is still in the vocabulary. **A gate on the vocabulary is not a gate on the data**, and presenting `type_active` as though it were would be exactly the confident wrong answer Rule U forbids.

**And the escape hatch is closed by a rule CMS itself wrote.** T2.3 confirms it at both layers: `EDGES.md` §2.4.1 refuses `citation --has_severity--> value_set` at declaration *and* at write. So there is no edge to hang an `edge_exists` on. **This document did not open a hole; it inherited a boundary and found it holds** — which is a consistency result, and the strongest version of it available, because the two rules were written by different rows against the same fixture.

> **Contortion ACT4, and it is now the third surface.** A value-level condition has no representation in: `Consumer.gate` (`INTERFACE.md` §10b.4, contortion 11) · edge consumer gates (`EDGES.md` Q17, ruled **R22** — *deferred to Phase 3, because both would make `Consumer.gate` a query language*) · and now `Precondition` (here). **Three surfaces, one missing mechanism, and this row still does not take it**, because R22 routed it and a spec row that takes a routed question in a design test is a spec row that overturned a ruling in a walk-through. **Q35** carries it with the count attached, and the count is the argument: R17 was granted on *two* fixtures reaching for one value.

**What the registry still buys on this fixture, measured rather than asserted.** With the precondition inexpressible, three mechanisms still fire on 0.5's exact failure: the family's definition asserting the A–L ordering carries `unverified_semantics` and is refused for auto-approval by tier (`INTERFACE.md` §2.7); an invocation by the cheap tier is refused by `tier_below_action_policy`; and a host that overrides either is enumerable by `invocations(gate_verdict="refused", outcome="applied")` — **1 override**, in the probe's own run. **The value the registry cannot see is gated by the tier that would have got it wrong.**

### 12.4 UC2 verdict

> **Expressible only in part, and the missing part is pre-registered, inherited and routed rather than discovered.** `flag_facility_for_review` declares, gates and records; its actual precondition does not exist in v0 and **cannot be modelled around**, because `EDGES.md` §2.4.1 closes the one detour — at declaration and at write, on the fixture that motivated the rule.
>
> **What UC2 contributed that no other fixture could:** the proof that the precondition vocabulary's boundary is *load-bearing* rather than convenient (T2.2 + T2.3 together), and the two-gates-two-values result that keeps `tier_below_action_policy` from being a duplicate of `tier_below_auto_approve_policy`.
>
> **CMS wins no conflict here, because there is none to win.** UC2 asks for a mechanism UC1 does not oppose; the refusal comes from a rule CMS itself forced in row #4. Recorded as **ACT4** and Q-numbered.

---

## 13. Design test 3 — UC3 NYC: `reconcile_borough`, whose effect is an edge and never a merge

**The subject [Observed 2026-08-28, re-verified 2026-08-29 by row #4].** Three datasets, three agencies, one word: **A** `uvpi-gqnh` (DPR trees, `data_updated_at` 2017-10-04), **B** `erm2-nwe9` (311 requests, 2026-08-28), **C** `693u-uax6` (DOT parking meters, 2026-08-24). Namespaces `dpr`, `oti_311`, `dot`. `EDGES.md` §11 wrote `A ≡ B` and `B ≡ C` as `equivalent_to` edges — **a chain, not a triangle**, because each publisher joins the one it found.

**UC3 conflicts are recorded as Q-numbered questions for the supervisor, never as R-numbers** (`USE-CASES.md` conflict rule).

**The action.** `reconcile_borough(a, b)` — two `TypeRef` inputs; precondition *there is an `equivalent_to` edge between them*; effect *write a `reconciled_with` edge*. **Never a merge.**

### 13.1 Expected outcomes — **stated before the walk-through**

| # | Prediction | Expected |
|---|---|---|
| **T3.1** | Two `TypeRef` inputs of `kind="value_set"` are legal | **PASS.** §2.3's `ref="type"` with `kinds=("value_set",)`. `predicate` would be refused; `value_set` is exactly the endpoint `EDGES.md` §2.4.1 permits at type level |
| **T3.2** | The precondition `edge_exists(equivalent_to, a, b)` is evaluated by `neighbors` and by nothing else | **PASS**, `PreconditionResult.evaluated_by == "neighbors"`, `known=1`. This is §2.4's no-query-language claim made mechanical |
| **T3.3** | **The precondition holds for `dpr ≡ oti_311` and FAILS for `dpr ≡ dot`** | **PREDICTED REFUSED for the two-hop pair, and this is the sharpest test in the document.** `equivalent_to` is symmetric and **not transitive** (`EDGES.md` §3.1); the precondition is a `depth=1` question. So an action **cannot manufacture the transitivity the edge family refuses**. Expect `Refusal(reason="precondition_unmet")` with `detail` naming the `edge_exists` condition |
| **T3.4** | Declaring `merge_types` as an effect | **REFUSED at declaration**, `Refusal(reason="effect_not_permitted")`. §2.5's general rule. **This is `ROADMAP.md`'s kill row arriving through a new door, and the door must be shut before the action exists rather than when it runs** |
| **T3.5** | **`merge_types` stays untouched.** With the `equivalent_to` edge present **and** `reconcile_borough` declared, approved and invoked, ask the **shipped** `Registry.merge_types(from_="borough", into="borough", namespace="dpr", into_namespace="oti_311")` | **STILL REFUSED**, `cross_namespace_merge`, non-overridably — **and again** under `acknowledge=["cross_namespace_merge","definitions_diverge"]`. `EDGES.md` T3.12 re-run with an action layer on top of it. Expect the check to run against `open_ontology.Registry`, not against the probe's own model |
| **T3.6** | The invocation's `created_by` | **`derived`** (**R17**), because a reconciliation driven by a deterministic rule over two type names has no human and no model in the loop. Expect **no contortion** — `EDGES.md` T3.8 hit this wall before R17 landed and had to claim `user`; expect the same shape to pass now, which is the ruling paying off one row later |
| **T3.7** | `source_version` carries both dataset versions | **PASS.** `"uvpi-gqnh@2017-10-04 / erm2-nwe9@2026-08-28"` on the invocation — **R21**'s field, and a nine-year gap between the two endpoints of one reconciliation |
| **T3.8** | Three namespaces, one invocation | **PASS.** The family is registered in `default`; `Invocation.namespace` is the **family's**, and the inputs keep their own — `EDGES.md` §2.2's rule inherited verbatim. Expect no new ambiguity |
| **T3.9** | `projection` over a cross-agency surface | **PREDICTED UNREMARKABLE, and worth checking anyway.** Namespaces and `reachability` surfaces are orthogonal; expect a projection whose `order` names one surface to include families from three namespaces, and expect that to be correct rather than surprising |
| **T3.10** | Anything UC3 wants that UC1 or UC2 does not | **PREDICTED: at most one, and it is Q-numbered rather than ruled.** UC3 is closest to the customer, so a conflict here is the supervisor's call — `USE-CASES.md`'s conflict rule |

### 13.2 What a failure would mean

**T3.3 coming out PASS** would mean the action layer manufactures transitivity `equivalent_to` refuses, and `reconcile_borough` should not ship. **T3.4 or T3.5 failing** is the kill row, reopened by this document — and unlike row #4, this document would have opened it with a *verb*, which is a door no previous row had. Either failure stops the row.

### 13.3 The walk-through — expected vs observed

**Method.** [`docs/tools/actions_nyc_probe.py`](../tools/actions_nyc_probe.py), using **two engines on purpose**, as `edges_nyc_probe.py` does: the **shipped** `open_ontology.Registry` on SQLite for everything about types — so T3.5's claim about `merge_types` is a claim about the real implementation — and the throwaway kits for edges and actions. Dataset ids, agencies and `data_updated_at` values are the ones row #4 pinned live; a design test whose numbers move between runs is not a design test. `py docs/tools/actions_nyc_probe.py` → `ALL 19 CHECKS PASSED`.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T3.1 | two `value_set` `TypeRef` inputs are legal | both declare; `InputSpec(kinds=("predicate",))` raises *"`predicate` may not be an input kind — EDGES 2.4.1's rule inherited"* | **PASS, both halves** |
| T3.2 | `neighbors` and nothing else | `PreconditionResult.evaluated_by == "neighbors"`; the adjacent pair is `allowed` | **PASS — §2.4's no-query-language claim, mechanical** |
| T3.3 | **refused for the two-hop pair** | `Refusal(reason="precondition_unmet", detail={"state": "false", "kind": "edge_exists", "subject": "a"})` for `dpr ↔ dot` — **while `neighbors(dpr, ["equivalent_to"], depth=2)` reaches `dot:value_set:borough` perfectly well** | **PASS — the sharpest result in the document** |
| T3.4 | refused at declaration | `Refusal(reason="effect_not_permitted", …)` at **each of the three shipped doors** — `propose_type`, `approve`, and `import_types`, which cannot refuse and so returns `import_refused:effect_not_permitted` with nothing written. *(The first draft checked one door and §17 audited three; round 1 imported an **active** family declaring `merge_types` through the shipped registry with no warning at all.)* | **PASS** |
| T3.5 | the **shipped** `merge_types` still refuses | `Refusal(reason="cross_namespace_merge")` with the `equivalent_to` **and** the `reconciled_with` edge present — **and again** under `acknowledge=["cross_namespace_merge","definitions_diverge"]` | **PASS — the load-bearing check, against `open_ontology.Registry`** |
| T3.6 | `derived`, no contortion | `InvocationProvenance.created_by == "derived"`, actor `derived:catalogue_rule` | **PASS — R17 paying off two rows later** |
| T3.7 | both versions | `source_version == "uvpi-gqnh@2017-10-04 / erm2-nwe9@2026-08-28"` | **PASS** |
| T3.8 | family's namespace, inputs keep theirs | `Invocation.namespace == "default"`; inputs in `dpr` and `oti_311` | **PASS — `EDGES.md` §2.2's rule inherited, no new ambiguity** |
| T3.9 | unremarkable | one surface, `counts={"catalogue_console": 3}`, three families in three namespaces, nothing evicted | **PASS** |
| T3.10 | at most one Q-numbered conflict | one: **Q38**, whether R24's tenancy ruling survives contact with actions | **PASS** |

**T3.3 is the result this fixture exists for, and it is worth spelling out.** `equivalent_to` is symmetric and **non-transitive** (`EDGES.md` §3.1). The write order is a chain — `A ≡ B`, `B ≡ C` — because each publisher joins the one it found. `neighbors(depth=2)` therefore **reaches** `dot:borough` from `dpr:borough`, and `EDGES.md` §4.4's `at_depth` is what stops that report from reading as an equivalence class.

**An action is a much sharper test of that than a report is**, because an action *writes*. If `reconcile_borough`'s precondition had been satisfied by reachability, the action would have written a `reconciled_with` edge between two types **nobody asserted were equivalent** — manufacturing, in one call, the transitivity the edge family spent a design test refusing. It is refused because the precondition is a **`depth=1`** question and §2.4 has no kind that means *reachable*. **That absence is now load-bearing**, and §16 records it as a rule not to relax: an `edge_reachable` precondition kind would be transitivity with extra steps.

**T3.4 and T3.5 together are the kill row checked at two different doors.** T3.4 is new: a *verb* is a door no previous row had, and `merge_types` in an `effects` list is `ROADMAP.md`'s kill row with a governed, approved, tool-shaped wrapper around it. It is refused **at declaration**, so the action never exists rather than being refused when it runs. T3.5 is `EDGES.md` T3.12 re-run with the action layer on top, against the shipped registry: still refused, still non-overridable.

### 13.4 UC3 verdict

> **Expressible, no contortion, and the one thing it proves is a negative: an action cannot manufacture the transitivity `equivalent_to` refuses.** `reconcile_borough` declares with two `value_set` type refs, gates on a `depth=1` `equivalent_to` question answered by `neighbors` and by nothing this document invented, and writes an edge. Declaring `merge_types` as an effect is refused at the declaration door; the shipped `merge_types` still refuses `cross_namespace_merge` twice with both edges present.
>
> **What UC3 contributed that no other fixture could:** T3.3 — the demonstration that the precondition vocabulary's *absence* of a reachability kind is load-bearing rather than an oversight — and the second door on the kill row.
>
> **One question for the supervisor, Q-numbered per `USE-CASES.md`'s conflict rule:** **Q38**, whether **R24**'s tenancy ruling survives contact with actions, since an edge written for the wrong tenant is a wrong row and an action invoked for the wrong tenant is a wrong *effect*. UC3 conflicts with neither UC1 nor UC2 on anything else.

---

### 13.5 The nine contortions, recorded and **not** designed away

| # | Contortion | Where | Why it was not designed away |
|---|---|---|---|
| **ACT1** | **One `AttributeSchema` mechanism governs two different objects** — the per-kind schema validates the *family's* eight keys, the name-level schema validates an *invocation's* inputs — and `PACKAGE.md` §5.2's key has no field saying which | §2.7 | It works because the two objects never share a store, which is a fact **outside** the mechanism. Adding a discriminator to `AttributeSchema` is a change to `PACKAGE.md` for one caller's convenience |
| **ACT2** | **`ResolveContext` is column-shaped, so resolving a verb runs on less signal than the mechanism was built for.** `sample_values` has no filler for an action, and `sibling_columns` — *"carries most of the signal"* — is empty | §5.1 | An action-shaped `ResolveContext` would be a second context object for one call. Recorded so that a weaker `resolve_type` on `kind="action"` is a known limit rather than a surprise |
| **ACT3** | **`add_task_stakeholder`'s two causes split unevenly**: *"already linked"* becomes a typed `edge_absent`; *"task not yours"* has no precondition kind and stays inside the action | §11.3 T1.2 | Authorization is §1's non-goal and **R24**'s ruling. Making it a precondition would put a permissions model in the registry through the side door |
| **ACT4** | **A value-level precondition is not expressible**, and this is the **third** surface to reach for the same missing mechanism | §2.4, §12.3 T2.2 | Ruling **R22** routed it to Phase 3 with contortion 11. Taking it here would be a query language arriving in a design test. **Q35** carries it with the count |
| **ACT6** | **`type_active` cannot use `resolve_type`, and its negative answer is unknowable at reasonable cost.** `resolve_type` needs a tier and a column-shaped context `preflight` does not have (**ACT2**); `list_types` has no `name` filter and a filtered listing is incomplete, so a **miss** is `None` plus a `why` rather than `False` | §2.4, §6.1 | A `name` filter on `list_types` is a change to `INTERFACE.md` §5.6 for one caller, and the mechanism that would make the negative cheap is the same one Phase 3's paging decision touches. **Q41**. Found by round 1's integrator lens asking which planned ids it could actually write |
| **ACT7** | **The UC1 fixture is a live codebase and moved during the row.** beacon gained an action between the 13:05 measurement and the 15:45 re-run: 222 → 223 modules, 19 → 20 categories | §11.6 | It cannot be pinned — it is somebody else's repository. The observation is dated, the invariant is asserted, and the movement is printed. **And `task_detail` still summed to 127**, because the new action went into a new keyword-gated category, which is the mechanism §10 exists to describe |
| **ACT8** | **A precondition cannot ask a question about the invocation ledger this document itself adds.** *"Have I already ingested this dataset at this version today?"* — the single most natural precondition an ingest run has — has no kind, and §1 rules out an idempotency key by name in the same breath | §2.4, §16 **Q44** | It is a fifth precondition kind reading a fifth store, and **R22** does not route it: R22 is about *value-level* conditions, and this is a *ledger* condition. Found by round 2's ingestion lens writing the seven preconditions a real NYC ingest action needs and finding **one** of them expressible |
| **ACT9** | **`host_state`'s identity is string equality on prose, and the cost scales with its share of the effect list.** Two admissions differing by a full stop, a capital letter or an interpolated row count are two effects | §2.5, §3.3 | §2.5 states the cost; round 2 measured how it scales — ~2 of 5 effects on UC1's `delete_person`, ~9 of 10 at ingest. The alternative is a slug field on `Effect`, which is a sixth key for a case one fixture has. **Q46** |
| **ACT5** | **A mid-action commit is invisible to `reversibility`.** `delete_person` commits an `unlink` before its own delete; one `not_durable_until_host_commits` warning would be false for the first half and true for the second | §11.3 T1.5 | Per-effect durability is a field on `Effect` and a mechanism with one fixture behind it. **[Observed]** once, in one host; one observation is not a design input |

---

## 14. Standing constraint 8, from the start — the planned `C19` group

**Ruling R31** (standing constraint 8): *every numbered rule in a spec section ships with either (a) a contract id that exercises it, or (b) an explicit `prose-only` tag with the reason — and `check_spec_drift.py` fails on a rule with neither.* The ruling names this row by name: *"and to #6 (actions spec) as it is written."*

**Every numbered rule in this document carries one or the other, from the first draft rather than retrofitted.** Eight sections, **61** numbered rules: **57** name a planned contract id, **4** carry a `prose-only:` tag with a reason. *(47 / 43 / 4 in the first draft; round 1 added eleven and round 2 three, every one of them a defect the round found.)*

| section | rules | ids | prose-only |
|---|---|---|---|
| §2.2 the declared shape | 5 | `C19-26` … `C19-28`, `C19-44` | 1 — an absence has no test that knows what to look for |
| §2.4 preconditions | 9 | `C19-01` … `C19-05`, `C19-45` … `C19-47` | 1 — **ACT4**, routed to Phase 3 by **R22** |
| §2.5 effects | 9 | `C19-06` … `C19-12`, `C19-48`, `C19-49` | 0 |
| §3 invocations | 6 | `C19-29` … `C19-33` | 1 — a value that does not exist |
| §5.2 the gate | 7 | `C19-13` … `C19-18`, `C19-50` | 0 |
| §6 the calls | 8 | `C19-34` … `C19-38`, `C19-51`, `C19-52` | 1 — **R25** routed paging |
| §8 capability flags | 5 | `C19-39` … `C19-43` | 0 |
| §10 the ceiling | 9 | `C19-19` … `C19-25`, `C19-53`, `C19-54` | 0 |
| **total** | **61** | **57** | **4** |

> **The tables moved in round 1, because five of the eight were unreachable from the section they belong to.** `check_spec_drift.py`'s `_section` reads from a heading to the **next heading of any level**, so a table sitting at the end of §3.5 is invisible to a checker asked about §3. **Thirty of the forty-seven rules were unreachable** and the mapping §14 promised could not have been wired to the checker it names. The five tables now sit directly under their own top-level heading, which is where `_section` can see them; the arrangement is verified by running that function's own code against this document.

> **These ids are PLANNED and nothing claims them yet, and that has an operational consequence the build row must not trip over.** `check_spec_drift.py`'s `R31_SECTIONS` currently lists three `EDGES.md` sections, and its `_check_rule_coverage` fails a rule whose named id *"no test in the suite claims"*. **Pointing it at this document today would fail fifty-seven times.** So `ACTIONS.md` is **deliberately not added to `R31_SECTIONS` in this change** — the extension lands in the build row, in the same change that lands the tests, which is the only order in which the gate is ever telling the truth. **Stated because the alternative failure is worse than the obvious one**: a checker wired up early gets silenced, and a silenced checker is how `gate_unregistered` went eighteen-said-nineteen-meant for a row (`INTERFACE.md` §5.4).
>
> **And nothing holds this document's ELEVEN printed shapes, which is a different gap in the same place.** `check_spec_drift.py` compares `INTERFACE.md`'s, `PACKAGE.md`'s and `EDGES.md`'s printed shapes against the code; it does not read this file at all, and there is no code to hold it against until the build row. **Round 1 found five drifts between this document and its own probe kit** — `Precondition.namespace`, `Invocation.compensates`, `InvocationProvenance.evidence`, and two call signatures — inside the section that argues field names were kept ugly *because* that is the drift the checker was written to catch. All five are fixed; the gap stays until the build row, and it is named here rather than discovered there.

**What the build row inherits, precisely:** a `C19` group of **57** ids, section-mapped above and row-mapped in the eight tables; **4** `prose-only` tags whose reasons are the argument, not a shrug; and the four probes in [`docs/tools/`](../tools/), whose **93** checks are the executable form of most of the 54 and should be **transposed into the suite rather than re-derived** — that is row 4b's own recorded lesson, where ten BLOCKING findings had been fixed *only* in a throwaway probe kit the package does not import.

---

## 15. Which mechanism this is designed against, and what would change it

### 15.1 The mechanism

**Primarily mechanism 1 — no review — and that is `INTERFACE.md`'s answer rather than `EDGES.md`'s.** `EDGES.md` §12 inverts the ranking for edges and puts **C** first. Actions invert it back, and the reason is what an action *is*:

| Mechanism | Status for ACTIONS | What answers it |
|---|---|---|
| **1** no review | **Dominant.** A verb is the highest-consequence thing anyone can add to a vocabulary: a noun that nobody reviewed describes something wrongly, and a verb that nobody reviewed *changes* something wrongly. **[Observed]** beacon's 222 actions arrive by *"drop a new file in `actions/`; no edits to this file required"* — a documented, deliberate, unreviewed-by-the-vocabulary write path | §2.1 — a family is a `TypeEntry`, so `propose_type` → `approve`/`reject` applies unchanged. §5.2's `approval_mode`, and §2.2's one cross-field rule making `irreversible` require a person |
| **C** silent drop | **Co-dominant, and measured rather than assumed.** §10.1: the busiest page is at **127 of 127**, and beacon's own source excludes two routes on that arithmetic. A new family is silently unreachable on a full surface — 0.1's incident shape with a provider cap playing the allowlist | §10 — `reachability`, `projection`, `would_evict`, `consumers_at_risk`. **Cause C made visible, the way `consumers` makes it visible for types** |
| **3** never retired | Present | Families retire like any type; `usage`/`orphaned` answers *"has anything invoked this in a year?"*, which **[Observed]** nothing in beacon can answer today |
| **2** could not find | Present | `resolve_type` on `kind="action"` — with contortion **ACT2**'s caveat that a verb resolves on less signal than the mechanism was built for |
| **4** collision | Present, and **not** aggravated | `namespace`. §13 shows an action refusing to manufacture an equivalence the edge layer refuses, which is mechanism 4 *not* arriving through the new door |

**No single call is the centre, and for actions that is easiest to see of the three documents.** There are two writes, one read and one arithmetic call. The centre is the *family* — the decision that a verb is a governed word — which is not a call at all.

### 15.2 What would change this

| If… | Then | What changes here |
|---|---|---|
| **A family needs a field the registry must READ to decide what to RUN** | §2.1 is wrong | `kind="action"` stops being a word and wants its own table and its own calls. §2.5's `effects` is the pressure point, and it stays on the near side deliberately |
| **A second fixture needs a value-level precondition** | **ACT4** stops being routable | The count reaches four surfaces and **R22**'s deferral should be revisited *for every surface at once*, never for this one alone — the reason R22 gave |
| **A host reports `observed_effects` dishonestly, or not at all** | §3.3's mechanism is decorative | The ledger still exists; the blast-radius comparison does not. Nothing here can detect it, and the answer would be an executor, which is §1's first non-goal |
| **Nobody ever runs `invocations(gate_verdict="refused", outcome="applied")`** | §4's argument is worth zero | The gate is advisory by construction and this is the assumption it rests on. **[Assumed]**, untested, and the same one `consumers`' `complete: false` friction rests on |
| **The 128 ceiling moves, or a provider drops it** | §10 loses its motivating fixture | `reachability` and `projection` stay useful — a bounded surface is not only a provider's bound — but the urgency goes, and §10 should be re-argued from something other than beacon's arithmetic |
| **R24 is revisited and the protocol gains a tenancy dimension** | §8's tenant-blindness is wrong | Every shape here gains a dimension and `projection` gains a filter. **Q38** says actions are a stronger test of R24 than edges were, and this row does not decide it |
| **An `edge_reachable` precondition kind is proposed** | §13's T3.3 result is undone | **Refuse it.** Reachability is transitivity with extra steps, and §2.4's absence of that kind is what stopped an action from writing an equivalence nobody asserted |
| **`approval_mode` needs a fourth value** *(a two-person rule, a quorum)* | §5.2's three are the wrong three | It is a policy language arriving one value at a time, and the right answer is probably to make `approved_by` a list before making the mode vocabulary bigger. Not taken; no fixture needs it |
| **Beacon registers its actions as families for real** | the fixtures stop being read-only | Everything in §11 becomes a live integration rather than a walk-through, and **ACT5** (the mid-action commit) is the first thing that would bite |

**Weaknesses named now so they are not discovered later:**

- **`observed_effects` is unverifiable.** §3.3 says so; it is repeated here because it is the single most over-readable sentence in the document.
- **The gate cannot enforce.** §4 says so at length. A deployment that never queries the overrides gets a ledger and no governance.
- **`projection`'s admission rule is one host's convention.** `counts` is the rule-independent half and `fits`/`would_evict` are labelled — but a caller who reads only the latter is trusting beacon's category-dropping behaviour without knowing it.
- **`min_auto_tier` assumes a total order per deployment**, inherited from `INTERFACE.md` §2.7's own **[Assumed]**, and it may be wrong for mixed vendors. §12 T2.7 makes the *absence* of an order honest; it does not make a partial order work.
- **Nothing sizes the invocation ledger.** An append-only record of every invocation of every family grows without bound, and no retention story exists — the same weakness `EDGES.md` §13 records for retracted edges, one object along.

---

## 16. Questions for the supervisor — **Q35 onward**

Numbering continues from Q34 (ruled as R39). None of these is taken on this document's authority.

| # | Question | Recommendation | Founder-visible? |
|---|---|---|---|
| **Q35** | **A value-level condition now has THREE surfaces reaching for it** — `Consumer.gate` (contortion 11), edge consumer gates (Q17, ruled **R22**), and now `Precondition` (**ACT4**). R17 was granted on **two** fixtures reaching for one missing value | **Do not take it in a spec row; re-open R22 in Phase 3 with the count attached.** R22's own reasoning — *both would make `Consumer.gate` a query language* — is still right, and the third surface strengthens the case for deciding all three **together** rather than for deciding one now. The recommendation is that Phase 3's decision be scoped to *all* gates, not to preconditions | **Yes** — it is the third instance of one gap and it now blocks a design test's central case |
| **Q36** | **`projection`'s admission rule is one host's convention** (§10.4). Is one rule enough for v0, or does the report need to carry two? | **One, for v0.** `counts` is rule-independent and a host with a different rule computes from it. A second rule invented before a second host exists is the framework-before-the-problem failure `ROADMAP.md` standing constraint 2 names | No |
| **Q37** | **`InvocationProvenance` drops `imported_from`** (§3.2), so a host with a year of undo records has no way to import them as invocations | **Add it in v1, not now.** It is additive and defaults `None`, exactly as **R21**'s `source_version` was — but nothing needs it yet, and `Provenance` gained its field only when a *second* shape had it and drifted. Record the omission and take it when a migration asks | No |
| **Q38** | **Does R24's tenancy ruling survive contact with actions?** R24 ruled the protocol tenant-blind on the reasoning that `namespace` scopes a vocabulary, not a tenant, and that a host filters inside its adapter. **An edge written for the wrong tenant is a wrong row; an action invoked for the wrong tenant is a wrong EFFECT** — and §11.4 shows beacon's enterprise blocker sitting exactly there | **Keep R24 for v0 and flag it as the ruling most likely to be revisited.** R24 is already explicitly provisional (*"Phase 4 may force a dimension"*). Nothing here should take it unilaterally, and beacon's 2B harness is the evidence that decides it | **Yes** — it gates the enterprise story, and R24 is founder-visible already |
| **Q39** | **The gate is advisory by construction** (§4). Should a deployment be able to declare *"invocations of this family MUST carry a `gate_verdict` of `allowed`"* — i.e. `record_invocation` refusing an override? | **No in v0, and the reason is the one §2.5 gives twice.** Refusing to record an override destroys the evidence that the override happened, which is worse than recording it. The enforcement a deployment wants belongs at the executor, which this protocol does not have | **Yes** — promoted by round 3's founder lens, and the reason is commercial rather than technical: it decides **whether the compliance-and-operations arm sells enforcement or evidence** (`VISION.md` §7). §4's answer is *evidence*, and that is a product decision wearing an engineering question's clothes |
| **Q40** | **A ninth key, `retention`, on the family.** The invocation ledger grows without bound (§15.2) and nothing sizes it | **Record it, do not take it.** It is the same question `EDGES.md` §13 records for retracted edges and `INTERFACE.md` has for events; three objects with one retention question want **one** answer, and taking it here would give the third object a mechanism the first two lack | No |
| **Q41** | **`type_active` has no cheap negative** (**ACT6**): `list_types` has no `name` filter, and a filtered listing is incomplete, so a *miss* is `None` plus a `why` rather than `False`. Should `INTERFACE.md` §5.6 gain a `name` filter? | **Yes in v1, and not in this row.** It is one additive keyword on a call this document does not own, `TypeQuery.name_in` already exists at the adapter level, and the façade is the only thing missing it. Taking it here would be a spec row amending another document's call surface for its own convenience | No |
| **Q42** | **`Capabilities.scope_conflict()` returns one sentence and there are now two independent store pairs** (type/edge and type/action). Which conflict does it name when both are wrong? | **Record it; do not decide it here.** A list return is the obvious answer and it changes a shipped method's signature for a case no backend has yet produced | No |
| **Q43** | **Does the invocation LEDGER page, and is that R25's question?** R25 names `list_types` and `neighbors`; §6.3 widened it to *"every listing"*, and round 2's ingestion lens argued the ledger is a different **object** — unbounded by construction where a vocabulary is bounded by curation, and already carrying the keyset cursor on primitive 21 | **Route it to R25's own Phase 3 decision, with the difference stated.** The recommendation is that Phase 3 decide paging for `list_types`, `neighbors` **and** the ledger together, and that it treat the ledger as the case that forces a retention answer as well as a paging one (**Q40**) | No — **demoted by round 3's founder lens**: paging is already routed to R25's Phase 3 batch, and a decision the founder has delegated does not come back for a second signature |
| **Q44** | **A precondition cannot ask about the invocation ledger** (**ACT8**). Idempotency — *"skip the 1,800 datasets I did yesterday"* — is the natural case, and **R22** does not cover it | **Do not take a fifth precondition kind in v0; route it to Phase 3 with Q35.** But record that it is a *different* gap from ACT4: R22 deferred **value-level** conditions, and nothing has ever ruled on a condition over this document's own store | **Yes** — it is the ingestion loop's most-wanted precondition and the venture's own consumer named it |
| **Q45** | **Should `propose_type(kind="predicate")` ever auto-approve?** Round 2's reviewer proposed that it always return a `Proposal`, never a live `TypeEntry`, on any namespace policy | **`INTERFACE.md`'s to rule on, not this document's — and the recommendation is yes.** §2.5's own line is *"an action may PROPOSE; only a human, or an auto-policy a deployment set deliberately, may APPROVE"*, and a capability predicate is the one kind where an auto-policy approving is the kill row. The guard fix landed in this row makes it belt-and-braces rather than load-bearing, which is why it is a question and not a change | **Yes** — it narrows `INTERFACE.md` §5.4's auto-approval path for one kind |
| **Q46** | **`host_state` effects are identified by their prose** (**ACT9**). A slug field would fix it | **No in v0.** A sixth key on `Effect` for a case one fixture has, and the cost is stated in §2.5 rather than hidden | No |

**Two more from round 3's founder lens, recorded here because neither is this document's to take:**

| # | Question | Recommendation | Founder-visible? |
|---|---|---|---|
| **Q47** | **Should §10 be cut entirely?** Round 3's founder lens would cut it — the `projection` call, `ProjectionReport`'s thirteen fields, `consumers_at_risk`, ten numbered rules and the `reachability` key they force onto every family — on the grounds that §17.5 already concedes it is separable, §10.6 concedes *"the part of this document the venture's own customer deletes"*, and it is `VISION.md` §10's failure mode at section scale: *a general bounded-surface calculator, built because one specific host had 222 actions and 127 slots.* | **Not this row's call, and not taken here — the brief for row #6 required it** (*"the tool-slot ceiling is a first-class design input"*), and a spec row does not delete a section its own brief mandated on a reviewer's recommendation. **The argument is strong and is recorded whole rather than rebutted.** The counter is that §10.1 is the one **[Observed]** measurement this row added — 128 / 127 / 222 / 19 / 27, two product routes excluded on that arithmetic, and §11.6's live confirmation — and measurements are not usually the part to cut. If the founder agrees with the lens, cutting §10 takes the family to **seven** keys and is a clean excision, which §17.5 exists to guarantee | **Yes** — it is a third of the document and the brief and the reviewer disagree |
| **Q48** | **Should `VISION.md` §7's compliance arm name a first deliverable?** The lens proposes: *a monthly signed override census*, run as `invocations(gate_verdict="refused", outcome="applied")`. §4's weakest **[Assumed]** is that *an operator who can see the override count will act on it* — and the paid arm removes that assumption **by being the operator**. | **Yes, and it is the founder's edit to make, not mine.** `VISION.md` §7 is the business model and a spec row does not amend it. Recorded because it converts this document's most-conceded weakness into a line item priced against staff time, exactly as §7 argues the rest of the arm should be — and because it can be sold before any of this ships | **Yes** — it is a change to the business model |

---

## 17. Kill-criterion check — required, and not skipped

**`ROADMAP.md`'s kill row:** *"A capability predicate gets merged as a duplicate → Stop."* And the rule of the ordering: *nothing may take a shape because Tenshen has it.*

**Neither is tripped, and here is the mechanical form of both.**

**1. Can an action merge anything?** **No, and it is refused at all three declaration doors rather than at the write.** `merge_types` is one of the six governance calls §2.5 excludes from the effect vocabulary as a **general rule**, not a family's opt-in. §13 T3.4 declares a family with `Effect(op="merge_types", …)` at **`propose_type`, `approve` and `import_types`** and is refused at each — the third returning `import_refused:effect_not_permitted` with nothing written, because `import_types` returns entries and cannot return a `Refusal`. **This is a door no previous row had** — a verb is a governed, approved, tool-shaped wrapper, and a merge inside one would be the kill row with a permission slip.

> **This paragraph counted THREE doors and named none of them, and round 1 walked through the one it had not thought of.** A reviewer used the shipped `Registry.import_types` to land an **active** `kind="action"` family declaring `merge_types` as an effect *and* breaching §2.2's cross-field rule, with **no warning at all** — while the same call refused a breaching *edge* family correctly, because `registry.py` guards that path and says why in its own docstring: *"a rule with one enforcement point is a rule with one door left open — and the thing on the other side of this one is the `ROADMAP.md` kill row."* The audit below was true of the specification's intent and false of the code, which is the worst place for an audit to be right.

**2. Does the shipped `merge_types` still refuse with an action layer on top?** **Yes, checked against `open_ontology.Registry` rather than against the probe's model.** §13 T3.5: with the `equivalent_to` edge written, a `reconcile_borough` family declared and approved, and its `reconciled_with` edge written, `merge_types("borough", "borough", namespace="dpr", into_namespace="oti_311")` returns `Refusal(reason="cross_namespace_merge")` — **and again** under `acknowledge=["cross_namespace_merge","definitions_diverge"]`. `EDGES.md` T3.12, re-run one layer up.

**3. Can a predicate be reached through an action?** **No — at three doors, and this document had one of the three when it first claimed to have them all.**

| door | what stops it | checked by |
|---|---|---|
| **declaration** | an `InputSpec` may not name `predicate` in `kinds` | §13 T3.1b |
| **invocation** | `preflight` and `record_invocation` refuse **any** `kind="predicate"` ref, whatever the family declared — `input_kind_mismatch` | §13 **R1-B1**, **R1-B1b** |
| **effect** | a `propose_type` effect must NAME a kind, from an **allowlist** of `entity` / `edge` / `value_set` | §2.5 rule 2.5-8, `K4` |
| **the merge itself** | `merge_types` refuses two predicate extents unless they are **non-empty and** byte-identical | `C10-09`, in the shipped registry |

> **Round 2 got through again, twice, and the second route was in the round-1 fix.** The effect rule tested `kind == "predicate"` and `Effect.kind` is optional, so **omitting** the key walked past it; `kind="action"` walked past it too, minting a live **verb** — the case §15.1 ranks above the noun. A blocklist was the wrong shape and it is an allowlist now.
>
> **And the door downstream was open, which is the finding that matters most in this row.** This section, and three other places, asserted that `INTERFACE.md` §5.10's refusal #2 is *"non-overridable"* — flat. **It is not.** The rule is *predicate **and extents not byte-identical***, and two freshly minted predicates have **empty** extents, which are byte-identical to each other. A reviewer minted two through an action, then merged them under two acknowledgements, **against the shipped `Registry`**. That is `ROADMAP.md`'s kill row, reproduced end to end, for the second time in this project's life. Fixed in `registry.py`, pinned by **`C10-09`**, `INTERFACE.md` §2.3 and §5.10 amended, and `ROADMAP.md`'s kill-criteria row records it — **not as a second implementation defect, which is how this document first wrote it up, but as ONE DESIGN DEFECT FOUND TWICE.** Round 3's founder lens made that a condition of sign-off and is right: refusal #2's guard is a **two-valued comparison over a three-valued fact**, row 3c broke it on *unknowable* and this row broke it on *empty*, and they are the two ends of one expression. **This document states the category correctly in §2.5 and did not notice it had just described the first trip.** The project applies the three-valued rule everywhere else that matters — `TierOrder.below` is `bool | None` (§5.2), `PreconditionResult.holds` is three-valued (§6.1), `ConsumerReport.complete` is permanently `false` — and the one guard it was not applied to is the one the kill row runs through. **The design is not what tripped**: `namespace` is untouched across both trips and `cross_namespace_merge` still refuses under acknowledgement on live NYC data (§13 T3.5b). **The debt is a checker, not a third patch** — `check_merge_guard.py`, enumerating every state an extent can be in, scoped into row 4c, because three defect classes in this repository were closed by a mechanical checker and this one has none.
>
> **The reviewer's own verdict on the allowlist is the sentence to keep:** *"the allowlist governs a permission; the kill row runs through the act."* §2.5 refuses to turn a record-time surplus effect into a refusal, on an argument this document still believes — so tightening a declaration can never close a run-time route, and the only thing that can is the call being made. **That is an argument for where the guard belongs, not against the declaration rule**, and both landed.

> **The first draft had the first door only, and this section audited all three as shut.** **[Observed, round 1]** a reviewer declared a family with `kinds=None`, handed `preflight` two `kind="predicate"` refs, got `verdict="allowed"`, and recorded it `applied`: **`merge_capabilities(commentable, searchable)`, constructed end to end.** A second reviewer reached the same row a different way — `Effect(op="propose_type", kind="predicate")` against the **shipped** `Registry` on a namespace whose policy auto-approves, which is **[Observed]** UC1's own configuration, minting a live `commentable` predicate at Haiku with no warning.
>
> **`EDGES.md` §2.4.1 had to learn the two-layer lesson the hard way and this document said it had inherited the lesson unchanged.** It had inherited half. That is worse than not having inherited it, because the audit was written as though the round had been paid for — and §17 is the section whose whole job is to be believed. The rule is general at all three doors now, and each is exercised rather than asserted.

**4. Did anything take its shape from Tenshen?** The eight keys, one at a time:

| key | Whose need |
|---|---|
| `inputs`, `preconditions` | **UC2 and UC3.** `edge_absent` is the one key whose *sharpest* example is UC1's opaque `mutation_failed`, and it is in the vocabulary because a negated edge query costs nothing once `edge_exists` exists — not because beacon has the failure |
| `effects` | **UC1, and it is the one place beacon's data drove a decision.** 15 FKs on `people.id` is what turned `effects` from a nice idea into the section with the longest argument. **Recorded as a Tenshen-shaped input rather than denied** — and the *rule* it produced (the six governance exclusions) came from UC3's kill-row test, not from beacon |
| `reversibility` | **UC1**, three values where beacon has a boolean plus a hand-written undo payload. Same category as `effects`: the fixture showed the gap, and the three values are `INTERFACE.md` §2.4's honesty rule applied to it |
| `approval_mode`, `min_auto_tier` | **UC2**, via `0.5-RESULTS.md`. The severity inversion is what makes tier a product parameter, and §12 is the end-to-end |
| `reachability` | **UC1.** 127 of 128, measured **[Observed]** |
| `payload_schema` | **UC2**, via `PACKAGE.md` §5.1's A–L ordering argument and **R10** |

> **Three of the eight are shaped by beacon, and that is more than any previous row, so it is stated rather than minimised.** `EDGES.md` §15 could say *"zero are shaped by beacon"*; this document cannot. The reason is structural: **beacon is the only fixture in the three that HAS actions.** CMS is a CSV and NYC is a catalogue; neither has a verb. So UC1 is the only place a real action's shape could come from, and the honest framing is not *"nothing came from Tenshen"* but **"the shapes came from the one fixture that has actions, and every RULE constraining them came from CMS or NYC"** — the six governance exclusions from UC3's kill-row test, the precondition boundary from UC2's severity case, the tier gate from 0.5.
>
> **The check that matters is the direction of the one real conflict, and it runs against UC1's interest.** UC1 would be *served* by a `host_state` effect that needs no `why` — beacon's actions mutate host state constantly and 11 of `delete_person`'s 15 FKs are undeclarable — and §2.5 requires the sentence anyway, so beacon's largest action carries two `host_state` admissions rather than a silent zero. **CMS's rule beat UC1's convenience**, per the rule of the ordering.

**5. Would deleting §10 leave the rest coherent?** Yes — §2–§9 stand without the ceiling section, and CMS and NYC need no `reachability` at all. That is the operational test of whether a design is centred on one host's constraint, and it is not: §10 is the part of this document that is *about* beacon, and it is separable.

---

## 18. Exit criteria — `ROADMAP.md` row #6, checked

| Criterion | Where |
|---|---|
| A governed action layer over the registry and the edge store, specified | §2–§9. An action family **is** a `kind="action"` `TypeEntry`; four calls, none of them in `INTERFACE.md` §5; three adapter primitives |
| `v0` and "unstable" in the header, and the assumptions line verbatim | Header, lines 3 and 5 |
| **No executor and no scheduler** | §1's first two non-goals, and §4 states the consequence rather than hiding it: the gate is advisory by construction |
| Invocations with append-only provenance | §3. `Invocation`, `InvocationProvenance` narrowing `Provenance` the *other* way from `EdgeProvenance`, `EventRecord.invocation_id`, three event values, and a correction that is a new event while a compensation is a new invocation |
| Gating — families through the proposal loop, invocations through `approval_mode` / `min_auto_tier` | §5. And §5.3 states what `min_auto_tier` does **not** decide, per **R20** |
| New `Refusal.reason` values through `INTERFACE.md` §5.12 in the same change (**R3**) | **Seven** added: `action_family_unknown`, `precondition_unmet`, `human_approval_required`, `tier_below_action_policy`, `effect_not_permitted`, `action_store_absent` — and `input_kind_mismatch`, which round 1 added in the change that closed the kill row. §5.12 enumerates **twenty-eight**; `types.REFUSAL_REASONS` carries them in the same commit. A seventh (`unknown_invocation`) is argued and **not** taken |
| New `warnings` values through `INTERFACE.md` §5.4 in the same change | **Three**: `effect_undeclared:<op>:<target>` (the brief offered it as a *refusal*; the UC1 design test moved it), `approval_unrecorded` (round 1) and `declaration_amended:<from>:<to>` (round 2). §5.4 now **twenty-five** across nine carriers |
| Capability flags in `PACKAGE.md`'s style, with `why`; adapter primitives ≤ 4 | §8 (three flags, two declarations, three more argued **not** taken) and §9 (**three** primitives, 19–21, **plus one amendment to primitive 15** — `read_events(invocation_id=)`, which §9.1 states with what **R30** says it costs) |
| Tenancy: none in the protocol (**R24**) | §8, and §11.4 names the consequence for beacon's enterprise blocker instead of claiming a fix |
| The tool-slot ceiling as a first-class design input | §10. Re-measured, not cited: 128 / 127 / 222 / 19 / 27, and `common 45 + task 48 + project 21 + person 13 = 127` reproduced arithmetically through `projection` |
| A design-test section per use case, expected outcomes stated first | §11, §12, §13. **Thirty-two predictions, committed in a separate commit ahead of the results; nine contortions recorded, none designed away**; **93 probe checks** across four probes, all passing — 54 in the first draft, 8 round-1 regressions, and a fourth probe (`actions_governance_probe.py`, 31 checks) for the machinery no fixture walks, which is where both rounds found their sharpest defects |
| Standing constraint 8 from the start | §14. **61** numbered rules across eight sections: **57** planned `C19` ids, **4** `prose-only` tags with reasons, and the tables **relocated in round 1** so the checker can actually reach all eight. `check_spec_drift.py`'s extension is the build row's, and §14 says why wiring it early would be worse than not wiring it |
| Which mechanism it is designed against, and what would change it | §15 |
| Kill-criterion check | §17. **Tripped in both rounds — four times in total — and closed each time** — the input vocabulary bound at declaration only, and `propose_type` could name a predicate. Now checked at **six** doors: three declaration call sites, the invocation-time input check, the `propose_type` effect allowlist, and the shipped `merge_types` — whose own guard round 2 found open on two empty extents and which `C10-09` now pins. The Tenshen-shape question is answered honestly rather than favourably |
| An adversarial review loop | §19 |

---

## 19. The adversarial review loop

**Protocol** (`USE-CASES.md`, standing constraint 7; the brief's stop rule): fresh reviewers each round, briefed with the three fixtures and told to **drive the design through each fixture's real data rather than read it** — 3c's lesson being that *"every finding of substance came from driving the real registry through a real scenario, none from reading."* Two reviewers per round, distinct lenses. **Stop: two consecutive clean rounds, or three rounds plus an honest convergence note.**

**The lenses were chosen from what worked.** Row 4b's most productive round swapped in a **consumer lens** and got five of its six findings from it, so round 1 here paired the standing **real-data lens** with an **"engineer who has to build this next week"** lens — the same idea, pointed at the implementer rather than at the reader.

### 19.1 Round log

| Round | Reviewers | Verdicts | BLOCKING | MAJOR | Outcome |
|---|---|---|---|---|---|
| **1** | real-data lens · build-it-next-week lens | NOT YET · NOT YET | **7** | **21** + 14 MINOR | **The kill row was constructible, twice, through two different doors.** Every finding reproduced by running code. Eleven new numbered rules, two new vocabulary values, one code change in the package, eight regression checks. §19.2 |
| **2** | fix-auditor lens · Phase 3 ingestion-consumer lens | NOT YET · NOT YET | **5** | **12** + 7 MINOR | **`ROADMAP.md`'s kill row tripped in test for the second time in this project's life — against the SHIPPED registry — and two of round 1's own fixes were where round 2's defects lived.** Three new numbered rules, a third warning value, two code changes in the package, a **fourth probe**, and `C10-09`. §19.3 |

### 19.2 Round 1 — what it found

**Seven BLOCKING, and the two that matter most are the same failure from two directions: a rule this document said it had inherited *unchanged* was inherited by half.**

**B1 — the kill row, constructed end to end.** `InputSpec.kinds` bound at declaration and at nothing else. A reviewer declared a family with `kinds=None`, handed `preflight` two `kind="predicate"` refs, got `verdict="allowed"`, and recorded it `applied`: **`merge_capabilities(commentable, searchable)`**. `EDGES.md` §2.4.1 binds at **both** layers and spent its own round 1 learning why; §2.3 claimed to inherit that rule *unchanged* and §17 audited it as shut. **Fixed** by validating every supplied input at both calls, with `input_kind_mismatch` as the twenty-eighth `Refusal.reason` (§7), and a general `predicate` exclusion that no family declaration can opt out of. `R1-B1` / `R1-B1b`.

**B6 — the same row through a third door.** `Effect(op="propose_type", kind="predicate")` was unconstrained, and a reviewer minted a **live** `commentable` predicate against the **shipped** `Registry` on a namespace whose policy auto-approves — **[Observed]** UC1's own configuration — at Haiku, with no warning. **Fixed:** rule 2.5-8.

**B3 — a fourth declaration door nobody had counted.** §17 audited *"three doors"* and named no call site. The shipped `_edge_family_refusal` is called from `propose_type`, `approve` **and `import_types`**, and says why in its own docstring; this document mentioned `import_types` nowhere. A reviewer imported an **active** action family declaring `merge_types` and breaching §2.2's cross-field rule, with no warning at all. **Fixed:** rule 2.2-4, and `import_refused:<reason>` on the path that cannot return a `Refusal`. `R1-B3`.

**B2 — the ledger fabricated an approval.** `record_invocation` filled `approved_by="auto:<policy>"` on every `applied` invocation, so an `irreversible`/`human` family recorded an `applied` invocation by `ai:reaper` with a policy approval nobody performed — the field `EDGES.md` §5.1 dropped from `EdgeProvenance` because *"a field whose only honest value is a lie should not be on the shape."* **Fixed:** `None` plus `approval_unrecorded`, the twenty-fourth warning value; §2.4's never-null rule binds only where the gate decided. `R1-B2`.

**B-code — `EventRecord` had no `invocation_id` and `read_events` no filter for one.** This document specified the field, a `read_events` filter for it and a `review` mode that reads it, in a change that **never touched `adapter.py`** — one row after `EDGES.md` set the precedent in that file's own comment. `InvocationProvenance.history` and the whole of `review` mode were unreachable. **Fixed** in the package, with `PACKAGE.md` §3.3/§3.4 amended in the same change and the async mirror regenerated.

**B-shape — `find_invocations` returned a 2-tuple**, so a backend had nowhere to say `known=None`, which §6.3 spends a paragraph requiring. Every other paging primitive already returns a `Page`. **Fixed:** `InvocationPage`.

**B-declaration — rule 2.2-1 contradicted the shipped decision for the identical case one kind along.** `edges.family_declaration_problem` records that a **missing** declaration is not a breach, because refusing the registration *"would make this row reject types `INTERFACE.md` says are legal, on data the one real host already has"*. This document refused it, and never said it was taking the opposite position. **Fixed** by adopting the shipped one, with the hole closed at the other end. `R1-B4`.

**Twenty-one MAJOR, of which four changed a mechanism rather than a sentence:**

- **`counts` was order-dependent** (§10.3). A family in two reachability groups made *"the useful half of this call is the counting"* rest on a guarantee that did not hold. No design test found it because **[Observed]** beacon's `category` is a single string. **Fixed:** `counts` (declared) and `admitted` (charged) are two fields. `R1-A3`.
- **`invocations(...).complete` was `True` on a filtered answer**, through a dead sub-expression `(not filtered or True)` — in the one query §4 asks an operator to act on. **Fixed:** every filtered answer is a floor. `R1-A4`.
- **`approval_mode="human"` was a three-prefix blocklist** and `bot:reaper`, `svc:cleanup`, `AI:bot` and `nobody` all walked through it. **Fixed:** an allowlist off the derived `created_by`. 
- **`review` mode and `compensated` were specified and executed by nothing**, and §11.5 claimed UC3 showed the second while UC3's probe contained no compensation at all — *a false claim in a walk-through*, which `USE-CASES.md` calls a silent accommodation rather than a pass. **Fixed** and both now run. `R1-A8a` / `R1-A8b`.

**And two findings about the audit rather than the design**, which are the ones worth keeping:

- **Thirty of the forty-seven numbered rules were unreachable by the checker §14 names.** `_section` reads to the next heading of any level, and five tables sat under a leaf subsection. §14 promised a mapping that could not have been wired.
- **§7 said §5.4 goes to "twenty-three values across five carriers"** while `INTERFACE.md` §5.4's own header and this document's §18 both said **nine** — a self-accounting error two screens apart, which is the failure mode `EDGES.md` §16 records three times in its own summary table. `check_spec_drift.py` holds the value list and the count word and has never held the carrier count.

### 19.3 Round 2 — what it found

**The lenses were chosen against round 1's own record.** One was pointed at *the previous round's fixes*, because this project has measured that they are the likeliest place for the next defect — four of ten BLOCKING in row 3e, two of four in row #4's round 3, and row 4b finding a defect *inside the mechanism built to prevent that very defect*. The other was pointed at **the Phase 3 ingestion loop** — the venture's actual customer — because §10 and §11 are built on beacon and nothing had asked whether the design survives the consumer it exists for.

**Both hit. The fix-auditor lens got the kill row; the ingestion lens got the argument §4 rests on.**

**The kill row, for the second time in this project's life, and this time against the shipped registry.** Round 1 closed a `propose_type` effect naming `kind="predicate"`. Round 2 omitted the key — `Effect.kind` is `str | None` and the rule tested equality — declared, preflighted `allowed` at Haiku, and let the host mint two live predicates. Then it merged them. **The merge should have been refused and was not**, because this document asserted four times that `INTERFACE.md` §5.10's refusal #2 is *"non-overridable"* flat, and the rule is *predicate **and extents not byte-identical*** — and two freshly minted predicates have **empty** extents, which are byte-identical to each other. `EDGES.md` §2.4.1 states the qualifier correctly. **This document dropped it, and dropping it is why nobody looked.**

- The declaration rule is an **allowlist** now (`entity` / `edge` / `value_set`), which also closes `kind="action"` — a live *verb* minted unattended, the case §15.1 ranks above the noun.
- The guard is fixed in `registry.py` and pinned by **`C10-09`**, which also asserts that a **non-empty** identical extent still merges, so the rule is narrowed rather than banned.
- `INTERFACE.md` §2.3 and §5.10 carry the qualifier; `ROADMAP.md`'s kill-criteria row records the second trip and the same judgment row 3c's got: **implementation defect, not design; the row stays armed.**
- **And the reviewer's answer to my own proposed fix is the sentence worth keeping:** *"the allowlist governs a permission; the kill row runs through the act."* A declaration rule can never close a run-time route, because §2.5 deliberately warns rather than refuses at record time. The guard had to move to the call being made.

**§4's whole argument failed on the venture's own fixture.** `invocations(gate_verdict="refused", outcome="applied")` is the one measurement §4 offers in place of enforcement. `gate_verdict`, `effect_undeclared` and `unreviewed` were on the façade and on **no primitive** — so on a pinned **2,399-dataset** Socrata catalogue with one override at row 1,200, the query returned **zero rows**, `complete=False`. **A floor of zero is indistinguishable from a clean deployment.** The three filters are on primitive 21 now, and it is not a coincidence that the three with no push-down were exactly the three governance reads.

**R24's tenancy consequence is worse than §11.4 said, and the number is the argument.** A catalogue ingester writes into the namespace of the row it is ingesting, and effect identity included namespace — so **2,394 of 2,399 correct invocations** carried `effect_undeclared`, and the one genuinely wrong-publisher invocation carried the identical warning. All three escapes were measured and all three fail. `namespace=None` on an edge op now **declares** an input-determined namespace, satisfied only when the observed namespace is one the invocation's own inputs carry — the correct run goes quiet and the wrong one still warns. **Q38 keeps its recommendation and gains its evidence.**

**Two of round 1's fixes were themselves defective**, which is the pattern this lens exists to find:

- The human-approval **allowlist** was still a blocklist. `created_by_of` maps an *unrecognised* prefix to `"user"` — right for provenance, wrong for a gate — so `bot:reaper`, `svc:cleanup`, `AI:bot`, `agent:claude` and `nobody` all walked through the fix for the blocklist. A human approver must now be *recognisable* as one.
- The **bare-entry** rule returned early on two keys, so an entry declaring `merge_types` as an effect and nothing else was written at all three doors — rule 2.5-5 bypassed by declaring **less**.

**And three rules bound at no door at all.** `InputSpec` and `Precondition` raised bare `ValueError`s in `__post_init__`, firing before any door was reached — in the document whose rule 2.2-4, itself a round-1 fix, says every declaration rule binds at all three.

**The gate-to-record window laundered an undeclared effect.** Rule 3-1 copies the declaration *"so amending the family does not re-describe an existing invocation's blast radius"* — and the copy was taken at **record** time from the **current** family, which does exactly what the rule forbids. My proposed fix (copy the whole policy) was refused by the reviewer with the right argument: *it widens the lie* — the ledger would file a `human`/`opus` gate approval against a family it describes as `auto` with no floor. The fix is `family_version` plus `record_invocation(judged=…)`, and `declaration_amended` as the twenty-fifth warning value.

### 19.4 What the two rounds say about the process

**Both rounds found the kill row, and neither found it by reading.** Four routes in total: predicate inputs unchecked at invocation; a `propose_type` effect naming a predicate; the same effect *omitting* the key; and the shipped merge guard on two empty extents. **Every one was constructed and run.** Not one came from a reviewer noticing a sentence.

**The most uncomfortable finding is not a defect, it is a repeat.** §17's kill-criterion audit was wrong in round 1 — claiming an inherited rule it had half of — and wrong again in round 2, in a different clause, in the same way: a qualifier dropped from a rule this document quotes another document as stating correctly. `EDGES.md` §15 records the identical failure one row earlier and **this document quoted that sentence while repeating the mistake, twice.** *A self-audit written by the author of the thing audited is worth what an adversary makes it worth*, and that is now three rows running where the kill-criterion section is where the loop earns its keep.

**The ingestion lens is the one to keep for a spec row.** It produced no finding about correctness — the other lens had that — and produced the two findings that change what the document is *for*: that §4's measurement did not survive its own storage primitive at the venture's real scale, and that §10's required field exists for the section its own customer deletes. **[Inferred]** those are not findable by an adversary reading for defects; they are findable only by an adversary trying to *use* the thing.

### 19.5 What round 1 says about the process

**Both lenses found the kill row, by different routes, and neither found it by reading.** The real-data lens constructed `merge_capabilities` and ran it; the build-it lens went through the 43 planned ids asking which it could turn into an assertion and found eleven it could not, which is a *different* kind of question and produced a different half of the list. **[Inferred]** that the second lens is the one to keep for a spec row: a specification's defects are mostly the questions it does not answer, and the only reliable way to find an unanswered question is to try to answer it.

**The single most uncomfortable finding is not a defect, it is a pattern.** §17's kill-criterion audit was **wrong**, in the section whose entire job is to be believed, and it was wrong in the specific way of claiming an inherited rule it had inherited half of. `EDGES.md` §15 records the identical failure one row earlier — *"in the first draft it was NOT structurally blocked, and this section said it was"* — and this document quoted that sentence while repeating the mistake. **A self-audit written by the author of the thing audited is worth what an adversary makes it worth**, and that is the third row in a row where the kill-criterion section is where the loop earns its keep.
