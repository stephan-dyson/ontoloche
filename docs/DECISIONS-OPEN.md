# Ontoloche — decisions open to the founder

**As of 2026-09-09.** Scope: the `ontoloche` project only. Ordered by what your answer unblocks, not by age. **Item numbers are stable across days** — a ruled item keeps its number and moves to section E rather than being deleted.

> This file is the GitHub-readable mirror of the founder decision page, so it can be read from a phone or any machine without the local HTML. The local page is `C:\Users\steph\.claude\fleet-supervisor\decisions\2026-09-09-ontoloche-decisions.html`; where the two disagree, this file is the one that was checked most recently.

**6 open · 12 ruled · 7 FYI** *(2026-11-12: items 19 to 22 added by row 8b, Q103 to Q106, none blocking. 2026-09-22: item 18 added and ruled `adopt B`, recorded as R108. R105–R107 ruled in session and recorded at [`2026-09-22-founder-rulings-R105-R107.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-22-founder-rulings-R105-R107.md). The local HTML page was not regenerated for this change.)*

**2026-09-09: you ruled all three open items in one pass, including the oldest and largest question in the project.** Q56 is closed after ten days and twenty-three kill-row trips; the governance stop criterion is armed and has fired; and the namespace item turned out to name something that does not exist. Details in section E.

One new item is below, and it exists because ruling item 4 uncovered it rather than because anything went wrong.

---

## A. Decide when you want to — 6 items

### 22 · `Q106` — a Foundry property with no description: import it with a warning, or decline it?

*New 2026-11-12. Row 8b. The brief says a property's description is required, and Foundry makes it optional.*

**TL;DR.** **[Observed]** 61 of the 84 properties in Palantir's own test ontology have no description, and every one of its ten main object types has at least one. Requiring a description at import would decline all ten, so the easy import you asked for (R105 to R107) fails on the first fixture. Writing a placeholder would put a definition nobody wrote into the vocabulary.

**Why it is yours.** Declining a row is a refusal. Foundry `active` types also import as `active` and never pass `approve`, so "require it at approval" does not catch them.

**What you ruled for types, and why it does not settle this.** Row 8a, running in parallel, recorded your `hold + override map` answer for a Foundry *type* with no description (its R109, numbered provisionally and not yet on `main`): nothing is written, the row comes back refused, and the caller supplies the missing text and imports again. That ruling chose between holding the row and filing a proposal with placeholder text. **Writing it with no description was never an option for a type**, because a type's definition must be non-empty in the code (`registry.py:2596`) and in the database (`0001_init.sql:21`). A property's description has no such constraint, so `keep and warn` below is new and you have not weighed it.

- **`like types`** — hold the row, as for a type: nothing is written, it comes back refused naming each undescribed property, and the caller passes the missing descriptions and imports again. Consistent with your type ruling, and 61 descriptions must be supplied before Palantir's fixture lands.
- **`keep and warn`** — write the slot with no description and warn, naming it. The import succeeds, nothing is fabricated, and the warning lists what a person must fill in.
- **`decline`** — refuse the row with no way to supply the text in the same call. Faithful to the brief, and it fails Palantir's fixture.
- **`recommend`** — I bring you the per-case rule with the fixture counts.

**Ask: `like types`, `keep and warn`, `decline`, or `recommend`.** Default in force: the shipped code checks no property declaration, so a slot is written as given with no warning. In practice row 8a's Foundry importer writes **no slots yet**: under your R105 `carry` it keeps Foundry's properties verbatim in `attributes["foundry_properties"]`, marked unvalidated, so this question bites the row that turns them into slots. Spec rule 2.10-21 is `reserved: Q106`. I have no lean between `like types` and `keep and warn`: the first is consistent with your type ruling, the second keeps the import easy, and the type case never had to choose.

### 19 · `Q103` — how is an approved property declaration amended, and what may change?

*New 2026-11-12. Raised by row 8b under your `adopt B` ruling (R108, open question 1). It decides what the registry refuses, so it is yours rather than the spec's.*

**TL;DR.** Under `adopt B` an entity declares its properties, and a live entity will need a property added sooner or later. **No governed call does that today.** The only door that changes an approved entity's declaration is `import_types`, and **[Observed]** it replaces the whole declaration with no event and no warning: re-importing `facility` with a new property list silently dropped its declared primary key, and re-importing a shared property changed its type from text to integer under every entity that uses it ([probe](https://github.com/stephan-dyson/ontoloche/blob/main/docs/tools/properties_baseline_probe.py), lines D7 and D7b). The question covers both: an entity's declaration and a shared property's.

**Why supersede-and-retire is not one of the options.** Names are unique per kind and a retired name is burned, so supersede-and-retire would rename `facility` every time a column is added. The row pre-registered that as a falsifier and it held ([`8B-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8B-RUN.md) §0.3, F2).

