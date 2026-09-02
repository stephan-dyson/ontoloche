# 6C-RUN — roadmap row 6c: ACTIONS v0.1 amendments, and a design test that decided a guard

**Row:** 6c. **Date:** 2026-09-01. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/ontoloche), `main`.
**What it carries:** the five rulings row 6b's questions produced — **R70** (rule 10-9's typo judgement narrowed to the namespace-scoped pool), **R71** (a retired blast-radius family warns at invocation, at both doors), **R72** (`parse_ref`, the public inverse of `ref_key`), **R73** (`review_invocation` specified as `ACTIONS.md` §6.5, and `unknown_invocation` minted as the thirty-first `Refusal.reason`), and **R75** (`retire(successor=)`'s alias half, decided by a design test rather than by a patch). Rulings file: [`2026-09-01-6b-rulings-R67-R76.md`](../decisions/2026-09-01-6b-rulings-R67-R76.md).
**The row's one sentence:** *two of the five changes were decided by running a design test before anything was patched, and both times the test said something the reading had not.*

---

## 1. The headline, in numbers

| | before (row 6b) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/PACKAGE.md) §6.2) | 327 | **366** — 338 through the five rulings, 9 from round 1's two lenses, 1 from round 2's, and **18 from round 3**, every one of which is a defect in a fix this row had already made |
| sync suite, one run, three legs | `757 passed` | **837 passed**, exit 0 — postgres + sqlite + `sqlite_minimal` in one run |
| async suite, one run, three legs | `796 passed` | **874 passed**, exit 0, same three legs |
| `Refusal.reason` values | 30 | **31** — `unknown_invocation`, the value §7 argued for and declined on a premise this row's fifth call expired |
| `warnings` values / carriers | 32 values, ten carriers | **37 values, eleven carriers** — R71 gives `edge_family_retired` two more carriers (`Preflight`, `Invocation`) rather than minting a variant of it; the other four are minted by trips and by the loop: `retire_no_op` (twelfth trip), `aliases_transferred` and `aliases_removed` (round 3 item 1, the two halves R75's write left open), and `word_previously_retired` (the **fourteenth** trip) |
| `ACTIONS.md` calls | 4 printed (5 shipped) | **5 printed, 5 shipped** — §6.5, and the heading corrected in the same change |
| `check_spec_drift.py` ACTIONS gates | 12 shapes / 4 calls / 10 vocabularies | **12 shapes / 5 calls / 2 module functions / 10 vocabularies** |
| `check_merge_guard.py` axes | 7 | **10** — the alias re-point (R75), **the same call, twice** (the twelfth trip), and **a tombstone's words at the mint doors** (the fourteenth), each over its shapes on every leg plus two paging doubles, **all proved by mutation**; axis nine's five repeat fixtures now repeat into DIFFERENT targets, which two of them did not |
| `ROADMAP.md` kill-row trips | 11 | **14 — one per round.** The twelfth is this row's own regression; the thirteenth bisects in two (one variant live at 6b's landing, one introduced by R75); the **fourteenth predates row 6c entirely**, in three doors no row of this lineage had touched, found by a lens briefed to look at two other calls. All three proved by BISECT rather than by reading a diff |

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

**Six, and each one is a place the ruling could not be obeyed literally rather than a place it was not obeyed.**

**D-6c-1 — R71 minted no warning value and still cost a FIELD.** The ruling's own words are that this warning *reuses* `edge_family_retired` and mints nothing, and that half held. What it could not avoid is that **`Preflight` had no `warnings` carrier at all**: shipping the fact at `record_invocation` alone would have been *a fix applied at one call site of two*, which is the single sentence of the kill row's ninth, tenth and eleventh trips. So `INTERFACE.md` §5.4's **value** count is unchanged by R71 and its **carrier** count is not, and the document says so rather than letting a number go stale.

**D-6c-2 — no `C19` id is exercisable on `sqlite_minimal`, so one of three legs cannot judge this row's own subject.** That leg declares `stores_attributes`, `stores_invocations`, `stores_invocation_events` and `stores_events` all `False`, and an action family is a `TypeEntry` whose eight declaration keys live in `attributes` — so a family cannot be *declared* there, let alone invoked. Every `C19` row on that leg is a **stated non-exercisable**, printed by the coverage line under ruling **R12** rather than skipped in silence. It is a real limit on what three legs mean for this row and it is recorded rather than smoothed: the ACTIONS surface is proved on two reference backends, not three.

**D-6c-3 — the eighth axis's paging doubles cannot pose the half the axis was built for.** On a page-capped backend the transferred word fails to resolve at 1.0 **before** the retirement as well as after, because `_alias_map` reads active rows to exhaustion and a capped page truncates that scan. That is Rule U working rather than a regression, so those rows print `written; resolution NOT POSABLE` **with the reason**, and the write half is still asked. Printing `REFUSED` for a probe that never ran is this file's own recorded failure, from row 4c's first adversarial round.

**D-6c-4 — `C19-82`'s constraint binds at the invocation door and not where the namespace is WRITTEN.** `INTERFACE.md` §2 types `namespace` as an unconstrained `str`, and every other door in the package accepts `org:beacon`. So a deployment can register types, edge families and action families in such a namespace and **never invoke a single action**, with nothing at the declaration door warning it. Binding the constraint where the word is written is `INTERFACE.md`'s door and changes a shipped type, which this row's fence bars: raised as **Q81** and left. What round 3 could take without a ruling is the *sentence* — the refusal now says which of its two failures this is (`C19-90`).

**D-6c-5 — `C19-89`'s condition cannot be constructed in the store and is constructed as a read-side double.** The finding is about an invocation carrying no `declared_policy.approval_mode`; `put_invocation` **refuses to overwrite an existing id**, which is the ledger's own append-only rule and is correct, so a filed row cannot be edited into that shape. The test wraps the adapter in a proxy that answers `find_invocations` with the field absent — which is exactly what a backend that filed rows before the field existed looks like from the registry's side. Round 2's own lens constructed it the same way; recorded because *"simulated"* and *"observed"* are different claims.

