# 6H-RUN — A GATE FOR RESULT-CONDITIONED SKIPS. THE SUITE CANNOT TELL COVERAGE FROM ABSENCE.

Opened by the ontoloche fleet supervisor's brief `2026-09-09-oo-skip-census-followon.md`, with its
AMENDMENT of 21:20 and the supervisor's answers of 21:25 folded in.
Worker: row 6h (Opus). Supervisor: ontoloche fleet supervisor, tmux `fleet-supervisor-ontoloche`, pane `%2`.

**The finding this row is built on, in the brief's own words.** *A skip decided by the ENVIRONMENT is
legitimate. A skip decided by the RESULT is never legitimate, because the result is the thing under test.*
Three instances are known — `C3-14` (row 4d, by mutation), `C10-16` (row 6f round 1) and `C3-26`, **written
by row 6f in the very round whose finding `F1` was this exact shape.** All three are fixed. What is not
fixed is the mechanism: **the suite treats a skip as coverage and cannot tell the two kinds apart**, and no
local edit removes that.

**What this row is NOT.** It is not row 6f and not row 6g. It is **not kill-row shaped and must not be
routed there** — nothing here merges a capability predicate or collapses two words onto one identity. Suite
integrity is not meaning destruction. **The kill-row count stays TWENTY-THREE**, and a build row is not a
trip. It does not touch `Q101` or per-key severity, which are the founder's and are open.

---

## §0 — PRE-REGISTRATION

**This section is committed BEFORE any census is run, before any file under `ontoloche/contract/` is
opened, and before a line of the checker is written.** `git log` is the only artefact that can prove that
ordering, because a pre-registration and a post-hoc rationalisation are textually identical. **If the
commit landing this section is not an ancestor of every commit that follows in this file's history,
everything below is decoration and this row's numbers should be read as tuned to their result.**

The supervisor's instruction on the number, taken verbatim rather than paraphrased:

> *A range wide enough to be safe is not a falsifier, and a pre-registration that cannot be wrong is
> decoration. Commit a single integer, and commit the reasoning that produced it in the same file, so that
> when the census disagrees a reader can see which step of the reasoning was wrong rather than just that
> the number was.*

§0.5 commits the integer. §0.5b commits what would falsify the model behind it.

### §0.1 — Prior exposure, disclosed

A pre-registration that hides what its author had already read is not one. Before writing this section I
had read, in this order and no more:

1. My brief, in full, **including the AMENDMENT sections A through E**.
2. The supervisor's answers file, `2026-09-09-oo-6h-supervisor-answers-1.md`, in full.
3. [`6G-RUN.md`](6G-RUN.md) — its title block, **§0 entire** (which this section is modelled on), §1.0 and
   §1.1's fixture-defect table. **I have not read its §2 or anything after it.**
4. [`docs/README.md`](../README.md) — the run-index rows only, surfaced by `grep -n "RUN"`. Those rows are
   dense summaries, so I have secondhand exposure to the headline results of rows 2a, 3d, 3e, 4b, 4c, 4d,
   6b, 6c, 6d, 6e, 6f, 6g and 7a, and to `R101`.
5. Directory listings (`tools/`, `docs/`, `docs/tools/`, `docs/runs/`, `ontoloche/`) and two file counts:
   **29 `.py` files in `ontoloche/contract/`** and **29 in `ontoloche/aio/contract/`**.
6. The module docstring of [`tools/unasync.py`](../../tools/unasync.py), first 30 lines, which establishes
   that **the sync tree is the single source of truth and `ontoloche/aio/` is generated from it**.

**I have NOT read, at the time of this commit:** any file under `ontoloche/contract/` or
`ontoloche/aio/contract/`; the body of any of the four gate scripts; `ontoloche/registry.py`; any spec;
any founder ruling; `STATUS.md`; `ROADMAP.md`; the governance register. **I have run no census and no
grep over `pytest.skip`.** Every figure in §0 that is not mine is the supervisor's, and is marked so.

**Inherited figures, at `e548541`, measured by the supervisor and NOT by me:** **121** bare `pytest.skip(`
call sites across **13** files in `ontoloche/contract/`, against **223** `requires_capability` markers
across **23** files. Re-derived by me in §1 with my own command, and **if my number differs, that
difference is a finding about the instrument and is published as one, not reconciled quietly.**

### §0.2 — The state space, fixed here, because a checker without one is a preference

Every bare `pytest.skip(` call site in `ontoloche/contract/` lands in exactly one of these cells with
respect to **what its guard reads**. The partition is fixed now and is not revisable after the census
begins.

| cell | the guard reads | example shape | verdict |
|---|---|---|---|
| **S0 — ENVIRONMENT** | a capability flag, a backend identity, an import, an env var — a fact about the CONFIGURATION, known before the call under test runs | `if not registry.caps.indexes_membership: skip(...)` | **legitimate**, but belongs on the audited `requires_capability` marker rather than the unaudited path |
| **S1 — SETUP RESULT** | a value returned by a call the test makes to BUILD its fixture, whose failure means the scenario cannot exist on this backend | `if isinstance(gone, Refusal): skip("this backend cannot retire the holder")` | ***probably* legitimate.** A fixture that cannot be BUILT has nothing to assert. **NOT this row's to rule** |
| **S2 — RESULT UNDER TEST** | a value produced by the call this test's assertions are about | `if unscored.confidence is not None: skip(...)` — the fixed `C3-26` | **never legitimate.** The result is the thing under test |
| **S3 — UNCONDITIONAL** | nothing; the skip is not guarded at all | a bare `pytest.skip("not implemented")` at the top of a body | **named here so it cannot be absorbed into another cell by accident** |
| **S4 — UNCLASSIFIABLE** | something this partition does not name | *unknown at the time of this commit* | **the cell that falsifies the model.** See §0.5b |

**S4 exists because the model is the supervisor's starting point and has already been wrong once.** The
original two-way rule — environment versus result — was applied by the supervisor to five real sites and
was **wrong about three of them**, which is how S1 came to exist at all. That correction was found by
RUNNING the rule, not by re-reading it. **A model that has been wrong once gets a cell for being wrong
again**, and populating S4 is a result, not a failure of the census.

**S1 is the cell this row is most likely to get wrong**, and I am **not authorised to fix anything in it**.
Per the supervisor's answers: *a wrong call there silently deletes real coverage or blesses a fake
assertion.* What I owe on S1 is **the shape and the count**, routed.

### §0.3 — The discriminator, fixed here and not revisable after the census begins

The brief's own sentence is explicit that it is a starting point and not a ruling:

> *A skip is illegitimate when its guard reads a value produced by the call the test's **assertions** are
> about — which means the checker needs to know which call that is, not merely that a result was read.*

**That is not mechanical as written, so this section makes it mechanical, and names what it would take to
show the mechanisation is wrong.**

**D1 — the discriminator this row will implement, stated so it can be attacked.** Working on the AST of a
single test function:

> A bare `pytest.skip(...)` is **S2 (illegitimate)** when the guard controlling it reads a name whose value
> is **also read, transitively, by an `assert` statement in the same test function**. It is **S1** when the
> guard reads a call result that **no `assert` in that function ever reads**. It is **S0** when the guard
> reads no call result at all.

**Why this and not something simpler.** "The guard reads a result" flags S1 and S2 alike and would have
been wrong about three of the supervisor's five. **What separates them is not where the value came from,
it is whether the test goes on to assert about it.** A fixture the test only builds with is not the thing
under test; a value the test asserts about is, by definition, the thing under test. **D1 is the brief's own
sentence with "the call the assertions are about" replaced by something a parser can see.**

**D1's calibration set, fixed now, and the checker is not accepted until it reproduces every cell:**

