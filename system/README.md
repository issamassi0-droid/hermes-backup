# The Cabinet-Office System Layer

Shared contracts that turn ten independent agents into one system.

**Location:** `/home/massi/.hermes/system/`
**Owner:** no single agent — amended by protocol (see `evolution.md`)
**Version:** 1.0.0
**Created:** 2026-09-11 by `@deep-dive`, at the user's explicit direction to *"fill the gaps and make it an integrated, maximally interactive system that guarantees information quality and is ready to evolve."*

---

## Why this exists

Before 2026-09-11, the ten agents in this install each had a rich SOUL.md. But nothing tied them together:

- No shared registry of who exists and what they can do
- No protocol for what a message between them should contain
- No persistent ledger so state survives a handoff
- No external routing rules — tiering lived only inside `architect/SOUL.md`
- No shared evidence rubric — each SOUL promised its own "Labeled Truth"
- No mechanism for the system to improve its own SOULs
- No single command to boot or restore the whole thing

The `system/` directory closes every one of those gaps.

---

## What's in here

| File | Purpose |
|---|---|
| `registry.json` | Master inventory of all 10 agents: role, , tiers, upstream/downstream, who can DM whom, and the pipeline definition per tier. **Single source of truth.** |
| `protocol.md` | The inter-agent envelope + payload types + reply semantics + message budget. Defines *how* agents talk via `message_agent`. |
| `ledger-schema.json` | Schema for the per-mission task ledger. Every stage writes one file; the Architect writes the ticket and the coverage matrix. |
| `routing.yaml` | External, versionable tiering rules: 4 tiers, escalation signals, stakes floors, latent-need checks, model selection, budget enforcement, compression contracts. The Architect SOUL embeds a copy of this. |
| `quality-charter.md` | System-level quality contract. 9 articles. Binding on every agent. Includes the evidence grading rubric and the blind-spot coverage requirement. |
| `evolution.md` | The self-improvement loop. Collection → analysis → 3-tier amendment protocol (auto / sign-off / user-approval). Constitutional layer is explicitly frozen. |
| `bootstrap.sh` | One-command boot, status, restore, and rollback. Zero external deps (jq optional). |
| `status.html` | Live status dashboard rendered inline in the desktop app. |
| `CHANGELOG.md` | Every system amendment, with before/after hashes. |
| `ledger/` | Per-mission task ledgers (created on demand). |
| `backups/` | Snapshot of the system layer + all SOULs before any restore. |

---

## Quick start

```bash
# Verify the system is complete
bash ~/.hermes/system/bootstrap.sh --status

# Snapshot everything before making changes
bash ~/.hermes/system/bootstrap.sh --install

# After something breaks, restore from the latest backup
bash ~/.hermes/system/bootstrap.sh --restore
```

---

## The three layers

```
┌──────────────────────────────────────────────────────┐
│ CONSTITUTIONAL (frozen — amend only by re-author) │
│ • the five Canon items │
│ • refusal lines in every Boundary │
│ • the 5 evidence labels │
├──────────────────────────────────────────────────────┤
│ SYSTEM (versioned, amendable via evolution.md) │
│ • registry.json · protocol.md · ledger-schema.json │
│ • routing.yaml · quality-charter.md · evolution.md │
├────────────────────────────────────���─────────────────┤
│ AGENT (per-profile SOUL.md — amended by bot-maker) │
│ • 10 SOULs, each with Creed/Canon/Skills/Boundary │
└──────────────────────────────────────────────────────┘
```

A change to a lower layer never overrides a higher layer. If an agent's SOUL contradicts the Quality Charter, the Charter wins.

---

## Division of authority

| Concern | Authority |
|---|---|
| Opening a mission, tiering, coverage matrix | `@architect` (sole) |
| Authoring or rewriting any SOUL | `@bot-maker` (sole) |
| Independent verification / rejection | `@editor-qa` (sole) |
| Writing to external platforms | `@publisher` (only after `@editor-qa` approval) |
| Performance feedback | `@analytics` (advisory only — never directive) |
| Amending system-layer files | see `evolution.md` § Amendment Protocol |
| Amending constitutional layer | user only |

---

## Interactivity at a glance

`message_agent` is Hermes' native DM tool. This system layer turns it into a real protocol:

- Every message follows the envelope in `protocol.md`
- Every agent knows who it can DM (see `registry.json` → `can_dm`)
- Fire-and-forget semantics are explicit (no synchronous-request thinking)
- Message budget: 12 per mission, then route through the Architect
- Escalation ladder: agent → architect → human

The result is a system where agents can actually hand work off, ask each other for clarification, request counter-evidence, and report feedback — without the usual multi-agent failure modes (fan-out, ping-pong acks, unstructured prose).

---

*Authored by `@deep-dive` under explicit user direction. To propose a change, message `@architect` with a `registry_notice` payload.*