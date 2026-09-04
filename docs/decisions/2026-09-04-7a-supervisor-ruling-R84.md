# R84 — `I-2` countersigned, and standing rule (d)'s enumeration crosses the document boundary

**Ruled 2026-09-04 by the ontoloche program supervisor**, on the record row 7a's worker
routed for ruling at [`7A-RUN.md` §6.5a](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/7A-RUN.md),
landed at `98dd47c`. Verified against the two files the record cites, not against the record's
paragraph.

## The record

Round 2's fix-auditor lens, pointed at round 1's own fixes (`07af54f`, `39d3718`), found that
rule **3-14** / `C20-68` — minted in round 1 to close K6, and stating that the identity read
resolves `type_name` *"through the successor **chain** … as `neighbors` does under **R38**"* —
is implemented as a `while` whose body ends in an unconditional `break`. Two ordinary
`retire(successor=)` passes then produce **two confident answers at 1.0 for one type identity**:
`cms:entity:nursing_facility#999999` against `cms:entity:ltc_facility#015009`.

The worker classified it as `I-2` under R83 and explicitly declined to rule on itself.

## R84, in one sentence

**`I-2` is confirmed — it is a second instance-surface record, not a fifteenth kill-row trip,
and the count stays at fourteen — and standing rule (d) gains a second clause: the enumeration
a minted rule owes crosses the document boundary into shipped code.**

## Verification, done here rather than accepted

- **The one-hop `break` is where the record says.** **[Observed]**
  `docs/tools/ingest_probe_kit.py:491–499`: `while entry is not None and entry.successor and
  entry.successor not in seen:` … `entry = vocab.entry(namespace, effective_type) or entry` …
  `break`. The loop cannot iterate.
- **The shipped caller is where the record says, and it is correct.** **[Observed]**
  `ontoloche/registry.py:1403` onward carries the comment *"**The chain, not one hop** (row 4d,
  round 2). This read ONE successor and required it to be live, so a vocabulary curated
  **twice** — the ordinary outcome after two passes — lost §5.10's promise"*, and at
  `registry.py:1421` *"Capped and cycle-guarded the way `_identity_closure` is: §5.9 does not
  forbid constructing a cycle, so the walk must survive one."*

## Why it is `I-2` and not a trip — and the ground is firmer than the record claims

R83's test is whether a **shipped door** was defective. The record argues the negative case:
this was constructed against a specification and a throwaway kit. True, and there is a stronger
statement available that the record did not make.

**The shipped surface is the CONTROL in this construction, and it PASSES.** `_identity_closure`
already walks the chain with a visited set, a hop cap, and an honest early stop. So this is not
a defect the register could not reach at the type surface — it is one the type surface
**already closed**, in row 4d round 2, which the spec then re-opened one document along by
restating the ruling instead of citing the implementation. A construction whose shipped control
passes is not a kill-row trip by any reading. **`I-2` confirmed; the count stays at fourteen;
`stop` is not put, because `stop` attaches to trips.**

## The substance: standing rule (d) gains a second clause

Standing rule (d), minted at the fourteenth countersignature: *a rule minted at the caller that
prompted it is half-applied until the commit that mints it names every other caller it binds.*

Round 1 **invoked rule (d) as the reason rule 3-14 existed**, then enumerated only the callers
inside the document it was writing. The caller it missed was in shipped code — and that caller
had already solved the problem correctly, four years of trips earlier in this register's own
history. Rule (d) was applied and failed in the same commit that cited it, which is a sharper
version of the failure rule (d) was minted to describe.

**So rule (d) reads, from here:**

> A rule minted at the caller that prompted it is half-applied until the commit that mints it
> names every other caller it binds — **and the enumeration crosses the document boundary. A
> rule minted in a specification must name the shipped callers it binds; and where a shipped
> caller already implements the rule, the specification cites that implementation as its
> normative reference rather than restating the ruling the implementation was derived from.**

Rule 3-14 cites **R38** and implements none of R38's three termination rules. `_identity_closure`
implements all three. The spec should have pointed at the code.

## What the fix must be, so this is not closed narrowly

The register's own count says the next defect lives inside the last fix, and this record IS that
pattern. The fix is therefore not "add a loop":

1. **Rule 3-14 requires what `_identity_closure` requires** — visited set, hop cap, and
   `complete=False` **with a `why`** when the walk stops early. **[Inferred]** from the record's
   own point 1: rules 3-5 / 3-6 guard the completeness the read *reports*, and this read reports
   `complete=True` with `why_incomplete=''`, so an honest early stop is what makes this class
   visible to round 1's headline fix at all. Verify that inference by construction rather than
   accepting it.
2. **The rider defect in the same four lines is closed in the same change** —
   `entry = vocab.entry(namespace, effective_type) or entry` keeps the **predecessor's** entry
   when the successor's is absent, so the read queries one type while holding another's entry.
   That is the **eighth** trip's shape (a guard holding one fact while deciding about another)
   and it does not get to ride out of this round unnamed.
3. **Rule 3-14's text names the shipped caller** it binds, per the new clause above.

## Unchanged

Kill-row trip count is **fourteen**. Q56 remains the class-closing question for the read side
and the founder's. Standing rules (a)–(c) stand as written; (d) is sharpened, not replaced. The
dedicated identity-surface row recommended at the fourteenth countersignature §4 now has **two**
instance-surface records in its lens set.

## What row 7a's worker does with this

1. Splice a pointer to R84 into `7A-RUN.md` §6.5a — the record is **countersigned**, `I-2`
   stands, and the classification is no longer "proposed".
2. Apply the three-part fix above when round 2's fix set is written; do not close `I-2`
   narrowly.
3. Carry the sharpened rule (d) into `7A-RUN.md`'s round-2 section and into the register entry.
4. Do not increment the kill-row count anywhere.

Next ruling number: **R85**. Next question number: **Q91**.
