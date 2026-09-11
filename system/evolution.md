# System Evolution Loop v1.0

How the Cabinet-Office system learns from its own runs and rewrites itself safely.

---

## The Loop

```
 ┌─────────────────────────────────────────────┐
 │ │
 v │
 ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ run the │───▶│ collect │───▶│ analyze │───▶│ amend │
 │ pipeline │ │ ledger + │ │ patterns │ │ SOULs / │
 │ │ │ analytics│ │ │ │ registry │
 └──────────┘ └──────────┘ └──────────┘ └──────────┘
 ▲ │
 │ │
 └──────────── next run uses new SOULs ◀──────────┘
```

The loop runs on a **cron schedule** (monthly) and on **demand** (after any 50th mission).

---

## What Gets Collected

Every mission leaves behind:
1. `ledger/<mission_id>/*.json` — per-stage artifacts + confidence + tokens
2. `ledger/<mission_id>/coverage.json` — blind-spot matrix + tier events
3. `analytics.json` (tier 3 only) — hypothesis updates for Researcher/Strategist

Collection is automatic. Nothing extra is required from agents.

---

## What Gets Analyzed

The Analyst role is played by **@analytics** (with **@architect** as co-analyst for tier calibration). For each review period, produce a `evolution_report.json`:

```json
{
 "period": "2026-09-11..2026-10-11",
 "missions_run": 47,
 "tier_distribution": {"0": 12, "1": 18, "2": 14, "3": 3},
 "tier_accuracy": {
 "correct": 44,
 "under_tiered": 2,
 "over_tiered": 1,
 "accuracy": 0.936
 },
 "qa_effectiveness": {
 "precision": 0.82,
 "recall": 0.71,
 "avg_cycles_to_converge": 1.3
 },
 "escalation_accuracy": {
 "total": 6,
 "correct": 5,
 "spurious": 1,
 "accuracy": 0.833
 },
 "coverage_completeness": {
 "missions_with_all_blind_spots_covered": 45,
 "missions_with_uncovered": 2,
 "completeness": 0.957
 },
 "token_economy": {
 "tier_0_actual_vs_budget": "0.4x",
 "tier_1_actual_vs_budget": "0.6x",
 "tier_2_actual_vs_budget": "0.9x",
 "tier_3_actual_vs_budget": "1.05x"
 },
 "proposed_amendments": [
 {
 "target": "routing.yaml",
 "change": "Raise tier-2 token budget to 16000 — actuals running 105% of budget.",
 "evidence": "9 of 14 tier-2 missions exceeded 15000 tokens.",
 "risk": "low"
 }
 ]
}
```

---

## Amendment Protocol

Proposed amendments fall into three risk classes. Each has a different approval path.

### Pre-Apply Check (before Class 1 auto-apply)

Before any Class 1 amendment is auto-applied, the Architect MUST verify the amendment's diff does not touch `routing.yaml`'s scoring section. If it does, escalate to Class 3 automatically — do not auto-apply under any circumstances, even if the amendment's own self-assessment scores it as low-risk.

### Class 1 Auto-Apply Procedure (revised)

1. Amendment proposed, tagged with a version ID (e.g. `amend-0042`).
2. Before the 7-day window closes, run the amendment against a fixed regression set of the last 20 completed missions (replay, not live).
3. Compare factual_error_rate and human_override_rate (see `quality-metrics.md`) before vs. after simulated application.
4. If either metric regresses by more than 10%, the amendment is automatically downgraded to Class 2 (Architect sign-off required) instead of auto-applying.
5. If applied and, within 14 days of going live, quality-trend.json shows a real regression matching the predicted failure mode, auto-revert to the pre-amendment contract version and notify the human via the standard `blocker` payload.

This requires every systemic contract to be version-tagged and stored (not overwritten) — i.e. `registry.json.v3`, `registry.json.v4`, etc., with the evolution loop always able to diff and revert.

### Class 1 — Low risk (auto-apply after 7 days)
- Token budget tweaks within +/-20%
- Temporal bound tweaks (e.g. Tech from 6m to 9m)
- Adding a new blind spot to the baseline list
- Adding a new hypothesis to the analytics feedback loop

Path: **@analytics proposes → @architect reviews → 7-day cooling-off → auto-applied to the relevant file → change noted in CHANGELOG.md.**

### Class 2 — Medium risk (requires @architect sign-off)
- Adding a new stage to a tier's pipeline
- Changing the verification floor for a stakes level
- Adding a new agent to the registry
- Modifying the message budget in protocol.md

Path: **@analytics proposes → @architect signs off → applied → change noted → 24h manual rollback window.**

### Class 3 — High risk (requires user approval)
- Changing the Quality Charter (any article)
- Removing an agent from the registry
- Changing the independent-verification rule (Art. III)
- Anything that alters the human escalation ladder

Path: **@analytics proposes → @architect reviews → @architect messages user → user approves in chat → applied.**

---

## SOUL Amendment Rules

An agent's SOUL may be amended by:
1. **@bot-maker** — the ONLY agent with standing authority to author or rewrite a SOUL.
2. **@architect** — may propose an amendment to @bot-maker, must include evidence from the ledger.
3. **The agent itself** — may propose an amendment to @bot-maker, must include evidence.

All SOUL amendments:
- Are logged in `system/CHANGELOG.md`
- Preserve the *Creed*, *Canon*, *Skills*, *Boundary* structure
- Never weaken a Boundary without explicit user approval

---

## Rollback

Every amendment is written to `system/CHANGELOG.md` with:
- timestamp
- target file
- before-hash
- after-hash
- proposer
- approver

To roll back, use `bootstrap.sh --rollback <changelog-entry-id>` which restores the file to its before-hash state.

---

## What the System Explicitly Does NOT Evolve

(The seven constitutional principles — see `constitutional.md`)

- The seven constitutional principles (see `constitutional.md`) — these are immutable.
- The refusal lines in any agent's Boundary.
- The evidence grading rubric's five labels.

These are the system's constitutional layer. Changing them requires a full re-authoring, not an amendment.

---

## Triggering a Review

```bash
# Manual monthly review
hermes message_agent analytics "Run evolution review for period <start>..<end>."
```

Or schedule via cron:
```
0 9 1 * * hermes message_agent analytics "Run monthly evolution review."
```

---

*Evolution Loop v1.0 — authored 2026-09-11 by deep-dive. The gap it fills: the system previously had no mechanism for its own SOULs to improve.*
---

## Change Class: EFFECTIVE (Low Token / High Value)

| Class | Trigger | Cost | Action |
|---|---|---|---|
| **E1** | Agent detects broken output | 1 LLM call | 1 self-repair attempt, log result |
| **E2** | Scoring rubric below cutoff | 1 LLM call | Shelve, no human gate needed |
| **E3** | Group room turns ≥ 8 | 0 LLM calls | Conversation pauses, prompt human |
| **E4** | Tool outside allowlist | 0 LLM calls | Block + log, suggest alternative agent |

