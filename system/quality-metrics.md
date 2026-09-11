# Quality Metrics Contract

Every completed mission MUST be scored on three axes before it is
considered closed:

| Metric | Definition | Measured by |
|---|---|---|
| factual_error_rate | % of claims in the final artifact that fail independent verification (Editor-QA re-check against source) | Editor-QA |
| source_verification_rate | % of claims tagged [V] or [M] vs. [U]/[H]/[X] at time of publish | Editor-QA |
| human_override_rate | % of missions where the human gate rejected or materially edited the output | Architect (logged at gate) |

Scores are written to `ledger/<mission_id>/quality.json` per mission and rolled up weekly into `quality-trend.json`.

A mission's quality score is a REQUIRED input to the Evolution Loop. No amendment may be evaluated using token cost or latency alone.

---

*Quality Metrics Contract v1.0 — added 2026-09-11 by deep-dive as Fix 1 of v1.1 patch.*