# 6I-RUN — REPAIR THE EVIDENCED SKIPS, RAISE THE UNDER-ASSERTED TWINS, SCOPE THE HELPER HOLE

**Row 6i, under [R104](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-supervisor-ruling-R104.md).**
Brief: `2026-09-09-oo-skip-repairs-followon.md`, plus `2026-09-10-oo-6i-supervisor-answers-1.md`
which corrects it on item 2 and fixes the process order.

Floor commit: **`d3f9a79`**, which is where `origin/main` is held while this row works.

---

## §0 — PRE-REGISTRATION

**Committed ALONE, before any measurement.** No census has been run in this row, no leg has been run in
this row, and `git log` is the proof of the order. Everything below is derived by READING source, which is
the only thing that has happened so far.

### §0.1 — The item order, and why it is not the brief's order

The brief numbers four items. This row does them in the order **3 (scope only) then 1+4 as ONE change then
2**, for two reasons that are not preference.

1. **Items 1 and 4 are the same family and must be one commit.** Item 1's second site is
   `ontoloche/contract/test_c4_propose_type.py:467`, which is the `gone` skip inside `_tombstone_holding`.
   Item 4's "three twins" are that same helper, copied into `test_c9_retire.py:1724` and
   `test_c12_foundry_import.py:1101`. The brief's own term — *"repair the family as ONE coherent change"* —
   binds here even though it was written about item 2's six.
2. **Item 3 is scope-only and gated on nothing**, so it goes first and cannot be crowded out by a
   measurement that runs long.

Item 2's instrumentation runs last because it is the longest wall-clock step and because its result cannot
change items 1, 3 or 4.

### §0.2 — HYPOTHESIS H1: the brief's literal repair line is WRONG, and the suite already knows why

**The brief authorises, in these words:**

```python
assert registry.caps.stores_events is False, gone
```

placed under the existing `if isinstance(gone, Refusal):`.

**H1: that placement asserts a capability for every refusal reason, and the suite's own seven `S5` sites do
not do that.** Every audited instance I have read narrows the guard to the ONE reason the capability
explains before it asserts:

```
ontoloche/contract/test_c19_actions.py:4701   if isinstance(out, Refusal) and out.reason == "cannot_record_override":
ontoloche/contract/test_c19_actions.py:4904   if isinstance(out, Refusal) and out.reason == "cannot_record_override":
ontoloche/contract/test_c9_retire.py:1858     if back.reason == "cannot_record_override":
```

and `test_c19_actions.py:4712` shows what the fall-through is for — `assert not isinstance(out, Refusal)`,
so a refusal the capability does NOT explain fails the id instead of skipping it.

**Why this is not pedantry.** `_tombstone_holding`'s guard is `isinstance(gone, Refusal)`, which catches
ANY reason. `test_c10_24`'s guard is the same and its skip message says so out loud — *"this backend
refused for another reason"*. Asserting `stores_events is False` in those branches tells a backend that
refuses for a reason unrelated to event storage, while storing events perfectly well, that it has failed.
**That is a legal operation closed by a gate, which is `C19-100`'s defect and the exact failure the brief's
item 2 forbids me to commit.** Applying the brief's line verbatim would commit at item 1 the error the
brief withholds authorisation for at item 2.

**The repair this row will make instead**, for all four sites, matching the four-file precedent rather than
the brief's paraphrase of it:

```python
if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
    assert registry.caps.stores_events is False, (
        "this backend records events, so the refusal is not a capability", gone.detail,
    )
    pytest.skip("NOT REACHABLE: stores_events=False refuses the forced retire")
assert not isinstance(gone, Refusal), (
    "the fixture's retire refused for a reason no capability explains", gone,
)
```

**FALSIFIER for H1:** if any of the seven existing `S5` sites asserts a capability under an unnarrowed
`isinstance(x, Refusal)` guard, then the unnarrowed form IS the suite's pattern and H1 is wrong. I have
read three of the seven and will read all seven before landing.

### §0.3 — HYPOTHESIS H2: the brief's evidence cite covers ONE of the two sites, not both

The brief and `6H-RUN.md` §3.2 both explain the two evidenced sites with **`ontoloche/registry.py:3969`**,
`if force and not self.caps.stores_events:`.

**[Observed — read by me at `d3f9a79`]** that line is in the **`retire`** path, and its own comment says
*"`merge_types` had the unconditional form since v0; `retire` now matches it."* It explains
`test_c4_propose_type.py:467`, which calls `registry.retire(..., force=True)`.

