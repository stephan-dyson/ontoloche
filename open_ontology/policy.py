"""Deployment-supplied policy -- INTERFACE.md 2.7 and 5.6.

v0 does not define the tier vocabulary or the ordering. It defines the *slot*, requires
the value to be an opaque string, and requires the comparison to be supplied by the
deployment. So ``TierOrder`` is a list somebody wrote down, and comparing a tier that
is not in it yields ``None`` -- not ``False``, which would auto-approve an unknown
model on the strength of not recognising its name.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

__all__ = ["TierOrder", "NamespacePolicy"]


@dataclass(frozen=True)
class TierOrder:
    """A total order over model tiers, cheapest first.

    INTERFACE.md 2.7 records the assumption that a total order exists per deployment
    and that mixed vendors may break it. When a tier is not in the list the comparison
    is unknown, and the caller must treat unknown as "do not auto-approve".
    """

    tiers: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "tiers", tuple(self.tiers))
        if len(set(self.tiers)) != len(self.tiers):
            raise ValueError("TierOrder must not repeat a tier")

    def rank(self, tier: str | None) -> int | None:
        if tier is None or tier not in self.tiers:
            return None
        return self.tiers.index(tier)

    def below(self, tier: str | None, minimum: str | None) -> bool | None:
        """Is ``tier`` below ``minimum``? ``None`` when it cannot be told."""
        if minimum is None:
            return False
        a, b = self.rank(tier), self.rank(minimum)
        if a is None or b is None:
            return None
        return a < b


#: The order the 0.5 run actually used. Supplied as a convenience, not as a claim
#: about anyone else's deployment.
DEFAULT_TIER_ORDER = TierOrder(("haiku", "sonnet", "opus"))


@dataclass(frozen=True)
class NamespacePolicy:
    """Everything about a namespace that is a deployment decision rather than a fact."""

    namespace: str = "default"

    # INTERFACE.md 5.4 -- "review" returns a Proposal; "auto" returns a TypeEntry whose
    # approved_by is "auto:<auto_policy_name>", never blank.
    approval_policy: str = "review"
    auto_policy_name: str = "auto"

    # INTERFACE.md 2.7 point 3 -- the gate that stops the 0.5 severity inversion being
    # auto-approved. None means no gate.
    min_auto_approve_tier: str | None = None
    tier_order: TierOrder = DEFAULT_TIER_ORDER

    # INTERFACE.md 5.7 -- the window an orphan judgement is made against, and which
    # UsageReport reports back so the judgement is checkable.
    orphan_window: timedelta = timedelta(days=90)

    # PACKAGE.md 2.6 -- thresholds for the deterministic resolver. Scores are a
    # resolver concern; no contract test may pass or fail on one, so these only ever
    # decide which *shape* comes back.
    near_duplicate_threshold: float = 0.72
    existing_threshold: float = 0.90
    definitions_diverge_threshold: float = 0.55

    def __post_init__(self) -> None:
        if self.approval_policy not in ("review", "auto"):
            raise ValueError("approval_policy must be 'review' or 'auto'")

    def tier_is_below_minimum(self, tier: str | None) -> bool | None:
        return self.tier_order.below(tier, self.min_auto_approve_tier)
