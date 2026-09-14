---
name: agent-dispatch-protocol
description: "Clear rules for when to use delegate_task vs message_agent, and multi-agent topology handling (sequential/parallel/mixed). The agent registry itself — every agent's contract, inputs, outputs, and decision authority — lives in /shared/agent-registry.md, a cluster-wide file this skill references but never duplicates."
version: 3.0.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [dispatch, delegate_task, message_agent, protocol, topology]
    category: orchestrator
    related_skills: [token-optimizer, model-router, final-audit]
    shared_dependencies: ["/shared/agent-registry.md"]
changelog:
  - "3.0.0: moved the agent registry out to /shared/agent-registry.md (cluster-wide, not orchestrator-only) to prevent other agents operating without knowledge of their own contract and decision-authority limits. This file now covers dispatch mechanics and topology only."
  - "2.0.0: added parallel/sequential topology rules, agent-swap escalation ceiling, registry staleness check, timeout definition distinct from connection failure"
---

# Agent Dispatch Protocol

## Rule: Use `message_agent` for Specialized Work

| Tool | When | What It Does |
|------|------|--------------|
| `message_agent` | Task needs specialized skills | Sends message to real agent with skills, memory, profile |
| `delegate_task` | Mechanical batch processing (N>1), no skills needed | Creates generic subagent with tools only |

If in doubt between the two: default to `message_agent`. A generic subagent with no skill access producing a wrong result costs more (in redo cycles) than the marginal overhead of a real agent.

## Agent Registry — moved to `/shared/agent-registry.md`
The full registry (every agent's role, inputs, outputs, tools, and — critically —
its decision authority under the Authority Boundary rule) is **not** duplicated
in this file. It lives in `/shared/agent-registry.md` because every agent in the
cluster, not just orchestrator, needs to know its own contract to operate
correctly. Load that file fresh each session — do not rely on a cached copy. If
an agent listed there fails to connect 3 times in a row across multiple tasks,
flag it to the user as possibly deprecated rather than continuing to route to it
silently.

**Reminder from the shared registry's Authority Boundary (do not re-derive this
locally, just apply it):** every agent's output routes to `orchestrator-agent`
only — never directly to another agent — and only orchestrator's own
`final-audit` run produces a PASS/REJECT decision. This skill's job is *how* to
route a confirmed plan across that boundary; it does not grant any agent
permission to bypass it.

## Dispatch Topology

### Sequential (chain)
Use when agent N+1 needs agent N's output to start (research → draft → qa → distribution). Dispatch one at a time. Pass the prior agent's full output as context — do not summarize it down before handoff unless it exceeds the next agent's practical context budget (if so, summarize via `token-optimizer` rules and say so to the user).

### Parallel (fan-out)
Use when two or more agents have no dependency on each other's output (e.g. `@research-agent-multi` on market data + `@analytics-agent` on internal spreadsheet data, for the same report). Dispatch together. Wait for all to return before the next stage. Cap: 4 concurrent agents by default; raising this requires explicit user confirmation, since it multiplies both cost and audit surface.

### Mixed
Most non-trivial tasks are a DAG, not a pure chain: e.g. research (parallel: web + video) → strategy (sequential, needs both research outputs) → draft → qa → distribution (sequential). Build the full DAG before showing the recommendation to the user, not incrementally.

## Connection Failure Protocol

| Attempt | Action |
|---------|--------|
| 1 | Normal attempt |
| 2 | Wait 3 seconds, retry |
| 3 | Wait 5 seconds, retry |
| **Fail 3 times** | **Notify user immediately — no more attempts** |

### Failure Notification

```
⚠️ Connection to @agent-name failed after 3 attempts.

Possible cause: Model <model-name> unavailable.

Options:
├─ Change model → "Use <model-name>"
├─ Retry → "Retry"
├─ Different agent → "Use @other-agent"
└─ Cancel → "Cancel"
```

## Agent Timeout (distinct from connection failure)
A failed *connection* means the agent never picked up the task. A *timeout* means it connected and is working but hasn't returned within the expected window for its declared complexity tier (🟢/🟡/🟠 — see `token-optimizer`). Do not apply the 3-attempt connection-failure protocol to a slow-but-working agent; instead check in with the user per SOUL.md's "On Agent Timeout" rule. Killing and retrying a genuinely long research job wastes the tokens already spent.

## Agent-Swap Escalation Ceiling
If the same task is retried with a *different* agent after a failure (connection or quality) and that second agent also fails for the same underlying reason (e.g. neither can access a required data source), stop trying additional agents automatically. Report to the user after 2 distinct agents have failed on the same task: what was tried, why it failed, and ask how to proceed. Do not silently cycle through the entire registry.

## Research Before Write Rule

If task requires **factual information** (future of X, policy, event, product, statistics):
1. Research first (myself or via `@research-agent-multi` / `@research-agent-youtube`)
2. Collect sources, note publish dates
3. Include findings as context in the writer's task, explicitly marking anything time-sensitive
4. Instruct the writer to cite those sources and to flag rather than smooth over conflicting figures across sources

If **opinion/creative** with no factual dependency: dispatch directly to `@strategy-agent` or `@drafting-agent`.

## Anti-Patterns

| Wrong | Right |
|-------|-------|
| `delegate_task` + "use youtube-content skill" | `message_agent(target='research-agent-youtube')` |
| Writing without research | Research first, then write with sources |
| Silent wait after 3 failures or a long-running timeout | Immediate user notification either way, via the right protocol for which one occurred |
| Fake skill access in subagent | Use real agents via message_agent |
| Cycling through every agent in the registry after repeated failure | Escalate to user after 2 distinct agent failures on the same root cause |
| Treating a slow research job as a connection failure | Distinguish timeout from connection failure; don't kill working agents prematurely |
