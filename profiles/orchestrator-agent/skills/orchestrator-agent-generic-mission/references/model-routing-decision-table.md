# Model Routing Decision Table

## Price Reference (per million tokens)

| Model | Input | Output | Use When |
|-------|-------|--------|----------|
| `gpt-4o-mini` | $0.15 | $0.60 | lookup, classification, simple extraction |
| `claude-haiku-4` | $0.25 | $1.25 | research, summarization, short writing |
| `gpt-4o` | $2.50 | $10.00 | medium writing, analysis, coding |
| `claude-sonnet-4` | $3.00 | $15.00 | complex strategy, long-form, deep analysis |
| `claude-opus-4` | $15.00 | $75.00 | high-stakes decisions, maximum reasoning |

## Task Type → Model Mapping

```
IF task_type == "lookup" AND complexity == 1:
    model = "gpt-4o-mini"
    tier = 1

ELIF task_type == "research" AND complexity <= 3:
    model = "claude-haiku-4"
    tier = 2

ELIF task_type == "writing" AND complexity <= 4:
    model = "gpt-4o"
    tier = 2

ELIF task_type == "strategy" OR complexity >= 5:
    model = "claude-sonnet-4"
    tier = 3

ELIF task_type == "deep_reasoning" OR stakes == "high":
    model = "claude-opus-4"
    tier = 4

ELSE:
    model = "gpt-4o"
    tier = 2
```

## User Override Keywords

| User Says | Action |
|-----------|--------|
| "نموذج أرخص" / "cheaper" | Downgrade one tier |
| "نموذج أذكى" / "smarter" | Upgrade one tier |
| "عميق" / "deep" | Set to `claude-opus-4` |
| "سريع" / "fast" | Set to `gpt-4o-mini` |
| "تلقائي" / "auto" | Orchestrator decides |

## Cost Calculation

```
cost = (input_tokens / 1_000_000 * input_price +
        max_output_tokens / 1_000_000 * output_price)
```

## Cache Eligibility Rules

| Query Type | Cache? | TTL |
|------------|--------|-----|
| Weather / stock prices | ✅ Yes | 3600s (1h) |
| Static facts (capital of X) | ✅ Yes | 86400s (24h) |
| Breaking news | ❌ No | — |
| Personal / contextual | ❌ No | — |
| Time-sensitive quotes | ⚠️ Maybe | 300s (5m) |
