#!/usr/bin/env python3
"""
Reliability Standards — Cabinet-Office System
Based on: MAS-FIRE, MTTR-A, ReliabilityBench, MAESTRO, COCO, CP-WBFT.
"""
import json
import pathlib
import time
import statistics
from datetime import datetime, timezone


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
RELIABILITY_DIR = SYSTEM_ROOT / "reliability"
RELIABILITY_DIR.mkdir(parents=True, exist_ok=True)

FAULT_TAXONOMY = {
    "intra_agent": {
        "factual_hallucination": {"severity": "high"},
        "referential_hallucination": {"severity": "high"},
        "logical_error": {"severity": "medium"},
        "procedural_error": {"severity": "medium"},
        "scope_violation": {"severity": "low"},
        "reasoning_drift": {"severity": "medium"},
        "overconfidence": {"severity": "medium"},
    },
    "inter_agent": {
        "message_corruption": {"severity": "high"},
        "role_ambiguity": {"severity": "medium"},
        "blind_trust": {"severity": "high"},
        "context_length_violation": {"severity": "medium"},
        "message_storm": {"severity": "high"},
        "deadlock": {"severity": "high"},
        "tool_format_error": {"severity": "low"},
        "tool_selection_error": {"severity": "medium"},
        "parameter_filling_error": {"severity": "low"},
    }
}

FAULT_TOLERANCE_TIERS = {
    "mechanism": {"handles": ["tool_format_error", "tool_selection_error", "parameter_filling_error"]},
    "rule": {"handles": ["message_storm", "deadlock", "context_length_violation"]},
    "prompt": {"handles": ["role_ambiguity", "blind_trust"]},
    "reasoning": {"handles": ["factual_hallucination", "referential_hallucination", "logical_error", "reasoning_drift"]},
}


class ReliabilityMetrics:
    def __init__(self):
        self.fault_events = []
        self.recovery_events = []

    def record_fault(self, mission_id: str, fault_type: str, severity: str):
        self.fault_events.append({
            "mission_id": mission_id,
            "fault_type": fault_type,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epoch": time.time()
        })

    def record_recovery(self, mission_id: str, fault_type: str, success: bool, recovery_time_s: float):
        self.recovery_events.append({
            "mission_id": mission_id,
            "fault_type": fault_type,
            "success": success,
            "recovery_time_s": recovery_time_s,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epoch": time.time()
        })

    def calculate_mttr_a(self) -> dict:
        if not self.recovery_events:
            return {"mttr_a_s": 0, "count": 0}
        times = [e["recovery_time_s"] for e in self.recovery_events]
        return {"mttr_a_s": statistics.mean(times), "count": len(times)}

    def calculate_mtbf(self) -> dict:
        if len(self.fault_events) < 2:
            return {"mtbf_s": 0, "count": 0}
        times = sorted([e["epoch"] for e in self.fault_events])
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        return {"mtbf_s": statistics.mean(intervals), "count": len(intervals)}

    def calculate_nrr(self) -> dict:
        mttr = self.calculate_mttr_a()
        mtbf = self.calculate_mtbf()
        if mttr["mttr_a_s"] == 0 or mtbf["mtbf_s"] == 0:
            return {"nrr": 0, "uptime_pct": 0}
        nrr = mtbf["mtbf_s"] / (mtbf["mtbf_s"] + mttr["mttr_a_s"])
        return {"nrr": nrr, "uptime_pct": nrr * 100}


if __name__ == "__main__":
    metrics = ReliabilityMetrics()
    for i in range(5):
        metrics.record_fault(f"mission-{i}", "factual_hallucination", "high")
        metrics.record_recovery(f"mission-{i}", "factual_hallucination", True, 6.2 + i * 0.5)

    mttr = metrics.calculate_mttr_a()
    mtbf = metrics.calculate_mtbf()
    nrr = metrics.calculate_nrr()

    print(f"✓ Reliability Standards")
    print(f"  MTTR-A: {mttr['mttr_a_s']:.2f}s")
    print(f"  MTBF: {mtbf['mtbf_s']:.2f}s")
    print(f"  NRR: {nrr['nrr']:.3f} ({nrr['uptime_pct']:.1f}% uptime)")
    print(f"  Fault types: {len(FAULT_TAXONOMY['intra_agent']) + len(FAULT_TAXONOMY['inter_agent'])}")
    print(f"  FT tiers: {len(FAULT_TOLERANCE_TIERS)}")
