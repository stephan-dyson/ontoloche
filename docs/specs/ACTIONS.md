# ACTIONS — governed actions over the registry and the edge store

**Version:** `v0` — **unstable.** Every name, field and return shape here may change without a deprecation path. Standing constraint 4.
**Status:** Draft, 2026-08-29. Satisfies `ROADMAP.md` row **#6**. Unblocks nothing in the Tenshen rebuild — beacon's actions stay in code (beacon spec §10.7) and this document is deliberately written so that they can stay there.
**Assumptions:** *written against the 2026-08-28 assumptions; see docs/decisions/* — specifically [`decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md`](../decisions/2026-08-28-assumptions-in-lieu-of-office-answers.md).
**Rulings this document carries:** **R20** (`model_tier` on provenance; no tier gate in *storage* — the gate here is a declared product parameter, §5.2) · **R24** (no tenancy dimension in the protocol) · **R25** (paging is Phase 3's, decided for every listing together) · **R18** (exactly one cross-field attribute rule per kind, and this document takes exactly one) · **R31** (every numbered rule ships executable — standing constraint 8, §14) · **R3** (`Refusal.reason` is closed — six values added to [`INTERFACE.md`](INTERFACE.md) §5.12 by this change, and one warning value added to §5.4).
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
| `reachability` | `list[str]` | the host surfaces that expose this family. Opaque strings. **Required**, may be empty. §10 |
| `payload_schema` | `str \| None` | the name of an `AttributeSchema` governing `Invocation.inputs`. §2.7 |

**`created_by` is not in this list** and neither is `namespace`: both are `TypeEntry`'s, already required by `INTERFACE.md` §2.1. Restating either in `attributes` would be a second home for one fact — `EDGES.md` §2.4's rule, repeated here rather than the mistake.

**Why eight and not five.** [`EDGES.md`](EDGES.md) §2.4 took five and treated the restraint as evidence its §2.3 decision was right. Eight is more, and three of the eight are the reason:

- `approval_mode` and `min_auto_tier` are **policy**, and `INTERFACE.md` §2.7 puts the type-side equivalent (`min_auto_approve_tier`) on the **namespace**, not the entry. They are per-family here because **an action's blast radius does not vary by namespace, it varies by action**: `search_tasks` and `delete_person` sit in one namespace **[Observed, beacon]** and share nothing a namespace-level tier gate could express. This is a deliberate departure from §2.7's shape; §5.2 argues it and §16 carries the question.
- `reachability` exists because §10's ceiling is real arithmetic on a real product **[Observed]** rather than a hypothetical, and there is nowhere else for it to live.

**Cross-field rules: one, in the shape R18 licensed.** Ruling **R18** accepted `symmetric ⇒ inverse_label is None` as *"the single cross-field rule `approve()` knows about `kind="edge"` attributes"* — explicitly narrowly, explicitly because a rule language is not v0's problem. This document takes exactly one for `kind="action"`:

> **`reversibility="irreversible"` ⇒ `approval_mode` MUST be `"human"`.** A family declaring that it cannot be undone *and* that a model may run it unattended has written the failure mode this project exists to prevent into its own configuration. Refused at declaration: `Refusal(reason="human_approval_required")`, §7.

Two candidate second rules were considered and **not** taken, because two is where an exception list becomes a grammar:

- *`effects == []` ⇒ `reversibility` must be `reversible`.* Tempting and wrong: an action with no declared **protocol** effects may still change host state (§2.5's `host_state`), so the antecedent does not imply the consequent. The real check is at record time and it is `effect_undeclared` (§7).
- *`approval_mode="auto"` ⇒ `min_auto_tier is not None`.* Almost right, and left out deliberately: a deployment running a single model tier has nothing to compare against, and forcing it to invent a tier string is how `model_tier`'s opaque-string posture (`INTERFACE.md` §2.7) gets quietly turned into a required ordering nobody defined. It is a **warning**, not a rule — §5.2.

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

> **Not a back door for gating on predicates, either.** §2.4's `predicate_holds` precondition asks *"does this input's type satisfy predicate P?"* — a question about **one** type's membership, answered by reading `TypeEntry.predicates`, which is `INTERFACE.md` §2.3's own derivation. It never compares two extents, and comparing two extents is what refusal #2 exists to prevent.

### 2.4 `preconditions` — four kinds, each one existing call, and no query language

> **The rule this section is built on.** A precondition is a question the registry can already answer with a call it already has. There are four kinds; there is no fifth; and *"anything else"* is not a precondition in v0 — it is the action's own code, and the registry does not pretend to know it.

| kind | asks | answered by |
|---|---|---|
| `type_active` | this `TypeRef` is a registered entry with `status="active"` | `resolve_type` / `list_types` |
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
    why:        str                 # REQUIRED, non-empty. What this condition protects
```

**`why` is required and non-empty**, on exactly the reasoning `PACKAGE.md` §5.2 gives for `FieldSpec.description` and `INTERFACE.md` §2.1 for a non-empty `definition`: an undescribed condition is how an escape hatch re-forms one level down. A precondition nobody can read is a precondition nobody will ever delete when it stops being true.

**`edge_absent` is not symmetry, it is a fixture.** **[Observed]** beacon's `add_task_stakeholder` returns `Failure(message="Couldn't link stakeholder — task not yours or already linked", code="mutation_failed")` — **one opaque code covering two unrelated causes**, ownership and duplication, which the model receiving it cannot tell apart. The duplication half is exactly `edge_absent`, and that is why the negated form is in the vocabulary rather than left to the action's code.

**What is deliberately NOT expressible, and it is the most important paragraph in this section.** A condition over a **value** — *"the facility has a citation whose `Scope Severity Code` is in `{J, K, L}`"* — has no kind here and cannot be given one in v0. That is not an oversight; it is `INTERFACE.md` §10b.4's **contortion 11** and ruling **R22**, arriving at a third surface:

- `Consumer.gate` cannot express a value-level gate (contortion 11, `INTERFACE.md` §10b.4).
- An endpoint-kind gate on edges cannot either (`EDGES.md` **Q17**, ruled **R22** — *deferred to Phase 3 with contortion 11, because both would make `Consumer.gate` a query language*).
- **And now a precondition cannot** (§12, contortion **ACT4**).

Three unrelated surfaces reaching for one missing mechanism is the shape that earned `created_by: derived` its ruling (**R17**, on two fixtures). This one has three and is still **not** taken here, because R22 routed it to Phase 3 and taking it in a spec row would be a query language arriving through the side door this section exists to keep shut. §16 carries it as **Q35** with the count attached.

> **The modelling escape hatch is closed too, and it is closed by a rule CMS itself motivated.** The obvious way to make severity checkable is to make it an edge — `citation:42 --has_severity--> value_set:scope_severity_code` — and `EDGES.md` §2.4.1 **refuses that at two layers**, at declaration and at write, because an instance-level family takes only `entity` endpoints. So the value test has no edge to stand on either, and §12 shows the refusal firing on the fixture that motivated the rule. **This document did not have to invent a boundary; it inherited one and found that it holds.**

| # | rule | exercised by |
|---|---|---|
| 2.4-1 | The precondition vocabulary is closed at four kinds; a family declaring a fifth is refused at declaration | `C19-01` |
| 2.4-2 | Each kind is answered by a call that already exists — `resolve_type` / `predicates` / `neighbors` — and this document adds no call to `INTERFACE.md` §5 | `C19-02` |
| 2.4-3 | `Precondition.why` is required and non-empty | `C19-03` |
| 2.4-4 | A precondition that does not hold returns `Refusal(reason="precondition_unmet")` naming the failing condition's `subject` and `kind` in `detail`, never a bare `False` | `C19-04` |
| 2.4-5 | A precondition whose answer is **unknown** — the backend cannot answer it, e.g. `stores_edges=False` under an `edge_exists` — is `None` plus a `why`, and `preflight` refuses rather than treating unknown as satisfied | `C19-05` |
| 2.4-6 | A value-level condition is not expressible in v0 | `prose-only:` the mechanism has no slot for it, and ruling **R22** routed exactly this question to Phase 3 with contortion 11. Recorded as contortion **ACT4** rather than designed away |

### 2.5 `effects` — a closed operation vocabulary, and the six calls it excludes

An `Effect` names an operation the family is **permitted** to perform, so an invocation's blast radius is knowable *before* it runs rather than reconstructible afterwards.

```
Effect:
    op:         "add_edge" | "retract_edge" | "propose_type" | "host_state"
    family:     str | None      # for add_edge / retract_edge: the edge family
    namespace:  str | None      # for propose_type
    kind:       str | None      # for propose_type
    why:        str             # REQUIRED for op="host_state", non-empty. Rule U
```

**Four operations, and the fourth is an admission rather than a capability.** `host_state` means *this action changes something this protocol does not model*, and it carries a mandatory sentence saying what. It exists because the alternative is worse: a family that mutates the host's database and declares `effects: []` is claiming a blast radius of zero, and **an empty list standing in for "we did not look" is what Rule U forbids by name**. `host_state` turns a silent zero into a stated unknown, which is the only honest thing available to a registry that does not own the host's schema.

**The six calls that may NOT be an effect, as a general rule rather than a family's opt-in:**

`approve` · `reject` · `retire` · `reinstate` · `merge_types` · `register_consumer`

> **Those six are the governance loop itself.** An action that can `approve` closes the proposal→approval loop with no human in it — mechanism **1** restored through the very layer this document adds. An action that can `merge_types` is `ROADMAP.md`'s kill row wearing a verb. An action that can `register_consumer` can make itself look gated. **An action may PROPOSE; only a human, or an auto-policy a deployment set deliberately, may APPROVE.** That sentence is the line, and `propose_type` is in the vocabulary precisely so the line has a legal side: an ingestion action meeting a new word may say so, and what it says is a request.

A family declaring any of the six is refused **at declaration**: `Refusal(reason="effect_not_permitted")`. Not at invocation. `EDGES.md` §2.4.1 spent a whole adversarial round learning that a rule checked only at write time is a rule a family author opts out of by declaring something permissive, and the lesson transfers without modification: **the door is the declaration.**

**Declared versus observed, and why the record-time failure is a warning rather than a refusal.** The brief for this row offered `effect_undeclared` as a candidate `Refusal.reason`. Driving UC1 through the model moved it (§11):

> **[Observed]** `delete_person` in beacon deletes one row, and **fifteen foreign keys reference `people.id` — 7 `ON DELETE CASCADE`, 6 `SET NULL`, and 2 with no `ondelete` clause at all** (method: `grep -rn "people\.id" src/beacon/models/*.py`, 2026-08-29). Four of the seven cascades belong to three edge families of the kind [`EDGES.md`](EDGES.md) §9 maps (`person_links` twice — both legs — plus `task_stakeholders` and `project_stakeholders`). Its `prompt_docs` says *"Not reversible via undo."*, and its declared surface says nothing at all about the other fourteen tables.

If `record_invocation` **refused** a report because the host observed an effect the family had not declared, the registry would be destroying the only evidence that the undeclared effect happened. **Refusing to record what already occurred is the worst available answer**, and it is the failure shape of a `register_consumer` that quietly no-ops (`INTERFACE.md` §5.12). So:

- **Declaration time** — an op outside the four, or one of the six governance calls → `Refusal(reason="effect_not_permitted")`.
- **Record time** — an observed effect not in the declared set → the invocation **is recorded**, `outcome` is whatever the host reports, and the record carries `warnings: ["effect_undeclared:<op>:<target>"]`. `invocations(effect_undeclared=True)` enumerates every one, which is the move `list_types(unverified_semantics=True)` makes for a proposal nobody cited (`INTERFACE.md` §2.8).

**That is a deliberate departure from the brief's candidate list, recorded rather than quietly taken.** The brief's own instruction is *"add only what a design test forces"*; the design test forced the value into a different vocabulary, not out of existence. §7 carries both halves, and `INTERFACE.md` §5.4 gains the warning in this change per **R3**'s rule as `EDGES.md` §2.8 extended it to warnings.

| # | rule | exercised by |
|---|---|---|
| 2.5-1 | The effect vocabulary is closed at four operations; a fifth is refused at declaration with `effect_not_permitted` | `C19-06` |
| 2.5-2 | `approve`, `reject`, `retire`, `reinstate`, `merge_types` and `register_consumer` may never be an effect, as a general rule and not a family's opt-in | `C19-07` |
| 2.5-3 | `propose_type` **may** be an effect — an action may propose, and only a human or a deployment's auto-policy may approve | `C19-08` |
| 2.5-4 | `op="host_state"` requires a non-empty `why`; a family declaring it without one is refused | `C19-09` |
| 2.5-5 | The exclusion binds at **declaration** time, not only at invocation time | `C19-10` |
| 2.5-6 | An observed effect outside the declared set is a **warning** on a recorded invocation, never a refusal that discards the record | `C19-11` |
| 2.5-7 | An effect naming an edge family that is not a registered `kind="edge"` entry is refused at declaration with `edge_family_unknown` — `EDGES.md` §4.3's existing value, not a new one | `C19-12` |

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
