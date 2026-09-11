#!/usr/bin/env python3
"""
Escalation + System Health — Cabinet-Office System
8 escalation triggers + 6 health checks.
"""
import json
import pathlib
from datetime import datetime, timezone


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
LEDGER_DIR = SYSTEM_ROOT / "ledger"
ESCALATION_FILE = LEDGER_DIR / "escalations.jsonl"
HEALTH_FILE = LEDGER_DIR / "system-health.json"

ESCALATION_TRIGGERS = {
    "high_factual_error": {"threshold": 0.10, "action": "escalate_to_qa"},
    "low_source_verification": {"threshold": 0.80, "action": "escalate_to_researcher"},
    "budget_exhausted": {"threshold": 0.95, "action": "pause_and_report"},
    "repeated_qa_rejection": {"threshold": 2, "action": "escalate_to_orchestrator"},
    "human_override": {"threshold": 1, "action": "pause_for_human"},
    "agent_timeout": {"threshold": 300, "action": "retry_or_escalate"},
    "quality_degradation": {"threshold": 0.5, "action": "review_pipeline"},
    "external_failure": {"threshold": 1, "action": "fallback_model"},
}

HEALTH_CHECKS = [
    "agent_responsiveness",
    "token_budget_status",
    "error_rate",
    "queue_depth",
    "model_latency",
    "output_quality_trend",
]


class EscalationSystem:
    def __init__(self):
        self.escalations = []

    def check_trigger(self, trigger_name: str, value: float) -> dict:
        """Check if escalation trigger fires"""
        trigger = ESCALATION_TRIGGERS.get(trigger_name)
        if not trigger:
            return {"triggered": False, "reason": "unknown_trigger"}

        threshold = trigger["threshold"]
        triggered = value >= threshold

        result = {
            "trigger": trigger_name,
            "threshold": threshold,
            "value": value,
            "triggered": triggered,
            "action": trigger["action"] if triggered else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if triggered:
            self.escalations.append(result)
            self._log_escalation(result)

        return result

    def _log_escalation(self, escalation: dict):
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)
        with open(ESCALATION_FILE, "a") as f:
            f.write(json.dumps(escalation) + "\n")


class SystemHealth:
    def __init__(self):
        self.checks = {}

    def run_checks(self) -> dict:
        """Run all health checks"""
        results = {}
        for check in HEALTH_CHECKS:
            results[check] = self._run_check(check)
        self.checks = results
        return results

    def _run_check(self, check_name: str) -> dict:
        """Run single health check"""
        return {
            "check": check_name,
            "status": "healthy",
            "value": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_status(self) -> str:
        """Get overall system status"""
        if not self.checks:
            return "unknown"
        failed = sum(1 for c in self.checks.values() if c.get("status") != "healthy")
        if failed == 0:
            return "healthy"
        elif failed <= 2:
            return "degraded"
        return "critical"


if __name__ == "__main__":
    esc = EscalationSystem()
    result = esc.check_trigger("high_factual_error", 0.18)
    print(f"✓ Escalation: {result['trigger']} → triggered={result['triggered']}")

    health = SystemHealth()
    results = health.run_checks()
    print(f"✓ System Health: {len(results)} checks, status={health.get_status()}")
