/*
 * Generate row 8a's two GENERATED Foundry fixtures (R106 route 1) from Palantir's own
 * fake Foundry. Both inputs are Apache 2.0:
 *
 *   @osdk/faux 0.66.0 from npm, and
 *   packages/shared.test/src of https://github.com/palantir/osdk-ts at
 *   ee09000147c05d761b893582b04514cbbdf124a4 (the workspace's packages/faux is 0.66.0
 *   at that commit, the same version npm serves).
 *
 * shared.test is private on npm (the published 1.2.0 is a different, older package), so
 * its source is copied next to this script rather than installed:
 *
 *   git clone --filter=blob:none --sparse https://github.com/palantir/osdk-ts.git
 *   git -C osdk-ts checkout ee09000147c05d761b893582b04514cbbdf124a4
 *   git -C osdk-ts sparse-checkout set packages/shared.test
 *   cp -r osdk-ts/packages/shared.test/src docs/tools/foundry_faux/shared.test
 *   (cd docs/tools/foundry_faux && npm install --ignore-scripts && npx tsx generate.mts)
 *
 * Writes foundry_faux_employee.json (addEmployeeOntology) and foundry_faux_legacy.json
 * (LegacyFauxFoundry's default ontology) into ontoloche/contract/fixtures/. Only the
 * ontology RID and editTodo's action type RID differ between runs, because both are
 * minted with a random UUID. A second run on 2026-11-12 matched the committed files
 * everywhere else.
 * shared.test/ and node_modules/ are not committed.
 */
import { FauxFoundry } from "@osdk/faux";
import { writeFileSync } from "node:fs";

const { LegacyFauxFoundry } = await import("./shared.test/stubs/LegacyFauxFoundry.ts");
const { addEmployeeOntology } = await import("./shared.test/ontologies/EmployeeOntology.ts");
const OUT = new URL("../../../ontoloche/contract/fixtures/", import.meta.url);

const legacy = new LegacyFauxFoundry();
writeFileSync(
  new URL("foundry_faux_legacy.json", OUT),
  JSON.stringify(legacy.getDefaultOntology().getOntologyFullMetadata(), null, 2),
);

const employee = new FauxFoundry("https://stack.palantir.com/");
addEmployeeOntology(employee.getDefaultOntology());
writeFileSync(
  new URL("foundry_faux_employee.json", OUT),
  JSON.stringify(employee.getDefaultOntology().getOntologyFullMetadata(), null, 2),
);
console.log("ok");
