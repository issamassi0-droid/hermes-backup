---
name: deep-web-research
description: >
  Advanced web research skill for complex, ambiguous, multi-interpretation queries
  requiring precise matching between user intent and trusted, recent sources.
  Activate for: multi-meaning entities (shared names, polysemous terms),
  comparison or deep-dive requests, controversial topics with conflicting sources,
  or any inquiry not answerable by a single direct search. Do not activate for
  simple factual queries with one clear meaning — the skill contains a complexity
  gate that routes those to a fast path automatically without extra cost.
version: 1.0.0
author: Nous Research
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Research, Web, Deep Research, Source Matching, Ambiguity Resolution]
    related_skills: []
    requires_toolsets: [web]
    requires_tools: [web_search]
---

# Deep Researcher: Decomposition, Disambiguation, and Dynamic Source Matching

## Core Philosophy

Research answer quality = **intent understanding accuracy** × **source matching accuracy**.

Most research errors stem not from weak search itself, but from:
1. Searching for the wrong question (intent misinterpretation)
2. Searching in the wrong source (question-source mismatch)

This skill addresses both causes with minimal time and token cost, via **effort scaling according to actual need** rather than a fixed template.

---

## Step Zero: Complexity Gate

Before any decomposition or analysis, ask one quick question:

> Is there more than one reasonable interpretation of this request **that would actually lead to a different search**?

- **No** (the vast majority of questions) → **Fast path**: execute direct search immediately, apply only the "Source Matching Protocol" (Section 4) briefly, and answer. Stop here. No decomposition, no questions, no probability analysis.
- **Yes or uncertain** → proceed to the "Full Path" below.

**Fast path example:** "What is the EUR/MAD exchange rate today?" — no ambiguity, no alternative interpretations, direct search.

**Full path example:** "Compare the performance of the new company and Amazon" — which new company? Performance on which dimension (financial/technical/operational)?

This gate prevents wasting time and tokens on simple questions.

---

## Full Path (When Real Ambiguity Exists)

### 1. Decomposition: From Linear Chain to Element Network

**Why not a linear chain (each element depends only on the one before it)?**
Because natural language often does not follow this pattern — an element at the end of a sentence may change the meaning of an element at the beginning (e.g., "the bank founded by Tesla's founder" — "bank" is understood only after reading "Tesla's founder," not in linear order). Therefore decomposition is a **dependency map**, not a chain.

Decompose the request into categories, and list only what actually exists (do not force every category onto every question):

| Category | Question it answers |
|---|---|
| **Entity/Entities** | Who/what specifically is the question about? |
| **Action/Request type** | Is it a fact request, comparison, causal explanation, prediction, opinion? |
| **Time constraint** | Is there an implicit or explicit time frame (now, historically, future)? |
| **Context constraint** | Field/specialty/geographic region that determines which meaning is intended |
| **Judgment criterion** (if any) | If comparison/evaluation, on what basis? |

For each category with more than one possible reading, write alternative readings **only if they would actually lead to a different search** — interpretations that do not change the search path do not deserve mention.

### 2. Qualitative Classification (No Fake Numeric Probabilities)

Instead of giving fake numbers (the language model does not have a true probability distribution over meanings), classify each interpretation into only three grades:

- **🟢 Most likely** — consistent with most signals in the question and conversational context
- **🟡 Possible** — possible but needs additional signal to be preferred
- **🔴 Excluded but mentioned** — only if the confusion is common enough to warrant warning

This classification is explicitly estimative, not calculative, and is a more honest representation and lighter processing than simulating fake probabilities.

### 3. Continuation Decision: Clarifying Questions or Inference?

Ask a clarifying question (via the question tool if available) **only if both conditions are met**:
- More than one interpretation exists at 🟢 or 🟡 close to each other
- Competing interpretations actually lead to substantially different sources/results (not just different phrasing of the same answer)

