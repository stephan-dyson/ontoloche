# 6C-RUN — roadmap row 6c: ACTIONS v0.1 amendments, and a design test that decided a guard

**Row:** 6c. **Date:** 2026-09-01. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/ontoloche), `main`.
**What it carries:** the five rulings row 6b's questions produced — **R70** (rule 10-9's typo judgement narrowed to the namespace-scoped pool), **R71** (a retired blast-radius family warns at invocation, at both doors), **R72** (`parse_ref`, the public inverse of `ref_key`), **R73** (`review_invocation` specified as `ACTIONS.md` §6.5, and `unknown_invocation` minted as the thirty-first `Refusal.reason`), and **R75** (`retire(successor=)`'s alias half, decided by a design test rather than by a patch). Rulings file: [`2026-09-01-6b-rulings-R67-R76.md`](../decisions/2026-09-01-6b-rulings-R67-R76.md).
**The row's one sentence:** *two of the five changes were decided by running a design test before anything was patched, and both times the test said something the reading had not.*

---

## 1. The headline, in numbers

| | before (row 6b) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/PACKAGE.md) §6.2) | 327 | **346** — 338 through the five rulings, then 8 more from round 1's two lenses |
| sync suite, one run, three legs | `757 passed` | **PENDING** |
| async suite, one run, three legs | `796 passed` | **PENDING** |
| `Refusal.reason` values | 30 | **31** — `unknown_invocation`, the value §7 argued for and declined on a premise this row's fifth call expired |
| `warnings` values / carriers | 32 values, ten carriers | **34 values, eleven carriers** — R71 gives `edge_family_retired` two more carriers (`Preflight`, `Invocation`) rather than minting a variant of it; `retire_no_op` is minted by the twelfth trip's fix |
| `ACTIONS.md` calls | 4 printed (5 shipped) | **5 printed, 5 shipped** — §6.5, and the heading corrected in the same change |
| `check_spec_drift.py` ACTIONS gates | 12 shapes / 4 calls / 10 vocabularies | **12 shapes / 5 calls / 2 module functions / 10 vocabularies** |
| `check_merge_guard.py` axes | 7 | **9** — the alias re-point (R75) and **the same call, twice** (the twelfth trip), each over its shapes on every leg plus two paging doubles, **both proved by mutation** |
| `ROADMAP.md` kill-row trips | 11 | **12** — and it is this row's own regression, proved by BISECT rather than by reading a diff |

---

## 2. The two design tests, and what each one said before anything was patched

Standing constraint 7's rule is that a design test is run against real data before the patch, and its verdict is recorded whether or not it agrees with the expectation. Both of this row's ran that way.

### 2.1 R70 — rule 10-9 over UC3's many-publishers catalogue

**Expected outcomes, stated before the walk-through** (`docs/tools/actions_nyc_probe.py`, R70.1–R70.5, driven through **both** engines — the throwaway kit and the shipped `Registry`):