**It does not explain `test_c10_merge_types.py:1337`**, which calls `merge_types` and never passes `force`.
The producer on that path is **`ontoloche/registry.py:5319`**, `if acknowledge and not
self.caps.stores_events:`, and the test passes `acknowledge=("definitions_diverge",
"no_consumer_evidence")`.

**H2: the conclusion survives and the citation does not.** Both guards read `self.caps.stores_events`, so
`assert ... stores_events is False` is the right assertion at both sites. But the brief called them
evidenced by one line that covers one of them, and a later reader following that cite at the merge site
finds a `force` check in a function the test never calls.

**FALSIFIER for H2:** a path exists by which `merge_types` reaches `registry.py:3969`. I will check the
call graph of `merge_types` for a nested `retire` before landing.

### §0.4 — THE PREDICTIONS. Two integers, both single values, neither a range

**P1 — of the six baselined sites, the number observed FIRING on the async three-backend leg is `0`.**

Derivation, exposed so the miss is accountable:

1. `6H-RUN.md` §3.2 measured the six firing **2 on `sync, SQLite only`** and **0 on `sync, three
   backends`**.
2. `6H-RUN.md` §3.5 records both three-backend legs at **316 skipped**, sync and async alike.
3. The async contract tree is generated from the sync one by `tools/unasync.py`, so the guards are the same
   guards.
4. So the async three-backend leg is the mirror of the leg that fired **0**, not of the leg that fired 2.

**The consequence I am binding myself to in advance:** if P1 is right, item 2's four unobserved sites
**stay baselined and unrepaired and I say so in the record**, and the two authorised sites are repaired on
`sync, SQLite only` evidence — **the superseded leg**, named as such, which is the point
`2026-09-10-oo-6i-supervisor-answers-1.md` §2 told me to state beside the count. If P1 is wrong and any
site fires, that is a finding about the six and it is brought, not reconciled quietly.

**P2 — `docs/tools/skip_census_baseline.json`'s `count` at this row's final state is `4`.**

Derivation:

1. It is `6` now, and `count` must equal `len(sites)` or the gate fails on its own arithmetic.
2. Two entries leave: `test_c10_merge_types.py::test_c10_24_merge_states_a_skipped_identity_guard_too#0`
   and `test_c4_propose_type.py::_tombstone_holding#0`. Both are `S2` today because their guard reads an
   observation an `assert` in the same function also reads; adding a capability proof inside the skip's own
   branch moves them to `S5`, which `check_skip_census.py` does not gate.
3. **No entry enters.** Item 4 adds `assert word in (gone.aliases or ())` to the c9 and c12 twins, which is
   what makes a site `S2`-eligible — but the same commit adds the capability proof, so they land on `S5`,
   not `S2`. The helper's OTHER skip, guarded on `written`, stays `S1`: no assertion in the function reads
   `written`, and neither of the two lines I add reads it either.
4. The four item-2 sites are untouched by P1's own consequence.

**FALSIFIER for P2:** any count other than 4, in either direction. A 5 means something I converted did not
convert; a 3 means something left the census that I did not intend to move.

### §0.5 — Fixed pass/fail criteria, set before the first measurement

