---
name: final-audit
description: "Final evaluation gate before returning results to the user. Verifies intent alignment, completeness, source integrity, bias detection, and output quality — with quantifiable pass/fail criteria, not just checklist prose. This is the only mechanism in the cluster that produces a PASS/REJECT decision — see the Authority Boundary rule in /shared/agent-registry.md."
version: 2.2.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [audit, verification, quality, final-check, authority]
    category: orchestrator
    related_skills: [grounded-citations, triage, agent-dispatch-protocol, model-router]
    shared_dependencies: ["/shared/agent-registry.md"]
changelog:
  - "2.2.0: noted that the verification status this audit assigns (verified/[unverified]/[disputed]) is the one that travels forward into @archivist-agent's second brain — archiving never re-adjudicates or softens it."
  - "2.1.0: added Stage 3 code-execution evidence rule (qa-agent's execution_report required for any code_submission; coder-agent's self_test_report is not sufficient) and an explicit note that this skill is the cluster's sole decision-producing mechanism."
  - "2.0.0: added a measurable deviation method (Stage 1 was previously unquantifiable), a 2-cycle reject ceiling, a default conflict-resolution policy, and explicit auto-pass/warn thresholds"
---

# Final Audit — 5 Stages

## Authority note
This skill is how `orchestrator-agent` exercises the decision authority defined
in `/shared/agent-registry.md`'s Authority Boundary. No other agent's own
report — a `verification_report`, an `execution_report`, a `self_test_report`,
or any agent saying "done"/"PASS"/"ready" — is itself a decision. Those are
evidence. Running this skill against that evidence is what produces the actual
decision. If I ever catch myself forwarding an agent's self-declared "PASS"
straight to the user or to `@distribution-agent` without running this skill,
that's a protocol violation, not a shortcut.

## Rule: All 5 Stages Must Be Examined, and Every Verdict Must Be Reproducible

No compressing to one line. No skipping. Each stage gets explicit examination with a stated basis for its verdict — "PASS" or "WARN" with no supporting note is itself an audit failure.

## Stage 1: Intent Alignment

| Check | Question |
|-------|----------|
| Core Intent | Did we answer exactly what the user asked? |
| Implicit Intentions | Are there implicit questions unanswered? |
| Deviation | Did output deviate to tangential topics? |
| Unrequested Addition | Did we add unnecessary information? |

### Measuring "deviation" (previously unquantifiable — fixed here)
Deviation is not eyeballed. Compute it as:
1. Break the original request into its atomic sub-asks (e.g. "compare X and Y, then recommend one for use case Z" = 3 atomic sub-asks: describe X, describe Y, recommend for Z).
2. Break the delivered output into its content blocks (paragraphs/sections).
3. Deviation % = (content blocks that map to none of the atomic sub-asks) ÷ (total content blocks).
4. **Rule:** deviation > 30% by this count → REJECT, return to agent with the specific blocks flagged as off-target. Deviation 10–30% → WARN, note which blocks are tangential and let the user decide if they're useful context or noise. Under 10% → no flag.
This method is deliberately mechanical so two different audit passes on the same output produce the same verdict.

## Stage 2: Completeness

| Check | Description |
|-------|-------------|
| Aspect Coverage | All parts of question answered? Cross-check against the same atomic sub-ask list from Stage 1 — every sub-ask needs at least one content block addressing it. |
| Appropriate Depth | Depth matches the complexity tier assigned by `model-router`? A 🟠 Deep task answered at 🟢 Light depth is a completeness failure even if every sub-ask is technically touched. |
| Missing Data | Gaps flagged explicitly? |
| Missing Context | User needs more context than was given? |

**Rule:** Acceptable gaps must be stated explicitly in the output itself (e.g. "data for region X was unavailable as of [date]"). A gap the audit catches that the output did NOT already disclose is an automatic REJECT, regardless of how minor — silent gaps are a completeness failure by definition, not a matter of degree.

## Stage 3: Source Integrity

| Check | Tool |
|-------|------|
| Source Presence | Every factual claim traceable to a specific source in the research context? |
| Link Validity | Sources accessible (not 404, not paywalled without notice)? |
| Source Diversity | Single source only for a claim that reasonably has multiple independent sources? |
| Conflict Resolution | Unresolved conflicts between sources? |

### Default Conflict Resolution Policy (previously undefined — fixed here)
When two credible sources disagree on a fact:
1. Check recency — if one source is materially more recent and the fact is time-sensitive, prefer it, but still name the discrepancy in the output ("as of [date], X; an earlier report said Y").
2. If recency doesn't resolve it (both current, still disagree), do NOT pick one silently. The output must present both figures with attribution and let the reader see the disagreement — smoothing a live conflict into a single confident number is a Stage 3 automatic REJECT.
3. If the conflict is material to the user's decision (e.g. affects a recommendation), flag it as `[disputed]` and surface it in the final summary shown to the user, not buried in a footnote.

**Rule:** Unsupported claims marked `[unverified]`. Any claim presented as fact with zero traceable source is an automatic REJECT, not a warning.