| | expectation |
|---|---|
| R70.1 | an ingestion host alone on the store gets zeroes |
| R70.2 | …and **still** gets zeroes when a co-tenant registers a surfaced family |
| R70.3 | …while a scope that *does* use surfaces still catches a misspelling |
| R70.4 | …and an empty namespace is still a legitimate scope (round 1 of the spec row's own finding) |
| R70.5 | …and a store-wide projection over a group nobody carries is still a typo |

**[Observed, pre-change]** R70.1 passed and **R70.2 failed**: four `ingest_dataset_*` families in `dpr` with `reachability=()`, alone on the store, answered `counts={'catalogue_ingest': 0}` — and answered **`Refusal(action_family_unknown)`** on the identical call the moment `close_311_request` was registered by a co-tenant in `oti_311`. Nothing about `dpr` changed between the two calls. That is **Q72** reproduced exactly, and UC3 is dozens of publishers in one catalogue, so *"somebody else's namespace"* is the ordinary condition rather than the exotic one.

**Both prior readings were wrong and each cost a round**, which is why the ruling put the change in a row that could re-run the test rather than in the row that found the symptom:

| reading | what it fixed | what it broke |
|---|---|---|
| round 1 of the spec row: the `namespace`-filtered pool, **no** *declares-any-surface* condition | — | an empty namespace refused a real projection |
| the fix: the **store-wide** pool **plus** the condition | the empty namespace | one host's answer depends on an unrelated host's data (**Q72**) |
| **R70: the `namespace`-scoped pool plus the condition** | both | — |

The pool judged is the **active, declared** one `counts` is computed over: a scope whose only surfaced family is *retired* answers with zeroes rather than refusing, which is this register's standing direction — *never turn "we could not find it" into a refusal.*

### 2.2 R75 — does `retire(successor=)` redirect the aliases it guards?

**The question R75 posed, and the two verdicts it allowed.** The guard at the retire path has read `rec.aliases` as *"transferred"* since row 4d and the call wrote no alias — the kill row's **tenth** trip in a different dress, *one door disagreeing with itself*, in a guard **R53** barred row 6b's lineage from re-comparing without a design test.

- **(a)** if the redirect is not real without a write → the missing alias re-point is the defect;
- **(b)** if the redirect is real through `resolve_type`'s chain → the guard is refusing a phantom, and the guard is amended.

**What separated the two, and it is the finding rather than the fix: there are two ALIAS SHAPES, and each verdict is true of one of them.**

| shape | how it arises | **[Observed]** after `retire("commentable", successor="taggable")` |
|---|---|---|
| **A — the alias also has a ROW** | `merge_types` writes it: the absorbed name becomes a **retired row whose `successor` names the survivor**, *and* a word in the survivor's `aliases` | the redirect **survives**, `existing / taggable / 1.0` — but the successor's alias list is still `()`, so what carries it is the **succession chain** and the `aliases` field plays no part |
| **B — the alias has NO row of its own** | `import_types` writing `aliases: [...]` onto a row | `existing / commentable / 1.0` → **`proposal / None / 0.3568`** |
| **B2 — the alias names a RETIRED row that does not point back at the holder** | the kill row's **fourth-trip** shape, and **the case this guard actually fires on** | `existing / commentable / 1.0` → **`proposal / None / 0.5556`** |

Reproduced on **sqlite and Postgres**, for **entities and predicates**. On `sqlite_minimal` the fixture is not reachable and the row says so rather than passing (`cannot_record_override`, `predicate_merge`).

**The mechanism, in one sentence:** `_alias_map` scans **active** rows only, so the moment the holder is retired the word it answered for is held by nothing and falls back to the scorer.

> **Verdict (a).** The missing alias re-point is the defect and the guard's reading was the intended one — the supervisor's stated hypothesis, and it is worth recording that it was **confirmed by evidence rather than adopted as a premise**, because the test was constructed to be able to say (b) and shape A is exactly the case that would have.

**What shipped.** `retire(successor=)` transfers `rec.aliases` onto the successor, deduplicated, **in the same transaction as the tombstone** and **only where the identity guard passed on exactly those words** — *the write a guard permits and the write a call performs must be the same write*, which is the tenth trip's sentence from the other end. Three decisions are stated rather than left implicit:

1. **The retired row keeps its own aliases**, as `merge_types` leaves them on the absorbed row: a tombstone is a record of what a word meant, and editing it would be rewriting a provenance-bearing row (`INTERFACE.md` §5.8).
2. **The retired row's own NAME is not added.** The succession chain already answers it at 1.0 — shape A is the observation that proves it — so adding it would be a second home for one fact (`EDGES.md` §2.4's rule) and a write no guard on this call examined. Pinned as `C9-28` rather than left as a comment, because *"we deliberately did not write that"* is what a later row silently reverses.
3. **An `aliases_added` event records the transfer.** An alias write with no history is the thing this project refuses; `merge_types` records the same fact on the survivor.