| # | criterion | pass |
|---|---|---|
| 1 | all five gates at the final state | `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, `check_skip_census` each **exit 0** |
| 2 | the four repaired sites classify | **`S5`**, by `--census`, named individually |
| 3 | suite floor, sync three backends | **at least 943 passed, 0 failed** |
| 4 | suite floor, async three backends | **at least 979 passed, 0 failed** |
| 5 | skip totals | **316** on both three-backend legs, or a stated reason for every unit of drift |
| 6 | the mirror | `git diff --stat origin/main -- ontoloche/aio/contract` shows the four generated files and NOTHING else, and `test_generated_matches_source.py` passes |
| 7 | item 2 | either evidence names which sites fire, or the record states plainly that none did and they stay baselined |
| 8 | item 3 | a scope, with a size verdict — **its own row, or not** — and no half-built checker |

**Criterion 5 is the one most likely to be missed and it is stated as a number on purpose.** Narrowing a
guard from `isinstance(x, Refusal)` to `isinstance(x, Refusal) and x.reason == "..."` can only skip FEWER
ids, never more. If the skip total moves, it moves DOWN, and every unit of it must be explained by an id
that now fails or now passes — not waved at.

### §0.6 — What this row will NOT do

- **Not repair item 2's four unobserved sites** unless the instrumentation observes them firing. Naming a
  capability for a refusal I have not seen is `C19-100` closing a legal operation, twice in two days.
- **Not build the item 3 checker.** Scope and a size verdict only.
- **The kill-row count stays TWENTY-THREE.** Nothing here merges a capability predicate or collapses two
  words onto one identity.
- **The governance register stays at ONE.** `Q101` and per-key severity are the founder's and are open.
- **No ruling is minted.** §0.2 and §0.3 contradict the brief on evidence I can show; they do not need a
  ruling to proceed, and if the supervisor disagrees the shape is here to be disagreed with.

### §0.7 — The measurement commands, fixed here so they cannot be chosen after the fact

```
py -m pytest -q -rs --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q -rs --pyargs ontoloche.contract
OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology py -m pytest -q -rs --pyargs ontoloche.aio.contract
```

**`-rs` is the instrumentation and it is the whole of it.** It prints every skip with its file, its line and
its reason, which is what identifies WHICH of the six fired without editing a single test to find out.
**Run one at a time, never in parallel** — row 6f lost two legs to an out-of-memory kill doing otherwise.

`py docs/tools/check_skip_census.py --census` is the census. The plain invocation is the gate.
**`--write-baseline` WRITES**; `tools/unasync.py` is a **generator**, is required here because all four
edited files are `test_c*.py` and therefore mirrored, and is never run to verify anything —
`test_generated_matches_source.py` on the async leg is what verifies the mirror.

### §0.8 — The terms this row is held to

Pre-registration committed alone, before measurement, with the miss recorded afterwards. **An adversarial
round with fresh lenses before landing, and nothing goes in after it.** Explicit paths staged, never
`git add -A`, with `git status --porcelain` immediately before staging. `rm` takes a literal absolute path.
The supervisor is told before any push, and **"landed" means verified on `origin` by `git ls-remote`**.

---

## §1 — ITEM 3: THE HELPER-PARAMETER HOLE, SCOPED. IT IS ITS OWN ROW, AND THE REASON IS NOT ITS SIZE

**Scope only. Nothing was built.** The brief asked for a scope and a verdict rather than half a checker,
and the verdict is **its own row** for a reason that is not "it is big".

### §1.1 — The cell, measured rather than described

`py docs/tools/check_skip_census.py --census` at `0fcac56`:

```
S0-ENVIRONMENT             60
S1-SETUP-RESULT            49
S2-RESULT-UNDER-TEST        6
S3-UNCONDITIONAL            1
S4-UNDECIDABLE             16
S5-PROVEN-ENVIRONMENTAL     7
```

**`S4` is 16 sites and it is not one hole, it is three**, which neither the brief nor `6H-RUN.md` §3.3
separates:

| sub-shape | count | what it is |
|---|---|---|
| **the guard reads a HELPER's parameter** | **6** | item 3's hole |
| the guard calls inline and binds no name | 8 | a different hole, not routed to this row |
| the guard is not an `if` at all | 2 | a third, not routed either |

**Counted by the checker's own `why` text, after I first wrote 5 / 9 / 2 from reading a truncated listing
and had to correct it.** I derived the `9` as `16 - 5 - 2` rather than counting it, so **`5 + 9 + 2` sums to
16 exactly as `6 + 8 + 2` does, and the total could not reveal the error.** It came out only when I
recounted the inline shape directly from the `why` text and got 8 against my own 9.

**A wrong split that sums correctly is exactly the shape that survives review**, and the first version of
this paragraph made it worse: it claimed the numbers "did not add up and that is how the miscount was
caught", which is false — they added up perfectly, which is why the miscount survived a pass. That sentence
is corrected here rather than quietly deleted, because a record that hides how a defect nearly survived is
worth less than the corrected number.

**Of the six, exactly ONE takes a RESULT as the parameter:**

```
ontoloche/contract/test_c19_actions.py:4908  _skip_if_cannot_record#0   guard reads `out`
```

The other five do not:

```
ontoloche/contract/conftest.py:142                  adapter_factory#0   guard reads `backend`
ontoloche/contract/conftest.py:198                  adapter#0           guard reads `request`
ontoloche/aio/contract/conftest.py:165              adapter_factory#0   guard reads `backend`
ontoloche/aio/contract/conftest.py:221              adapter#0           guard reads `request`
ontoloche/aio/contract/test_c0_backend_local.py:120 _run_the_race#0     guard reads `first`
```

**Four of those five are pytest FIXTURES.** `backend` is a parametrisation string and `request` is pytest's
own request object, and both arrive from the fixture machinery rather than from any call this or any other
static checker can find in the source. **They are not reachable by "following values across call
boundaries" — there is no calling expression to follow.**

**The fifth is worse than unreachable, and it is the one that should decide the build.**
`_run_the_race(first, ...)`'s guard is `not (await first.capabilities()).stores_proposals` — **the canonical
LEGITIMATE environment guard, the exact shape `S0` exists for.** It sits in `S4` only because `first` is a
parameter, and `first` is an ADAPTER: the object the test drives the system through, which this checker
already has a RECEIVER rule to keep out of the observation set. **A pass that flags helper parameters
without resolving them would flag a capability read as a result-conditioned skip.**

So the hole's resolvable, result-carrying population today is **one site**, and that site is correctly
written.

### §1.2 — Why the general shape is the wrong build, and what the right one is

The brief describes closing this as *"following values across call boundaries"*. That is the general
interprocedural build and it has a defect the existing gate does not have.

**`_skip_if_cannot_record` has FOUR call sites** — `test_c19_actions.py` lines 5013, 5065, 5152, 5225 — and
they are four different enclosing tests with four different assertion sets. **The same helper site is
therefore `S1` under one caller and potentially `S2` under another**, which breaks the thing that makes the
current baseline stable: site identity is `(file, function, ordinal)`, deliberately not the line number,
*"because a gate that fails for unrelated reasons is a gate somebody weakens"* — this checker's own
sentence. A per-caller category needs a per-caller identity, and a per-caller identity means one helper
appears in the baseline `N` times and renumbers whenever a caller is added.

**The cheaper build that gets the property without the identity problem.** The question item 3 actually
needs answered is binary and does not need a category per caller:

> Does **any** caller of this helper assert on the value it passes in?

That is **one hop, same module, name-resolved** — build a module-level map of `FunctionDef` by name, bind
each call's positional and keyword arguments to the helper's parameters, and run the *existing*
`_roots` / `_assertion_nodes` machinery on the caller. If any caller asserts on the argument's root, the
helper's guard is reading the result under test and must carry the `S5` proof or be flagged. Site identity
stays `(file, helper, ordinal)`. **No new baseline shape, no renumbering, no cross-module analysis.**

### §1.3 — The verdict, and it is not about line count

**Its own row.** The build above is perhaps 120-180 lines plus calibration, which by itself would not
justify a row. Three things do:

1. **It moves a whole cell.** Sites currently reported as `S4` — *"an honest refusal to answer, and it is
   never gated"* — become gateable. Changing what a category MEANS is not a change you land inside a row
   whose subject is four skip sites.
2. **The five non-result sites must be excluded by a rule, not by luck.** If the new pass flags a
   parameter it cannot resolve, `conftest.py`'s fixtures enter the baseline for reading `backend` and
   `request`, which are environment through and through — and `_run_the_race` enters it for reading a
   CAPABILITY, which is the shape `S0` is named after. **That is `C19-100` again, a legal skip closed by a
   gate**, and it is not hypothetical: the failure is already visible in today's `S4` listing. The rule that
   excludes them ("a parameter with no resolvable caller stays `S4`", and the receiver rule extended across
   the call) has to be calibrated and mutation-tested, not asserted.
3. **The gate's own calibration set has to grow with it**, and the term this row is held to says the
   adversarial round comes before landing. Row 6h's round found five blocking, two of them in fixes made an
   hour earlier. A cell-moving change bolted onto the end of this row would get the round this row's
   subject earned, not the round its own subject needs.

**What is NOT a reason to give it a row: urgency.** The hole's entire result-carrying population is one
site and that site is correct. **This is exposure, not a defect**, and `6H-RUN.md` §0.3 pre-registered it
as known exposure (b) before it fired. It should be built because the next helper written in that shape
will not be correct, not because this one is.

---

## §2 — ITEM 2: THE INSTRUMENTATION, AND THE MISS THAT FOUND A WRONG NUMBER IN A LANDED RECORD

**`P1` was `0`. The answer is `2`. The miss is the result.**

Had `P1` come in at `0` it would have confirmed a prediction derived from a cell that is wrong, and nobody
would have looked at the cell. **The miss is what sent me back to the derivation, and the derivation is
where the defect was.** That is the second time in two rows that the useful finding came from the
prediction failing rather than holding.

### §2.1 — The async three-backend leg, at the floor

```
OO_POSTGRES_DSN=... py -m pytest -q -rs --pyargs ontoloche.aio.contract
979 passed, 316 skipped, 0 failed in 385.71s
```

**Identical to row 6h's landing figure, at `0fcac56`, which is `d3f9a79` plus this row's
pre-registration and its item 3 scope — both docs-only.** `git diff --stat 7f13800..d3f9a79` touches
`STATUS.md`, `docs/DECISIONS-OPEN.md`, `docs/README.md` and the `R104` file and no code at all, so 6h's
`943` / `979` are a valid floor for this row and were not re-taken for their own sake.

**Which of the six fired**, by mapping each baselined site onto its async mirror through
`classify_source` — same function name, same guard text — and matching the mirror's line against the
`-rs` block:

| baselined site | async mirror | fired |
|---|---|---|
| `test_c10_22_a_truncated_collision_scan_is_reported_not_silent#0` | `aio/test_c10_merge_types.py:1192` | no |
| **`test_c10_24_merge_states_a_skipped_identity_guard_too#0`** | **`aio/test_c10_merge_types.py:1321`** | **YES** |
| `test_c12_21_a_word_a_tombstone_answers_to_is_not_free_at_import_types#0` | `aio/test_c12_foundry_import.py:1067` | no |
| `test_c12_24_a_skipped_identity_guard_says_so#0` | `aio/test_c12_foundry_import.py:1209` | no |
| `test_c3_27_the_confidence_is_the_MIN_of_both_halves#0` | `aio/test_c3_resolve_type.py:1289` | no |
| **`_tombstone_holding#0`** | **`aio/test_c4_propose_type.py:460`** | **YES** |

