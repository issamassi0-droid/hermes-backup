---
name: model-router
description: "Selects thinking tier and model spec for a task, given its complexity score from token-optimizer. This skill was previously referenced by token-optimizer and SOUL.md but did not exist — this closes that gap."
version: 1.0.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [model, routing, tier-selection]
    category: orchestrator
    related_skills: [token-optimizer, agent-dispatch-protocol, final-audit]
---

# Model Router

## Purpose
Given a task's complexity score (1–6, from `token-optimizer` Stage 1) and task type, produce the thinking tier and concrete model spec to show in the SOUL.md recommendation block. This is the missing piece that previously let "Model Recommendation" happen ad hoc with no defined rule.

## Tier Mapping

| Complexity score | Thinking tier | Typical use | Default expected turnaround |
|---|---|---|---|
| 1–2 | 🟢 Light | Lookups, simple formatting, short factual answers | ~2 min |
| 3–4 | 🟡 Medium | Single-document research, standard drafting, moderate analysis | ~5 min |
| 5–6 | 🟠 Deep | Multi-source research, strategy synthesis, long-form drafting with citations, code review | ~15 min |

The turnaround column feeds the Agent Timeout check in `agent-dispatch-protocol` — it is a guideline for when to check in with the user, not a hard kill switch.

## Selecting a Concrete Model
1. Start from the tier above.
2. Check the target agent's declared skill list (`agent-dispatch-protocol` registry) — some agents are only calibrated for specific tiers (e.g. a heavy citation-verification pass on `@qa-agent` should not be downgraded to 🟢 just because the input is short, if verifying claims is inherently a multi-step task).
3. If the task explicitly names stakes ("this goes to a client," "this is for publication," "just a draft for myself") — treat stated stakes as a modifier: raise one tier for high-stakes, allow one tier lower for explicitly low-stakes throwaway work, but never below 🟡 for anything that will be shown to a third party.
4. If unsure between two tiers, default to the higher one and say so in the recommendation ("defaulted to 🟡 Medium given ambiguity in scope") rather than silently picking the cheaper option to make the recommendation look better.

## Interaction with Budget
Tier and cost tier (💰/💰💰/💰💰💰 from `token-optimizer`) are correlated but not identical — a 🟠 Deep task on a short input can still be 💰 Budget in raw tokens. Report both independently in the recommendation; do not conflate them into one number.

## Staleness Check
Model availability changes over time (deprecations, renames). If a model spec in this table hasn't been confirmed against the live agent registry in the current session, treat it as `[unverified: model availability]` in the recommendation rather than asserting it as fact.
