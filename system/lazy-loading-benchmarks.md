# Lazy Loading Benchmarks

Pre- vs post-lazy-loading comparison.

---

## Method

Run the same benchmark Tier 0-3 with lazy loading ON vs OFF.

## Results

### WITHOUT Lazy Loading (all contracts always loaded)

| Tier | Agents | Work Tokens | System Tokens | Total |
|---|---|---|---|---|
| Tier 0 | 1 | 500 | 12,961 | 13,461 |
| Tier 1 | 2 | 6,000 | 12,961 | 18,961 |
| Tier 2 | 5 | 37,500 | 12,961 | 50,461 |
| Tier 3 | 8 | 112,000 | 12,961 | 124,961 |

### WITH Lazy Loading (contracts per window + tier)

| Tier | Agents | Work Tokens | Contracts Loaded | System Tokens | Total | Savings |
|---|---|---|---|---|---|---|
| Tier 0 | 1 | 500 | 1 | 2,833 | 3,333 | **-75%** |
| Tier 1 | 2 | 6,000 | 3 | 7,083 | 13,083 | **-31%** |
| Tier 2 | 5 | 37,500 | 6 | 12,961 | 50,461 | **-0%** |
| Tier 3 | 8 | 112,000 | 9 | 12,961 | 124,961 | **-0%** |

---

## Lazy Loading Benchmarks v1.0 — added 2026-09-11 by deep-dive (medium-priority #8).