```
SKIPPED [1] aio/test_c10_merge_types.py:1321: this backend refused for another reason (cannot_record_override)
SKIPPED [1] aio/test_c4_propose_type.py:460:  this backend cannot retire the holder (cannot_record_override)
```

**The two that fired are exactly the two the brief authorised, and both fired as `cannot_record_override`
— the one reason the narrowed guard of §0.2 keeps as a skip.** The four unobserved sites fired nowhere on
this leg either.

### §2.2 — Why `P1`'s derivation was unsound, and it is not that I guessed badly

`P1` step 4 read: *"the async three-backend leg is the mirror of the leg that fired 0."* That step is only
sound if `6H-RUN.md` §3.2's `0` for `sync, three backends` is right, and **it cannot be**, for a reason
that needs no re-run to establish.

**[Observed — `ontoloche/contract/conftest.py:35` and `:100`]:**

```python
BACKENDS = ("sqlite", "postgres", "sqlite_minimal")
...
metafunc.parametrize("backend", list(BACKENDS))
```

**Both legs parametrise over the SAME three backends.** The `sync, SQLite only` leg is not a different
selection — it is the same collected set with the `postgres` third skipping inside `adapter_factory` for
want of a DSN. **The `sqlite_minimal` cases are bit-identical between the two legs.**

