# 6D-RUN — the dedicated IDENTITY-SURFACE row

**Opened by the founder, [ruling R89](../decisions/2026-09-04-founder-ruling-R89.md), 2026-09-04
22:44 ("agree with your rec"), on the eleventh put of the kill row's `stop` question.** The kill
row's adversarial loop leaves the build rows and lives here. This row has **no feature, no
amendment and no product change of its own** except what closing a finding it constructs requires.

**Why the row exists, in one sentence.** Row 7a demonstrated that this loop can *predict* where its
next defect will live — seven pre-registered predictions at `4f3b2eb`, seven confirmed — and, in the
same breath, that **prediction is not prevention**: P3 was written by the author of rule 3-19,
*after* rule 3-19 existed, so it could only ever be confirmed. In a row with no diff of its own the
prediction arrives **before** the rule, which is the only configuration in which the register's
demonstrated capability becomes the thing it has never had.

**The lens set** is the **fourteen kill-row trip records** and the **eight instance-surface cells**
(`I-1`…`I-8`), read as ONE register:
[`2026-08-29-3c-rulings-R6-R12.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-08-29-3c-rulings-R6-R12.md),
including its standing rules (a)–(e) and every countersignature.

**The surface** is the **type half, which is shipped**. The **instance half exists only as a spec**
([`INGEST.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INGEST.md)): this row
**predicts** against it and hands those predictions to the `INGEST` build row. It does not build it,
and it does **not** take **E22** or **E2**, which stay that row's first two obligations per
`INGEST.md` §8.1a.

**Suite floor, restated at the start as the brief requires** — row 6c's landing at `0c0c7f6`, which
row 7a (a spec row) did not move: **366 ids, sync `837 passed`, async `874 passed`, three legs,
capability matrix 18/18, `check_merge_guard.py` at ten axes.** This row never drops below it.

**Kill-row trip count at the start of this row: FOURTEEN.** It stays fourteen until the supervisor
countersigns otherwise; classification is not this worker's (R83). **It did: see [§6.6](#66-countersigned--r90-and-r91-the-count-is-sixteen) —
[R91](../decisions/2026-09-04-6d-supervisor-ruling-R91.md) countersigns the FIFTEENTH and SIXTEENTH trips and
[R92](../decisions/2026-09-04-6d-supervisor-ruling-R92.md) the SEVENTEENTH, EIGHTEENTH and NINETEENTH. **FOUR of the
five were PREDICTED at `d4b86a8` before any lens ran. The count is NINETEEN.**

---

## 0. PRE-REGISTERED PREDICTIONS — written and committed BEFORE any lens, probe or construction exists

> **This section is the row's first deliverable and its ordering is the entire point of the row.**
> It is committed and pushed **before a single probe is written**. A prediction written after a probe
> exists is a *confirmation*, not a prediction, and the record is required to say which it was.
> `git log` is the check: the SHA that lands this section precedes every SHA that lands a probe.
>
> The method is [`7A-RUN.md` §6.11](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md)'s
> — every prediction carries **its falsifier, stated in advance** — and the scoring table at §0.7 is
> [§6.16a](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md)'s, reproduced
> empty and filled only when the lenses return.

### 0.1 The surface, enumerated — the address space every prediction below is written against

A prediction that does not name a door is not checkable, so the doors are named first. **[Observed]**
from `ontoloche/registry.py` at this row's start (`722cdcb`); line numbers are that commit's.

**The five doors R89 names, plus the sixth writer the register keeps counting and never enumerated:**

| # | door | line | what it writes that changes what a word resolves to |
|---|---|---|---|
| D1 | `propose_type` | 2131 | `name` |
| D2 | `approve` → `_write_approved` | 2452 / 2559 | `name`, `status` — **and R40 forces every `kind="predicate"` down this two-step path** |
| D3 | `import_types` | 4674 | `name`, `aliases`, `status`, per-row `kind`, one `namespace` per batch |
| D4 | `retire` | 2942 | `status`, `successor`, and (R75) transferred `aliases` |
| D5 | `merge_types` | 4275 | `aliases`, `successor`, `status` |
| **D6** | **`reinstate`** | **3620** | **`status` — it makes dormant words live again, and it is in NEITHER of the fourteenth countersignature's two lists (transfer callers `retire`/`merge_types`; mint callers `propose_type`/`approve`/`import_types`)** |

**The guards:**

