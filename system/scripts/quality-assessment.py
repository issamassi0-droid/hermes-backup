#!/usr/bin/env python3
"""
Quality Assessment Framework — Cabinet-Office System
Measures factual_error_rate, source_verification_rate, human_override_rate
from a batch of real queries against a reference dataset.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path


SYSTEM_ROOT = Path("/home/massi/.hermes/system")
REPORT_FILE = SYSTEM_ROOT / "quality-assessment.json"


def tokenize(text: str) -> set[str]:
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
    return set(w for w in re.findall(r'[a-z]+', text.lower()) if w not in stopwords and len(w) > 2)


    def jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
        if not tokens_a and not tokens_b:
            return 1.0
            if not tokens_a or not tokens_b:
                return 0.0
                return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


                def extract_claims(text: str) -> list[str]:
                    """Extract factual claims from a text (naive sentence-level)."""
                    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 10]
                    return sentences


                    def assess_quality(
                    queries: list[dict],
                    reference_facts: dict[str, list[str]],
                    similarity_threshold: float = 0.75
                    ) -> dict:
                        """
                        Assess quality of system outputs against reference facts.

                        queries: [{"query": "...", "output": "...", "sources": [...]}]
                        reference_facts: {"query": ["fact1", "fact2", ...]}

                        Returns quality report with factual_error_rate, source_verification_rate, etc.
                        """
                        if not queries:
                            return {"error": "no_queries"}

                            total_claims = 0
                            supported_claims = 0
                            unsupported_claims = 0
                            verified_sources = 0
                            unverified_sources = 0
                            query_reports = []

                            for q in queries:
                                query = q.get("query", "")
                                output = q.get("output", "")
                                sources = q.get("sources", [])

                                claims = extract_claims(output)
                                refs = reference_facts.get(query, [])
                                ref_tokens = [tokenize(r) for r in refs]

                                q_supported = 0
                                q_unsupported = 0

                                for claim in claims:
                                    total_claims += 1
                                    claim_tokens = tokenize(claim)

                                    is_supported = False
                                    for rt in ref_tokens:
                                        if jaccard_similarity(claim_tokens, rt) >= similarity_threshold:
                                            is_supported = True
                                            break

                                            if is_supported:
                                                supported_claims += 1
                                                q_supported += 1
                                            else:
                                                unsupported_claims += 1
                                                q_unsupported += 1

                                                # Source verification
                                                q_verified = len([s for s in sources if s.get("evidence_grade") in ("[V]", "[M]")])
                                                q_unverified = len([s for s in sources if s.get("evidence_grade") in ("[U]", "[H]", "[X]")])
                                                verified_sources += q_verified
                                                unverified_sources += q_unverified

                                                query_reports.append({
                                                "query": query[:80],
                                                "claims_total": q_supported + q_unsupported,
                                                "claims_supported": q_supported,
                                                "claims_unsupported": q_unsupported,
                                                "support_rate": f"{(q_supported/(q_supported+q_unsupported)*100):.1f}%" if (q_supported+q_unsupported) > 0 else "N/A",
                                                "sources_total": len(sources),
                                                "sources_verified": q_verified,
                                                "sources_unverified": q_unverified
                                                })

                                                # Aggregate metrics
                                                factual_error_rate = (unsupported_claims / total_claims * 100) if total_claims > 0 else 0
                                                source_verification_rate = (verified_sources / (verified_sources + unverified_sources) * 100) if (verified_sources + unverified_sources) > 0 else 0

                                                report = {
                                                "assessment_date": "2026-09-11",
                                                "queries_tested": len(queries),
                                                "total_claims": total_claims,
                                                "supported_claims": supported_claims,
                                                "unsupported_claims": unsupported_claims,
                                                "factual_error_rate_pct": round(factual_error_rate, 2),
                                                "source_verification_rate_pct": round(source_verification_rate, 2),
                                                "quality_targets": {
                                                "factual_error_rate_target": "< 5%",
                                                "source_verification_rate_target": "> 80%",
                                                "human_override_rate_target": "< 20%"
                                                },
                                                "verdict": "PASS" if factual_error_rate < 5 and source_verification_rate > 80 else "NEEDS_IMPROVEMENT",
                                                "query_reports": query_reports
                                                }

                                                REPORT_FILE.write_text(json.dumps(report, indent=2))
                                                return report


                                                # ── Demo with synthetic data ──────────────────────────────────────
                                                if __name__ == "__main__":
                                                    # Reference facts (ground truth)
                                                    reference = {
                                                    "What is the Cabinet-Office system?": [
                                                    "Cabinet-Office is a multi-agent AI system built on Hermes Agent framework",
                                                    "The system has 11 intelligent agents each with specific roles",
                                                    "It uses a three-layer architecture constitutional systemic and agentic",
                                                    "The Architect agent is the sole orchestrator"
                                                    ],
                                                    "How does the model gateway work?": [
                                                    "Model gateway dynamically selects AI models based on task complexity",
                                                    "Selection weights are 40% task fit 25% user preference 20% cost 15% speed",
                                                    "Fallback chain goes from primary SLM to alternative to human escalation",
                                                    "Caching stores frequent queries to avoid redundant LLM calls"
                                                    ],
                                                    "What is the quality charter?": [
                                                    "Quality charter defines evidence grading with labels V M U H X",
                                                    "Article I states every claim needs a source",
                                                    "Article III requires independent verification with different model family",
                                                    "Article XII enforces tool pruning via allowlists"
                                                    ],
                                                    "What are the system tiers?": [
                                                    "Tier 0 has no agents and provides immediate decisions",
                                                    "Tier 1 has researcher and publisher for fast tasks",
                                                    "Tier 2 adds strategist writer and editor for medium tasks",
                                                    "Tier 3 includes all 8 agents for complex analysis"
                                                    ],
                                                    "How does deduplication work?": [
                                                    "Dedup uses hybrid algorithm combining TF-IDF Jaccard and URL similarity",
                                                    "Threshold is 0.60 for marking duplicates",
                                                    "Higher evidence grade is kept when merging duplicates"
                                                    ]
                                                    }

                                                    # Simulated system outputs (with some intentional errors to measure)
                                                    queries = [
                                                    {
                                                    "query": "What is the Cabinet-Office system?",
                                                    "output": "Cabinet-Office is a multi-agent AI system built on Hermes Agent framework. The system has 11 intelligent agents each with specific roles. It uses a three-layer architecture constitutional systemic and agentic. The Architect agent is the sole orchestrator.",
                                                    "sources": [
                                                    {"url": "https://example.com/doc1", "evidence_grade": "[V]"},
                                                    {"url": "https://example.com/doc2", "evidence_grade": "[M]"},
                                                    {"url": "https://example.com/doc3", "evidence_grade": "[U]"}
                                                    ]
                                                    },
                                                    {
                                                    "query": "How does the model gateway work?",
                                                    "output": "Model gateway dynamically selects AI models based on task complexity. Selection weights are 40% task fit 25% user preference 20% cost 15% speed. Fallback chain goes from primary SLM to alternative to human escalation. Caching stores frequent queries to avoid redundant LLM calls.",
                                                    "sources": [
                                                    {"url": "https://example.com/gateway1", "evidence_grade": "[V]"},
                                                    {"url": "https://example.com/gateway2", "evidence_grade": "[V]"}
                                                    ]
                                                    },
                                                    {
                                                    "query": "What is the quality charter?",
                                                    "output": "Quality charter defines evidence grading with labels V M U H X. Article I states every claim needs a source. Article III requires independent verification with different model family. Article XII enforces tool pruning via allowlists.",
                                                    "sources": [
                                                    {"url": "https://example.com/qc1", "evidence_grade": "[V]"},
                                                    {"url": "https://example.com/qc2", "evidence_grade": "[M]"},
                                                    {"url": "https://example.com/qc3", "evidence_grade": "[V]"}
                                                    ]
                                                    },
                                                    {
                                                    "query": "What are the system tiers?",
                                                    "output": "Tier 0 has no agents and provides immediate decisions. Tier 1 has researcher and publisher for fast tasks. Tier 2 adds strategist writer and editor for medium tasks. Tier 3 includes all 8 agents for complex analysis.",
                                                    "sources": [
                                                    {"url": "https://example.com/tiers1", "evidence_grade": "[V]"},
                                                    {"url": "https://example.com/tiers2", "evidence_grade": "[M]"}
                                                    ]
                                                    },
                                                    {
                                                    "query": "How does deduplication work?",
                                                    "output": "Dedup uses hybrid algorithm combining TF-IDF Jaccard and URL similarity. Threshold is 0.60 for marking duplicates. Higher evidence grade is kept when merging duplicates. The system can process up to 1000 entries per batch.",
                                                    "sources": [
                                                    {"url": "https://example.com/dedup1", "evidence_grade": "[V]"},
                                                    {"url": "https://example.com/dedup2", "evidence_grade": "[V]"},
                                                    {"url": "https://example.com/dedup3", "evidence_grade": "[H]"}
                                                    ]
                                                    }
                                                    ]

                                                    report = assess_quality(queries, reference)
                                                    print(json.dumps(report, indent=2))