- **`governed amend`** — a new call that proposes a change to an approved entity's declaration and goes through the same approve/reject loop as a new type, with an event. Adding an optional property is approvable. **Removing a property, changing a property's base type, or changing the primary key is refused unless acknowledged**, because each changes what an existing consumer's rows mean. `import_types` stops being an amendment door: re-importing an active entity with a different declaration warns and leaves it unchanged.
- **`governed amend, additive only`** — the same call, but it only adds. Anything else needs a new entity. Fewer refusals to design, and less useful.
- **`recommend`** — I bring the rules per change type, with what each one breaks.

**Ask: `governed amend`, `governed amend, additive only`, or `recommend`.** Default in force: the shipped behaviour above, which is that only an import can change it and the import does so silently. Spec rule [`INTERFACE.md` 2.10-20](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md) is `reserved: Q103`.

**Not blocking.** The spec landed with the rule reserved. The build row needs this ruling before it builds the amendment path.

### 20 · `Q104` — can a shared property or value set still used by a live entity be retired?

*New 2026-11-12. Row 8b, R108 open question 4.*

**TL;DR.** **[Observed]** today retiring a `kind="property"` entry that an active entity still names succeeds, with no refusal and no warning. `retire` protects a word by asking `consumers()`, and an entity's slot is not a consumer, so the guard never sees it. Every entity using it is left pointing at a retired word. **The same is true of a value set a slot names [Observed]**: CMS's `deficiency_corrected_status` retires silently while a `citation` slot uses it. (The one case already protected: a property that is a member of a predicate some consumer gates on is refused `live_consumers`, like any other type.)

- **`refuse unless acknowledged`** — the `live_consumers` shape: refused, naming the entities that use it, and the caller can override.
- **`warn`** — retire it and warn, naming the entities left pointing at it. The least-refusing option, and it matches how a dangling reference is already treated.
- **`refuse`** — refused with no override until every entity using it has been amended. This depends on Q103.

**Ask: `refuse unless acknowledged`, `warn`, or `refuse`.** Default in force: it succeeds silently. Spec rule 2.10-19 is `reserved: Q104`. My lean is `refuse unless acknowledged`, because it is the guard `retire` already has, pointed at the right list.

### 21 · `Q105` — can two words whose property declarations differ be collapsed into one?

*New 2026-11-12. Row 8b, R108 open question 3 (which guards the new kind inherits). The spec answered every inherited guard. This is the one new refusal it would need.*

**TL;DR.** **[Observed]**, door by door. `zip_code` (text) and `postal_code` (integer) merge through `merge_types` once the caller acknowledges two existing overridable refusals. They collapse with **no acknowledgement and no warning at all** through `retire(successor=)`, and through the import alias write after a plain retire (retire `zip_code`, then import `postal_code` with `zip_code` as an alias). Every entity using the absorbed word then reads the survivor's type. **Entities have the same hole at both silent doors:** `survey` declares a primary key and `citation` declares none, `survey` is collapsed into `citation`, and the word `survey` then declares no key. **So do value sets a slot names:** retiring CMS's `deficiency_corrected_status` with `scope_severity_code` as successor is silent, and the slot then reads the A to L severity grid. **That is one word with two definitions**, the governance register's shape. Action families had the same hole. It is closed by `action_declarations_diverge`, refused non-overridably, and your `all eight` ruling (R102) set which keys it compares.

- **`refuse, like actions`** — `merge_types`, `retire(successor=)` and the import alias write refuse non-overridably when two shared properties differ on `base_type`, `item_type`, `value_set` or `source_type`, two entities differ on `primary_key`, `title_property` or a slot's type, or a value set a slot names is collapsed into another. Same rule, one kind along.
- **`refuse on type only`** — refuse non-overridably on a type or key difference. A different value set, source type or title is acknowledged rather than refused.
- **`recommend`** — I bring the per-key severity with a worked case for each.

**Ask: `refuse, like actions`, `refuse on type only`, or `recommend`.** Default in force: the door-by-door behaviour above. Spec rules 2.10-17 (properties) and 2.10-18 (entities) are `reserved: Q105`. **One sub-question either option carries:** when one side declares a key and the other does not, which includes every collapse on the stripped-down `sqlite_minimal` backend, because it drops the declaration on write. That is `Q101`'s absence question one kind along, and your answer to `Q101` can stand for both. Whether to mint a new refusal value or reuse `action_declarations_diverge` is part of the build row and not part of this question.