**D-6c-6 — the row could not make one of its own fix shapes work as written, and the operand is why.** Round 2's `M2` prescribed gating `projection`'s scope sentence on `listing.complete`. `list_types` reports `complete=False` **whenever any filter was applied**, so a `kind`+`namespace` listing is never complete and that gate would have deleted `C19-86`'s sentence rather than narrowing it. The census became its own read, paged to exhaustion, carrying its own `complete`. Recorded here because *the operand a lens names does not always carry the fact it needs* is the ninth trip's shape arriving in a fix **shape**, and this row is the first to hit it.

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
| **the loop** *(rounds 1–3)* | `ACTIONS.md` **2.5-12**, **2.5-13**, **6-12**, **6-13**, **10-11**, **10-12** new or amended; `INTERFACE.md` §5.4 **34 → 36 values** and §5.9's R75 paragraph gains what the write left open | rounds 1–2: `C9-29` … `C9-31`, `C10-20`, `C19-82` … `C19-86`. **Round 3: `C9-32`, `C9-33`, `C9-34`, `C12-19`, `C19-87`, `C19-88`, `C19-89`, `C19-90`** |

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

**Stop rule** (standing constraint 7): two consecutive clean rounds, or three rounds plus an honest convergence note. **Neither round 1 nor round 2 was clean — each found a kill-row trip — so round 3 runs and is the cap.** This section is written as each lens returns rather than at landing, so the row is resumable from the repository rather than from a session, and §6.4 is deliberately written for a reader with no memory of the session that produced it.

| round | lenses | BLOCKING | MAJOR | MINOR | kill-row trips | ids after |
|---|---|---|---|---|---|---|
| **1** | kill row, briefed with all eleven · beacon integrator | **1** | 7 | 5 | **1 — the twelfth** | 346 |
| **2** | fix-auditor on round 1's own fixes · kill row, briefed with all twelve | **2** | 6 | 4 | **1 — the thirteenth** | 347 |
| **3** *(the cap)* | fix-auditor on round 2's AND item 1's fixes · kill row with all thirteen · integrator on R70/R71/R73 | **2** | 3 | 7 | **1 — the FOURTEENTH** | **366** |

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

### 6.4 Every finding of all THREE rounds, with its disposition

**This table is the row's working state, and it is written for a reader with no memory of the session that produced it.** *(Rounds 1 and 2 first, then round 3 and the item that closed every one of their `OPEN` rows.)* The probes that found these lived in a session scratchpad and are **not durable**; what is durable is the contract id beside each fixed finding, which reproduces it, and the observed evidence quoted beside each open one, which is enough to reconstruct the probe. An open row is work, not a note.

#### Round 1 — kill-row lens (briefed with eleven trips)

| # | finding | disposition |
|---|---|---|
| B1 | **the TWELFTH trip** — `retire` never read `rec.status`, so R75's alias write was cashed twice | **fixed** — `retire_no_op:already_retired`, `C9-29`; ninth checker axis |
| M2 | `list_types(predicate=<a transferred alias>)` answers a confident zero for a word three other doors call one identity | **QUESTION** — R54's door; the fence bars changing what an identity guard compares |
| M3 | the alias-transfer event was filed as `"retired"` **on the live survivor** | **fixed** — `aliases_transferred`, `C9-31` |
| M4 | `parse_ref` raised on `ref_key`'s own output for a namespace carrying `:`, and accepted `'::'`, `'a:b:'`, a non-`NAME_RE` name and an unknown `kind` | **fixed at the WRITE door** (`C19-82`); the parser stays the faithful inverse and §2.3 states the boundary. **The `rsplit` alternative was considered and declined**: it would accept a 4-segment string, making a corrupted row parse instead of raise |
| M5 | `review_invocation` ignored its `namespace`; and it does not enforce the separation of duty its own docstring argues for | namespace **fixed** (`C19-85`); **self-review is a QUESTION** — the registry does not know a deployment's duty model |
| M6 | `_alias_map`'s memo key clobbered by its own loop variable — 2 vs 41 `find_types` calls over forty closures | **fixed** — rename; D-4c-11's claim is true again |
| m1 | an ordinary `import_types` erases an R75 re-point with no warning | **fixed, round 3** — `aliases_removed` warning **and** event, `C12-19`; see round 2's `m4`, which is the same defect's other half |
| m2 | retiring an **entity** on `indexes_membership=False` is refused with a `why` about *a predicate's extent* | **fixed, round 3** — the sentence names the row's own kind; the refusal is correct and stays. `C9-34` |
| m3 | `retire(A, successor=B)` where `A.aliases` holds `B`'s own name wrote `B` into `B.aliases` | **fixed** — `C9-30` |

#### Round 1 — beacon integrator lens

| # | finding | disposition |
|---|---|---|
| B1 | **BLOCKING** — a `TypeRef` named `person#p-1` was stored and read back by `parse_ref` as an **`InstanceRef` naming an object that never existed**, no exception anywhere | **fixed** — `flat_form_problem` at both doors, `C19-82` |
| M1 | a namespace carrying `:` produced a ledger row `parse_ref` refuses — written by this layer itself | **fixed**, same change |
| M2 | `invocations(unreviewed=True)` read the family's mode **today**, so an amendment moved historical invocations into and out of the queue with no event and no warning | **fixed** — mode of record, `C19-84` |
| M3 | `review_invocation`'s `namespace` accepted and ignored — a tenant-scoped operator drained another tenant's queue | **fixed** — `C19-85` |
| M4 | `projection`'s default scope is the whole catalogue and the report could not say so — a co-tenant's 40 families were charged to a publisher that does not own them | **fixed** — `ProjectionReport.namespace`, `C19-86` |
| M5 | **R70 regression** — a typo'd `namespace` answered *everything fits* about a scope holding nothing | **fixed** — the scope sentence, `C19-86` |
| M6 | `edge_family_retired` had a constructible false negative **and** false positive on an input-determined namespace | **fixed** — `C19-83` *(and round 2 found the fix reintroduced the false positive — see below)* |
| m1 | `review_invocation` accepted an empty / non-person `reviewed_by` | empty **fixed** (`ValueError`); non-person is the self-review **QUESTION** |
| m2 | `Invocation` carried `reviewed_at` and no `reviewed_by` | **fixed** — `C19-85` |
| m3 | `retire`'s alias transfer is invisible at the call — the returned entry carries no signal | **fixed, round 3** — `aliases_transferred:<successor>`, the thirty-fifth warning value, minted with its §5.4 row per **R3** as `retire_no_op` was. `C9-33` |
| m4 | `projection` accepted a negative `budget` | **fixed** — `ValueError`, `C19-86` |
| m5 | §10's printed signature comments every parameter except `namespace` | **fixed** |

