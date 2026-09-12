# Guard: Duplicate Serve Process Prevention

## Problem

The routing table defines facade aliases (e.g. `deep-dive → research-agent-youtube`).
When the desktop resolves a facade to its underlying profile, it opens that profile's
`state.db`. If it ALSO spawns a separate serve process for the underlying profile, two
processes write to the same SQLite database. SQLite WAL mode does not tolerate multiple
writers from separate processes — the second writer triggers `StateDbReplacedError`
("state.db was replaced underneath this process"), which is sticky per-process and
permanently disables all writes for that process lifetime.

## Rule

Before spawning `hermes serve --profile <profile>`, check `spawn-ledger.json` for any
existing serve process that already holds a writer handle to the target profile's
`state.db`.

Resolve the effective database path:
- If the profile is a facade alias (defined in `routing.yaml` under `naming.mapping`),
  the effective DB is `<underlying_profile>/state.db`, NOT `<facade_profile>/state.db`.
- If the profile is a real profile (has its own `profiles/<name>/state.db`), use that.

**Never spawn a serve process if another serve process already holds a writer fd to the
same resolved `state.db` path.**

## Resolution Table

Read from `~/.hermes/system/routing.yaml` → `naming.mapping`:

| Facade       | Underlying Profile       | Shared DB                              |
|-------------|--------------------------|----------------------------------------|
| deep-dive   | research-agent-youtube   | profiles/research-agent-youtube/state.db |
| omni-researcher | research-agent-multi | profiles/research-agent-multi/state.db |
| architect   | orchestrator-agent       | profiles/orchestrator-agent/state.db   |
| strategist  | strategy-agent           | profiles/strategy-agent/state.db       |
| draft-writer | drafting-agent          | profiles/drafting-agent/state.db       |
| editor-qa   | qa-agent                 | profiles/qa-agent/state.db             |
| publisher   | distribution-agent       | profiles/distribution-agent/state.db   |
| analytics   | analytics-agent          | profiles/analytics-agent/state.db      |
| bot-maker   | agent-factory            | profiles/agent-factory/state.db        |
| omarchy     | system-operator          | profiles/system-operator/state.db      |

## Enforcement

1. **Desktop spawn guard**: When the desktop app decides which serve processes to start,
   it must resolve each profile name through the facade table first. For each unique
   resolved DB path, spawn exactly ONE serve process. If a facade is requested but its
   underlying profile already has a serve process running, do NOT spawn a second.

2. **Orchestrator routing guard**: When the orchestrator-agent dispatches a task to a
   facade-named agent (e.g. `deep-dive`), it must route the task through the underlying
   profile's existing serve process, not spawn a new one.

3. **Spawn-ledger check**: Before any `hermes serve` launch, parse
   `~/.hermes/spawn-ledger.json` and check if any entry holds an open fd to the
   resolved `state.db` path. If yes, skip the spawn.

## Recovery

If a duplicate serve is detected (two entries in spawn-ledger.json writing to the same
state.db):

1. Identify the OLDER process (lower pid, earlier create_time).
2. Kill the older process — the desktop will respawn it if needed.
3. The surviving process retains its writer handles and continues normally.
4. Log the incident in `~/.hermes/logs/duplicate-serve-guard.log` with timestamp,
   killed pid, surviving pid, and the shared db path.
