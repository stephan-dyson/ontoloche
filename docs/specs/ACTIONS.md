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

---

## 3. Invocations

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
    compensated_by:     str | None            # the invocation_id that compensated this one
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

> **`approved_by` is never null on an `applied` invocation.** If no human approved it, the value is `"auto:<policy-name>"`. A record that leaves the field blank invites a reader to assume a human signed off — the rubber-stamping failure `WALKTHROUGH.md` names, arriving through the data model.

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
2. **Every override is enumerable.** `invocations(gate_verdict="refused", outcome="applied")` returns every case where a host ran something the gate refused. That is the same move `INTERFACE.md` §2.8 makes with `list_types(unverified_semantics=True)`: **the registry cannot stop the thing; it can make the thing countable, and a count is what turns a policy discussion into a measurement.**

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
| `human` | **refuses** unless `approved_by` names a human actor — one whose id is not prefixed `ai:`, `auto:` or `derived:` | that human's actor id |

**`min_auto_tier` is a product parameter, and the registry compares two opaque strings it did not order.** `INTERFACE.md` §2.7 is explicit — *"v0 does not define the tier vocabulary or the ordering… requires the policy comparison to be supplied by the deployment"* — and this document inherits that posture without softening it. **The registry does not know that `haiku` is below `sonnet`.** A deployment supplies the order; without one, `min_auto_tier` cannot be evaluated and `preflight` reports `tier_floor_why` saying so rather than guessing. **[Assumed], inherited from §2.7:** that a total order over tiers exists per deployment. Untested, and possibly wrong for mixed vendors.

**`min_auto_tier=None` under `approval_mode="auto"` means there is no floor, and it is a legitimate configuration** — a single-tier deployment has nothing to compare. It is **not** a warning value, deliberately: minting one would put a vocabulary entry on a correct configuration. What the caller gets instead is Rule U on the report: `Preflight.tier_floor=None` with `tier_floor_why="the family declares no floor; every tier auto-approves"`. **The honest surface is a stated absence, not an alarm.**

**Below the floor, `preflight` returns `Refusal(reason="tier_below_action_policy")`** — a new value, and §7 argues why `tier_below_auto_approve_policy` is not reused.

### 5.3 What `min_auto_tier` does NOT decide — ruling R20, restated because it is easy to over-read

**R20 ruled: `model_tier` on provenance — YES. A tier gate on AI-written edges — NO in v0**, because *"gating a weekly batch job is a product decision about beacon's behaviour, not a storage shape"*, relayed to the beacon program as an observation rather than a requirement.

**Nothing here reverses that, and the difference is worth being exact about.** R20 declined to put a gate *in the storage layer*, where it would have applied to every host whether or not the host wanted one. `min_auto_tier` is not in the storage layer: it is a **field a deployment declares on a family it approved**, evaluated against an order the same deployment supplied. The registry ships no default floor, no tier vocabulary and no ordering.

So, concretely, for the one host that exists:

- **[Observed, beacon spec §2.5]** `infer_person_relationships` classifies person pairs with **Haiku** and auto-applies at **≥ 0.7 confidence**. That threshold is **beacon's**, it stays beacon's, and this document does not move it. If beacon registered that job as an action family it would choose its own `min_auto_tier`, and if it chose `None` the registry would record every invocation at `haiku` and refuse nothing.
- What the registry adds is that the choice is **written down, approved and enumerable** instead of living in a service module. `invocations(family="infer_person_relationships")` answers *"how many edges did the cheap tier write unattended last month?"* — the query `0.5-RESULTS.md` makes necessary and which nothing in beacon can answer today.

**The 0.5 finding is what makes the parameter a product parameter rather than a knob.** **[Observed]** four agents, four tiers, one CMS slice: the cheapest tier **inverted the scope-and-severity scale** — reported that higher letters are less serious when J/K/L are Immediate Jeopardy — while every number it produced stayed correct and nothing errored. An action whose precondition depends on that scale, invoked by that tier, unattended, is that failure with a write attached. §12 is that scenario, end to end.

