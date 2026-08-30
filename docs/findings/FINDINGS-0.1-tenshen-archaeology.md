# Finding 0.1 — Tenshen archaeology

**Status:** Complete, 2026-08-27. Satisfies `ROADMAP.md` §0.1's exit criterion.
**Method:** `git log -S` on each of the seven vocabularies against `origin/master`, plus reading each declaration's surrounding comment and its call sites.
**Executed by:** agent, in-repo. No founder time spent.

---

## Read this before the verdict — what this finding does and does not test

**The four mechanisms in `ROADMAP.md` §0 are hypotheses about why the ontology at the partner agency got polluted.** They were written to describe a multi-team Foundry deployment with rotating contractors. **This finding did not test them.** It examined a different system — single-owner, AI-authored, no procurement, no teams — and found a different set of causes.

**A poor fit between those four mechanisms and Tenshen is therefore not evidence against them.** It is evidence that the two systems have different diseases, which is itself the useful result. The founder's standing read on the partner-agency side — *too complex, vendor lock-in, already polluted* — remains **untested and unchallenged by anything below.** §0.2 is its test, and this document has no bearing on it.

## Verdict, first

**In Tenshen, the seven vocabularies are mostly not duplicates at all**, and the one documented production incident was caused by a mechanism the four-row table does not name.

Three distinct things are happening:

| Cause | Count | Is it pollution? | Roadmap mechanism |
|---|---|---|---|
| **A — capability predicates** | 5 of 7 | **No.** Each answers a different question and is correct | none — the table has no row for "healthy" |
| **B — semantic collision** | 2 of 7 | Yes | **Mechanism 4** — the kill-criterion one |
| **C — silent per-consumer drop** | the actual harm | Yes, and it shipped a bug | **absent from the table** |

In this codebase: **mechanism 4 is present**, mechanisms 1 and 3 are largely absent, and the mechanism that caused real damage is a fifth one. Whether any of that holds at the partner agency is unknown and untestable from here.

---

## The seven, and what each actually means

| Vocabulary | File | Born | Values | The question it answers |
|---|---|---|---|---|
| `_ALLOWED_ENTITY_TYPES` | `assistant/actions/search_audit.py` | 2026-04-21 `cb5581d3` | task, project, person, reminder, organization, note | what can be **searched** |
| `entity_type` | `docs/architecture/event-spine.md` | 2026-05-09 `eb29b906` | task, project, person, meeting, decision, open_loop, draft | what a spine **event** can be about |
| `ENTITY_MODEL` | `services/collab_membership_service.py` | 2026-05-25 `2d576852` | project, task | what can be **shared** |
| `_ENTITY_TYPES` | `services/view_query_spec.py` | 2026-06-13 `8eb1eec6` | person, organization, thing, project | what is a **subject noun** |
| `CLOSED_ENTITY_TYPES` | `services/user_progress_service.py` | 2026-07-30 `0e0200d2` | task, project | what resolves to a **readable page** |
| `_LINKABLE_ENTITY_TYPES` | `services/aura_render.py` | 2026-08-02 `c7edfa90` | task, project, capture | what a **watch can link to** |
| `ENTITY_TYPES` | `services/comment_service.py` | 2026-08-24 `ab304364` | task, project | what can carry **comments** |

Every one arrived inside a **different feature commit**, months apart, spanning 2026-04-21 to 2026-08-24. None was a vocabulary decision. Each author was solving a local problem.

---

## Cause A — most of these are capability predicates, and they are correct (5 of 7)

`CLOSED_ENTITY_TYPES` carries its own comment:

> `# The two entity types that resolve to a page a user can read back.`

That is not a claim about what an entity *is*. It is a claim about which types support one capability. The same is true of `ENTITY_TYPES` (commentable), `_LINKABLE_ENTITY_TYPES` (linkable from a watch), `ENTITY_MODEL` (shareable), and `_ALLOWED_ENTITY_TYPES` (searchable).

**These five are each locally correct and mutually consistent.** They are subsets of one universe, each defined by a different predicate. A registry that detected them as duplicates and merged them would be **destroying true information** — it would assert that anything commentable is searchable, which is false.

**This is the single most important design consequence in this document**, and it is bad news for the interface as drafted: `merge_types` is not merely secondary here, it is *hazardous*. Five of the seven "duplicates" must never be merged.

## Cause B — semantic collision is present (2 of 7)

`view_query_spec.py` declares both lists, one line apart, deliberately:

```python
_RECORD_TYPES = frozenset({"task", "project", "note", "meeting", "open_loop"})
_ENTITY_TYPES = frozenset({"person", "organization", "thing", "project"})
```

Here **"entity" means a subject noun** — a person, an organization, a thing — as opposed to a work record. But in `comment_service.py`, **"entity" means task-or-project**, which `view_query_spec` classifies as *records, not entities*.

The two files use the same word for genuinely different concepts. `project` appears in both, so it is simultaneously an entity and not one, depending on which module is asking.

This is **mechanism 4** — the one `ROADMAP.md` flags as a Phase 1 kill criterion. It occurred **inside one codebase, under a single owner, with no teams involved.** That is worse news than the roadmap anticipated, not better: the roadmap assumed collision required organizational distance.

## Cause C — the harm was silent per-consumer drop, and the table does not name it

`aura_render.py` carries a production incident in a comment. Verbatim:

> `# Entity types a referent can resolve to. no_activity_on accepts an`
> `# arbitrary entity_type string from the compiler, so anything outside this`
> `# set resolves to no link rather than to a guessed route.`
> `# capture joined the set on 2026-08-09. The capture emitters had just been`
> `# wired (an "alert me when something is captured" watch could finally fire),`
> `# and the very first firing rendered "nothing to open" -- the event carried`
> `# entity_type="capture" + the ingest id all along, but this tuple rejected it,`
> `# so the open-and-ack gesture the row already supports was dead for exactly`
> `# the watch kind that had just started working.`