#### Round 2 — fix-auditor lens (pointed at round 1's own fixes)

**The register's counted policy held for the fifth row running: every finding is inside round 1's fixes.**

| # | finding | disposition |
|---|---|---|
| B1 | **BLOCKING** — the ninth axis's detector iterated `("predicate","entity")` only, so the twelfth trip **reproduces intact on `kind="edge"`** and the axis reported `{}` | **fixed** — detector widened to every kind **and** a `retire(edge)` fixture added, because a detector that scans a kind no fixture writes still cannot fail. Mutation-proved |
| M1 | **`C19-83`'s fix reintroduced the false positive it was written to remove.** `_input_namespaces` unions **every** namespace **any** input mentions, so an unrelated input drags one in. **[Observed]** `person_links` ACTIVE in `beacon` where the edge lands, retired in `tenant_a` mentioned only by an unrelated `cfg` input → `preflight warnings: ('edge_family_retired:person_links',)` on both legs and the async mirror | **fixed, round 3** — exactly that shape, `C19-87`. Both of `C19-83`'s true directions still fire, asserted beside it |
| M2 | **`C19-86`'s scope sentence asserts a falsehood for two of the four causes it enumerates.** `projection` probes the scope with `list_types("action", namespace=…)`, which defaults to `include_retired=False`, so an **all-retired** scope and an **all-proposed** scope are both told *"holds no `kind="action"` row of any status"*. **[Observed]** `list_types(action, tenant_a)` → `[]` while `include_retired=True` → `[('publish_doc','retired')]`, and the retired-only and typo'd-scope sentences are byte-identical. The `scope_active == 0` branch is **unreachable on all three legs** | **fixed, round 3** — `C19-88`, with **one correction to the fix shape and one to the finding.** `listing.complete` is `False` whenever ANY filter was applied, so gating on it would have deleted the sentence entirely; the census is its own read, `include_retired=True` and **paged to exhaustion**, carrying its own `complete`. And **[Observed]** the *all-proposed* cause cannot exist: no code path persists a `TypeRecord` with `status="proposed"`, so the four causes are three and `scope_active == 0` is reached by RETIRED rows |
| M3 | **`C19-82` binds at the wrong layer.** `INTERFACE.md` §2 types `namespace` as an unconstrained `str`; every other door accepts `org:beacon`, and both invocation doors now refuse it — a deployment can register types, edge families and action families there and **never invoke a single action**, with nothing at the declaration door warning it. The refusal's `why` is also wrong for this case: it says *reads back as a DIFFERENT reference* when `parse_ref` **raises** | **half fixed, half argued, round 3** — the `why` is per case (`C19-90`): a `#` segment *reads back as a DIFFERENT reference*, a `:` namespace makes `parse_ref` **RAISE**. The binding layer is **Q81** for the founder, exactly as the finding says: it is `INTERFACE.md`'s door and this row's fence bars taking it |
| M4 | **`C9-30`'s filter is one-sided.** It drops the successor's name and nothing else, so when the retired row's **own name** is in its own alias list it still transfers — the exact write `C9-28` forbids, by the other route. **[Observed]** `taggable.aliases == ('commentable',)` on both legs | **fixed, round 3** — exactly that shape, `C9-32`, with the dropped words in `aliases_not_added` |
| m1 | **The twelfth trip's fix prescribes a remedy `reinstate` refuses.** The guard comment, §5.4's new row and the trip record all say *"the path to change a successor is `reinstate` then `retire`"* — and `reinstate` refuses `successor_active` whenever the successor is live, which is the ordinary case. **[Observed]** on both legs and the async mirror | **fixed, round 3** — corrected in **four** places (the guard comment, `INTERFACE.md` §5.4's row, `C9-29`'s test docstring and the trip record). The trip record is **appended to rather than edited over**, which is §5.8's own rule applied to this register |
| m2 | **`C19-84`'s Rule-U fallback is unwarned.** On a backend keeping no `declared_policy` the original defect is fully live and `why_incomplete` says nothing about it — the comment claims *"the report says the set is a floor either way"* and `complete=False` is on for any filter | **fixed, round 3** — the clause names the count and the denominator, `C19-89`. Constructed with a read-side double, because `put_invocation` refuses to overwrite an existing id and the store cannot be edited into that shape |

**What the fix-auditor verified SOUND, so round 3 need not re-pose it:** the twelfth trip's guard position relative to `_require`/`force`/the successor guards/the transaction, over three consecutive calls and five backend shapes; two different rows converging on one successor; the full `retire → retire-successor → reinstate → retire → reinstate` cycle (ends refused `alias_collision`); `aliases_transferred` missed by no reader (`_lifecycle_collisions`, `_DECLARATION_EVENTS`, `read_events` filters, `provenance`); `C19-84`'s amendment immunity on every shipped backend; `C19-85`'s `reviewed_by` ordering under two reviews in one clock instant (8/8 on Postgres); the `_alias_map` memo now hitting; `projection`'s `ValueError` not breaking `budget=0`.

**What it could NOT test, and why:** `sqlite_minimal` for any `C19` fix (that leg declares `stores_attributes`, `stores_invocations`, `stores_invocation_events` and `stores_events` all `False`, so an action family cannot be declared there at all); `projection`'s `scope_active == 0` branch; a genuinely `declared_policy`-less reference backend (simulated with a read-side wrapper).

#### Round 2 — kill-row lens (briefed with twelve trips)

