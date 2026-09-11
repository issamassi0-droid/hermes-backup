#!/usr/bin/env python3
"""
Dynamic Router — Cabinet-Office System
Routes tasks to optimal model based on complexity, cost, speed, and historical performance.
"""
import json
import pathlib
import time


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
MODEL_REGISTRY = SYSTEM_ROOT / "model-registry.json"


class DynamicRouter:
    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self):
        if MODEL_REGISTRY.exists():
            return json.loads(MODEL_REGISTRY.read_text())
        return {"models": []}

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

    def select_model(self, task: str) -> dict:
        """Select optimal model for task"""
        complexity = self.calculate_complexity(task)
        models = self.registry.get("models", [])

        if not models:
            return {"model": "default", "score": 0.5}

        # Simple selection: pick model with best complexity match
        best = min(models, key=lambda m: abs(m.get("complexity", 0.5) - complexity))
        best["score"] = 1.0 - abs(best.get("complexity", 0.5) - complexity)
        return best

    def route(self, task: str) -> dict:
        """Route task and return decision"""
        model = self.select_model(task)
        return {
            "task": task[:50],
            "model": model.get("model", "default"),
            "score": model.get("score", 0),
            "timestamp": time.time()
        }


if __name__ == "__main__":
    router = DynamicRouter()
    tasks = [
        "What is 2+2?",
        "Write a short article about AI",
        "Analyze the impact of artificial intelligence on global economics"
    ]
    for task in tasks:
        result = router.route(task)
        print(f"  '{task[:40]}' → {result['model']} (score: {result['score']:.2f})")
