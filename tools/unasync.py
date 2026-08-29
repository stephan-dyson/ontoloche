"""Sync -> async source transformation. Deliverable 3b's answer to "how do you not drift?"

The sync package is the single source of truth. Everything under ``open_ontology/aio/``
and ``open_ontology/aio/contract/`` is *generated from it by this file* and checked in,
and ``test_generated_matches_source.py`` regenerates and compares, so a change to the
sync code that is not mirrored fails the suite rather than rotting quietly.

The transformation is deliberately mechanical and deliberately loud:

* it is driven by the **AST**, not by regexes over lines, so ``await`` lands on whole
  call expressions and is parenthesised exactly when Python's precedence needs it;
* which functions become ``async def`` is a **fixpoint**, not a list somebody maintains:
  seed the fifteen storage primitives as awaitable, then anything that calls an
  awaitable is itself awaitable, until nothing changes;
* it **refuses to emit** code it cannot prove is right -- an ``await`` inside a lambda,
  or inside a generator expression it could not convert to a list comprehension, is an
  error, not a silent mistranslation.

Run it::

    python tools/unasync.py            # write the generated tree
    python tools/unasync.py --check    # exit 1 if the tree is stale (what the suite does)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------- config

#: The fifteen primitives (minus ``transaction``, which stays a *call* returning an
#: async context manager), the optional attribute-store extension, and the SQL layer's
#: connection hooks. Everything else that becomes async is *derived* from these.
SEED_AWAIT_ATTRS = frozenset(
    {
        # PACKAGE.md 3.4 primitives 1-2 and 4-15
        "capabilities",
        "migrate",
        "put_type",
        "get_type",
        "find_types",
        "put_proposal",
        "get_proposal",
        "find_proposals",
        "put_consumer",
        "find_consumers",
        "bump_usage",
        "get_usage",
        "append_event",
        "read_events",
        # EDGES.md 7.1's three, added by row 4b. Seeds, not derived: the fixpoint below
        # picks up `neighbors`, `add_edge`, `retract_edge` and everything that calls
        # them from these three.
        "put_edge",
        "get_edge",
        "find_edges",
        # the optional AttributeStore extension (deviation D-2)
        "put_attr_schema",
        "get_attr_schema",
        "observe_attributes",
        "read_attr_observed",
        # the SQL layer's connection hooks
        "_execute",
        "_fetchall",
        "_fetchone",
        "_begin",
        "_commit",
        "_rollback",
        "_columns_of",
        "_current_version",
        "_recover_from_failed_probe",
    }
)

#: Bare (non-method) calls that are awaitable before the fixpoint starts. The suite's
#: ``make_registry`` fixture hands back a builder that must now open a connection, so
#: every call to it in a test is an await. Everything else in this set is derived.
SEED_AWAIT_NAMES = frozenset({"make_registry"})

#: Primitive 3. ``transaction()`` is called, never awaited; ``with`` becomes
#: ``async with``. Adding it to the awaitable set would be the classic mistranslation.
CONTEXT_MANAGER_ATTRS = frozenset({"transaction"})

#: Never inferred as awaitable however they are called. ``__init__`` cannot be a
#: coroutine, which is the one place mirroring is not mechanical -- see the trailer for
#: ``registry.py`` and docs/runs/3B-ASYNC.md D-A1. ``_migration_sql`` is monkeypatched with a
#: plain lambda by C0-05 and does no I/O. ``close`` belongs to the hand-written driver
#: layer, which the generator does not touch.
NEVER_ASYNC = frozenset({"__init__", "_migration_sql", "close"})

#: Applied to the assembled text as whole-word substitutions.
RENAMES = {
    "StorageAdapter": "AsyncStorageAdapter",
    "AttributeStore": "AsyncAttributeStore",
    "Registry": "AsyncRegistry",
    "BaseSqlAdapter": "AsyncBaseSqlAdapter",
    "DegradedAdapter": "AsyncDegradedAdapter",
    "SQLiteAdapter": "AsyncSQLiteAdapter",
    "PostgresAdapter": "AsyncPostgresAdapter",
    "AbstractContextManager": "AbstractAsyncContextManager",
    "contextmanager": "asynccontextmanager",
}

#: Absolute module paths that must point at the async mirror instead of the sync module.
REDIRECTS = {
    "open_ontology.adapter": "open_ontology.aio.adapter",
    "open_ontology.registry": "open_ontology.aio.registry",
    "open_ontology.backends": "open_ontology.aio.backends",
    "open_ontology.backends.sqlite": "open_ontology.aio.backends.sqlite",
    "open_ontology.backends.postgres": "open_ontology.aio.backends.postgres",
    "open_ontology.backends._sql": "open_ontology.aio.backends._sql",
    "open_ontology.contract._support": "open_ontology.aio.contract._support",
    "open_ontology.contract.doubles": "open_ontology.aio.contract.doubles",
}

BANNER = """\
# ---------------------------------------------------------------------------------
# GENERATED FILE -- do not edit. Edit {source} and run:
#
#     python tools/unasync.py
#
# The sync module is the single source of truth; this is its mechanical async mirror
# (deliverable 3b). open_ontology/aio/contract/test_generated_matches_source.py fails
# if this file and its source have drifted apart.
# ---------------------------------------------------------------------------------
"""


@dataclass(frozen=True)
class FileSpec:
    source: str
    target: str
    #: top-level names to carry over; empty means the whole module
    extract: tuple[str, ...] = ()
    #: emitted before the copied import block; supplies names the async mirror needs
    #: that the sync module has no reason to import
    extra_header: str = ""
    #: emitted at the end of the generated module
    trailer: str = ""
    #: module the extracted code borrows its pure module-level helpers from
    borrow_from: str = ""
    #: ``(pattern, replacement)`` applied to the source text BEFORE it is parsed. The
    #: one use is ``Registry.__init__`` -> ``_open``: a constructor cannot await, so the
    #: sync constructor is mirrored as an ordinary coroutine and a classmethod calls it
    #: (deviation D-A1). Nothing else in the mirror needs a pre-substitution.
    pre_substitutions: tuple[tuple[str, str], ...] = ()


REGISTRY_TRAILER = '''
    # ---------------------------------------------------------------- construction
    #: Deviation D-A1 (docs/runs/3B-ASYNC.md). ``__init__`` cannot be a coroutine, so the
    #: two calls the sync constructor makes -- ``capabilities()`` and ``migrate()`` --
    #: have nowhere to be awaited. The sync ``__init__`` is transformed into ``_open``
    #: and construction goes through this classmethod. It is the ONLY place the async
    #: mirror's shape differs from the sync original, and it differs because Python
    #: says so, not because the design does.
    @classmethod
    async def open(cls, adapter, **kwargs) -> "AsyncRegistry":
        self = cls.__new__(cls)
        await self._open(adapter, **kwargs)
        return self

    def __init__(self, *args, **kwargs):
        raise TypeError(
            "AsyncRegistry is constructed with `await AsyncRegistry.open(adapter, ...)`; "
            "__init__ cannot await capabilities() and migrate()"
        )
'''

ADAPTER_EXTRA_HEADER = '''
# The records, queries, pages and capability flags are storage shapes with no I/O in
# them, so the async mirror does not copy them -- it re-exports the sync package's.
# One definition, two protocols over it.
from open_ontology.adapter import (
    CAPABILITY_FLAGS,
    EDGE_CAPABILITY_FLAGS,
    REQUIRED_CAPABILITIES,
    AttrObservedRecord,
    AttrSchemaRecord,
    Capabilities,
    ConsumerRecord,
    EdgePage,
    EdgeQuery,
    EdgeRecord,
    EventRecord,
    ProposalPage,
    ProposalQuery,
    ProposalRecord,
    TypePage,
    TypeQuery,
    TypeRecord,
    UsageRecord,
)

__all__ = [
    "AsyncStorageAdapter",
    "AsyncAttributeStore",
    "Capabilities",
    "TypeRecord",
    "ProposalRecord",
    "ConsumerRecord",
    "UsageRecord",
    "EventRecord",
    "TypeQuery",
    "TypePage",
    "ProposalQuery",
    "ProposalPage",
    "AttrSchemaRecord",
    "AttrObservedRecord",
    "EdgeRecord",
    "EdgeQuery",
    "EdgePage",
    "CAPABILITY_FLAGS",
    "EDGE_CAPABILITY_FLAGS",
    "REQUIRED_CAPABILITIES",
]
'''

SQL_EXTRA_HEADER = '''
# The row <-> record mapping, the dialects and the migration loader are pure functions
# of a dialect object; the async mirror borrows them rather than copying them.
__all__ = ["AsyncBaseSqlAdapter"]
'''

#: Contract-test modules that are GENERATED into the async tree. One is excluded:
#: ``test_c0_backend_local.py`` holds the two tests that BUILD BACKENDS DIRECTLY
#: rather than taking the ``adapter`` fixture, so neither survives token substitution:
#: C0-08 races two writers on two threads (the async equivalent is ``asyncio.gather``,
#: a different mechanism) and C0-09 constructs an adapter with ``owns_schema=False``
#: (the async form is ``await AsyncSQLiteAdapter.open(...)``, D-A1). Its async
#: counterpart, ``aio/contract/test_c0_backend_local.py``, is hand-written and claims
#: the same contract ids. Both are binding. Same reasoning as the hand-written driver
#: ``close()`` methods -- 3B-ASYNC.md D-A12.
HAND_WRITTEN_ASYNC = frozenset({"test_c0_backend_local.py"})

CONTRACT_TESTS = tuple(
    sorted(
        p.name
        for p in (ROOT / "open_ontology" / "contract").glob("test_c*.py")
        if p.name not in HAND_WRITTEN_ASYNC
    )
)

SPECS: tuple[FileSpec, ...] = (
    FileSpec(
        source="open_ontology/adapter.py",
        target="open_ontology/aio/adapter.py",
        extract=("StorageAdapter", "AttributeStore"),
        extra_header=ADAPTER_EXTRA_HEADER,
        borrow_from="open_ontology.adapter",
    ),
    FileSpec(
        source="open_ontology/backends/_sql.py",
        target="open_ontology/aio/backends/_sql.py",
        extract=("BaseSqlAdapter",),
        extra_header=SQL_EXTRA_HEADER,
        borrow_from="open_ontology.backends._sql",
    ),
    FileSpec(
        source="open_ontology/registry.py",
        target="open_ontology/aio/registry.py",
        extract=("Registry",),
        extra_header='\n__all__ = ["AsyncRegistry"]\n',
        trailer=REGISTRY_TRAILER,
        borrow_from="open_ontology.registry",
        pre_substitutions=((r"^    def __init__\(", "    def _open("),),
    ),
    FileSpec(
        source="open_ontology/contract/_support.py",
        target="open_ontology/aio/contract/_support.py",
        # The 153 KB CMS fixture is checked in once, under the sync suite, and read
        # from where it lives. The generated copy sits elsewhere in the tree, so the
        # only thing that changes is how it gets there -- not which file it reads.
        pre_substitutions=(
            (
                r'FIXTURE = Path\(__file__\)\.resolve\(\)\.parent / "fixtures"',
                'FIXTURE = Path(__file__).resolve().parents[2] / "contract" / "fixtures"',
            ),
        ),
    ),
    FileSpec(
        source="open_ontology/contract/doubles.py",
        target="open_ontology/aio/contract/doubles.py",
    ),
    *(
        FileSpec(
            source=f"open_ontology/contract/{name}",
            target=f"open_ontology/aio/contract/{name}",
        )
        for name in CONTRACT_TESTS
    ),
)


# ------------------------------------------------------------------------ machinery


class TransformError(RuntimeError):
    """The transformation could not be proved correct. Never emit anyway."""


def _offsets(text: str) -> list[int]:
    out, pos = [0], 0
    for line in text.splitlines(keepends=True):
        pos += len(line)
        out.append(pos)
    return out


def _pos(offsets: list[int], lineno: int, col: int) -> int:
    return offsets[lineno - 1] + col


def _apply(text: str, edits: list[tuple[int, int, str]]) -> str:
    for start, end, replacement in sorted(edits, key=lambda e: (-e[0], -e[1])):
        text = text[:start] + replacement + text[end:]
    return text


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    out: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            out[id(child)] = node
    return out


def _is_cm_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in CONTEXT_MANAGER_ATTRS
    )


def _awaitable_call(node: ast.AST, attrs: set[str], names: set[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        return node.func.attr in attrs and node.func.attr not in CONTEXT_MANAGER_ATTRS
    if isinstance(node.func, ast.Name):
        return node.func.id in names
    return False


def _own_body(fn: ast.AST) -> list[ast.AST]:
    """Every node inside ``fn`` that is not inside a nested function or lambda."""
    out: list[ast.AST] = []
    stack = list(ast.iter_child_nodes(fn))
    while stack:
        node = stack.pop()
        out.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return out


def _needs_async(fn: ast.AST, attrs: set[str], names: set[str]) -> bool:
    for node in _own_body(fn):
        if _awaitable_call(node, attrs, names):
            return True
        if isinstance(node, ast.With) and any(
            _is_cm_call(item.context_expr) for item in node.items
        ):
            return True
    return False


@dataclass
class Module:
    spec: FileSpec
    text: str
    tree: ast.Module = field(init=False)

    def __post_init__(self) -> None:
        for pattern, replacement in self.spec.pre_substitutions:
            self.text, count = re.subn(pattern, replacement, self.text, flags=re.M)
            if count != 1:
                raise TransformError(
                    f"{self.spec.source}: pre-substitution {pattern!r} matched {count} times"
                )
        self.tree = ast.parse(self.text)

    def functions(self) -> list[tuple[ast.FunctionDef, ast.AST | None]]:
        parents = _parents(self.tree)
        return [
            (n, parents.get(id(n)))
            for n in ast.walk(self.tree)
            if isinstance(n, ast.FunctionDef)
        ]


def fixpoint(modules: list[Module]) -> tuple[set[str], set[str], set[int]]:
    """Grow the awaitable sets until nothing changes.

    Returns the attribute names to await when called, the bare function names to await
    when called, and the ids of the function nodes that become ``async def``.
    """
    attrs = set(SEED_AWAIT_ATTRS)
    names: set[str] = set(SEED_AWAIT_NAMES)
    async_ids: set[int] = set()
    for _ in range(64):
        changed = False
        for module in modules:
            for fn, parent in module.functions():
                if id(fn) in async_ids or fn.name in NEVER_ASYNC:
                    continue
                method = isinstance(parent, ast.ClassDef)
                # A method whose name is awaited somewhere MUST be a coroutine, even
                # when its own body does no I/O -- that is how the protocol stubs
                # (``def put_type(...) -> TypeRecord: ...``) and the abstract connection
                # hooks become ``async def`` instead of staying sync by accident.
                if not (_needs_async(fn, attrs, names) or (method and fn.name in attrs)):
                    continue
                async_ids.add(id(fn))
                changed = True
                if method:
                    # ``transaction`` is the exception that proves the rule: the SQL
                    # base's own ``transaction`` really is an ``async def`` (it is an
                    # ``@asynccontextmanager``), but callers still *call* it and then
                    # ``async with`` the result. Awaiting it would be the mistranslation.
                    if not fn.name.startswith("__") and fn.name not in CONTEXT_MANAGER_ATTRS:
                        attrs.add(fn.name)
                elif isinstance(parent, ast.Module):
                    names.add(fn.name)
        if not changed:
            return attrs, names, async_ids
    raise TransformError("the awaitable fixpoint did not converge")


def transform(module: Module, attrs: set[str], names: set[str], async_ids: set[int]) -> str:
    text = module.text
    tree = module.tree
    offsets = _offsets(text)
    parents = _parents(tree)
    edits: list[tuple[int, int, str]] = []

    enclosing: dict[int, ast.AST | None] = {id(tree): None}

    def walk(node: ast.AST, fn: ast.AST | None) -> None:
        for child in ast.iter_child_nodes(node):
            enclosing[id(child)] = fn
            inner = child if isinstance(child, (ast.FunctionDef, ast.Lambda)) else fn
            walk(child, inner)

    walk(tree, None)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and id(node) in async_ids:
            start = _pos(offsets, node.lineno, node.col_offset)
            edits.append((start, start, "async "))
        elif isinstance(node, ast.With) and any(
            _is_cm_call(item.context_expr) for item in node.items
        ):
            start = _pos(offsets, node.lineno, node.col_offset)
            edits.append((start, start + len("with"), "async with"))
        elif _awaitable_call(node, attrs, names):
            fn = enclosing.get(id(node))
            if isinstance(fn, ast.Lambda):
                raise TransformError(
                    f"{module.spec.source}:{node.lineno}: an await would land in a lambda"
                )
            if fn is None or id(fn) not in async_ids:
                where = getattr(fn, "name", "<module>")
                raise TransformError(
                    f"{module.spec.source}:{node.lineno}: awaitable call in non-async {where}"
                )
            start = _pos(offsets, node.lineno, node.col_offset)
            end = _pos(offsets, node.end_lineno, node.end_col_offset)
            parent = parents.get(id(node))
            needs_parens = isinstance(parent, (ast.Attribute, ast.Subscript)) or (
                isinstance(parent, ast.Call) and parent.func is node
            )
            if needs_parens:
                edits.append((start, start, "(await "))
                edits.append((end, end, ")"))
            else:
                edits.append((start, start, "await "))

    return _delist_generators(_apply(text, edits), module.spec.source)


def _delist_generators(text: str, where: str) -> str:
    """``tuple(await f(x) for x in xs)`` builds an *async* generator, which ``tuple``
    cannot consume. A list comprehension containing an ``await`` is a plain list, so the
    fix is a pair of brackets. Iterated because wrapping shifts every later offset."""
    for _ in range(32):
        tree = ast.parse(text)
        offsets = _offsets(text)
        parents = _parents(tree)
        target = None
        for node in ast.walk(tree):
            if isinstance(node, ast.GeneratorExp) and any(
                isinstance(n, ast.Await) for n in ast.walk(node)
            ):
                target = node
                break
        if target is None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Lambda) and any(
                    isinstance(n, ast.Await) for n in ast.walk(node)
                ):
                    raise TransformError(f"{where}:{node.lineno}: await inside a lambda")
            return text
        start = _pos(offsets, target.lineno, target.col_offset)
        end = _pos(offsets, target.end_lineno, target.end_col_offset)
        if text[start] != "(" or text[end - 1] != ")":
            raise TransformError(f"{where}:{target.lineno}: unbracketed generator expression")
        parent = parents.get(id(target))
        bare_argument = (
            isinstance(parent, ast.Call)
            and not parent.keywords
            and len(parent.args) == 1
            and parent.args[0] is target
        )
        if bare_argument:
            # CPython reports a bare ``f(x for x in y)`` genexp as spanning the *call's*
            # parentheses, so the brackets go just inside them.
            text = text[: start + 1] + "[" + text[start + 1 : end - 1] + "]" + text[end - 1 :]
        else:
            text = text[:start] + "[" + text[start + 1 : end - 1] + "]" + text[end:]
    raise TransformError(f"{where}: the generator-expression rewrite did not settle")


# ------------------------------------------------------------------ import rewriting

_IMPORT_FROM = re.compile(r"^(\s*)from\s+(\.+)([\w.]*)\s+import\s", re.M)


def _package_of(source: str) -> str:
    return source.rsplit("/", 1)[0].replace("/", ".")


def _resolve(package: str, dots: str, tail: str) -> str:
    parts = package.split(".")
    if len(dots) > 1:
        parts = parts[: -(len(dots) - 1)]
    return ".".join([*parts, tail]) if tail else ".".join(parts)


def rewrite_imports(text: str, source: str) -> str:
    """Relative imports become absolute, then get redirected at the async mirror.

    Absolute is the honest form in generated code: the file has moved a level down the
    tree and half its imports now point at a *different* module than the same line did
    in the source.
    """
    package = _package_of(source)

    def substitute(match: re.Match) -> str:
        indent, dots, tail = match.group(1), match.group(2), match.group(3)
        absolute = _resolve(package, dots, tail)
        absolute = REDIRECTS.get(absolute, absolute)
        return f"{indent}from {absolute} import "

    return _IMPORT_FROM.sub(substitute, text)


# ----------------------------------------------------------------------- assembly


def _segment(text: str, node: ast.AST) -> str:
    lines = text.splitlines(keepends=True)
    decorators = [d.lineno for d in getattr(node, "decorator_list", [])]
    start = min([node.lineno, *decorators]) - 1
    return "".join(lines[start : node.end_lineno])


def _bound_names(text: str) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                out.add(alias.asname or alias.name.split(".")[0])
    return out


def _module_level_defined(tree: ast.Module) -> set[str]:
    """Names this module *defines* (as opposed to imports) at module level."""
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return out


def build(spec: FileSpec, transformed: str) -> str:
    tree = ast.parse(transformed)
    banner = BANNER.format(source=spec.source)
    docstring = ast.get_docstring(tree, clean=False)
    head = f'"""{docstring}"""\n' if docstring else ""

    imports = "".join(
        _segment(transformed, node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )

    def is_docstring(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and node.value.value == docstring
        )

    if not spec.extract:
        body_nodes = [
            node
            for node in tree.body
            if not isinstance(node, (ast.Import, ast.ImportFrom)) and not is_docstring(node)
        ]
        body = "".join(_segment(transformed, node) + "\n" for node in body_nodes)
        borrowed = ""
    else:
        chosen = [
            node
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in spec.extract
        ]
        found = {node.name for node in chosen}
        missing = [n for n in spec.extract if n not in found]
        if missing:
            raise TransformError(f"{spec.source}: nothing named {missing} to extract")
        body = "\n\n\n".join(_segment(transformed, node).rstrip() for node in chosen) + "\n"

        used: set[str] = set()
        for node in chosen:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    used.add(sub.id)
        defined = _module_level_defined(tree) - found
        already = _bound_names(imports + "\n" + spec.extra_header)
        borrow = sorted((used & defined) - already)
        borrowed = ""
        if borrow:
            if not spec.borrow_from:
                raise TransformError(f"{spec.source}: needs {borrow} but has no borrow_from")
            joined = ",\n    ".join(borrow)
            borrowed = (
                "\n# Pure module-level helpers with no I/O in them, borrowed not copied.\n"
                f"from {spec.borrow_from} import (\n    {joined},\n)\n"
            )

    text = "".join([banner, "\n", head, "\n", imports, spec.extra_header, borrowed, "\n\n", body])
    if spec.trailer:
        text = text.rstrip("\n") + "\n" + spec.trailer.rstrip("\n") + "\n"
    return text


def finish(text: str, spec: FileSpec) -> str:
    text = rewrite_imports(text, spec.source)
    for old, new in RENAMES.items():
        text = re.sub(rf"\b{old}\b", new, text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    ast.parse(text)
    return text.rstrip("\n") + "\n"


def generate() -> dict[Path, str]:
    """The whole generated tree, as ``{path: text}``. Writes nothing."""
    modules = [
        Module(spec=spec, text=(ROOT / spec.source).read_text(encoding="utf-8"))
        for spec in SPECS
    ]
    attrs, names, async_ids = fixpoint(modules)
    out: dict[Path, str] = {}
    for module in modules:
        transformed = transform(module, attrs, names, async_ids)
        out[ROOT / module.spec.target] = finish(build(module.spec, transformed), module.spec)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python tools/unasync.py")
    parser.add_argument("--check", action="store_true", help="exit 1 if the tree is stale")
    args = parser.parse_args(argv)

    generated = generate()
    stale: list[str] = []
    for path, text in generated.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        stale.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")

    if args.check:
        if stale:
            print("stale generated files:\n  " + "\n  ".join(stale))
            return 1
        print(f"{len(generated)} generated files are current")
        return 0

    print(f"wrote {len(stale)} of {len(generated)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