| site | required D1 verdict | why it is in the set |
|---|---|---|
| `C3-26`, **in its pre-fix form**, recovered from git history | **S2** | the shape the row exists to catch |
| `C3-14`, pre-fix, recovered from git history | **S2** | found by mutation in row 4d |
| `C10-16`, pre-fix, recovered from git history | **S2** | found by row 6f round 1 |
| the supervisor's `if isinstance(gone, Refusal): skip(...)` site | **S1** | the middle category, which D1 must NOT flag |
| the supervisor's `if not registry.caps.indexes_membership: skip(...)` site | **S0** | the legitimate environment shape |

**A checker that cannot reproduce all five is not shipped**, and if D1 fails any of them the failure is
published in this document with the shape that broke it, **before** D1 is amended. **Amending D1 after
seeing a case it gets wrong is legitimate and is exactly what §0.5b's falsifier is for; amending it
silently is the defect this row exists to gate.**

**D1's known exposure, written down before it is run rather than discovered defensively.** Two shapes I
expect to be hard: **(a)** a value used to build a fixture AND asserted about later — genuinely both S1 and
S2 by D1's reading, which is an S4 candidate; **(b)** `pytest.skip` reached through a helper function, where
the guard and the skip are in different frames and no single-function AST walk sees both.

### §0.4 — The measurement this row owes, its method fixed BEFORE it is taken

The supervisor named the number he will judge the gate on: **how many currently-passing ids the gate flags,
split by the three categories.** That is the measurement, and its method is fixed here.

**The counting command, stated in advance so the number can be attacked** — the amendment requires this,
because *a census whose own instrument is unverified is the exact defect this row exists to gate*:

```
grep -rn --include='*.py' 'pytest\.skip(' ontoloche/contract/ | grep -v __pycache__
```

**And it is run a second way, by the checker's own AST parse, and the two numbers are published side by
side.** They measure different things — grep sees text, the AST sees calls — and **a discrepancy is a
finding about the instrument, published as one.** The supervisor's own figure moved 114 → 113 for exactly
this class of error, and his `requires_capability` count was polluted by 53 `__pycache__` binaries until he
noticed the file count was impossible.

**Scope, fixed:** `ontoloche/contract/` only. `ontoloche/aio/contract/` is **generated** from it by
`tools/unasync.py`, so gating the mirror would gate a derivative; its number is **reported** in §1 and not
gated, and the reason is stated there rather than left implicit.

**What is published, per cell of §0.2:** the count, and for **S2 and S4 every site BY NAME** — file,
enclosing test function, and the guard's text. S0 and S1 are published as counts with a representative
sample, because naming 100+ legitimate sites is noise that hides the ones that matter.

**The id-level number:** for every S2 site, the contract id whose test contains it, so that *"how many
currently-passing ids this would break"* is answered in ids and not only in call sites. **One id may hold
more than one site and one site may serve more than one id; both numbers are published and neither is
presented as the other.**

### §0.5 — THE PREDICTION. ONE INTEGER, WITH THE REASONING EXPOSED

**I predict the census finds `9` sites in cell S2.**

**This is a guess made from having read zero test files.** It is derived from roughly fifteen minutes of
not reading the tests, as follows, and each step is a place the reasoning can be shown wrong:

1. **121** bare skip sites is the supervisor's figure at `e548541`; I take it as given for the prediction
   and re-derive it in §1.
2. **I guess ~85 of them are S0.** This project runs a multi-backend suite with capability degradation as
   a first-class idiom — `DegradedAdapter`, a capability matrix with **223** markers, a whole gate that
   tallies passed/skipped/failed per configuration. **The dominant reason to skip in this suite is that a
   backend cannot do the thing**, and that is an environment fact.
3. **That leaves ~36 sites whose guard reads a value a call returned.**
4. **I guess two thirds of those, ~24, are S1** — the `isinstance(gone, Refusal)` shape. A suite whose API
   returns `Refusal` objects rather than raising will build fixtures through calls that can refuse, and a
   test that cannot build its scenario has nothing to assert. **This is the shape that made the two-way
   rule wrong about three of five.**
5. **That leaves ~12 in S2.** Three are already known and already fixed (`C3-14`, `C10-16`, `C3-26`), so
   they will not appear.
6. **12 − 3 = 9.**

**Where I expect this to be wrong, said now rather than after.** Step 2 is the weakest: if this suite
skips on environment through `requires_capability` markers *by preference* — which is what 223 markers
suggests — then the 121 bare sites are **disproportionately** the cases that could not be expressed as a
marker, which is exactly the population enriched in S1 and S2. **If that is true, 85 is far too high and
the S2 count is far above 9.** I am predicting the low number anyway, because I would rather be wrong in
the direction that makes the finding bigger than shade the number toward a safe middle.

**The eight-versus-two drift is the reason I do not predict a small number confidently.** While this row sat
queued, the unaudited surface grew by **eight** and the audited one by **two** — written by rows 6f and 6g,
**both running adversarial lenses specifically looking for weak assertions.** A suite that adds unaudited
skips faster than audited ones while careful rows watch is not a suite where 9 is obviously the right order
of magnitude.

**The miss is recorded when the census lands** — predicted, actual, and **what the gap says about the
model**, per the supervisor's instruction: *if you predicted 12 and find 40, the interesting finding is not
the 40, it is what you did not know about the suite that made you say 12.*

**Secondary predictions, recorded so that finding them cannot later be described as obvious:**

> **P2 — D1 flags at least one site the author would defend, and defending it will be the row's hardest
> paragraph.** **Falsifier:** every S2 site is unambiguous on sight. **Why it matters:** a checker whose
> false positives are invisible from the inside is the specific exposure amendment B names for this row.

> **P3 — the grep count and the AST count DISAGREE.** Reasons available: a multi-line call, a `skip` imported
> as a bare name, a string or comment containing the text, a `skip` inside a helper. **Falsifier:** they
> match exactly. **Why it is predicted:** the supervisor's own count moved twice for this class of reason,
> and this row's entire premise is that unverified instruments are the defect.

> **P4 — S3 (unconditional skip) is non-empty, and at least one such site is an id that reads as coverage
> and asserts nothing at all.** **Falsifier:** every bare skip in the suite is guarded.

### §0.5b — What would make me conclude the THREE-CATEGORY MODEL IS WRONG

The supervisor's requirement, and the model is his: *if the split does not fall into three categories, say
so — it is a starting point and it has already been wrong once.* Fixed thresholds, so this cannot be
decided by how attached I am to the model when the numbers land:

1. **The model is WRONG if S4 holds five or more sites** — five sites that need a category this partition
   does not name is a partition that does not describe the suite.
2. **The model is WRONG if D1's S1/S2 boundary is UNDECIDABLE for 20% or more of the result-reading sites**
   (S1 + S2 + S4 as the denominator) — because the middle category is then not a category, it is a place
   where the checker cannot see, and a gate built on it would be flagging by coin-flip.
3. **The model is WRONG if D1 misclassifies any member of §0.3's five-site calibration set** and the
   misclassification cannot be fixed without making D1 flag one of the other four.

**If any of the three trips, I report the model as wrong, bring the supervisor the shape, and DO NOT bend
the census to fit it.** The gate can still land on the cells that survive; what it cannot do is present a
partition that failed as one that held.

### §0.5c — What I do if the number is LARGE

Fixed here, because that is the moment the temptation to narrow the rule arrives — and section E already
rules on it in advance: ***if the gate would fail existing tests, do not weaken the gate to make them
pass.***

**Large is defined now, so it is not defined by the number: S2 exceeding `25` sites is LARGE.**

What happens then, in order, and **none of the steps is "narrow D1"**:

1. Every S2 site is published in this document **by name**, with what its test was asserting.
2. The count of currently-passing **ids** affected is published beside it.
3. The number and the shape are **ROUTED to the supervisor**, and the row does not proceed on its own
   judgement that the cost is acceptable.
4. **The ratchet still lands at the true baseline.** A large backlog is what the ratchet is FOR — it blocks
   the leak on the commit it lands and leaves the backlog as a separate, schedulable problem. **A large
   number is not a reason to relax D1, and if I find myself writing an argument for relaxing it, I stop and
   route instead.**

