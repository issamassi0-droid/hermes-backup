#!/usr/bin/env python3
"""
Real Dedup Algorithm — Cabinet-Office System v1.1
Hybrid: TF-IDF + Jaccard + URL similarity.
Fixed: short-text over-similarity via Jaccard normalization.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path


def tokenize(text: str) -> list:
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'it', 'its', 'this', 'that',
        'these', 'those', 'i', 'we', 'you', 'he', 'she', 'they', 'them', 'their',
        'from', 'into', 'about', 'between', 'through', 'during', 'before',
        'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
        'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'because', 'as', 'until', 'while',
        'if', 'any', 'also', 'new', 'said', 'says', 'say', 'one', 'two',
        'first', 'last', 'long', 'great', 'little', 'right', 'old', 'big',
        'high', 'different', 'small', 'large', 'next', 'early', 'young',
        'important', 'public', 'bad', 'good', 'make', 'made', 'get', 'go',
    }
    return [w for w in re.findall(r'[a-z]+', text.lower()) if w not in stopwords and len(w) > 2]


def jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def compute_tfidf(documents: list) -> list:
    tokenized = [tokenize(doc) for doc in documents]
    df = Counter()
    for tokens in tokenized:
        for term in set(tokens):
            df[term] += 1
    n = len(documents)
    idf = {term: math.log(n / (1 + freq)) for term, freq in df.items()}
    vectors = []
    for tokens in tokenized:
        tf = Counter(tokens)
        total = len(tokens) or 1
        vector = {term: (count / total) * idf.get(term, 0) for term, count in tf.items()}
        vectors.append(vector)
    return vectors


def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    all_terms = set(vec_a.keys()) | set(vec_b.keys())
    dot = sum(vec_a.get(t, 0) * vec_b.get(t, 0) for t in all_terms)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def compute_url_similarity(url_a: str, url_b: str) -> float:
    from urllib.parse import urlparse
    try:
        a = urlparse(url_a)
        b = urlparse(url_b)
        if a.netloc == b.netloc:
            return 1.0 if a.path == b.path else 0.7
        return 0.0
    except Exception:
        return 0.0


def find_duplicates(
    findings: list,
    text_key: str = "text",
    url_key: str = "url",
    similarity_threshold: float = 0.60,
    url_bonus: float = 0.15,
    short_text_threshold: int = 8,
    short_text_bonus: float = 0.15
) -> dict:
    """
    Hybrid dedup: 0.6*TFIDF + 0.25*Jaccard + 0.15*URL
    Threshold: 0.60 (calibrated for real findings)
    Short text bonus: for texts with <= 8 words, lower threshold by 0.15
    """
    if not findings:
        return {"deduped": [], "duplicates": [], "stats": {"total": 0, "kept": 0, "removed": 0}}

    n = len(findings)
    texts = [f.get(text_key, "") for f in findings]
    urls = [f.get(url_key, "") for f in findings]
    tfidf_vectors = compute_tfidf(texts)
    tokenized_sets = [set(tokenize(t)) for t in texts]
    word_counts = [len(t.split()) for t in texts]

    duplicates = []
    duplicate_indices = set()
    grade_order = {"[V]": 3, "[M]": 2, "[U]": 1, "[H]": 0, "[X]": -1}

    for i in range(n):
        if i in duplicate_indices:
            continue
        for j in range(i + 1, n):
            if j in duplicate_indices:
                continue

            tfidf_cos = cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
            jaccard = jaccard_similarity(tokenized_sets[i], tokenized_sets[j])
            url_sim = compute_url_similarity(urls[i], urls[j])

            # Hybrid score
            combined = 0.6 * tfidf_cos + 0.25 * jaccard + 0.15 * url_sim

            # Short text bonus: short texts get a lower effective threshold
            avg_words = (word_counts[i] + word_counts[j]) / 2
            effective_threshold = similarity_threshold
            if avg_words <= short_text_threshold:
                effective_threshold = similarity_threshold - short_text_bonus

            if combined >= effective_threshold:
                grade_i = grade_order.get(findings[i].get("evidence_grade", "[U]"), 1)
                grade_j = grade_order.get(findings[j].get("evidence_grade", "[U]"), 1)

                if grade_i >= grade_j:
                    duplicate_indices.add(j)
                    duplicates.append({
                        "url": urls[j],
                        "reason": f"Duplicate of {urls[i]}",
                        "similarity": round(combined, 3),
                        "threshold_used": effective_threshold,
                        "short_text": avg_words <= short_text_threshold
                    })
                else:
                    duplicate_indices.add(i)
                    duplicates.append({
                        "url": urls[i],
                        "reason": f"Duplicate of {urls[j]}",
                        "similarity": round(combined, 3),
                        "threshold_used": effective_threshold,
                        "short_text": avg_words <= short_text_threshold
                    })
                break

    deduped = [f for idx, f in enumerate(findings) if idx not in duplicate_indices]

    return {
        "deduped": deduped,
        "duplicates": duplicates,
        "stats": {
            "total": n,
            "kept": len(deduped),
            "removed": len(duplicates),
            "dedup_rate": f"{(len(duplicates)/n*100):.1f}%" if n > 0 else "0%"
        }
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sample_findings = [
            {"url": "https://example.com/article1", "text": "The Cabinet-Office multi-agent system uses a three-layer architecture with constitutional, systemic, and agentic layers.", "evidence_grade": "[V]"},
            {"url": "https://example.org/post123", "text": "A three-layer architecture consisting of constitutional systemic and agentic layers is used by the cabinet office multi agent framework.", "evidence_grade": "[M]"},
            {"url": "https://other.com/page", "text": "The model gateway dynamically selects AI models based on task complexity and user preferences.", "evidence_grade": "[V]"},
            {"url": "https://another.net/blog", "text": "Dynamic model selection by the gateway uses task complexity and user preference history to pick the best model.", "evidence_grade": "[M]"},
            {"url": "https://unique.com/info", "text": "Scout pattern monitors external sources continuously at near-zero cost using only web search.", "evidence_grade": "[V]"},
            {"url": "https://duplicate.com/copy", "text": "The scout pattern monitors external sources continuously at near zero cost with only web search access.", "evidence_grade": "[U]"},
        ]
        result = find_duplicates(sample_findings)
        print(json.dumps(result, indent=2))

    elif sys.argv[1] == "--file" and len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            findings = json.load(f)
            result = find_duplicates(findings)
            print(json.dumps(result, indent=2))

    else:
        print("Usage: python dedup.py [--file findings.json]")