`sqlite_minimal` is *"a real SQLite store with four of the nine reference tables absent -- five capability
flags declined at once, natively rather than through `DegradedAdapter`"* (conftest's own comment). It is
the backend that declines `stores_events`, and it is the one these two sites fire under.

**So a site that fires under `sqlite_minimal` on the SQLite-only leg MUST fire under `sqlite_minimal` on
the three-backend leg.** §3.2's `2` and `0` are inconsistent **by construction**, before any measurement.
One of the two cells is wrong as a matter of how the suite parametrises.

**What is wrong is a MEASUREMENT, not a judgement.** Row 6h declined to repair four sites it had not
observed firing, and R104 upheld that as the best judgement in the row. **That restraint was correct then
and this measurement makes it more correct, not less** — the four still fire nowhere. A wrong cell in a
firing table did not produce a wrong call; it produced a right call for a partly wrong reason, and it then
produced a wrong prediction in the row that inherited it.

**`6H-RUN.md` is landed and this row does not touch it.** The corrected measurement lives here. The
supervisor holds the correction to `6H-RUN.md` and to `R104` as their own commit, after this row lands,
with the wrong figure left legible.

### §2.3 — The sync three-backend control, and which cell is wrong

```
OO_POSTGRES_DSN=... py -m pytest -q -rs --pyargs ontoloche.contract
943 passed, 316 skipped, 0 failed in 680.20s
```

**The totals reproduce row 6h exactly and the firing table contradicts it.** Same leg, same floor, same
`943 / 316 / 0`, different cell — so nobody can attribute the difference to a different run.

