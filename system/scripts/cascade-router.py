#!/usr/bin/env python3
"""
Cascade Router — Cabinet-Office System
Starts with cheap model, escalates only when needed.
"""
import json
import pathlib
import time


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
MODEL_REGISTRY = SYSTEM_ROOT / "model-registry.json"

CASCADE_CHAIN = [
    {"model": "ling-3.0-flash", "cost": 0.0, "complexity_max": 0.4},
    {"model": "meituan-longcat-2.0", "cost": 0.0, "complexity_max": 0.7},
    {"model": "nemotron-3-ultra", "cost": 0.0, "complexity_max": 1.0},
]


class CascadeRouter:
    def __init__(self, model_chain: list = None):
        self.model_chain = model_chain or CASCADE_CHAIN

    def calculate_complexity(self, task: str) -> float:
        """Simple complexity estimation"""
        words = len(task.split())
        if words < 10:
            return 0.2
        elif words < 30:
            return 0.5
        elif words < 60:
            return 0.7
        return 0.9

    def _try_model(self, task: str, model_id: str) -> tuple:
        """Try executing with a model"""
        time.sleep(0.1)
        return True, f"Response from {model_id}", 0.8

    def route(self, task: str) -> dict:
        """Route task through cascade"""
        complexity = self.calculate_complexity(task)

        for model in self.model_chain:
            if complexity <= model["complexity_max"]:
                try:
                    success, output, confidence = self._try_model(task, model["model"])
                    if success:
                        return {
                            "task": task[:50],
                            "model": model["model"],
                            "confidence": confidence,
                            "escalations": 0
                        }
                except Exception:
                    continue

        return {
            "task": task[:50],
            "model": self.model_chain[-1]["model"],
            "confidence": 0.5,
            "escalations": len(self.model_chain) - 1
        }


if __name__ == "__main__":
    router = CascadeRouter()
    tasks = [
        "What is the capital of France?",
        "Write a detailed analysis of quantum computing applications"
    ]
    for task in tasks:
        result = router.route(task)
        print(f"  '{task[:40]}' → {result['model']} (escalations: {result['escalations']})")
