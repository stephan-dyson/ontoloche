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
countersigns otherwise; classification is not this worker's (R83).

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

*Written as each lens returns, before any fix, per constraint 7. Nothing here yet: this file's first
commit contains §0 and nothing else, which is the ordering R89 opened this row for.*