### §0.6 — THE GATE'S SHAPE AND ITS PASS CONDITION, fixed BEFORE a line of it is written

**The supervisor corrected his own brief on this point and the correction is the operative instruction:**
section D said a fifth gate joins the set from the commit that adds it, which *"was written without
thinking through the case where the gate fails on landing."* **The gate lands as a RATCHET — not as a
reporter, and not as a blocker.**

Three things it must do from the commit that adds it:

1. **Record a BASELINE of currently-flagged sites, checked into the repo as DATA, not prose.**
2. **FAIL when the count RISES above that baseline.** New violations are blocked from day one.
3. **FAIL when the baseline in the repo does not match what the checker counts** — so nobody can quietly
   raise the baseline without the diff showing it.

**The baseline may only ever go DOWN. Lowering it is a normal commit anyone may make. Raising it requires
the supervisor's ruling.**

**Why not the two obvious shapes, in the supervisor's own reasoning:** *a checker that reports and exits 0
is the exact defect this row exists to kill* — it would read as coverage and assert nothing, `F1`'s own
sentence applied to the instrument instead of the tests. *A checker that blocks on all 121 sites forces
exactly one outcome: someone weakens it until it passes*, which section E forbids, leaving no legal move.

**Design decisions fixed here rather than during implementation:**

- **The baseline is a LIST of site identities, not a bare integer.** A bare count lets one violation be
  fixed and another added with the count unchanged, and **a ratchet that does not bite on a swap is not a
  ratchet.** Identity is `(file, enclosing test function, ordinal within that function)`. **Line numbers
  are deliberately excluded** — they churn on every edit above them and would make the gate fail on
  unrelated commits, which is how a gate gets weakened.
  **Falsifier:** if that identity proves unstable in practice — parametrisation, generated names,
  duplicate function names across files — I fall back to a per-file count **and say so in this document**.
- **The baseline file holds the GATED list and nothing else.** Census totals per category live in this run
  record with their command and their date. **An ungated number checked into the repo is a number that goes
  stale silently, which is this row's own defect wearing a different hat** — `6G-RUN.md`'s `F5` is the
  recorded instance, a docstring claiming 347 while its own constant said 409, *in the module that exists
  to catch stale prose numbers*.
- **Only S2 is gated.** S0 and S1 are counted and reported. Gating S1 would be ruling on the middle
  category, which I am explicitly not authorised to do.

**The pass condition, fixed now so it cannot be relaxed to fit what the checker returns:**

> The gate is met when **(a)** it exits 0 at the true baseline on a clean tree, **(b)** it exits **1** when
> a result-conditioned skip of the `C3-26` shape is added to any contract test, **(c)** it exits **1** when
> the baseline file is edited to a higher count without a corresponding site, and **(d)** it exits **1**
> when a flagged site is fixed and the baseline is not lowered.

**Every one of (b), (c) and (d) is DEMONSTRATED by running it, not asserted.** `6G-RUN.md`'s own lesson is
the reason: **a gate cell that cannot fail is decoration.** The mutation for (b) is a **mutate-and-restore**
on a tracked file, and `git status --porcelain` is confirmed clean afterwards.

**And the counter-clause, so the pass condition cannot be met by over-flagging:** the gate must exit 0
against a **control** — a test file containing one S0 skip and one S1 skip of the supervisor's two shapes
and no S2 — and **the gate is NOT met if it flags either.** A checker that flags everything passes (b) and
has deleted real coverage.

### §0.7 — What I am AUTHORISED to fix, and what I am NOT

From the supervisor's answers, restated as constraints rather than summarised:

- **AUTHORISED:** sites that are **unambiguously S2**, the `C3-26` shape. Fix them and lower the baseline.
- **NOT AUTHORISED:** anything in **S1**. Bring the shape and the count; the supervisor rules.
- **NOT AUTHORISED:** converting S0 skips to `requires_capability` markers **in bulk**. **One worked
  example first**; if it is clean the supervisor authorises the sweep.
- **NOT AUTHORISED:** touching `Q101` or per-key severity. Both are the founder's and both are open.

### §0.8 — Numbers

**Every published number in this document is re-derived by its defining command LAST**, after the prose is
written, and the command is printed beside the number. Rows 6e, 6f and 6g each caught one of their own
numbers by this discipline. Numbers in §0 are thresholds I am setting or figures I have **inherited and
marked as inherited**; they are not measurements of mine.

### §0.9 — State at pre-registration

| fact | value |
|---|---|
| `main` locally, and `origin/main` | **`e548541`** — in sync, working tree clean, **0 local-only commits** |
| `origin/main` | **held at `e548541` by the supervisor**, who will not push while this row runs |
| Other rows mid-round | **none** — the partition is empty, so moving `origin/main` moves no baseline. **I tell the supervisor before I push regardless** |
| Kill-row count | **TWENTY-THREE** — unchanged by this row, which is not kill-row shaped |
| Governance register | **A3 is CLOSED** (`R103`), the stop criterion has **STOOD DOWN**, the ACTIONS surface has reopened |
| Standing gate set | **FOUR** — `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`. This row proposes the **fifth** |
| Bare `pytest.skip(` sites | **121 across 13 files — the supervisor's figure, INHERITED, not measured by me** |
| `requires_capability` markers | **223 across 23 files — the supervisor's figure, INHERITED, not measured by me** |
| `ontoloche/contract/` | **29 `.py` files**; `ontoloche/aio/contract/` **29**, generated |
| Predicted S2 count | **9** (§0.5), a guess from zero test files read |
| `oo-pg` | port **55432**, DSN per §0.10 |
| Next ruling number | **R104** |

### §0.10 — The suite floor, and the commands that fill it

Fixed by running the commands below at `e548541` **before any change**, so that *"never drops below it"*
names a number this row observed rather than one it inherited.

```
py -m pytest -q --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q --pyargs ontoloche.aio.contract
```

**Run ONE AT A TIME, never in parallel** — row 6f caused an out-of-memory kill running two at once and lost
two full legs. The SQLite-only leg runs first as the cheap *is-anything-broken* check.

The gates, **five** if this row's lands, and every one of them run at the final state:

```
py docs/tools/check_links.py             -> exit 0
py docs/tools/check_spec_drift.py        -> exit 0
py docs/tools/check_merge_guard.py       -> exit 0
py docs/tools/check_capability_matrix.py -> exit 0
py docs/tools/check_skip_census.py       -> exit 0   (this row's, if it lands)
```

| leg | result at `e548541` | at this row's final state |
|---|---|---|
| sync, SQLite only | **527 passed, 731 skipped, 0 failed** (290.30s) | *see §3.6* |
| sync, three backends | **942 passed, 316 skipped, 0 failed** (678.42s) | *see §3.6* |
| async, three backends | *see §3.6* | *see §3.6* |

**Recorded honestly:** the floor cells are empty at this commit because holding §0 back to wait for a run
would have meant committing it after the tests were open, and **the ordering that makes this section
binding is worth more than a filled cell.** The commands are printed and are not revisable.

### §0.11 — The adversarial round, REQUIRED, and its terms fixed here

**Not optional and not a judgement call this row gets to make on the strength of its own care.** The
supervisor's amendment B is explicit that the omission of this requirement from row 6g's brief already cost
once: row 6g's round found **3 BLOCKING**, two of which **closed a legal operation non-overridably at three
doors** — the precise `R102` §3 trap, re-created by the fix meant to honour it — after that row had
committed a census before its comparator, demonstrated its central prediction against two wrong
implementations, verified its gate cells against a pristine comparator and checked five restraint claims.

> **SELF-VERIFICATION DOES NOT SUBSTITUTE FOR A FRESH ADVERSARY, and a row that reports it verified itself
> thoroughly has given a reason to run the round, not to skip it.**