| guard | line | scope it reads |
|---|---|---|
| `_word_rows` | 7267 | **one namespace**, `include_retired=True`, **kind-filtered**, `match_aliases` **defaulted `False`** |
| `_word_spellings` | 7352 | an exact `name_in` query over two spellings; its residual is stated in its own docstring |
| `_alias_holder` | 7384 | **one namespace**, `_active_page` — active rows only; name side kind-gated, **alias side not** |
| `_alias_clash` | 7432 | **one namespace**, `_active_page` — active rows only; **neither side kind-gated**; returns the **FIRST holder in page order** |
| `_alias_identity_breach` | 6937 | §5.10 #2/#3 at an alias write; `declared_predicates` is a **REQUIRED keyword** (the eleventh trip's rule) |
| `_identity_breach` | 4085 | §5.10 #1/#2/#3, the R53 extraction; `there_gates`/`here_gates` are **OPTIONAL keywords defaulting to `None`** |
| `_identity_stale` | 1266 | the read-side staleness gate (Q56's cheap half) |
| `_identity_closure` | 5358 | the closure its own docstring says is walked in **both** directions, aliases consulted |
| `_extent` / `_written_extent` | 1135 / 4051 | Rule U's four extent operands |
| `_gates_on` | 659 | the consumer set the ninth trip made computed rather than read |

**The read and the gate:** `resolve_type` (1337), `_search_namespaces` (1750, ruling R6),
`list_types` (2770), `_alias_map` (5277), `_scope_census` (9628), `projection` (9681); and
[`check_merge_guard.py`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/tools/check_merge_guard.py),
**ten axes**, Parts A / A2 / B.

### 0.2 The four seed predictions row 6c handed forward, restated with falsifiers — **S1–S4**

Ruling [**R81**](../decisions/2026-09-03-6c-rulings-R79-R82.md) makes
[`6C-RUN.md` §6.7](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6C-RUN.md)'s
*"what a fourth round would most likely find"* this row's round-1 brief. They are carried verbatim
in substance and given the falsifier §6.7 did not state.

| # | prediction (6c's words, sharpened to an address) | falsifier — what would make this WRONG |
|---|---|---|
| **S1** | **The next defect lives in round 3's fourteen new ids and its tenth axis.** Specifically `_word_rows(match_aliases=True)` now reading aliases at three doors that never read them (D1 at 2176, D2 at 2658, D3 at 4769), and `_scope_census` (9628) feeding `projection`'s pool as well as its sentence. | No lens reports a finding whose subject is a `C4-15` / `C5-13` / `C12-21` id, axis 10, `_word_rows(match_aliases=)`, `_scope_census` or `projection`. |
| **S2** | **The `C10-20` escape is real and its state is constructible.** `merge_types` (4430) escapes on `not same_word(holder, left.name)` while `_alias_clash` returns only the **first active holder in page order** (7441–7455), so a genuine third live holder of one of `left.aliases` that sorts *after* a row spelling `left.name` is swallowed. It needs an ordering-controlled double. **This is Q82 / [R80](../decisions/2026-09-03-6c-rulings-R79-R82.md), and R80 rules it goes FIRST in this row's kill-row lens.** | An ordering-controlled double is built, every page order is driven, and the guard refuses in **every** order — in which case R80's second half applies and the state is pinned as a test proving the doors refuse the construction. |
| **S3** | **Cross-namespace variants of trip 14 exist**, and `namespace` — untouched across all fourteen trips and the longest-standing unexamined claim in the register — is unexamined because **nothing has ever asked it**, not because it holds. | A cross-namespace lens constructs nothing at any of D1–D6, **and** the gate is extended to pose the question and stays green. |
| **S4** | **The ACTIONS layer has an untested twin of every trip.** An action family **is** a `kind="action"` `TypeEntry` (`ACTIONS.md` §2), so it enters D1–D6 through the same code; `import_types` takes `kind` **per row** (4674, `row.get("kind", kind)`), so one batch mixes kinds through one namespace. | A kill-row lens driven at `kind="action"` through all six doors finds nothing that the same lens at `kind="predicate"` does not already find. |

### 0.3 The fourteen trip records — **T1–T14**, one prediction per record, each naming where the record's shape RECURS on the shipped surface

Each row states the record's shape in one sentence (taken from the register, not re-derived), the
address where that shape is predicted to recur, and the falsifier. **No probe has been written and
no construction attempted at the time of this commit.** A claim that is a reading of source is
tagged **[Observed]**; a judgement about what a reading implies is **[Inferred]**.

| # | the record's shape | where it is predicted to RECUR | falsifier |
|---|---|---|---|
| **T1** | *Unknowable is not equal* (trip 1) — a comparison-based guard treating "no evidence" as "equal evidence". | The **capability-degraded skip paths** the ninth trip's fix introduced. Refusal #1 is **skipped** where the backend cannot report membership (`indexes_membership=False`), and `_identity_breach` (4085) takes `there_gates` / `here_gates` as **optional** keywords defaulting to `None` **[Observed]**. **[Inferred]** predict: at least one of the six doors reaches a skip whose outcome is indistinguishable from a pass, with nothing said to the caller. | Every capability-degraded configuration at all six doors either refuses or emits a stated warning naming the skip; no door returns a clean write with a guard silently skipped. |
| **T2** | *Empty is not equal* (trip 2) — two empty extents comparing byte-identical. | The **word-set** operands rather than the extent ones. `merge_types` builds `moving = tuple(a for a in (left.name,) + tuple(left.aliases) if a)` (4428) **[Observed]** — a falsy filter, not an empty-**key** filter — while `same_word` rules an empty key never equal to anything (trip 8, `C4-14`). **[Inferred]** predict: a word set that is non-empty but whose every member has an empty `identity_key` makes a collision guard's question vacuous while the guard reports it as asked. | A probe driving empty-key words through D1–D6 finds every door refusing or warning; no door treats *no comparable word* as *no clash*. |
| **T3** | *A guard written for ONE CALL over a fact MORE THAN ONE CALL can change* (trips 3 and 6). | **D6 `reinstate`.** **[Observed]** `_word_rows` has call sites at 1625, 2176, 2658, 4769 and 7023 and **none inside `reinstate`'s body (3620–3896)**; the fourteenth countersignature's rule-(c) enumeration names five doors and `reinstate` is in neither list, although it writes `status` — an identity field since trip 6 — and makes dormant words live. **[Inferred]** predict a rule-(d) failure **by number** at D6. | The enumeration is shown complete because `reinstate` provably cannot make live a word a tombstone still answers to — proved, not asserted. |
| **T4** | *A caller nobody guarded*, found by the checker's own AST caller enumeration (trip 4). | **The enumeration's file boundary.** Part A scans `registry.py`'s AST for writers of the identity fields. **[Inferred]** predict: a writer of an identity field outside that one module — `ontoloche/actions.py`, or the generated `ontoloche/aio/` mirror — is invisible to Part A by construction, which is trip 4's shape one directory along. | Part A's source list provably covers every module that writes `name`, `aliases`, `successor` or `status`, and a mutation in each such module turns it red. |
| **T5** | *Partial is not equal* (trip 5) — the guards discarded the one signal the read emits. | **Two call sites drop the scan's `why` while four fold it in. [Observed]:** `merge_types` binds `holder, clash_why = self._alias_clash(...)` at **4429** and **`clash_why` is never used again in that method**, whose own comment three lines above says *"It warns and proceeds"* — and `alias_check_incomplete` appears **zero** times in `merge_types`' body (4275–4674). `import_types` binds **`_variant_why`** at **4769** and discards it while folding its other two (4899, 4942). `propose_type` (2234), `_write_approved` (2673) and `reinstate` (3811) all fold theirs. **[Inferred]** predict one defect at two call sites, in standing rule (d)'s countable form. | A truncated scan at `merge_types` and at `import_types`' name door is shown to reach the caller as `alias_check_incomplete` by some other path. |
| **T6** | *Stale is not equal* (trip 6) — the guard looked correctly and then the fact changed. | **`_identity_stale` (1266) and the words that have no row of their own.** Q79 already records that a **transferred alias** is invisible to it. **[Inferred]** predict the same blindness now covers a **second** class minted since: a word a tombstone answers to and that `word_previously_retired` protects — the guard that refuses the mint has no counterpart at the read. | `_identity_stale` returns a warning for a transferred alias **and** for a tombstone-held word, in one store, on every leg. |
| **T7** | *One word is not one string* (trip 7) — the guards compared bytes, the resolver compared normalised words. | **`_word_spellings` (7352) and its own stated residual**: a **retired** row whose NAME is a non-canonical variant of an incoming alias is not found by its `name_in` probe, and the docstring says so in as many words. It is used at `_alias_identity_breach` (7026) and at `retire`'s successor lookup (3154) **[Observed]**. **[Inferred]** predict the residual is reachable at one of those two — the seventh trip alive at HEAD in the one place the register wrote down and did not close. | The residual is shown unreachable at both sites, or closed because `_word_rows`' keyed scan answers the same question at each. |
| **T8** | *An empty key is not a word* (trip 8) — `identity_key` manufacturing mechanism 4 in both directions. | **R79's `namespace_not_flat` is this shape one field along, and this row owns R79 as item 1.** `INTERFACE.md` §2 types `namespace` as an unconstrained `str` and every declaration door accepts `org:beacon`, while `C19-82` refuses those segments at the invocation doors. **[Inferred]** predict: the word-identity rule that governs `name` and `aliases` has no counterpart on `namespace`, so two namespaces that are one word by any normalisation are two scopes to every guard. | `namespace` is shown compared by the same rule as `name` at every door, or shown to need no such rule because no door resolves across namespaces. |
| **T9** | *Nothing on the right-hand side* (trip 9) — the guard compared the left against itself; the fix computed the fact rather than refusing for want of looking. | **The asymmetry between the two extracted guards. [Observed]:** `_alias_identity_breach` (6937) makes `declared_predicates` a **REQUIRED keyword**, which is the eleventh trip's own closing rule; `_identity_breach` (4085) — the R53 extraction carrying refusals #1/#2/#3 — takes `there_gates` and `here_gates` as **optional keywords defaulting to `None`**. **[Inferred]** predict the required-keyword rule was applied to one guard of two: *a fix applied at one call site of N*, verbatim. | Every caller of `_identity_breach` is shown to pass both gate sets explicitly so the default is unreachable, and a mutation removing one turns the gate red. |
| **T10** | *One door disagreeing with itself* (trip 10) — the guard evaluated a state the call destroys. | **D2, the two-step path R40 forces every `kind="predicate"` down.** `propose_type` checks the world at propose time; `_write_approved` (2559) writes at approve time, and the world moves in between — trip 6's sentence with a governance delay measured in days rather than in calls. **[Inferred]** predict a fact checked at D1 and not re-checked at D2, or re-checked against the proposal's stored row rather than against the store as it now is. | Every check `propose_type` performs is shown to be re-performed at `_write_approved` against current state, with a mutation per check. |
| **T11** | *An operand a guard cannot safely default is a REQUIRED KEYWORD* (trip 11's closing rule). | **`_word_rows(match_aliases: bool = False)` (7267) [Observed]** — the operand whose absence *is* the fourteenth trip, defaulted to the value that caused it, on the one function that answers *does any row answer to this word?* **[Observed]** `_alias_identity_breach`'s call at 7023 passes no `match_aliases`, and `resolve_type`'s at 1625 passes none either. **[Inferred]** predict a caller inherits the trip-14 answer by omission. | Both default-taking call sites are shown to want the narrow question for a reason that survives a lens, and the gate poses the wide question at each. |
| **T12** | *The write a call performs must be idempotent in the state the guard read* (trip 12) — a guard evaluated once for a call that can run twice. | **D3 `import_types` run twice, and D2 `approve` run twice.** `retire` has `retire_no_op:already_retired` and `reinstate` has `reinstate_no_op:not_retired`; **[Observed]** no equivalent value exists for an import re-run or a re-approval. **[Inferred]** predict axis 9 drives the four collapsing callers twice and the second-order case — the *same batch* imported twice, a proposal approved twice — is not among them. | Axis 9 is shown to cover a repeated `import_types` batch and a repeated `approve`, each proved by mutation. |
| **T13** | *A tombstone's `name` and `aliases` are an unconsumed permission; every caller that transfers them must ask who holds them now* (standing rule (c)). | **The transfer half at D6 and along D4's chain.** `reinstate` re-activates dormant aliases and asks `_alias_clash` (3808), which reads **active rows only** **[Observed]**, so a word held by a **second** tombstone is invisible there. **[Inferred]** predict the rule-(c) question is asked over active holders at every door and over retired holders at three, and the gap is the same 2×2 the fourteenth countersignature drew. | Every transfer door is shown to ask the retired-holder question, or that question is shown meaningless at transfer doors for a stated reason. |
| **T14** | *Standing rule (c) at the MINT doors; trips 8, 12, 13 and 14 were four quadrants of one table closed one at a time.* | **The table has a third dimension nobody has added: `kind`. [Observed]** `_word_rows` is called with `kind=` at all three mint doors (2176, 2658, 4769) so it is **kind-scoped**; `_alias_clash` (7432) filters by **no kind at all** on either side; `_alias_holder` (7384) gates the **name** side on `other.kind == kind` and the **alias** side on **nothing**. **[Inferred]** predict the open cell is *(aliases × retired × a different kind)*, and that the three guards give three different answers to *does any row answer to this word?* on one store. | A probe shows the three guards agreeing across kinds at every door, or `PACKAGE.md` §4.1's blessing of one word under two kinds makes the disagreement correct **and** the gate poses it. |

### 0.4 The eight instance-surface cells — **N1–N8**, predicted in BOTH directions

The eight `I-n` cells are *one question asked at eight doors* — **which rows answer to this identity,
and did the resolution see all of them?** — and they differ only in how the set went wrong. Each is
predicted **twice**, because R89 gives this row both obligations and only one surface:

- **on the SHIPPED type half**, where the cell's shape is a construction this row may run; and
- **forward onto the INSTANCE half**, where it is a prediction **handed to the `INGEST` build row**
  and this row builds nothing. `INGEST.md` §8.1a's obligations — **E22** and **E2** — stay that
  row's, and nothing here takes them.

| # | cell | on the SHIPPED type half — where the shape is predicted to recur | handed FORWARD to the `INGEST` build row | falsifier |
|---|---|---|---|---|
| **N1** | `I-1` **truncated** — a scan that finds a match answers `existing` at 1.0 over `scanned=3541 of 14627`. | The type half's own truncation signal, dropped at two of six sites — this is **T5**, and N1 is why T5 is graded BLOCKING if constructed rather than MAJOR: the fifth trip is this cell's own ancestor. | Every candidate scan states its `why` and no tie test is evaluated over a partial set; the shipped `_word_rows` / `_active_page` `why` contract is the normative citation, adopted or declined **by name**. | Both dropped-`why` sites are shown to be unreachable in a truncating configuration. |
| **N2** | `I-2` **mis-walked** — the successor chain followed for ONE hop, reported as complete. | **`_identity_closure` (5358) is the control that PASSES** — *"The chain, not one hop (row 4d, round 2)"*, capped and cycle-guarded. Predict the recurrence is not in the closure but in a **caller** that takes its first element: `_alias_map` (5277), `_scope_census` (9628) or `projection` (9681), which S1 already points at. | Rule 3-14 cites `_identity_closure` as normative and must adopt **all** of it — R87's third form of standing rule (d). | No caller of `_identity_closure` uses fewer than all of its results, and each such use is enumerated in the commit that writes it. |
| **N3** | `I-3` **mis-written** — a rule that binds the identity READ and no door that WRITES. | **`_identity_stale` (1266) binds the read and no write door consults it** — Q56's cheap half is a read-side warning, so a write door that would create the stale state is not gated by it. This is **T6**'s other end. | Every `INGEST.md` rule states whether it binds a read, a write, or both, and a rule that binds only the read names the write doors that can create the state it warns about. | A write door is shown to consult the staleness verdict, or the read-only binding is shown sufficient because no write can create the state. |
| **N4** | `I-4` **mis-keyed** — the act's scope key is the raw label, the gate's is `norm`; 71 normalised keys carry more than one raw spelling. | **Two keys in one guard family. [Observed]** `_word_rows` compares by `same_word` (a normalised key) while `_word_spellings` builds an **exact `name_in`** query (7352, 3154) — a byte query and a keyed comparison answering one question, which is trip 7's diagnosis inside the fix for trip 8. | The instance key and the gate key are one key or the difference is stated at every door, per standing rule (e). | The byte query is shown to be a strict pre-filter whose misses are all caught by the keyed comparison downstream. |
| **N5** | `I-5` **mis-timed** — a drained-but-unwritten proposal is invisible; the guard asks who holds an *unreviewed* proposal rather than who holds one. | **The strongest of the eight on this surface. [Observed]** `_alias_holder` and `_alias_clash` read `_active_page` — **active rows only**; `_word_rows` filters callers to `status == "retired"` at all three mint doors. **A row in `status="proposed"` is in neither set**, and R40 forces every `kind="predicate"` through a two-step path that leaves it there. **[Inferred]** predict: between `propose_type` and `approve`, **nothing holds the word** — standing rule (c) at the one status the 2×2 does not have a row for. | Rule 4-11 asks who holds a proposal, not who holds an unreviewed one — and the type half's answer is cited as normative if it has one. | A probe shows a pending proposal's word is held against a second proposal, a second import and a second approval, on every leg. |
| **N6** | `I-6` **mis-counted** — the tied set dedupes on `ref_key`, so two host records under one id collapse to one and answer at 1.0 with `known=1`. | **`_alias_clash` returns the FIRST holder in page order and stops (7441–7455) [Observed]** — a set of holders reported as one. That is **S2 / Q82 / R80**, and N6 is the instance half of the same sentence: *a door that reports one answer for a set it did not count.* | `known` must agree with the set the decision was made over, at every door — `C20-18`'s shape, already an `INGEST.md` obligation. | `_alias_clash`'s single return is shown sufficient because any holder is disqualifying and the escape at 4430 never excuses one. |
| **N7** | `I-7` **mis-governed** — the set is right and the rules judging it belong to another entry; one caller gets both policies. | **`retire(successor=)` moves `aliases` (R75). [Inferred]** predict it does not move — and is not asked whether it should move — the other facts keyed to the word: attribute schemas (R10's name-level override), the consumer report, and the `payload_schema` an action family declares. A word that resolves to the successor at 1.0 while a governed fact still answers from the predecessor is `I-7` on the type half. | Rule 5-7 has **no carrier** in `InstanceResolution` (R86, verified: zero occurrences of `policy` in its printed shape) — the build row states the carrier or states that the rule is inert. | Every fact keyed to a word is shown to follow the word, or shown to be deliberately keyed to the row with that stated. |
| **N8** | `I-8` **mis-directed** — the closure walked FORWARD only, ending in `mode='auto'`: a second row for one identity with no human in the loop. | **`_identity_closure`'s docstring says the walk is BOTH directions and consults aliases (≈5380). [Inferred]** predict a caller that walks it forward only, or a door that asks *who does this word point to* and never *who points at this word* — the second question is what `_alias_map` (5277) exists for, and it is one function rather than the closure. | `INGEST.md` has **zero** occurrences of `backward` and **zero** of `alias` (R87, verified) — the citation must adopt or decline both **by name**. | Every caller of the closure is shown to take both directions, and a mutation reversing one turns a check red. |

### 0.5 The GATE — countable absences pre-registered **before** the round, which no previous row has done

Nine consecutive trips have ended with a paragraph titled *why the checker exited 0*, and since trip
eleven that paragraph has been **countable rather than descriptive** — *zero occurrences of
`register_consumer`*, *zero repeated calls on one row*, *zero occurrences of `include_retired`*.
**Every one of those counts was taken AFTER the trip.** This section takes them first. Counts are
**[Observed]** in
[`check_merge_guard.py`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/tools/check_merge_guard.py)
at `722cdcb`.

| # | the count, taken now | what the gate therefore cannot pose | falsifier |
|---|---|---|---|
| **G1** | `cross_namespace`: **0**. Every fixture namespace literal in the file is `"default"` (19 occurrences; `namespace="default"` 11 times), and the only other namespace-shaped literals are the actor `"user:sd"` and the consumer `"svc:meta"`. | Nothing in the ten axes has ever driven **two namespaces**. The claim *"`namespace` is untouched across all fourteen trips and `cross_namespace_merge` still refuses on live NYC data"* is repeated in fourteen countersignatures and rests on a gate that **cannot pose a cross-namespace question at all**. This is **S3** made countable. | The gate is shown to drive a second namespace by some path these counts miss. |
| **G2** | `kind="action"`: **0**. The kinds driven are `predicate` (60), `edge` (4), `entity` (3), `data` (1). | An action family **is** a `TypeEntry` and enters the same six doors, and the gate has never driven one. This is **S4** made countable, and the eleventh trip's ACTIONS-layer sibling (`ref_kind` trusting the caller's byte) is the evidence that the layer is reachable. | The gate is shown to drive an action family, or `kind="action"` is shown to be structurally unable to reach D1–D6. |
| **G3** | `include_retired`: **2** — both added by axis 10 for the fourteenth trip. | Nine of the ten axes still cannot see a tombstone's words. Axis 10 closed the mint doors; **[Inferred]** predict the transfer doors and D6 `reinstate` are still driven over active rows only, which is **T3** and **T13**. | Every axis is shown to hold `C16-06`'s invariant over rows of every status. |
| **G4** | **[Inferred]** the *status* dimension has no `proposed` fixture. | `C16-06`'s detectors filter to active rows; axis 10 added retired ones; **nothing drives a row that is `proposed` and not yet approved** — which is the state R40 forces every predicate through. This is **N5** made countable, and it is predicted here so the count is on the record before the round rather than in its post-mortem. | A `proposed`-status fixture is found in the file, or the state is shown unreachable at every door. |

**The prediction this section is really making, stated plainly so it can fail:** the round's *why
the checker exited 0* paragraph — if there is a trip — will name one of G1–G4, and the register will
be able to say for the first time that the gate's blind spot was written down **before** the trip
walked through it. If the round produces a trip whose gate-blindness is **none** of G1–G4, that is a
falsification of this section and it will be recorded as one.

### 0.6 What would falsify the ROW's reading, rather than confirm it

Taken from `7A-RUN.md` §6.11's closing paragraph, because the same trap applies here and is worse in
a row with no diff:

1. **If every lens comes back clean**, that is not a victory. This row's lenses are pointed at the
   surface fourteen trips already visited; a clean sweep is evidence that the lenses were pointed
   where the last three rows' fixes already looked. The convergence note must say so.
2. **If the predictions score high but nothing is PREVENTED**, the row has reproduced row 7a's own
   indictment one surface along. §6.16a's sentence is the standard: *predicting your own next defect
   and then shipping it is not a success.* This row has no diff to ship, so the equivalent failure
   is **predicting a defect and closing it as a finding rather than as a rule that binds every door**
   — which is standing rule (d), and it has failed by name eleven times in this register.
3. **[Inferred]** a shrinking finding count is the weakest signal this register has, per row #4's
   round 3. It is not evidence of convergence and will not be reported as such.
4. **If a construction reaches a shipped door and lets two identities answer to one word, it is a
   kill-row trip — the FIFTEENTH — and it is NOT this worker's to classify.** It is recorded to the
   fourteen records' standard and routed to the supervisor for countersignature (R83). **The count
   is FOURTEEN until the supervisor says otherwise.**

### 0.7 The scoring table — **reproduced EMPTY, filled only when the lenses return**

`7A-RUN.md` §6.16a's shape. Thirty predictions: **S1–S4**, **T1–T14**, **N1–N8**, **G1–G4**.

| # | prediction | outcome |
|---|---|---|
| S1 | round 3's new ids and the tenth axis | *pending* |
| S2 | the `C10-20` page-order escape (Q82 / R80, first) | *pending* |
| S3 | cross-namespace variants of trip 14 | *pending* |
| S4 | the ACTIONS-layer twin | *pending* |
| T1 | capability-degraded skip = pass | *pending* |
| T2 | empty-key word set makes a guard vacuous | *pending* |
| T3 | `reinstate` is the unenumerated door | *pending* |
| T4 | an identity-field writer outside `registry.py` | *pending* |
| T5 | `clash_why` / `_variant_why` dropped at two of six sites | *pending* |
| T6 | `_identity_stale` blind to tombstone-held words | *pending* |
| T7 | `_word_spellings`' stated residual is reachable | *pending* |
| T8 | `namespace` has no word-identity rule | *pending* |
| T9 | required-keyword rule at one guard of two | *pending* |
| T10 | propose-time check not re-made at approve time | *pending* |
| T11 | `match_aliases` defaulted to the trip-14 answer | *pending* |
| T12 | no no-op for a repeated import or approval | *pending* |
| T13 | retired-holder question missing at the transfer doors | *pending* |
| T14 | the 2×2 is a 2×2×2 and `kind` is the third axis | *pending* |
| N1 | truncation signal dropped (type half) | *pending* |
| N2 | a caller taking one result of the closure | *pending* |
| N3 | a read-bound rule with no write door gated | *pending* |
| N4 | byte query and keyed comparison in one family | *pending* |
| N5 | **nothing holds the word of a pending proposal** | *pending* |
| N6 | one answer reported for a set never counted | *pending* |
| N7 | a governed fact left behind by a moved word | *pending* |
| N8 | a forward-only walk of a both-directions closure | *pending* |
| G1 | the gate cannot pose a cross-namespace question | *pending* |
| G2 | the gate has never driven an action family | *pending* |
| G3 | nine of ten axes cannot see a tombstone's words | *pending* |
| G4 | no `proposed`-status fixture anywhere in the gate | *pending* |

**Scored:** — / 30 confirmed, — falsified, — unreachable. Filled at §6 as each lens returns, and
totalled in the convergence note.

---

## 6. The adversarial loop

*Written as each lens returns, before any fix, per constraint 7. Four lenses were dispatched at
`d4b86a8`, the pre-registration commit: the **kill row** (twenty-two records as one lens, with
R80/Q82 first by ruling), the **fix auditor** (pointed at `0c0c7f6` and everything since), the
**cross-namespace lens** (prediction S3) and the **actions-twin lens** (prediction S4).*

### 6.0 The gate's counts, taken at `d4b86a8` — **after the predictions were committed and BEFORE any lens returned**

**This is the ordering R89 opened the row for, in its smallest form.** Nine consecutive trips ended
with a paragraph titled *why the checker exited 0*, countable since trip eleven — *zero occurrences
of `register_consumer`*, *zero repeated calls on one row*, *zero occurrences of `include_retired`* —
and **every one of those counts was taken after the trip had already walked through the gap.**
§0.5 predicted four gaps; this section takes their counts. `git log` carries the ordering: §0 landed
at **`d4b86a8`**, these counts were taken against that same tree, and the first lens had not
reported.

**[Observed]**, `docs/tools/check_merge_guard.py` at `d4b86a8` — the ten-axis gate that is this
surface's only mechanical guard:

| # | what §0.5 predicted | the count | verdict |
|---|---|---|---|
| **G1** | the gate cannot pose a cross-namespace question | `cross_namespace`: **0**. Every fixture namespace literal in the file is `"default"` — 19 occurrences, `namespace="default"` 11 times. The only other namespace-shaped literals are the actor `"user:sd"` and the consumer `"svc:meta"` | **CONFIRMED as a count.** No fixture, on any leg, at any door, in any of the ten axes, has ever driven two namespaces — and *"`namespace` is untouched across all fourteen trips and `cross_namespace_merge` still refuses on live NYC data"* appears in **fourteen** consecutive countersignatures |
| **G2** | the gate has never driven an action family | `kind="action"`: **0**. The kinds driven are `predicate` 60, `edge` 4, `entity` 3, `data` 1 | **CONFIRMED as a count.** An action family **is** a `TypeEntry` and enters the same six doors; the eleventh trip's sibling already walked a capability-predicate merge to `applied` through that layer |
| **G3** | nine of ten axes cannot see a tombstone's words | `include_retired`: **2**, both added by axis 10 for the fourteenth trip | **CONFIRMED as a count**, with the qualification the count itself carries: axis 10 closed the **mint** doors; whether the **transfer** doors and `reinstate` are still driven over active rows only is T3 and T13, and that is a lens's answer rather than a grep's |
| **G4** | no `proposed`-status fixture anywhere in the gate | `proposed`: **0**. `status="proposed"`: **0**. And `propose_type`: **24** | **CONFIRMED as a count, and it is the sharpest of the four.** The gate drives the propose **door** two dozen times and has **never held a row in the `proposed` state** — the one state ruling **R40** forces every `kind="predicate"` through. §0.4's **N5** predicts that between `propose_type` and `approve` nothing holds the word; this count says the gate could not have told anyone either way |

**What this section is worth, stated so it can be argued with.** A count is not a defect. None of the
four is a finding, and this row will not report one as such. What they establish is the thing nine
post-mortems could not: **the gate's blind spots were on the record before the round, not after it.**
If a trip arrives in this row and its *why the checker exited 0* paragraph names one of G1–G4, the
register can say for the first time that the gap was written down before anything walked through it.
If a trip arrives whose blindness is **none** of these four, §0.5 said in advance that that is a
falsification of §0.5, and it will be recorded as one rather than explained away.

### 6.1 Round 1, lens 1 to return — **the CROSS-NAMESPACE lens. NOT YET: 1 BLOCKING, 3 MAJOR, 2 MINOR.**

*Written to disk as the lens returned, before any fix, per constraint 7. Every claim below was
re-verified by the worker against `ontoloche/registry.py` rather than against the lens's paragraph —
the standard the twelfth countersignature set — and the headline construction was re-run by the
worker independently. Where the worker's reading differs from the lens's, the difference is stated
rather than smoothed.*

#### The answer this row has been unable to write for fourteen countersignatures

*"`namespace` is untouched across all fourteen trips and `cross_namespace_merge` still refuses on
live NYC data"* appears verbatim in **fourteen** consecutive countersignatures. It is **two claims,
and they come apart.**

**Half one — *`cross_namespace_merge` still refuses on live NYC data* — TRUE, and for the first time
it has actually been DRIVEN rather than asserted.** Live NYC Socrata headers (`uvpi-gqnh` 45 columns
→ `dpr`, `erm2-nwe9` 32 → `oti_311`, `693u-uax6` 16 → `dot`), the seven words two agencies both hold,
merged across the boundary: **6 of 6 refused `cross_namespace_merge`**, on sqlite and on the paging
double. **[Observed]** The sentence now has evidence behind it, which it never had.

**Half two — *`namespace` is untouched across all fourteen trips* — TRUE as history and FALSE as
safety.** It was untouched because **nothing had ever asked it**. Asking produced six findings.

**And two negatives this register has never been able to state with evidence, now driven:**

1. **No write door crosses the boundary.** D1–D6 are correctly scoped. **[Observed]**
   `merge_types` → `cross_namespace_merge`; `retire(successor=)` → `successor_unregistered` with
   `found_in: ['dot']`; `reinstate`, `propose_type`, `approve` and `import_types` are
   single-namespace by construction. There is **no door that writes into namespace A while a guard
   reads namespace B** — which is the question §0's T-series was written to ask, and the answer is
   the reassuring one.
2. **No cross-namespace row reaches an identity answer.** `resolve_type`'s **outcome**,
   `list_types(namespace=None, predicate=…)` and `_identity_closure` all resolve per namespace;
   R6 hits stay in `alternatives`. **[Observed]** `list_types(predicate='commentable',
   namespace=None)` → `[('dot','memo'), ('dpr','doc'), ('dpr','note')]`, each carrying its own scope.

> **So the scoping holds, and the whole defect surface is ONE function: `_search_namespaces`
> (`registry.py` 1750–1990), ruling R6's cross-namespace *advisory* read.** It is the only guard in
> the package that reads more than one namespace, **and it is built out of none of the identity
> machinery.** **[Observed, worker-verified]** `sed -n '1750,1990p' ontoloche/registry.py | grep -c
> "same_word\|identity_key"` → **0**, against **27** in the file as a whole.
>
> **Nothing constructed here lets two identities answer to one word. This is NOT a fifteenth trip
> and the count stays FOURTEEN.**

#### The findings

| # | severity | the defect | disposition |
|---|---|---|---|
| **X1** | **BLOCKING** | **A word a live tombstone in another namespace still answers to is invisible, under a `complete=True` seal.** `_search_namespaces` decides *is this word burned elsewhere?* with `rec.status == "retired" and rec.name == candidate` — **[Observed, worker-verified at `registry.py:1834`]**, the row's **name only**, so the tombstone's `aliases`, which §5.8 says it keeps **by design**, are never consulted. The async mirror carries the identical comparison **[Observed, `ontoloche/aio/registry.py:1530`]** | **ACCEPTED, OPEN.** The **FOURTEENTH** trip's own shape — *a tombstone's `name` and `aliases` are an unconsumed permission* (standing rule (c)) — one scope along, at the read rather than at a mint door. It is also Rule U's confident negative in the call ruling **R6** exists to prevent: *"scoping without lookup reintroduces mechanism 2"* |
| **X2** | MAJOR | **Cross-namespace matching is by BYTES; the home namespace's is keyed.** `rec.name == candidate` at **[Observed]** `registry.py:1867` (and 1834), mirrored at `aio/registry.py:1563`/1530, plus `ProposalQuery(name=candidate)` in `_rejections_everywhere` — three byte sites, against `_word_rows`/`same_word` governing the same question at home | **ACCEPTED, OPEN.** The **SEVENTH** trip verbatim — *one word is not one string* — at a site §0 named in neither its guard table nor T7 |
| **X3** | MAJOR | **The kind-blind fix was applied to the exact-name probe only.** `exact_elsewhere` is kind-blind (the row-3e round-1 fix, `registry.py:1866`) while the **scoring pool** three lines later is kind-filtered — **[Observed, worker-verified at `registry.py:1877–1878`]** `if kind is not None: pool = [rec for rec in pool if rec.kind == kind]`. With `kind=` supplied, a word held elsewhere as an **alias** or under a **variant spelling** produces total silence | **ACCEPTED, OPEN.** Standing rule (d)'s countable form — *a fix applied at one call site of N* — which is the NINTH, TENTH and ELEVENTH trips' single sentence, one function along |
| **X4** | MAJOR | **`namespace` has no word-identity rule, and no door can undo a split it creates.** **[Observed]** 27 keyed comparisons in `registry.py` and **zero** applied to a namespace value, in `registry.py`, `actions.py`, `edges.py` or `attributes.py`. `nyc_dpr` / `NYC_DPR` / `nyc__dpr` / `nyc-dpr` are one word by `same_word` and four scopes by every door; each answers its word at **confidence 1.0**; and `merge_types` refuses `predicate_merge` while `retire(successor=)` refuses `successor_is_self`, so **no door can reconcile them** | **ACCEPTED, OPEN.** The **EIGHTH** trip — *`identity_key` manufacturing mechanism 4* — one field along. One agency with two loaders becomes N scopes and there is no way back |
| **X5** | MINOR | **Guard #4 fires fourth, over operands the first three have already crossed.** `_identity_breach(left, right)` runs at `registry.py:4312`, `if left.namespace != right.namespace` at 4330, so #1/#2/#3 compare two namespaces' extents as one set. **[Observed]** three of four cross-namespace merges return `predicate_merge` — including a **kind mismatch** — and only identical non-empty extents reach `cross_namespace_merge` | **ACCEPTED.** Outcome safe, story wrong: `C9-19`'s class, named in this method's own comment. On live NYC data #4 does fire 6/6 because the shared columns have empty-but-equal extents |
| **X6** | MINOR | **`import_types` silently ignores a per-row `namespace`.** **[Observed]** a row carrying `"namespace": "dot"` in a batch called with `namespace="dpr"` is written to `dpr` with `warnings=()`; the `dot` row is untouched. A Foundry dump with a namespace column lands its identities in the wrong scope with nothing said | **ACCEPTED.** Accepted-and-ignored — the `mark_reviewed` shape row 6c fixed at `registry.py:9289` |

#### R79 / Q81 — this row's item 1, and its evidence question is now ANSWERED

R79 rules `namespace_not_flat` in two steps: a **warning** at the three declaration doors now, and a
**refusal one row later**, *"only after the warning has been live for a row and the `capability`-style
evidence question — did any reference backend or the design partner's harness ever write one? — has
an answer."* R79 marked its own answer **[Inferred]**. The lens answered it:

- **[Observed]** every declaration door accepts `org:beacon` and it resolves at **1.0**; the
  invocation door refuses the same string, and its sentence is exactly the state the warning is for:
  *"`namespace='org:beacon'` contains ':', which `ACTIONS.md` §2.3's flat identity form spends as a
  separator — `ref_key` would write a string `parse_ref` RAISES on."* `parse_ref` does raise.
- **[Observed]** the full namespace-literal census over the repo: the gate is 11 × `"default"`; the
  contract suite is `default` 176, `dpr` 39, `oti_311` 21, `tenant_a` 13, `dot` 6, `agency` 6,
  `tenshen` 5 and eight singletons. **No reference backend and no harness has ever written a `:`
  namespace.** R79's `[Inferred]` becomes `[Observed]`, which is the precondition its step two names.
- **[Observed]** a driven negative worth keeping: R6's `{namespace}:{name}` alternative label is
  **not** ambiguous, because `NAME_RE` forbids `:` in a name, so the label splits uniquely at the
  last colon. And `_CURSOR_SEP` is `\x1f`, not `:`, so keyset pagination survives a `:` namespace
  (`ontoloche/backends/_sql.py:687`).

#### What the worker verified independently, and the one place the lens's summary overstates

**Verified at source, not taken from the paragraph:** `registry.py:1834` (name-only tombstone test),
`1867` (byte comparison), `1877–1878` (kind-filtered pool beside a kind-blind probe), the zero/27
keyed-comparison counts, and the async mirror at `aio/registry.py:1530`. **Re-run independently by
the worker**, from the probe's own directory with `PYTHONPATH` at the repo root:

```
resolve_type('boro_nm')  from 'oti_311', naming EVERY namespace
   complete       = True
   why_incomplete = ''
   tombstone seen = []
   reason = "nothing in the vocabulary fits 'boro_nm'; near misses in other namespaces are
             listed in alternatives: default:equivalent_to, dpr:boro_ct, dpr:borocode"
```

— while `dpr:boroname` is a **live tombstone whose `aliases` are `('borough', 'boro_nm')`**. The
byte-exact name **is** surfaced (`dpr:boroname was RETIRED there`); the two words the same tombstone
answers to are not.

**The overstatement, recorded rather than smoothed.** The lens's table lists `borough` alongside
`boro_nm` as silent. **[Observed]** it is not: `resolve_type('borough')` answers *"'borough' is
already in the vocabulary"*, because the caller's own namespace holds a `borough` column — a
different fact reached by a different path. **X1 stands on `boro_nm` and `boro_name`**, and stating
that narrowing here is standing rule (a)'s spirit applied to a lens report: the finding is what
reproduces, not what the summary says.

#### Scoring — §0's predictions, first four scored

| # | prediction | outcome |
|---|---|---|
| **S3** | cross-namespace variants of trip 14 exist; `namespace` is unexamined because nothing asked it | **CONFIRMED — at the READ, and its falsifier's first conjunct was MET.** §0.2 stated the falsifier as *"a cross-namespace lens constructs nothing at any of D1–D6 **and** the gate is extended to pose the question and stays green."* The first conjunct **held**: nothing was constructed at any write door. The second was never reached, and this row does not get to claim a falsification it did not run. **The prediction is confirmed at a surface §0 did not name** — X1–X3 are all `_search_namespaces` |
| **T8** | `namespace` has no word-identity rule, so two namespaces that are one word are two scopes to every guard | **CONFIRMED, countably** — 27 keyed comparisons, **zero** on a namespace. Both branches of its falsifier are closed: `namespace` is not compared by `name`'s rule at any door, and the *"no door resolves across namespaces"* escape fails, because `_search_namespaces` reads a `namespace=None` census, scores across namespaces, and queries the proposal store across namespaces |
| **G1** | the gate cannot pose a cross-namespace question | **CONFIRMED, and it reaches further than §0.5 claimed.** `cross_namespace` 0, `into_namespace` 0, `retired_elsewhere` 0 in the gate; 11 namespace literals, all `"default"`. **And the blind spot is in the contract suite too**: the R6 test body carries **0** `alias` and **0** `same_word\|identity_key` — every R6 assertion uses a byte-exact candidate |
| **T7** | `_word_spellings`' stated residual is reachable | **EXTENDED, not scored.** The seventh trip's shape is live at `_search_namespaces` 1834/1867 — a site §0 named in neither its guard table nor in T7. T7's own subject (`_word_spellings`) was not reached by this lens and stays *pending* |

**§0 predictions this lens found FALSE: none.** Every prediction it touched held.

#### A CORRECTION to §0, appended rather than edited over

§5.8's rule — *a correction is a new event, never an edit* — applied to this row's own
pre-registration. **§0.1's guard table lists ten guards and every one of them reads a single
namespace. `_search_namespaces` is filed under *"the read and the gate"* and it is in fact the
register's ONLY cross-namespace guard** — and it is where three of this lens's four substantive
findings live. The pre-registration is not edited; the omission is recorded here, and it is a
**rule-(d) failure by this row against itself**: §0 enumerated the doors a prediction binds and left
out the one function that crosses the boundary the prediction is about.

### 6.2 Round 1, lens 2 to return — **the ACTIONS-TWIN lens. NOT YET: 2 BLOCKING, 3 MAJOR, 1 informational — and TWO constructions routed for countersignature.**

*Written to disk as the lens returned, before any fix, per constraint 7. **Both BLOCKING
constructions were re-run by the worker independently**, and both were then re-run a second time
with `force` and every acknowledgement **removed**, because the fourteen records hold themselves to
*"ordinary calls, no `force`, no acknowledgement"* and the lens's scripts used both. That second run
changed one of the two findings materially, and the change is recorded here rather than smoothed.*

**[Observed]** `py docs/tools/check_merge_guard.py` → **EXIT 0** at HEAD with every finding below live.

#### The one sentence this lens owes the register

**Eleven rows have asserted that the ACTIONS layer inherits these guards. It inherits nine of
fourteen.** Trips 8–14 hold at `kind="action"` **same-kind**; trips 1, 2 and 5 are **skipped by
design** at `registry.py:4216` (`if "predicate" in (here.kind, there.kind)`), per `ACTIONS.md` §2.1,
**with nothing put in their place**; and two are open — the declaration operand (**A3**) and trip 14
**cross-kind** (**A1**).

#### A1 — BLOCKING — the fourteenth trip's fix is KIND-SCOPED, so the tombstone's word is free one kind along

**The defect.** A word a retired `kind="action"` family still answers to as an alias is minted as a
`kind="predicate"` row's **name** at the mint doors with **no refusal and no warning**, and
`reinstate` then refuses `alias_collision` **non-overridably** — the tombstone permanently
un-reinstatable, which is ruling **R11**'s whole reason for existing. That is the **fourteenth
trip's own harm**, at the cell axis 10 cannot pose.

**Worker's independent re-run, with `force` REMOVED — five ordinary calls, no `force`, no
acknowledgement, which is the fourteen records' own standard [Observed]:**

```
sqlite :: tombstone kind='action' -> mint kind='predicate'
  step2_resolve_zeta: ('existing', 'alpha_act', 'action', 1.0)
  step3_retire:       ('retired', ['zeta'], [])
  step4_propose:      ('WRITTEN via approve', 'zeta', 'predicate', 'active', [])   <- warnings EMPTY
  step5_reinstate:    ('REFUSED', 'alias_collision', overridable=False,
                       path_back="retire 'zeta' first, or leave this word retired")
  step5_resolve_zeta: ('existing', 'zeta', 'predicate', 1.0, [])
  D3_import_types:    ('zeta', 'predicate', 'active', ['predicate_requires_review'])
```

**Reproduces in BOTH directions** (action tombstone → predicate mint, and predicate tombstone →
action mint) and **on the async mirror**. **The same-kind controls are the proof it is a defect and
not the design [Observed]:** action→action and predicate→predicate both answer step 4 with
`word_previously_retired:alpha_same`, write nothing, and **reinstate successfully**.

**Why it is T14 exactly.** §0.3 predicted *"the open cell is (aliases × retired × a different kind),
and the three guards give three different answers to* does any row answer to this word?"
**[Observed, worker-verified]** `_word_rows` is called `kind=`-scoped at all three mint doors
(`registry.py` 2176, 2658, 4769) so the action tombstone is not in the scan; `_alias_clash`
(`registry.py:7432`) filters by **no kind at all** and therefore *does* see it at `reinstate`. **One
store, one word, two guards, opposite answers** — the tenth trip's *one door disagreeing with
itself*, with `kind` as the disagreeing dimension (**A2**).

**Why the gate exits 0, countably.** `grep -c 'kind="action"' docs/tools/check_merge_guard.py` →
**0**. Axis 10's fixture `_tombstone_word_store` seeds a `kind="predicate"` tombstone and drives all
three mint doors at `kind="predicate"` — **one kind on both sides in every fixture**, so the third
axis of the 2×2×2 has never been driven on any leg. This is **G2**, and §0.5 counted it in advance.

**Routing.** This reaches shipped doors with ordinary calls and ends in the fourteenth trip's own
harm. **It meets the fourteen records' standard and is routed to the supervisor for
countersignature (R83). The count stays FOURTEEN; classification is not the worker's.**

#### A3 — BLOCKING — §5.10's identity refusals have NO OPERAND for an action family's declaration

**The defect.** Two action families with **contradictory governance declarations** are collapsed
with no refusal and no warning; `resolve_type` then answers the dead word with the survivor at
**1.0**, while `preflight` answers the same word with the **tombstone's** policy — and a Haiku-tier
machine actor records `applied` against a verb the surviving family declares **human-approval-only
and irreversible**.

**Worker's independent re-run with `force` and ALL acknowledgements REMOVED. This is where the
finding NARROWS, and the narrowing is the worker's, not the lens's [Observed]:**

| door | lens's run (`force=True`, `acknowledge=ALL_ACK`) | **worker's ordinary-calls run** |
|---|---|---|
| **D5 `merge_types`** | `('MERGED', 'new_verb', ['old_verb'], …)` | **`('REFUSED', 'definitions_diverge', overridable=True)`** — the door is **not** silent; it is *acknowledgeable past* |
| **D4 `retire(successor=)`** | `('RETIRED','retired',[])` | **`('RETIRED', 'retired', [])`** — **no `force`, no acknowledgement** |
| **D3 `import_types`** | `('new_verb', ['old_verb'], [])` | **`('new_verb', ['old_verb'], [])`** — **warnings EMPTY**, no `force`, no acknowledgement |

**So A3 stands on TWO of three doors with ordinary calls, not three**, and the merge door's real
defect is a weaker and different one: an **overridable** `definitions_diverge` is the only thing
between a caller and a governance collapse that `preflight` treats as non-overridable at invocation
time. The lens's *"all three doors succeed"* is true only under `ALL_ACK` and is corrected here.

**What follows on the two doors that do walk it, unchanged by the narrowing [Observed]:**

```
resolve_type('old_verb')  -> ('existing', 'new_verb', 'action', 1.0, [])      <- 5.3's guarantee
preflight('old_verb')     -> ('allowed',  approval_mode=auto,  reversibility=reversible,   warnings=[])
preflight('new_verb')     -> ('refused',  approval_mode=human, reversibility=irreversible, warnings=[])
record_invocation('old_verb', outcome='applied', actor='ai:haiku', tier='haiku')
                          -> ('RECORDED', 'applied', 'old_verb', ['declaration_unjudged', 'approval_unrecorded'])
invocations(family='new_verb') -> 0        <- the survivor's ledger is EMPTY; the record is filed under the dead word
```

**The guards are not inert — they run and have nothing to compare, and the control proves it.**
**[Observed, worker-verified]** give the two families diverging declared `predicates` with a consumer
gating on one, and `merge_types` **and** `retire(successor=)` both refuse `different_consumer_sets`,
**`overridable=False`**. Refusal #2 is skipped at `registry.py:4216` on
`if "predicate" in (here.kind, there.kind)` — a **deliberate** skip per `ACTIONS.md` §2.1, since
actions must be mergeable — and **nothing was ever put in its place for what an action family
actually is**: `approval_mode`, `min_auto_tier`, `reversibility`, `effects`.

> **This is the NINTH trip's sentence at a surface it was never asked about** — *a guard that cannot
> read a fact must compute it if the fact is computable, skip and say so if it is not, and never
> refuse for want of looking.* Here the fact **is** in the caller's hand: both families' declarations
> are stored attributes. The guard neither computes nor says so; it passes.

**Why the predicate lens cannot find it.** For predicates, refusal #2 refuses the identical
construction non-overridably at every door. **[Observed]** every predicate control in the lens's twin
table is refused. This is precisely what §0.2's **S4** falsifier asked for — *does the action lens
find anything the predicate lens does not?* — and the answer is yes.

**Why the gate exits 0, countably. [Observed]** in `check_merge_guard.py`: `preflight` **0**,
`record_invocation` **0**, `approval_mode` **0**, `reversibility` **0**, `ActionFamily` **0**. The
gate **cannot construct an action family at all**, let alone drive one through a collapse door. And
in `ontoloche/contract/test_c19_actions.py` and its `aio/` twin: `successor=` **0**, `reinstate(`
**0** — the ACTIONS layer has never been driven through D4-with-successor or D6 on any leg.

**Routing.** Two shipped doors, ordinary calls, one word carrying two governance identities at
§5.3's guarantee, ending in `applied` at Haiku tier against an irreversible human-approval verb.
**Routed to the supervisor for countersignature (R83). The count stays FOURTEEN.**

#### The rest

| # | severity | the defect | disposition |
|---|---|---|---|
| **A2** | MAJOR | **The three guards give three different answers to *does any row answer to this word?* on ONE store.** **[Observed]** with `action:alpha_act` ACTIVE `aliases=('zeta',)` and `action:beta_act` RETIRED `aliases=('omega',)`, asked as `kind="predicate"`: `omega` → `_word_rows` `[]`, `_alias_holder` `None`, `_alias_clash` `None`, but `_word_rows(kind=None)` `['action:beta_act[retired]']`; `alpha_act` → `_word_rows` `[]`, `_alias_holder` `None`, **`_alias_clash` `alpha_act`** | **ACCEPTED, OPEN.** The TENTH trip — *one door disagreeing with itself* — with `kind` as the disagreeing dimension. It is the mechanism A1 walks through, and it is **T14**'s second clause |
| **A4** | MAJOR | **A RETIRED action family still preflights `allowed` and still records `applied`.** **[Observed]** after `retire`, `preflight` → `('allowed', …)` with **no warning at all**, while `resolve_type` in the same store answers `('proposal', None, 0.4615)` — *this word is not a live type*. `_action_family` (`registry.py:7835`) passes `rec.status` into `ActionFamily` and **no caller ever tests it** | **ACCEPTED, OPEN, and it is standing rule (d) verbatim.** Ruling **R71** minted `edge_family_retired:<name>` for a *declared edge family* retired after declaration, with the words *"`preflight` went on answering `allowed` and `record_invocation` went on warning nothing."* **The identical question about the action family ITSELF was never asked.** **[Observed]** `grep -c 'family_retired' ontoloche/types.py` → **1**, and it is `edge_family_retired`. This is `I-3`/**N3**'s shape — a rule binding the read with no door that writes |
| **A5** | MAJOR | **The store `PACKAGE.md` §4.1 BLESSES cannot be resolved, retired or reinstated.** **[Observed]** one word under two kinds — which `propose_type` permits by name — makes `resolve_type`, `retire` and `reinstate` all **raise `AmbiguousKind`** out of the return type. `retire` and `reinstate` have **no `kind` parameter at all**, so a §4.1-blessed word can never be retired or reinstated by any caller | **ACCEPTED, OPEN, and NOT action-specific** — reproduces at `entity`+`predicate` too, and is reported as kind-general rather than dressed as a twin. It is the **EIGHTH** trip's fourth defect surviving: that record says `resolve_type` *"raised `AmbiguousKind` out of the call designed against mechanism 2, on a store `PACKAGE.md` §4.1 explicitly blesses"*, it was fixed **at the successor lookups**, and `registry.py:1381` — the **first** lookup in the same function — still takes `kind=None`. **A fix applied at one call site of N, inside the fix for a trip whose diagnosis is that sentence** |
| **A6** | informational | **T4 settled, in both directions.** **[Observed, worker-verified]** `ontoloche/actions.py` writes **no** identity field onto a stored record — `grep -nE "(aliases\|successor)\s*="` returns nothing. **T4's named address is FALSIFIED.** But `ontoloche/aio/registry.py` carries **53** `aliases=`/`successor=`/`status=` writes, and Part A's `REGISTRY_SOURCE` (`check_merge_guard.py:126`, parsed at 316 and 454) is `ontoloche/registry.py` **alone**; `grep -c aio docs/tools/check_merge_guard.py` → **0** | **RECORDED.** Mitigated, not closed: `ontoloche/aio/contract/test_generated_matches_source.py` compares the mirror byte for byte — **and [Observed, line 22] it carries `pytestmark = pytest.mark.nonbinding`.** The only thing standing between Part A and a second writer of every identity field is a check ruling **R2** makes non-binding |

#### The TWIN TABLE — all fourteen trips at `kind="action"`, which no row has ever produced

| # | trip | twin at `kind="action"` |
|---|---|---|
| 1 | unknowable extent | **NOT CONSTRUCTIBLE** — refusal #2 skipped at `registry.py:4216`; deliberate per `ACTIONS.md` §2.1. **What replaces it is nothing: that is A3** |
| 2 | empty extent | **NOT CONSTRUCTIBLE**, same gate. `merge_types` on two bare action families returns a `MergeResult`; the predicate control is `REFUSED predicate_merge, overridable=False` |
| 3 | `retire(successor=)` redirects at 1.0 | **CONSTRUCTED, REPRODUCES.** Harmless between identical declarations; **A3** is this row with the declarations diverging |
| 4 | alias onto a retired word | **CONSTRUCTED, REPRODUCES** — written, no refusal, no warning; `resolve_type` at 1.0. Predicate control: `import_refused:predicate_merge`. Subsumed by A3 |
| 5 | partial extent | **NOT CONSTRUCTIBLE**, same gate as 1 and 2 |
| 6 | alias rides across two merges | **CONSTRUCTED, REPRODUCES** — no two active rows on one word, so the harm is the declaration. Subsumed by A3 |
| 7 | one word is not one string (alias door) | **CONSTRUCTED, REPRODUCES** — `aliases=['Commentable_W']` written with no warning; predicate control refuses `predicate_merge`. Subsumed by A3 |
| 8 | variant of a retired NAME | **REFUSED** `name_previously_retired`. The `identity_key` fix is kind-independent and holds |
| 9 | nothing on the right-hand side | **REFUSED** `different_consumer_sets`, non-overridable. `_gates_on` is kind-independent |
| 10 | one branch of two | **REFUSED**, same evidence |
| 11 | one call site of four | **REFUSED**, driven at all four call sites |
| 12 | retire the same row twice | **REFUSED** `retire_no_op:already_retired`. `C9-29` holds |
| 13 | merge a spent tombstone twice | **REFUSED** `alias_collision`, non-overridable. `C10-20` holds — **and `_alias_clash`'s lack of a kind filter is why**, which is the same asymmetry that makes A1 possible. *One guard's missing kind filter closes trip 13 and opens trip 14's twin* |
| 14 | a tombstone's word at the mint door | **SPLITS.** Same kind **REFUSED** (`word_previously_retired`, reinstate succeeds); **different kind REPRODUCES — that is A1** |

#### Scoring

| # | prediction | outcome |
|---|---|---|
| **S4** | the ACTIONS layer has an untested twin of every trip | **CONFIRMED.** Its falsifier — *"finds nothing the same lens at `kind="predicate"` does not already find"* — fails on A1, A3 and A4, each invisible to a predicate lens because the predicate control is refused non-overridably |
| **T14** | the 2×2 is a 2×2×2 with `kind` as the third axis | **CONFIRMED, both clauses** — A1 (the open cell) and A2 (three guards, three answers). §4.1's blessing does **not** make the disagreement correct: `reinstate` refuses the state `propose_type` blesses, and A5 shows the blessed store cannot be governed at all |
| **G2** | the gate has never driven an action family | **CONFIRMED**, worker-verified: `kind="action"` **0**; `predicate` 60, `edge` 4, `entity` 3, `data` 1. The falsifier's escape — *`kind="action"` is structurally unable to reach D1–D6* — is **closed**: it reached all six |
| **N3** | a read-bound rule with no write door gated | **CONFIRMED on the ACTIONS surface** — A4: retirement binds `resolve_type` and no invocation door consults it |
| **T4** | an identity-field writer outside `registry.py` | **FALSIFIED at the address §0 named, CONFIRMED one directory along.** §0.3 named `ontoloche/actions.py` **or** `ontoloche/aio/`; the first is wrong and the second is right. **The record scores this as a partial falsification rather than a confirmation**, because a prediction that names two addresses and is right about one has not earned a clean confirmation, and this register does not grade its own predictions generously |

**§0 predictions found FALSE by this lens: one — T4, at the first of the two addresses it names.**

### 6.3 Round 1, lens 3 to return — **the FIX AUDITOR. NOT YET: 3 BLOCKING (two new), 2 MAJOR — and two more constructions ROUTED FOR COUNTERSIGNATURE.**

*Written to disk as the lens returned, before any fix. Both new BLOCKING constructions and every
countable claim were re-verified by the worker against the shipped code.*

**A correction to the brief, and the lens was right to make it. [Observed, worker-verified]**
`git log 0c0c7f6..HEAD --oneline -- ontoloche/` returns **zero** commits: `0c0c7f6` is row 6c's
**doc-only** landing (`ROADMAP.md`, `STATUS.md`, `docs/README.md`, `6C-RUN.md`). The last fixes on
the identity surface are **`2da0433`** (the fourteenth trip — three mint doors and axis 10) and
**`dcb1c5a`**, with **`e5540ff`** (the thirteenth trip) one commit back. The brief said *"`0c0c7f6`
and everything since"*; the lens widened to the commits that actually contain the fixes, which is
what the lens is for.

#### F4 — BLOCKING — **the trip-14 rule was applied to the incoming NAME only; the same word arriving as an incoming ALIAS is free at three doors**

**The defect.** `2da0433` closed the *retired × alias* quadrant for a word arriving as a row's
**name**. The identical word arriving as an incoming **alias** passes `_alias_identity_breach`, whose
only keyed scan is — **[Observed, worker-verified at `registry.py:7023`]** —

```python
keyed, _keyed_why = self._word_rows(namespace, alias)
```

**`match_aliases` defaulted to `False`: the exact operand whose absence IS the fourteenth trip**,
and the scan's `why` discarded in the same line. §0.3's **T11** predicted this call site by name and
by line before the lens existed.

**Worker's independent re-run — five ordinary calls, no `force` on the mint side, no
acknowledgement [Observed]:**

```
import_types(name='beta', aliases=['commentable'])
   -> [('beta','predicate','active',('commentable',),('predicate_requires_review',))]   <- nothing about the tombstone
reinstate('searchable') -> Refusal alias_collision  overridable=False  path_back=None
merge_types('searchable'->'beta') -> Refusal predicate_merge  overridable=False
resolve_type('commentable') -> existing / beta / 1.0

CONTROL, identical fixture, the word arriving as a NAME:
import_types(name='commentable') -> ('searchable','retired',(…,'word_previously_retired:searchable'))
reinstate('searchable') -> TypeEntry        <- the fix works, at the door it was written for
```

**It is worse than the trip it descends from.** The name door's refusal carries a `path_back`; this
one carries **`path_back=None`**. The tombstone is permanently un-reinstatable and the caller is not
told how it could have been avoided.

**The same state is reached at two more doors** — `retire(successor=)`'s R75 transfer (warnings
`('predicate_requires_review','aliases_transferred:beta')`, nothing about the tombstone) and
`merge_types`' word move. **Three unenumerated doors, one rule.**

**Causation proved by mutation, and the fix is a SURVIVOR in both directions.** A one-line shadow
change of `_word_rows(namespace, alias)` → `_word_rows(namespace, alias, match_aliases=True)` closes
**all three** doors — import refuses `import_refused:predicate_merge`, the transfer and the merge
drop the word, `reinstate` returns a `TypeEntry`. **And with that change the shadow gate exits 0 and
the shadow suite passes.** Nothing pins either answer.

**Class:** the **FOURTEENTH** trip's own harm, one field along — standing rule (c) at the doors that
**write an alias** rather than the doors that **mint a name**.

**Why the gate exits 0, countably. [Observed, worker-verified]** axis 10's door list is literally
`doors = ("propose_type", "import_types", "approve")` (`check_merge_guard.py:2695`) — **three mint
doors, zero alias-write doors, zero transfer doors.** And `word_previously_retired` appears **0**
times in `merge_types` (4275–4674), **0** in `reinstate` (3620–3895), **0** in `retire` (2942–3619),
and **0** in `import_types`' alias-write region.

**Routed to the supervisor for countersignature (R83). The count stays FOURTEEN.**

#### F5 — BLOCKING — **`_alias_holder`'s exact self-skip fires on a STRANGER at `_write_approved`, and `approve` RAISES out of a public governance call**

**The defect.** The row-4d guard at `registry.py:2624` exists for *"the word was free when the
proposal was made and may not be now."* `_alias_holder`'s first line is
`if other.name == name and other.kind == kind: continue` — an **exact self-skip written for a caller
whose row already exists**. At `_write_approved` the row does **not** exist yet, so the skip fires on
a **different** row that took the exact word; the refusal is unreachable for the exact spelling, and
control falls through to `put_type(expect_absent=True)`.

**Worker's independent re-run [Observed], three ordinary calls on the path R40 forces every
`kind="predicate"` down:**

```
A. the EXACT spelling -- what an ordinary import writes
   import_types(name='commentable')            -> [('commentable','active')]
   _alias_holder('commentable','predicate')    -> holder=None  why=None      <- a live row holds it
   approve                                     -> RAISED ontoloche.errors.AlreadyExists

B. a VARIANT spelling -- the guard's own trip-8 case
   _alias_holder('commentable','predicate')    -> holder='commentable_'
   approve                                     -> Refusal alias_collision     <- the guard works

C. two pending proposals for ONE word
   second propose -> a DIFFERENT proposal, warnings=('predicate_requires_review',)
   approve(#1) -> TypeEntry active
   approve(#2) -> RAISED ontoloche.errors.AlreadyExists
```

> **The guard answers the exotic case and crashes on the ordinary one.** And the trip-14 fix at 2658
> is layered directly on top of a guard that cannot fire in its own headline case.

**Worker's addition, not in the lens's report. [Observed]** `grep -n "AlreadyExists"
docs/specs/INTERFACE.md` returns **nothing**: this is an **undocumented exception escaping a
specified governance call**, where §5's contract is a `TypeEntry` or a `Refusal`. A caller written
against the specification cannot catch it.

**Class:** the **TENTH** trip — *one door disagreeing with itself* — and trip 4's shape, a guard
reused at a caller it was not written for.

**§0 scoring, and this exceeds the prediction. N5** predicted *"between `propose_type` and `approve`
nothing holds the word."* **Confirmed — and the second approval does not merely write, it raises.**
**T10** predicted *"a fact checked at D1 and not re-checked at D2"*; the fact is `get_type`, and the
re-check is the one that crashes.

**[Inferred], and the lens said so rather than claiming it:** the async mirror makes the same call at
`aio/registry.py:2320` with a byte-identical self-skip, but its async probe hung and produced no
output, so **no `[Observed]` is claimed on that leg**. Recorded as the lens recorded it.

**Why the gate exits 0, countably.** `ONE_WORD_DOORS` has **3** entries and none is the approve
door; the approve-window branch builds its store with `_alias_only_store` alone, which writes the
word as an **alias**. `_door_import_name` — the only fixture that takes the word as a **NAME** —
appears in the approve window **0** times.

**Routed to the supervisor for countersignature (R83). The count stays FOURTEEN.**

#### The rest

| # | severity | the defect | disposition |
|---|---|---|---|
| **F1** | BLOCKING | **Duplicate of §6.2's A1** — the trip-14 fix is kind-scoped — reported for two things A1 does not carry. **(i) It is not action-specific:** constructed at a `kind="predicate"` tombstone → `kind="entity"` mint, all three doors, `resolve_type('commentable')` → `existing / commentable(entity) / 1.0` while `reinstate` refuses non-overridably. **(ii) It is a MUTATION SURVIVOR:** widening the trip-14 scan to all kinds at D1 — i.e. **repairing** it — leaves `gate exit=0, 183 passed, 240 skipped`. **The kind dimension of this fix is unpinned in both directions** | **ACCEPTED, OPEN, folded into A1's routing.** Two lenses reached it independently from different briefs, which is worth more than either report — the same thing row 6c recorded when two lenses collided on `projection`'s pool |
| **F2** | MAJOR | **`import_types`' name door drops the trip-14 scan's `why`; the two sibling doors report it.** `variants, _variant_why = self._word_rows(...)` at `registry.py:4769`, and `git blame` puts line 4770 (`match_aliases=True`) inside `2da0433` — **the fix widened the question at that call and left its `why` on the floor.** **[Observed]** with six retired rows over a `page_cap=3` and the active rows under it, so the retired-inclusive scan truncates and the active-only scan does not: `import_types` → `('predicate_requires_review',)`, **`alias_check_incomplete` absent**; `propose_type` and `approve` on the identical store → `alias_check_incomplete:this backend caps an unlimited query at 3 rows` | **ACCEPTED, OPEN.** The **FIFTH** trip — *partial is not equal* — **inside the fourteenth trip's own fix**. **T5 CONFIRMED (import half), N1 CONFIRMED.** Countable gate reason: `alias_check_incomplete` occurs **1** time in the whole gate, in the propose-door axis; **no axis asserts the truncation contract at `import_types`** |
| **F3** | MAJOR | **`merge_types` binds `clash_why` and never uses it, while its own comment says *"It warns and proceeds."*** **[Observed, worker-verified]** `clash_why` has **1** occurrence in `merge_types`' body — the binding — and `alias_check_incomplete` has **0**. A merge over a look that finished and a merge over a look that did not are **byte-identical to the caller**: both return `('definitions_similarity:0.6667','definitions_uncertified')` | **ACCEPTED, OPEN.** The FIFTH trip again, at the door `e5540ff` (the thirteenth trip's fix) added. **T5 CONFIRMED (merge half)** — §0.3 named both call sites, 4429 and 4769, before either lens existed |

#### (a) Rule-(d) failures, by number — the countable form R85 minted

1. **`INTERFACE.md` §5.9's new bullet and §5.4's `word_previously_retired:<holder>` row (`2da0433`).** The rule is *a retired row's ALIASES are not reusable*; the commit enumerates **three** doors. **Unenumerated doors it binds:** `import_types`' **alias** write, `retire(successor=)`'s R75 transfer, `merge_types`' word move — **all three constructed at F4** — and `reinstate`'s dormant-alias re-activation.
2. **The same rule, second unenumerated dimension: `kind`.** The rule as written says nothing about the holder's kind; the implementation is kind-scoped. Unenumerated door: every mint door at a cross-kind tombstone (**F1 / A1**).
3. **`INTERFACE.md` §5.4's `aliases_transferred:<successor>` row (`dcb1c5a`, `C9-33`).** The rule is *the one act that moves a word between identities must be announced at the call*. **[Observed]** `aliases_transferred` occurs **0** times in `merge_types`' body — and `merge_types` moves `(left.name,) + left.aliases` onto `right`. Unenumerated door: `merge_types`.
4. **T3 confirmed countably at D6.** `_word_rows` occurs **0** times inside `reinstate`'s body. **The lens could not construct a harm there beyond a refusal that carries a `path_back`, and recorded it as a rule-(d) failure rather than as a construction** — which is the honest grade and is kept.

#### (b) R88 failures — fix commits that did not list what they DECLINED

**[Observed]** `git log -1 --format=%B <sha> | grep -ci "declin"` → **0** for both.

1. **`2da0433`** in fact declined: the incoming-**alias** doors (F4), the `kind` dimension (F1/A1), and `_variant_why` **at the very line it edited** (F2). Its "honest counterweight" paragraph states a *cost*, not a decline list.
2. **`dcb1c5a`** in fact declined: `merge_types`' `clash_why` (F3) — its own housekeeping paragraph edits the comment **three lines above that binding** and says nothing about it — and `merge_types` having no `aliases_transferred` equivalent.

#### (c) Mutation survivors — **2 of 10**, and a survivor count is the measure (E23), not a red count

Baseline `gate exit=0, 183 passed, 240 skipped`.

| mutation | gate | tests | verdict |
|---|---|---|---|
| M1–M3 — trip-14 guard off at D1 / D2 / D3 | 1 | 1 | **red** — axis 10 is honestly proved for its own case, one row each |
| **M4 — widen the trip-14 scan to all kinds at D1** | **0** | **0** | **SURVIVOR** |
| M5–M9 — `aliases_transferred`, `aliases_not_added`, `C9-35`, `aliases_removed` | 0 | 1 | red in the **contract suite only**, never in the gate |
| **`match_aliases=True` at 7023 — F4's repair** | **0** | **0** | **SURVIVOR** |

**The reading, and it is more precise than *the gate is weak*:** axis 10 **is** honestly proved for
the case it claims — M1/M2/M3 each turn exactly one `tombstone word` row red, so it is not green for
a reason other than the one it states. What it does not pin is **the two dimensions either side of
it**: the `kind` argument and the incoming-alias door. And **five of nine** mutations are caught by
the contract suite and not by the gate at all.

#### (d) Scoring, and one methodological near-miss the lens volunteered

**CONFIRMED by this lens:** **S1**, **T5** (both halves), **T10**, **T11**, **T13**, **T14**, **N1**,
**N5** (exceeded — it raises rather than merely writing), **G2**, **G3** (`include_retired` = 2),
**G4** (`status="proposed"` fixtures = 0). **T3** confirmed as a rule-(d) failure by count rather
than as a construction, and graded that way. **T9** confirmed as a **shape only** — `_identity_breach`
has **5** call sites and **1** passes `there_gates=`/`here_gates=`; the lens could not build a defect
from the default because the `None` branch falls back to reading the consumer report off the store
honestly, so it is graded **MINOR and unconstructed** rather than confirmed.

**§0 predictions found FALSE by this lens: none.**

> **The near-miss, recorded because §0.6 asked for exactly this.** The lens's first, coarser fixture
> for T5 made `import_types` *appear* to satisfy T5's falsifier — the active scan truncated too and
> fed the warning by another path — and only the sharpened fixture (retired rows over the cap, active
> rows under it) isolated the trip-14 scan. **A less careful lens would have scored T5 FALSIFIED.**
> That is a fact about how much a falsification in this row's scoring table is worth, and it belongs
> beside the table rather than in a footnote.

> **And §0.6 point 1, applied by the lens to itself:** F1 duplicates A1, and F2, F3 and F5 all live
> inside predictions §0 wrote before the lens existed. **This round's yield is concentrated where §0
> already pointed, which is evidence about the lenses' aim rather than a victory.**

### 6.4 Round 1, lens 4 to return — **the KILL ROW (twenty-two records as one lens). NOT YET: 5 BLOCKING, 4 MAJOR/MINOR — and Q82 is CONSTRUCTED.**

*Written to disk as the lens returned, before any fix. The headline construction was re-run by the
worker independently, including the full 120-permutation sweep. **[Observed, worker-verified]**
`git diff --stat d4b86a8 HEAD -- ontoloche/` is **empty**: no code has moved since the
pre-registration, so every finding stands at HEAD.*

#### K1 — BLOCKING — **R80 / Q82 is CONSTRUCTED. The register's only carried-forward suspicion is now a state.**

**Ruling [R80](../decisions/2026-09-03-6c-rulings-R79-R82.md) put this first in this row's kill-row
lens and gave it two possible discharges: construct the state, or prove the doors refuse it. **The
first was achieved.** R80's second half does not apply.**

**The defect.** `merge_types`' non-overridable `alias_collision` escapes on
`not same_word(holder, left.name)` (`registry.py:4430`) while `_alias_clash` returns only the
**first** active holder in page order (`registry.py:7441`). So a live row whose **name** is another
legal spelling of `left.name` fires the escape, and the genuine third holder behind it in the page
is never seen. **A non-overridable identity guard's answer is a function of sort order.**

**Worker's independent re-run — every page order of the five active rows [Observed]:**

```
page orders in which the guard REFUSED alias_collision : 60 of 120
page orders in which the guard was SWALLOWED           : 60 of 120
ACTIVE holders of 'zeta' after a REFUSED order         : [1]
ACTIVE holders of 'zeta' after a SWALLOWED order       : [2]
every SWALLOWED order begins with : ['aaa_note','bbb_memo','beta','gamma_']
every REFUSED  order begins with  : ['aaa_note','bbb_memo','beta','delta']

beta.aliases                          : ('gamma', 'zeta')
ACTIVE rows answering to 'zeta' AFTER : [('predicate','beta',('gamma','zeta')),
                                         ('predicate','delta',('zeta',))]
resolve_type('zeta')                  : outcome='existing' "'beta' matches at 1.0" confidence=1.0 warnings=()
THE PAIR ASKED DIRECTLY               : Refusal('predicate_merge', overridable=False)
CONTROL, step 5 (the escape-firer) not made
                                      : Refusal('alias_collision', overridable=False, held_by='delta')
```

**Two ACTIVE rows answering to one word — `C16-06`'s whole-store invariant and mechanism 4 — with
`resolve_type` at §5.3's guarantee, on a pair the same registry refuses non-overridably under every
acknowledgement.** Reproduced on the **async mirror** (2 of 4 driven orders swallowed) and on **both
paging doubles**.

**Which record, and it is a NEW SENTENCE rather than a new door.** Trip 13's own guard (`C10-20`), at
the escape R80 named: *a guard that excuses a holder by comparing the holder's NAME to `left.name`
cannot tell `left` from a different live row that is another spelling of `left.name`.* It is also
**N6 on the type half** — a set of two holders reported as one.

**Why the gate exits 0, countably. [Observed, worker-verified]**
`grep -c "reversed(\|shuffle\|itertools.permutations" docs/tools/check_merge_guard.py` → **0**. **The
ten-axis gate contains ZERO page-order controls**; every fixture reads its backend's natural order,
so a guard whose answer is a function of page order is **unfalsifiable by it**. R58's own class —
*a guard never reads a page* — arriving at the file built to enumerate these guards.

**§0 scoring: S2 CONFIRMED, and its falsifier is FALSE.** §0.2 stated the falsifier as *"every page
order is driven and the guard refuses in **every** order."* It refuses in **half**.

#### K4 — BLOCKING — a capability-degraded SKIP whose outcome is indistinguishable from a pass, on **UC1 Tenshen's own declared shape**

**The defect.** `_alias_identity_breach` appends refusal #1's check only `if self.caps.indexes_membership`
(`registry.py:7137`). On a backend declaring it `False` — **the very shape the FIRST trip was about**
— the guard is skipped and **nothing at all is said to the caller**.

**[Observed]**, the same five calls on two backends:

```
A  fully capable sqlite (the CONTROL)
   consumers('ent_a') / ('ent_b')      : ['svc:meta'] vs []
   import aliases=['ent_a'] onto ent_b : warnings=('near_duplicate:ent_a',
                                                   'import_refused:different_consumer_sets')
   resolve_type('ent_a')               : outcome='proposal' type=None confidence=0.8

B  DegradedAdapter(indexes_membership=False)
   consumers('ent_a') / ('ent_b')      : [] vs []
   import aliases=['ent_a'] onto ent_b : TypeEntry(aliases=('ent_a',), warnings=())
   any warning naming a SKIPPED guard  : []
   resolve_type('ent_a')               : outcome='existing' "'ent_b' matches at 1.0" confidence=1.0
```

**Refused non-overridably on one backend, written with `warnings=()` on another, and `resolve_type`
cashes it at 1.0.** The shipped comment at 7158 names the residual as **Q69** — *in the docstring,
not to the caller*.

**Which record — a NEW SENTENCE.** Trips 1 and 9 asked whether *unknowable* equals *equal* or
*different*. **This asks whether *unknowable* equals *nothing to say*.**

**§0 scoring: T1 CONFIRMED and its falsifier FALSE** — §0.3 required *"either refuses or emits a
stated warning naming the skip."* It does neither. **T9 CONFIRMED as a count**: of `_identity_breach`'s
**five** call sites (3092, 3219, 3247, 4312, 7175), **only 7175** passes `there_gates`/`here_gates`;
the other four take the `None` default — the eleventh trip's required-keyword rule un-applied to the
sibling guard.

**Why the gate exits 0.** `_legs()` builds `sqlite`, `sqlite_minimal` and optional Postgres;
`DegradedAdapter(indexes_membership=False)` appears **0** times as a leg. The twelve `page_cap`
doubles are the only degradation the file drives.

#### K2, K3, K5, K6 — four constructions that arrived at findings other lenses reached independently

| # | severity | what it is | independent arrival |
|---|---|---|---|
| **K2** | BLOCKING | The tombstone's word at the **alias-write** doors — `_alias_identity_breach` calls `_word_rows(namespace, alias)` at `registry.py:7023` with `match_aliases` **defaulted `False`**. Reproduced at D3's alias write **and** at D4's R75 transfer; `reinstate` then refuses non-overridably | **= §6.3's F4.** Two lenses, different briefs, same construction |
| **K3** | BLOCKING | `clash_why` bound and never used, so a truncated scan reads as *the words are free* **silently** — and this lens chains it further than the fix auditor did: behind `page_cap=3` the merge proceeds to **two live holders and `resolve_type` at 1.0**, where §6.3's F3 stopped at *byte-identical warnings* | **= §6.3's F3, escalated MAJOR → BLOCKING.** The escalation is accepted: F3 showed the caller cannot tell; K3 shows what it costs |
| **K5** | BLOCKING | `approve` **raises `AlreadyExists`** out of a call typed `-> TypeEntry \| Refusal`, because nothing holds a pending proposal's word and `import_types` mints the row underneath it | **= §6.3's F5**, reached by a different route (import under a pending proposal, rather than the self-skip) |
| **K6** | MAJOR | The **cross-kind** cell — a word a retired predicate answers to is free to an entity mint, and `reinstate` then refuses it | **= §6.2's A1 and §6.3's F1. Three lenses, three briefs, one cell** |

#### K7 — MAJOR — **the round's UNPREDICTED finding, and it was found twice**

**[Observed]** on a store `PACKAGE.md` §4.1 **blesses**, built by two ordinary proposals that are
each accepted with no refusal:

```
merge_types('alpha','beta') -> RAISED AmbiguousKind: 'alpha' exists under kinds ['entity','predicate']
retire('alpha')             -> RAISED AmbiguousKind
reinstate('alpha')          -> RAISED AmbiguousKind
```

`merge_types:4297` and `reinstate:3654` call `self._require(namespace, name)` with **no `kind=`**,
and `_require:540` byte-matches. **Chained with K6, an operator who reuses a tombstone's word
cross-kind lands in a store whose three governance doors are dead for that word.**

**This is §6.2's A5, reached independently.** Neither lens was told about the other. **No §0
prediction names this address** — §0.7 said in advance that *an unpredicted finding is the most
valuable thing a lens can return*, and this round produced exactly one, **found twice**.

**Which record.** Trip 8's fourth defect — *"`resolve_type` omitted `kind=` and raised `AmbiguousKind`
out of the call designed against mechanism 2, on a store `PACKAGE.md` §4.1 explicitly blesses"* — at
**three doors the fix did not reach**. A rule-(d) failure by number.

#### K8, K9 — the remainder

**K8** (MAJOR) restates T8/G1 from the word side — `same_word('org:beacon','org_beacon')` is `True`,
both namespaces accept `alpha` with `warnings=()`, both answer at 1.0. **This is §6.1's X4** and is
not counted twice. **K9** (MINOR): the same `import_types` batch run three times returns a written
row each time with **no no-op value**, and three active predicates were each given the raw alias
`状态` with no refusal and no warning, because `identity_key('状态') == ''`. `resolve_type('状态')`
correctly answers `none`, **so no 1.0 collapse follows and the harm is bounded** — recorded with its
bound rather than dressed up. **T2 CONFIRMED; T12 CONFIRMED for `import_types` and FALSIFIED for
`approve`.**

#### The four §0 predictions this lens reports FALSE — **three accepted, ONE REJECTED**

*This is the row's job rather than a lens's: two lenses disagree about S4, and the worker resolves it
against evidence rather than by averaging.*

| # | the lens's falsification | the worker's adjudication |
|---|---|---|
| **T7** | The `_word_spellings` residual is **not** reachable at `_alias_identity_breach`, because `registry.py:7023` runs `_word_rows(namespace, alias)` — a keyed scan over rows of **every status** — beside the `name_in` probe. That is **T7's own stated falsifier**, verbatim. The other site (`retire`'s successor lookup at 3154) feeds only the `found_in` **advice** in a `successor_unregistered` detail and gates nothing | **ACCEPTED. T7 is FALSIFIED.** And it leaves a smaller finding the lens did not name: **`_word_spellings`' docstring still states a residual that the call site above it closes.** A documented residual that no longer exists is a §2.3 Cause-B hazard for the next reader, and it is recorded here rather than fixed |
| **T12 (half)** | `approve` **does** have the no-op T12 says is missing: run twice it returns `Refusal('already_decided')`. Only `import_types` lacks one | **ACCEPTED. T12 is confirmed for `import_types` and FALSIFIED for `approve`** — a half-score, recorded as a half rather than rounded up |
| **T3 (as a collapse)** | `reinstate` is genuinely unenumerated — `_word_rows` appears **0** times in its body — but **no state could be constructed in which `reinstate` CREATES a second live holder**. In every construction `reinstate` is the **victim** (`alias_collision`, non-overridable), never the door | **ACCEPTED, and it sharpens §6.3(a)4.** The rule-(d) enumeration gap is real and stands; **the predicted *failure by number at D6* does not.** §0.3 predicted a harm at D6 and there is none. Recorded as a partial falsification |
| **S4** | *"The kill-row lens driven at `kind="action"` through the six doors found exactly what the `kind="predicate"` lens found (K2 reproduces verbatim) and nothing additional"* — which is S4's own stated falsifier | **REJECTED, and the reason is evidential rather than a preference between lenses.** This lens's `kind="action"` sweep drove **word-identity** constructions — *does the same word collapse?* — and those do transfer verbatim, which is a true and useful result. But **§6.2's A3 is a DECLARATION collapse reached through D3, D4 and D5 — the word doors — whose `kind="predicate"` control is refused `predicate_merge` NON-OVERRIDABLY at every door.** A3 and A4 are therefore exactly *"something the same lens at `kind="predicate"` does not already find"*, at the doors S4 names. This lens did not run A3's construction **because its own brief told it not to spend the round on the ACTIONS layer**, so its sweep could not have reached the finding that decides the prediction. **S4 stands CONFIRMED (§6.2).** The falsification is recorded, not discarded — a lens's negative that the worker overrules belongs on the record with the argument that overruled it |

#### The lens's own report on §0.5, and it is the most important sentence of the round

The lens checked §0.5's central claim against its own findings — *the round's `why the checker exited
0` reasons will be among G1–G4, written down before the round* — and reported it **honestly and
against itself**:

> **G4 is K5's reason verbatim; rule (c)'s field gap is K2's; G2 is K6's; G1 is K8's. K1's and K3's
> reasons are NEW counts — zero page-order controls, and one `alias_check_incomplete` assertion — so
> §0.5 is NOT falsified, but it is NOT clean either: two of six gate-blindness reasons were not among
> the four.**

**That grading is adopted without amendment.** §0.5 predicted the gate's blind spots in advance and
got **four of six**. The register does not get to call that a clean confirmation, and this row does
not.

#### Scoring from this lens

**CONFIRMED:** S1, **S2**, T1, T2, T5, T8, T9, T10, T11, T13, T14, N1, N5, N6, G1, G2, G3, G4.
**FALSIFIED:** T7 (accepted), T12 for `approve` (half), T3 as a collapse (partial). **S4's
falsification REJECTED** with the argument above.
**Not probed by this lens, stated plainly rather than scored:** T6, N2, N3, N4, N7, N8.

**Routed to the supervisor for countersignature (R83): K1, K2, K3, K4 and K5.** The count stays
**FOURTEEN**; classification is not the worker's.

### 6.5 Round 1, totalled — **four lenses, four verdicts of NOT YET, no lens returned nothing**

#### The findings, deduplicated — because four lenses reached six of them independently

| lens | raw findings | BLOCKING |
|---|---|---|
| cross-namespace (§6.1) | 6 | 1 |
| actions-twin (§6.2) | 6 | 2 |
| fix auditor (§6.3) | 5 | 3 |
| kill row (§6.4) | 9 | 5 |
| **raw total** | **26** | **11** |
| **DISTINCT** | **19** | **8** |

**Six findings were reached by more than one lens from different briefs, and that is worth more than
any single report.** Row 6c recorded the same thing when two lenses collided on `projection`'s pool:
*a finding that arrives with its own replication.* Here:

| the finding | reached by |
|---|---|
| the trip-14 fix is **kind-scoped** | **three lenses** — A1 (actions), F1 (fix auditor), K6 (kill row) |
| the tombstone's word at the **alias-write** doors | F4, K2 |
| `clash_why` bound and never used | F3, K3 — and K3 escalates it MAJOR → BLOCKING by chaining to two live holders at 1.0 |
| `approve` raises out of a governance call | F5, K5 — by two different routes |
| `AmbiguousKind` at the §4.1-blessed store | A5, K7 — **the round's one unpredicted finding, found twice** |
| `namespace` has no word-identity rule | X4, K8 |

#### The seven distinct constructions ROUTED FOR COUNTERSIGNATURE (R83)

*Each reaches a shipped door and either lets two identities answer to one word, or lets a door answer
at §5.3's guarantee on a pair the registry refuses non-overridably. **The worker does not classify
them.** The count is **FOURTEEN** until the supervisor rules.*

| # | construction | the sentence | ordinary calls? |
|---|---|---|---|
| **1** | **K1 — R80/Q82, page order** | a non-overridable identity guard's answer is a function of **sort order**: 60 of 120 orders swallow it, two live rows answer to one word, `resolve_type` at 1.0 | acknowledgements used (the door requires them); **the escape itself needs none** |
| **2** | **F4 / K2 — the alias-write doors** | the trip-14 rule was applied to the incoming **name** only; `_word_rows(namespace, alias)` at 7023 defaults `match_aliases=False`. `reinstate` then refuses with **`path_back=None`** | **five ordinary calls, no `force`, no acknowledgement** |
| **3** | **F3 / K3 — the dropped `clash_why`** | a truncated scan reads as *the words are free*, **silently**, and the merge proceeds to two live holders and 1.0 | ordinary calls on a paging backend |
| **4** | **K4 — the capability-degraded skip** | refused non-overridably on one backend, written with `warnings=()` on another — on **UC1 Tenshen's own declared shape** | **five ordinary calls** |
| **5** | **F5 / K5 — `approve` raises** | nothing holds a pending proposal's word, and the second approval does not merely write — it **raises `AlreadyExists`**, which appears **0 times in `INTERFACE.md`** | **three ordinary calls** |
| **6** | **A1 / F1 / K6 — the cross-kind cell** | the trip-14 fix is kind-scoped, so the tombstone's word is free one kind along and the tombstone is left permanently un-reinstatable | **five ordinary calls**, both directions, async mirror |
| **7** | **A3 — no operand for a DECLARATION** | two verbs with contradictory governance collapse; `preflight` answers the dead word with the **tombstone's** policy and a Haiku actor records `applied` against an irreversible human-approval verb | **two of three doors with ordinary calls** (worker's narrowing) |

#### §0.7's scoring table, FILLED — 30 predictions, pre-registered at `d4b86a8` before any lens ran

| # | prediction | outcome |
|---|---|---|
| **S1** | round 3's new ids and the tenth axis | **CONFIRMED** — F2 is inside `2da0433` itself; K2/F4 is its unenumerated field |
| **S2** | the `C10-20` page-order escape (Q82 / R80) | **CONFIRMED, falsifier FALSE** — refuses in 60 of 120 orders, not in every one. **R80's first discharge achieved; its second half does not apply** |
| **S3** | cross-namespace variants of trip 14 | **CONFIRMED at the READ.** Its falsifier's first conjunct was **met** — nothing constructed at any write door — and that is stated rather than smoothed |
| **S4** | the ACTIONS-layer twin | **CONFIRMED.** The kill row reported it falsified; **the worker REJECTED that** on evidence (§6.4), because A3 is a declaration collapse at the word doors whose predicate control refuses non-overridably |
| **T1** | capability-degraded skip = pass | **CONFIRMED, falsifier FALSE** — K4 neither refuses nor warns |
| **T2** | empty-key word set makes a guard vacuous | **CONFIRMED**, with its bound stated: `resolve_type` answers `none`, so no 1.0 collapse follows |
| **T3** | `reinstate` is the unenumerated door | **PARTIAL.** The enumeration gap is **confirmed by count** (`_word_rows` 0 occurrences in its body); **the predicted HARM at D6 is FALSIFIED** — in every construction `reinstate` is the victim, never the door |
| **T4** | an identity-field writer outside `registry.py` | **PARTIAL.** **FALSIFIED** at `actions.py` (no stored-record identity write); **CONFIRMED** at `aio/registry.py` — 53 writes, invisible to Part A, covered only by a `nonbinding` test |
| **T5** | `clash_why` / `_variant_why` dropped at two of six sites | **CONFIRMED, both halves** — §0 named lines 4429 and 4769 before either lens existed |
| **T6** | `_identity_stale` blind to tombstone-held words | **NOT PROBED** |
| **T7** | `_word_spellings`' residual is reachable | **FALSIFIED** — `_word_rows` at 7023 closes it, which is T7's own stated falsifier. It leaves a smaller finding: **the docstring states a residual its own call site closes** |
| **T8** | `namespace` has no word-identity rule | **CONFIRMED, countably** — 27 keyed comparisons, zero on a namespace |
| **T9** | required-keyword rule at one guard of two | **CONFIRMED as a count** — 1 of `_identity_breach`'s 5 call sites passes the gate sets — **and unconstructed as a defect on its own**, which is how it is graded |
| **T10** | propose-time check not re-made at approve time | **CONFIRMED** — and the re-check is the one that crashes |
| **T11** | `match_aliases` defaulted to the trip-14 answer | **CONFIRMED, and it named `registry.py:7023` by line before any lens ran.** This is the prediction that most nearly became prevention |
| **T12** | no no-op for a repeated import or approval | **PARTIAL.** **CONFIRMED** for `import_types`; **FALSIFIED** for `approve`, which returns `already_decided` |
| **T13** | retired-holder question missing at the transfer doors | **CONFIRMED** — D4's R75 transfer and D5's word move both reach it |
| **T14** | the 2×2 is a 2×2×2 with `kind` as the third axis | **CONFIRMED, falsifier FALSE, by three independent lenses** |
| **N1** | truncation signal dropped (type half) | **CONFIRMED** — F2, F3 and K3 |
| **N2** | a caller taking one result of the closure | **NOT PROBED** |
| **N3** | a read-bound rule with no write door gated | **CONFIRMED on the ACTIONS surface** — A4 |
| **N4** | byte query and keyed comparison in one family | **NOT PROBED** |
| **N5** | nothing holds the word of a pending proposal | **CONFIRMED AND EXCEEDED** — it does not merely write, it raises |
| **N6** | one answer reported for a set never counted | **CONFIRMED on the type half** — K1's `_alias_clash` first-holder return |
| **N7** | a governed fact left behind by a moved word | **NOT PROBED** as predicted — **but A3 is its shape**, reached from the other side: the governed fact is the *declaration*, and it stays with the tombstone |
| **N8** | a forward-only walk of a both-directions closure | **NOT PROBED** |
| **G1** | the gate cannot pose a cross-namespace question | **CONFIRMED**, and further than claimed — the R6 contract test body is byte-exact too |
| **G2** | the gate has never driven an action family | **CONFIRMED**, escape closed — it reached all six doors |
| **G3** | nine of ten axes cannot see a tombstone's words | **CONFIRMED** |
| **G4** | no `proposed`-status fixture anywhere in the gate | **CONFIRMED**, and it is K5's gate reason verbatim |

**Scored: 21 CONFIRMED · 3 PARTIAL · 1 FALSIFIED outright · 5 NOT PROBED.**

#### The four things this round is owed, stated against the row rather than for it

**1. §0.5 got FOUR of SIX, and that is not a clean confirmation.** The kill row graded it against
itself and the grading is adopted: G4, G2, G1 and rule (c)'s field gap were each a *why the checker
exited 0* reason **written down before the round** — but K1's (zero page-order controls) and K3's
(one `alias_check_incomplete` assertion) were **new counts**. Nine trips have ended with that
paragraph written afterwards; this row wrote two thirds of it in advance. Two thirds is the result,
not three thirds.

**2. The yield is concentrated where §0 pointed, and that is evidence about AIM, not a victory.**
The fix auditor volunteered it and it is kept: F1 duplicates A1; F2, F3 and F5 all live inside
predictions §0 wrote before those lenses existed. A round that finds what its own predictions named
has demonstrated that the predictions were good **and** that the lenses were pointed by them.

**3. One falsification nearly went the other way, and that changes what a falsification is worth
here.** The fix auditor's first fixture for T5 made `import_types` *appear* to satisfy T5's
falsifier; only a sharpened fixture isolated the trip-14 scan. **A less careful lens would have
scored T5 FALSIFIED.** Every falsification in the table above should be read with that in mind — and
it is why the S4 falsification was adjudicated rather than accepted.

**4. THIS ROUND PREDICTED. IT DID NOT YET PREVENT — and that distinction is the whole reason the row
exists.** R89 opened row 6d because *"a loop that can predict where its next defect will be is wasted
in a row that writes the rule first and predicts second."* §0 named `registry.py:7023` by line, and
the gate's four blind spots by count, **before any lens ran** — and the lenses then found defects at
exactly those addresses. **But those defects already existed at HEAD.** Prediction ahead of a
*finding* is what row 7a already demonstrated. **Prevention is a rule that binds every door named in
advance, landing before the next defect** — and that is what round 1's fixes have to do to make this
row different from row 7a. Until they do, this row has reproduced row 7a's result one surface along,
and §6.16a's sentence still stands unanswered: *predicting your own next defect and then shipping it
is not a success.*

### 6.6 COUNTERSIGNED — [R90](../decisions/2026-09-04-6d-supervisor-ruling-R90.md) and [R91](../decisions/2026-09-04-6d-supervisor-ruling-R91.md). **The count is SIXTEEN.**

> **The trip count in this row is SIXTEEN from here.** Every *"the count stays FOURTEEN"* above records
> what was true **when that lens returned**, and is left standing rather than edited over — §5.8's rule
> that *a correction is a new event, never an edit*, applied to this row's own run record. This section
> is that event.

#### R91 — A1 is the FIFTEENTH trip; F4 is the SIXTEENTH

The supervisor re-ran every countable claim rather than accepting the records — `registry.py:4216`, the
three `_word_rows` mint-door call sites, `_alias_clash` at 7432, six zero-counts in the gate, and
`check_merge_guard.py` exiting 0 at HEAD with all four findings live. Both are countersigned; the
register carries them in the fourteen records' shape.

**And R91's central sentence is one this register has never been able to write:**

> §0.3 predicted both at **`d4b86a8`** before any lens or probe existed — **T14** named the fifteenth
> **by cell**, **T11** named the sixteenth **by address** (`registry.py:7023`). **Every previous trip
> surprised its row. These two were named in writing, then constructed, and no build row shipped code
> through either door in between. This is the first prevention in the register's history.**

**§0.7 is updated accordingly, in R91's own words:** **T14 — CONFIRMED by construction, before any fix.
T11 — CONFIRMED by construction, before any fix.**

#### The 2×2×2, and what it obliges the fix to be

Trip 14 closed **one** cell: *(retired word × arrives as a NAME × same kind × mint door)*.

| dimension | trip 14 | the FIFTEENTH | the SIXTEENTH |
|---|---|---|---|
| how the word arrives | name | name | **alias** |
| the holder's kind | same | **different** | same |
| the door | mint | mint | **write / transfer** |

**Eight cells; the fourteenth trip's fix and axis ten drove exactly one.** R91 rules the two trips are
closed in **ONE change**, **one mutation per cell** so no cell is left a survivor, with the commit
enumerating all eight and naming what it declines (R85, R88). **A3's fix is a separate change — it is a
different table.**

#### A3 and F5 are NOT trips — ruled, with their classes

- **A3 — the ninth trip's class at the ACTIONS surface. BLOCKING. Not a trip**, because the word resolves
  to **one** row: one word, one identity, **two governance answers**. It is the **mis-governed cell
  (`I-7`) reached in SHIPPED code for the first time**, and it mints **Q94** for the founder: *does the
  kill criterion extend to governance identity — one word answering with two policies — or is that a
  separate register?* **Supervisor's default until ruled: separate, recorded beside the trips and never
  folded into their count.**
- **F5 — the tenth trip's class and trip 4's shape. BLOCKING. Not a trip**, and the reason is worth
  keeping: **no second row is written** — the second `approve` raises rather than writing — so the store
  never ends holding two rows for one word. **Fail-closed by accident.** The async mirror stays
  `[Inferred]`, as the lens honestly recorded.

#### R90 — the cross-namespace record countersigned, and a correction to §6.1 that is the supervisor's own

R90 adopts §6.1's split of the fourteen-countersignature refrain and rules **not a fifteenth trip**: the
scoping holds, and the six findings are all in `_search_namespaces`, R6's cross-namespace **advisory**
read. **From here the register does not write that sentence in its old form again.**

**Two corrections this row records against itself:**

1. **§6.1 said 27 keyed comparisons in `registry.py`; the supervisor's grep gives 41 matching lines.**
   The difference is the grep's **shape** — §6.1 counted `same_word(`/`identity_key(` with the open
   paren, R90 counted the bare names and so caught docstring mentions too. **The fact is unchanged and
   reproduces either way: ZERO inside the one multi-namespace guard, against dozens everywhere else.**
   Recorded because a number this row published was not the number a reader re-running the obvious grep
   would get.
2. **R90 takes the supervisor's own share of §6.1's finding, and this row does not soften it.** R83
   quoted the refrain approvingly as *"the count's meaning"*, and R84–R88 rested on it. R90's words:
   *"a claim stated without its evidence is a detectable object, and this one sat undetected for fourteen
   rounds because everyone who repeated it, including the supervisor, mistook repetition for evidence."*

#### What is NOT yet countersigned — stated plainly, because R91 predates §6.4

**R91 countersigns `aa6d2e5` (§6.2) and `3126023` (§6.3). The kill row's record landed afterwards at
`85c9eb6` (§6.4), so its constructions are ROUTED AND UNRULED.** Two of them are new and neither
duplicates a countersigned trip:

| # | construction | why it is routed and not folded in |
|---|---|---|
| **K1** | **R80 / Q82 constructed** — 60 of 120 page orders swallow a non-overridable identity guard; **two ACTIVE rows answer to one word** and `resolve_type` answers at 1.0 on a pair refused `predicate_merge` non-overridably | It meets the identity criterion R91 states. It is **not** a cell of the 2×2×2 — its dimension is **page order**, which no cell of that table names. R80 ruled it goes first in this lens and gave two discharges; **the first was achieved**, so R80's second half does not apply |
| **K4** | a capability-degraded **skip** indistinguishable from a pass: refused non-overridably on one backend, written with `warnings=()` on another, `resolve_type` at 1.0 — on `indexes_membership=False`, **UC1 Tenshen's own declared shape** | Also meets the identity criterion. A **new sentence**: trips 1 and 9 asked whether *unknowable* equals *equal* or *different*; this asks whether *unknowable* equals **nothing to say** |

**The worker does not classify either.** They are reported to the supervisor with §6.4's evidence, and
the count is **SIXTEEN** until ruled otherwise. **[R92](../decisions/2026-09-04-6d-supervisor-ruling-R92.md) ruled: K1 is the SEVENTEENTH trip, K3 the EIGHTEENTH and K4 the NINETEENTH — see [§6.7](#67-countersigned--r92-the-count-is-nineteen).]**

#### The fix set this round owes, per R90 and R91 together

1. **ONE change over the 2×2×2** (R91) — all eight cells enumerated, **one mutation per cell**, nothing
   left a survivor. The two survivors round 1 measured are both inside this table: widening the trip-14
   scan to all kinds, and `match_aliases=True` at 7023.
2. **ONE change over `_search_namespaces`** (R90) — not six fixes in lens order. **The countable form of
   "done" is R90's own grep going from 0 to a number**, with each identity comparison it gains named
   against the finding it closes.
3. **A3's change is separate** (R91) — a different table.
4. **Both commits list what they DECLINED** (R88), and **enumerate the doors each rule binds** (R85).

### 6.7 COUNTERSIGNED — [R92](../decisions/2026-09-04-6d-supervisor-ruling-R92.md). **The count is NINETEEN.**

> **The trip count in this row is NINETEEN from here.** §6.6's *"the count is SIXTEEN"* records what was
> true when R91 was countersigned; this section is the next event, per §5.8.

**R92 countersigns the three constructions §6.4 routed and §6.6 flagged as unruled:**

| # | trip | the new sentence |
|---|---|---|
| **K1** | **SEVENTEENTH** | **a non-overridable identity guard's answer is a function of SORT ORDER.** 60 of 120 page orders swallow it. **R80's first discharge achieved** — Q82, the register's only carried-forward suspicion, is now a state |
| **K3** | **EIGHTEENTH** | **the FIFTH trip's operand, un-applied to a guard the THIRTEENTH's fix added.** `_alias_clash` did not exist when trip 5 closed *partial is not equal*, and its `why` was never wired. R92: *"a guard added later inherited the rule's exemption, not the rule"* — rule (d) by number, R84's clause in its purest form |
| **K4** | **NINETEENTH** | **`unknowable` treated as `nothing to say`, on UC1's own declared shape.** Trips 1 and 9 asked whether *unknowable* equals *equal* or *different*; **this asks whether it equals *nothing to say*, and the shipped answer is yes** |

**R92 accepts §6.4's escalation of K3 from the fix auditor's MAJOR to BLOCKING** — *F3 showed the caller
cannot tell; K3 shows what it costs* — and records the acknowledgement caveat on K1 without letting it
change the classification: the merge door requires acknowledgements on the **specified** path (they are
not `force`), and **the escape under test needs none**.

**Round 1 produced FIVE trips — the fifteenth through the nineteenth, more than any round in this
register's history.** R92 states the three facts that sit beside that without softening it: every one was
reached on **shipped code no build row had changed** (`git diff --stat d4b86a8 HEAD -- ontoloche/` is
empty); **four of five were predicted before the lens ran** — T14, T11, S2, T1 — and the fifth, K3, is
T5's cell reached one guard further than T5 named; and **they cost one round of a row with no diff of its
own**, where the alternative was the next four build rows each paying for the cells they happened to
touch, as trips 8/12/13/14 were paid for.

#### The reconciliation R92 asked for — **§6.4's gate reason for K4 was imprecise, and the correct one is sharper**

**What §6.4 published:** *"`_legs()` builds `sqlite`, `sqlite_minimal` and optional Postgres;
`DegradedAdapter(indexes_membership=False)` appears **0** times as a leg."*

**The supervisor counted the string `indexes_membership=False` **4** times. Here is what those four are
[Observed, `docs/tools/check_merge_guard.py` at `eddb017`]:**

| line | what it is | live or prose |
|---|---|---|
| **12** | module docstring, narrating the FIRST trip (`0e89037`, row 3c) | **prose** |
| **66** | the docstring's extent-state table — the row `unknowable \| indexes_membership=False \| REFUSED` | **prose** |
| **904** | Part B's **extent-state** axis: `("unknowable", lambda a: DegradedAdapter(a, indexes_membership=False))`, driven for every caller in `PROBES` over `_both(registry, ["note"], ["doc"])` | **LIVE — drives the EXTENT operand, refusal #2** |
| **1241** | the **staleness** axis: `("stale (unknowable)", lambda a: DegradedAdapter(a, indexes_membership=False), False)`, driven for every caller in `STALE_PROBES` | **LIVE — drives the staleness comparison** |

**The verdict on the published sentence, stated against this row.** It is **narrowly true**: `_legs()`
yields `("sqlite", …, True)`, `("sqlite_minimal", …, False)` and optionally `("postgres", …, True)`, and
**0 of the file's 13 `DegradedAdapter` occurrences are legs**. But it was **misleading as a gate reason**,
because a reader takes *"appears 0 times as a leg"* to mean *the gate never drives this adapter* — and it
does, at two axes. **The sentence should not have been published in that form.**

**The correct reason is stronger than the one it replaces, and it is countable:**

> **The degraded adapter IS driven — at the extent-state axis and at the staleness axis. It is never
> driven at the ONE axis that drives the guard K4 skips.** Refusal #1 is exercised only by the
> **CONSUMER-SET axis** — axis seven, added by the ELEVENTH trip precisely because refusal #1 had been
> unfalsifiable — and **[Observed]** that axis (lines 1815–2117) contains **0** of the file's **13**
> `DegradedAdapter` occurrences: it iterates `_legs()` and wraps nothing. **So refusal #1 has never been
> driven degraded, on any leg, in any axis, since the axis was built.**

**That is the ELEVENTH trip's own indictment recurring in a new dress.** Then it was countable as *zero
occurrences of `register_consumer`*, which made refusal #1 a guard the checker could not fail on. Now it
is *zero degradation on the only axis that drives it* — the axis built to end that exact problem,
exercising the guard on capable backends alone. **A gate that added an axis to make a guard falsifiable,
and then drove that axis only where the guard is never skipped.**

#### §0.7 updated, per R92 — the trip number recorded beside each prediction it named in advance

| # | prediction | outcome, as scored after R91 and R92 |
|---|---|---|
| **S2** | the `C10-20` page-order escape (Q82 / R80) | **CONFIRMED BY CONSTRUCTION — the SEVENTEENTH trip.** Falsifier FALSE: refuses in 60 of 120 orders, not in every one. **R80's first discharge achieved; its second half does not apply** |
| **T1** | capability-degraded skip = pass | **CONFIRMED BY CONSTRUCTION — the NINETEENTH trip.** Falsifier FALSE: K4 neither refuses nor emits a warning naming the skip |
| **T5** | `clash_why` / `_variant_why` dropped at two of six sites | **CONFIRMED BY CONSTRUCTION — the EIGHTEENTH trip** (the `clash_why` half; the `_variant_why` half is F2, MAJOR and open). §0 named **both** lines — 4429 and 4769 — before either lens existed |
| **T14** | the 2×2 is a 2×2×2 with `kind` as the third axis | **CONFIRMED BY CONSTRUCTION, BEFORE ANY FIX — the FIFTEENTH trip** (R91) |
| **T11** | `match_aliases` defaulted to the trip-14 answer | **CONFIRMED BY CONSTRUCTION, BEFORE ANY FIX — the SIXTEENTH trip** (R91), named by line at `registry.py:7023` |

**Four of the five trips this round were named in §0 before any lens ran.** The fifth, the eighteenth, is
**T5's cell reached one guard further than T5 named** — §0 predicted the dropped `why`, and the lens
carried it to the collapse.

**Running score, unchanged in its totals: 21 CONFIRMED · 3 PARTIAL · 1 FALSIFIED · 5 NOT REACHED.**

#### What R92 adopts from §6.5, and one thing it singles out

R92 adopts §6.5's table and singles out the **adjudications made against the row** as the reason it can be
trusted — T7 falsified, T3's harm at D6 falsified, T12 half-falsified — and the one made **for** the row
over a lens's objection, **S4 CONFIRMED**, with the standard stated: *overruling a lens on evidence and
keeping the overruled negative on the record.*

**K7 is noted so it is not lost under the trips:** the round's **one unpredicted finding**, found twice
independently. Not a trip (a raise, not a second row), MAJOR, rule (d) by number.

#### The fix set, as R92 fixes it — **THREE changes, not one and not nineteen**

| # | change | closes | the countable form of "done" |
|---|---|---|---|
| **1** | **the 2×2×2** | 15th, 16th, and K6's cross-kind cell | all **eight** cells enumerated, **one mutation per cell**, no cell left a survivor |
| **2** | **page order + truncation, together** | 17th, 18th | `_alias_clash` returns the **SET** or answers **`unknowable`**, and its `why` is **consumed at every caller**; the gate gains a **page-order axis**, every fixture driven in at least two orders — **the `reversed(\|shuffle\|permutations` grep goes from 0 to a number** |
| **3** | **the capability-degraded skip** | 19th | a skipped guard **emits a stated warning naming the skip** (T1's own falsifier); the gate gains **`DegradedAdapter` as a leg** |

**Separate, and named as such:** **A3** (R91 — a different table), **`_search_namespaces`** (R90 — one
change, measured by R90's own grep going from 0 to a number). **K7 and F5 travel with whichever change
touches their door, each named.** Every fix commit **enumerates the doors its rule binds** (R85) **and
lists what it DECLINED** (R88).

### 6.8 ROUND 2 — **PRE-REGISTERED PREDICTIONS, committed before any lens is dispatched**

> **The ordering is the row's whole point and it is checkable in `git log`:** this section lands
> before round 2's first lens exists. §0 did it for the surface; this does it for **the fix set**,
> which is the harder case — *the next defect lives in the last fix* is this register's
> most-counted sentence, and the last fix is now mine.

**The five commits under audit**, and every one of them is this row's own:

| commit | what it changed |
|---|---|
| **`9a4e140`** | the 2×2×2 — `_retired_holder`, the kind-blind mint scans, `word_held_by_tombstone`, axis 11 |
| **`f8992f3`** | page order + truncation — `_alias_clash` returns the SET, `merge_warnings`, `OrderedAdapter`, axis 12 |
| **`a446b89`** | the degraded skip — `skipped` accumulators, `identity_guard_skipped`, the `sqlite_degraded` LEG, axis 13 |
| **`304967a`** | A3 — `_action_declarations_diverge` at three collapse doors, `action_declarations_diverge` |
| **`9d2f203`** | the cross-namespace read — `_answers_to`, the keyed rejections query, guard #4 moved first, `import_field_ignored` |

**And the harness is under audit with them.** A gate is an artefact and takes the same rule as the
probes it runs: **axes 11, 12 and 13, and the `sqlite_degraded` leg**, are as much this row's diff
as `registry.py` is. Every one of them was written by the person who wrote the fix it checks.

#### KNOWN OPEN before the round starts — stated as facts, NOT scored as predictions

*Recording these as predictions would be scoring a confirmation. They are [Observed] now, and the
round's job is to find what is **not** on this list.*

1. **F2 bound no commit, and it is R88's own failure mode inside this row.** §6.3 ACCEPTED F2 —
   `import_types`' name door discards `_variant_why` while `propose_type` and `_write_approved`
   fold theirs in — and change 1 **declined** it into change 2. Change 2's subject was
   `_alias_clash`'s `why`; F2 is `_word_rows`' `why`, a different scan. **[Observed]**
   `registry.py:5108` still reads `variants, _variant_why = self._word_rows(...)`. *A fix commit
   lists what it declined, or a later round finds it and counts it* — and the later round is this
   one, on a decline this row wrote down and then did not carry.
2. **G1 and G2 are open by declaration.** `check_merge_guard.py` still holds **zero**
   `cross_namespace` fixtures and **zero** `kind="action"` fixtures; both were named as declined
   in the commits that could have closed them.
3. **Cells 3 and 4 of the 2×2×2** remain declined — **Q95**, the founder's.
4. **X4's keying half** remains declined — **Q96**. **R79's flat-form half** is ruled and unbuilt.

#### The predictions — **R2-P1 … R2-P10**, each with the falsifier stated in advance

| # | prediction | why | falsifier |
|---|---|---|---|
| **R2-P1** | **The round will NOT be clean. At least one BLOCKING.** | Seven rows of this register have run this loop and **not one closed clean**. Round 1 here went 8 BLOCKING across 19 distinct findings. A clean round immediately after five fix commits would be evidence about the lenses, not about the fixes. | any lens returning NOT YET |
| **R2-P2** | **The fix auditor finds the most, and its findings cite the five commits.** | The register's counted policy, right for seven rows running: 3e 4-of-10, #4 round 3 2-of-4, 4d round 2 five inside round 1's fixes, 6b round 2 the tenth trip inside the ninth's fix, 6c round 3 **every** finding inside a fix of that row, 7a rounds 2 and 3. | which lens has the highest BLOCKING count, and whether its findings cite `9a4e140`…`9d2f203` |
| **R2-P3** | **A skip note or a `why` is collected and then LOST on a refusal path.** `retire_skips` is surfaced at exactly one place — **[Observed]** `registry.py:3781`, inside the success return — and `merge_warnings` only reaches a `MergeResult`. So a guard skipped on a call that then refuses for another reason says **nothing**. | This is the EIGHTEENTH trip's own shape (a signal collected and not read) applied to the fix for the NINETEENTH. Three changes added accumulators; none of them audited the refusal paths. | a probe showing every accumulator reaches the caller on both the success and the refusal path, at all four doors |
| **R2-P4** | **`_action_declarations_diverge` compares `effects` by equality, and equality of a LIST is order-sensitive.** Two families declaring the same effects in a different order will be refused `action_declarations_diverge` — a false refusal that closes a legal merge. | `C10-09`, `C12-09`, `C12-15` and `C16-07` exist because a fix that closes a legal operation is worse than the defect. A3's own narrowing (`C19-99`) pins only the case where the four keys are byte-identical. | a probe showing two families whose `effects` differ only in order still merge |
| **R2-P5** | **The three new axes contain at least one fixture that cannot build its own subject** — and therefore reports `held` while a reverted guard survives. | This row has hit that class **four times already**: C9-36 and C10-21 vacuous (change 1), axis 12 decorative on its first cut (change 2), axis 13 passing for the wrong reason on its first cut (change 3). Four for four is not a run of bad luck; it is what writing a fixture against your own fix does. | a mutation run over every row of axes 11, 12 and 13 with no survivors |
| **R2-P6** | **`merge_types` now performs three full namespace scans per call** — `_identity_breach`, `_alias_clash` and `_retired_holder` — and **nobody measured the cost.** | `_word_spellings`' own docstring records the last time this register shipped a per-call scan without measuring: 64,840 records and 1.56 s for twenty import rows. Row 6b measured 200,020 row reads for twenty returned rows. **No commit in this row's fix set carries a measurement.** | a measurement showing the added scans are bounded and stated |
| **R2-P7** | **The `sqlite_degraded` leg is 89 rows of NOT REACHABLE and at least one of them is wrong** — a row reported unreachable that is in fact reachable, or reachable and silently uninteresting. | A leg added late is a leg every existing axis meets for the first time, and `NOT REACHABLE` is the verdict this file uses when a fixture cannot be built. R12's rule is that a coverage line is part of the claim; 89 unexamined coverage lines is a claim nobody read. | every `sqlite_degraded` NOT REACHABLE line shown to name a real capability the fixture needs |
| **R2-P8** | **A detail field is still page-order dependent even though the verdict is not.** Change 2 made `merge_types`' escape read the whole SET, and `reinstate` reports `held_by_all` — but `import_types` still reports `clashes[0]`. | The SEVENTEENTH trip was a verdict that depended on page order; a DETAIL that depends on it is the same defect one field along, and this row fixed the verdict at three doors and the detail at one. | every door's refusal detail shown to be stable across page orders |
| **R2-P9** | **`identity_guard_skipped` is pinned for ENTITIES only.** Axis 13's `_skip_pair` uses entities deliberately — a predicate pair is refused by #2 first — so the predicate path of the same skip is asserted by nothing. | This is axis 13's own recorded reasoning, and it means the note is proved at one kind of two. *A rule minted at the caller that prompted it* is standing rule (d); *a rule proved at one kind of two* is the same sentence one dimension along. | a probe showing the skip note reaches the caller on a predicate pair too, or an argument that it cannot arise there |
| **R2-P10** | **At least one finding will be UNPREDICTED by this table**, and it will be in the harness rather than in `registry.py`. | Round 1's one unpredicted finding (`AmbiguousKind` at the §4.1-blessed store) was found twice and named by no §0 prediction. This round's diff is half harness by line count, and a harness is the artefact this row has been least careful with — four fixture defects in five changes. | every round-2 finding mapping onto R2-P1…R2-P9 or onto the known-open list |

#### What would falsify the ROW's reading rather than confirm it

1. **If the round comes back clean**, that is not a victory — it is evidence the lenses were pointed
   where the fixes already looked, and the convergence note must say so. §0.6 said this before round
   1 and it is repeated because the temptation is larger now that five commits have landed.
2. **If every finding is in `registry.py` and none in the gate**, the harness audit was not real.
   The supervisor's instruction is explicit — *a harness is an artefact and takes the same rule as
   the probes it runs* — and this row's own record is four fixture defects in five changes.
3. **A shrinking finding count is the weakest signal this register has** (row #4's round 3). Round 2
   finding fewer than round 1's nineteen is not convergence and will not be reported as such.


---

## 7. The fix set

*Three changes, as ruling [R92](../decisions/2026-09-04-6d-supervisor-ruling-R92.md) fixed them.
Each lands as its own commit, enumerating the doors its rule binds (R85) and listing what it
declined (R88), with all three legs green before it is pushed.*

| # | change | closes | commit |
|---|---|---|---|
| **1** | **the 2×2×2** | the FIFTEENTH and SIXTEENTH trips, and K6's cross-kind cell | **`9a4e140`** — 373 ids, `Refusal.reason` 31 → 32, axis 10 → 11, six mutations and no survivors; three legs **1741 passed / 566 skipped / 0 failed**, exit 0 |
| **2** | page order + truncation | the SEVENTEENTH and EIGHTEENTH trips | **`f8992f3`** — the page-order grep 0 → 2, axis 12, ids 375 |
| **3** | the capability-degraded skip | the NINETEENTH trip | **`a446b89`** — `identity_guard_skipped`, axis 13, `sqlite_degraded` as a LEG, ids 377 |
| **4** | **A3**, separate per R91 | the declaration operand refusal #2 never had | **`304967a`** — at all THREE collapse doors; my own §6.2 narrowing was wrong, ids 380 |
| **5** | **`_search_namespaces`**, separate per R90 | X1–X6 | **`9d2f203`** — the identity grep 0 → 6, ids 383 |

**Separate, and named as such:** **A3** (governance identity — a different table, R91),
**`_search_namespaces`** (R90, one change measured by R90's own grep going from 0 to a number).
**K7 and F5** travel with whichever change touches their door.

---

## 8. Questions this row raises — **Q95 onward**

*R1–R92 exist; Q94 was minted by R91. The next question number is **Q96**.*

### Q95 — does the tombstone-word rule bind a tombstone's own NAME at the TRANSFER doors, and if it does, what happens to `C12-09`?

**Raised by change 1 (`9a4e140`), which declined two of the eight cells rather than take them.**

**The question.** Ruling **R91** named the 2×2×2 and change 1 closed six of its eight cells. The two
it did not close are the pair where the word arrives as a **NAME** at a **transfer** door:

| cell | the state |
|---|---|
| **3** | a tombstone whose own **name** is a word `merge_types` or `retire(successor=)` is about to move onto a live row, **same kind** |
| **4** | the same, **across kinds** |

**Why they were declined rather than closed, and it is not a scope fence but a collision with a
pinned ruling.** Change 1's guard asks about a tombstone's **aliases** and deliberately not about
its **name**, because *a retired row's own name written as an alias onto another row is the ordinary
post-retirement succession that **`C12-09` blesses** when the two extents agree.* **[Observed]** `PACKAGE.md` §6.2's row for
`C12-09` reads, verbatim: *"**and an imported alias between two identical non-empty extents is
still written** — the half a careless fix deletes. §5.10 refusal #2 permits that collapse
(`C10-09` narrowed the guard rather than closing the operation), so a fix that refused every
predicate alias would pass a suite asserting only refusals while removing a legal write."*
**That last clause is this question in advance.** Closing cells 3 and 4 with the same rule that closes 5–8 would
**reverse that narrowing**, and the register's own history says a fix that closes a legal operation
is worse than the defect it closes.

**The evidence that made it a question rather than a judgement.** The gate found it, not a reading:
change 1's first cut *did* bind the name half, and `check_merge_guard.py` went red on
`import_types known-equal` within one run — the one extent state `C12-09` is about. **A guard whose
first cut reddens the id that pins a deliberate narrowing is telling you the narrowing is the
subject, not the collateral.**

**The three answers, with the cost of each:**

1. **Leave it as change 1 shipped it — the rule binds ALIASES only.** `C12-09` stands untouched. The
   residual is real and is stated: a tombstone whose own **name** is moved onto a live row by
   `merge_types` or `retire(successor=)` is left un-reinstatable, and no door says so. That is the
   fifteenth and sixteenth trips' own harm reached through the one field the rule does not cover.
2. **Bind the name half too, and narrow `C12-09`** to *"…may still be aliased **when no tombstone
   answers to the word**"*. Closes the residual; changes what a pinned id asserts, which is a ruling
   and not a fix.
3. **Bind the name half and let the succession path move**, so the blessed act becomes `reinstate`
   → `merge_types` → `retire` rather than a direct alias write. Closes the residual without
   narrowing `C12-09`'s claim, at the cost of a three-call path where callers have one — which is
   the shape the twelfth trip's own correction had to make for `successor_active`.

**The worker's default, which is what shipped: (1).** A row that closes a cell by reversing a
narrowing another row pinned on purpose is doing the thing standing rule (d) exists to prevent, one
ruling along — and **this row does not get to overturn `C12-09` by fixing something else.**

**[Observed]** the residual is not hypothetical: `_retired_holder`'s docstring states the cut, and
`check_merge_guard.py`'s axis 11 drives the six closed cells and **not** cells 3 and 4, so the gate
records the gap rather than hiding it.

**Q95 IS THE FOUNDER'S, and the worker's first routing of it was wrong.** This row filed it as the
supervisor's *"on its face — a narrowing of a contract id, not a change to a shipped guarantee"*.
The supervisor corrected that, and the correction is recorded here rather than edited over:

> **Reversing `C12-09`'s narrowing changes what the registry DECLINES TO SERVE, which is the Q56
> class and the founder's decision.** `C12-09` is not a test's private business — it pins an
> operation a caller may legally perform, and narrowing it removes a write that works today.

**The worker's decline is the default in force**, and Q95 **rides with Q94 in the founder item** —
one decision, not two, exactly as R92 folded the twelfth and thirteenth `stop` puts together.

**The general lesson this row takes from being corrected**, because it is the same shape the row has
been finding all round: *whether a question belongs to the supervisor or to the founder is decided by
what changes if it is answered, not by which artefact the change lands in.* A contract id looks like
a test and `C12-09` is a guarantee wearing one.

