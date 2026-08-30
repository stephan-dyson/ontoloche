# 6B-RUN — roadmap row 6b: ACTIONS v0 built, and the identity guards given the review they did not get

**Row:** 6b. **Date:** 2026-08-30. **Repo:** [`open-ontology`](https://github.com/stephan-dyson/open-ontology), `main`.
**What it carries, in two halves that stayed in separate commits:** **(A)** the implementation of [`docs/specs/ACTIONS.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/ACTIONS.md) v0 — a `kind="action"` family, `preflight`, the invocation ledger, `projection`, three adapter primitives and the **58** planned `C19` contract ids; and **(B)** ruling **R53**'s extraction of the identity guards into one function with **R64**'s naming, which the seventh-trip countersignature rules to be *"the review 4c's guards did not get — its first adversarial lens is the extracted function against all the trip records."*
**The kill row tripped a NINTH and a TENTH time in this row**, and they are one defect one branch apart: a guard with nothing on its right-hand side comparing the left against itself, and then — inside the fix for that — a guard reading the consumer set of the row `import_types` is about to overwrite. **The tenth is the sixth trip's diagnosis applied to a FIX rather than to a guard**, which is also the eighth's shape. Full record, for countersignature: [`2026-08-29-3c-rulings-R6-R12.md`](../decisions/2026-08-29-3c-rulings-R6-R12.md); [`ROADMAP.md`](https://github.com/stephan-dyson/open-ontology/blob/main/ROADMAP.md)'s kill row carries it.
**Why it ran next:** row #6 specified ACTIONS.md across three adversarial rounds and **it did not converge** (§19.5). Its own honest verdict was that the next thing to move the document *"is not a seventh lens. It is the `C19` suite, `check_spec_drift.py` pointed at this file, and `check_merge_guard.py` enumerating the callers."* This row is those three things.

---

## 1. The headline, in numbers

| | before (row 4d) | after |
|---|---|---|
| contract ids ([`PACKAGE.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/PACKAGE.md) §6.2) | 249 | **327** — 309 at half A, then 318 → 322 → 327 through the loop (§6) |
| sync suite, one run, three legs | `596 passed, 170 skipped` | **`757 passed`** (post-rename `ontoloche` paths) |
| async suite, one run, three legs | `631 passed, 170 skipped` | **`796 passed`** (post-rename `ontoloche` paths) |
| adapter primitives ([`PACKAGE.md`](https://github.com/stephan-dyson/open-ontology/blob/main/docs/specs/PACKAGE.md) §3.4) | 18 | **21** — `put_invocation`, `get_invocation`, `find_invocations` |
| store version | 4 | **5** — `oo_invocation`, and `oo_event.invocation_id` |
| `Capabilities` flags | 14 | **17** — `stores_invocations`, `stores_invocation_events`, `indexes_invocations_by_family` |
| `Refusal.reason` values **returned by code** | 23 of 30 | **30 of 30** |
| `warnings` values **returned by code** | 29 of 32 | **32 of 32** |
| documents `check_spec_drift.py` reads | 3 | **4** — `ACTIONS.md`, 12 shapes / 4 calls / 10 closed vocabularies / 8 R31 sections |
| `docs/tools/actions_*.py` probe checks | 96 (kit only) | **129** — the same 96, plus **33** asking the SHIPPED registry |
| `ROADMAP.md` kill-row trips | 8 | **11** — the ninth by this row's first adversarial lens (the review ruling **R53** and the seventh-trip countersignature designated as *"the review 4c's guards did not get"*), the tenth by its second, **inside the ninth's own fix** |

---

## 2. Half A — what ACTIONS v0 does, and what it still cannot do

**An action family can now be proposed, resolved against the verbs that already exist, approved or rejected, retired, reinstated and namespaced — because it is a `TypeEntry` and nothing here added a call to `INTERFACE.md` §5.** It declares eight keys; a declaration that breaks a rule is refused at **all three** shipped doors; an invocation of it is gated on preconditions of four closed kinds, on an approval mode of three, and on a tier floor the deployment orders; and every use of it leaves an append-only record saying who invoked it, on what tier, what it declared it would change, and what the host claims it actually changed.

**It cannot execute, schedule, retry, order, roll back, or enforce**, and §4 of the specification says so in the strongest form available because a weaker statement would be a lie of omission. `preflight` can be skipped. What makes the gate not-nothing is countable rather than rhetorical: `invocations(gate_verdict="refused", outcome="applied")` returns every override, and the three filters that query needs are on the primitive rather than above it — which is the difference between a floor and a zero.

### 2.1 What ACTIONS.md said the build row owed, item by item

| §14 owed | shipped |
|---|---|
| a `C19` group of **58** ids, section-mapped | **60** — the 58 planned, plus `C19-59` (UC1's arithmetic through `projection`) and `C19-60` (the override census at a size that would have returned zero before the push-down) |
| **4** `prose-only` tags whose reasons are the argument | unchanged and now **gated**: `check_spec_drift.py` fails a rule with neither an id nor a tagged reason, in all eight sections |
| the four probes' checks **transposed into the suite rather than re-derived** | done — and the probes additionally gained a **shipped-registry leg**, so the kit's verdicts stopped being claims about a model the package does not import |
| `check_spec_drift.py` pointed at this file **in the same change that lands the tests** | done, and it caught two drifts on its first run (§3, D-6b-1) |
| `read_events(invocation_id=)` with **the six implementations and the `oo_event` column** | done, in one change — the order §9.1 spent a round trip learning |

---

## 3. Deviations — every place the implementation could not follow the specification as written

Standing constraint 7's rule: recorded rather than designed away.

| id | what the spec said | what shipped, and why |
|---|---|---|
| **D-6b-1** | §9's printed `InvocationRecord`, column for column | It was **missing `declared_policy` and `family_version`** — the entirety of round 2's gate-to-record fix, which §19.4 records round 3 as having corrected *in four places*, none of them this one. So a third-party backend built from §9 alone had two columns fewer than rules 3-7 and 3-8 require, and the ledger it produced could not answer *"was Haiku permitted to run this unattended in March?"* at all. **Found mechanically, by `check_spec_drift.py` reading this block for the first time** — §14's whole argument arriving as evidence rather than as a plan. The document is amended; the code is what the rules require |
| **D-6b-2** | §2.4's table: `predicate_holds` is *"answered by `predicates()` / `list_types(predicate=…)`"* | The obvious reading — `predicates(of=subject)` and look for the word — **can never answer `False`**. `INTERFACE.md` §5.6 makes any FILTERED listing incomplete and `of=` is a filter, so every miss is Rule U's unknown and rule **2.4-4**'s *"a precondition that does not hold"* has no reachable state at all. It is answered instead by an **unfiltered** `predicates(namespace=…, include_retired=True)` and the target predicate's own `extent` + `why_extent_incomplete`, which is Rule U already published by the read: in the extent → `True`; demonstrably absent from a fully-read extent → `False`; extent unreadable, or the predicate unregistered, or the subject unregistered → `None` plus the read's own sentence. Contortion **ACT6**'s twin, in the kind next door, and the same `_extent` every identity guard uses — so ruling **R54**'s identity resolution is inherited rather than re-implemented |
| **D-6b-3** | §5.2: a `review`-mode invocation *"is enumerable by `invocations(unreviewed=True)` **until an `invocation_reviewed` event is appended**"*; §3.5 mints the event value | **Nothing in §6's four calls appends one**, so the read is unreachable and the queue can never drain. `review_invocation(invocation_id, *, reviewed_by)` is a **fifth** call the specification does not have. It is deliberately not folded into `record_invocation`: a review is a second act by a second person at a later time, and a parameter on the write call would let the actor who ran the action mark their own invocation reviewed. It reuses `action_family_unknown` for an unknown id rather than minting a twenty-ninth `Refusal.reason` in a build row — §7 argued `unknown_invocation` and declined it *because no call in ACTIONS.md names an existing invocation by id*, and this call does. Raised as a question rather than decided here |
| **D-6b-4** | §3.1: `family_version` is *"bumped at every declaration door"* | It is **counted from the append-only event log**, not stored as a ninth attribute. A ninth key would be a second home for a fact the log already holds (EDGES.md §2.4's rule), and on a backend with `stores_events=False` it would be a number nothing could check. On such a backend `_family_version` returns `1` for every read, which is honest: that registry cannot tell one generation from another, so it **never emits `declaration_amended`** rather than emitting it wrongly. Rule U — *we cannot tell* is not *it has not changed*. `C19-56` skips there with that reason |
| **D-6b-5** | §9: the façade derives `compensated_by` from the store's forward pointer | The first cut derived it by **walking the ledger**, bounded — and round 1 then found the bound reporting the wrong `outcome`, round 2 found the sentence dropped at the second call site, and round 2 measured the walk at **200,020 row reads for twenty returned rows**. Three defects, one cause: *a derivation the store could answer was being computed above it.* Primitive 21 gains a **`compensates` filter** and the derivation is one indexed lookup — no bound to lie about, no sentence to drop, no walk. That is round 2 of the SPEC row's own finding one derivation along: **the reads with no push-down were exactly the governance reads.** `C19-62` |
| **D-6b-6** | the brief: *"each item = one commit"* | Items **1 and 2** (the declaration door and `preflight`) landed in one commit, because `preflight` lives in the same file as the door and the two could not be staged apart without committing untested code in between. Items 3, 4, 5 and 6 kept their own. Recorded rather than quietly merged |
| **D-6b-7** | §6.3: `invocations` reports `indexes_invocations_by_family=False`'s sentence | The first cut stamped that sentence — and therefore `complete=False` — on **every** read, including a complete unfiltered census. §8 says the flag means *"correctness is unchanged... a scan **may hit `limit`**, and **then** `complete=False` with `why_incomplete` = this sentence"*, so it belongs only where a family filter was applied **and** the page was bounded. Saying *incomplete* about a complete answer is Rule U pointing the wrong way, and a `why` that never turns off is the noise row 3d ruled against for the durability warning. **Found by `check_capability_matrix.py` within one run of being written** |
| **D-6b-8** | §2.7: `payload_schema` names a schema keyed `(namespace, "action", <family name>)` | **That is the key ruling R10 already gave** the name-level schema governing the family's OWN eight declaration keys — one key, two dicts. Contortion **ACT1** predicted it in the abstract (*"it works because the two objects never share a store, which is a fact OUTSIDE the mechanism"*) and they share `oo_attr_schema`: registering the schema made the family **unregisterable**. `ACTION_PAYLOAD_KIND = "action_payload"` is `edges.EDGE_PAYLOAD_KIND` one kind along — **deviation D-4c-1 reproduced by the row that inherited the mechanism.** `C19-63` |
| **D-6b-9** | §9: the façade derives `compensated_by`; the primitive holds only the forward pointer | Primitive 21 gains a **`compensates` filter**, so the derivation is one indexed lookup rather than a walk. Not in the specification, and taken because the walk produced three defects across two rounds — a bound that reported the wrong `outcome` (`C19-62`, round 1), a Rule-U sentence dropped at the second call site (round 2), and **200,020 row reads for twenty returned rows**. §9 and PACKAGE.md §3.4 amended in the same change |
| **D-6b-10** | the brief: both suites on three legs, above the floor | **Obtained for sync (`746 passed, 238 skipped`) with ONE nonbinding failure, and the failure is environmental.** `test_every_optional_capability_can_be_declined_alone` runs the whole suite eighteen times in subprocesses; it **wedged** under contention with an unrelated `pytest -n 8` run sharing the machine, and `check_capability_matrix.py` run standalone immediately afterwards exits **0** with *"every optional capability can be declined alone"*. It is `nonbinding` under ruling **R2** and excluded from the conformance verdict by design. **The async three-leg number was not obtained in this round** — recorded rather than estimated |

---

## 4. The rule → id mapping (standing constraint 8)

**`check_spec_drift.py` now reads `ACTIONS.md` as well as `INTERFACE.md`, `PACKAGE.md` and `EDGES.md`**, and row 6b is the row that ruling **R31** named by name: *"and to #6 (actions spec) as it is written."* All **eight** sections are under the gate — not a subset, because that document's round 1 relocated its eight tables precisely so `_section` could reach them, and thirty of forty-seven rules had been unreachable before it did.

| section | rules | ids | prose-only |
|---|---|---|---|
| §2.2 the declared shape | 5 | `C19-26` … `C19-28`, `C19-44` | 1 — an absence has no test that knows what to look for |
| §2.4 preconditions | 9 | `C19-01` … `C19-05`, `C19-45` … `C19-47` | 1 — **ACT4**, routed to Phase 3 by **R22**/**R41**/**R60** |
| §2.5 effects | 10 | `C19-06` … `C19-12`, `C19-48`, `C19-49`, `C19-55` | 0 |
| §3 invocations | 8 | `C19-29` … `C19-33`, `C19-56`, `C19-57` | 1 — a value that does not exist |
| §5.2 the gate | 7 | `C19-13` … `C19-18`, `C19-50` | 0 |
| §6 the calls | 8 | `C19-34` … `C19-38`, `C19-51`, `C19-52` | 1 — **R25**/**R58** routed paging |
| §8 capability flags | 5 | `C19-39` … `C19-43` | 0 |
| §10 the ceiling | 10 | `C19-19` … `C19-25`, `C19-53`, `C19-54`, `C19-58` | 0 |
| **total** | **62** | **58** | **4** |

**Two more ids came from the build itself**, which is what the other rows' groups did too: `C19-59` drives UC1's 127/128 arithmetic through the shipped `projection`, and `C19-60` drives §4's override census at a size that would have returned zero before round 2's push-down landed.

### 4.1 Which existing ids had to change, and this is the notice the brief requires

**Three** — and none of them is a kill-row id. This section was written before any of them was touched.

| id | what changed, and why it is a fixture or a count rather than a rule |
|---|---|
| `C17-01` | asserted `len(primitives) == 18`. It is **21**, and the assertion's own docstring says the number is hard-coded *"on purpose: this test's job is to notice that the protocol GREW"* — so noticing is the test working, and the message now says why both increments are evidence that a family needs no primitive |
| `test_parity.py` | the async twin of the same count, plus `AWAITABLE_PRIMITIVES`, which the assertion holds the protocol against so the two cannot drift apart |
| `C0-04` | `FORBIDDEN` gains ACTIONS' nine rich shapes, and **it caught two prose mentions on its first run** — one in `adapter.py`'s own comment predicting exactly this, one in `sqlite_minimal.py`'s table. `InvocationRecord` / `InvocationPage` are storage shapes and live in `adapter.py`; `\bInvocation\b` does not match them |

**No `C19` id was renumbered and no kill-row id was edited**: `C9-08`, `C9-18` … `C9-25`, `C10-09`, `C10-11`, `C10-13` … `C10-19`, `C12-08`, `C12-09`, `C12-12`, `C12-13`, `C4-12` … `C4-14`, `C3-14` … `C3-16` all pass unchanged, and `check_merge_guard.py`'s six axes exit 0 with no edits to their fixtures.

---

## 5. Half B — the extraction, and what putting five copies side by side showed

**Ruling R53's own reasoning is why this is a refactor and not a fix:** *"extraction is a refactor with no new behaviour, and this row's evidence is that the CHECKER — not a shared function — catches the next caller."* A shared function does not close the kill row's class. What it does is make the class **readable in one place**, which is the precondition for a ninth walk being attempted at all — and the seventh-trip countersignature rules that attempt to be this row's first adversarial lens.

### 5.1 Which callers, and which reading was named

| what | where it was | where it is |
|---|---|---|
| §5.10 refusal **#1** `different_consumer_sets` | three copies — `merge_types`, `retire(successor=)`, `_alias_identity_breach` | `Registry._identity_breach` |
| §5.10 refusal **#2** `predicate_merge` — *the kill row itself* | the same three | the same |
| §5.10 refusal **#3** `kind_mismatch` | the same three | the same |
| the guards' reading of an extent | `self._extent(ns, name, True)` — a positional call whose meaning lived in a comment (**D-4d-1**) | `Registry._written_extent(ns, name, include_retired=True)`, and `_extent`'s `identity` is a **required keyword** |

**Every collapsing caller reaches it, and `check_merge_guard.py` prints the ROUTE rather than a boolean:**

```
  and do the collapsing callers REACH `_identity_breach`? (ruling R53's extraction, made checkable):
    import_types           _alias_identity_breach -> _identity_breach
    merge_types            _identity_breach
    reinstate              _alias_identity_breach -> _identity_breach
    retire                 _identity_breach
```

**`reinstate` reaching the guards only through the ALIAS door is a fact a boolean hides**, and printing it is `KNOWN_CALLERS`' own lesson applied to a second artefact: *a person's judgement, written down and wrong, is one a reviewer can find.*

### 5.2 The finding that only putting them side by side could produce

**The three callers did not agree on the ORDER, and nobody had noticed.**

| door | order | why it is preserved rather than canonicalised |
|---|---|---|
| `merge_types` | #1 → #2 → #3 | §5.10's own order — this is the call §5.10 was written about |
| `_alias_identity_breach` | #3 → #1 → #2 | an alias whose holder is of another kind is a *kind* question before it is an *extent* question |
| `retire(successor=)` | #1 → (`successor_unregistered`, `retired_operand`) → #3 → #2 | the two successor refusals sit **between** the identity guards, so this door resolves the successor row before it can ask the rest |

`order=` is therefore a **parameter and not a constant**. R53's boundary is that this row may extract and may **not** change what a guard compares — and **which of two non-overridable refusals a caller is told is part of what it compares**. `C9-19`, `C12-13` and D-4c-5 are all one defect: *the right outcome reached by the wrong route*, or the right outcome with the wrong story, and **the story is what a caller acts on**.

### 5.3 What the extraction's own first run found, in the code doing the extracting

Both were found by a **gate**, within minutes, in the change that was supposed to be behaviour-free.

- **A synthetic `TypeRecord` built as a comparison operand made Part A flag `_alias_identity_breach` as an unjudged CALLER.** The AST scan reads every construction of a record carrying an identity field, and a throwaway operand built that way is **indistinguishable from a write**. It is a `TypeRef` now, and `_identity_breach` refuses refusal #1 against one by name, because #1 reads consumers off a stored row and a `TypeRef` names a word rather than a row. *The enumeration doing exactly what row 4c built it to do, to the row that was extending it.*
- **A shared `detail` base dict changed all three refusals' payloads at once.** The three guards already used `from`/`into` for three different things — the two **kinds** (#3), the two **gate sets** (#1), and for #2 nothing at all. `C10-03` asserts `merge_types`' `kind_mismatch` detail by **full equality** and caught it; `C10-09` caught a `why` being stamped over the one place the shipped guard leaves it `None`. Each guard's detail is now exactly its shipped one, key for key.

### 5.4 The checker learns the question the extraction makes askable

**Part A** asks *is there a caller nobody has judged?* **Part B** asks *does the guard give the right answer in every state?* Between them they could not ask the question the fourth and third trips are: **is a caller judged to collapse actually running the guards at all?**

Before the extraction that question had no mechanical form — three copies of an expression is not something an AST can ask about without enumerating shapes, which row 4c's second round proved is *the same artefact as the guard it checks*. **After the extraction it is one name.**

`check_shared_guard()` walks `registry.py`'s call graph and fails on a `collapses=True` caller that reaches `_identity_breach` by no path, and on a `_identity_breach` that does not reach `_written_extent` (R64's reading, `C10-14`). **Proved by mutation**, not asserted: bypassing `merge_types`' guard makes Part A2 print `DOES NOT REACH IT` and exit 1 — *and* reddens sixteen Part B rows, which is the fifth and sixth trips' own lesson demonstrated rather than restated: **constraint 7's loop and constraint 8's gate are both load-bearing and neither substitutes for the other.**

**The residual, stated in the shape ruling R52 asks for:** Part A2 proves a caller *can reach* the guard, not that it reaches it on every path through itself. A caller with an early return that skips the guard passes A2 and fails Part B — which is why both halves run.

### 5.5 No id changed

`C9-08`, `C9-18` … `C9-25`, `C10-09`, `C10-11`, `C10-13` … `C10-19`, `C12-08`, `C12-09`, `C12-12`, `C12-13`, `C4-12` … `C4-14`, `C3-14` … `C3-16` all pass unchanged. `check_merge_guard.py`'s six axes exit 0 with **no edits to their fixtures**. Both suites came back at exactly the counts they had before the extraction — **721** and **759** on three legs — which is what a pure refactor is supposed to look like and is the only evidence that it was one.

---

## 6. The adversarial loop — three rounds, five lenses where the brief asked for six, and it did NOT converge

**Stop rule** (standing constraint 7, and the brief's): two consecutive clean rounds, or three rounds plus an honest convergence note. **Three rounds ran; none was clean; this is the note.**

| round | lenses | BLOCKING | MAJOR | MINOR | kill-row trips | ids after |
|---|---|---|---|---|---|---|
| **1** | the extraction against all eight trip records · beacon integrator | **4** | 8 | 7 | **1** — the ninth | 318 |
| **2** | fix-auditor on round 1's own fixes · *(kill-row lens died on a rate limit, no report)* | **3** | 3 | 2 | **1** — the tenth | 322 |
| **3** | kill row, briefed with all ten · does-the-writing-tell-the-truth | **2** | 3 | — | **1** — the eleventh | 327 |

**Round 2 ran with one lens, and round 3 asked its questions for the first time.** The round-2 kill-row lens — briefed with all nine trips and pointed at the new `ACTIONS` doors — terminated on a weekly API rate limit after reporting only *"two failures appeared on the Postgres leg"*. Its brief was re-issued in round 3 and **found the eleventh trip on the first target it looked at**, which is the strongest available evidence that a missed lens is a missed finding rather than a missed formality.

### 6.1 The one sentence this loop is about

**Every round found the previous round's fix applied to fewer places than it needed to be.**

| trip | the operand refusal #1 could not do without | reached |
|---|---|---|
| **9** | the target's consumer set, when the row does not exist yet | nowhere — the guard compared a row against **itself** |
| **10** | the same, when the row **does** exist | **one branch of two** — the other read the state the write overwrites |
| **11** | the same, at every caller | **one call site of four** — `retire`, `reinstate` and `merge_types` all called it bare |

That is the **sixth** trip's diagnosis — *a guard written for one call, over a fact more than one call can change* — applied to a **fix**, three rounds running. It is also the **eighth**'s: *a fix that publishes a shared answer is only as good as its application.* **Three consecutive rounds is new information for the founder's `stop` question, and it is stated here rather than folded into a tally.**

The fix that finally fits the class is not another operand: `declared_predicates` is a **required keyword** now, which is ruling **R64**'s treatment of `_extent`'s `identity` — *no caller can take a reading by accident* — so a fifth caller fails at the call rather than at a kill-row walk two rounds later. `C12-18` pins that there is no default to fall back to.

### 6.2 What the loop established that no gate here measures

1. **`check_merge_guard.py` could not fail on refusal #1 at all**, and the reason is countable rather than descriptive: the file contained **zero** occurrences of `register_consumer` and zero of `Consumer(`. No fixture, on any leg, at any door, had ever registered one — so both gate sets were empty in every probe and `different_consumer_sets` passed **vacuously everywhere**, in the file built to enumerate exactly these guards. Trips five through ten were *"its fixtures could not pose the question"*; this is *"the guard was unfailable"*. **Seventh axis added, and proved by mutation.**
2. **Two of the three rounds' BLOCKING were at the ACTIONS layer rather than the registry**, and both were the same shape one surface along: `ref_shape` trusted an unrecognised **shape** (round 1) and `ref_kind` trusted the caller's **kind** (round 3), on a rule §2.3 states as *"general or it is nothing"*. **A general exclusion cannot rest on the caller spelling one word correctly.**
3. **The integrator lens found what no correctness lens did, for the third row running**, and all three of its BLOCKING were in the **read** half or in *what the code does when nobody passed the optional argument*. The write half had been reviewed three times as a specification; the read half had never been used.
4. **Gates found four defects inside the changes that introduced them** — `check_spec_drift.py` on §9's record, `check_capability_matrix.py` twice, `C12-15`'s narrowing once — none of which a reader could have found. Constraint 7's loop and constraint 8's gate each found what the other could not, for the fifth consecutive row.
5. **The findings did not shrink.** 4 BLOCKING, then 3, then 2 — over rounds with two, one and two lenses, so the trend is not comparable. **What is comparable: every round pointed at the previous round's work found a kill-row trip.**

### 6.3 What a fourth round would find, [Assumed]

Every round of this row attacked something the previous round wrote and succeeded, three for three. **Round 3's fixes have had no such round**, and two of its findings were left unfixed by design and are carried as questions (**Q77**, **Q78**) rather than closed. The most likely next finding, on this row's own evidence: **a fifth caller or a second branch of one of round 3's three fixes** — which is precisely why `declared_predicates` became required rather than merely passed, since that is the one change in this row that makes the class fail at the call site instead of at a walk.

**Stopping here is the cap, not a verdict that the work is clean**, and this section is the record that it was stopped rather than finished. `ACTIONS.md` §19.5 reached the same conclusion from the other side and named what would move it: *the `C19` suite, `check_spec_drift.py` pointed at this file, and `check_merge_guard.py` enumerating the callers.* All three now exist — and all three found defects in this row that no reviewer had.


---

## 7. What the build taught

**1. A specification can print an answer that no state can reach, and only writing the code finds it.** §2.4's table says `predicate_holds` is *"answered by `predicates()` / `list_types(predicate=…)`"* — and the obvious reading, `predicates(of=subject)` and look for the word, **can never return `False`**: `INTERFACE.md` §5.6 makes any *filtered* listing incomplete, `of=` is a filter, so every miss is Rule U's unknown and rule **2.4-4**'s *"a precondition that does not hold"* has no reachable state at all. Three adversarial rounds read that table. Nothing in reading it can find that, because the sentence is true and the mechanism it names cannot deliver it. **D-6b-2.**

**2. The two most expensive defects of this row were both a fallback for an unrecognised value.** `ref_shape` returned `"type"` for anything that was not an `EdgeRef` or an `InstanceRef` — so a bare string walked past a `predicate` exclusion §2.3 calls *"general or nothing"*. `_alias_identity_breach` fell back to comparing a row **against itself** when the row being aliased onto did not exist yet — so refusal #1 was equal by construction, and that is the **ninth kill-row trip**. `is_person` records the identical mistake one section along, in the same shape, and its own docstring names the rule: **unknown is not a person.** It is also not a type ref, and it is not an agreeing consumer set. *A permissive default for a value you did not recognise is the single shape this row shipped twice.*

**3. Symmetry is a correctness property of a comparison, not a tidiness one.** Round 1's fix for the ninth trip computed one side of the consumer-set comparison and read the other off a stored record — and on `indexes_membership=False` a record's `predicates` come back **empty**, so the comparison compared a fact against an absence and refused a legal import. That is the **first** trip's operand pointing the other way: *unknowable is not equal*, **and it is not different either.** `check_capability_matrix.py` found it within one run of it being written.

**4. Three gates found four defects that three adversarial rounds of the specification had not.** `check_spec_drift.py`, reading `ACTIONS.md` for the first time, found §9's `InvocationRecord` missing `declared_policy` and `family_version` — *the entirety of round 2's gate-to-record fix*, in the block a third-party backend author builds from, in a document whose §19.4 records round 3 correcting that exact omission in four other places. `check_capability_matrix.py` found an unfiltered, **complete** census being stamped incomplete, and then found round 1's asymmetric comparison. `check_merge_guard.py`'s Part A refused the extraction's own synthetic `TypeRecord` as an unjudged caller. **None of the four is a defect a reader could have found**, and all four were found in the change that introduced the gate.

**5. A printed shape can be held by one document and drift in another.** `ACTIONS.md` §9 and `PACKAGE.md` §3.3 print the same two records; §9's three **primitive signatures** were held by neither half of the checker — the shape half reads dataclasses and the call half reads `Registry`. Three had drifted, and the checker reported the document clean. `InvocationRecord` printed `family` before `namespace`, so `InvocationRecord("id-1", "add_task_stakeholder", "beacon")` built **silently and wrongly** from the document. *There is no half nobody is checking* has now had to be said four times, once per document.

**6. Extracting a guard does not close its class, and R53 said so before this row started.** *"This row's evidence is that the CHECKER — not a shared function — catches the next caller."* What the extraction bought is that the three refusals became **readable in one place**, which is the precondition for the ninth walk being attempted at all — and for `check_merge_guard.py` to be able to ask a question it could not ask before: *does a caller judged to collapse actually REACH the guards?* Three copies of an expression is not something an AST can ask about without enumerating shapes, and row 4c's round 2 proved that enumerating shapes is **the same artefact as the guard it checks**.

**7. Putting five copies side by side is itself a finding.** The three callers of §5.10's identity refusals **did not agree on the order** — `merge_types` fires #1/#2/#3, `_alias_identity_breach` fires #3 first, `retire` interleaves two successor refusals between them — and nobody had noticed in nine trips. `order=` is a parameter rather than a constant because **which of two non-overridable refusals a caller is told is part of what the guard compares**, and R53's boundary is that this row may extract and may not change that.

**8. The integrator lens keeps producing the findings no correctness lens does, for the third row running.** Row #6's own §19.6 recorded it: *"the ingestion-consumer lens produced no correctness finding at all and produced the two that changed what the document is FOR."* Here it produced three BLOCKING — and every one is in the **read** half or in *what the code does when nobody passed the optional argument*. A layer whose declaration doors refused everything thrown at them had a governance query returning the wrong families and a ledger reporting the wrong outcome. **The write half was reviewed three times as a specification; the read half had never been used.**

---

## 8. Questions for the supervisor — **Q69 onward**

Numbering continues from Q68. None of these is taken on this row's authority.

| # | Question | Recommendation | Founder-visible? |
|---|---|---|---|
| **Q69** | **The alias door's refusal #1 is unevaluable on `indexes_membership=False`, and this row SKIPS it there.** A stored row's `predicates` come back empty on such a backend, so comparing them against an incoming row's known ones compares a fact against an absence — the first trip's operand pointing the other way. Refusing instead would ban `import_types` from writing any aliased row on **UC1 Tenshen's own declared shape** | **Keep the skip, and record the residual rather than closing it here.** What still guards a PREDICATE pair there is refusal #2, which refuses every one of them because the extents are unknowable too; what is unguarded is a NON-predicate pair whose consumer sets differ — and on a backend that cannot see membership, `merge_types`' own #1 is equally blind (both sides read blank and compare equal), so this door is no weaker than the call it mirrors. Closing it properly means a backend reporting `predicates` independently of `indexes_membership`, which is a `Capabilities` question | No |
| **Q70** | **Nothing sizes the invocation ledger.** §6.3 says *"one row per action per data row, forever"* and **Q40** admits nothing sizes it. Row 6b's rounds turned that from a cost into three defects and then removed the cause: the one derivation that read the ledger is now an indexed lookup (D-6b-5), so **no v0 code path walks it**. What remains is the original storage question — the integrator lens asked for a number and a rotation story before wiring 222 actions into a CRM | **Record it against Q40 and route the paging half to R58.** There is no longer a bound to lie about, so this is back to being a *retention* question — and **Q40**'s own ruling (**R44**) is that types, edges and invocations have one retention question and want one answer. The evidence this row adds is that an unbounded ledger produced a **correctness** defect the moment anything derived from it, which is worth carrying into that decision | **Yes** — it is the second time **Q40**'s unanswered retention question has produced a defect rather than a cost |
| **Q71** | **`invocations(unreviewed=True)` can say *here are some* and can never say *the queue is 4,000 deep and grew 300 this week*.** `known == len(rows)` and `complete=False` on every filtered read. `review` mode is the mode beacon would put `infer_person_relationships` in — a nightly job produces, a person reviews — and **bounding a queue has no shape anywhere in this document**, exactly as §10.6 records that bounding a *run* does not | **Do not take a count in v0; route it with Q70.** A `known` that meant *the size of the set* on a filtered read is precisely the ambiguity **R13** declined to resolve and **R58** now resolves for Phase 3. Recorded because the reviewer needed it before wiring, and because a review queue nobody can size is a governance mechanism that cannot be operated | **Yes** — it decides whether `approval_mode="review"` is usable by the one host that exists |
| **Q72** | **Rule 10-9's typo judgement depends on an unrelated namespace's data.** `projection` refuses an `order` naming groups no family carries — *unless* **some** family somewhere declares a surface. So an ingestion host whose families all declare `reachability=()` gets zeroes when it is alone on the store and a **refusal** the moment a co-tenant registers one family with a surface. UC3 is dozens of publishers in one catalogue | **Narrow the judgement to the namespace-filtered pool, in a row that can re-run §10's design test.** Round 1 of the spec row moved it *out* of the filtered pool because an empty namespace was refusing a real projection; the correct rule is probably *"a typo is an order naming groups no family in THIS SCOPE carries, where the scope declared any surface at all"*, and getting that wrong in either direction has now cost a round each | No |
| **Q73** | **A retired edge family stays live inside a family's declared blast radius.** §2.5-7 checks that an effect names a registered `kind="edge"` family **at declaration**, and *"the door is the declaration"* has no answer for the family being retired afterwards. `preflight` still says `allowed`, `record_invocation` still warns nothing | **Warn at invocation, do not refuse — and not in this row.** `edge_family_retired` already exists in §5.4 for the identical fact one layer down, so no value need be minted. Refusing would make a steward's ordinary retirement break every host mid-flight, which is the shape §2.5 refuses twice. It is a rule-table change, so it belongs to a row that can add its `C19` id | No |
| **Q74** | **`Invocation.inputs` round-trips to flat identity strings.** §2.3 argues at length that `EdgeRef` carries `family` and `namespace` so *"the reference can be READ without a store round trip"* a year later — and the ledger stores `"beacon:edge:b_edges#e-abc123"`, which a reader has to re-split, with no parser exported | **Take the parser, not the shape.** The string is the honest storage form (`InvocationRecord.inputs` is JSON, PACKAGE.md §3.3), so what is missing is a public inverse of `ref_key` — one function, additive, no shape change. Recorded rather than taken because it is a surface `ACTIONS.md` does not print | No |
| **Q75** | **`review_invocation` refuses `action_family_unknown` for an unknown invocation id.** §7 argued `unknown_invocation` and declined it **because no call in `ACTIONS.md` names an existing invocation by id** — and D-6b-3's fifth call does | **Mint `unknown_invocation` when the fifth call is specified, not before.** §7's argument for declining it was conditional on a fact this row changed, and reusing a value that names a *family* for a missing *invocation* is INTERFACE.md §2.3's Cause B. It is one value under R3 with its §5.12 row; it is not taken here because the call it belongs to is itself a deviation awaiting a ruling | No |
| **Q76** | **§2.2's prose and §5.2's contradict each other about `min_auto_tier=None` under `auto`** — one calls it *"a **warning**, not a rule"*, the other *"**not** a warning value, deliberately"*, one screen apart, with the code emitting neither. Corrected in this row; the question is what catches the next one | **Nothing does, and that is the honest answer to record.** `check_spec_drift.py` holds shapes, signatures, closed vocabularies and rule tables — a contradiction between two paragraphs is none of those. §19.5's own conclusion was that *"every number and every `Fixed:` claim in this document is a hand-written assertion that nothing derives"*, and this is the same class one level down: **prose about a mechanism, held by nothing.** Recorded as the limit of constraint 8 rather than as a task | No |
| **Q77** | **`retire(successor=)` runs refusal #1 over aliases it never transfers, and the retired row's aliases then stop resolving.** The guard at `registry.py`'s retire path checks `rec.aliases` as *"transferred"* — and retire's only write is the retired record; the successor is never rewritten. Round 3 observed both halves: a legal retirement refused `predicate_merge` about a transfer that does not happen, and, where it succeeds, `resolve_type` on the old row's alias going from **`existing … 1.0`** to `proposal / 0.4706` | **Do not change it in this row, and rule on which half is intended.** The comment says the aliases are *"re-pointed"* and the code writes none, which is the TENTH trip's *one door disagreeing with itself* — but this is row 4d's guard, and **R53's boundary is that this row may extract and may not change what a guard compares.** Both readings are defensible: the redirect is real via `resolve_type`'s chain (so the guard is right and the alias write is missing), or it is not (so the guard is refusing a phantom). Deciding needs a design test, not a patch | No |
| **Q78** | **On `indexes_membership=False`, an ENTITY identity collapse is guarded by nothing.** Refusal #1 is blind (both `predicates` lists read empty), #2 does not apply (no predicate operand) and #3 does not apply (same kind). Round 3 verified the doors **agree** — `merge_types` and `retire(successor=)` write the same pair on the same backend — so it is not a disagreement, it is an absence | **Record it; closing it means a `Capabilities` change.** The gap is that a backend declaring it cannot index membership also cannot report a row's `predicates`, so the registry cannot tell *"this type declares nothing"* from *"we cannot see what it declares"* — Rule U's own distinction, missing one level down in the record shape rather than in a guard. That is a PACKAGE.md §3.2 question about what a `False` flag entails, and it is the same shape as beacon finding **U3** (`attribute_projections`), which is the precedent for how it would be answered | No |