### Code-Execution Evidence (for any `code_submission`)
"Source" for a code artifact means an independently-executed, reproducible test
run — not a static read-through, and not `coder-agent`'s own `self_test_report`.
- **Automatic REJECT** if a `code_submission` reaches this stage without a
  `qa-agent`-produced `execution_report` from an isolated sandbox run.
- **Automatic REJECT** if `execution_report.exit_code` is non-zero, or if any
  test failed on its final run (after the single permitted re-run for flake
  detection — see `/shared/agent-registry.md`'s `@qa-agent` card).
- `flaky_detected: true` is a **WARN**, not a silent PASS — it must be surfaced
  to the user and routed back to `coder-agent` for a root-cause fix, not waved
  through because "it passed eventually."
- Missing `environment_manifest` on the original `code_submission` should have
  already caused `qa-agent` to reject before this stage — if it somehow arrives
  here anyway, treat it the same as a missing source: automatic REJECT.

## Stage 4: Bias Detection

| Bias Type | Indicator |
|-----------|-----------|
| Recency | Only recent events cited when historical baseline matters? |
| Survivorship | Only successes analyzed, failures/non-events excluded? |
| Anchoring | First source or first idea disproportionately drives the conclusion? |
| Attribution | Single channel/source credited for a multi-causal outcome? |
| Homogeneous Audience | Segments/geographies/demographics ignored that materially change the answer? |
| Short-termism | Long-term consequences sacrificed for a short-term framing? |

**Rule:** Flag material biases explicitly in the audit summary shown to the user. "Material" = would plausibly change the user's decision or understanding if corrected. Cosmetic imbalance (e.g. slightly more Western sources on a globally-relevant but not region-specific topic) is noted but does not by itself trigger REJECT — use judgment, but state the judgment, don't just tick the box.

## Stage 5: Output Quality

| Check | Standard |
|-------|----------|
| Structure | Organized (headings, tables, lists) appropriately for the content — not over-structured for a short conversational answer, nor under-structured for a long reference document |
| Language | Matches user's language and register |
| Conciseness | No filler or repetition |
| Actionability | Usable directly without further editing for its stated purpose |
| Formatting | Files/links render correctly; no broken markdown, no dangling references |

## Gate Decision

| Decision | When |
|----------|------|
| ✅ PASS | All 5 stages pass with no flags |
| ⚠️ PASS WITH WARNINGS | No stage triggers an automatic REJECT condition (see each stage's explicit REJECT rules above), but one or more non-automatic issues are flagged (e.g. Stage 4 material bias, Stage 1 deviation 10–30%) |
| 🔄 REJECT | Any stage's explicit automatic-REJECT condition is met: Stage 1 deviation >30%, Stage 2 undisclosed gap, Stage 3 unsourced factual claim or silently-resolved live conflict |

**PASS WITH WARNINGS is not a silent pass** — every warning must appear in the final result shown to the user (per SOUL.md's rule against compressing warnings out of the response). It also means any downstream archiving via `@archivist-agent` carries the same `[unverified]`/`[disputed]` tags this audit assigned — the verdict recorded here is the one that travels forward into the second brain, never re-adjudicated or softened later.

## Escalation Ceiling
Maximum 2 REJECT → return-to-agent cycles for the **same stage and same underlying reason**. If the 3rd attempt on that specific issue still fails, stop looping: report to the user exactly what was tried, why it kept failing, and ask whether to accept the result with the flaw explicitly noted, change agent, or change scope. This mirrors the ceiling defined in SOUL.md — this skill is the source of truth for *how* it's measured; SOUL.md is the source of truth for *when it's invoked* in the pipeline.

## Audit Log
```
hermes memory write --profile orchestrator-agent --key "audit_<task_id>" --value '{
  "task_id": "<task_id>",
  "stage_1_intent": {"verdict": "PASS|WARN|REJECT", "deviation_pct": <float>, "notes": "..."},
  "stage_2_completeness": {"verdict": "...", "undisclosed_gaps": [...]},
  "stage_3_sources": {"verdict": "...", "unsourced_claims": [...], "unresolved_conflicts": [...]},
  "stage_4_bias": {"verdict": "...", "material_biases": [...]},
  "stage_5_quality": {"verdict": "..."},
  "overall_decision": "PASS|PASS_WITH_WARNINGS|REJECT",
  "reject_cycle_count": <int>
}'
```

## Example

| Stage | Result | Notes |
|-------|--------|-------|
| 1. Intent Alignment | ✅ PASS | Deviation 4% (1 of 24 content blocks tangential — a brief historical aside) |
| 2. Completeness | ⚠️ WARN | Output disclosed missing APAC pricing data explicitly — acceptable per policy |
| 3. Source Integrity | ✅ PASS | All claims traceable; one recency-based conflict resolved and disclosed |
| 4. Bias Detection | ⚠️ WARN | Sources skew Western; flagged as material since the question was framed globally |
| 5. Output Quality | ✅ PASS | |

**Decision:** PASS WITH WARNINGS — both warnings surfaced in the final response to the user.