| # | rule | exercised by |
|---|---|---|
| 5.2-1 | `approval_mode` is closed at three values; a family declaring a fourth is refused at declaration | `C19-13` |
| 5.2-2 | `approval_mode="human"` refuses a `preflight` whose `approved_by` is absent or names a non-human actor (`ai:` / `auto:` / `derived:` prefixed) with `human_approval_required` | `C19-14` |
| 5.2-3 | An actor tier below `min_auto_tier` returns `tier_below_action_policy`, with the family's floor and the actor's tier in `detail` | `C19-15` |
| 5.2-4 | `min_auto_tier=None` under `approval_mode="auto"` is a legal configuration reported as `tier_floor=None` plus a `why`, never a warning and never a refusal | `C19-16` |
| 5.2-5 | The registry never orders tiers itself; with no deployment-supplied order the floor cannot be evaluated and the report says so rather than guessing | `C19-17` |
| 5.2-6 | `model_tier` on `InvocationProvenance` is the tier of the **invoking** actor, distinct from the family's own `provenance.model_tier` | `C19-18` |

---

## 6. The calls — four, and none of them in `INTERFACE.md` §5

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
    evaluated_by:  str            # "resolve_type" | "predicates" | "neighbors"
```

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
) -> InvocationReport: ...
```

```
InvocationReport:
    invocations:     tuple[Invocation, ...]
    known:           int | None      # None = the backend cannot count. Rule U beats Rule K
    complete:        bool            # False whenever a filter suppressed rows or the
                                     #   limit truncated the answer
    why_incomplete:  str | None
    warnings:        list[str]
```

**`known: int | None` and not `int`**, because `INTERFACE.md` §3's amendment settled that a backend entitled to say *"we did not count"* must have somewhere to say it, and `0` would falsify it. This is the fifth carrier of Rule K and it takes the `TypeListing` shape rather than the `ConsumerReport` one, because the rows are not a list this document has already materialised.

**It does not page, and that is ruling R25 rather than an omission.** R25 routed paging for `list_types` and `neighbors` to Phase 3 *together*, on the reasoning that Rule K's unanswered question — what `known` means on a page — is identical for every listing. A third listing that paged in isolation would answer it unilaterally. `limit` bounds the answer and `complete=False` says the bound was hit.

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

**Ruling R3's rule:** a value is added by amending §5.12 **in the change that introduces it**. This document adds **six**, taking the closed vocabulary from twenty-one to **twenty-seven**. As with `EDGES.md` v0's four, **no v0 code path returns any of them** — row #6 is a spec and ships no action store — and they are enumerated in `INTERFACE.md` §5.12 and in `types.REFUSAL_REASONS` anyway, because a reason specified in a spec and absent from the tuple is the same drift the checker exists to catch, pointing the other way.

