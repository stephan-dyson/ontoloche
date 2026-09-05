# R90 — the fourteen-countersignature refrain was two claims; not a fifteenth trip; and the supervisor owns the half it repeated without driving

**Ruled 2026-09-04 by the ontoloche program supervisor**, countersigning row 6d's first lens record at
[`6D-RUN.md` §6.1](https://github.com/stephan-dyson/ontoloche/blob/main/docs/runs/6D-RUN.md), landed
at `fdc6ca5`. Follows [R89](2026-09-04-founder-ruling-R89.md), the founder's ruling that opened this row.

## Verification, done here rather than accepted

- **[Observed]** `def _search_namespaces` is at `ontoloche/registry.py:1750`.
- **[Observed]** `sed -n '1750,1990p' ontoloche/registry.py | grep -c 'same_word\|identity_key'` → **0**.
- **[Observed]** the same grep over the whole file → **41** matching lines. The record says 27; the
  difference is the grep's shape, not the claim's — **zero inside the one multi-namespace guard against
  dozens everywhere else** is the fact, and it reproduces.

## R90, part one: the refrain was two claims, and the register adopts the split

For fourteen consecutive countersignatures this register wrote, verbatim, *"`namespace` is untouched
across all fourteen trips and `cross_namespace_merge` still refuses on live NYC data."* §6.1 shows it is
**two** claims:

1. ***`cross_namespace_merge` still refuses on live NYC data*** — **true, and for the first time driven
   rather than asserted.** Live Socrata headers for three agencies, the seven words two agencies both
   hold, merged across the boundary: **6 of 6 refused**, on sqlite and on the paging double.
2. ***`namespace` is untouched across all fourteen trips*** — **true as history and false as safety.** It
   was untouched because nothing had ever asked it. Asking produced six findings.

Adopted. From here the register does not write the sentence again in that form. The two halves are
stated separately, and the second is stated as what it is: *a claim no lens had tested*, until row 6d.

## R90, part two: the supervisor owns the half it repeated

**This countersignature does not get to file the finding as the worker's alone.** R83 quoted the refrain
approvingly as *"the count's meaning"* — the reason fourteen trips could be counted as one kind of thing
— and R84 through R88 rested on it. The supervisor repeated a claim it had never driven, in the section
of the register whose purpose is to make untested claims visible. That is the failure this register's
own rule about causal claims was written for, and it is recorded here in the same words the rule uses:
**a claim stated without its evidence is a detectable object, and this one sat undetected for fourteen
rounds because everyone who repeated it, including the supervisor, mistook repetition for evidence.**

Row 6d's §0.6 — *what would falsify the ROW's reading rather than confirm it* — is the mechanism that
caught it, and it is the mechanism R89 opened this row to install. Recorded so the next supervisor reads
it before repeating anything.

## R90, part three: not a fifteenth trip, and the count stays FOURTEEN

§6.1 is right and it is confirmed: **nothing constructed here lets two identities answer to one word.**
The two negatives the register could never state with evidence are now driven — no write door crosses
the boundary (D1–D6 correctly scoped; `retire(successor=)` refuses `successor_unregistered` with
`found_in: ['dot']`), and no cross-namespace row reaches an identity answer (`resolve_type`,
`list_types(namespace=None, …)` and `_identity_closure` all resolve per namespace; R6 hits stay in
`alternatives`). The six findings are all in `_search_namespaces`, ruling R6's cross-namespace
**advisory** read — a guard that reads more than one namespace and is built out of none of the identity
machinery. That is a real defect surface and it is not the kill row's.

## What this requires of the fix set, when the round closes

1. **`_search_namespaces` is the surface, and the fix is one change over it** — R85's rule, not six
   fixes in lens order. The countable form of "done" is the grep in part one going from 0 to a number,
   with each identity comparison it gains named against the finding it closes.
2. **The fix commit lists what it declined** (R88).
3. **§0.7's scoring table is filled for S3 and every T-record whose prediction named a cross-namespace
   recurrence**, with the falsifier stated in §0.6 marked triggered or not. A prediction confirmed is
   recorded as confirmed; a prediction that the lens could not reach is recorded as *not reached*, never
   as confirmed.

## Unchanged

Kill-row trip count is **FOURTEEN**. Q56 remains the class-closing question for the read side and the
founder's. Standing rules (a)–(e) stand. The `INGEST` build row is not open.

Next ruling number: **R91**. Next question number: **Q94**.
