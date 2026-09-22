# R105–R107 — the founder's answers to FOUNDRY-PARITY.md §6

**Founder rulings, 2026-09-22.** Given in session, in answer to the three questions in [`findings/FOUNDRY-PARITY.md`](../findings/FOUNDRY-PARITY.md) §6. His words are quoted exactly.

Context: the founder restated the project's goal the same day as two things. First, be able to replace the ontology function of Palantir Foundry, including an easy way to import from that platform. Second, solve the existing pain points of handling this layer.

---

## R105 — entity properties: `recommend`

**The question.** Do entity properties come into scope, given that `INTERFACE.md` §0 says the registry *"is not a schema store"*? The options were `in`, `carry` or `recommend`.

**His word: `recommend`.** A design pass brings the options with evidence before anything is decided. That pass is [`findings/PROPERTIES-OPTIONS.md`](../findings/PROPERTIES-OPTIONS.md), and its recommendation goes back to the founder as a new question. **`INTERFACE.md` §0 is unchanged until that is ruled.**

**In force until then:** an importer carries Foundry properties verbatim and never validates them. That is the `carry` behaviour, adopted as an interim and not as a ruling.

## R106 — a real Foundry export from the partner organisation: not available

**The question.** Can the partner organisation export its ontology metadata for a design test?

**His words:** *"probably not, but we can probably figure out another way to get there."*

**What this means for the importer row.** Its design tests cannot rest on a customer export. `PROPERTIES-OPTIONS.md` §4 records three other routes, each checked on 2026-09-22:

1. **Palantir's own fake Foundry.** `@osdk/faux`, in Palantir's `osdk-ts` repo under Apache 2.0, has a `FauxOntology` whose `getOntologyFullMetadata()` returns `OntologiesV2.OntologyFullMetadata`, typed by Palantir's generated API types. Palantir's test ontologies (`EmployeeOntology`, object types with link types, interface types, shared property types) register into it. https://github.com/palantir/osdk-ts/blob/main/packages/faux/src/FauxFoundry/FauxOntology.ts
2. **Palantir's Python SDK as a shape check.** `foundry-platform-sdk` (1.106.0 on PyPI on 2026-09-22, Apache 2.0) parses responses into pydantic models, including `OntologyFullMetadata`. A fixture that the SDK parses conforms to Palantir's published model. https://github.com/palantir/foundry-platform-python
3. **A free AIP Developer Tier account.** Palantir's getting-started page says *"Sign up for AIP Developer Tier to get access to the platform and start building with a trial account."* https://www.palantir.com/docs/foundry/getting-started/overview. Whether that tier exposes `fullMetadata`, and whether its terms allow using the output as a test fixture, are both **unverified**.

**What stays [Assumed].** Routes 1 and 2 prove the fixture has the published *shape*. They do not prove a real customer ontology looks like Palantir's test ontologies. Only route 3 or a customer export turns that into an observation.

## R107 — full replacement, not an escape hatch

**The question.** `VISION.md` §11 question 5: would portable ontology plus actions over a retained Foundry compute layer be enough, or is the goal to replace it?

**His words:** *"full replacement - Palantir forces users into vendor lock in, we want to give them a viable, low cost option to get out and continue their business."*

**Consequences, recorded so they are not rediscovered one row at a time:**

1. **The import is one-way.** No round trip back into Foundry is needed, so Ontology-as-code and Marketplace packaging are out of the importer's scope.
2. **`carry` is not enough for properties in the long run.** A customer leaving Foundry needs property definitions that can back their own tables. Unvalidated properties sitting in `attributes` do not do that. This weighs on R105's recommendation.
3. **"Continue their business" is wider than the ontology definitions.** A customer leaving Foundry also needs their instance data, somewhere for actions to actually run, and a replacement for Functions and apps. Each has a stated position today that **R107 does not overturn**, and each is now a known gap to plan for rather than a non-goal to lean on:
   - **Instance data.** The host holds the instances (R78). A replacement customer's host is their own database, and the data has to get there. `VISION.md` §6 says to consume Airbyte / dlt / dbt for that. Whether any of them has a Foundry source is **unverified**.
   - **Action execution.** `ACTIONS.md` §0 says *"The registry records and gates; the host runs."* A customer leaving Foundry has no host application yet, so something has to execute an action. A reference executor, or a documented host pattern, is a future question.
   - **Functions and apps.** Still out of scope (`VISION.md` §6: no compute, no dashboarding).
4. **`VISION.md` §11 question 5 is answered.** The answer is recorded here. `VISION.md` itself is not edited by this record.

---

**Next question number:** these rulings raise one new founder question, `Q102`, on `PROPERTIES-OPTIONS.md`'s recommendation. It is on [`DECISIONS-OPEN.md`](../DECISIONS-OPEN.md) as item 18.