| value | returned by | why none of the twenty-one said it |
|---|---|---|
| **`action_family_unknown`** | `preflight`, `record_invocation`, `projection` naming a family that is not a registered `kind="action"` entry | The exact shape of `edge_family_unknown`, one kind along, and it is a **separate value for the same reason `unknown_edge` is separate from `edge_family_unknown`**: reusing the edge value would make one word mean two things (`INTERFACE.md` §2.3's Cause B), and the alternative — an empty `Preflight` for a typo'd family — is mechanism **C** committed by the gate |
| **`precondition_unmet`** | `preflight` when a declared condition does not hold, **or cannot be evaluated** | Nothing in the vocabulary is about a *runtime state of the world*. The fourteen policy refusals are about the vocabulary; `precondition_unmet` is the first about the data. `detail` carries the failing condition's `kind`, `subject` and whether it was **false** or **unknown** — one value, two states, and the states are in `detail` rather than in two words, per `endpoint_kind_mismatch`'s precedent |
| **`human_approval_required`** | **declaration**: an `irreversible` family declaring `approval_mode != "human"`. **`preflight`**: a `human`-mode family invoked with no human approver | The brief for this row named it `irreversible_requires_human`. **It is widened deliberately.** The declaration case and the invocation case are the same failure — *this needs a person and does not have one* — and `EDGES.md` §5.12 records the economy explicitly: *"a closed vocabulary that grows a value per variant of one failure is not closed for long."* `detail` names which door. Not `tier_below_auto_approve_policy`: that is about a *type proposal*'s tier, not about an invocation's approver |
| **`tier_below_action_policy`** | `preflight` when the actor's tier is below the family's `min_auto_tier` | **`tier_below_auto_approve_policy` is NOT reused**, and the temptation to reuse it is exactly `INTERFACE.md` §2.3's Cause B. That value is about **approving a proposed type**; this one is about **invoking an approved action**. Two policies, two objects, two lifecycles: a deployment may auto-approve Haiku's *proposals* and refuse Haiku's *invocations*, and one word could not express that |
| **`effect_not_permitted`** | **declaration** of a family whose `effects` name an operation outside §2.5's four, or one of the six governance calls | The brief named `effect_undeclared` as a refusal; the design tests moved it to a **warning** at record time (§2.5) and left this door with no value at all. Nothing said *"you may not declare that"* — `attributes_schema_violation` is about a schema's field types, and this is a rule about the vocabulary of one field's values |
| **`action_store_absent`** | any invocation call against an adapter declaring `stores_invocations=False` | A capability refusal, the **fifth** of that shape after `proposals_not_stored`, `cannot_record_override`, `consumer_source_read_only` and `edge_store_absent` — and it exists for the reason the first of those does: an empty `InvocationReport` would read as *"nothing has ever run"*, which is Rule U's forbidden empty in the one call a caller would believe |

**A seventh was considered and NOT taken: `unknown_invocation`.** `EDGES.md` needed `unknown_edge` because `retract_edge` names an existing edge by id. **No call in this document names an existing invocation by id** — `compensates` names one, and a `compensates` pointing at nothing is recorded with a warning rather than refused, because refusing would discard the compensation record itself (§2.5's argument again) — and `invocations(...)` is a *filter*, where an empty result is the honest answer rather than a silent drop. **Stated so that the absence is a decision rather than an oversight.**

**One warning value, added to `INTERFACE.md` §5.4 in this change** — the same rule, extended to warnings by `EDGES.md` §2.8:

| value | carrier | from |
|---|---|---|
| `effect_undeclared:<op>:<target>` | **`Invocation`** | §2.5 — the host reported an effect the family did not declare. One per surplus effect. The record is **kept**; refusing it would destroy the only evidence the undeclared effect happened |

§5.4 goes to **twenty-three** values across five carriers.

---

## 8. Capability flags for an action store

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
    after: tuple[datetime, str] | None = None,   # keyset: (created_at, invocation_id)
    limit: int = 100,
) -> tuple[tuple[InvocationRecord, ...], bool]: ...   # (page, truncated)
```

**Keyset-paged on `(created_at, invocation_id)`, the same key row 4b used for edges** — and for the same reason: an offset page over an append-only table shifts under a concurrent write, and an invocation ledger is append-only by construction. The registry does not expose the cursor (R25); the primitive has one so the façade can bound its own reads honestly.

**`compensates` is on the primitive and `compensated_by` is on the surface**, which is one fact stored one way and read the other. The store holds the forward pointer because the compensating invocation is written *after* the one it compensates and a store never rewrites a row (`INTERFACE.md` §5.8); the façade derives the backward pointer. **Stated because the asymmetry is real and a reader who saw only the surface would look for a field the store does not have.**

**`Evidence` and `history` are not on the record.** Evidence goes through `append_event`'s existing path with `invocation_id` set (§3.5), which is where `Provenance.history` already lives (`PACKAGE.md` §3.4 primitive 15). Putting them on `InvocationRecord` would give one concept two homes and would make a backend that stores invocations but not events undescribable.

---

## 10. The tool-slot ceiling is a first-class design input

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
    counts:           dict[str, int]        # families per reachability group. RULE-INDEPENDENT
    rule:             str                   # "greedy_whole_group" -- 10.4
    order_source:     "caller" | None       # None = no order supplied. Rule U
    fits:             tuple[str, ...]       # groups admitted, in order
    would_evict:      tuple[str, ...]       # groups that do not fit, in order
    over_by:          int                   # 0 when everything fits
    consumers_at_risk: tuple[str, ...]      # consumer ids gating on an evicted family
    known:            int | None            # families counted. None = backend cannot count
    complete:         bool                  # Rule K
    why_incomplete:   str | None
```

**Selection:** every registered, `active`, `kind="action"` family whose `reachability` intersects `order`. `surface` is a label recorded on the report, not a filter — a family does not know which *page* a host assembles, and asking it to would put the host's routing table in the registry.

**With `order=None` the call answers `counts` and nothing else.** `fits` and `would_evict` are empty, `order_source` is `None`, `complete` is `False`, and `why_incomplete` reads *"no order supplied; the registry does not choose which families reach a surface"*. **That is §10.2's rule made structural rather than promised.** The one question this document most obviously *could* have answered — *which 128?* — is the one it is built to be unable to answer.

**Refuses with `action_family_unknown`** when `order` names a group no registered family carries **and** `order` names nothing else either — a projection over an entirely unknown vocabulary is a typo, and an empty report for a typo is mechanism C committed by the call that exists to surface it. When `order` names a mix of known and unknown groups, the unknown ones appear in `counts` with `0` and `complete` goes `False` with a `why`, because a host legitimately assembles a context from groups that happen to be empty today.

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

| # | rule | exercised by |
|---|---|---|
| 10-1 | `reachability` values are opaque strings in the host's vocabulary; the registry never interprets one | `C19-19` |
| 10-2 | The registry never chooses which families reach a surface — with `order=None` the report carries `counts` only, `order_source=None`, `complete=False` and a `why` | `C19-20` |
| 10-3 | `counts` is rule-independent and `fits`/`would_evict` are computed under the named `rule`; a caller may use one without the other | `C19-21` |
| 10-4 | `rule="greedy_whole_group"` admits groups whole, in the caller's order, until `budget − reserved` is exhausted | `C19-22` |
| 10-5 | `consumers_at_risk` inherits `ConsumerReport.complete == False` and can never be a complete casualty list | `C19-23` |
| 10-6 | A projection whose `order` names only groups no family carries is refused with `action_family_unknown`, not answered with an empty report | `C19-24` |
| 10-7 | The 128 ceiling is a provider's and the registry neither enforces nor assumes it — `budget` is a caller's argument with no default | `C19-25` |

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
| T1.3 | refused at declaration | `Refusal(reason="human_approval_required", detail={"door": "declaration", "reversibility": "irreversible", "approval_mode": "auto"})` | **PASS** |
| T1.4 | 3 declarable, the rest admitted | 15 FKs on `people.id` — **7 CASCADE / 6 SET NULL / 2 unspecified**, reproduced by the probe. **3 `retract_edge`** effects (`person_links`, `task_stakeholders`, `project_stakeholders`) + **2 `host_state`**, both carrying a `why` | **PASS — every number as pre-registered** |
| T1.5 | a second, unguessable effect | `person_service.delete_person` calls `connection_service.unlink`, and **that call commits** before the delete. Declared as the second `host_state` | **PASS — and it is the finding of this fixture** |
| T1.6 | `effects: ()` honestly | `search_tasks`: `reads_only=True`, `covers_routes=[]`, `effects=()`, `reversibility="reversible"`, `tier_floor=None` with a `why` | **PASS** |
| T1.7 | the arithmetic reproduces | cap **128**; `budget = MAX_TOOLS_PER_REQUEST - 1` appears **twice** in the source; **222** modules; **27** `reads_only`; **19** categories, all used, summing to 222; `counts` = common **45**, task **48**, project **21**, person **13** = **127**, `fits` all four, `over_by=0`. Then a 49th `task` family → `would_evict=("person",)`, `over_by=1` | **PASS — beacon's own comment, reproduced arithmetically** |
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
> **What it did not exercise:** a `review`-mode family (beacon has no such state) and `compensated` as an outcome — beacon's undo path exists but nothing records the compensation as an invocation, so the outcome is *specified here and shown by UC3*.

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

**Method.** [`docs/tools/actions_cms_probe.py`](../tools/actions_cms_probe.py) reads the checked-in 400-row sample, builds the `cites` edges through `edges_probe_kit`, declares the family through `actions_probe_kit`, and compares every count against the frozen ground truth. `py docs/tools/actions_cms_probe.py` → `ALL 18 CHECKS PASSED`.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T2.1 | expresses | one `InstanceRef` input, `reversible`, `approval_mode="auto"`, `min_auto_tier="sonnet"` | **PASS** |
| T2.2 | **NOT expressible** | `Precondition(kind="value_in_set", …)` raises *"is not one of ('type_active', 'predicate_holds', 'edge_exists', 'edge_absent') — the vocabulary is closed at four"* | **PASS — the pre-registered failure, and the central finding** |
| T2.3 | refused at two layers | the permissive family `has_severity` with `dst=("entity","value_set")` **raises at declaration**; the correctly declared family refuses the write with `Refusal(reason="endpoint_kind_mismatch", detail={... "problem": "level" ...})` | **PASS — both layers, on the fixture that motivated the rule** |
| T2.4 | vocabulary, not data | the one expressible precondition is `type_active("cms:value_set:scope_severity_code")` — *is the scale still in the vocabulary*, not *what does this facility score* | **PASS, and it is a weak substitute, which is the point** |
| T2.5 | refused | `Refusal(reason="tier_below_action_policy", detail={"tier": "haiku", "min_auto_tier": "sonnet"})` | **PASS** |
| T2.6 | allowed | `verdict="allowed"`, `approved_by="auto:action_policy"` | **PASS** |
| T2.7 | refused as **unknown** | `Refusal(reason="tier_below_action_policy", detail={"state": "unknown", "why": "no deployment tier order supplied; the registry does not order tiers (INTERFACE 2.7)"})` | **PASS — the pre-registered choice, and `state` distinguishes it from a false** |
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

**Method.** [`docs/tools/actions_nyc_probe.py`](../tools/actions_nyc_probe.py), using **two engines on purpose**, as `edges_nyc_probe.py` does: the **shipped** `open_ontology.Registry` on SQLite for everything about types — so T3.5's claim about `merge_types` is a claim about the real implementation — and the throwaway kits for edges and actions. Dataset ids, agencies and `data_updated_at` values are the ones row #4 pinned live; a design test whose numbers move between runs is not a design test. `py docs/tools/actions_nyc_probe.py` → `ALL 14 CHECKS PASSED`.

| # | Expected | **Observed** | Verdict |
|---|---|---|---|
| T3.1 | two `value_set` `TypeRef` inputs are legal | both declare; `InputSpec(kinds=("predicate",))` raises *"`predicate` may not be an input kind — EDGES 2.4.1's rule inherited"* | **PASS, both halves** |
| T3.2 | `neighbors` and nothing else | `PreconditionResult.evaluated_by == "neighbors"`; the adjacent pair is `allowed` | **PASS — §2.4's no-query-language claim, mechanical** |
| T3.3 | **refused for the two-hop pair** | `Refusal(reason="precondition_unmet", detail={"state": "false", "kind": "edge_exists", "subject": "a"})` for `dpr ↔ dot` — **while `neighbors(dpr, ["equivalent_to"], depth=2)` reaches `dot:value_set:borough` perfectly well** | **PASS — the sharpest result in the document** |
| T3.4 | refused at declaration | `Refusal(reason="effect_not_permitted", detail={"door": "declaration", "op": "merge_types", "why": "the governance loop is not an effect"})` | **PASS** |
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

### 13.5 The five contortions, recorded and **not** designed away

| # | Contortion | Where | Why it was not designed away |
|---|---|---|---|
| **ACT1** | **One `AttributeSchema` mechanism governs two different objects** — the per-kind schema validates the *family's* eight keys, the name-level schema validates an *invocation's* inputs — and `PACKAGE.md` §5.2's key has no field saying which | §2.7 | It works because the two objects never share a store, which is a fact **outside** the mechanism. Adding a discriminator to `AttributeSchema` is a change to `PACKAGE.md` for one caller's convenience |
| **ACT2** | **`ResolveContext` is column-shaped, so resolving a verb runs on less signal than the mechanism was built for.** `sample_values` has no filler for an action, and `sibling_columns` — *"carries most of the signal"* — is empty | §5.1 | An action-shaped `ResolveContext` would be a second context object for one call. Recorded so that a weaker `resolve_type` on `kind="action"` is a known limit rather than a surprise |
| **ACT3** | **`add_task_stakeholder`'s two causes split unevenly**: *"already linked"* becomes a typed `edge_absent`; *"task not yours"* has no precondition kind and stays inside the action | §11.3 T1.2 | Authorization is §1's non-goal and **R24**'s ruling. Making it a precondition would put a permissions model in the registry through the side door |
| **ACT4** | **A value-level precondition is not expressible**, and this is the **third** surface to reach for the same missing mechanism | §2.4, §12.3 T2.2 | Ruling **R22** routed it to Phase 3 with contortion 11. Taking it here would be a query language arriving in a design test. **Q35** carries it with the count |
| **ACT5** | **A mid-action commit is invisible to `reversibility`.** `delete_person` commits an `unlink` before its own delete; one `not_durable_until_host_commits` warning would be false for the first half and true for the second | §11.3 T1.5 | Per-effect durability is a field on `Effect` and a mechanism with one fixture behind it. **[Observed]** once, in one host; one observation is not a design input |
