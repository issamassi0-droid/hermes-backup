---
name: system-hardening
description: "Cross-cutting failure modes that don't belong to any single skill: partial fan-out failure, duplicate-task detection, skill-file integrity checks, observability, data retention, rollback, code-execution isolation, and self-testing. Load alongside agent-dispatch-protocol, token-optimizer, final-audit, and model-router — this is not a replacement for any of them."
version: 1.1.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [hardening, reliability, observability, idempotency, security, sandboxing]
    category: orchestrator
    related_skills: [agent-dispatch-protocol, token-optimizer, final-audit, model-router]
    shared_dependencies: ["/shared/agent-registry.md"]
changelog:
  - "1.1.0: added §8 code-execution isolation, covering sandbox requirements for qa-agent's execution_report runs — this was a gap once coder-agent/qa-agent started producing runnable code, not just text."
---

# System Hardening

These are gaps that don't live inside any single pipeline stage — they're properties the whole system needs, and a spec that only covers the happy path plus obvious failures (connection drops, bad audits) still breaks in production without them.

## 1. Partial Fan-Out Failure
`agent-dispatch-protocol` defines parallel dispatch but not what happens when *some* of N parallel agents succeed and others fail or time out. Rule:
- If ≤50% of a parallel batch fails, proceed with the successful results, explicitly mark the missing portion as `[unavailable: @agent-name failed/timed out]` in the downstream task context, and surface this to the user in the final result — do not silently present a partial picture as complete.
- If >50% of a parallel batch fails, treat the whole stage as failed: stop, apply the Agent-Swap Escalation Ceiling from `agent-dispatch-protocol`, and report to the user rather than pushing a mostly-empty result forward into the next pipeline stage.
- Never let a downstream sequential agent silently receive a gap-filled/hallucinated stand-in for a failed parallel input — the missing-data flag must travel with the context, not get smoothed over by the next agent's own inference.

## 2. Idempotency & Duplicate Task Detection
Nothing in the original spec prevents the same task being dispatched twice (e.g. user resends a message after a slow response, or a retry fires after the original actually succeeded).
- Before dispatch, check `session_search` / recent `task_id` log for a task with materially identical intent within the current session window (default: last 30 minutes).
- If a near-duplicate is found and its audit result was PASS or PASS WITH WARNINGS, surface that prior result to the user first ("I already did this — here's that result — want me to redo it or is this sufficient?") rather than re-dispatching and re-spending tokens by default.
- If the prior attempt REJECTed or was cancelled, proceed with a fresh `task_id` but note the prior attempt's `task_id` in the new entry's context for traceability.

## 3. Skill/Registry Integrity Check
SOUL.md and the skills reference each other (agent registry, token thresholds, audit ceilings). A stale or hand-edited skill file that drifts out of sync with the others is a silent failure mode.
- On session start, verify that every skill referenced by name in SOUL.md (`agent-dispatch-protocol`, `token-optimizer`, `model-router`, `final-audit`) is actually loadable and declares a `version` in its frontmatter.
- If a referenced skill is missing, unreadable, or its version looks incompatible (e.g. SOUL.md v2.0.0 expects `final-audit` ≥2.0.0 for the quantifiable deviation method, but only v1.0.0 is present), do not silently fall back to improvising the missing logic from memory of what it "probably says." State plainly: "final-audit skill is at an older version than expected — deviation measurement may not be quantifiable; proceeding with best-effort audit and flagging this in the result."

## 4. Observability & Traceability
Every `task_id` should produce a reconstructable trail: what was requested, what was decided, what was dispatched, what came back, what the audit found, what was shown to the user. This isn't optional logging — it's what makes "verify before I respond" (Core Principle 2) actually checkable after the fact rather than a self-report with no evidence.
- Minimum trail per task: request text (or a faithful compressed version), the displayed recommendation, the user's normalized response, each agent dispatch and its raw result, the audit verdict per stage, and the final text shown to the user.
- This trail is what a human reviewer should be able to use to answer "why did the orchestrator do X" without asking the orchestrator to explain itself after the fact from memory.

## 5. Data Handling & Retention
Tasks may carry sensitive user data (draft contracts, personal research, unreleased company info) through multiple agents.
- Do not include sensitive content in memory-log `value` fields beyond what's needed for the audit trail (Section 4) — log references/summaries of sensitive payloads, not the full payload itself, unless the user has explicitly asked for full retention.
- When a task is cancelled or REJECTed permanently, note in the log that downstream agents may still be holding a copy of the dispatched content in their own context — this system does not control agent-side retention, and that limitation should be disclosed to the user on request, not assumed away.

## 6. Rollback / Compensating Actions
Some agent actions aren't purely informational — `@distribution-agent` may actually publish something (a doc pushed to Obsidian, a PDF sent somewhere). If a downstream audit REJECTs *after* such an action already happened:
- This is a different failure class than a pre-publication reject. Flag it distinctly: "the draft was already published/sent by @distribution-agent before the audit caught [issue] — do you want it retracted/corrected, or is this acceptable to leave as-is?"
- Never let the pipeline treat "audit ran after an irreversible action" the same as "audit ran before one." The recommendation step should flag upfront which pipeline stages are reversible and which aren't (e.g. "note: the distribution step publishes immediately and is not easily undone — confirm before we get there" as part of the initial plan display, not a surprise after the fact).

## 7. Code-Execution Isolation
`@qa-agent`'s `execution_report` (the only accepted evidence for code
correctness — see `final-audit` Stage 3 and the `@qa-agent` card in
`/shared/agent-registry.md`) must never run against a live/shared environment.
- **Isolation:** a disposable sandbox/container per run, torn down after, with
  no access to other data or systems in the cluster.
- **Network:** disabled by default. If `coder-agent` declares network access is
  genuinely required (e.g. hitting a real API), that requirement surfaces to
  the user as an additional flagged item in the plan recommendation — the same
  way an irreversible `@distribution-agent` step is flagged — not silently
  granted.
- **Resource/time limits:** strict caps on CPU, memory, and wall-clock time,
  enforced independently of the general Agent Timeout in
  `agent-dispatch-protocol` — a runaway loop in submitted code is a different
  failure class from a slow-but-working agent, and should be killed, not
  waited out.
- **Environment fidelity:** the sandbox must match `environment_manifest`
  exactly (declared runtime version, locked dependency versions). A mismatch
  invalidates the `execution_report` — re-run in a correctly provisioned
  sandbox rather than trusting a result from a different environment than the
  one the code was written against.
- **Flaky handling:** exactly one re-run permitted on a failing test, per the
  `@qa-agent` protocol — this section only governs the isolation properties of
  each run, not the retry-count policy itself.

## 8. Self-Testing
A spec this detailed is only as good as its adherence in practice. Periodically (or when asked to "audit yourself"):
- Pull the last N task logs (Section 4) and re-run the `final-audit` Stage 1 deviation formula on them independently, to check whether the live audit verdicts actually match a recomputation — this catches drift where "PASS" verdicts stopped being backed by the stated method.
- Report any mismatch to the user as a system reliability finding, not something to quietly patch and forget.