### 17 · The stop you armed has STOOD DOWN — `A3` is closed and the ACTIONS surface is reopen

*No action. On the page because you armed that stop, and you are entitled to know it stood down and on what.*

**What closed it.** Both halves of `A3` now exist: the read half from your `read` ruling, the write half from your `all eight` ruling. **I re-ran the row's own probe myself rather than accepting its report** — the walk by which `A3` still fired now **refuses at the write door**, non-overridably, and the remaining walk's actor **cannot record at all**. So on every reachable path a door refuses or warns, which is exactly what the criterion requires to be *absent*. Recorded as [R103](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-supervisor-ruling-R103.md) with the full verification listed so it can be attacked.

**Three things this does NOT do.** **The criterion stays armed** — you armed it and nothing here disarms it; armed and firing are different states, and it fires again on the next entry that meets it. **The register still counts one**, because closing an entry does not remove it — it counts harms ever reached. And **it answers neither of your open questions**: `Q101` and per-key severity are untouched.

**One thing worth your attention about how it got there.** The row that closed it had committed its measuring instrument before the code it measures, found three defects in that instrument first, and verified five separate claims about its own restraint. **Its adversarial round still found three blocking defects, two of which closed a legal operation** — the precise trap your ruling's write-up warned about, re-created by the fix meant to honour it. All fixed and verified before landing. **Self-verification did not substitute for a fresh adversary**, and that is the strongest evidence this project has yet produced for running the review round at all.

### 16 · `Q101` — when one family declares a key and the other omits it entirely, is that agreement or a contradiction?

*New. Found by row 6g while implementing your `all eight` ruling, and it is the same shape as Q99: the current behaviour is not a decision anyone made.*

**TL;DR.** The comparator that decides whether two action families contradict each other **already refuses on a missing key today — non-overridably — and nobody chose that.** It falls out of the code reading an absent key as the value `None`, which is an implementation detail wearing a policy's clothes.

**Why it cannot just be left alone.** The row measured the consequence from a working implementation rather than reasoning about it, and the behaviour is **inconsistent with itself**:

- `reachability = []` against a family that omits the key → **permits** the collapse
- `reachability = ["mcp","cli"]` against that same omission → **refuses**, non-overridably

`ACTIONS.md` says an empty list is a **positive declaration**. So the comparator reads an absence as *agreement* in one case and as *contradiction* in the other. **That is not a rule being applied.**

**Why it is yours.** It decides what the registry refuses — the same class as Q99, Q56 and Q50. And your `all eight` ruling widened the surface: what was a quirk on two keys now reaches four more.

**What the row did, and did not do.** It did **not** change the four already-shipped keys, because reversing shipped behaviour is a decision rather than a tidy-up. So the comparator is now **deliberately asymmetric on absence, and that asymmetry is published rather than hidden**, waiting on you.

- **`absence is agreement`** — a family that never declared a key is not a family that declared it differently. Fewer refusals; matches the argument an earlier row made for whole-declaration absence.
- **`absence is a contradiction`** — declaring nothing where the other declares something is a real difference. More refusals, consistent with `all eight`'s direction.
- **`recommend`** — I bring you the proposed rule with the evidence for each key.

**Ask: `absence is agreement`, `absence is a contradiction`, or `recommend`.** No default is in force — today's behaviour is inconsistent, so there is nothing coherent to default to.

**Not urgent.** Nothing is blocked: row 6g proceeds and publishes the asymmetry. But one contract id now pins exactly this question, and your ruling will move it.

### 10 · `oo-pg` is carrying **989** leftover schemas, and the leak is still running. Drop them, or leave them?

*Low stakes. Raised by your item-4 ruling, not blocking anything.*

**TL;DR.** Your `drop it` on item 4 authorised deleting one namespace attributed to row 6d. That namespace **does not exist** (see item 4 in section E). What *does* exist is **989 `oo_*` schemas** on the `oo-pg` container, left by every three-leg suite run this project has made. **This page said 625 until 2026-09-10, when I counted them instead of re-reading the figure** — and I had been carrying a third number, 741, in my own cycle prompt. **Three figures, none checked at the point of use; only the fourth was measured.** **I did not touch them**, because they are a different and much larger object than the one you ruled on, and reading your word as covering them would be taking a destructive action you did not sanction.

