---
title: Model Gateway — Dynamic Model Interaction Layer
type: system-contract
version: "1.0"
status: active
date: 2026-09-11
author: deep-dive
---

# Model Gateway Contract

The system interacts with AI models through a unified gateway. The user selects models;
the gateway routes, caches, tracks costs, and falls back automatically.

---

## 1. User Model Registry

The user declares available models in `model-registry.json`. Each model entry:

```json
{
 "id": "claude-sonnet-4",
 "provider": "anthropic",
 "model_id": "claude-sonnet-4-20250514",
 "params": "1T",
 "context_window": 200000,
 "cost_per_1m_tokens": {"input": 3.0, "output": 15.0},
 "tier": "capable",
 "best_for": ["strategy", "drafting", "verification"],
 "speed": "medium",
 "enabled": true
}
```

---

## 2. Dynamic Selection Logic

The gateway selects a model per task based on:

| Factor | Weight | How measured |
|---|---|---|
| Task complexity | 40% | Router intent analysis |
| User preference | 25% | Saved history |
| Cost budget | 20% | Remaining daily/weekly budget |
| Speed requirement | 15% | Tier and urgency |

### Selection algorithm:

```
1. Router classifies task complexity (low / medium / high / critical)
2. Filter models by: enabled=true AND tier >= complexity AND context_window >= needed
3. Score remaining by: 0.4*fit + 0.25*preference + 0.2*budget + 0.15*speed
4. Pick highest score
5. Log selection + reason
```

---

## 3. Fallback Chain

If the selected model fails (timeout, error, quality rejection), escalate:

```
SLM (user default) → SLM (alternative) → Medium model → Large model → Human escalation
```

The fallback chain is user-configurable. Default:

```
1. User's primary choice (e.g., ling-3.0-flash)
2. System default SLM (e.g., llama-3-8b)
3. System capable fallback (e.g., claude-sonnet)
4. Human escalation (blocker payload)
```

---

## 4. Caching Layer

Cache frequent queries to avoid redundant LLM calls:

- Key: hash(normalized_query + model_id + skill)
- TTL: 1 hour for search tasks, 24 hours for factual lookups
- Max cache: 1000 entries, LRU eviction
- Hit rate target: >30% for repeated tasks

---

## 5. Cost Tracking

Every model call is logged with:

```json
{
 "timestamp": "2026-09-11T10:30:00Z",
 "model_id": "claude-sonnet-4",
 "mission_id": "20260911_abcd12",
 "agent": "editor-qa",
 "stage": "verify",
 "input_tokens": 4500,
 "output_tokens": 1200,
 "cost_usd": 0.0195,
 "cached": false,
 "fallback_used": false
}
```

Rolled up daily/weekly. Alerts when budget threshold reached.

---

## 6. User Preference Learning

The system learns from user corrections:

- If user manually switches model → record preference for that task type
- If user rejects output → mark model as weak for that task type
- If user accepts → reinforce current choice

Stored in `model-preferences.json`:

```json
{
 "task_type": "research",
 "preferred_model": "ling-3.0-flash-fin-free",
 "switch_count": 3,
 "acceptance_rate": 0.85
}
```

---

## 7. Model Gateway API

The gateway exposes:

| Method | Purpose |
|---|---|
| `select(task, context)` → model_id | Pick best model for task |
| `execute(model_id, prompt, options)` → response | Call model with fallback |
| `cache_get(query)` → response | Check cache |
| `cache_set(query, response)` | Store in cache |
| `log_call(metrics)` | Record usage |
| `get_budget_status()` → {daily, weekly, remaining} | Cost tracking |

---

## 8. Integration Points

- `registry.json` → reads model list + context windows
- `routing.yaml` → model selection happens at tier assignment
- `evolution.md` → model performance feeds evolution loop
- `quality-metrics.md` → model choice logged with quality score
- `quality-charter.md` → model selection is logged and auditable
- `protocol.md` → model_id in every inter-agent envelope metadata

---

*Model Gateway v1.0 — added 2026-09-11 by deep-dive. The missing piece: the system now talks to models, not through them.*
