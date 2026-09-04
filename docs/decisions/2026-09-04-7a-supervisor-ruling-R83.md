# R83 — is row 7a's truncated-scan defect a fifteenth kill-row trip?

**Ruled 2026-09-04 by the ontoloche program supervisor**, on the question row 7a's worker
left open for countersignature at [`7A-RUN.md` §6.2a](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md).
Verified against the commits (`d9faebb`, `39c7322`, `7d0aa28`, `2dc6b31`, `07af54f`, `39d3718`)
and against the register itself, not against the worker's paragraph.

## The question

Round 1 of row 7a's adversarial loop found, from two lenses independently, that a truncated
candidate scan which *finds* a match answers `existing` at confidence `1.0` on
`"MILLER'S MERRY MANOR"` — a label **twelve** distinct Indiana CMS facilities answer to —
and the public-data lens proved the row's own gate blind to it **by mutation** (deleting
`INGEST.md` §3.4's load-bearing sentence left the probe still printing 16/16 pass).

The worker recorded it in the fourteen trip records' shape, offered its reading for
countersignature, and asked the supervisor to classify it: **is this the register's
fifteenth kill-row trip, or is it `INGEST.md`'s own defect?**

## R83, in one sentence

**It is not a fifteenth trip — the kill-row count stays at fourteen — and it is nonetheless
recorded in the register, as the first entry in a separate series: the instance-surface
records, numbered `I-n`, which never merge with the trip count.**

The worker's reading is adopted on the classification. What is added is where the finding
then lives, so that "not a trip" does not become "not recorded".

## Why it is not a trip

**1. What the register's count actually counts.** Every one of the fourteen is a state
*constructed against shipped code* and put to a *shipped door*, and every record carries the
same refrain to say so — `namespace` untouched, `cross_namespace_merge` still refusing on
live NYC data, caught in test, none in a real merge. That refrain is not decoration; it is
what the number means. Row 7a ships no door. **[Observed]** `git diff --name-only a1b0364^..39d3718 -- ontoloche/`
returns **nothing**: the row's 4,114 lines are `docs/specs/`, `docs/runs/` and `docs/tools/`
probes, exactly as its brief fenced it. `resolve_instance` exists as rules 3-1…3-7 and a
probe, and as nothing else.

Incrementing the count to fifteen would quietly change the sentence *"fifteen trips in test,
none in a real merge"* into a sentence about two different kinds of object. The register's
one durable statistic would stop meaning anything, and it would stop meaning anything at the
exact moment the founder's `stop` question is still open on it.

**2. `stop` is therefore NOT put an eleventh time here.** The ten puts are attached to trips.
This is not one, and the countersignature does not get to borrow a trip's weight for a record
that is not a trip. Q56 remains the class-closing question for the read side and remains the
founder's; defaults in force are unchanged.

## Why it is recorded anyway

**3. Route 1 is the fifth trip verbatim, one identity surface down — verified.** The fifth
trip's record reads: *"Nobody had closed* partial is not equal *— and the read path had been
publishing exactly that fact, as `PredicateEntry.why_extent_incomplete`, since row 3c. The
guards discarded the one signal the read emits."* §6.2a's construction is that sentence with
the nouns changed: the candidate primitive publishes `complete=False` **with a `why`**, and
`resolve_instance`'s tie test is evaluated over `scanned=3541 of 14627` as though it were the
set. Same operand (`partial`), same discarded signal, new surface. The worker's cross-reference
is confirmed, not merely repeated.

**4. The register's *rules* have already crossed to the instance surface even though its
*trips* have not.** By the round's own dispositions: **K4** is standing rule (c) one surface
down (*a pending ingest proposal is an unconsumed permission to mint an instance identity, and
no door asks who already holds one for this word*); **K7** is standing rule (d) **measured** —
one document, one row, one rule (§3.4), and the row's own two probes order it opposite ways.
A register that counted only what it could count, and recorded nothing else, would have lost
both of those. Hence the `I-n` series: the rules travel, the count does not, and the two are
kept legible apart.

**5. The new fact, and it is the cheapest finding in the register's history.** The thirteenth
countersignature named *the loop reaching past its own diff*. This is its inverse: **the loop
reaching before the diff exists.** The fourteen trips were paid for at two or three adversarial
rounds taxed off each build row from 4c onward. This one cost one round of a spec row over a
surface with no code written yet — no guard to extend, no callers to enumerate, no suite floor
to hold, no regression to bisect. That is the first hard evidence for constraint 7's loop being
run *before* a build row rather than only inside one, and row 7a is the first row to have done
it. It belongs in the `stop` question's counterweight column as an argument about **where** the
loop runs, not as an eleventh put.

**6. K6's shipped half is Q56's, not a trip's.** §6.2b's K6 is the round's one finding
constructed against the **shipped** `Registry`, so it is the one that could have been a trip.
It is not. Its shipped half — `resolve_type('facility')` answering `existing / nursing_facility / 1.0`
after `retire(successor=)` — is the specified redirect behaviour, and the question of whether
that `1.0` should carry a warning when the two extents no longer agree **is Q56**, already
founder-visible with the shipped behaviour as the standing default. K6's defect is the
*unshipped* half: an identity read that does not follow the successor chain `EDGES.md` rule
4.3-14 / **R38** requires of `neighbors`, and `InstanceRecord.type_name` being the host's raw
string. Recorded here so the register is not asked this a second time.

## What this changes

**7. The dedicated identity-surface row's surface widens.** The fourteenth countersignature
(§4) recommended the kill row's next home be a dedicated identity-surface row, scoped to
`_word_rows`, `_alias_holder`, `_alias_clash`, `_identity_stale` and the five doors — all of
them **type**-identity. `I-1` says that surface has an **instance half**, and that the fourteen
records are not a lens over it: they are constructed at a door that mints or merges a *word*,
and `I-1` was reached at a door that resolves a *row*. So that row's brief gains, when the
founder opens it:

- lenses = the fourteen trip records **and** the `I-n` records;
- surface = both halves, with the instance doors added once the `INGEST` build row has landed
  any;
- sequencing unchanged — behind the Layer B spec row, in the actions-continuation slot.

**8. Unchanged:** standing rules (a)–(d) stand as written and are confirmed to bind the
instance surface as well as the type surface; the trip count is fourteen; Q56 is the
class-closing question and the founder's; row 7a's `stop` recommendation is not restated
because row 7a has no trip to attach one to.

## What row 7a's worker does with this

1. Record R83 at `7A-RUN.md` §6.2a as the supervisor countersignature of the record, adopting
   the worker's reading on the classification.
2. Label the record **`I-1`** and say in one line that it is the first of a series distinct
   from the trip count.
3. Do **not** increment the kill-row count anywhere — it stays fourteen in
   `7A-RUN.md`, `INGEST.md`, `STATUS.md` and the register.
4. Carry K1's accepted fix as round 1's fix already did; nothing in R83 reopens a disposition.
5. Proceed to round 2. The loop's cap of 3 is unchanged and round 1 counts as round 1.

Next ruling number: **R84**. Next question number: **Q91** (Q85–Q90 exist in `INGEST.md` §11).
