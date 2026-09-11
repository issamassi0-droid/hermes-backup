# Cabinet-Office Multi-Agent System v1.6.0

> Multi-agent AI system — three-layer architecture

---

## Installation

```bash
git clone https://github.com/issamassi0-droid/hermes-pipeline-dotfiles.git
cd hermes-pipeline-dotfiles

bash setup.sh --import
```

---

## Usage

```bash
# Run missions
python3 system/cabinet-office.py run "Research AI trends" --tier tier_2
python3 system/cabinet-office.py run "Analyze herdr experiences" --tier tier_3
python3 system/cabinet-office.py run "What is ling-3.0-flash?" --tier tier_1

# System
python3 system/cabinet-office.py status
python3 system/cabinet-office.py health
python3 system/cabinet-office.py quality
python3 system/cabinet-office.py budget
python3 system/cabinet-office.py heartbeat --check
```

---

## Tiers

| Tier | Use Case | Time |
|---|---|---|
| Tier 0 | Immediate decision | ~11 sec |
| Tier 1 | Fast research | ~44 sec |
| Tier 2 | Strategy + verification | ~2 min 40 sec |
| Tier 3 | Full analysis | ~5 min 20 sec |

---

## Agents (11)

| Agent | Role |
|---|---|
| @architect | Sole orchestrator |
| @omni-researcher | Comprehensive research |
| @deep-dive | YouTube research |
| @strategist | Strategy conversion |
| @draft-writer | First draft |
| @editor-qa | Independent verification |
| @publisher | Publishing |
| @analytics | Performance measurement |
| @bot-maker | Agent creation |
| @omarchy | System management |
| @scout | Source monitoring |

---

## Metrics

| Metric | Value | Target |
|---|---|---|
| factual_error_rate | 0.0% | < 5% |
| source_verification_rate | 100% | > 90% |
| human_override_rate | 2 | < 20 |

---

## License

MIT — open source, no fees.
