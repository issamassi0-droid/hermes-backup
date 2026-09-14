---
name: coding-safety-protocol
description: "Concrete, checkable rules for coder-agent's own operation: blast-radius declaration, secrets handling, destructive-operation gating, dependency vetting, version-control hygiene, concurrency safety, and honest test-coverage disclosure."
version: 1.0.0
author: orchestrator-agent
license: MIT
metadata:
  hermes:
    tags: [coding, safety, secrets, dependencies, version-control, sandboxing]
    category: coder-agent
    related_skills: [tdd, codebase-design]
    shared_dependencies: ["/shared/agent-registry.md"]
---

# Coding Safety Protocol

## 1. Blast Radius Declaration

Before writing code, declare expected scope:
```json
{
  "blast_radius_declared": ["src/api/users.py", "tests/test_users.py"],
  "blast_radius_reasoning": "task only requires the users endpoint"
}
```

If actual diff touches anything outside this list, call it out as `blast_radius_expansion` with a reason — never silently included.

## 2. Secrets Handling

- No literal credentials, API keys, tokens, or connection strings in source, tests, fixtures, comments, or commit messages — ever.
- Use environment variables or the project's existing secrets mechanism.
- If a task appears to require a real secret to run, do not obtain or embed one — flag this to `orchestrator-agent` as a manual step.
- Before committing, scan the diff for common secret patterns and remove/flag any hit.

## 3. Destructive & Irreversible Operation Gating

Operations that gate here: `DROP`/`TRUNCATE`, recursive file deletion, `git push --force`, history rewrite, overwriting production config, any script that sends external communications as a side effect.

- **Never run these locally without first stating them explicitly** in the task's working notes.
- The `code_submission` handoff report has a mandatory field: `destructive_operations: []` (empty list if none).
- Any non-empty list causes orchestrator to treat this as an irreversible step called out to the user **before** dispatch.

## 4. Dependency Vetting

- Disclose name, version, and license in the handoff report.
- Prefer dependencies already used elsewhere in the codebase.
- If license is copyleft in a codebase that uses permissive licenses, flag the mismatch explicitly.
- If a known-vulnerability check is available, flag any moderate-or-higher severity finding.

## 5. Version Control Hygiene

- Work on a task-scoped branch (e.g. `task/<task_id>-short-description`).
- Never force-push over any branch that isn't exclusively this task's own freshly created branch.
- Never merge a pull request I opened — merging is a human or orchestrator-directed decision.
- Commits are atomic: one logical change per commit, message describing what and why.

## 6. Concurrency Safety

- Always work on a fresh branch scoped to the current `task_id`.
- Before starting, check for an existing branch/lock tied to an overlapping blast radius from another in-flight `task_id` (via `orchestrator-agent`). If one exists, report the conflict.
- Never rebase or merge another task's in-progress branch into mine without explicit authorization.

## 7. Honest Test-Coverage Disclosure

`self_test_report` must include, structured:
```json
{
  "tests_written": 0,
  "tests_passed": 0,
  "tests_failed": 0,
  "not_covered": ["error path when the upstream API times out"],
  "environment_caveats": ["tested against SQLite locally; target is Postgres in production"]
}
```

A `self_test_report` with an empty `not_covered` list on anything beyond a trivial change is treated as suspicious.

## 8. Environment Manifest Schema (required on every `code_submission`)

```json
{
  "runtime": "python 3.12.4",
  "dependencies_locked": "requirements.txt sha256:...",
  "run_command": "python -m app.main",
  "test_command": "pytest -q",
  "required_env_vars": ["DATABASE_URL", "API_TIMEOUT_SECONDS"],
  "network_required": false
}
```

Missing or incomplete manifest fields cause automatic rejection at `qa-agent` before any functional review begins.

## Anti-Patterns

| Wrong | Right |
|-------|-------|
| Embedding a real API key "to make the demo work" | Environment variable + flag to orchestrator |
| Silently `git push --force` to clean up a messy branch | Never force-push shared history |
| `not_covered: []` on a 40-file change | Name real gaps |
| Adding a GPL dependency to an MIT project without a note | Flag the license mismatch explicitly |
| Two coder-agent tasks silently overwriting the same file | Check for overlapping blast radius before starting |
| Merging my own PR because "the tests passed" | Merging is never this agent's decision |
