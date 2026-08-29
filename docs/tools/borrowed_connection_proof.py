"""The borrowed-connection proof -- ruling R5 / beacon finding U1, roadmap row 3d.

Drives the REAL registry over a connection the HOST owns, on both reference backends,
and prints what a host would observe. Nothing here is a test double, and nothing here
is a fixture: it is the demonstration a reader can run when the contract test C0-12
passing is not, on its own, convincing.

    OO_POSTGRES_DSN=postgresql://... python docs/tools/borrowed_connection_proof.py

Its output is pasted verbatim into docs/runs/3D-RUN.md.
"""

import os
import sqlite3
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.abspath("."))

from open_ontology._clock import FixedClock
from open_ontology.backends.postgres import PostgresAdapter
from open_ontology.backends.sqlite import SQLiteAdapter
from open_ontology.backends.sqlite_minimal import MinimalSQLiteAdapter  # noqa: F401
from open_ontology.policy import NamespacePolicy
from open_ontology.registry import Registry

DSN = os.environ["OO_POSTGRES_DSN"]


def say(label, value):
    print(f"    {label:<52} {value}")


def postgres_leg():
    import psycopg

    schema = "oo_proof_" + uuid.uuid4().hex[:8]
    owner = PostgresAdapter(DSN, schema=schema)
    owner.migrate()
    print("postgres -- host owns the connection AND the schema")
    say("host schema created and committed by the host", schema)

    host = psycopg.connect(DSN)  # autocommit=False: the host manages its transaction
    with host.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}"')
    guest = PostgresAdapter.open(connection=host, schema=schema, owns_schema=False)
    caps = guest.capabilities()
    say("Capabilities.transaction_scope", caps.transaction_scope)
    say("Capabilities.transactional", caps.transactional)
    say("why['transaction_scope']", caps.why["transaction_scope"][:60] + "...")
    say("migrate() (verify-only, host owns the schema)", guest.migrate())

    registry = Registry(
        guest, clock=FixedClock(), policy=NamespacePolicy(approval_policy="auto")
    )
    entry = registry.propose_type(
        "facility", "a Medicare/Medicaid-certified nursing home", [], "user:sd"
    )
    say("registry.propose_type -> status", entry.status)
    say("host transaction still open", host.info.transaction_status.name)

    class Boom(RuntimeError):
        pass

    try:
        with guest.transaction():
            registry.propose_type("doomed", "a word that will not survive", [], "user:sd")
            raise Boom
    except Boom:
        pass
    say("after an exception: 'doomed' present?", guest.get_type("default", "doomed") is not None)
    say("after an exception: 'facility' present?", guest.get_type("default", "facility") is not None)
    say("after an exception: host transaction", host.info.transaction_status.name)

    with psycopg.connect(DSN, autocommit=True) as outsider:
        with outsider.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}"')
            cur.execute("SELECT count(*) FROM oo_type")
            say("what ANOTHER connection sees before host commit", cur.fetchone()[0])

    host.commit()
    with psycopg.connect(DSN, autocommit=True) as outsider:
        with outsider.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}"')
            cur.execute("SELECT count(*) FROM oo_type")
            say("what it sees after the HOST commits", cur.fetchone()[0])
    host.close()
    owner._execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    owner.close()


def sqlite_leg():
    print("\nsqlite -- SAVEPOINT works here too, so 2B's harness is not Postgres-only")
    path = os.path.join(tempfile.mkdtemp(), "proof.sqlite")
    owner = SQLiteAdapter(path)
    owner.migrate()
    owner.close()
    say("host schema created and committed by the host", os.path.basename(path))

    host = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    host.execute("PRAGMA foreign_keys = ON")
    host.execute("BEGIN IMMEDIATE")  # the HOST's transaction, opened by the host
    guest = SQLiteAdapter.open(connection=host, owns_schema=False)
    caps = guest.capabilities()
    say("Capabilities.transaction_scope", caps.transaction_scope)
    say("Capabilities.transactional", caps.transactional)
    say("migrate() (verify-only, host owns the schema)", guest.migrate())

    registry = Registry(
        guest, clock=FixedClock(), policy=NamespacePolicy(approval_policy="auto")
    )
    registry.propose_type("facility", "a Medicare/Medicaid-certified nursing home", [], "user:sd")
    say("host transaction still open", bool(host.in_transaction))

    class Boom(RuntimeError):
        pass

    try:
        with guest.transaction():
            registry.propose_type("doomed", "a word that will not survive", [], "user:sd")
            raise Boom
    except Boom:
        pass
    say("after an exception: 'doomed' present?", guest.get_type("default", "doomed") is not None)
    say("after an exception: 'facility' present?", guest.get_type("default", "facility") is not None)
    say("after an exception: host transaction open", bool(host.in_transaction))

    other = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    other.execute("PRAGMA busy_timeout = 2000")
    say(
        "what ANOTHER connection sees before host commit",
        other.execute("SELECT count(*) FROM oo_type").fetchone()[0],
    )
    host.execute("COMMIT")
    say(
        "what it sees after the HOST commits",
        other.execute("SELECT count(*) FROM oo_type").fetchone()[0],
    )
    other.close()
    host.close()


postgres_leg()
sqlite_leg()
print("\nNeither adapter issued a COMMIT. Durability at clean exit is the host's -- R5.")