---

## 3. Deviations — every place the implementation could not follow the ruling as written

*(section written at landing)*

---

## 4. The rule → id mapping (standing constraint 8)

Every change amended its spec and its ids **in the same commit**, which is what constraint 8 asks and what each commit message states.

| ruling | rule(s) amended or added | ids |
|---|---|---|
| **R70** | `ACTIONS.md` 10-9 rewritten; §10.3's prose and §10.6's note | `C19-54` (amended), **`C19-74`** |
| **R71** | `ACTIONS.md` **2.5-11**, new; §6.1's printed `Preflight` gains `warnings`; `INTERFACE.md` §5.4's carrier list | **`C19-75`**, **`C19-76`** |
| **R72** | `ACTIONS.md` §2.3 prints `ref_key` **and** `parse_ref` | **`C19-77`**, **`C19-78`** |
| **R73** | `ACTIONS.md` §6 heading four → five, **6-9 / 6-10 / 6-11** new, §6.5 new, §7's declining argument amended; `INTERFACE.md` §5.12 thirty → thirty-one | **`C19-79`**, **`C19-80`**, **`C19-81`** |
| **R75** | `INTERFACE.md` §5.9/§5.12's *"every alias the retired row carries is re-pointed"* now describes a write that exists | **`C9-26`**, **`C9-27`**, **`C9-28`** |

### 4.1 Which existing ids had to change, and this is the notice the brief requires

**One, and it is not a kill-row id.** `C19-54` keeps its rule and gains the narrowed scope, with `C19-74` holding the direction it does not hold. **No `C19` or `C9` id was renumbered, and every kill-row id passes unchanged**: `C9-08`, `C9-18` … `C9-25`, `C10-09`, `C10-11`, `C10-13` … `C10-19`, `C12-08`, `C12-09`, `C12-12` … `C12-18`, `C4-12` … `C4-14`, `C3-14` … `C3-16`. `check_merge_guard.py`'s seven existing axes exit 0 **with no edits to their fixtures**, and Part A's AST scan now prints `retire writes aliases,status,successor COLLAPSES` — the enumeration noticing a new writer of an identity field, which is what row 4c built it for.

### 4.2 The eighth axis, and why an axis rather than an id alone

`retire` became the **fourth** writer of `aliases`. This file's standing rule is that a writer of an identity field is **judged** by Part A and then **driven** by Part B. The new axis runs both alias shapes through the door on every leg **plus the `partial` and `truncated` paging doubles**, and asks two separable questions: does the re-pointed word still resolve at 1.0, and does the write happen only where the guard passed. **Proved by mutation** — disabling the write turns six rows red and the checker exits 1.

> **And the doubles found the axis's own honest limit, recorded rather than smoothed.** On a page-capped backend the word fails to resolve at 1.0 **before** the retirement as well as after, because `_alias_map` reads active rows to exhaustion and a capped page truncates that scan. That is Rule U working, not a regression — so those rows print `written; resolution NOT POSABLE` **with the reason**, and the write half is still asked. Printing `REFUSED` for a probe that never ran is this file's own recorded failure, from row 4c's first adversarial round.

---

## 5. What each amendment cost, in one paragraph each

**R70** narrowed a rule and left both prior wrong readings named in the code and in the document, because *"getting this wrong in either direction has already cost a round each"* is the ruling's own reason for taking it in a row that re-runs the test.

**R71** minted **nothing**. `edge_family_retired` already carried the identical fact one layer down, where `EDGES.md` §4.3 emits it on the read *and* on the write because *"a caller who has just written under a word somebody withdrew is entitled to know"* — and a caller about to invoke a verb whose declared blast radius lands on one is in exactly that position. What it did cost is a **field**: `Preflight` had no `warnings` carrier, and shipping the warning at `record_invocation` alone would have been *a fix applied at one call site of two*, which is the single sentence of the kill row's ninth, tenth and eleventh trips. §5.4's value count is unchanged and its **carrier** count is not, and the document says so rather than letting a number go stale.

