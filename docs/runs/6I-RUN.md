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