| # | finding | disposition |
|---|---|---|
| B1 | **the THIRTEENTH trip** — `merge_types` cashes a tombstone's words once per **call**, not once per **row** | **fixed** — non-overridable `alias_collision`, `C10-20`; axis nine's `_repeat_merge` now repeats into a different target, mutation-proved |
| M2 | **R75 minted a class of word Q56's cheap half cannot see.** A transferred alias has no row of its own, so `_identity_stale` short-circuits — the retired **name** warns `identity_stale` and **the word it moved does not**, in one store. **[Observed, bisected]** `resolve_type('zeta')` was `proposal / None / 0.7500` before R75 and is `existing / beta / 1.0000` after | **QUESTION** — Q56 is the founder's, and the fence bars changing what an identity guard compares. Fix shape if ruled: resolve the left-hand side through a keyed, paged scan over rows of **every** status (`_word_rows`'s treatment, which trip 8 already built for the name door) |
| m3 | `list_types(predicate=<a transferred alias>)` answers a confident zero | **QUESTION** — same door as round 1's M2, same fence |
| m4 | an ordinary `import_types` erases an R75 transfer and leaves its `aliases_transferred` event standing, asserting a fact the store no longer holds | **fixed, round 3** — `aliases_removed` warning **and** event, `C12-19`. §5.8's *a correction is a new event*, applied to the removal half, exactly as the row asked |

**What it explicitly did NOT probe, and said must not be read as cleared:** **R70 `projection`** (read only — the greedy-prefix arithmetic and the per-predicate `_consumer_report` recomputation in the `consumers_at_risk` loop are unexamined by execution), **R71 `_retired_blast_radius`**, and **R73 `review_invocation`'s namespace scoping**. Also not run: the full three-leg suite and Postgres, under the machine's resource gate.

#### Round 3 — kill-row lens (briefed with all THIRTEEN trips, aimed at `import_types` and `reinstate` under standing rule (c))

| # | finding | disposition |
|---|---|---|
| B1 | **the FOURTEENTH trip** — a word a TOMBSTONE still answers to as an **alias** is free at **all three doors that MINT a name**: `propose_type`, `approve` and `import_types`. **[Observed, five ordinary calls]** minted with empty warnings, after which the store refuses **both** `merge_types` and `reinstate` non-overridably — the tombstone permanently un-reinstatable, which is ruling **R11**'s own governance act | **fixed** — `word_previously_retired:<holder>`, `C4-15`, `C5-13`, `C12-21`; **tenth** checker axis, mutation-proved. Provenance by BISECT: **predates row 6c entirely**; R75 widened the blast radius rather than introducing it |

**What it probed and found SOUND, so round 4 need not re-pose it:** `reinstate`'s per-row question, asked unconditionally through `_alias_clash(rec.name, rec.kind, dormant)` and refusing `alias_collision` non-overridably at **every** cash-point it could construct — the `retire → retire-successor → reinstate → retire → reinstate` cycle, two tombstones on one word, merge-produced tombstones, both directions of the variant-B chain: **no `reinstate` trip**. `C16-06`'s two-active-holders invariant under a **fuzz**: exhaustive depth-3 over 27 operations (**19,683 sequences**) plus **6,000** random depth-6 sequences over 66 operations — `retire`, `retire(successor=)`, `reinstate`, `merge_types`, four `import_types` shapes, `propose_type`+`approve`, consumer registration, vocabulary growth and variant spellings — **no breach**, and mutation-proved by disabling `merge_types`' `_alias_clash` to reproduce trips 12/13. The empty-identity-key axis (`状态` written byte-identically onto two live predicates: `resolve_type` answers `none / None / 0.0`, **no 1.0 collapse**, Q68's shipped default holds). `identity_stale` reaching the import alias door. And `C12-20` already closed in the worktree it read.

**One suspicion it could NOT construct, reported as such rather than as a finding:** `merge_types`' new `C10-20` guard escapes on `not same_word(holder, left.name)`, and `_alias_clash` returns only the **first** active holder in page order — so a genuine third live holder that sorts *after* a row whose name is a spelling of `left.name` would be swallowed. **[Inferred]** — the prerequisite state could not be built, because every door that would create a second live holder already refuses. It needs an ordering-controlled double and is carried to §6.6 rather than counted here.

**What it did NOT probe, and said must not be read as cleared:** Postgres, `sqlite_minimal` and the full suite (the resource gate); cross-namespace anything, including per-namespace variants of trip 14; `approve`'s pending-proposal window as a door **in its own right** for other word classes; `attributes`, edge instances, `record_use` and the whole ACTIONS layer.

#### Round 3 — fix-auditor lens (pointed at round 2's fixes **and** at item 1's, some of them hours old)

**The register's counted policy held for the SIXTH row running, and this time it is sharper than that: every single finding is inside a fix made in THIS ROW, and six of the eight are inside fixes made in this ROUND.**

