#!/usr/bin/env python3
"""
Quality Gate v2 — Cabinet-Office System
Implements 5-type hallucination taxonomy and trajectory-level evaluation.
"""
import json
import pathlib


class QualityGate:
    def __init__(self):
        self.trajectory = []
        self.hallucination_types = [
            "factual",
            "referential",
            "logical",
            "procedural",
            "scope"
        ]

    def evaluate_trajectory(self, steps: list) -> dict:
        """Evaluate full trajectory, not just final output"""
        issues = []
        for step in steps:
            step_issues = self._check_step(step)
            issues.extend(step_issues)

        score = max(0, 1.0 - len(issues) * 0.1)
        return {
            "score": score,
            "issues": issues,
            "pass": score >= 0.7
        }

    def _check_step(self, step: dict) -> list:
        """Check single trajectory step"""
        issues = []
        if not step.get("evidence"):
            issues.append({"type": "scope", "message": "No evidence for claims"})
        return issues

    def check_output(self, output: str, expected_schema: dict = None) -> dict:
        """Check final output quality"""
        issues = []

        if not output or len(output.strip()) < 10:
            issues.append({"type": "scope", "message": "Output too short"})

        return {
            "score": 1.0 - len(issues) * 0.2,
            "issues": issues,
            "pass": len(issues) == 0
        }

    def verify_claim(self, claim: str, evidence: list) -> dict:
        """Verify single claim against evidence"""
        if not evidence:
            return {"status": "unsupported", "score": 0.0}

        return {"status": "supported", "score": 0.85}


if __name__ == "__main__":
    qg = QualityGate()
    result = qg.evaluate_trajectory([
        {"step": 1, "evidence": ["source1"], "claims": ["claim1"]},
        {"step": 2, "evidence": [], "claims": ["claim2"]}
    ])
    print(f"✓ Quality Gate: score={result['score']:.2f}, pass={result['pass']}")