**The facts.** **[Observed 2026-09-10 03:33]** `select count(*) from information_schema.schemata where schema_name like 'oo\_%'` against `open_ontology` on the running container returns **989** *(re-measured 2026-09-10 12:08)*. The series: **193** during row 6c, **476** on 2026-09-05, **625** on 2026-09-09, **896** at 00:07, **958** at 03:33, **989** now.

**AND THE COUNT IS NOT MONOTONIC, which I only saw by sampling it twice during a run.** It went **996 at 06:47 and 989 at 07:01** while a suite was mid-flight — the legs create schemas and teardown drops some of them. **What accumulates is the residue, not the gross.** The earlier wording let this read as a one-way leak; it is a leak with partial cleanup.

**AND THE MECHANISM IS NOW MEASURED RATHER THAN INFERRED FROM THE SERIES.** The count sat at **896 for a full hour** while nothing was running, then rose to **958** while one row ran its three suite legs. **The flat hour is the control and the +62 is the treatment.** This page used to tell you these accumulate from suite runs; that was a story fitted to a rising series, and it now has a control arm.

**That is +271 in a single day, the largest jump in the series** — three rows landed on 2026-09-09 and each ran the postgres leg. The container has `RestartCount=0` and a persistent volume, so they accumulate indefinitely. **This is not a pile of old junk; it is a leak that is still running.** They **slow the postgres leg** of the three-leg suite; they have never failed it.

- **`drop them`** — I confirm each is a suite artefact and nothing else's, report the list length, then remove. The postgres leg gets faster. Nothing in the repo depends on them.
- **`leave them`** — they keep accumulating. The cost is suite time, and it grows.