**The mechanism, stated precisely:** a type exists the moment a *producer* emits it. Every *consumer* independently gates on its own allowlist. Adding a type therefore does not fail loudly — it fails **silently, per consumer**, and the feature is simply dead in whichever consumers did not get updated.

Note the shape: nothing was polluted. No duplicate type was created. No merge would have helped. The vocabulary was *too small*, in one place, and nothing reported it. It was found by a human noticing a button did nothing.

**This is the failure that cost real time, and no row in the four-mechanism table describes it.**

---

## Could an author have found an existing list? (the roadmap's second question)

**Partly — and the gap is instructive.**

The obvious grep for `ENTITY_TYPES` across `src/` returns **5 of 7**:

```
search_audit.py:12           _ALLOWED_ENTITY_TYPES
aura_render.py:56            _LINKABLE_ENTITY_TYPES
comment_service.py:28        ENTITY_TYPES
user_progress_service.py:58  CLOSED_ENTITY_TYPES
view_query_spec.py:31        _ENTITY_TYPES
```

It misses `ENTITY_MODEL` (different noun entirely) and the event-spine list (lowercase `entity_type`, inside a SQL column comment, in `docs/` not `src/`).

So discovery was **possible but not prompted**. There is no shared module, no import to trip over, and five different naming conventions (`_ALLOWED_`, `_LINKABLE_`, `CLOSED_`, `_ENTITY_`, bare) across six directories. Crucially: **finding the other lists would not have helped**, because per Cause A the right move was usually to write a *new* predicate anyway. What the author needed was not "does a list exist?" but **"who else gates on this type?"** — and nothing answers that.

---

## What this changes in the Phase 1 interface

**First, the size of the claim.** This is one system's disease. Re-centring the whole interface on it before §0.2 measures the partner agency would be **designing for the consumer we happened to dissect first** — which is precisely the "Tenshen's data model with the names filed off" failure `VISION.md` §9 names. So the changes below are of two kinds, and the difference matters:

- **`consumers(type)` and `predicate` are additions the evidence forced.** A real incident proved `consumers` necessary; five real vocabularies proved `predicate` necessary. These stand regardless of what the partner agency says — the partner agency cannot make them unnecessary.
- **Calling `consumers` "the centre" is provisional.** It is the centre *of Tenshen's disease*. If §0.2 finds the partner agency suffering plain duplicate sprawl, the centre is contested and `resolve_type` may reclaim it. **Do not treat the ordering as settled until 0.2 reports.**

`ROADMAP.md` §1 states the provisional surface, with the note *"`resolve_type` and `merge_types` carry the thesis."* **That note is unsupported — but so is any replacement asserted from this evidence alone.**

| Call | Status after 0.1 |
|---|---|
| `merge_types` | **Demote, and add a guard.** Hazardous against capability predicates — 5 of 7 must never merge. If it survives, it needs to refuse when the two types have different consumer sets |
| `resolve_type` | Keep, demote from centre. It answers a question that was rarely the blocker |
| `usage` / `provenance` / `list_types` / `propose_type` | Unchanged, still bookkeeping |
| **`consumers(type)` → who gates on this** | **NEW, and required.** "If I add type X, which code paths silently drop it?" The call that would have prevented the only documented incident. *Provisionally* the centre — confirm or contest at 0.2 |
| **`predicate` as a first-class concept** | **NEW.** The registry must be able to hold "commentable", "searchable", "linkable" as named capability sets, distinct from the type list — otherwise it cannot represent Cause A without flattening it |

**Kill criterion check.** `ROADMAP.md` §1 says: *stop and redesign if the dominant mechanism is semantic collision across teams.* Collision **is** present (Cause B), but it is not dominant (2 of 7) and not across teams. **Not a kill — but a re-centering**, and the merge-centred shape the roadmap warned about is confirmed to be the wrong centre.

---

## Limits of this evidence — read before generalising

0. **This tested Tenshen; it did not test the Foundry hypotheses.** An earlier revision of this document scored the founder's partner-agency read (*too complex / vendor lock-in / already polluted*) against Tenshen evidence and called it unsupported. That was a category error — those are claims about a multi-team Foundry deployment and nothing in a single-owner codebase can speak to them. **They remain live and untested.** Recorded because the error was in the conclusion, not the data.
1. **N=1 codebase**, single owner, AI-authored commits. The partner agency is multi-team with rotating contractors; §0.2 may find a completely different distribution, and mechanisms 1 and 3 (no review, never retired) may well dominate *there* even though they are weak here. **The absence of teams is the whole point** — Tenshen structurally *cannot* exhibit contractor rotation or cross-team collision, so their absence here is a property of the sample, not a finding.
2. **Cause A vs Cause B is my reading of intent** from names, comments and call sites. It was not confirmed with the authors. The `view_query_spec` collision is solid because the file declares both lists side by side; the capability-predicate reading of the other five is an inference from comments — strong, but not certified.
3. **Only one incident is documented.** Others may exist unrecorded, and their mechanism could differ.
4. **Seven vocabularies is a small sample.** A real disagreement rate cannot be estimated from it.

## What this makes cheaper in Phase 0.2

The partner conversation should now ask a sharper question than "why did it get polluted?" Ask instead:

- **"When someone adds a new object type, how do they find out what breaks?"** — tests Cause C directly, and it is the question with a known-expensive answer here.
- **"Do two teams use the same word for different things?"** — tests Cause B, the kill criterion.
- The original pollution question stays, but it is now the *third* priority, not the first.