**R72** is one additive function and a new kind of gate. `parse_ref` **raises** for anything outside §2.3's grammar: *a permissive default for a value you did not recognise* is the single shape row 6b shipped twice — `ref_shape` returning `"type"` for a bare string, and `_alias_identity_breach` comparing a row against itself, which is the ninth trip. `check_spec_drift.py` gained `ACTION_FUNCTIONS`, which holds a printed module-level signature **and** checks the name is in `actions.__all__` — *a surface the package does not export is one a consumer hand-rolls, which is Q74 itself*. Proved by mutation in both directions.

**R73** is the row's one vocabulary growth, and the conditionality is the whole argument. §7 argued `unknown_invocation` and declined it **because no call named an existing invocation by id**; §6.5's fifth call names one. §7's v0 argument is kept **verbatim** and the amendment records which premise moved, so a reader who wants to know whether this vocabulary grows carelessly can see exactly where. The build row's placeholder — `action_family_unknown` for a missing *invocation* — is replaced rather than left: one word for two objects is §2.3's Cause B.

**R75** is §2.2 above.

---

## 6. The adversarial loop

**Stop rule** (standing constraint 7): two consecutive clean rounds, or three rounds plus an honest convergence note. **Round 1 was not clean; round 2 is in flight.** This section is written as each lens returns rather than at landing, so the row is resumable from the repository rather than from a session.

| round | lenses | BLOCKING | MAJOR | MINOR | kill-row trips | ids after |
|---|---|---|---|---|---|---|
| **1** | kill row, briefed with all eleven · beacon integrator | **1** | 7 | 5 | **1 — the twelfth** | 346 |
| **2** | fix-auditor on round 1's own fixes · kill row, briefed with all twelve *(in flight)* | **1** | 4 | 2 | — *(so far)* | 346 |

### 6.1 Round 1 — the kill row's TWELFTH trip, and it is this row's own regression

