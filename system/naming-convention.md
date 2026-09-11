---
title: Naming Convention — Cabinet-Office Multi-Agent System
type: contract
language: english
version: "1.0"
date: 2026-09-11
---

# Naming Convention Contract

> Defines the three-layer naming system for all agents in the Cabinet-Office framework.

---

## 1. Three-Layer Model

Every agent has **three names** serving different audiences:

| Layer | Purpose | Audience | Example |
|---|---|---|---|
| **Technical** | File names, code, APIs, documentation | Engineers, systems | `orchestrator-agent` |
| **Functional** | Reports, dashboards, CLI, architecture diagrams | Technical managers, architects | `Orchestrator` |
| **Display** | User chat, help text, guides | End users | `المُنسّق` |

---

## 2. Naming Rules

### 2.1 Technical Names

| Rule | Example |
|---|---|
| Lowercase, hyphen-separated | `research-agent-multi` |
| Format: `[role]-agent` or `[role]-factory` | `strategy-agent` |
| Must be unique | No two agents share the same technical name |
| Used in: file names, registry keys, API endpoints, CLI flags | `--agent research-agent-multi` |
| Maximum 40 characters | — |

### 2.2 Functional Names

| Rule | Example |
|---|---|
| Title case, single word preferred | `Strategist` |
| May use two words if needed | `Agent Factory` |
| Used in: reports, dashboards, documentation headers | `Researcher` |
| Maximum 30 characters | — |

### 2.3 Display Names

| Rule | Example |
|---|---|
| Arabic for Arabic users | `المُنسّق` |
| English fallback | `Orchestrator` |
| User-friendly, non-technical | `الباحث` (not `research-agent-multi`) |
| Used in: chat, help text, guides | — |

---

## 3. Agent Name Registry

| Handle | Technical | Functional | Display (Ar) |
|---|---|---|---|
| @architect | `orchestrator-agent` | Orchestrator | المُنسّق |
| @omni-researcher | `research-agent-multi` | Multi-Source Researcher | الباحث |
| @deep-dive | `research-agent-youtube` | YouTube Researcher | باحث يوتيوب |
| @strategist | `strategy-agent` | Strategist | الاستراتيجي |
| @draft-writer | `drafting-agent` | Drafter | الكاتب |
| @editor-qa | `qa-agent` | QA Auditor | المدقق |
| @publisher | `distribution-agent` | Distributor | الناشر |
| @analytics | `analytics-agent` | Analyst | المحلّل |
| @bot-maker | `agent-factory` | Agent Factory | صانع الوكلاء |
| @omarchy | `system-operator` | System Operator | مشغّل النظام |
| @scout | `source-monitor` | Source Monitor | الراصد |

---

## 4. Where Each Name Is Used

### 4.1 Technical Name (`orchestrator-agent`)

- File names: `orchestrator-agent.py`, `orchestrator-agent-config.json`
- Registry keys: `agents["orchestrator-agent"]`
- CLI flags: `--agent orchestrator-agent`
- API endpoints: `/api/v1/agents/orchestrator-agent/status`
- Environment variables: `CABINET_OFFICE_ORCHESTRATOR_AGENT_ENABLED=true`

### 4.2 Functional Name (`Orchestrator`)

- Architecture diagrams
- System reports
- CLI help text: `cabinet-office.py run --help`
- Dashboard headers
- Documentation section titles

### 4.3 Display Name (`المُنسّق`)

- Chat responses: "سيرسل المُنسّق المهمة للباحث..."
- User guides
- Help messages
- Error messages shown to users

---

## 5. Migration Guide

### 5.1 Registry.json

```json
{
 "name": "orchestrator-agent",
 "functional_name": "Orchestrator",
 "display_name": "المُنسّق",
 "handle": "@architect"
}
```

### 5.2 SOUL.md

Each SOUL.md must include:

```markdown
## Names

- **Technical:** `orchestrator-agent`
- **Functional:** Orchestrator
- **Display:** المُنسّق
```

### 5.3 File Naming (Optional)

Profile directories may use either:
- Handle: `profiles/architect/` (current, unchanged)
- Technical: `profiles/orchestrator-agent/` (future migration)

---

## 6. Rationale

### Why three names?

| Problem | Solution |
|---|---|
| `@architect` is unclear in technical docs | `orchestrator-agent` is self-documenting |
| `orchestrator-agent` is too technical for users | `المُنسّق` is intuitive |
| Single name forces compromise | Three names serve each audience perfectly |

### Why not just two?

| Approach | Problem |
|---|---|
| Technical only | Users confused |
| Functional only | Engineers lose precision |
| Display only | Developers lose clarity |
| **Three names** | ✅ Each audience gets optimal name |

---

> [!INFO]
> **Version:** 1.0 | **Date:** 2026-09-11
> **Status:** Active — applies to all agents in registry.json
