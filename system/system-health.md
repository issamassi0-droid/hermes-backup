# System Health Dashboard

Weekly observability report reviewed by the human. Turns "we fixed known risks" into "we'd notice if a new one appeared."

---

## Dashboard Metrics

| Metric | Source | Target |
|---|---|---|
| factual_error_rate (rolling) | quality-trend.json | < 5% |
| human_override_rate (rolling) | quality-trend.json | < 20% |
| escalation count / week | ledger | < 3 |
| Architect failover events | architect-failover log | 0 |
| Tier accuracy | evolution_report.json | > 90% |
| QA effectiveness (precision/recall) | evolution_report.json | > 0.8 |

## Review Cadence

- Weekly: Dashboard reviewed by human
- Monthly: Evolution review with full metrics
- Quarterly: Constitutional review (principles unchanged?)

## Alert Thresholds

- factual_error_rate > 10% → immediate blocker
- human_override_rate > 30% → tier calibration review
- 2+ escalations in a week → Architect performance review

---

## System Health v1.0 — added 2026-09-11 by deep-dive (v1.1 patch, high-priority #4).