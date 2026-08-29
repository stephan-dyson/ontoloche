# Rulings 2026-08-28 — the three items PACKAGE.md v0 left open

Supervisor rulings under the founder's make-assumptions directive (`2026-08-28-assumptions-in-lieu-of-office-answers.md`). All three are sequencing / design-consistency calls, not product calls; the founder may reverse any of them. Raised by deliverable #2's author at landing (`48c89dd`, `docs/PACKAGE.md` §11).

## R1 — AsyncStorageAdapter is a new row 3b, not part of #3

**The finding [Observed, PACKAGE.md §7]:** the adapter protocol is synchronous; beacon is `AsyncSession` throughout; a sync adapter cannot share beacon's transaction and driving one from a thread is not safe. So ROADMAP #5 (2B) cannot land without an `AsyncStorageAdapter`.

**Ruling:** a **new row 3b**, after #3 and before #5, may run alongside #4. NOT inside #3, because #3 is already the first code in the repo (skeleton + SQLite backend + contract suite green on CMS data) and 2A needs no async; growing #3 delays the very gate (2A green) that A5 makes load-bearing. 3b's deliverable: the async protocol mirror + an async conformance run of the same 109 tests. **[Assumed]** that mirroring sync→async is mechanical once the sync suite is green; if 3b's author finds it is not, that is a finding for the roadmap, not a licence to redesign #3.

## R2 — `attribute_census` stays package-local, outside conformance

It is derivable from stored data, contract-bears nothing, and no second consumer exists. INTERFACE v0 is not amended for a helper. Revisit at INTERFACE v1 if EDGES (#4) or 2B needs it.

## R3 — `Refusal.reason` is a CLOSED vocabulary, amended in the doc

An open `reason` vocabulary in a project whose thesis is *governed vocabularies resist rot* would be the product's own disease in its own contract. The three PACKAGE-introduced values are adopted into INTERFACE.md (new §5.12), which now enumerates all fourteen and states that additions require amending that section in the same change that introduces them.

The fourteen: `different_consumer_sets`, `predicate_merge`, `kind_mismatch`, `cross_namespace_merge`, `retired_operand`, `definitions_diverge`, `no_consumer_evidence`, `live_consumers`, `tier_below_auto_approve_policy`, `already_decided`, `unknown_proposal`, `proposals_not_stored`, `cannot_record_override`, `attributes_schema_violation`.

## R4 — D-1 gets a fifteenth `Refusal.reason`: `consumer_source_read_only` *(added 2026-08-28 21:20 after 3b landed)*

**The finding [Observed, `2A-RUN.md` §4 D-1, inherited unchanged by `3B-ASYNC.md`]:** `register_consumer` against a read-only consumer source raises `NotSupported` instead of returning a `Refusal`, because none of R3's fourteen reasons says this honestly, and PACKAGE §3.4 primitive 10 / test C11-04 require a `Refusal`, never a silent no-op.

**Ruling:** R3's own amendment rule applies — add the fifteenth value **`consumer_source_read_only`** to INTERFACE §5.12 in the same change that makes `register_consumer` return `Refusal(reason="consumer_source_read_only")` in the sync registry (the async mirror regenerates from it). Not an open vocabulary; one more closed value, named for the actual condition. **Assigned to row 3c** (the use-case validation pass), which is already amending INTERFACE/PACKAGE; the change lands with a C11-04 assertion on the new reason in both suites.