**Rules:**
- Maximum 3 questions, but start with one if it is enough to resolve the majority
- Do not ask about details inferable from previous conversation context
- If both conditions are not met: **do not ask** — proceed with the 🟢 most likely interpretation, and state your assumption in one concise sentence before or after the answer, so the user can correct it if wrong.
- **Do not repeat the question after the user responds** even if slight ambiguity remains — work with the best available interpretation, as excessive prolongation harms more than it helps.

---

## 4. Source Matching Protocol (Dynamic by Question Nature)

This part is applied **always** (in both fast and full paths), but with varying depth. Matching is not random — every question has a "signature" that determines the required source type:

| Question signature | Source requirement | Freshness criterion |
|---|---|---|
| Number/current state (price, position, legal status) | Official/primary direct source | Real-time — do not accept results older than days |
| News event | 2-3 independent sources for cross-checking | Hours to days |
| Controversial/multi-opinion topic | Deliberately fetch sources from different angles, not one source | Moderate, but diversity matters more than freshness |
| Stable/historical concept | One trusted source is usually sufficient | No time constraint |
| Technical/scientific data | Primary source (research paper, official documentation), not aggregator | Depends on field evolution speed |

**Source conflict rule:** If trusted sources conflict, **do not silently favor one** — explicitly state the conflict to the user with each position and its source, and let them weigh the matter.

---

## 5. Feedback Loop

After the first search round, ask yourself: **Does what I found confirm the 🟢 interpretation or contradict it?**

- If initial results clearly contradict it → reopen the list, elevate the marginalized 🟡 interpretation, and search again from a different angle. Do not stubbornly cling to the first interpretation.
- If results are ambiguous/conflicting without clear reason → expand search with alternative terms before concluding.
- If results confirm the interpretation → proceed to formulation directly, no need for extra search "for over-verification."

---

## 6. Stop Criteria (Cost Control)

Stop searching and decomposing when:
- Every part of the answer is attributed to a verified source, or
- Reasonable search angles are exhausted without a clearer result (in this case, tell the user the limits of what was found instead of continuing forever), or
- You reach 6-8 search operations for one question without progress — this indicates the decomposition itself may be wrong, so return to Step 1 instead of repeating the same search with different phrasing.

---

## Decision Flow Summary

```
User Question
      │
      ▼
[Complexity Gate] ── Single clear interpretation ──► Direct search + brief source match ──► Answer
      │
   Real ambiguity
      │
      ▼
[Network decomposition: entity/action/time/context/criterion]
      │
      ▼
[Qualitative classification: 🟢/🟡/🔴]
      │
      ▼
Close interpretations with divergent results? ──Yes──► Clarifying question (≤3, usually 1)
      │ No                                             │
      ▼                                                ▼
Proceed with 🟢 interpretation + state assumption     Proceed with user's answer
      │                                                │
      └──────────────────┬─────────────────────────────┘
                          ▼
              [Source matching by question signature]
                          ▼
                  Search + cross-verification
                          ▼
        [Feedback loop: confirm or contradict?]
              │                    │
          Contradict              Confirm
              │                    │
        Revise interpretation   Formulate answer
        and search from new         │
        angle                       ▼
              └──────────► [Stop criteria] ──► Final answer + note any source conflict
```

## Procedure

1. Receive the user query.
2. Apply the Complexity Gate (`scripts/router.py:is_trivial`).
3. If fast path: execute direct search and answer.
4. If full path: decompose, classify, and decide on clarifying questions.
5. Apply the appropriate specialized skill (`scripts/contested_topics.py`, etc.).
6. Execute searches, cross-verify, and apply the feedback loop.
7. Formulate the final answer, noting any source conflicts or assumptions.

## Pitfalls

- **Over-decomposition:** Do not decompose simple queries. The gate prevents this.
- **Over-questioning:** Maximum 3 clarifying questions, usually 1.
- **Silent source conflict:** Always surface conflicting sources explicitly.
- **Token waste:** Do not load reference files unless the specialized skill is activated.

## Verification

- The router correctly routes simple queries to the fast path.
- Clarifying questions are capped at 3.
- Source matching rules are applied per the signature table.
- Reference files are loaded only when the specialized skill is invoked.