| # | finding | disposition |
|---|---|---|
| M1 | **`C19-87`'s quantifier deleted a true warning.** Rule U's *every candidate has retired it* was applied to `landed` as well as to `candidates` — but **a landing is a fact and a candidate is a maybe**. **[Observed, sqlite + async mirror]** one invocation landing `person_links` in `tenant_a` (retired) **and** in `default` (active) answered `()` where the `tenant_a`-only landing warns. `C19-83`'s FIRST direction, restored by the fix for its second — and the answer to *can a host suppress this?*: one appended `add_edge` did it | **fixed** — `C19-91` |
| M2 | **`projection`'s POOL was ONE un-paged `list_types` read while `_scope_census` paged the same scope to exhaustion in the same call** *(graded BLOCKING by the integrator lens, which found it independently — see below)* | **fixed** — `C19-92` |
| M3 | **`C12-19` filed a FABRICATED correction.** `standing` falls back to the eighth trip's variant-spelling row; with an incoming `deprecated` row the `name_previously_retired` branch is skipped, so the alias diff ran against a row the call never touches. **[Observed]** `beta_` retired holding `zzz_word`, an import of a `deprecated` `beta` answered `aliases_removed:zzz_word` and filed the event on `beta` — while `beta_` **still held the word** and `beta` never had | **fixed** — `C12-20` |
| m1 | `C9-32`'s claim and §5.9's sentence — *the skipped words are stated rather than silently filtered* — were both true only when at least one word **also survived**, because the block was gated on `repoint_words` | **fixed** — `C9-35` |
| m2 | `C19-89`'s clause printed **`5 of 0 row(s)`**: pre-filter count over post-filter denominator *(found independently by the integrator lens)* | **fixed** — `C19-93` |
| m3 | **`C19-90` was right about ONE of three identity segments.** A `:` anywhere before the `#` yields four segments, so `parse_ref` **raises** for `name`, `kind` and an `EdgeRef.family` too; all three said *"reads back as a DIFFERENT reference"* | **fixed** — `C19-94`, and the consequence is **asked** of `parse_ref` now rather than classified |
| m4 | **axis nine's asymmetry survived at two of its five fixtures.** The thirteenth trip's record names *"the asymmetry between two fixtures in one axis"* as the entire gap and `_repeat_merge` was corrected; `_repeat_import` and `_repeat_reinstate` still repeated into the **same** row, which is idempotent by coincidence and can pose nothing | **fixed** — both repeat into a different target now, **both mutation-proved** (no live defect at either door: `import_refused:alias_collision` and `alias_collision` are the shipped answers) |
| m5 | the new `not census_complete` sentence said *"an all-zero answer"* over counts that were not zero | **fixed** — it is about the READ now, `C19-92` |

**What it verified SOUND:** `C12-19` on the row it was written for; `C9-33`'s call-site warning; `C9-32`'s two-sided filter; `C19-87`'s explicitly-scoped path (no host-supplied list can move it) and its no-inputs fallback; `C19-89`'s gating when `unreviewed` was not asked; `_scope_census`'s termination on every double, including the repeated-cursor guard; `C10-20`'s invariant at the sibling doors; both new warning values with their §5.4 rows; `EdgeRef` opacity; and that the `import_refused:*` branches drop `extra_import_warnings`, so nothing claims a removal that did not happen.

#### Round 3 — integrator lens (R70 `projection` EXECUTED, R71 `_retired_blast_radius`, R73 `review_invocation`)

