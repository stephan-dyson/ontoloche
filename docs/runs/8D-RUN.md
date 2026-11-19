# 8D-RUN — roadmap row 8d: the type-surface defect row (D14 first, then B5-1 and B5-2)

**Status:** in flight. **Opened** by the supervising session on 2026-11-19 under the founder's instructions *"keep the project moving forward"* (2026-11-12) and *"you don't need my permission to move to the next item on the roadmap"* (2026-11-18). **Brief:** [`handoffs/2026-11-19-row-8d-type-surface-defects-brief.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/handoffs/2026-11-19-row-8d-type-surface-defects-brief.md). **Fixes:** D14 ([`8B-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8B-RUN.md) §2.5 finding 10, probe line D14) and B5-1 and B5-2 ([`8C-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8C-RUN.md) §2.5). **Branch:** `agent/row-8d`, cut from `main` at `add906f`, local only.

**Claim tags:** **[Observed]** seen directly in this repo, in a command's output, or on a page opened this row · **[Inferred]** a reasonable read · **[Assumed]** believed, untested · **[guess]** an inference not checked.

---

## §0 — PRE-REGISTRATION, committed before any code and any test

This section is the row's first commit. Every prediction below is made from the brief, `8B-RUN.md` §2.5, `8C-RUN.md` §2.5, `INTERFACE.md` §2.5a, §2.10 and §12, the probe, and the shipped code at `add906f`. A wrong prediction stays here and is scored as a miss in §1.

### §0.1 — What was observed before this section was written

