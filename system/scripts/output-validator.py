#!/usr/bin/env python3
"""
Output Validator — Cabinet-Office System
Rejects ungraded claims and measures factual error rate.
"""
import json
import pathlib
import re


class OutputValidator:
    def __init__(self):
        self.metrics = {
            "total_claims": 0,
            "graded_claims": 0,
            "ungraded_claims": 0,
            "factual_errors": 0
        }

    def validate(self, output: str, evidence_grades: dict = None) -> dict:
        """Validate output and reject ungraded claims"""
        claims = self._extract_claims(output)
        graded = 0
        ungraded = 0
        errors = 0

        for claim in claims:
            if self._is_graded(claim, evidence_grades):
                graded += 1
            else:
                ungraded += 1

            if self._is_factual_error(claim, evidence_grades):
                errors += 1

        self.metrics["total_claims"] = len(claims)
        self.metrics["graded_claims"] = graded
        self.metrics["ungraded_claims"] = ungraded
        self.metrics["factual_errors"] = errors

        return {
            "valid": ungraded == 0,
            "total": len(claims),
            "graded": graded,
            "ungraded": ungraded,
            "errors": errors,
            "action": "approve" if ungraded == 0 else "escalate_to_qa"
        }

    def _extract_claims(self, output: str) -> list:
        """Extract claims from output"""
        sentences = re.split(r'[.!?]', output)
        claims = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 15 and not sent.startswith(('I ', 'We ', 'My ')):
                claims.append(sent)
        return claims

    def _is_graded(self, claim: str, evidence_grades: dict = None) -> bool:
        """Check if claim has evidence grade"""
        if not evidence_grades:
            return False
        return claim[:30] in evidence_grades

    def _is_factual_error(self, claim: str, evidence_grades: dict = None) -> bool:
        """Check if claim is factual error"""
        if not evidence_grades:
            return False
        grade = evidence_grades.get(claim[:30], "")
        return grade in ['[U]', '[H]', '[X]']


if __name__ == "__main__":
    validator = OutputValidator()
    output = """
    AI will replace 50% of jobs by 2030.
    Machine learning improves healthcare outcomes.
    """
    result = validator.validate(output, {})
    print(f"✓ Validator: valid={result['valid']}, ungraded={result['ungraded']}, action={result['action']}")
