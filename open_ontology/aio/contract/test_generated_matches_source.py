"""The anti-drift check -- not one of the 115, and the reason 3b is not a fork.

An async mirror maintained by hand is a second copy that will drift; ruling R1's kill
criterion says so. This package is not maintained by hand. It is regenerated from the
sync package by ``tools/unasync.py``, and this test regenerates it *again*, in memory,
and compares byte for byte. A change to ``registry.py`` that nobody mirrored fails
here, loudly, in the same run as everything else.

It skips with a reason from an installed wheel, where ``tools/`` is not shipped and
nothing can have drifted since the wheel was built -- the same rule the Postgres leg
follows: a check that cannot run says so rather than disappearing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.nonbinding

GENERATOR = Path(__file__).resolve().parents[3] / "tools" / "unasync.py"


def _load_generator():
    if not GENERATOR.exists():
        pytest.skip(
            f"PENDING -- {GENERATOR.name} is not present (this is an installed package, "
            "not the repository); nothing can have drifted since the build"
        )
    spec = importlib.util.spec_from_file_location("_oo_unasync", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_oo_unasync"] = module
    spec.loader.exec_module(module)
    return module


def test_the_generated_async_tree_is_current():
    unasync = _load_generator()
    stale = []
    for path, expected in unasync.generate().items():
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            stale.append(str(path.relative_to(unasync.ROOT)).replace("\\", "/"))
    assert not stale, (
        "the async mirror is stale -- run `python tools/unasync.py`:\n  " + "\n  ".join(stale)
    )
