---
name: knowledge-archiving-protocol
description: "Concrete schemas and mechanics for archivist-agent's operation: vault structure, note frontmatter, dedup/supersession rules, archiving-worthiness criteria, and retrieval mechanics. This is archivist-agent's operating protocol, distinct from raw obsidian-cli usage."
version: 1.0.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, knowledge-management, archiving, retrieval, second-brain]
    category: archivist-agent
    related_skills: [obsidian-cli]
    shared_dependencies: ["/shared/agent-registry.md"]
---

# Knowledge Archiving Protocol

## Vault Structure

```
vault/
├── Permanent/          ← one atomic conclusion per note (the topical axis)
├── Daily/               ← one note per calendar day, linking everything
│                          archived that day (the temporal axis)
├── Tasks/               ← one note per task_id with reusable output,
│                          linking to the Permanent notes it produced
├── MOCs/                ← Maps of Content — topical index notes for browsing,
│                          never storage themselves
└── _index.md            ← top-level entry point linking all MOCs
```

- **Topical axis:** `Permanent/` notes + tags + MOCs. Answers "what do we know
  about X?"
- **Temporal axis:** `Daily/` and `Tasks/` notes. Answers "what did we learn/do
  on [date]" or "what came out of task [task_id]?"
- Every Permanent note is linked from at least one Daily note (when it was
  created/updated) and ideally one MOC (where it belongs topically). A note
  with neither is effectively lost — treat this as a defect to fix immediately,
  not a later cleanup task.

## Mandatory Frontmatter (every Permanent note)

```yaml
---
title: "Short descriptive title"
task_id_source: "20260914-143200-a1b2"      # originating task
verification_status: "verified"              # verified | unverified | disputed
sources:
  - "https://example.com/article (2026-08-01)"
created: 2026-09-14
last_updated: 2026-09-14
superseded_by: null                          # or [[Newer Note]]
supersedes: null                             # or [[Older Note]]
tags: [topic-a, topic-b]
---
```

- `verification_status` must exactly mirror what `final-audit` assigned — never
  upgraded to `verified` during archiving, no matter how confident the writing
  sounds.
- `disputed` notes additionally carry a `disputed_with: [[Other Note]]` field
  pointing to the conflicting note, so both sides of a disagreement are
  discoverable from either one.

## Note Body Convention for Non-Verified Status

A `[disputed]` or `[unverified]` note states its own uncertainty in its first
paragraph, not just in frontmatter a casual reader might skip:
> **Disputed.** Source A (2026-08-01) states X. Source B (2026-07-15) states Y.
> Not resolved as of [date] — see [[Other Note]] for the competing account.

A confidently-worded note body with an `[unverified]` frontmatter tag buried
above it is a protocol violation — the uncertainty must be legible in the
prose itself, since that's what gets read and reused.

## Dedup & Supersession Mechanics

Before writing any new Permanent note:
1. Full-text and tag search the vault for existing notes on the same subject.
2. **Exact/near-duplicate subject, compatible info** → update the existing
   note (`last_updated` bumped, new source appended to `sources:`), don't
   create a new one.
3. **Exact/near-duplicate subject, contradicting info, both still current** →
   do not silently pick a winner. Create/update both notes, cross-link via
   `disputed_with:`, tag both `disputed`.
4. **Same subject, but the old note's fact is now outdated** (time passed,
   situation changed) → create a new note, set the new note's `supersedes:`
   and the old note's `superseded_by:`, leave the old note's own content and
   verification status untouched (it was accurate as of when it was true).
5. **Genuinely new subject** → create fresh, link into the nearest relevant MOC.

## Archiving-Worthiness Criteria

Archive a conclusion only if at least one is true:
- It could plausibly be relevant to a *different, future* task (not just this
  one).
- It corrects, updates, or usefully extends existing vault knowledge.
- It resolves or documents a previously `[disputed]`/`[unverified]` note.

Do **not** archive:
- One-off trivial lookups with no reuse value (unit conversions, a single
  date fact already common knowledge, etc.) — these stay in orchestrator's
  operational task log only, per `system-hardening` §4's observability trail,
  not in the vault.
- Anything that failed `final-audit` outright (REJECT) — only PASS / PASS WITH
  WARNINGS conclusions are eligible, carrying whatever `[unverified]`/
  `[disputed]` tags they earned.

When genuinely unsure whether something clears this bar, archive it with a
clearly lower-confidence tag rather than silently dropping it — but a plainly
trivial, non-reusable fact should not be archived just because it's easier
than deciding.

## Retrieval Mechanics (answering a `retrieval_query`)

1. Search by keyword/topic/tag — not only exact title string matching.
2. Return every genuinely relevant note with: title, `verification_status`,
   `last_updated`, and a one-line summary of what it says.
3. Flag staleness explicitly: if a note's topic is one that changes often
   (people's roles, prices, current events) and `last_updated` is more than a
   reasonable freshness window for that topic, say so — don't present it as
   current by default.
4. If nothing relevant exists, return an explicit empty result — do not
   stretch a loosely related note into a false match to seem more useful.

## `archive_receipt` Schema (returned to orchestrator after every archiving action)

```json
{
  "action": "create | update | supersede | reject",
  "notes_touched": ["Permanent/example-note.md"],
  "moc_updated": "MOCs/relevant-topic.md",
  "daily_log_updated": "Daily/2026-09-14.md",
  "links_added": ["[[Related Note]]"],
  "verification_status": "verified | unverified | disputed",
  "reason_if_rejected": null
}
```

## Anti-Patterns

| Wrong | Right |
|---|---|
| Writing a disputed fact as confident prose because it "sounds better" | State the dispute plainly in the note's own first paragraph |
| Deleting an outdated note | Supersede it; keep the trail intact |
| Creating a new note without searching first | Always search; update or link rather than duplicate |
| Archiving every single task's output "to be thorough" | Apply the worthiness criteria; skip non-reusable trivia |
| Returning "no relevant notes" without a broad tag/content search | Search topically, not just by exact title |
| Presenting an old note on a fast-changing topic as current | Flag staleness explicitly in the retrieval result |
