# Ontoloche — decisions open to the founder

**As of 2026-09-09.** Scope: the `ontoloche` project only. Ordered by what your answer unblocks, not by age. **Item numbers are stable across days** — a ruled item keeps its number and moves to section E rather than being deleted.

> This file is the GitHub-readable mirror of the founder decision page, so it can be read from a phone or any machine without the local HTML. The local page is `C:\Users\steph\.claude\fleet-supervisor\decisions\2026-09-09-ontoloche-decisions.html`; where the two disagree, this file is the one that was checked most recently.

**11 open · 16 ruled · 7 FYI** *(2026-11-18: item 31 added, Q108, a refusal question row 7b's review found; non-blocking, the current behaviour is the default in force. 2026-11-18: items 28 to 30 added, the three refusal questions in `INGEST.md` §11 that were never carried here. None blocks row 7b, which builds the spec's default for each. 2026-11-17: item 23 ruled `fold into the build row`, R111, row 8c opens. 2026-11-16: row 8a merged into main with row 8b's items; item 27 ruled `fix and land`; from now on only refusal rulings come here. 2026-11-15: item 27 added, row 8a round 6 found one MAJOR. 2026-11-15: item 26 ruled `round 6`. 2026-11-13: item 26 added, row 8a stopped at the review cap. 2026-11-12: items 19 to 23 added by row 8b, Q103 to Q107, none blocking. Item 23 asks whether row 8b's open round-5 findings get a fix pass. 2026-11-12: item 25 added, open, row 8a round 4. 2026-11-12: item 24 added and ruled, R109–R110, row 8a. 2026-09-22: item 18 added and ruled `adopt B`, recorded as R108. R105–R107 ruled in session and recorded at [`2026-09-22-founder-rulings-R105-R107.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-09-22-founder-rulings-R105-R107.md). The local HTML page was not regenerated for this change.)*

**2026-09-09: you ruled all three open items in one pass, including the oldest and largest question in the project.** Q56 is closed after ten days and twenty-three kill-row trips; the governance stop criterion is armed and has fired; and the namespace item turned out to name something that does not exist. Details in section E.

One new item is below, and it exists because ruling item 4 uncovered it rather than because anything went wrong.

---

## A. Decide when you want to — 11 items

### 28 · `Q87` — should the ingest loop refuse to propose when no consumer is registered for the namespace?

*New 2026-11-18, carried from [`INGEST.md` §11](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INGEST.md) where row 7a raised it on 2026-09-04. It never reached this page.*

**TL;DR.** `consumers()` exists so nobody proposes a new thing blind. When it returns `known=0` for a namespace, the spec today keeps going and puts `consumers_unregistered` on the resolution. The stronger reading is that the propose path refuses outright, which turns an unmet host obligation into a hard stop in somebody else's deployment.

**Why it is yours.** It decides whether the registry refuses a proposal.

- **`warn`** — today's spec: resolve and propose, carrying `consumers_unregistered`.
- **`refuse`** — the propose path refuses on a namespace with no registered consumer. Resolution still answers.
- **`recommend`** — I bring the per-case rule with fixture counts once row 7c has the propose path running.

**Ask: `warn`, `refuse`, or `recommend`.** Default in force: `warn`. Row 7b builds it that way and pins it; row 7c is where proposing lands.

### 29 · `Q89` — should the registry refuse a self-review?

*New 2026-11-18, carried from `INGEST.md` §11 (contortion ING9).*

**TL;DR.** R73's argument for `review_invocation` is that a review is a second act by a second person at a later time. **[Observed in the spec]** nothing enforces the second person. The ingest loop is the caller that makes this matter: a batch of a thousand rows with a thousand self-reviews is a drained queue that reviewed nothing.

**Why it is yours.** It decides whether `review_invocation` refuses a call.

- **`refuse`** — the reviewer must differ from the actor that recorded the invocation.
- **`warn`** — accept it and carry a warning naming the self-review.
- **`allow`** — today's behaviour, no check.

**Ask: `refuse`, `warn`, or `allow`.** Default in force: `allow`, the shipped `review_invocation`. Row 7b does not touch it. Row 7c drives the review queue and would build your answer if it arrives first.

### 30 · `Q91` — when a retire hands a type to a successor with different governed facts, should `resolve_instance` decline to answer?

*New 2026-11-18, carried from `INGEST.md` §11, where it was always marked yours.*

**TL;DR.** After `retire(successor=...)`, the successor's entry may declare a different match policy or tenancy predicate. **[Observed in row 7a's design test]** one retire over the CA and CO fixture let a California caller see a Colorado row, and 73 of 1,373 real CMS labels resolved differently for one caller. The spec's default refuses to inherit: the hop answers `unknowable` until the host declares the successor's facts. That is safe and loud, and it stops a live ingest loop on every retire.

**Why it is yours.** `unknowable` versus answering with a warning is the same choice you made for `resolve_type` in Q56 (`read`, R99), which allowed answering below 1.0 and refusing.

- **`unknowable`** — the spec's default (a): no inheritance, the loop stops until the host acts.
- **`warn`** — reading (c): inherit and keep answering, with a warning naming the changed fact.
- Silent inheritance, reading (b), is refused by the spec and not offered.

**Ask: `unknowable` or `warn`.** Default in force: `unknowable`. Row 7b builds that and pins it.

### 31 · `Q108` — should `resolve_instance` serve a retired type that has no successor?

*New 2026-11-18, found by row 7b's adversarial review (round 3) and routed by the supervisor as a refusal question.*

**TL;DR.** When an entity type is retired with no successor, and no live entity type holds its name as an alias, `resolve_instance` still reads the retired type's own host rows. **[Observed]** it answers `existing legacy_home#015009` for a known label, proposes a new instance under `legacy_home` for an unknown one, and `get_instance_checked("legacy_home", "015009")` returns the row. `resolve_type("legacy_home")` answers `proposal` for the same word, so the two doors disagree about whether the retired type is still in service.

**Why it is yours.** It decides whether the registry keeps serving a retired type, which is what the registry refuses or holds. INGEST.md 3.4a governs a retired entry only through its successor chain, and no rule row says what happens when there is none. The build's reading is that rules 3-14, 3-15 and 3-19 put a retired member's rows in the extent [Inferred].

- **`serve`** — as today: answer from the tombstone's own rows, including proposals under the retired name.
- **`unknowable`** — decline under Rule U until the host names a successor or an alias holder.
- **`refuse`** — a `Refusal` saying the type is retired, so a caller cannot mistake it for an empty or undecided read.

**Ask: `serve`, `unknowable` or `refuse`.** Default in force: `serve` (current behaviour). Non-blocking: row 7b lands with it and pins it in `C20-80` r4 ([`7B-RUN.md` §2.4](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7B-RUN.md)).

### 22 · `Q106` — a Foundry property with no description: import it with a warning, or decline it?

*New 2026-11-12. Row 8b. The brief says a property's description is required, and Foundry makes it optional.*

**TL;DR.** **[Observed]** 61 of the 75 properties in Palantir's main test ontology (`legacy`, as committed) have no description, and every one of its ten object types has at least one. Requiring a description at import would decline all ten. **Your R109 already holds half of that fixture for a different reason** (*corrected 2026-11-17 by row 8c, from row 8b's finding*): 5 of the 10 object types, all 6 link types and 5 action types have no definition, so they come back held until you pass their text in a `definitions=` map. So the fixture does not land in one call today whichever way you rule. `like types` would add 61 property descriptions to that same map. Writing a placeholder would put a definition nobody wrote into the vocabulary.

**Why it is yours.** Declining a row is a refusal. Foundry `active` types also import as `active` and never pass `approve`, so "require it at approval" does not catch them.

**What you ruled for types, and why it does not settle this.** Row 8a recorded your `hold + override map` answer for a Foundry *type* with no description (R109, now on `main`): nothing is written, the row comes back refused, and the caller supplies the missing text and imports again. That ruling chose between holding the row and filing a proposal with placeholder text. **Writing it with no description was never an option for a type**, because a type's definition must be non-empty in the code (`registry.py:2596`) and in the database (`0001_init.sql:21`). A property's description has no such constraint, so `keep and warn` below is new and you have not weighed it.

- **`like types`** — hold the row, as for a type: nothing is written, it comes back refused naming each undescribed property, and the caller passes the missing descriptions and imports again. Consistent with your type ruling, and 61 descriptions must be supplied before Palantir's fixture lands.
- **`keep and warn`** — write the slot with no description and warn, naming it. The import succeeds, nothing is fabricated, and the warning lists what a person must fill in.
- **`decline`** — refuse the row with no way to supply the text in the same call. Faithful to the brief, and it fails Palantir's fixture.
- **`recommend`** — I bring you the per-case rule with the fixture counts.

**Ask: `like types`, `keep and warn`, `decline`, or `recommend`.** Default in force: the shipped `import_types` checks no property description, so a slot with none is written as given with no warning. Row 8c's importer turns Foundry properties into slots and keeps that default: it leaves an absent or empty description out of the slot and fills in nothing. **This question is now only about a property on an entity.** A Foundry *shared* property type is imported as its own entry, so it is a type, and R109 already holds it when it has no description. Spec rule 2.10-21 is `reserved: Q106`. I have no lean between `like types` and `keep and warn`: the first is consistent with your type ruling, the second keeps the import easy, and the type case never had to choose.

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

### 25 · Row 8a: should a Foundry import write over a live row Foundry did not import?

*New, 2026-11-12. Found by row 8a's adversarial round 4. Not blocking: the row ships with the behaviour below reported, and your answer changes a refusal, which is yours to make.*

**What happens today.** `import_types` has always replaced a standing row's predicates, aliases and attributes, and its definition when one is supplied ([`INTERFACE.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/specs/INTERFACE.md) §2.5). `import_foundry` makes that routine. A reviewer seeded a locally approved `employee` with the predicate `audited`, registered a consumer gating on `audited`, and imported a Foundry `Employee`. The local predicate and definition were gone, and the consumer's gate matched nothing. `retire` refuses the same effect with `live_consumers`.

**What row 8a did.** Reported, not refused. Each item that would write over a live row now carries `detail["replaces"]` (what would be dropped, and which system wrote the standing row), on the dry run as well, so the loss is visible before anything is written. `C12-61`.

**The question, two parts.**
- **(a)** Should `import_foundry` hold or refuse writing over a live row whose `imported_from` is not `foundry`? Options: `report` (today), `hold` (a new hold reason, lifted by a map like R109's), or `refuse when a consumer gates on a dropped predicate` (the `live_consumers` reasoning).
- **(b)** On a re-run without `definitions=`, the planner holds `definition_missing` on a row the store already defines, while `import_types` itself would keep the stored definition. So a Foundry status change to that row is not applied. Options: `hold` (today, R109 read literally) or `lift the hold when the store holds a definition of that kind`.


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

## E. Ruled — 16 items

### 23 · `Q107` — row 8b stopped at its five-round cap with five MAJOR findings open in the spec. Run a sixth, fix-and-review pass? → **RULED: `fold into the build row`** *(2026-11-17)*

**Ruled `fold into the build row`**, recorded as R111 ([`2026-11-17-founder-ruling-R111.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-11-17-founder-ruling-R111.md)). Row 8c's first task is the 14 findings in `8B-RUN.md` §2.5, each fix reviewed by row 8c's loop with the code. D14 stays unrouted and out of row 8c's scope.

*New 2026-11-12. Row 8b. Not blocking anything that runs today: no code implements §2.10 yet.*

**TL;DR.** Row 8b's spec amendment (`INTERFACE.md` §2.10) went through five adversarial rounds, the cap it set itself before round 1. Round 5 still found **5 distinct MAJOR and 9 MINOR**, so under its own rule it stopped and brought them instead of fixing them. All are wording a build row would have to guess at, three of the five MAJORs are in the reference reader (rule 2.10-11), and every one has a proposed fix. The list is [`8B-RUN.md` §2.5](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8B-RUN.md).

**Why it is yours.** The cap is the row's own commitment, and only you can lift it. Applying unreviewed fixes would put text into the spec that no adversary has seen, which is the thing the loop exists to prevent.

- **`fix pass`** — open a short follow-on: apply the 14 proposed fixes, then run fresh lenses until one full round finds no MAJOR, with its own cap. The build row then starts from a reviewed reader.
- **`fold into the build row`** — leave §2.10 as it is and make the 14 findings the properties build row's first task, reviewed with its code.
- **`leave`** — accept §2.10 as landed. A build row will meet these gaps and decide them itself.

**Also carried here, unrouted:** a defect older than row 8b, found by its round 4 and reproduced (probe line D14). After `retire(word, successor=X)`, importing another entry with that word as an alias is written silently, so one word has two live claimants, for every kind, and the retired word can no longer be reinstated. It does not reach the kill row (the predicate version is refused). No row carries it yet.

### 27 · Row 8a round 6 found one MAJOR. Fix it and land, or land as is? → **RULED: `fix and land`** *(2026-11-16)*

**Ruled with the recommended scope:** a `foundry_*` carry key is left out of `attributes_changed` when the standing row came from Foundry, and `visibility`, `groups` and the edge declaration keys are always reported. **Built** as `C12-68`, and the row lands without another review round. **Standing instruction from the same answer:** only refusal rulings come to you. A report field, a test, a process or a cap choice is decided by the running session, recorded in that row's run record, and does not stop the row.

*Asked 2026-11-15. Item 26 ruled `round 6` without saying whether round 6 had its own cap, so it was read the narrow way: a MAJOR comes back to you. Full table: [`8A-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8A-RUN.md) §1.6, round 6 review.*

**Where the row stands.** Round 5's six are fixed at `afab2f4`: 2136 passed, 0 failed, all five gates exit 0, 42 of 42 mutations killed. Two of round 6's three lenses (tests, mapping) said ship it.

**The one MAJOR.** `detail["replaces"]` compares attribute *keys*, never values. So a write that changes a value under a key both rows carry says nothing. Observed: a local `visibility: "restricted"` became `NORMAL`, and a local edge family's `symmetric: True` became `False`, with `replaces` silent on both. It is a report, not a refusal.

**The fix would be** an `attributes_changed` list for shared keys whose values differ. One choice is yours inside it: on a re-import of a row Foundry already wrote, should a changed `foundry_*` carry key count (it fires on every legitimate change to the Foundry document), or only the keys the importer does not own (`visibility`, `groups`, the edge declaration keys)?

**Options.**
- **`fix and land`** *(my recommendation)*: add `attributes_changed`, excluding `foundry_*` keys when the standing row was imported from Foundry, pin it, mutation, full suite, and land without another review round. It is one line of comparison in code that two lenses already passed.
- **`fix and review`**: the same fix, then one more fresh round.
- **`land as is`**: land `afab2f4` with this recorded as a known defect for a later row.

### 26 · Row 8a stopped at the review cap. Fix the six MAJORs in a sixth round, or land as is? → **RULED: `round 6`** *(2026-11-15)*

**Built.** Round 5's six are fixed and pinned as `C12-65`–`C12-67` (`8A-RUN.md` §1.6, round 6). The ruling did not say whether round 6 has its own cap, so it is read the narrow way: one fresh review round, and a MAJOR it finds comes back to you rather than starting a seventh.

*Asked 2026-11-13. §0.9 item 3 capped the adversarial loop at five rounds and said a MAJOR in round 5 comes to you. Round 5 found six. Full table: [`8A-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8A-RUN.md) §1.6, round 5.*

**Where the row stands.** Committed through round 4 (`ea5b7a7`): 2118 passed, 0 failed, all five gates exit 0. The importer's holds, refusals and mapping held up under all three round-5 lenses.

**The six.** Three are defects or gaps in round 4's own fix, `detail["replaces"]` (a false loss on every re-run of an `EXPERIMENTAL` or `ENDORSED` type, a status change and a provenance overwrite not reported, and most of the field unpinned). Two are test gaps where the code is right (a `names=` rename on an edge's endpoints, a blank `definitions=` value). One is older than the row: a backend that declines `stores_attributes` drops everything the importer carries, and no warning exists for that anywhere in the package.

**None of the six adds a refusal.** All are reports, warnings or tests.

**Options.**
- **`round 6`** *(my recommendation)*: fix all six, add the tests, prove them by mutation, full suite, then one more fresh round. The pattern so far is that each round's fixes carry the next round's MAJORs, so a sixth round could find more. If you take this, say whether round 6 gets its own cap (one round, then land whatever it finds as recorded defects).
- **`land as is`**: land `ea5b7a7` with the six recorded as known defects in `8A-RUN.md`, for a later row.
- **`fix 1 to 2 only`**: fix the false-loss defect and the unreported status change (the two that make `replaces` say something untrue or omit the biggest loss), land, and leave the test gaps and the attribute warning for a later row.

### 24 · Row 8a's two Foundry import questions → **RULED: `hold + override map` (R109) and `hold both + names map` (R110)** *(2026-11-12)*

**Recorded as [R109–R110](https://github.com/stephan-dyson/ontoloche/blob/main/docs/decisions/2026-11-12-founder-rulings-R109-R110.md).** Numbered provisionally, because row 8b runs in parallel on `main` and may mint rulings of its own first. Row 8b's `Q106` (item 22 on `main`) already cites R109 as provisional, so if the numbers move, that citation moves with them. **Item 24**, because `main` has taken items 19 to 23 for row 8b (`Q103`–`Q107`).

*New 2026-11-12. Asked by row 8a before its §0 was written, because both decide what the registry refuses.*

**R109, a Foundry type with no description.** The brief said import it as `proposed`. In this registry `proposed` is a proposal record, which needs a definition too, so that instruction had nowhere to land. You chose `hold + override map`: nothing is written, the row comes back `import_refused:definition_missing`, and the caller passes `definitions={apiName: text}` and imports again. `"imported from foundry"` is never written as a definition again. **Built and tested as `C12-33` and `C12-38`.** Every Foundry link type is held under it, because a link side has no description field at all.

**R110, two Foundry names that convert to one.** `NursingHome` and `Nursing_Home` both become `nursing_home`, and without a rule the second silently replaced the first. You chose `hold both + names map`: every member of the collision is held, `names={apiName: name}` resolves it, and a mapped name goes through the same check so the map cannot create a collision of its own. **Built and tested as `C12-37`.**

**Nothing else from row 8a needs you.** Brief questions 2 to 4 do not decide a refusal in this row and have interim answers in [`8A-RUN.md`](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/8A-RUN.md) §0.7. Route 4 (a real Foundry instance through the AIP Developer Tier) stays your call and was not attempted.

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