| baselined site | sync SQLite only (6h) | **sync three backends** | **async three backends** |
|---|---|---|---|
| `test_c10_22_a_truncated_collision_scan_is_reported_not_silent#0` | — | no | no |
| **`test_c10_24_merge_states_a_skipped_identity_guard_too#0`** | **fired** | **FIRED** | **FIRED** |
| `test_c12_21_a_word_a_tombstone_answers_to_is_not_free_at_import_types#0` | — | no | no |
| `test_c12_24_a_skipped_identity_guard_says_so#0` | — | no | no |
| `test_c3_27_the_confidence_is_the_MIN_of_both_halves#0` | — | no | no |
| **`_tombstone_holding#0`** | **fired** | **FIRED** | **FIRED** |
| **row 6h §3.2 recorded** | **2** | **0** | *not counted* |

**`6H-RUN.md` §3.2's `0` for `sync, three backends` is the wrong cell. The correct value is `2`.** Both
three-backend legs report **314 distinct skip sites** and fire the same two, both as
`cannot_record_override`.

### §2.4 — ITEM 2's VERDICT: the four stay baselined, on three legs instead of one

**NOT REPAIRED, and now for a materially better reason than the brief could give.** The four sites fired on
**no leg** — not `sync, SQLite only`, not `sync, three backends`, not `async, three backends`. Naming a
capability for a refusal observed nowhere is inventing the cause, and getting it wrong converts a legal
skip into a false failure on a conformant degraded backend. **An unrepaired site with a recorded reason is
a better outcome than a repaired one with an invented cause.**

**And ITEM 1's two are evidenced on three legs**, not on the one superseded leg the brief cited:

```
sync, SQLite only      test_c10_merge_types.py:1337 / test_c4_propose_type.py:467   cannot_record_override
sync, three backends   test_c10_merge_types.py:1337 / test_c4_propose_type.py:467   cannot_record_override
async, three backends  aio/...:1321                 / aio/...:460                   cannot_record_override
```

---

## §3 — ITEMS 1 AND 4, APPLIED AS ONE CHANGE

### §3.1 — What changed, and the shape it took

Four sites, four sync files, plus the four generated mirrors. **All three `_tombstone_holding` copies now
have byte-identical bodies**, which is R104 reading 1 applied in the direction R104 named: **UP**.

```python
gone = registry.retire("alpha", "no longer used", retired_by="user:sd", force=True)
if isinstance(gone, Refusal) and gone.reason == "cannot_record_override":
    assert registry.caps.stores_events is False, (
        "this backend records events, so the refusal is not a capability", gone.detail,
    )
    pytest.skip("NOT REACHABLE: stores_events=False refuses the forced retire ...")
assert not isinstance(gone, Refusal), (
    "the fixture's forced retire refused for a reason no capability explains", gone,
)
assert word in (gone.aliases or ()), (
    "INTERFACE.md 5.8 -- a tombstone keeps its words by design", gone.aliases
)
```

**The narrowing is the whole repair and the bare form would have been a defect** — see §0.2. The
fall-through is what makes narrowing safe: a refusal no capability explains now FAILS the id instead of
skipping it, which is R104's own sentence about what `S5` is for.

### §3.2 — ITEM 4 IS NOT COSMETIC, and this is the measurement that says so

**`test_c12_foundry_import.py:1114` — the c12 twin — fires on 2 live ids** on both three-backend legs. So
R104's reading 1 was right about **a path the suite actually walks**, not about a theoretical symmetry. The
c9 twin is silent on every leg; that does not weaken the reading, it means one of the three was reachable
and unasserted rather than none of them.

### §3.3 — The safety of the narrowing, MEASURED on the pre-repair code

**Every firing of these guards across the whole async leg — seven of them — is `cannot_record_override`.
Zero other reasons, anywhere:**

```
aio/test_c10_merge_types.py:1266     cannot_record_override
aio/test_c10_merge_types.py:1321     cannot_record_override
aio/test_c12_foundry_import.py:1100  cannot_record_override   (2 ids)
aio/test_c12_foundry_import.py:1275  cannot_record_override
aio/test_c3_resolve_type.py:687      cannot_record_override
aio/test_c4_propose_type.py:460      cannot_record_override
```

So the fall-through would have fired on nothing across 979 passing ids. **That is a measurement on the
PRE-repair code and the claim is about the POST-repair code**, so it predicts rather than proves; §4's legs
are what prove it.

### §3.4 — The census, the baseline, and `P2`

**`P2` predicted `4`. The baseline count is `4`. HIT.**

