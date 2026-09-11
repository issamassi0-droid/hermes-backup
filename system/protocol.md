# Inter-Agent Protocol v1.0

The rules for how agents in the Cabinet-Office system talk to each other. Everything goes through `message_agent` — this file defines *what* to send and *when*.

---

```naming
All agent identifiers in this document use **technical names** (see naming-convention.md).
- Technical: `orchestrator-agent` (file names, APIs)
- Functional: Orchestrator (reports, diagrams)
- Display: المُنسّق (user chat)
```

## 1. The Envelope

Every inter-agent message MUST start with this header, on its own lines:

```
[MISSION:<mission_id>]
[FROM:<sender_name>]
[TO:<recipient_name>]
[STAGE:<pipeline_stage>]
[URGENCY:<low|normal|high|blocker>]
---PAYLOAD---
<structured payload — see §3>
---END---
```

No prose before the header. No prose after `---END---`. If an agent needs to add a note, it goes inside the payload as a `note` field.

---

## 2. When to Send

| Situation | Sender | Recipient | Payload type |
|---|---|---|---|
| Pipeline handoff (next stage ready) | any | next stage | `handoff` |
| Blocked — needs decision | any | `orchestrator-agent` | `blocker` |
| Factual contradiction found | `qa-agent` | `drafting-agent` | `revision_request` |
| Counter-evidence gap | `strategy-agent` | `research-agent-multi` | `clarification_request` |
| Video-heavy topic, no coverage | `research-agent-multi` | `research-agent-youtube` | `video_request` |
| Performance data ready | `analytics-agent` | `research-agent-multi`, `strategy-agent` | `hypothesis_update` |
| New agent provisioned | `agent-factory` | `orchestrator-agent` | `registry_notice` |
| Tier escalation needed | any | `orchestrator-agent` | `escalation` |

**Rule:** Message ONE clearly relevant agent. Never fan out "just in case."

---

## 3. Payload Types

### `handoff`
```json
{
 "type": "handoff",
 "mission_id": "20260911_abcd12",
 "from_stage": "research",
 "to_stage": "strategy",
 "artifact_path": "/home/massi/.hermes/system/ledger/20260911_abcd12/research.json",
 "artifact_summary": "14 sources, 3 Tier-1, credibility score 78%",
 "confidence": 0.82,
 "temporal_bounds": "Tech: <=6m",
 "next_action": "Build structural blueprint from triaged corpus."
}
```

### `blocker`
```json
{
 "type": "blocker",
 "mission_id": "20260911_abcd12",
 "blocked_at_stage": "draft",
 "reason": "Strategist brief references source S7 which is not in the dossier.",
 "options": [
 "Re-run research for S7",
 "Drop the claim from the draft",
 "Escalate to human"
 ],
 "recommendation": "Drop the claim — S7 is Tier-3 only."
}
```

### `revision_request`
```json
{
 "type": "revision_request",
 "mission_id": "20260911_abcd12",
 "cycle": 1,
 "unsupported_claims": [{"claim_id": "c12", "claim_text": "...", "why_unsupported": "No source in dossier."}],
 "overstated_claims": [],
 "off_brief_claims": [],
 "missing_counterarguments": [{"topic": "cost", "why_required": "Brief required a cost counterpoint."}],
 "max_revision_cycles": 2
}
```

### `clarification_request`
```json
{
 "type": "clarification_request",
 "mission_id": "20260911_abcd12",
 "questions": [
 "What is the source for the 40% figure?",
 "Is there any 2026 data, or is 2025 the latest?"
 ],
 "waiting_on": "omni-researcher"
}
```

### `video_request`
```json
{
 "type": "video_request",
 "mission_id": "20260911_abcd12",
 "topic": "Herdr AI agent multiplexer",
 "reason": "Topic is video-heavy; web sources thin on lived experience.",
 "target_videos": 4,
 "needed_by": "strategy"
}
```

### `hypothesis_update`
```json
{
 "type": "hypothesis_update",
 "mission_id": "20260911_abcd12",
 "cycle": 1,
 "success_criteria_met": {"criterion_1": {"met": true, "confidence": 0.9}},
 "hypothesis_updates": [
 {"hypothesis": "Angle A resonated", "status": "validated", "confidence": 0.85}
 ],
 "recommendations_for_next_cycle": ["Lead with migration-phobia angle."]
}
```

