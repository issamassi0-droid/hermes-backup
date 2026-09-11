#!/usr/bin/env python3
"""
Quality Assessment v2 — Cabinet-Office System
Measures factual_error_rate, source_verification_rate, claim_support_rate.
"""
import json
import pathlib
import re
from collections import Counter


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent


class QualityAssessment:
    def __init__(self):
        self.metrics = {
            "factual_error_rate": 0.0,
            "source_verification_rate": 0.0,
            "claim_support_rate": 0.0,
            "total_claims": 0,
            "verified_claims": 0,
            "supported_claims": 0,
            "errors": 0
        }

    def assess(self, output: str, sources: list) -> dict:
        """Assess output quality"""
        claims = self._extract_claims(output)
        total = len(claims)
        verified = 0
        supported = 0
        errors = 0

        for claim in claims:
            is_verified, is_supported = self._verify_claim(claim, sources)
            if is_verified:
                verified += 1
            if is_supported:
                supported += 1
            else:
                errors += 1

        self.metrics["total_claims"] = total
        self.metrics["verified_claims"] = verified
        self.metrics["supported_claims"] = supported
        self.metrics["errors"] = errors

        if total > 0:
            self.metrics["factual_error_rate"] = errors / total
            self.metrics["source_verification_rate"] = verified / total
            self.metrics["claim_support_rate"] = supported / total

        return self.metrics

    def _extract_claims(self, output: str) -> list:
        """Extract factual claims from output"""
        sentences = re.split(r'[.!?]', output)
        claims = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20 and not sent.startswith(('I ', 'We ', 'My ')):
                claims.append(sent)
        return claims

    def _verify_claim(self, claim: str, sources: list) -> tuple:
        """Verify single claim against sources"""
        claim_lower = claim.lower()
        for source in sources:
            source_lower = source.get("text", source.get("content", "")).lower()
            # Simple keyword overlap
            claim_words = set(claim_lower.split())
            source_words = set(source_lower.split())
            overlap = len(claim_words & source_words) / max(1, len(claim_words))
            if overlap > 0.3:
                return True, True
        return False, False


if __name__ == "__main__":
    qa = QualityAssessment()
    output = """
    Artificial intelligence is transforming healthcare.
    Machine learning can predict diseases with 95% accuracy.
    Deep learning requires large datasets.
    """
    sources = [
        {"text": "AI is transforming healthcare through machine learning"},
        {"text": "Deep learning models require large training datasets"},
    ]
    result = qa.assess(output, sources)
    print(f"✓ Quality Assessment v2")
    print(f"  Factual Error Rate: {result['factual_error_rate']:.1%}")
    print(f"  Source Verification: {result['source_verification_rate']:.1%}")
    print(f"  Claim Support: {result['claim_support_rate']:.1%}")