| # | finding | disposition |
|---|---|---|
| B1 | **`projection` pages one read of the scope and not the other.** **[Observed, `DegradedAdapter(page_cap=3, page_cursor=True)`, 9 families]** `counts={'ingest': 3, 'publish': 0, 'report': 0}` against a truth of `6/2/3`; `over_by=0` — *everything fits* about a scope §10 exists to say does not; `why_incomplete` **positively asserting** *"groups no family in this scope carries: ['publish','report']"* about two groups **five families carry**; and a truncated pool **refusing a live group as a typo** (`Refusal(action_family_unknown)` for a group an active registered family declares). Reproduced on the async mirror. Honestly noted as **not reachable on the two shipped SQL backends today** — a contract-level defect a third-party backend author hits first | **fixed** — `C19-92`; the pool is the census, one read, and the typo refusal and the unknown-groups claim are both gated on it finishing |
| M1 | **`C19-87` made the ledger's own knowledge subordinate to the guess it was meant to correct.** `o.namespace in candidates` meant `landed` was empty in exactly the case where the correction matters. **[Observed, both directions, sqlite + async]** false positive: family ACTIVE in `beacon` where the edge landed, warned because the inputs named a namespace where it is retired — *round 2's `M1` sentence verbatim, at the door whose own comment says the ledger knows where the edge went*. False negative: the edge landed in `tenant_b` where the family is retired, inputs named `tenant_a`, **no warning at all** | **fixed** — `C19-91`; an observed effect matching by `(op, family, kind)` **is** where the edge landed, whatever the inputs said |
| m1 | `C19-89`'s clause is arithmetically impossible — `5 of 0 row(s)` *(the fix-auditor's `m2`, found independently)* | **fixed** — `C19-93` |
| m2 | `consumers_at_risk` recomputes `_consumer_report` **once per predicate per evicted family** — five `find_consumers` where two suffice, answer verified identical. And an evicted family `get_type` cannot return contributed **nothing and said nothing** | **fixed** — `C19-95`, both halves |
| m3 | `review_invocation` accepts a review of an `auto`-mode invocation never in any queue, and the event was **indistinguishable from a genuine drain** | **fixed** — `C19-96`. Accepting it is correct (refusing to record a review a person performed is §2.5's *worst available answer*); the event carries the mode of record and `was_queued` |

**What it drove and found SOUND:** **R73's namespace scoping, end to end and on every shape it could construct** — a tenant-scoped operator cannot drain another tenant's queue, cannot drain it by omitting the argument, and every failed attempt left both queues intact (`review(A1, namespace='tenant_b')` → `Refusal(unknown_invocation)`, queues unchanged); two reviews of one invocation append two events with `reviewed_by` following the latest; empty/whitespace `reviewed_by` raises. **`projection`'s arithmetic on every COMPLETE read** — over a 12-publisher / 53-family store with repeats and unknown groups in `order` and `reserved` at 0/2/8: `fits ∩ would_evict == ∅`, `fits + would_evict == dict.fromkeys(order)`, `known == sum(admitted.values())`, `admitted[g] ≤ counts[g]`, `over_by == max(0, total − capacity)`, rule 10-10's repeat charged once. **The census (`C19-88`) telling the three empties apart.** **`_retired_blast_radius` everywhere except the `observed` gate** — no inputs at all, opaque inputs refused at both doors before any namespace question, one warning per family rather than per effect, an unregistered family silent (Rule U), and preflight and record agreeing on every one.

**One thing it found and did not grade, taken anyway:** a scope of **active** `kind="action"` rows that DECLARE no family produced `counts={'publish': 0}`, `fits=('publish',)` and **no scope sentence at all** — a fourth empty cause rule 10-11 does not enumerate. Not graded because *"a bare `kind="action"` row is a shape no shipped call produces on purpose"*; taken because an unreachable-on-purpose shape still reaches a **report**, and a report with nothing to say about its own zero is what that field exists to end (`C19-92`).

#### Round 3, item 1 — every `OPEN` row closed, and two of round 2's own fix shapes corrected in the closing

**All ten `OPEN` rows above are closed** *(commit `dcb1c5a`)*, and the one half that is argued rather than fixed is argued because the finding itself said it needed a ruling: `C19-82`'s **binding layer** is `INTERFACE.md`'s door, and this row's fence bars taking it. It is **Q81**.

Eight contract ids carry the work — `C9-32`, `C9-33`, `C9-34`, `C12-19`, `C19-87`, `C19-88`, `C19-89`, `C19-90` — and **three of them close the same field from three directions**, which is the round's own summary of itself: R75 made `aliases` a write, and the ways to lose a word through it were *transferred and never announced*, *transferred with the wrong words filtered*, and *erased by an ordinary import with no refusal, no warning and no event*. Two warning values were minted with their §5.4 rows per **R3**, taking the vocabulary to **thirty-six**.

> **Two of round 2's fix shapes were wrong in a way that only showed up in the fixing, and both are recorded rather than smoothed.** *(1)* `M2`'s shape said *"gate the sentence on `listing.complete`"* — and `list_types` reports `complete=False` **whenever any filter was applied**, so a `kind`+`namespace` listing is never complete and that gate would have deleted `C19-86`'s sentence entirely rather than narrowing it. **The operand a lens names does not always carry the fact it needs**, which is the ninth trip's shape arriving in a fix *shape*. The census is its own read, paged to exhaustion, carrying its own `complete`. *(2)* `M2` also enumerated an **all-proposed scope** as one of four indistinguishable causes. **[Observed]** no code path in this package persists a `TypeRecord` with `status="proposed"` — a pending proposal is a row in the PROPOSAL store, and `find_types` over a namespace holding one answers `[]`. So the four causes are **three**, the empty-scope sentence is literally true of an all-proposed scope, and what makes `scope_active == 0` reachable is **retired** rows.

### 6.5 What round 2 changed about the register's own rules

The thirteenth trip is the twelfth's class at the sibling caller, and the difference between them is the rule:

> **A tombstone's `name` and `aliases` are an UNCONSUMED PERMISSION.** §5.8 keeps a tombstone's words by design, so nothing in the state is spent when a caller transfers them. Trip 12 answered that **per caller** — *have I run before?* — and `retire_no_op:already_retired` is one caller's special case. The obligation is **per row**: *who holds these words now?* Every caller that transfers a tombstone's words inherits that question, and `merge_types` was the one that never asked it.

And it widens standing rule (b) of the twelfth countersignature. That rule says a change adding a writer of an identity field lands **with** the checker axis that can pose its new failure mode. R75 added `retire` as a writer of `aliases`; the axis landed a round later and **still could not pose the sibling caller's version of the same failure**, because its `merge_types` fixture repeated into one target while its `retire` fixture used two. So: **the axis a new writer lands with must drive every OTHER writer of that field too.**


### 6.6 Round 3 — the cap, and what it must be pointed at

**Round 3 runs because neither round 1 nor round 2 was clean, and it is the cap** (standing constraint 7). It is dispatched from this section rather than from any session's memory. **The row does not land until §6.4 has no `OPEN` row left, or each surviving one is argued here.**

**Three lenses, and the first two are not a choice.**

1. **The FIX-AUDITOR, pointed at round 2's own fixes.** The tenth trip's countersignature made this a standing requirement — *"every round after a fix round begins with a lens pointed at that fix"* — and it has now been right for five consecutive rows, most recently by finding that `C19-83`'s fix **reintroduced the false positive it was written to remove** (§6.4, round 2 M1). Round 2's fixes are its targets: the `merge_types` collision guard (`C10-20`) and axis nine's two fixture corrections, plus whatever of §6.4's OPEN rows are closed before it is dispatched.
2. **The KILL ROW, briefed with all THIRTEEN trip records.** Both rounds so far produced a trip, and the register's own rule from round 2 is the sharpest thing to aim it at: *a tombstone's `name` and `aliases` are an unconsumed permission, and every caller that transfers them must ask who holds them now.* `merge_types` and `retire` have been given that question. **`import_types` and `reinstate` have not been re-examined under it**, and §6.4's round-2 `m4` is already one instance of the class at `import_types`.
3. **One lens on the three surfaces round 2's kill-row lens explicitly did not probe and said must not be read as cleared: R70 `projection` (executed, not read — the greedy-prefix arithmetic and the per-predicate `_consumer_report` recomputation in the `consumers_at_risk` loop), R71 `_retired_blast_radius`, and R73 `review_invocation`'s namespace scoping.** The integrator lens is the natural shape for it: it has produced the findings no correctness lens did for four consecutive rows, and every one of those was in the read half or in what the code does when nobody passed the optional argument.

**The one rule every lens gets, because it is the only one this project has never had to restate:** nothing of substance has ever come from reading. Every finding is constructed and RUN, against the shipped `Registry`, with the observed output pasted.

**Resource gate for round 3's lenses:** single-process SQLite, the `DegradedAdapter` doubles and the async mirror are unrestricted. Postgres and the full three-leg suite are gated on the fleet's four-reading check; a lens must not run either.

**Stop:** two consecutive clean rounds, or — since that is now unreachable within the cap — **three rounds plus an honest convergence note**, which §6 must carry in the shape rows 4c, 4d, #6 and 6b wrote theirs: what the rounds found, whether the findings shrank, what a fourth round would most likely find, and the statement that the row was stopped rather than finished.
### 6.7 The convergence note — and the row was STOPPED rather than finished

**Standing constraint 7's stop rule is two consecutive clean rounds, or three rounds plus an honest convergence note. No round of this row was clean, so the second branch is the one that applies, and this is that note.**

#### What the three rounds found

| round | lenses | BLOCKING | MAJOR | MINOR | kill-row trips | ids after |
|---|---|---|---|---|---|---|
| **1** | kill row (eleven trips) · beacon integrator | 1 | 7 | 5 | **1 — the TWELFTH** | 346 |
| **2** | fix-auditor · kill row (twelve trips) | 2 | 6 | 4 | **1 — the THIRTEENTH** | 347 |
| **3** | fix-auditor · kill row (thirteen trips) · integrator | **2** | **3** | **7** | **1 — the FOURTEENTH** | **366** |

Round 3's row is **distinct findings**: three lenses reported fourteen, and two of them were found **twice, independently** — `projection`'s un-paged pool (the integrator graded it BLOCKING, the fix-auditor MAJOR) and `C19-89`'s impossible denominator. That two lenses aimed at different things collided on one defect is worth more than either report: it is the first time in this row that a finding arrived with its own replication.

#### Did the findings shrink? No — and saying otherwise would be the comfortable reading

**The count did not fall: 13, 12, 12.** What moved is the **mix**: MAJOR went 7 → 6 → 3 while MINOR went 5 → 4 → 7, and both BLOCKING of round 3 are trips or near-trips rather than ordinary defects. Read charitably that is a loop finding smaller things; read honestly it is a loop that has not run out of things to find.

**And one number did not move at all: every round produced a kill-row trip.** Three rounds, three trips — the twelfth, the thirteenth and the fourteenth — in a row whose subject was *amendments to a specified surface*.

#### Where the defects live, counted rather than asserted

**Every single round-3 finding is inside a fix made in this row, and six of the twelve are inside fixes made in round 3 itself, most of them hours old at the time the lens read them.** That is the sixth consecutive row for which this register's counted policy — *the next defect lives in the last fix* — has been right, and this row is its sharpest instance: `C19-87` broke `C19-83`'s first direction while closing its second; `C12-19` filed the fabricated correction it was minted to prevent; `C19-90` was right about one identity segment of three; `C9-32`'s own claim about stating skipped words was false in the pure case. **A fix is the most dangerous code in this repository, and it is dangerous in a specific way: it is written by someone holding one example in mind.**

#### What a fourth round would most likely find, and this is a prediction rather than a hope

1. **Defects in round 3's fourteen new ids and its tenth axis** — by the counted policy, this is where the next one is, and the policy has been right six rows running. The specific shapes to point a lens at: `_word_rows(match_aliases=True)` now reads aliases at three doors that never read them, and `_scope_census` now feeds `projection`'s pool as well as its sentence.
2. **The one suspicion round 3's kill-row lens could not construct**: `merge_types`' `C10-20` escape on `not same_word(holder, left.name)` against `_alias_clash`'s **first-holder-in-page-order** return. It needs an ordering-controlled double, and it is the only [Inferred] finding this row is carrying forward.
3. **Cross-namespace variants of trip 14**, which no lens has touched: `namespace` is untouched across all fourteen trips, and that is now the longest-standing unexamined claim in the register.
4. **The ACTIONS layer under a kill-row lens.** Three rounds pointed that lens at `INTERFACE.md`'s doors; an action family **is** a `TypeEntry`, so every trip's shape has an untested twin one kind along.

#### The landing run, and the one red it produced

**Three legs, one run each: sync `837 passed`, async `874 passed`, both exit 0**, over postgres, sqlite and `sqlite_minimal`. Floors were 757 / 796.

**The first attempt came back with one red and it is worth recording, because it is this row's own defect class arriving from the other end.** `check_capability_matrix.py` reported `stores_events=False` **FAILS, 1 failed** — and round 1 of this row had already learned that a matrix red names itself in seconds if you re-run the one configuration with `-ra` instead of reading a tally. It did: `test_c19_96`, written hours earlier, drives `review_invocation`, which refuses `cannot_record_override` where a review cannot be recorded. That is **correct behaviour and the test's scaffolding rather than its subject**, so the fix is a *declaration*, not code.

> **The symmetry is the finding.** Round 1's own red was `get_closest_marker` silently keeping one of two stacked `@requires_capability` marks, so three ids ran in configurations whose fixtures cannot exist; this row wrote the `iter_markers` fix that made stacking honest, and then **omitted the declaration** that fix exists to honour. A harness that ignores a declaration and a test that makes none are the same defect from opposite ends, and both were caught by the gate built for the first one. Matrix back to **18/18 conformant**, exit 0.

**And a housekeeping fact that is NOT this row's, checked because the brief asks for it:** the `oo-pg` container holds **193** leftover `oo_%` schemas. **[Observed]** the count is unchanged across a fresh Postgres test at this HEAD, so the fixture's teardown (D-4d-9) works today and these are accumulated from earlier runs. Left in place rather than dropped: they block nothing, and 193 schema drops on a shared container is not a change to make unasked.

#### The honest statement

**The row was STOPPED rather than finished.** It is at constraint 7's cap with a BLOCKING found in its final round, a fourteenth kill-row trip fixed in its final commit, and a named, unconstructed suspicion carried forward. Nothing here says the surface is clean; what it says is that three rounds were run, everything they found was fixed or argued, and the argument for a fourth is on the record for whoever rules on it.

> **What is different about this row's last two trips, and it is the one thing that has changed for the better.** The twelfth trip was this row's own regression. The thirteenth split — one variant the row's own, one live at 6b's landing. **The fourteenth is entirely pre-existing, in doors no row of this lineage had touched, and it was found by a lens briefed to look somewhere else.** Two rounds running, the loop has reached past its own diff. That is the strongest argument on the record against `stop` — and it is also, read the other way, an argument that fourteen trips in fourteen rounds says something about the guard surface rather than about any one row. Both readings are the founder's, and the `stop` option is put explicitly for the tenth time.

---

## 7. What the build taught

**A fix is the most dangerous code in this repository, and this row measured it.** Every one of round 3's twelve distinct findings is inside a fix made in this row; six are inside fixes made in round 3 itself, most of them hours old when the lens read them. The register has said *"the next defect lives in the last fix"* for six consecutive rows, and this row is where the sentence earned a mechanism rather than a tally: **a fix is written by someone holding one example in mind.** `C19-87` closed one direction of `C19-83` and re-opened the other. `C12-19` filed exactly the fabricated correction it was minted to prevent, because it took `standing` at face value when `standing` can be a different row. `C19-90` was right about one identity segment of three. `C9-32`'s own claim about stating skipped words was false in the pure case its fixture did not contain. **Every one of those is the fixer's example being narrower than the rule.**

**So the lesson is procedural and it is checkable: a fix must be written against the RULE, not against the reproduction.** Two of round 3's fixes now do that structurally rather than by care — `flat_form_problem` **asks** `parse_ref` which of its two failures a reference has instead of classifying `(field, separator)` pairs, and `projection` builds its pool from the census it already read instead of a second, narrower read. Both replace a judgement that can go stale with a question that cannot.

**A checker only asks the questions its fixtures can pose — the ninth and tenth dresses, in one row.** The thirteenth trip's record named *the asymmetry between two fixtures in one axis* as its entire gap, and this row corrected `_repeat_merge` and left `_repeat_import` and `_repeat_reinstate` repeating into the same row, which is idempotent by coincidence. Then the fourteenth trip found that `include_retired` appeared **zero** times in the whole of `check_merge_guard.py` and both `C16-06` detectors read active rows — *the gate was structurally unable to see a tombstone's words at all.* And the tenth axis, written for that trip, **needed a second pass of its own**: under mutation its `propose_type` row read `held`, because ruling R40 makes that door return a pending proposal and nothing is minted there. **A new axis is a fix, and it is subject to the paragraph above.** Mutation is what caught it, and mutation is now the only reason this file's verdicts can be trusted.

**Two lenses found one defect independently, and that is new here.** `projection`'s un-paged pool arrived twice in one round — BLOCKING from the integrator driving the call, MAJOR from the fix-auditor reading the fix — and so did `C19-89`'s impossible denominator. Three rows of this loop have run three lenses; this is the first finding that arrived with its own replication, and it is the strongest single piece of evidence that the lens *shapes* are pointed at different things rather than at the same thing three times.

**And the loop reached past its own diff, twice running.** Trip 12 was this row's regression; trip 13 split, one variant pre-existing; **trip 14 is entirely pre-existing, in three doors no row of this lineage touched, found by a lens briefed to look at two other calls.** Standing rule (c) — *a tombstone's `name` and `aliases` are an unconsumed permission* — was minted by the thirteenth countersignature for the callers that **transfer** those words, and the fourteenth trip is that same rule at the callers that **mint** one. **The register's lesson is about how a rule is landed, not about the rule:** a rule stated for the callers that prompted it is a rule half-applied, and the question owed in the commit that mints one is *which OTHER callers does this bind?*

**The design is still not what tripped.** Fourteen trips, fourteen caught in test, none in a real merge; `namespace` untouched across all fourteen and `cross_namespace_merge` still refusing on live NYC data. That sentence has now been true for long enough that its own unexamined half is worth naming: **no lens has ever probed a cross-namespace variant of any trip**, and §6.7 carries that to whoever runs round 4.

**One fixture drift, recorded because it is not this row's.** `docs/tools/actions_beacon_probe.py` reports three failures at this HEAD — the design partner's repository moved from the pin (`a895a872` → `71dcd5e7`, 222 → 224 action modules, 19 → 22 categories) and the downstream T1.7 assertions follow the changed counts. **[Observed, by bisect]** the identical three failures at `9fb6ee0`, before any round-3 change. The other three probes pass unchanged (36 / 29 / 39 checks). The probe names its own drift, which is what it was built to do.

---

## 8. Questions for the supervisor — **Q81 onward**

**Q81 — where should the flat-form constraint BIND?** `C19-82` refuses a supplied `InputRef` whose identity segments carry `:` or `#` at **both invocation doors**, and `C19-90`/`C19-94` now say which of the two failures a caller has. But `INTERFACE.md` §2 types `namespace` as an **unconstrained `str`**, and every other door in the package accepts `org:beacon`: a deployment can register types, edge families and action families in such a namespace and **never invoke a single action**, with nothing at the declaration door warning it. Binding the constraint where the namespace is **written** changes a shipped type and is `INTERFACE.md`'s door, which this row's fence bars. *(Raised by round 2's fix-auditor lens; the `why` half was taken in round 3, this half was not.)* **Default if unruled:** leave it at the invocation doors and record the asymmetry in `PACKAGE.md` §7.3, because a namespace constraint added late breaks stored rows that are legal today.

**Q82 — is `merge_types`' `C10-20` escape safe against `_alias_clash`'s first-holder return?** The guard escapes on `not same_word(holder, left.name)`, and `_alias_clash` returns only the **first** active holder in page order — so a genuine third live holder of one of `left.aliases` that sorts *after* a row whose name is a spelling of `left.name` would be swallowed. **[Inferred]** — round 3's kill-row lens could not construct the prerequisite state, because every door that would create a second live holder already refuses, and it reported the suspicion rather than a finding. **This is the only unconstructed claim this row carries forward.** It needs an ordering-controlled double. **Default if unruled:** point round 4's first lens at it before anything else, since a kill-row escape is the one class this register does not carry on an inference.

**Q83 — does a fourth round run?** Standing constraint 7's cap is three, and §6.7 states plainly that the findings did **not** shrink (13, 12, 12) and that every round produced a kill-row trip. The row is landed at the cap under the *three rounds plus an honest convergence note* branch, which is the constraint as written. The question is whether the constraint's cap is still the right number for a row whose every round found a trip. **Default if unruled:** land at the cap as constraint 7 says, and let §6.7's four predictions be round 4's brief if a later row re-opens this surface.

**Q84 — `word_previously_retired` makes a tombstone's aliases permanently unusable in v0, exactly as a retired name is.** That is §5.9's own rule applied at one more field, and it is the fix the fourteenth trip required; it is also a real cost, and the register should name who pays it. A word given away as an alias and then retired can never be minted again — and unlike a retired **name**, a caller cannot see that the word is spoken for without resolving it first. *(This is Q80's neighbour: `list_types(predicate=<a transferred alias>)` answers a confident zero, and that is the founder's.)* **Default if unruled:** keep the permanence, because the alternative is the fourteenth trip; revisit both together whenever Q79/Q80 are ruled, since all three are one question about what a tombstone's words mean to a reader.
