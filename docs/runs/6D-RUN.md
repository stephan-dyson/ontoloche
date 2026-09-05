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