Full record, countersigned: [`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md). In one sentence: **`retire` read `.status` twice and both times on the successor**, so ruling R75's alias write was cashed a second time on a repeat retirement and left **two active rows answering to one word**.

**The lens proved the provenance by BISECT rather than by reading a diff** — a shadow package built at `664d3a5^` answers the identical script with zero holders where HEAD had two — and the supervisor's countersignature makes that the standard from here. Its second new rule is the one this row paid for: **a change that adds a writer of an identity field lands WITH the checker axis that can pose its new failure mode, in the same commit.** R75's write landed at `664d3a5` and axis nine landed a round later, and that ordering is what let the trip exist.

**The integrator lens produced five findings and every one was in the READ half, or in what the code does when nobody passed the optional argument** — the fourth consecutive row that sentence has been true of this lens. The sharpest was not the permissive default R72 was written against but its inverse: a `TypeRef` whose `name` carried a `#` was stored and read back as an **`InstanceRef` naming an object that never existed**, with no exception anywhere — *a confident reading of the wrong thing*, which is the seventh trip's shape arriving in a parser.

### 6.2 Round 1 was ALSO red on `main`, and the row's own record did not say so

`check_capability_matrix.py` — `nonbinding` under **R2**, so the conformance verdict is untouched, and a red on `main` regardless — reported **five configurations that cannot pass the suite** where 6b's landing had eighteen conformant. It was caught by the supervisor reading the log rather than by the worker, whose background command reported the **wrapper's** exit code and not pytest's. *A verdict read off the wrong process is a verdict nobody took.*

**Bisected, not inferred.** At `ddf2f5e` (6b's landing, this row's parent) all eighteen configurations are conformant, exit 0: the regression is row 6c's.

**The cause is one line and it is a class rather than an instance.** `conftest`'s capability gate read `get_closest_marker("requires_capability")`, which returns exactly **one** mark — so **stacking two `@requires_capability` decorators silently discarded all but the innermost.** Three ids stacked, were skipped for the flag they named innermost, and RAN in configurations where their fixture cannot exist.

> **A declaration this harness silently ignores is the shape the register refuses everywhere else**: one word for two facts, a permission cashed twice, a guard reading an operand nobody passed. `iter_markers` honours every declaration, which makes stacking a legitimate way to say *this needs the edge store AND the attribute store* rather than a trap, and makes the composite constants composable at all. **Fixed in both conftests** — the async one is not generated by `tools/unasync.py`, so it is the call site a fix reaches last, which is this project's most-repeated defect.

**And the red named itself badly, which is its own finding.** The matrix runs each configuration with `-q --tb=no` and parses only the tally, so five failing configurations is all it can say — true, and three steps from the cause. Re-running the same configurations through the same entry point with `-ra` named the three ids in seconds. A bookkeeping test now asserts the cause directly, so the next regression of this class arrives as *the capability gate must honour every declaration* rather than as a number.

### 6.3 Round 2 — the fix-auditor, and the register's prediction held

The tenth trip's countersignature made this lens a standing requirement rather than a choice: *"every round after a fix round begins with a lens pointed at that fix."* It returned **1 BLOCKING, 4 MAJOR, 2 MINOR — and every single finding is inside round 1's fixes**, which is the fifth row running that this project's counted policy has been right about where its next defect lives.

**The BLOCKING is the ninth axis itself**, added by round 1 to close the twelfth trip. Its detector iterated `("predicate", "entity")` only — and `retire(successor=)` covers **edge** families by ruling R19 and **action** families by ACTIONS.md §2.1, both of which carry `aliases`. **[Observed, by mutation]** with the trip's guard removed, two ordinary retirements left `{'beta_edges': ('zeta',), 'gamma_edges': ('zeta',)}` — `C16-06` verbatim — and the axis built to catch exactly that returned `{}`.

> **Widening the detector was necessary and not sufficient, and the difference is the eighth dress of this file's oldest sentence.** *A checker only asks the questions its fixtures can pose* — and a **detector** that scans a kind no **fixture** ever writes still cannot fail. The axis gains `retire(edge)`, a bare `kind="edge"` fixture through the ordinary door, plus the two paging doubles axis eight already had. Proved by mutation: the `retire(edge)` row goes `FAILED` and the checker exits 1.

The remaining round-2 findings are recorded with their fixes in §6.4 as they land. **The kill-row lens of round 2 died mid-flight on a session limit after reporting only that its first probe reproduced; it has been re-issued rather than counted, because this register's own evidence is that a missed lens is a missed finding rather than a missed formality** — row 6b's round-2 kill-row lens died the same way and its re-issue found the eleventh trip on the first target it looked at.

### 6.4 What round 2 has changed so far

*(written as each fix lands; the row does not close while this section is open)*

| finding | lens | state |
|---|---|---|
| the ninth axis blind to `kind="edge"` | fix-auditor | **fixed**, detector *and* fixture, mutation-proved |
| `_retired_blast_radius` warns on an unrelated input's namespace | fix-auditor | open |
| `projection`'s scope sentence asserts a falsehood for a retired-only and a proposed-only scope | fix-auditor | open |
| the flat-form refusal binds at the invocation door while every other door accepts the namespace | fix-auditor | open |
| `C9-30`'s filter is one-sided — the retired row's own name still transfers | fix-auditor | open |
| the twelfth trip's fix prescribes a remedy `reinstate` refuses | fix-auditor | open |
| `C19-84`'s Rule-U fallback is unwarned | fix-auditor | open |
| kill row, round 2 | kill row | in flight |

---

## 7. What the build taught

*(section written at landing)*

---

## 8. Questions for the supervisor — **Q79 onward**

*(section written at landing)*