### `escalation`
```json
{
 "type": "escalation",
 "mission_id": "20260911_abcd12",
 "from_tier": 2,
 "to_tier": 3,
 "signal": "evidence_gap + strategy_conflict",
 "confidence_at_escalation": 0.55
}
```

### `registry_notice`
```json
{
 "type": "registry_notice",
 "agent_name": "fact-checker",
 "entrypoint": false,
 "tiers_served": ["2", "3"]
}
```

---

## 4. Reply Semantics

`message_agent` is **fire-and-forget**. There is no synchronous reply.

- The recipient's reply arrives later as a **background-process completion notification**.
- The recipient MUST use the same envelope, swapping `FROM`/`TO`.
- The recipient MAY stay silent if the message is a pure FYI with nothing to add (e.g. `registry_notice`).
- **Never ping-pong acknowledgements.** A `handoff` that lands correctly does not need a "got it" reply.

---

## 5. Group Room Turn Limits

Multi-agent conversations (3+ agents in a shared room) have a configurable turn limit. Default: **8 turns**. After the limit is reached, the conversation pauses and the Architect requests human direction. Prevents the classic failure mode where two agents loop forever.

Configurable via `routing.yaml → group_room_turn_limit`.

## 6. Message Budget

- A single mission may generate at most **12 inter-agent messages**.
- After 12, any further communication must go through the Architect.
- This prevents the classic multi-agent failure mode: agents talking more than they work.

---

## 6. Failure Modes to Avoid

| Anti-pattern | Why it kills the system |
|---|---|
| Forwarding the user's words verbatim | Leaks intent; recipient lacks context |
| "Just checking in" messages | Wastes budget; wakes the sender needlessly |
| Broadcasting to 3+ agents | Fan-out; no single owner |
| Embedding secrets in payload | Vault handles secrets; payloads are plaintext |
| Synchronous-request thinking | `message_agent` is async; the reply WILL arrive late |

---

## 7. Escalation Ladder

```
stage agent
 | can't resolve
 v
architect
 | can't resolve (stakes = high, novel, or irreversible)
 v
human
```

The Architect is the ONLY agent allowed to escalate to the human. Any other agent that believes human input is required MUST escalate to the Architect first.

---

*Protocol v1.0 — authored 2026-09-11 by deep-dive to fill the inter-agent communication gap.*

---

## 8. Additional Payload Types (v1.1)

### `proposal`
Sent by the Architect to the human during a `human_gate` stage. Lists items requiring approval.
```json
{
 "type": "proposal",
 "mission_id": "20260911_abcd12",
 "from_stage": "strategy",
 "proposal_count": 4,
 "proposals": [
 {
 "id": "p1",
 "title": "Build CLI tool for X",
 "why": "Frequent issue, existing solutions broken, bounded scope (500 lines).",
 "score": 78,
 "estimated_cost": "low"
 }
 ],
 "respond_with": "approve / shelve / modify"
}
```

### `dedup`
Sent between researchers and the orchestrator to eliminate duplicate findings.

**Implementation:** `scripts/dedup.py` — hybrid algorithm (0.6*TF-IDF + 0.25*Jaccard + 0.15*URL), threshold 0.60.

**Deduplication Procedure:**

1. Architect runs `dedup.py` on all findings for the mission.
2. Each finding's text is tokenized (stopwords removed, min length 3).
3. TF-IDF vectors computed across all findings; pairwise cosine similarity calculated.
4. Jaccard similarity computed on token sets as secondary signal.
5. URL similarity adds bonus for same-domain findings.
6. Combined score >= 0.60 → duplicate; higher evidence grade kept.
7. Conflicting claims (same topic, contradictory content) flagged to Editor-QA.

```json
{
 "type": "dedup",
 "mission_id": "20260911_abcd12",
 "from_stage": "research",
 "sources_total": 14,
 "sources_deduped": 9,
 "duplicates_removed": 5,
 "technique": "hybrid_tfidf_jaccard_url_v1.1"
}
```