**This row is unusually exposed** and the exposure is named rather than hoped past: **a checker that decides
which skips are illegitimate is an instrument whose own false positives are invisible from the inside.** It
will look correct to whoever wrote it, on the cases they had in mind. The refinement that produced S1 was
found by RUNNING the rule against a fifth case, not by re-reading it.

**Terms, fixed now:**

- **Lenses are FRESH** — no lens has seen D1, this document, or the checker before it is dispatched.
- **At least four lenses**, each pointed at a different surface: (1) D1's false positives, (2) D1's false
  negatives, (3) the ratchet's own evadability, (4) this document's numbers against the commands that
  produced them.
- **Findings are graded BLOCKING / MAJOR / MINOR and every one is recorded**, including the ones I decline,
  with the reason for declining.
- **The round runs BEFORE the row lands**, and *"landed"* means **verified on `origin` by `git ls-remote`**,
  never my own word for it.

### §0.12 — What I do NOT get to change

- **The kill-row count stays TWENTY-THREE.** This row is not kill-row shaped and must not be routed there.
  **I never self-classify a kill-row trip** — a construction reaching the criterion's shape is ROUTED.
- **The governance register is not mine to open or close.**
- **S1 is not mine to rule.** Bring the shape and the count.
- **D1 is not narrowed to make existing tests pass.** If the gate would fail existing tests, the count is
  routed; the rule is not weakened.
- **The baseline is not raised by this row or any other without the supervisor's ruling.**
- **`tools/unasync.py` is a GENERATOR, not a check.** It is not run to "verify" anything, and
  `unasync` reporting *"0 of 25"* is **not** a mirror-consistency check on this box (LF/CRLF). The reliable
  check is the sync and aio diffs against `origin/main` being **identical**.
