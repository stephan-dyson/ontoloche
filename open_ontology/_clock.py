"""PRIVATE. An injectable clock, so the contract suite is not time-flaky.

The orphan window (INTERFACE.md 5.7) is a comparison against "now", and a suite that
reads the wall clock fails at midnight on the last day of a month for reasons that have
nothing to do with storage.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

__all__ = ["Clock", "SystemClock", "FixedClock", "utcnow"]


def utcnow() -> datetime:
    return datetime.now(UTC)


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return utcnow()


class FixedClock:
    """A clock that only moves when a test moves it."""

    def __init__(self, at: datetime | None = None):
        self._at = at or datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._at

    def advance(self, delta: timedelta) -> datetime:
        self._at = self._at + delta
        return self._at

    def set(self, at: datetime) -> datetime:
        self._at = at
        return self._at