1. **D14 reproduces as recorded.** **[Observed]** `properties_baseline_probe.py` on `add906f` prints `D14 alias import over a tombstone with successor ()`, `D14 live alias holders of zip_code ['post_code']` and `D14 reinstate zip_code successor_active`.
2. **D14 by kind.** **[Observed]** in a scratch run of the probe's five calls: for `entity`, `property`, `value_set` and `kind="action"` rows the import of `post_code` with `aliases=["zip_code"]` is written `active` with `warnings=()`, and `resolve_type("zip_code", kind=k)` answers `existing postal_code` (the successor) at 1.0 (`action`: confidence `None`). For `predicate` the `retire(successor=)` itself is refused `predicate_merge`, so no tombstone with a successor exists and D14 is unreachable, as 8B §2.5 finding 10 said. `edge` was not tried yet.
3. **The defect site.** **[Observed]** `import_types` asks three guards of an incoming alias: `_alias_identity_breach`, `_alias_clash` (live rows) and `_retired_holder` (a retired row's **aliases**, never its name). `_retired_holder`'s own comment says the tombstone's **name** is skipped on purpose, because writing a retired name as another row's alias is the succession `C12-09` blesses. Nothing asks whether that tombstone has a **successor** that is live, which is the only case where the word ends with two live claimants.
4. **A second door reaches the same state.** **[Observed]** in scratch: an import of a `deprecated` `post_code` with `aliases=["zip_code"]` is written `retired` with `warnings=()`, and `reinstate("post_code")` then returns it `active` with `warnings=()`. `zip_code` again has two live claimants. `reinstate`'s `_alias_clash` reads live rows only, and `zip_code` is retired.
5. **What does not warn today in the neighbouring shapes.** **[Observed]** in scratch: a successor chain `a_w -> b_w -> c_w` (c live) and an import of `d_w` aliasing `a_w` is written with `warnings=()`. `retire(zip_code, successor=post_code)` and then an import of `post_code` aliasing `zip_code` is written with `warnings=()`, and that one is correct: one claimant.
6. **B5-1 and B5-2 reproduce.** **[Observed]** in scratch, `faux_employee` (whose `Employee` maps the absent `fooSpt` onto `fullName`) plus a hand-added shared property type `FooSpt` (from `faux_legacy`'s `fooSpt`, apiName changed): the dry run reports `unresolved_shared [{'shared': 'foo_spt', 'why': 'not_in_document'}]` and the planned `FooSpt` item as `foo_spt would_write`; the real run writes `FooSpt` as `foo_spt` and reports `unresolved_shared []`, with no `property_reference_*` warning on `employee`. The slot is bound to `FooSpt`'s row and nothing says so.
7. **Where B5 sits.** **[Observed]** `Registry._foundry_unresolved` looks a reference's target up by `(kind, apiName)` in the plan. An absent apiName gives `target = None`, the dry run answers `not_in_document`, and the real run asks the store, which by then holds the twin's row under the same word. R110's hold (`foundry._hold`) groups planned items by `(kind, word)` and never sees the absent apiName. The same lookup serves the `interface` (predicate) references and the `src`/`dst` entity references of a link, so the shape is not specific to shared property types [Inferred].

### §0.2 — The D14 fix, stated so the predictions have a design to be wrong about

1. **A warning, `alias_word_succeeded:<word>:<live claimant>`**, on the `TypeEntry` `import_types` returns when a written row carries, as an alias, a word that is the **name** of a retired row of the **same kind and namespace** whose successor walk ends at a **live** row other than the one being written. `<live claimant>` is that row's name. The value is new and goes into `WARNING_VALUES` and `INTERFACE.md` §5.4's table in the same change.
2. **The same warning at `reinstate`**, on the `TypeEntry` it returns, for the same condition over the reinstated row's aliases.
3. **The walk is the reader's.** It follows `successor` within the kind and namespace, up to `_IDENTITY_CHAIN_CAP`. A dead end (no live row at the end) is one claimant and is not warned. A walk that ends at the row being written is one claimant and is not warned. A walk that is cut off by the cap is warned with `?` as the claimant, because Rule U: *we could not finish* is not *there is none* [the `?` spelling is this row's call].
4. **Nothing else changes.** The alias is still written, `resolve_type` still answers the successor, and `reinstate` of the tombstone is still refused `successor_active` while the successor is live. These are the **defaults in force**, pinned by the same test.
5. **What goes to the founder:** whether the alias write (and the `reinstate`) should be **refused**, or the reader should **answer the alias holder** instead of the successor. That decides what the registry refuses or holds, so it becomes `DECISIONS-OPEN.md` item 35 with options and a recommendation. It is non-blocking: the default in force exists.

### §0.3 — The B5 fix

1. **In `_foundry_unresolved`, a reference whose apiName the document does not define, while a planned item of the target kind converts to the same word, is resolved against that item** (its *twin*), so the dry run and the real run read the same target and agree: `held:<reason>` when the twin is held, `retired` when it is deprecated, resolved when it will be written, and `refused:<reason>` on a real run that refused it (a dry run cannot predict a guard's refusal, 2.5a, as for any defined target).
2. **The case is reported on the plan and on the result**, identically on both runs: the referencing item's `detail["bound_by_conversion"]` lists `{<label>: <word>, "api": <absent apiName>, "bound_to": <twin apiName>}`, and the item carries the warning **`reference_bound_by_conversion:<label>:<absent apiName>:<twin apiName>`**, on a dry run and a real run alike. A new value, in `WARNING_VALUES` and `INTERFACE.md` §5.4 in the same change. The properties report's `unresolved_shared` keeps its meaning (not live after the import).
3. **Only when the twin is not held.** A held twin binds nothing, so the reference reads `held:<reason>` and no `bound_by_conversion` is written.
4. **No hold changes.** Whether the import should **hold** the referencing item (an R110-style hold extended to an absent apiName) is a refusal question and goes to the founder as `DECISIONS-OPEN.md` item 36, default in force: report, as built.

### §0.4 — Order, and what "red first" means here

1. This section, committed alone.
2. **D14:** one commit with the failing contract test, then one commit with the fix. The test asserts, on all three backends, for `entity`, `property`, `value_set`, `edge` and an action row: two live claimants after the import (the default pinned), the reader answering the successor, `reinstate` of the tombstone refused `successor_active`, and the new warning. For `predicate` it pins that the `retire(successor=)` is refused `predicate_merge`. **Predicted red** on the warning alone, on every kind but `predicate`, on all three legs. Then the `reinstate` door, the same way.
3. **B5-1 and B5-2:** one commit with the failing test, then the fix. **Predicted red** on the dry run's `not_in_document` and on the missing warning.
4. **Row 8c's other round-5 MINORs** (§0.7), each a failing test then the fix, or a recorded reason it is left.
5. `DECISIONS-OPEN.md` items 35 and 36, the probe and the fixture snapshot, the mutation script, the async mirror (`tools/unasync.py`), the full suite and the five gates, then the adversarial loop (§0.9).

### §0.5 — Design tests (brief §3), predicted

| test | before the fix (`add906f`) | after the fix |
|---|---|---|
| probe line `D14 alias import over a tombstone with successor` | `()` | `('alias_word_succeeded:zip_code:postal_code',)` |
| probe lines `D14 live alias holders` and `D14 reinstate zip_code` | `['post_code']`, `successor_active` | unchanged, now in the probe's asserted set as the default in force |
| B5-1 on `faux_employee` plus `FooSpt`, dry run | `unresolved_shared` `not_in_document`, no warning | `unresolved_shared []`, `employee` warned `reference_bound_by_conversion:shared:fooSpt:FooSpt`, `bound_by_conversion` in its detail |
| the same, real run | `unresolved_shared []`, no warning | identical to the dry run's report, plus the written entry's own warnings |
| the interface case: `FooInterface` renamed `fooInterface` in the document, `Employee` still implementing `FooInterface` | dry `not_in_document`, real resolves silently | both warned `reference_bound_by_conversion:predicate:FooInterface:fooInterface` |
| the five Foundry fixtures, dry and real, every item's outcome, reason, warnings, detail and the properties report | — | **byte-identical** to `add906f` on all five. None of them has an absent apiName with a converting twin [Inferred from 8C §2.5 B5-1: it needs a hand-added twin] |
| UC1 to UC3 (`C13`, `C14`, `C21-16`, `C21-17`) | green | green, unchanged |
| the reserved-rule probe lines (2.10-17 to 2.10-21) | at their recorded values | unchanged. D12's `alias import over a retired property/entity, warnings` stay `()`: the tombstone there has no successor |

The fixture comparison is a new snapshot tool, `docs/tools/type_surface_snapshot.py`, run at `add906f` before any code changes and again at the end.

### §0.6 — Kill row: the doors the fixes touch, and where the shapes are predicted to recur

**The D14 shape:** *a write leaves one word with two live same-kind claimants, one by alias and one by succession, and nothing says so.* **The B5 shape:** *a reference is bound to a row other than the one its source named, and the plan holds the evidence and says nothing.*

| # | door | touched? | prediction before any lens runs |
|---|---|---|---|
| K1 | `import_types`' alias write | **yes**, warns | the defect site |
| K2 | `reinstate` of a row that carries the word as an alias | **yes**, warns | **a recurrence**, §0.1 item 4, closed by the same warning |
| K3 | `retire(successor=)`'s alias transfer and `merge_types`' alias move | no | **predicted not a new source**: each moves aliases a live row already holds, so the two claimants already existed (K1 or K2 made them, warned). A move does not re-warn [this row's call: the warning is about the write that creates the state] |
| K4 | `propose_type` and `approve` (`_write_approved`) | no | **predicted unreachable**: neither takes `aliases` |
| K5 | the reader's successor walk (`resolve_type`, rule 2.10-11's reader) | no | answers the successor, as today, pinned. 8B finding 2's dead-end chain stays one claimant |
| K6 | `reinstate` of the tombstone itself | no | refused `successor_active` while the successor lives, as today, pinned. After the successor is retired, refused `alias_collision` by the alias holder, as today |
| K7 | `_foundry_unresolved` for `shared`, `predicate`, `src` and `dst` references | **yes**, the B5 fix | the B5 site. Predicted to cover the link endpoints by the same code path, with one test case for an edge endpoint |
| K8 | an absent apiName whose word a **stored** row (from an earlier import of a different apiName) already holds | no | **a recurrence predicted and left**: the store's row resolves the reference by design (round 3 of 8a: *the store first*), and its `imported_from.apiName` is the only evidence. Recorded, not fixed: reading provenance at that door is new behaviour |
| K9 | R110's hold (`foundry._hold`) | no | unchanged; extending it is item 36 |
| K10 | the type-identity kill row (a capability predicate merged as a duplicate) | no | **predicted zero new trips**: the predicate version of D14 is refused at `retire`, and `check_merge_guard.py` Part A finds no new identity writer (the warnings write no field) |

### §0.7 — Row 8c's other round-5 MINORs, and what this row does with each

| # | minor | plan |
|---|---|---|
| A5-1 | the `{"dataType": value}` wrapper leaks into the carry on a shared or invalid-name property | **left**: hand-built shape, the value is kept |
| A5-2, C5-2 | a non-`str` `description` or `displayName` lands nowhere | **left**: the SDK types both `str`. Keeping it would mean choosing where an ill-typed value goes, which is new behaviour |
| C5-3 | a non-object shared property type lands `opaque`, `"{}"` | **left**: hand-built, as A5-1 |
| A5-3, C5-7 | a list `primaryKey` repeating a name plans a row its own validator refuses | **left**: making the dry run hold it is a hold, and the real run already refuses visibly |
| C5-1 | a `$primaryKey` property apiName is overwritten in the carry | **left**: [unverified] whether Foundry permits `$` in an apiName |
| C5-4 | two shared property types mapped onto one property list the surviving word twice in `unresolved_shared` | **fixed**: deduplicate the entries, test first. Small, changes only a report |
| C5-5 | a non-`str` `sharedPropertyTypeMapping` target | **left**: kept in the carry, nothing lost |
| C5-6 | an empty non-map `properties` reads as empty, not `TypeError` | **left**: raising would refuse a document that imports today |
| A5-4 | `required=False` on a key slot under one `DegradedAdapter` projection | **left**: no shipped backend reaches it |
| A5-5 | `source_type` serialises with `default=str` | **left**: only a Python caller reaches it |
| C5-8 | a run-record wording slip | corrected in 8C already |

### §0.8 — What goes to the founder

**Predicted: two items, neither blocking.** Item 35 (D14: warn, refuse the write, or answer the alias holder) and item 36 (B5: report, or hold the referencing item). Each gets options and a recommendation, and the default in force is built and pinned.

### §0.9 — The stopping rule and the round cap

Row 6j's adopted criterion (`6J-RUN.md` §5 item 10): the loop ends when a full round finds no in-scope code MAJOR reachable by a shape a contributor would plausibly write, measured by whether the shape, or anything structurally like it, appears anywhere in the live suite. For spec text this row edits, row 8b's adaptation applies: a spec MAJOR counts when it is reachable using only calls and shapes the documents print. A round that produces a MAJOR or BLOCKING fix is followed by a full round that sees it, the last round sees the final code, tests and text, and nothing reviewed is edited while a lens is running.

**Cap: three rounds plus a confirming round** (the brief's). Each round runs three fresh lenses: the build implementer (the fixes against `INTERFACE.md` and this section), the door adversary (K1 to K10, each by mutation or construction), and the fidelity reviewer (every number in §1 recomputed, every red commit re-run). **At the cap:** if round 3 finds a reachable in-scope MAJOR, the row fixes it and runs round 4, the confirming round. If round 4 finds one, the row lands not clean with the finding recorded here and in `STATUS.md`. If a fix lands after the last round, §2 says so plainly.

### §0.10 — The commands this row will run

```
py docs/tools/properties_baseline_probe.py [--assert]
py docs/tools/type_surface_snapshot.py --write <file> | --compare <file>
py docs/tools/type_surface_mutation_sweep.py [--only <substring>]
py tools/unasync.py
py -m pytest --pyargs ontoloche.contract ontoloche.aio.contract     # three legs, OO_POSTGRES_DSN set
py docs/tools/check_links.py
py docs/tools/check_spec_drift.py
py docs/tools/check_merge_guard.py
py docs/tools/check_capability_matrix.py
py docs/tools/check_skip_census.py
```

`OO_POSTGRES_DSN=postgresql://postgres:openontology@localhost:55432/open_ontology` (container `oo-pg`). The full suite takes about 21 minutes, so it runs in the background.

---

## §1 — Results against §0, scored

Every number below is from a command this row ran, and each is **[Observed]** unless it says otherwise. §0 is left exactly as committed at `adb31d0`. Findings from the adversarial loop are scored here where they change a §0 prediction, and listed round by round in §2.

### §1.1 — Red first, per commit

| step | red commit | what failed, and why | green commit |
|---|---|---|---|
| D14 | `bd86531` | `C12-78` and `C12-79`: 11 failures per sqlite-shaped leg, 22 on sqlite and postgres, each on the missing `alias_word_succeeded` warning alone (5 kinds at the import, 1 chain, 5 kinds at `reinstate`) | `8f1c039` |
| B5-1, B5-2 | `3a491fd` | `C12-80`: the shared, interface and endpoint cases on the missing warning, and the held twin reading `not_in_document` where `held:definition_missing` was predicted | `8ec42ac` |
| C5-4 | `0b02ad5` | `C12-81`: `bar_spt` listed twice in `unresolved_shared` | `2fb397b` |
| D14 on a backend keeping no aliases | `783cbf3` | `C12-78`'s `an_alias_the_backend_does_not_keep_is_not_warned`: the warning named a second claimant that `stores_aliases=False` never stored | `45eab75` |
| round 1 (§2) | `0724e83` | `C12-79`'s third door unwarned, `C12-80`'s retired twin reported bound, `C12-78`'s 17-hop chain warned `?` | `4e110dd` |

- **Miss (predicted kinds): the third backend.** §0.4 item 2 predicted red "on all three legs". On `sqlite_minimal` the `retire(successor=)` that builds the tombstone is refused `no_consumer_evidence` (no membership index, and the forced override needs `stores_events`), so D14 cannot arise there. The red commit gates the D14 cases on `indexes_membership` and adds `C12-78`'s `without_a_membership_index_no_successor_can_be_named`, which pins that refusal on minimal and the successful retire elsewhere, with no skip.
- **Hit: `edge`.** §0.1 item 2 had not tried it. It behaves as the other four kinds.
- **Miss (process): `bd86531` was committed without its async mirror.** The same slip as 7D §1.1. `8f1c039` regenerated it, and every later red commit carried its mirror.

### §1.2 — The fixes against §0.2 and §0.3

- **§0.2 item 1 (the import door): a miss, found by the capability matrix.** The first full run on `1ceeec2` failed `check_capability_matrix` for `stores_events=False` (5 failures) and `stores_aliases=False` (10). Two causes. The D14 cases used aliases and `reinstate` (which needs an event trail) as scaffolding without declaring them, so they now carry `requires_capability`. And on `stores_aliases=False` the warning named a second claimant the backend never stored, a Rule U defect in the design. The import door now asks only when the backend keeps aliases (`45eab75`). `reinstate` needs no gate, since such a backend has no dormant aliases to check.
- **§0.2 item 2 (the reinstate door): a hit for the alias holder, and a miss for a door §0 did not name.** Round 1's door lens found that reinstating the retired **end** of a chain, whose first word a live row already holds as an alias, recreates the state with nothing said. §0.6 had K2 (the holder) and K6 (the tombstone) and no row for the successor. Now warned (`4e110dd`).
- **§0.2 item 3 (the walk is the reader's): a miss, found by round 1.** The `?` branch had no test at `1ceeec2`, and the walk stopped one hop short of `resolve_type`'s (the reader takes the first hop and `_IDENTITY_CHAIN_CAP` more), so a 17-hop chain the reader finishes was warned `?`. The walk now takes the reader's hops, in one helper `_succession_claimant` that both doors use. Dead ends stay one claimant, as predicted.
- **§0.2 item 4 (nothing else changes): a hit.** The alias write, the reader and `reinstate`'s `successor_active` are unchanged and pinned.
- **A call recorded:** the tombstone is found by `_word_spellings(word)` (the word and its `identity_key`), so an alias spelled `Zip_Code`-style still finds `zip_code`.
- **§0.3 (B5): items 1 to 4 hit as stated, with one gap closed by round 1.** `_foundry_unresolved` builds `(kind, word) -> planned item`, and a reference whose apiName the plan lacks is resolved against the twin. Round 1's implementer lens found the binding reported when the twin was written retired (DEPRECATED) or refused by the real run, beside an `unresolved` entry for the same reference. A binding now stands only when its reference is not unresolved (`4e110dd`). A refusal is known only on the real run, so the dry run may still report it there, as §0.3 item 1 allows.
- **`check_merge_guard.py` Part A** flagged first `_succeeded_alias_warnings` (`8ec42ac`) and then `_succession_claimant` (round 1) as unknown `successor` writers, its over-broad scan naming any mention of the field. Each reads only, and the verdict now sits on `_succession_claimant`. The checker exits 0.
- **Text:** `INTERFACE.md` §5.4 gains both values (fifty-one to fifty-three, and `FoundryItem` becomes a carrier), rule 2.10-17 and §12 say D14 is warned and routed, and §2.5a gains the twin paragraph and K8's recorded gap. `PACKAGE.md` §6.2 gains `C12-78` to `C12-81` (575 to 579). Round 1's tests extend those four ids and add none.

### §1.3 — Design tests (§0.5)

| test | predicted | observed | score |
|---|---|---|---|
| probe `D14 alias import over a tombstone with successor` | `('alias_word_succeeded:zip_code:postal_code',)` | the same | hit |
| probe `D14 live alias holders`, `D14 reinstate zip_code` | unchanged, now asserted | `['post_code']`, `successor_active`. `--assert` holds 22 lines (19 plus D14's three) | hit |
| B5-1, dry and real | both report it, identical | `C12-80` shared case: the warning and `bound_by_conversion` on both runs, `unresolved_shared []` on both | hit |
| the interface case | warned `predicate:FooInterface:fooInterface` | the same | hit |
| a link endpoint (K7) | covered by the same path | `homeOffice` warned `dst:office:Office` on both runs | hit |
| the five Foundry fixtures | byte-identical | `type_surface_snapshot.py --compare` against `add906f`: **0 differences across 10 reports**, after D14, B5, C5-4 and round 1 | hit |
| UC1 to UC3 | green | see §1.6 | see §1.6 |
| the 19 reserved-rule lines | unchanged | unchanged | hit |

### §1.4 — Kill row (§0.6)

- K1 and K2 are closed by the warning, K7 by the twin resolution.
- **A door §0.6 did not list:** `reinstate` of a chain's retired end (round 1, door lens). Closed by the warning.
- K3 (moves): not tested to the end. The door lens's `merge_types` attempt was refused `no_consumer_evidence` before it moved anything. The prediction stands, unverified.
- K4: **hit, unreachable.** `propose_type` and `approve` take no `aliases` (the door lens read the signatures).
- K5 and K6: unchanged and pinned. The door lens recorded one MINOR against K5's reader that predates this row: spellings sharing one `identity_key` (`Zip_Code`, `zip-code`) can resolve differently from `zip_code` once a row holds one of them as an alias. Each such write is warned. Left, as K5's.
- K8: recorded in `INTERFACE.md` §2.5a and left. K9: unchanged.
- **K10: zero new trips.** `check_merge_guard.py` exits 0 with the reader verdicts recorded.

### §1.5 — Every touched contract id red by mutation

`docs/tools/type_surface_mutation_sweep.py` on `4e110dd`: **15 mutations, 15 killed**, the unmutated copy green first. Seven on `C12-78`, three on `C12-79`, four on `C12-80`, one on `C12-81`. Two mutations are left out as **equivalent**, each commented in the sweep. Removing the tombstone's `successor` test changes nothing, because the walk stops at once when there is no successor. And since round 1, removing the held-twin guard changes nothing, because round 1's filter drops every binding whose reference is unresolved (it survived on `4e110dd`, which is how it was found).

### §1.6 — The suite and the gates

- First full run, on `1ceeec2`: three legs `1 failed, 3555 passed, 1054 skipped` (`0:22:25`). The one failure was `test_every_optional_capability_can_be_declined_alone`, the suite's copy of the capability matrix, which failed as §1.2 records. `check_links`, `check_spec_drift`, `check_merge_guard` and `check_skip_census` exited 0, `check_capability_matrix` exited 1, and `unasync --check` said 27 generated files are current.
- On `45eab75` the capability matrix and the skip census exited 0.
- RUN-ON-FINAL

### §1.7 — Row 8c's other MINORs (§0.7)

C5-4 is fixed (`C12-81`). The other ten (A5-1, A5-2/C5-2, C5-3, A5-3/C5-7, C5-1, C5-5, C5-6, A5-4, A5-5) are left for the reasons §0.7 gives, and no lens in this row reopened any of them. C5-8 was already corrected in 8C.

### §1.8 — What went to the founder

As §0.8 predicted: item 35 (`Q113`, D14: `warn`, `refuse` or `answer the alias holder`, recommended `refuse`) and item 36 (`Q114`, B5: `report` or `hold`, recommended `report`). Neither blocks. The default in force for each is built and pinned. Round 1's third door went into item 35's text, and no new item was needed.

---

## §2 — Adversarial loop

The rule (§0.9): three fresh lenses a round (implementer, door adversary, fidelity), at most 3 rounds and a confirming round. A round is clean when no lens finds a MAJOR.

### Round 1, on `45eab75` plus the §1 draft

| lens | MAJOR | MINOR | what was done |
|---|---|---|---|
| implementer | 1: B5 reported a binding to a twin the real run refused | 4: a DEPRECATED twin, the same. The walk one hop short of the reader's. The import-door warning is stored on the row and can go stale, while the reinstate door's is not. A held referencing item still says bound | The MAJOR and the first two MINORs fixed red first (`0724e83`, `4e110dd`). The stored warning is **left**: the import door stores its warnings as R55's alias warnings already do, and changing what a row stores is outside this row. The held item is **left**: a held item's warnings describe the plan, and the plan did bind it |
| door adversary | 1: reinstating a chain's retired end recreates D14 unwarned | 1: K5's spelling split, predating this row | The MAJOR fixed red first (`0724e83`, `4e110dd`). The MINOR left as K5's (§1.4) |
| fidelity | 2: §1 scored §0.2 item 3 as a hit with no test behind it. §1 omitted the capability-matrix round | 6: rule 2.10-17's tense. §5.4 and PACKAGE missing the `stores_aliases` gate. PACKAGE's mech column read `**4**`. The minimal-backend exception missing from item 35 and §5.4. §0.4 item 4, §0.7 and K4 unscored. A circular comment in the sweep | All fixed in `7e720e9` and this section, except the circular comment, which is left (it points at a section that now exists) |
