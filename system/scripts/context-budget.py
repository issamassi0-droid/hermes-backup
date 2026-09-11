#!/usr/bin/env python3
"""
Context Budget Calculator — Cabinet-Office System
Calculates remaining tokens for actual work after loading contracts.
"""
import json
import pathlib


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
REGISTRY = SYSTEM_ROOT / "registry.json"

TIER_BUDGETS = {
    "tier_0": {"contracts": 1, "overhead_pct": 305},
    "tier_1": {"contracts": 2, "overhead_pct": 130},
    "tier_2": {"contracts": 4, "overhead_pct": 56},
    "tier_3": {"contracts": 9, "overhead_pct": 32},
}

CONTEXT_WINDOWS = {
    "small": {"tokens": 8000, "max_contracts": 1},
    "medium": {"tokens": 32000, "max_contracts": 3},
    "large": {"tokens": 128000, "max_contracts": 6},
    "xlarge": {"tokens": 200000, "max_contracts": 9},
    "max": {"tokens": 1000000, "max_contracts": 9},
}


class ContextBudget:
    def __init__(self, tier: str = "tier_2", window_size: str = "large"):
        self.tier = tier
        self.window_size = window_size
        self.budget = TIER_BUDGETS.get(tier, TIER_BUDGETS["tier_2"])
        self.window = CONTEXT_WINDOWS.get(window_size, CONTEXT_WINDOWS["large"])

    def calculate(self) -> dict:
        """Calculate token budget"""
        total_tokens = self.window["tokens"]
        overhead_pct = self.budget["overhead_pct"]
        overhead_tokens = int(total_tokens * overhead_pct / 100)
        remaining = total_tokens - overhead_tokens
        used_pct = (overhead_tokens / total_tokens) * 100

        return {
            "tier": self.tier,
            "window": self.window_size,
            "total_tokens": total_tokens,
            "overhead_tokens": overhead_tokens,
            "remaining_tokens": remaining,
            "used_pct": round(used_pct, 1)
        }

    def can_fit(self, required_tokens: int) -> bool:
        """Check if required tokens fit in budget"""
        budget = self.calculate()
        return required_tokens <= budget["remaining_tokens"]


if __name__ == "__main__":
    for tier in ["tier_0", "tier_1", "tier_2", "tier_3"]:
        cb = ContextBudget(tier=tier)
        result = cb.calculate()
        print(f"  {tier}: {result['used_pct']}% overhead → {result['remaining_tokens']} tokens remaining")