- **Read-only means read-only: no writes to any tracked file, including a mutate-and-restore**, wherever a
  step is declared read-only. Where a mutate-and-restore IS required (§0.6's demonstrations), it is
  declared as a write and `git status --porcelain` confirms the restore.
- **`git add -A` is FORBIDDEN.** Explicit paths, with `git status --porcelain` immediately before staging.
  **The supervisor shares this working tree.**
- **`rm` takes a literal absolute path, never a `$var`.**
- **"LANDED" means ON ORIGIN**, verified by `git ls-remote`. Nothing is called landed before that.
- **I tell the supervisor before I push.**

---

*Sections §1 onward are written after this commit, and every one of them is bound by the above.*

---

## §1 — THE CENSUS, AND THE MODEL THAT DID NOT SURVIVE IT

**Every number in §1 and §2 is followed by the command that produces it**, per §0.8. Where
a number came from a mutation that no longer exists in the tree, the mutation script is
printed with it. Numbers with no command beside them are a defect in this document, and
the first draft of this section had eleven of them — found by the round, not by me.

### §1.0 — The count, by the command §0.4 fixed in advance

```
grep -rn --include='*.py' 'pytest\.skip(' ontoloche/contract/ | grep -v __pycache__ | wc -l
grep -rn --include='*.py' 'requires_capability' ontoloche/contract/ | grep -v __pycache__ | wc -l
```

| figure | supervisor at `e548541` | **mine, same command** |
|---|---|---|
| bare `pytest.skip(` sites, `ontoloche/contract/` | 121 in 13 files | **121 in 13 files** |
| `requires_capability` markers | 223 in 23 files | **223 in 23 files** |

**The instrument agrees with itself across two operators**, which is the only thing that
makes the eight-versus-two drift in the amendment readable as a fact rather than a
measurement artefact.

**P3 is CONFIRMED, and the disagreement is better than predicted.** The checker's AST parse
of the same directory finds **120**, not 121, at `e548541`. The 121st is at
`test_c3_resolve_type.py:1230`, and it is **inside a comment**:

```
    # first cut read `if unscored.confidence is not None: pytest.skip(...)` -- a skip
```

**That comment is `C3-26`'s own record of the defect this row exists to gate.** The grep
census counts the DESCRIPTION of the defect as an INSTANCE of it. A text instrument cannot
tell a skip from a sentence about a skip, and the one place in this suite where that
distinction was written down is the one place the instrument got it wrong.

**At the FINAL state of this row those figures are 122 and 121**, because §2.4 adds a
gate-runner to `test_manifest.py` and it carries one `pytest.skip("PENDING -- ... is not in
this install")` — the same line its three sibling gate-runners already carry. **So the row
that measures the unaudited surface adds one site to it**, and that is stated here rather
than netted out. Every §1 figure below is at the final state unless it says `e548541`.

### §1.1 — SCOPE, corrected by the round: the gate scans BOTH trees

§0.4 fixed the scope as `ontoloche/contract/` only, on the argument that
`ontoloche/aio/contract/` is generated by `tools/unasync.py` and gating a derivative would
double-count the source. **That argument is true of 22 of the 29 async files and false of
the rest**, which a fresh lens found and demonstrated:

```
for f in ontoloche/aio/contract/*.py; do head -5 "$f" | grep -q "GENERATED FILE" \
  && echo "GEN  $f" || echo "HAND $f"; done
```

**`ontoloche/aio/contract/conftest.py` and `ontoloche/aio/contract/test_c0_backend_local.py`
are HAND-WRITTEN and carry skips of their own.** `tools/unasync.py`'s own
`HAND_WRITTEN_ASYNC` names the second and explains why (`C0-08` races two writers on two
threads; `C0-09` builds an adapter directly — neither survives token substitution). **A
result-conditioned skip written into either of those two files would have been invisible to
this gate permanently**, which is the defect this row exists to prevent, in real files,
today.

**So the gate scans both trees and skips generated files by their own banner.** The scope
sentence in §0.4 is superseded, and this paragraph is the record of it.

### §1.2 — The census, split

```
py docs/tools/check_skip_census.py --census
```

| cell | both trees | sync tree | hand-written async | gated |
|---|---|---|---|---|
| **S0 — ENVIRONMENT** | **60** | 47 | 13 | no — legitimate |
| **S1 — SETUP RESULT** | **49** | 49 | 0 | no — **not this row's to rule** |
| **S2 — RESULT UNDER TEST** | **6** | 6 | 0 | **YES** |
| **S3 — UNCONDITIONAL** | **1** | 1 | 0 | no — reported |
| **S4 — UNDECIDABLE** | **16** | 11 | 5 | no — an honest refusal to answer |
| **S5 — PROVEN ENVIRONMENTAL** | **7** | 7 | 0 | no — **the category the model did not have** |
| | **139** in 16 files | 121 in 13 | 18 in 3 | |

```
py docs/tools/check_skip_census.py --census --dir ontoloche/contract
py docs/tools/check_skip_census.py --census --dir ontoloche/aio/contract
```

**All six gated sites are in the sync tree.** The three hand-written async files add
eighteen sites, thirteen of them plain environment, and no S2 — which is the answer to
*"was the scope correction worth making?"*: **it found no defect and closed a hole**, and
both halves of that are the result.

### §1.3 — THE THREE-CATEGORY MODEL IS WRONG, and §0.5b's own criterion says so

**§0.5b criterion 1 TRIPS.** It fixed the model as wrong if five or more sites need a
category the partition does not name. **Seven do.**

The suite invented the missing category on purpose, uses it in four files, and wrote down
why. This is `test_c10_merge_types.py:1490-1494`, verbatim and with the file's own emphasis
(which is none — the emphasis in earlier drafts of this document was mine and is removed):

> NOT REACHABLE, never a pass. The collision is built by writing an alias, so a backend
> declining `stores_aliases` drops it and the merge has nothing to refuse -- the fixture
> cannot pose the question there. Gated on the CAPABILITY rather than on the outcome, so a
> store that CAN hold the alias and merged anyway is a finding and not a skip.

```
grep -rn --include='*.py' 'NOT REACHABLE' ontoloche/contract/ | grep -v __pycache__
    -> 15 hits across 4 files: test_c10_merge_types.py, test_c12_foundry_import.py,
       test_c19_actions.py, test_c9_retire.py
```

**S5 — PROVEN ENVIRONMENTAL.** The guard reads the result under test, and then the block
**asserts the capability that explains that result BEFORE it skips.** Six of the seven
carry a *"NOT REACHABLE, never a pass"* comment; **the seventh, `test_c9_38` at
`test_c9_retire.py:1911`, carries no comment at all** — only the phrase inside its skip
string. An earlier draft of this section said all seven; that was wrong and the round
caught it.

**Why it is not the `C3-26` shape, stated as a mechanism rather than as a judgement:** break
the implementation on a *capable* backend and the assertion fails, so the id **FAILS** and
does not skip. `C3-26`'s defect was that *"if the implementation returned `0.0` or `1.0`
tomorrow, the id would SKIP, not fail."* S5 is precisely the repair of that, applied by the
suite before this row existed. **A gate that flagged S5 would delete the correct pattern
along with the wrong one**, which is the counter-clause §0.6 fixed in advance.

**An EIGHTH site carries the S5 shape and this checker cannot see it**, which the round
found and this paragraph owes. `test_c19_actions.py:4908`, the helper
`_skip_if_cannot_record(registry, out)`, does exactly the S5 thing — asserts
`registry.caps.stores_events is False` and then skips — but `out` arrives as a **parameter**,
so nothing in that frame binds an observation and the checker cannot classify it. It is
reported as **S4-UNDECIDABLE**. **This is the gate-evasion path §0.3 pre-registered as known
exposure (b)**, and it fired: *"`pytest.skip` reached through a helper function, where the
guard and the skip are in different frames."* **The S5 count of 7 is an instrument count,
not a shape count. Eight sites carry the shape.**

**Criterion 2 ALSO TRIPS, and I am reporting it rather than arguing the denominator down.**
Undecidable sites are **16** against a result-reading denominator of **71** (S1 + S2 + S4) —
**22.5%**, above the 20% bar; against **78** including S5 it is **20.5%**, also above.

**But it trips on the CHECKER, not on the model, and the distinction is load-bearing.**
Hand-classified, the sixteen are **fifteen plain ENVIRONMENT** — `adapter.capabilities()`,
`registry._attribute_store() is None`, `not spec.exists()`, a `requires_attribute_store`
marker lookup, a `backend == ...` chain — **and one the S5 shape**
(`_skip_if_cannot_record`). **None of them needs a category this partition does not name.**
What they need is a checker that can follow a value through an inline call or a parameter,
and that is an instrument limit which §0.6 answers by never gating S4.

**Criterion 3 does NOT trip.** D1 reproduces all seventeen calibration verdicts (§1.6).

**And a defect in my own pre-registration, recorded rather than smoothed over.** §0.5b's
criteria were written to catch *a category the model does not name* but are measured on
*the cell the checker could not classify*, and those are two different things. The
criteria caught the right answer for reasons they did not name.

### §1.4 — THE FINDING THE SPLIT MAKES VISIBLE: one row wrote both shapes six hours apart

An earlier draft of this section said *"same author, same file, same shape, same day."* The
round pointed out that **every commit in this repository is authored by `stephan.dyson`, so
"same author" excludes nothing**, and that at the granularity this project actually uses —
the row — the claim needed checking. Checked, it is sharper than what it replaced.

```
git log --oneline -S'def test_c10_24_merge_states_a_skipped_identity_guard_too' \
  --format='%h %ad' --date=short -- ontoloche/contract/ | tail -1
```

| commit | time | subject, truncated | what it wrote |
|---|---|---|---|
| `f8992f3` | 2026-09-05 **04:36** | *CHANGE 2 of 3 -- PAGE ORDER and TRUNCATION: the SEVENTEENTH and EIGHTEENTH tr…* | `test_c10_22` — **flagged** |
| `a446b89` | 2026-09-05 **05:23** | *CHANGE 3 of 3 -- THE CAPABILITY-DEGRADED SKIP: the NINETEENTH trip…* | `test_c10_24`, `test_c12_24` — **both flagged** |
| `4f8db52` | 2026-09-05 **11:46** | *ROUND 2 FIX, CHANGE D of 4 -- the ACCUMULATOR family, confirmed by FOUR lense…* | `test_c10_27`, `test_c12_27` — **the S5 repair** |

All four commits are claimed by [`6D-RUN.md`](6D-RUN.md) (`grep -c` returns 5, 9, 3 and 6
hits). **So one row wrote three of the six flagged sites in its first rounds, invented the
proven-environmental repair six hours later in its round 2, and did not go back for its own
three.** The second commit's own subject line is *THE CAPABILITY-DEGRADED SKIP*.

**That is a stronger version of the brief's structural claim than "two shapes side by
side."** The row was not ignorant of the distinction — it minted the repair the same
morning. **What it lacked was anything that would tell it which of its existing skips had
the defect**, which is what this gate now is.

The six flagged sites were written by **three rows**: 6c (`2da0433`, 2026-09-02 — two
sites), 6d (three sites above) and 6f (`daa86e7`, 2026-09-09 — one site).

### §1.5 — The prediction, and the miss

**Predicted: 9. Found: 6 gated.** The honest version needs the whole path, because the
number moved for three different reasons and only one of them was the census:

| moment | S2 | why it moved |
|---|---|---|
| the checker's first working cut | **12** | S5 did not exist yet |
| after the derivation fix | **13** | `test_c12_24` arrived from S4 |
| after S5 was separated | **6** | the seven proven sites left S2 |
| after the round's fixes, both trees | **10** | four false positives appeared — see §1.6 |
| after the capability-read fix | **6** | the same six, by a far stronger classifier |

**My 9 sits between 6 and 13. The round corrected my scoring of it, and the correction
stands:** an earlier draft said *"two errors cancelled."* **There were three.**

| step of §0.5's derivation | predicted | actual (sync tree, the scope I predicted) | verdict |
|---|---|---|---|
| 2. S0 — environment | **~85** | **47** | wrong by nearly half, in the direction §0.5 named as its weakest step |
| 3. result-reading sites | **~36** | **62** (S1 + S2 + S5) | wrong by 72% |
| 4. S1 — setup result | **~24** | **49** | wrong by more than double |
| **the step I never wrote down** | **0** | **S3 + S4 + S5 = 19** | **the model had no cell for one site in six** |
| 5–6. S2 | **9** | **6** | close, and close by accident |

**The predicted S2 share of result-reading sites was 12/36 = 33%. The actual is 6/62 =
9.7%.** The final number landed near mine because three large errors ran in opposite
directions, not because the reasoning was nearly right.

**What I did not know about the suite that made me say 9**, which the supervisor asked for
explicitly: I assumed the bare skip is the *fallback* for what a `requires_capability`
marker cannot express, so the residue would be mostly environment. **It is not.** This API
returns `Refusal` objects rather than raising, so fixtures are built through calls that can
refuse, and *"the fixture could not be built on this backend"* is the single largest reason
this suite skips.

**The interesting number is therefore not the 6. It is the 49.** The middle category the
brief said *"is where the line actually needs drawing"* is the **largest cell**, and it is
the one this row is not authorised to rule on.

### §1.6 — Seven defects in my own instrument, kept rather than tidied away

A census whose instrument is unverified is what this row exists to gate. Four were mine,
found by reading the sites. **Three were found by the adversarial round**, and one of those
three was introduced by the fix for another.

| # | found by | what it reported | what was actually wrong |
|---|---|---|---|
| 1 | me | **all 120 sites `S3-UNCONDITIONAL`** (the count at that moment) | the guard walker searched for the skip's *statement* and never matched an expression. **The first run said every skip in the suite was unguarded and nothing about the output looked wrong** |
| 2 | me | `registry` treated as a call result | `registry = make_registry(adapter)` is an assignment from a call, so the canonical legitimate guard would have been flagged everywhere. Fixed by a receiver rule |
| 3 | me | `test_c12_24` in S4 while `test_c12_27` was in S2 | the same shape in the same file, two ways. `tuple(out[0].warnings or ())` contains a call; `rows[0].warnings or ()` does not |
| 4 | me | **13 sites in S4** including `not checker.exists()` | any non-builtin call in a guard tripped it, including `w.startswith(...)` on a comprehension variable |
| 5 | **round, BLOCKING** | **an extra assertion UN-FLAGGED a real defect** | defect 2's receiver rule was *"any name you call a method on"*, so one `assert unscored.outcome.startswith("ex")` moved the gate's own pinned `C3-26` case from S2 to **S0**. **The fix for defect 2 created a worse defect than defect 2** |
| 6 | **round, BLOCKING** | the six baselined sites could all be dropped by DELETING one assertion each | §2.1 |
| 7 | **me, cleaning up after 5** | four canonical ENVIRONMENT guards flagged as S2 | narrowing the receiver rule to close defect 5 flagged `caps = adapter.capabilities()`, `registry.caps.stores_invocations`, and a guard on a fixture that had acquired an observation root because `adapter._migration_sql = lambda: broken` was read as *binding* `adapter` |

**Defect 1 is the one worth keeping for its own sake.** A gate reporting *120 unconditional
skips* is a dramatic, publishable, completely false finding.

**Defect 5 is the one worth keeping as a lesson.** It was introduced by my own amendment to
D1, it made the classifier weaker in exactly the direction the row exists to prevent, and
**it was invisible from inside**: the calibration set passed, the census looked reasonable,
and the number was plausible. A fresh lens found it in one mutation.

**Defect 7 is what defect 5's fix cost**, found by me and published here rather than after
someone else noticed the gate flagging capability checks.

**Calibration, pinned in the checker and run on every gate invocation:**

```
py docs/tools/check_skip_census.py --selftest   ->  17 shapes, 17 OK, exit 0
```

Five shapes were pre-registered. **Nine more were written by the adversarial lenses**, each
one a mutation that broke the classifier as it then stood, and **three more are the false
positives of defect 7**, pinned so the cost of defect 5's fix cannot come back silently.

**§0.3 said the pre-fix forms would be "recovered from git history" and that turned out to
be impossible**, which is a defect in my own §0. Row 6f fixed `C3-26` and `C10-16` inside
its own working tree before it committed, so no commit ever held them:

```
git log -S'the unscorable branch is not reachable' --oneline e548541
    -> (nothing)
```

**That command is pinned at `e548541` on purpose, and the round is why.** An earlier draft
printed it without the revision, and by then it was FALSE — this row had pinned the `C3-26`
reconstruction into `check_skip_census.py`, which put the string into git history at
`250f9b8`. **The row published a command asserting a string was absent from history, in the
commit that added it.** The conclusion survives; the evidence as first printed did not.

**`C3-14`'s pre-fix form is neither recoverable nor reconstructible without guessing, so it
is EXCLUDED from the calibration set and named as missing rather than invented.**

### §1.7 — The six gated sites, by name, and the seven ids behind them

**Six sites in FOUR files** (an earlier draft said five; `wc -l` on the baseline's own file
column is the check), and **seven ids**, because one is a helper with two callers.

```
py -c "import json;d=json.load(open('docs/tools/skip_census_baseline.json'));\
print(len({e['site'].split('::')[0] for e in d['sites']}), 'files', d['count'], 'sites')"
    -> 4 files 6 sites
grep -n '_tombstone_holding' ontoloche/contract/test_c4_propose_type.py
    -> 450 (def), 503, 548  -- two callers, C4-15 and C4-16
```

| # | site | guard | what its assertions are about |
|---|---|---|---|
| 1 | `test_c10_merge_types.py::test_c10_22…#0` | `isinstance(out, Refusal)` | `out.warnings` must name **the collision scan specifically** — the **inline comment at `:1207-1210`** records that asserting the bare value let a mutation survive |
| 2 | `test_c10_merge_types.py::test_c10_24…#0` | `isinstance(merged, Refusal)` | `merged.warnings` must carry `identity_guard_skipped:different_consumer_sets:` |
| 3 | `test_c12_foundry_import.py::test_c12_21…#0` | `isinstance(gone, Refusal)` | `gone.aliases` must still hold `zzz_moved` — asserted **one line after the skip that hides it** |
| 4 | `test_c12_foundry_import.py::test_c12_24…#0` | `any(w.startswith('import_refused:') for w in warnings)` | the same `warnings` must carry `identity_guard_skipped:…` |
| 5 | `test_c3_resolve_type.py::test_c3_27…#0` | `answer.type is None or answer.type.name != 'searchable'` | `answer.confidence == pytest.approx(0.94)` — rule **5.3.2-14** |
| 6 | `test_c4_propose_type.py::_tombstone_holding#0` | `isinstance(gone, Refusal)` | `word in gone.aliases`, **and it is a HELPER**: `C4-15` and `C4-16` both call it |

**SIX is under §0.5c's `25`, so the LARGE branch does not fire.** No site was removed from
this list to keep it under the bar, and the bar was fixed before the count.

**Site 3 is the one to read twice.** It skips on `gone` being a `Refusal`, and the very next
line asserts `"zzz_moved" in (gone.aliases or ())`. **That is `F1`'s sentence exactly — a
conditional assertion whose body never ran, which is worse than a tag because it reads as
coverage.** The round added a sharper reading: `C12-21` carries
`@pytest.mark.requires_capability("stores_aliases", "indexes_membership", "stores_events")`
at `:1047`, and `registry.py:3969` refuses `cannot_record_override` **only** when
`force and not self.caps.stores_events`. **On every leg this id actually runs, that refusal
cannot fire — so the skip is unreachable except on a defect.** Verified:

```
sed -n '3969p' ontoloche/registry.py  ->  if force and not self.caps.stores_events:
```

**Site 5 is `C3-27`, written by row 6f**, in `test_c3_resolve_type.py`, **94 lines below**
the comment block in `C3-26` (`:1229`–`:1239`) explaining why this is never legitimate. An
earlier draft said 95.

**Which of the six actually FIRE**, from the floor runs' `-rs` output — this is measured,
not reasoned:

| leg | sites that fired | reason |
|---|---|---|
| sync, SQLite only | **2** — `test_c10_24#0`, `_tombstone_holding#0` | `cannot_record_override` on both |
| sync, three backends | **0** | — |

`cannot_record_override` is precisely what the seven S5 sites assert
`caps.stores_events is False` for before they skip. **The repair for those two is not
invented: it is the pattern already in the suite, in four other files.**

**None of the six is repaired in this row**, and §3 says why and routes it.

---

## §2 — THE ADVERSARIAL ROUND, AND WHAT IT COST THE GATE

**Required by the brief's amendment B, not chosen.** Four fresh lenses, none of which had
seen D1, this document, or the checker, dispatched at the terms §0.11 fixed: false
positives, false negatives, ratchet evadability, and this document's numbers against the
commands that produce them.

**The round was worth more than everything this row did before it.** It found **five
BLOCKING-class defects** — the four in §2.1 through §2.4 below, plus the scope hole recorded
in §1.1 — and **two of the five were defects in the fixes I had just made**. The
supervisor's sentence in amendment B is the finding restated: *self-verification does not
substitute for a fresh adversary, and a row that reports it verified itself thoroughly has
given a reason to run the round, not to skip it.* Before the round I had: a pre-registered
discriminator, a five-shape calibration set including `C3-26`'s verbatim pre-fix source,
four gate cells demonstrated by mutation, a counter-clause control, and six sites
hand-verified one at a time. **All of that was consistent with a classifier that could be
switched off by adding an assertion.**

### §2.1 — F1, BLOCKING: the cheapest way to make this gate green was to DELETE COVERAGE

Found by two lenses independently.

**Every one of the six flagged sites stopped being flagged if you simply deleted the
assertion that read the guarded value.** The site dropped to S1, the census shrank, the gate
then failed as *stale* — and its own message told you to run `--write-baseline`, which the
baseline's own comment described as *"a normal commit anyone may make."* **The ratchet's
prescribed remedy was the weakening it exists to prevent.** Reproduced:

```
delete `assert word in (gone.aliases or ()), (...)` from _tombstone_holding
  ->  the site reclassifies S2 -> S1
  ->  py docs/tools/check_skip_census.py            exit 1  ("no longer flagged")
  ->  py docs/tools/check_skip_census.py --write-baseline  would have written 5
```

**And the sharpest half is what it revealed about the classifier's fairness.**
`_tombstone_holding` exists **three times**, near-identically, in
`test_c4_propose_type.py:450`, `test_c12_foundry_import.py:1101` and
`test_c9_retire.py:1725`. All three run the same `retire(force=True)` and skip on
`isinstance(gone, Refusal)`. **Only the c4 copy was flagged, and the only difference is that
the c4 copy asserts that its fixture held.** The gate was punishing the strongest of the
three.

**THE FIX.** The enclosing function's assertion count rides in the baseline, and a site may
only leave the flagged set while its function still asserts at least as much:

| what happened to a baselined site | verdict | `--write-baseline` |
|---|---|---|
| the skip became an assertion (asserts went UP) | **REPAIRED** | permitted, exit 0 |
| the skip is gone and the function asserts LESS | **DE-ASSERTED** | **refused** |
| the function itself is gone | **GONE** | **refused** |

Refusing takes `--allow-deassertion`, which exists so that the choice appears in the shell
history and in the commit rather than nowhere. Demonstrated in §2.5.

### §2.2 — F2, BLOCKING: an added assertion UN-FLAGGED the gate's own pinned defect

**This one was mine, it was introduced by my own amendment to D1, and it is the most
instructive thing in the row.**

D1's first amendment (§1.6 defect 2) said *a name you call a method on is a receiver, not a
result* — to stop `registry = make_registry(adapter)` making the canonical legitimate guard
look illegitimate. **"Any name you call a method on" was far too wide.** A lens added one
ordinary line to the checker's own calibration case:

```
C3-26 pre-fix (VERBATIM from the brief)          -> ['S2-RESULT-UNDER-TEST']
  + assert unscored.outcome.startswith("ex")     -> ['S0-ENVIRONMENT']
```

**Adding an assertion moved a real, pinned defect into the most legitimate bucket there
is.** Combined with F1's stale-then-lower path, any baselined site could be retired by
adding an assertion instead of by repairing anything.

**THE FIX.** A receiver is now specifically *a name whose method call produces an ASSIGNED
value* — the object the test drives the system through. An incidental `.startswith()` inside
an assertion no longer launders a result into configuration. **And the fix cost four false
positives**, which is §1.6 defect 7 and is published there rather than absorbed.

### §2.3 — F3, BLOCKING: nineteen of twenty-two evasion shapes walked past it

Two lenses wrote synthetic variants of the exact `C3-26` shape and ran them through the
gate. The first flagged 2 of 27; the second, 3 of 22. **Every escape was the same defect in
substance: call the system, read the result, skip when the result is not what the test
wanted, assert on that result otherwise.** Grouped by root cause, with the fix:

| escape | landed in | fix |
|---|---|---|
| `while`, ternary, `and`, `match`, `try/except` guard | **S3 — "unconditional"** | non-`if` guards are S4, never S3. **A skip in an `except` handler for the exception the test exists to catch was scoring as UNGUARDED** |
| `seen = out.reason` then `assert out.reason` | S1 | roots: a derived name inherits the observation it came from, so guard and assert meet at `out` |
| `refused = isinstance(out, Refusal)` | S1 | builtins are derivations, not fresh observations |
| the only check is `with pytest.raises(...)` | S0 | a `raises`/`warns` block IS an assertion |
| `import pytest as p` then `p.skip(...)` | **not a site at all** | module aliases are read from `import` as well as `from … import` |
| `raise pytest.skip.Exception(...)` | **not a site at all** | detected |
| module-level `_bail = pytest.skip` | **not a site at all** | detected |
| `assert registry is not None` before the skip | **S5 — laundered** | an S5 proof must name a CAPABILITY (`.caps`, `.capabilities()`), and must be in the skip's OWN branch, not an enclosing one |
| a file one directory deeper | never scanned | `rglob` |
| a skip in the hand-written async tree | never scanned | §1.1 |

**Nine of these are now pinned in the calibration set**, each as the mutation that broke the
classifier, so the breakage cannot come back quietly.

**What is NOT fixed, and is named rather than hidden:** a guard whose call is written inline
and binds no name (S4), and a guard on a **helper's parameter** (S4). Both are honest
refusals to answer and neither is gated. **§0.3 pre-registered known exposure (b) as exactly
this, and it fired** — see §1.3's eighth S5 site. The residual is real: a result-conditioned
skip written into a helper that takes the result as a parameter is invisible to this gate.
**It is the largest remaining hole and it is §3's first routed item.**

### §2.4 — F4, BLOCKING: nothing ran the gate

`grep -rn check_skip_census` over the whole repository returned hits in this run record and
nowhere else. There is no CI directory, no pre-commit config, no Makefile. **A fifth gate
that only runs when somebody remembers to run it is not a fifth gate**, and this repository
has already written the sentence: `test_manifest.py`'s own docstring for the merge-guard
runner says *"a guard that is only verified when somebody remembers to run a script is a
guard nobody is verifying."*

**THE FIX.** `ontoloche/contract/test_manifest.py` gains
`test_no_test_skips_on_the_result_it_exists_to_assert`, which shells out to the checker and
asserts `returncode == 0`, exactly as its three siblings do for `check_spec_drift.py`,
`check_merge_guard.py` and `check_capability_matrix.py`.

**It does not move `TOTAL`.** That constant counts ids matching `^def (test_c(\d+)_(\d+)_`
and this test is not one:

```
grep -n 'TOTAL = ' ontoloche/contract/test_manifest.py   ->  TOTAL = 414   (unchanged)
```

**It is not mirrored into the async tree**, because `unasync.py`'s `CONTRACT_TESTS` globs
`test_c*.py` and `test_manifest.py` does not match — the async copy is hand-written. The
gate scans both trees regardless.

### §2.5 — F5, MAJOR: a duplicate baseline entry raised the count with the gate green

`new` and `stale` both compared against `set(declared)`, so a repeated entry was never
stale, and `count` could go 6 → 7 while the gate reported *the ratchet holds*. **The
baseline's own contract sentence is that the number cannot move without the site moving with
it**, and this was the one way it could. Now refused.

### §2.6 — F6, MAJOR: the gate failed on a commit that added no defect

Site identity was `(file, function, ordinal-within-function)` and the ordinal counted
**every** skip in the function. **Adding an ordinary environment skip above a flagged one
renumbered the flagged one**, the gate failed with *RESULT-CONDITIONED SKIPS ADDED*, and the
printed remedy was `--write-baseline`. **This file's own `Site` docstring says a gate that
fails for unrelated reasons is a gate somebody weakens**, and it was that gate. Ordinals are
now grouped by `(function, guard text)`.

### §2.7 — Every gate cell, re-demonstrated after the round's fixes

`6G-RUN.md`'s lesson is that **a gate cell that cannot fail is decoration.** Each row below
is a declared write to a tracked file, restored by `git checkout --`, with
`git status --porcelain` confirmed clean after.

| cell | mutation | exit |
|---|---|---|
| **(a)** clean tree at the true baseline | none | **0** |
| **(b)** a `C3-26`-shaped skip added | a helper in `test_c17_edges.py` guarding on `out.types` and asserting it | **1** |
| **(c)** baseline count raised without a site | `count: 6` → `7` | **1** |
| **(c′)** F5: a duplicate entry inflates the count | one site repeated, `count: 7` | **1** |
| **(d)** a flagged site repaired, baseline left | `test_c3_27`'s skip → an assertion | **1** |
| **(d′)** lowering a REPAIRED site | `--write-baseline` after (d) | **0**, writes 5 |
| **(e)** F1: the assertion DELETED instead | `assert word in (gone.aliases or ())` removed | **1**, and `--write-baseline` **REFUSES** with `DE-ASSERTED: the enclosing function went from 1 assert(s) to 0` |
| **(f)** F6: an unrelated environment skip added above a flagged one | `if not registry.caps.stores_events: skip` inserted in `test_c3_27` | **0** — S0 60 → 61, S2 unchanged |
| **(g)** F3: laundering all six with `assert registry is not None` | one line above each of the six skips | **0** — **S2 stays 6, nothing laundered** |
| **(h)** a file that will not parse | a malformed insertion | **1**, and it names the file rather than raising a traceback |

**The counter-clause, which is the half that matters for a gate like this one.** Both
legitimate shapes added to a contract file at once — one S0 (`not
registry.caps.indexes_membership`) and one S1 (`isinstance(gone, Refusal)`): **S0 and S1 each
went up by one, S2 stayed at 6, gate exit 0.** A checker that flagged everything would pass
(b) and have deleted real coverage.

**And the classifier itself is gated.** `run_gate()` runs the seventeen-shape calibration
before it counts anything. A lens demonstrated that the FIVE-shape version was decoration —
seven plausible one-line regressions to the classifier all passed it, and six of the seven
also passed the full gate. **Nine of the twelve added shapes are that lens's own mutations.**

---

## §3 — WHAT IS ROUTED, WHAT IS NOT DONE, AND WHY

### §3.1 — ROUTED: the middle category is the largest cell, and it is not mine to rule

**49 sites are S1 — SETUP RESULT**, against 6 gated. The brief said this cell *"is where the
line actually needs drawing"*; the census says it is where most of the suite lives. The
supervisor's answers are explicit that a wrong call here *"silently deletes real coverage or
blesses a fake assertion"*, so what this row owes is the shape and the count, and here they
are.

**The shape, from the sites themselves:** the API returns `Refusal` objects rather than
raising, so a fixture is built by calls that can each refuse, and the test skips when one
does. `if not written or word not in (written[0].aliases or ())`, `if isinstance(gone,
Refusal)`, `if live is None`, `if why is None`. **These are not the `C3-26` shape and I have
not treated them as such.**

**But the boundary is thinner than the brief's example suggests**, and this is the part that
needs a ruling. `_tombstone_holding` in `test_c4_propose_type.py` is flagged and its two
identical twins are not, and the only difference is that the flagged one **asserts that its
fixture held**. Three readings are available and I am not choosing between them:

1. The c4 copy is right and the other two are under-asserted. The gate is pointing at the
   wrong member of the family.
2. All three are S1 and the c4 assertion is a fixture check that should not make the skip
   illegitimate. Then D1's S1/S2 line is in the wrong place for helper fixtures.
3. All three should carry the S5 proof, which for this shape is one line —
   `assert registry.caps.stores_events is False, gone` — and there is precedent in four
   files.

**Reading 3 is what the measurement supports and I still have not applied it**, because
applying it to a category I am not authorised to rule on is the same act as ruling on it.

### §3.2 — ROUTED: the six gated sites are NOT repaired, and the reason is a measurement

**Authorised, and deliberately unused.** The supervisor's answer authorises repairing
unambiguously result-under-test sites and lowering the baseline. I have not, and the reason
is not caution in general but a specific number:

| leg | of the six, how many actually FIRE |
|---|---|
| sync, SQLite only | **2**, both `cannot_record_override` |
| sync, three backends | **0** |

**Four of the six have not been observed firing on any leg this row ran.** For those four,
the honest repair is to name the environmental cause — and **I cannot name a cause I have
not observed.** Writing `assert registry.caps.X is False` for a refusal I have never seen
fire is inventing the capability that explains it, and getting that wrong converts a legal
skip into a false failure on a conformant degraded backend. **That is `C19-100`'s defect —
*it closed a legal operation* — which section E names twice and which row 6g re-created at
three doors while trying to honour the ruling against it.**

**For the two that DO fire, the repair is not invented and I am bringing it rather than
applying it**, because repairing two of six leaves a half-repaired family and the other four
need the async leg's evidence first:

```
test_c10_merge_types.py:1337   this backend refused for another reason (cannot_record_override)
test_c4_propose_type.py:467    this backend cannot retire the holder (cannot_record_override)
```

`registry.py:3969` is `if force and not self.caps.stores_events:` — so
`cannot_record_override` on a forced retire is **exactly** a `stores_events` fact, which is
what the seven S5 sites already assert. **The repair is one line each and it has precedent
in four files.** It is a small, safe, well-evidenced change and it is still not mine to make
unilaterally on a family whose other four members I cannot yet evidence.

### §3.3 — ROUTED: the largest remaining hole in the gate

**A result-conditioned skip written into a helper that takes the result as a parameter is
invisible to this gate**, and one such helper already exists —
`test_c19_actions.py:4908`, which happens to be correct. §0.3 pre-registered this as known
exposure (b) and it fired. Closing it means following values across call boundaries, which
is a different and much larger checker. **Named, not fixed, and it is the first thing I
would build next.**

### §3.4 — NOT ROUTED, because it is not this row's

- **The kill-row count stays TWENTY-THREE.** Nothing here merges a capability predicate or
  collapses two words onto one identity. **This row is not kill-row shaped and I have not
  self-classified a trip.**
- **The governance register is untouched.**
- **`Q101` and per-key severity are untouched.**
- **`R104` is unminted.** Nothing here needed a ruling to proceed; §3.1 and §3.2 are
  requests for one.

### §3.5 — The suite, at the floor and at the final state

Run one at a time, never in parallel, by §0.10's own commands.

| leg | at `e548541` | **at this row's final state** | delta |
|---|---|---|---|
| sync, SQLite only | 527 passed, 731 skipped, 0 failed (290.30s) | *not re-run — the three-backend leg supersedes it* | — |
| sync, three backends | 942 passed, 316 skipped, 0 failed (678.42s) | **943 passed, 316 skipped, 0 failed** (652.55s) | **+1** |
| async, three backends | *not measured at the floor* | **979 passed, 316 skipped, 0 failed** (369.81s) | — |

**The +1 is exactly the gate-runner §2.4 adds**, and nothing else moved. **The async floor
was not measured at `e548541` and this document does not pretend otherwise** — 979 is
recorded as the state at landing, not as an improvement on a number nobody took. Row 6g's
index entry reports 979 for the async leg at its landing, which is the nearest comparison
available and is cited as a comparison rather than as a floor this row observed.

**The mirror did not drift, checked the way the brief's section D requires** — by diffing
both trees against `origin/main`, not by running the generator:

```
git diff --stat origin/main -- ontoloche/contract      ->  test_manifest.py | 36 +++
git diff --stat origin/main -- ontoloche/aio/contract  ->  (empty)
```

**An empty async diff is the CORRECT result here and the reason is worth stating**, because
an empty diff is also what a drifted mirror looks like if you are not paying attention:
`test_manifest.py` is **not** generated. `unasync.py`'s `CONTRACT_TESTS` globs `test_c*.py`,
which `test_manifest.py` does not match, and `ontoloche/aio/contract/test_manifest.py` is
hand-written. **`tools/unasync.py` was not run at any point in this row** — it is a
generator, not a check, and the async leg's own
`test_generated_matches_source.py` is what verifies the mirror. It passed.

### §3.6 — Landing

| requirement | state |
|---|---|
| `check_links.py` | **exit 0** |
| `check_spec_drift.py` | **exit 0** |
| `check_merge_guard.py` | **exit 0** |
| `check_capability_matrix.py` | **exit 0** |
| `check_skip_census.py` — **the fifth, part of the set from the commit that adds it** | **exit 0** |
| run record indexed in `docs/README.md` | **yes** |
| tree clean | **yes** |
| landed | **means verified on `origin` by `git ls-remote`, never my own word for it** |
