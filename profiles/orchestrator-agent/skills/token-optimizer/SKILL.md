---
name: token-optimizer
description: "Analyzes, compresses, and budgets tokens for every LLM prompt. Runs as a pre-processing gate before any agent dispatch. Model selection itself is NOT handled here — see model-router."
version: 2.0.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [token, optimization, compression, budget]
    category: orchestrator
    related_skills: [model-router, final-audit, agent-dispatch-protocol]
changelog:
  - "2.0.0: defined budget ceilings, generalized token-estimation formula beyond English/Arabic, tightened cache staleness rules, clarified division of labor with model-router"
---

# Token Optimizer

## Scope
This skill handles token **estimation, compression, and budgeting**. It does not decide *which model* an agent runs on — that's `model-router`. Run both before displaying a recommendation: token-optimizer produces the token/cost numbers, model-router produces the tier (🟢/🟡/🟠) and model spec.

## How It Works

### Stage 1: Analyze

| Metric | Method |
|--------|--------|
| Current tokens | Estimate: chars / 4 for Latin-script languages (English, French, Spanish, etc.), chars / 2.5 for dense/non-spaced scripts (Arabic, Chinese, Japanese, Korean). If the input language is unclear or mixed, estimate both ways and use the higher figure — never silently default to the English ratio for unknown scripts, since that undercounts and produces broken budgets. |
| Filler ratio | Count filler phrases ("please", "kindly", "due to the fact that", equivalents in the input language) |
| Task type | lookup / research / writing / strategy / coding |
| Complexity | 1–6 scale based on required steps (see `model-router` for how this maps to thinking tier) |

### Stage 2: Compress (Based on Task Type)

**Lookup queries** → Remove context, keep question only, max_tokens: 200–500

**Research queries** → 3–5 keywords + criteria, max_tokens: 1000–2000, cache_eligible: true

**Writing** → Type + length + audience + key points, max_tokens: ~130 words per 100 words of target output

**Strategy** → Domain + goal + constraints + output, max_tokens: 1500–3000

**Coding** → Language + task + I/O, max_tokens: 500–1500

**Multi-agent plans** → Sum the compressed max_tokens of every agent in the plan (sequential or parallel) to get the plan-level ceiling shown in the SOUL.md recommendation. Never show a per-agent number alone when the plan involves more than one agent — the user needs the total to make an informed "yes."

### Stage 3: Output

```json
{
  "original_tokens": "<count>",
  "compressed_prompt": "<text>",
  "compressed_tokens": "<count>",
  "compression_ratio": "<percentage>",
  "max_tokens": "<ceiling>",
  "cache_eligible": "<true|false>",
  "estimated_cost_usd": "<value>"
}
```

### Stage 4: Semantic Cache Check

| Query type | cache_ttl | Notes |
|---|---|---|
| Repetitive factual queries (stable facts: definitions, historical events, unit conversions) | 3600s | Short TTL because "repetitive" doesn't guarantee the fact is timeless |
| Static research queries (explicitly confirmed non-time-sensitive by the user or task type, e.g. "explain how X algorithm works") | 86400s | Never assign this TTL by default — a query only qualifies if nothing about it could plausibly change within a day. Current events, prices, rankings, "latest," "current," or anything with a named living person's role/status is disqualified regardless of how "static" it looks on the surface. |
| Personal or time-sensitive queries | cache_eligible: false | Always |
| Any query touching an agent registry, model availability, or pricing | cache_eligible: false | These change independently of the query itself; a cache hit here can serve stale infrastructure info |

- If a semantic cache hit exists and passes the disqualification check above → return cached response, no dispatch, but still tell the user the result is from cache and when it was generated, so they can force a refresh if needed.

## Budget Ceilings (feeds SOUL.md Budget Tracking)

| Cost tier | Token range (plan-level) | Requires explicit user confirmation above default? |
|---|---|---|
| 💰 Budget | up to ~5,000 | No — default assumption |
| 💰💰 Mid | ~5,000–15,000 | No — default assumption |
| 💰💰💰 Premium | 15,000+ | Yes — always called out explicitly in the recommendation, never bundled silently into "Mid" |

Default ceiling absent other user instruction: 💰💰 Mid, ~15,000 tokens total across the whole plan. SOUL.md pauses the plan at 80% of whatever ceiling was confirmed.
