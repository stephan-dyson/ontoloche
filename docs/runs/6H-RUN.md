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

| leg | result at `e548541` |
|---|---|
| sync, SQLite only | *filled by the run this commit authorises* |
| sync, three backends | *same* |
| async, three backends | *same* |

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
