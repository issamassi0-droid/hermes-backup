#!/usr/bin/env python3
"""
Self-Learning Engine — Cabinet-Office System
Extracts learnings from mission history and feeds them back into the pipeline.
"""
import json
import pathlib
from datetime import datetime, timezone


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
LEDGER_DIR = SYSTEM_ROOT / "ledger"
LEARNINGS_FILE = LEDGER_DIR / "learnings.jsonl"


class SelfLearningEngine:
    def __init__(self):
        self.learnings = []
        self.skills = []

    def extract_learnings(self, mission_id: str, mission_report: dict) -> list:
        learnings = []

        if "quality_issues" in mission_report:
            for issue in mission_report["quality_issues"]:
                learnings.append({
                    "category": "quality",
                    "type": issue.get("type", "unknown"),
                    "description": issue.get("description", ""),
                    "mission_id": mission_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        if "tool_usage" in mission_report:
            for tool, result in mission_report["tool_usage"].items():
                learnings.append({
                    "category": "tool",
                    "tool": tool,
                    "success": result.get("success", False),
                    "mission_id": mission_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        self.learnings.extend(learnings)
        self._save_learnings(learnings)
        return learnings

    def identify_patterns(self) -> dict:
        patterns = {"quality_issues": {}, "tool_success": {}}
        for learning in self.learnings:
            cat = learning.get("category")
            if cat == "quality":
                issue_type = learning.get("type", "unknown")
                patterns["quality_issues"][issue_type] = patterns["quality_issues"].get(issue_type, 0) + 1
            elif cat == "tool":
                tool = learning.get("tool", "unknown")
                if tool not in patterns["tool_success"]:
                    patterns["tool_success"][tool] = {"success": 0, "fail": 0}
                if learning.get("success"):
                    patterns["tool_success"][tool]["success"] += 1
                else:
                    patterns["tool_success"][tool]["fail"] += 1
        return patterns

    def generate_skill(self, pattern: dict) -> dict:
        skill = {
            "name": f"skill_{pattern.get('category', 'generic')}",
            "category": pattern.get("category", "generic"),
            "description": f"Auto-generated skill for {pattern.get('category', 'generic')}",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        self.skills.append(skill)
        return skill

    def get_evolution_proposals(self) -> list:
        proposals = []
        patterns = self.identify_patterns()
        for issue_type, count in patterns.get("quality_issues", {}).items():
            if count >= 3:
                proposals.append({
                    "target": "quality-charter.md",
                    "change": f"Add explicit check for {issue_type} issues",
                    "evidence": f"{count} occurrences",
                    "risk": "low"
                })
        return proposals

    def _save_learnings(self, learnings: list):
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)
        with open(LEARNINGS_FILE, "a") as f:
            for learning in learnings:
                f.write(json.dumps(learning) + "\n")


if __name__ == "__main__":
    engine = SelfLearningEngine()
    report = {
        "quality_issues": [{"type": "missing_source", "description": "Claim without evidence"}],
        "tool_usage": {"web_search": {"success": True}}
    }
    learnings = engine.extract_learnings("mission-001", report)
    print(f"✓ Self-Learning Engine: extracted {len(learnings)} learnings")