| cell | before | after | why |
|---|---|---|---|
| `S2-RESULT-UNDER-TEST` | 6 | **4** | the two authorised sites left |
| `S5-PROVEN-ENVIRONMENTAL` | 7 | **11** | **+4 — exactly the four repaired, each `S5` by name** |
| `S1-SETUP-RESULT` | 49 | **47** | the two twins moved out of `S1`, not into `S2` |
| `S0` / `S3` / `S4` | 60 / 1 / 16 | 60 / 1 / 16 | untouched |

The `written` guard in all three helper copies stayed `S1`, as §0.4 derived: nothing added reads `written`.
`--write-baseline` accepted the lowering as **REPAIRED** rather than **DE-ASSERTED** — the enclosing
functions went UP in assertion count, which is the check `_leaving_verdict` exists to make.

**The four sites left in the baseline are exactly item 2's four unobserved sites.**

### §3.5 — The mirror, checked the way section D requires

```
git diff --stat origin/main -- ontoloche/contract      ->  4 files, 95 insertions(+), 8 deletions(-)
git diff --stat origin/main -- ontoloche/aio/contract  ->  4 files, 95 insertions(+), 8 deletions(-)
```

**The mirror moved by exactly the amount the source moved, file for file.** `unasync.py` reporting
*"wrote 4 of 25 files"* is NOT this check and is not offered as one — it is the generator's own account of
what it did. The check that the mirror AGREES is `test_generated_matches_source.py` on the async leg.

The per-file split is itself a check: `test_c4_propose_type.py` gains **24** lines against **27** for its
two twins, and the 3-line difference is exactly the fixture assertion the c4 copy already had and the other
two did not. **If that number had come out equal, item 4 would not have done anything.**

---

## §4 — THE SUITE AT THE FINAL STATE

Run **one at a time, never in parallel**, by §0.7's own commands. The four static gates were run
concurrently with one leg, which inflates that leg's wall clock and cannot change a pass or a fail.

| leg | floor | **final state** | delta |
|---|---|---|---|
| sync, SQLite only | 527 / 731 / 0 at `e548541` | **528 passed, 731 skipped, 0 failed** (309.34s) | **+1 passed** |
| sync, three backends | **943 / 316 / 0** (680.20s, taken by THIS row at `0fcac56`) | **943 passed, 316 skipped, 0 failed** (688.54s) | **0** |
| async, three backends | **979 / 316 / 0** (385.71s, taken by THIS row at `0fcac56`) | **979 passed, 316 skipped, 0 failed** (372.06s) | **0** |

**The `+1` on the SQLite-only leg is row 6h's gate-runner, not this row's.** That leg's floor is
`e548541`, five commits back, because 6h did not re-run it — §3.5 of `6H-RUN.md` says so and this row does
not pretend otherwise. Between `e548541` and `d3f9a79` the only code change is 6h's own, which added the
runner; `git diff --stat 7f13800..d3f9a79` is docs-only. **So 527 to 528 is fully accounted for and this
row contributed none of it.**

**The two three-backend floors were taken by THIS row at `0fcac56`, not inherited.** That is the whole
reason §2.3 can say which of 6h's cells is wrong.

### §4.1 — CRITERION 5, and the thing it was set to catch

**316 skipped before, 316 skipped after, on both three-backend legs. Zero drift, so there is nothing to
explain.**

§0.5 predicted that if this number moved it would move DOWN, because narrowing a guard can only skip fewer
ids. **It did not move at all, and the reason is §3.3's measurement: there was no id skipping on any other
reason for the narrowing to take away.** The supervisor's `answers-2` warned to expect ids that used to
skip on some other refusal reason now falling through to the assertion and FAILING. **That hypothesis is
now tested rather than assumed on both sides: it was measured false on the pre-repair code and confirmed
false on the post-repair code.**

The four repaired sites skip with their new reasons in exactly the pattern they fired in before:

```
test_c10_merge_types.py:1352     1 id    NOT REACHABLE: stores_events=False refuses the acknowledgement ...
test_c12_foundry_import.py:1128  2 ids   NOT REACHABLE: stores_events=False refuses the forced retire ...
test_c4_propose_type.py:481      1 id    NOT REACHABLE: stores_events=False refuses the forced retire ...
test_c9_retire.py:1751           0 ids   (silent on every leg, before and after)
```

### §4.2 — The five gates

| gate | result |
|---|---|
| `check_links.py` | **exit 0** |
| `check_spec_drift.py` | **exit 0** |
| `check_merge_guard.py` | **exit 0** |
| `check_capability_matrix.py` | **exit 0** |
| `check_skip_census.py` | **exit 0** |

