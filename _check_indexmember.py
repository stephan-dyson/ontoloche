import sys
sys.path.insert(0, ".")
from open_ontology.backends.sqlite import SQLiteAdapter
from open_ontology.contract.doubles import DegradedAdapter
from open_ontology.contract import run_contract_suite


def factory():
    return DegradedAdapter(SQLiteAdapter(":memory:"), indexes_membership=False)


rc = run_contract_suite(factory, args=["-q", "-k", "c9_ or c1_ or c10_"])
print("EXIT CODE:", rc)
