# Wall-Clock Latency Report

Real-world mission latency estimates.

---

## Method

Average end-to-end time per tier, assuming:
- Average LLM call: 8 seconds
- Average tool call: 3 seconds
- Sequential agents in chain (no parallelism within tier)

## Results

| Tier | Agents | Avg Calls/Agent | Estimated Latency |
|---|---|---|---|
| Tier 0 | 1 | 1 | **~11 seconds** |
| Tier 1 | 2 | 2 | **~44 seconds** |
| Tier 2 | 5 | 3 | ~2 minutes 40 seconds |
| Tier 3 | 8 | 4 | ~5 minutes 20 seconds |

## Bottleneck

Tier 3's 8-agent sequential chain is the actual bottleneck users notice, not tokens.

---

## Latency Report v1.0 — added 2026-09-11 by deep-dive (medium-priority #9).