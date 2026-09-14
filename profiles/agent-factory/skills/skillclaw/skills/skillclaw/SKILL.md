---
name: skillclaw
description: Enable collective skill evolution for Hermes (and compatible agents) by installing and running the SkillClaw client and optional evolve server.
---

# SkillClaw Skill

**Purpose** – When a user asks to “install SkillClaw”, “enable collective skill evolution”, or “set up the SkillClaw evolve server”, invoke this skill. It provides the exact install commands for the SkillClaw client proxy and optional server, plus usage notes that mirror the repository’s README.

## When to use

- The user wants to add automatic skill evolution to Hermes, OpenClaw, Claude Code, Codex, QwenPaw, IronClaw, PicoClaw, ZeroClaw, or any OpenAI‑compatible backend.
- The user asks for a quick install on macOS/Linux or Windows.
- The user asks to start the local proxy (`skillclaw setup`) or the background evolve server (`skillclaw start --daemon`).
- The user wants to know how to point multiple agents/devices to a shared storage layer (OSS/S3/local) so skills are shared.

## Quick install (client only)

```bash
# Clone and run the installer (macOS / Linux)
git clone https://github.com/AMAP-ML/SkillClaw.git && cd SkillClaw
bash scripts/install_skillclaw.sh
# Activate the virtualenv created by the installer
source .venv/bin/activate
```

Windows (PowerShell) – manual steps because the repo currently provides only a bash installer:

```powershell
git clone https://github.com/AMAP-ML/SkillClaw.git
Set-Location SkillClaw
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

After installation run the client proxy:

```bash
skillclaw setup          # configures the local proxy (adds /v1/chat/completions endpoint)
skillclaw start --daemon # runs the proxy as a background daemon
```

## Optional evolve server (collective skill sharing)

If the user wants automatic skill evolution across sessions or a team, start the server on any machine that can access the shared storage:

```bash
# Ensure the same repository checkout is available on the server host
cd SkillClaw/evolve_server
# Pick an engine – `workflow` (LLM pipeline) or `agent` (OpenClaw workspace)
skillclaw-evolve-server --engine workflow --storage s3://my‑bucket/skillclaw  # example
# Or start as a daemon
skillclaw-evolve-server start --daemon
```

The server reads session artifacts from the configured storage, deduplicates, improves, and writes back `SKILL.md` files. All clients that share the same storage automatically receive the updated skills.

## How it works (high‑level)

1. **Client proxy** intercepts every LLM request, records the request/response and any generated artifacts.
2. **Artifacts** are stored in the chosen backend (`local`, `oss`, `s3`).
3. **Evolve server** (optional) reads those artifacts, runs either:
   - *workflow engine*: Summarize → Aggregate → Execute a new `SKILL.md`.
   - *agent engine*: Launch an OpenClaw workspace that edits the skill file directly.
4. Updated `SKILL.md` files are written back to the storage. Clients automatically import the new version on the next turn.

## Safety notes

- The client never writes to user‑owned skill directories; it only writes to the internal `~/.hermes/skills/skillclaw/` area.
- The evolve server may run arbitrary LLM‑generated code. It is meant to be run in a controlled environment (trusted storage, limited API keys). Do not expose the server directly to the internet.
- Do **not** install third‑party packages from untrusted sources while the server is running.

## References

- Repository README: https://github.com/AMAP-ML/SkillClaw
- Paper (arXiv): https://arxiv.org/abs/2604.08377
- Hermes integration page (SkillClaw `hermes` support).

## Example conversation

User: “Please set up SkillClaw so my Hermes agent can evolve skills.”

Agent response:
```
Using skillclaw to enable collective skill evolution.
Cloning the SkillClaw repo, installing the client, and starting the proxy daemon.
```
(Then run the commands shown above and confirm success.)
