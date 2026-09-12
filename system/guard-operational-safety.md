# Guard: Operational Safety

System-wide guardrails that the agent and the desktop app MUST follow to prevent
recurrence of known corruption and process-destruction incidents.

---

## 1. Venv Integrity — Never Corrupt or Half-Rebuild

### Incident
All 2054 `.py` files in `~/hermes-agent/venv/` had their indentation collapsed to
one space, breaking the entire Hermes install.

### Rule
- The venv is built at `~/hermes-agent/venv/` with:
  - `uv venv venv --python 3.11`
  - `UV_PROJECT_ENVIRONMENT=venv uv sync --extra all --locked`
- NEVER hand-edit any file inside `venv/`.
- NEVER reformat, prettify, or re-indent any `.py` file under `venv/` — this is what
  produced the one-space indentation collapse.
- If `venv/` looks corrupted, rebuild by DELETING the whole `venv/` directory and
  re-running the two commands above inside `~/hermes-agent/`. Do not attempt
  partial repair, do not run `uv sync` without `--locked` and `--extra all`.
- After rebuild, verify with `hermes --version` before taking any other action.
- Do not set `model.base_url` to a hardcoded local socket (`http://127.0.0.1:31415/v1`)
  in `~/.hermes/config.yaml` — that value changes with the model provider and only
  works for one provider. Leave `base_url` to the provider config.

## 2. Config Files — YAML Indentation Is Load-Bearing

### Incident
Every `config.yaml` `custom_providers:` block was corrupted to 1-space indent.
A list item under a key with the wrong indent is silently parsed as a *string*
instead of a nested block, so the config is accepted but providers do not resolve.

### Rule
- The `custom_providers:` block in `~/.hermes/config.yaml` and every
  `profiles/<name>/config.yaml` MUST use this exact shape:

  ```yaml
  custom_providers:
    - name: X
      model_base_url: <url>
      model_api_key_env: ENV_VAR
      models:
        - name: Y
          ...
  ```

  Two-space indent for each nesting level; four spaces inside a `-` list item.
- NEVER collapse or re-indent an existing block with an automated "fix".
- ALWAYS validate the file after editing:
  `python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <file>`
  before restarting any hermes process.
- If a template/editor rewrites a `config.yaml`, re-check the `custom_providers`
  block shape against the canonical example above.

## 3. Profile Facades Share One Database — See guard-duplicate-serve.md

`deep-dive` is a facade for `research-agent-youtube` (see `routing.yaml →
naming.mapping`). A facade shares the underlying profile's `state.db`. Spawning a
serve for a facade while the underlying profile's serve is also running means two
writers on one SQLite file → sticky `StateDbReplacedError` and a destroyed turn.

- Read `guard-duplicate-serve.md` before spawning any serve process.
- Never spawn both `<facade>` and `<underlying>` serve processes.

## 4. Profile Directories — Preserve config.yaml and state.db

### Incident
The `deep-dive` profile directory was recreated empty at deploy time: its
`config.yaml` (with corrected indentation) disappeared and `state.db` was never
initialized, so the serve process fell back to the underlying profile's store.

### Rule
- Profile config and state live in `profiles/<name>/config.yaml` and
  `profiles/<name>/state.db`.
- When the desktop app or any script provisions a profile, it MUST NOT delete or
  recreate the directory if it already exists. Merge into what is present.
- If a profile directory needs scaffolding, copy the shared base (SOUL.md, hooks,
  skills) WITHOUT touching (a) `config.yaml`, (b) `state.db`, (c) `sessions/`.
- If `state.db` is missing from a profile, initialize it with `hermes serve -p
  <name> --init` (or the documented init path) instead of routing to a facade's DB.

## 5. Recovery Order — After Any Incident

1. Fix the config file that caused the problem.
2. Rebuild the venv only if `.py` corruption is confirmed.
3. Kill ALL hermes processes (gateway + every serve), clearing sticky per-process
   state like `_db_replaced`.
4. Restart the desktop app so it respawns services from the corrected config.
5. Verify: `hermes --version`, a live session on each profile that was failing.

---

## Checklist Before Restarting Any Hermes Process

- [ ] `hermes --version` returns `Hermes Agent vX.Y.Z`
- [ ] `~/.hermes/config.yaml` parses as YAML
- [ ] every `profiles/<name>/config.yaml` parses as YAML
- [ ] every used profile has a `state.db`
- [ ] no two serve processes resolve to the same `state.db` path
- [ ] no `model.base_url` hardcoded to a loopback socket in config
- [ ] `venv/` files were not hand-edited