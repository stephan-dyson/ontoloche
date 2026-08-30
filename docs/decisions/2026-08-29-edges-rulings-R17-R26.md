# Rulings 2026-08-29 — the ten questions EDGES v0 left (Q12–Q21 → R17–R26)

Supervisor rulings under the founder's make-assumptions directive. Source: [`docs/specs/EDGES.md`](../specs/EDGES.md) §14. Each is yes/no on the worker's recommendation; the founder may reverse any. **Three are founder-visible** (R17, R20, R24/R25) and are flagged in the pane report.

## R17 (Q12) — `created_by` gains a fourth value, `derived`: YES, row 3e. *Founder-visible.*

Two unrelated fixtures reach for the same missing value — beacon's `EntityMention.match = deterministic` and UC3's BBL join — and the alternative is an unvalidated string convention. `derived` = produced by a deterministic rule with no human and no model in the loop; it is additive to INTERFACE §2.1 and to the Tenshen-derived `seed | ai | user`. 3e (already amending the shape) adds it with tests. The founder set the original three from Tenshen; this is the first vocabulary change to that field.

## R18 (Q13) — the one cross-field attribute rule: ACCEPTED, narrowly

`symmetric ⇒ inverse_label is None` is the single cross-field rule `approve()` knows about `kind="edge"` attributes. PACKAGE §5.6 records it as an explicit exception list of length one; a rule language is not v0's problem.

## R19 (Q14) — `reinstate` covers edge **families**, never edge **instances**

A family is a `TypeEntry` (EDGES §2.3), so R11's `reinstate` applies to it with no second mechanism. An edge instance is never reinstated: a retracted edge is no claim (EDGES §3.2); re-asserting it is a new edge whose provenance cites the retracted one. 3e states this in `reinstate`'s spec text; EDGES §2.6 already agrees.

## R20 (Q15) — `EdgeProvenance.model_tier`: YES. A tier gate on AI-written edges: NO in v0. *Founder-visible.*

The field is additive and symmetric with `Provenance`. The gate is a product decision about beacon's `infer_person_relationships` (Haiku, auto-apply ≥ 0.7) — 0.5's failure shape one level down — and belongs to the beacon program; relayed as an observation, not a requirement.

**FOUNDER RULING 2026-08-30 13:2x (beacon item 35, relayed by the general fleet supervisor; verbatim *"go with recommendation (a+log+safety raise)"*).** R20 stands as ruled and is refined on the beacon side, not here: (a) auto-apply stays for beacon's weekly `infer_person_relationships` job at >= 0.7 -- no tier gate in the protocol, no proposal table, consistent with 21.1 s12 R3; (b) **every auto-applied edge is logged with the model identity and its confidence** (plus the pair and the job run) so a wrong batch can be reverted in one documented query -- which is exactly what `EdgeProvenance.model_tier` + `confidence` (this ruling) exist to carry; (c) **safety raise: edges produced on the literal-Haiku path auto-apply only at >= 0.85**, the light-tier path keeps 0.7, and the threshold lives in one place. Owner of (a)-(c): beacon (a 21.x row filed by phase21-approve-and-build). **open-ontology owes nothing:** the provenance fields are shipped (row 4b); the threshold is a host job parameter and is *not* exposed as a protocol constant -- a per-model threshold in `EDGES.md` would be the tier gate this ruling declined, one level up. Recorded so a reader of R20 sees the product decision that closed its open half.

## R21 (Q16) — `Provenance.source_version`: YES, row 3e

Additive, defaults `None`; two shapes for one concept is the drift the drift-check exists to catch.

## R22 (Q17) — endpoint-kind consumer gates: DEFERRED to Phase 3 with contortion 11 (R8's sibling)

Both would make `Consumer.gate` a query language; neither fixture needs it yet.

## R23 (Q18) — nullable `PersonLink.relationship_type`: neither a reserved family nor a silent drop — RECORDED; beacon's call

The honest fix is on beacon's side (make the column NOT NULL, or map nulls explicitly in its adapter). Relayed.

## R24 (Q19) — tenancy: the edge protocol carries NO tenancy dimension in v0; filtering is the host's job. *Founder-visible — gates 2B.* **[Assumed]**

`namespace` scopes a vocabulary, not a tenant (EDGES E3). A host-owned backend applies its tenancy predicate inside its adapter, the same way an `owns_schema=False` backend projects its columns — the protocol stays tenant-blind and says so. This is provisional: Phase 4 (multi-organisation) may force a dimension, and if beacon's 2B harness shows the adapter-side filter cannot be made safe, that is a finding routed upstream, not a workaround. Recorded in ROADMAP Phase 2B's dependency notes and relayed to beacon.

## R25 (Q21) — the 9.7M-degree node: routed to Phase 3 with R13 — paging for `list_types` and `neighbors` is decided **together**. *Founder-visible — the first measured scale limit.*

`erm2-nwe9` has 9,738,128 rows on one `agency` value; a single unpaged hop is a result nobody can hold. The default assembly bound tells the truth (`complete=False` + why) and does not solve it. Nothing pages in isolation; Phase 3's ingestion loop is the consumer that forces the design and it arrives with this number. Recorded as a required Phase 3 decision in ROADMAP.

## R26 (Q20) — Shape B's table-row endpoint: Slice 0 is the answer; no `record` level

A `record` level would let any table row be a node, deleting the distinction §2.4.1 holds. Evidence for beacon's Slice 0 (one entity-type vocabulary), not a change here.
