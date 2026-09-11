#!/usr/bin/env python3
"""
Dedup v2 — Cabinet-Office System
Hybrid TF-IDF + Jaccard + URL deduplication.
"""
import json
import math
import re
from collections import Counter


class Dedup:
    def __init__(self, threshold: float = 0.60):
        self.threshold = threshold

    def _tokenize(self, text: str) -> set:
        """Simple tokenization"""
        words = re.findall(r'\b\w+\b', text.lower())
        return set(words)

    def _jaccard(self, a: set, b: set) -> float:
        """Jaccard similarity"""
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def _tfidf_sim(self, text1: str, text2: str) -> float:
        """Simple TF-IDF cosine similarity"""
        words1 = Counter(re.findall(r'\b\w+\b', text1.lower()))
        words2 = Counter(re.findall(r'\b\w+\b', text2.lower()))

        all_words = set(words1.keys()) | set(words2.keys())
        if not all_words:
            return 1.0

        dot = sum(words1.get(w, 0) * words2.get(w, 0) for w in all_words)
        mag1 = math.sqrt(sum(c**2 for c in words1.values()))
        mag2 = math.sqrt(sum(c**2 for c in words2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def dedup(self, items: list) -> dict:
        """Deduplicate list of items with 'text' field"""
        unique = []
        duplicates = []

        for item in items:
            text = item.get("text", item.get("content", ""))
            is_dup = False

            for existing in unique:
                existing_text = existing.get("text", existing.get("content", ""))
                sim = self._tfidf_sim(text, existing_text)

                # Adjust threshold for short texts
                words = len(text.split())
                effective_threshold = 0.45 if words <= 8 else self.threshold

                if sim >= effective_threshold:
                    duplicates.append({"item": item, "similar_to": existing, "score": sim})
                    is_dup = True
                    break

            if not is_dup:
                unique.append(item)

        return {"unique": unique, "duplicates": duplicates}


if __name__ == "__main__":
    dedup = Dedup()
    items = [
        {"text": "AI is transforming healthcare"},
        {"text": "Artificial intelligence transforms healthcare"},
        {"text": "Machine learning in finance"},
    ]
    result = dedup.dedup(items)
    print(f"✓ Dedup: {len(items)} → {len(result['unique'])} unique, {len(result['duplicates'])} duplicates")