**This is this row's run. The supervisor runs them again before closing the row, and that run is the one
that counts** — "landed" means verified on `origin` by `git ls-remote`, never a row's own word for it.

### §4.3 — CRITERION 6, both halves, because the first half alone is not the check

**Half one — the diff:**

```
git diff --stat origin/main -- ontoloche/contract      ->  4 files, 95 insertions(+), 8 deletions(-)
git diff --stat origin/main -- ontoloche/aio/contract  ->  4 files, 95 insertions(+), 8 deletions(-)
```

**Half two — the agreement:** `ontoloche/aio/contract/test_generated_matches_source.py` **ran and passed on
the final async leg.** It does not merely check that the files look regenerated: it loads `tools/unasync.py`
and **regenerates the whole tree in memory, comparing byte for byte.** It is absent from the `-rs` skip
block on both the floor and the final leg, which is how this row knows it RAN rather than skipping — the
test skips itself from an installed wheel where `tools/` is not shipped, and a skipped anti-drift check
reads exactly like a passing one in a totals line.

**`unasync.py` was run ONCE, as a generator, to produce the mirror. It was never run to verify anything.**

---

## §5 — LANDING, AND WHAT THIS ROW DID NOT DO

### §5.1 — The two predictions, recorded at equal length because a hit is not more virtuous than a miss

**`P1` predicted `0`. The answer is `2`. MISSED.** The derivation's step 4 inherited `6H-RUN.md` §3.2's
`sync, three backends = 0` and reasoned the async leg mirrors it. The step was unsound because the cell was
wrong, and **the miss is what sent me to the cell.** A hit would have confirmed a prediction resting on a
wrong number and nobody would have looked. §2.2 and §2.3 exist because `P1` failed.

**`P2` predicted `4`. The baseline count is `4`. HIT.** Its four derivation steps were each right for the
reason given: `count` must equal `len(sites)`; two entries left by gaining a capability proof in the skip's
own branch; **no entry entered**, because the same commit that made the twins `S2`-eligible also made them
`S5`; and the `written` guard stayed `S1` because nothing added reads `written`. §3.4's census confirms all
four.

**The miss produced the better finding and the hit is the one that looks like success.** Both are here at
the same length on purpose.

### §5.2 — NOT DONE, deliberately, and each with its reason

- **Item 2's four sites are NOT repaired.** They fired on **no leg of three**. Naming a capability for a
  refusal observed nowhere is inventing the cause, and getting it wrong closes a legal operation on a
  conformant degraded backend. They stay baselined with a recorded reason.
- **Item 3's checker is NOT built.** Scoped in §1, verdict **its own row**, and the reason is the identity
  scheme rather than the size: a checker that follows values across call boundaries makes one helper `S1`
  under one caller and `S2` under another, which `(file, function, ordinal)` cannot express. **The baseline
  itself has to change first.** The cheaper build is named in §1.2 so the next row starts from a scoped
  option rather than from the whole problem.
- **`6H-RUN.md` is NOT edited.** Row 6h is landed and its session is closed. The corrected measurement lives
  here; the supervisor corrects `6H-RUN.md` and `R104` as their own commit after this row lands, with the
  wrong figure left legible.
- **The kill-row count stays TWENTY-THREE.** Nothing here merges a capability predicate or collapses two
  words onto one identity. Suite integrity is not meaning destruction.
- **The governance register stays at ONE.** `Q101` and per-key severity are the founder's and are open.
- **No ruling is minted.** §0.2 and §0.3 contradicted the brief on evidence and were accepted without one.

### §5.3 — The defect shape this row met three times

**`C19-100` — *it closed a legal operation* — was waiting in three separate plausible next steps:**

1. **The brief's authorised repair line**, asserting `stores_events is False` under a bare
   `isinstance(gone, Refusal)`, at a site whose own skip message reads *"this backend refused for another
   reason"*.
2. **Item 2's four unobserved sites**, where naming a capability for an unseen refusal is the same act at a
   different door.
3. **A naive item 3 checker**, which would flag `_run_the_race(first, ...)` — a guard reading
   `first.capabilities().stores_proposals`, the canonical legitimate environment guard — as a
   result-conditioned skip.

**Row 6g re-created this defect at three doors on 2026-09-07 while trying to honour the ruling against it.**
Three near-misses in one row, in three different shapes, is not caution being rewarded — it is a defect that
is genuinely easy to re-commit, and the thing that caught all three was measuring before naming.
