import sys
sys.path.insert(0, ".")
from open_ontology.backends.sqlite import SQLiteAdapter
from open_ontology.contract.doubles import DegradedAdapter
from open_ontology.contract import run_contract_suite

mode = sys.argv[1] if len(sys.argv) > 1 else "single"

if mode == "single":
    def factory():
        return DegradedAdapter(SQLiteAdapter(":memory:"), stores_proposals=False)
elif mode == "multi":
    def factory():
        return DegradedAdapter(
            SQLiteAdapter(":memory:"),
            stores_proposals=False,
            stores_events=False,
            indexes_membership=False,
        )
else:
    raise SystemExit("mode?")

rc = run_contract_suite(factory, args=["-q", "-rs"])
print("EXIT CODE:", rc)