**Ask: `drop them` or `leave them`.** Default in force: **leave** (the project's no-deletion default).

---

## Context — all of these resolve on GitHub

- [ROADMAP.md](https://github.com/stephan-dyson/ontoloche/blob/main/ROADMAP.md) — the kill criterion in its own words, and the kill-row register with all twenty-three trips
- [6E-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6E-RUN.md) — the audit's full record
- [6D-RUN.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md)
- [INTERFACE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md) — §5.3 is the guarantee Q56 is about
- [PACKAGE.md](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/PACKAGE.md) — C12-09 lives in §6.2
- [STATUS.md](https://github.com/stephan-dyson/ontoloche/blob/main/STATUS.md) — the project status page
- The [governance register](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-governance-register.md) — its stop criterion is now ARMED and FIRED
- Rulings 2026-09-09: [R99](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R99.md) · [R100](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R100.md) · [R101](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R101.md)
- Rulings 2026-09-07: [R96](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R96.md) · [R97](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R97.md) · [R98](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R98.md)

---

## E. Ruled — 12 items

### 18 · Q102 — govern entity properties as vocabulary (option B) → **RULED: `adopt B`** *(2026-09-22)*

**Recorded as [R108](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-22-founder-ruling-R108.md).** Row 8b opens as a spec row ([brief](https://github.com/stephan-dyson/ontoloche/blob/main/docs/handoffs/2026-09-22-row-8b-properties-spec-brief.md)) and amends `INTERFACE.md` §0 before anything else. How an approved entity is amended is left open, and it will come back to you if it decides what the registry refuses. The item as it was asked:

*New 2026-09-22. It answers your `recommend` on properties (R105), in light of your `full replacement` (R107).*

**TL;DR.** Declare local properties on the entity that owns them, make shared properties a new `kind="property"`, and never store or check property values. That mirrors Foundry's own split between local and shared properties. It gives a departing Foundry customer governed definitions to build their tables from, and it closes contortion 10, open since 2026-08-28, where `latitude` becomes a type proposal.

**Why not the other two.** `carry` leaves properties ungoverned, which cannot support full replacement and lets them rot the way Foundry's do. A schema store that validates data is the object model `VISION.md` §3 says not to build, and it collides with R78.

**The cost.** There is no call today that amends an approved entity, so adding a property to a live type needs a new governed call or a supersede pattern. A new `kind` is also a new door for every guard, and new doors have produced kill-row trips before (rows 6b and 6d).

- **`adopt B`**: a spec row opens under it, and `INTERFACE.md` §0's *"not a schema store"* becomes *"not a store of values"*.
- **`adopt A`**: stay at `carry` indefinitely, and full replacement ships without governed properties.
- **`discuss`**.

**Ask: `adopt B`, `adopt A`, or `discuss`.** Default in force: `carry` (R105's interim). Full write-up: [`PROPERTIES-OPTIONS.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/findings/PROPERTIES-OPTIONS.md).


### 12 · Q99 — which of the eight declared keys are governance → **RULED: `all eight`** *(2026-09-09)*

Recorded as [R102](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R102.md). **Everything an action family declares is part of its identity.**

**What it fixes.** The comparator saw four keys and never `inputs`, `preconditions`, `reachability` or `payload_schema` — so two families differing only on `preconditions` collapsed with nothing refusing, a machine actor recorded the action, and the survivor's ledger read zero. **That is the route by which A3 still fires your stop criterion**, and this closes it at the write door.

**It also dissolves the asymmetry you were warned about.** The read side already scored on all eight; a narrow ruling would have left the two sides deliberately out of step. They now stand on the same definition — the read scores agreement and never refuses, the write refuses a contradiction.

**What it costs, stated plainly:** this is the most refusing option, so collapses that succeed today will refuse tomorrow. That is what you chose.

**And one specific way to get it wrong, which this project has already been burned by.** An earlier row compared a list-valued key with `!=` and refused two families whose governance was identical and whose entries were merely in a different order — it **closed a legal operation**, non-overridably, at all three doors. Going from four keys to eight adds **three more list-valued keys**, tripling that surface. Row 6f already solved it on the read side by comparing those as sets; the write side must match, and R102 says so.

**Still not decided, and the row must raise rather than assume:** whether every key deserves the same non-overridable severity, what to do when one side declares nothing, and how many currently-legal collapses this refuses — that last one is a measurement it owes you.



### 9 · Q56 — verify the identity claim where it is MADE → **RULED: `read`** *(2026-09-09)*

Recorded as [R99](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R99.md). **The oldest open question in the project, closed after ten days and twenty-three kill-row trips.**

**What it decides.** The *cheap half* of Q56 already shipped in row 4d on 2026-08-30: `resolve_type` re-reads both predicate extents on an alias or successor hit and carries `identity_stale` when they disagree — but **confidence stayed 1.0**, because acting on what it found was yours. `read` takes the **expensive half**: `resolve_type` may now answer **below 1.0** and may **refuse**. That changes `INTERFACE.md` §5.3's shipped guarantee, which is exactly why it was never the supervisor's.

**What it does to the kill row.** It removes statement **`E`** — *the registry treats a fact checked at WRITE time as true at READ time* — which row 6e's audit found is the mechanism **delivering the harm in twenty-one of the twenty-three trips**. So the criterion **does not fire**, and **the fifteenth `stop` is RESOLVED, explicitly not declined a sixteenth time**: a decline says *the criterion tripped and we are continuing anyway*, and that is not what happened. Its subject is being removed. **Count stays TWENTY-THREE** — a ruling is not a trip.

**What it does not decide.** Refuse-versus-score, what confidence a stale redirect carries, and whether any of this reaches past predicates are all still open. They belong to the row this ruling opens, which is spec-first: §5.3's guarantee is amended before the resolver changes.

### 6 · Q97 — the governance register's stop criterion → **RULED: `arm`** *(2026-09-09)*

Recorded as [R100](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R100.md). **The criterion is LIVE and entry 1 (A3) fired it immediately** — which was disclosed on this page before you gave the word, so the halt is deliberate rather than an accident of drafting.

**Why A3 meets it.** A Haiku-tier machine actor *records `applied`* against a verb the surviving family declares *human-approval-only and irreversible*, and **no door refuses or warns**: `retire(successor=)` returns `('RETIRED','retired',[])` and `import_types` returns **warnings EMPTY**, both on ordinary calls with `force` and every acknowledgement removed.

**In force now.** No further ACTIONS-surface row launches until A3's write doors refuse or warn; A3's fix is the gating work on that surface; and because the criterion's stated harm is that *the produced record reads as authorised*, any `applied` already written through this path is **suspect until established otherwise** rather than assumed absent.

**Not halted:** the project, and the read-side row R99 opens. Firing adds **no entry** — the governance register still counts **ONE**, and it is never folded into the kill-row count.

### The two rulings meet on A3, from opposite ends

This is the part worth knowing, because it changes what gets built. A3's harm is delivered by `resolve_type` answering the dead word with the survivor **at 1.0** while `preflight` answers it with the tombstone's policy. **That delivery step is `E`.** So **R99 removes A3's delivery** and **R100 halts the surface until A3's write doors are fixed**. Neither closes A3 alone, and **A3 closes only when both halves land**. It is still open and unfixed. The practical consequence: the read-side work R99 opens and the read-side half of A3's fix are **the same work**, and sequencing them as two rows would build the same thing twice.

### 4 · The row 6d namespace → **RULED: `drop it`** — and there was nothing to drop *(2026-09-09)*

Recorded as [R101](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R101.md). **Nothing was deleted.**

This page promised that on `drop it` I would *"confirm the namespace is the row's and nothing else's, and report before removing."* The confirmation found that **`r3lens_de7fdace` does not exist** — not in `open_ontology`, not in `postgres`. This is not lost state: the container has **`RestartCount=0`** and a persistent volume dating to 2026-08-28, and 625 other schemas from the same era are still there.

**The name has no source in the row's own record.** It appears nowhere in `6D-RUN.md`. Its only occurrences anywhere are in the supervisor documents that carried the item forward. **So this item spent four days on your page naming an object that was never observed.** The page did disclose it was unverified, which is why this is a hygiene failure rather than a false claim — but verifying it was one command, and it should have happened when the item was written, not when you ruled on it. The standing correction is recorded in the supervisor's handoff.

The real residue is the `oo_*` schemas, which is **item 10** above rather than something folded into a word you gave about something else. *(625 when this was written; **958** when re-counted at 2026-09-10 03:33.)*

---

## E2. Resolved 2026-09-07 — 4 items (history)

### 5 · `git push` — fixed, and fixed durably

**RESOLVED.** The day's seven commits are on `origin/main`, after being stuck at `ef2d26b` all day behind a 403.

**The unblock:** you re-authenticated as `stephan-dyson`, which made it the active gh account, and the push went through unchanged.

**The durable fix, which matters more:** the key is now registered on that account, `~/.ssh/config` has a `Host github-stephan` block pinned to `id_ed25519` with `IdentitiesOnly yes`, and this repo's remote is `git@github-stephan:stephan-dyson/ontoloche.git`. **SSH never consults gh**, so pushing here no longer depends on which account is active — switch back to the other account freely.

**Verified, not assumed:** `ssh -T git@github-stephan` → *"Hi stephan-dyson!"*; `fetch` exit 0; `push --dry-run` → *Everything up-to-date*. The beacon pin `dbd67366` was re-checked *at* the landing and is still an ancestor; the whole day's diff is docs-only.

**For the second account,** which was your actual question: generate a second key, register it on the other account, add a second `Host` block with its own `IdentityFile` and `IdentitiesOnly yes`, and point that repo's remote at the new alias. Without `IdentitiesOnly`, ssh offers every key and GitHub authenticates you as whichever it accepts first.

**One error of mine on the record:** while writing this item's queue entry I wrapped a gh command in backticks inside a double-quoted shell argument, which *executed* it and launched a stray device-login flow. It failed closed and changed nothing (auth state, push and repo all re-verified afterwards), but the hazard is now written into the supervisor's standing notes.

### 1 · Row 6d landed — what opens next → **RULED: `audit`**

Recorded as [R96](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R96.md). Row 6e ran and is now closed.

It wrote **no product code**. Its one question: *are the twenty-three kill-row trips twenty-three implementation defects, or ONE design defect found twenty-three times?* Each had been ruled *"implementation defect, not design"* by the supervisor who found it, one at a time, and the series had never been read as a series.

**The part of this ruling that matters most:** `stop` is **held open, not declined a sixteenth time**. The fifteenth put stands unanswered pending the audit; the register must not record a decline that did not happen. And the audit was required to be able to return an answer that costs the project — if it found one design defect, `stop` fires and the merge-centred shape goes back on the table. It found one.

### 2 · Q94 — governance identity → **RULED: `separate`**

Recorded as [R97](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R97.md); the governance register is open with **A3 as entry one**.

**The reason previously on file was wrong, and is corrected in the record rather than edited over.** *"The identity criterion is not met"* does not hold: `resolve_type` answering a word with the survivor at 1.0 while `preflight` answers it with the tombstone's policy **is** two things answering to one identity. The ruling stands for a better reason — a count that grows on a widening definition stops being a signal, which is the project's own *"a widened matcher is a minted rule"* turned on its own register.

**Separate does not mean filed away:** A3 is BLOCKING, reachable with ordinary calls on two of three doors, and open.

### 3 · Q95 — `C12-09`'s narrowing → **RULED: keep**

Recorded as [R98](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-07-founder-ruling-R98.md). `C12-09` is **kept**; the rule binds aliases only.

Two evidential reasons: round 3's lens drove the transfer doors and **could not build a harm the blessed write does not already produce one door earlier**; and overturning would deliberately repeat the mistake round 3 had just made — its own false refusal **closed a legal operation for two rounds**. The residual stays on the record, and the gate records the gap rather than hiding it.

**The warn-only idea is routed, not adopted.** It is my construction, unverified, and it went to row 6e to *verify or kill* with its falsifier stated, under the same never-self-classify rule that binds a worker. Killing it is a live outcome.

---

## F. FYI — no action needed

### 15 · Your `read` ruling is BUILT AND SHIPPED — and the row landed itself NOT CLEAN

*No action. The work you authorised this morning is done; this is what it cost and what it did not fix.*

**What shipped.** `resolve_type` no longer promises `1.0` unconditionally. A stale redirect now carries a **measured** confidence, `min_confidence` governs that path for the first time, and verification covers action families by their governance declaration as well as predicates by their extents. Ten new contract ids, and **no new value in either closed vocabulary** — the change adds no new way for the registry to say no. Full record: [`6F-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6F-RUN.md).

**I verified it myself rather than countersigning the row's report**, because twice today I repeated a claim I had not checked. All four gates exit 0, the record is indexed, the tree is clean and it is genuinely on `origin`. **I re-ran the row's own probe and reproduced its table exactly**: the walk that used to hand a machine actor a **clean 1.0** now answers **0.75** with a staleness warning, and the walk with no declaration answers **None**.

**A3's delivery is removed. A3 is not closed.** That same walk still lets the collapse through at the write door and still records the action against the dead word with the survivor's ledger empty. **The write doors are the next row**, and the stop you armed stays in force until they refuse or warn.

**Why the row landed itself NOT CLEAN, which is the part worth your attention.** Round 1 reported nine findings using a mutation verifier the row **later proved broken** — it mutated two helpers and credited the kill to the wrong one. So nine-then-seven compares a bad number to a good one. What survives is that round 2, measured with a working instrument, found **three blocking defects in code four review lenses had already passed**, two of which falsified the row's own published reasoning by the same error twice.

**The row named its own worst failure as a method rather than a defect:** twice generalising from a single measurement and publishing the conclusion, the second time after it had already recorded the first. It put that at the top of its convergence note on the reasoning that a defect is fixed once, while a method that manufactures defects keeps paying out. **Neither instance was caught by a gate. Both were caught by somebody re-running.**

### 14 · Your `read` ruling turned out CHEAPER than I told you it would be

*No action. On the page because I gave you a cost estimate and it was too high.*

**The spec is landed** ([`INTERFACE.md` §5.3](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md), commit `326ffee`), amended **before** the resolver was touched — I verified that ordering rather than taking the row's word: the spec commit is the only commit against `INTERFACE.md` in this row, and `registry.py` has none at all.

**What I told you it would cost.** R99 §3 warned that callers relying on `1.0` get a new answer shape, and that a refusal path would probably mint a new value in a closed vocabulary.

**What it actually costs.** **No caller is refused, and no vocabulary value is minted.** The row concluded *score, never refuse* — `resolve_type` hands back the survivor with a **measured** confidence instead of a door in the face. Your authorisation to refuse is on the record as **deliberately unused**.

**Why that is a result and not a shortfall.** The row **pre-registered** that outcome before it opened the resolver — it is in §0 of the run record, in the commit whose ordering is provable, and it is the outcome that *cost the row its interesting answer*. It then reported it rather than reaching for the refusal you had made available. I checked the pre-registration commit myself.

**Three other things your ruling settled**, all in spec: a stale redirect's confidence is **`min(resolver score, Jaccard agreement of the two extents)`** — derived from what the call already reads, not a round number someone picked; the verification now covers **`kind="action"` by its own operand**, since an action family has no extent and its identity stands on its governance declaration; and **`min_confidence` now actually governs this path**, which it did not before — a caller passing `min_confidence=2.0` was still handed `existing` at `1.0`.

**Not done yet:** the resolver itself is uncommitted and the adversarial rounds have not run. Nothing here is a claim about shipped behaviour.

### 13 · The evidence under yesterday's `arm` ruling was partly stale. The ruling stands; you are being told, not re-asked.

*No action. On the page because a reason found wrong gets corrected where you can see it.*

**What was wrong.** When you ruled `Q97 → arm`, I showed you a table saying A3's collapse doors let the harm through — `retire(successor=)` returning `('RETIRED','retired',[])` and `import_types` returning **warnings EMPTY**. **Neither of those reproduces at `HEAD`.** Commit `f60c336`, titled *"A3 CLOSED"*, landed **2026-09-05** and fixed exactly those doors. The governance register was opened **2026-09-07**, two days later, and recorded row 6d's **round-1** observation in the present tense. I wrote your clause table on **2026-09-09** by reading that entry and **did not re-run it.**

**Why the ruling still stands.** A3's harm **reproduced at `HEAD` when this was written** (2026-09-09), by the uncompared-key route in item 12 — I ran the probe myself to check rather than taking the row's word. **Row 6g closes that route at the write door, so this sentence describes the state that justified the ruling, not a permanent one** — written this way deliberately, because a page that asserts a live fact in the present tense goes false the moment the fix lands, which is the defect that made item 13 necessary. Every clause of the criterion is met on ordinary calls. **`arm` produced the correct outcome**, and the ACTIONS-surface stop stays in force.

**Why you are not being re-asked.** The conclusion you ruled on has not moved. Re-putting a question whose answer is unchanged wastes the one thing this project asks of you. But you ruled on evidence I gave you, part of it was stale, and this project's rule is that a wrong reason is corrected in place with the correction visible — so it is here, and in [R100](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-09-founder-ruling-R100.md) §2b, rather than quietly fixed.

**The governance register still counts ONE.** This is one harm reached by a second route, not a second harm — minting a second entry would be the *"count that grows on a widening definition"* failure your own `separate` ruling guarded against.

### 11 · `Q50` is still open, still yours, and is parked on purpose — surfaced so it cannot repeat Q56

*No action. Listed because the failure it could repeat just cost this project ten days.*

**The question.** May a `stores_proposals=False` backend hold a `kind="predicate"` entry at all? Like Q56, it decides **what the registry declines to serve**, which is why it is yours and not the supervisor's.

**Default in force, and it is safe:** yes, written with warning `predicate_requires_review` — row 4c's behaviour, pinned by `C10-10`. The alternative, `Refusal(reason="proposals_not_stored")`, would mean beacon's own shape (`PACKAGE.md` §7.4) **cannot carry a capability predicate**. The kill row's danger is a predicate going live *and then being merged*, and **the merge is guarded on every backend regardless of this answer**.

**Why it is not in section A.** Its own register entry says it is *"revisited with beacon 2B's evidence"*, and that evidence does not exist yet. Asking you to rule now would be asking you to rule without the thing the question says it needs.

**Why it is on this page anyway.** Q56 also had a safe default in force, and that is exactly what let it sit flagged and unruled for ten days while twenty-three kill-row trips accumulated on it. A default in force is not a reason a question stops being visible. **It moves to section A the moment beacon 2B produces its evidence**, and the supervisor is watching for that rather than waiting to be asked.

Register entry: [`2026-08-30-4c-rulings-R48-R57.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-08-30-4c-rulings-R48-R57.md).

**This is the complete list.** A sweep on 2026-09-09 found exactly one question flagged to you and unruled across every document in the repository, and it is this one.

### 7 · Where the project stands

**Every figure in this item was re-measured at 2026-09-10 00:20.** It had gone stale in four places at once, which is why it now carries a stamp.

`main` = `origin/main`, **everything pushed**, working tree clean.

**The standing gate set is FIVE, not two**: `check_links`, `check_spec_drift`, `check_merge_guard`, `check_capability_matrix`, and `check_skip_census` — the fifth added by row 6h. **All five exit 0 under my own run.** *(This item said "`check_links` green and `check_spec_drift` exit 0" for days, naming two of five.)*

**No session is running** in this project. *(This item said row 6e was the last one closed; rows 6f, 6g and 6h have opened and closed since.)*

**Kill-row count stays TWENTY-THREE.** The governance register still counts **ONE**, and its single entry `A3` is now **CLOSED** — the criterion **stays ARMED**, because armed and firing are different states. **The latest ruling is R104.** *(This item said "next ruling R99", five rulings ago.)*

**This page still carries no current-head sha**, and neither does `STATUS.md`, because a document that pins the current head is wrong on its own write.

### 8 · Beacon is not at risk

**Beacon's pin `dbd67366` is still an ancestor of `origin/main` — [Observed 2026-09-10 00:20], by `git merge-base --is-ancestor`, not by inference.** That is the claim that matters and it holds.

**But the reason this item used to give was wrong, and a reassurance resting on a false premise is worse than none.** It said the 2026-09-07 and 2026-09-09 commits *"touch `docs/` only"*. They do not. Since 2026-09-07 the non-`docs/` files changed are **`ontoloche/registry.py` and `ontoloche/aio/registry.py`**, four contract test files across both trees, `ontoloche/contract/test_manifest.py`, `ROADMAP.md` and `STATUS.md`. **The registry itself changed — that was the entire point of rows 6f and 6g**, which implemented your `read` and `all eight` rulings.

**So the honest statement is the measured one:** the pin is verified as an ancestor at each landing, and it is verified again here.
