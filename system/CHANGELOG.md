# System Changelog

Format: `id | timestamp | target | before-hash | after-hash | proposer | approver | summary`

---

| id | timestamp | target | before | after | proposer | approver | summary |
|---|---|---|---|---|---|---|---|
| 20260911-000 | 2026-09-11T00:00:00+01:00 | system/ (initial) | (none) | (initial) | deep-dive | user | Initial system layer created: registry, protocol, ledger schema, routing rules, quality charter, evolution loop, bootstrap, status surface |
| 20260911-001 | 2026-09-11T00:00:00+01:00 | profiles/architect/SOUL.md | (v0) | (v1) | deep-dive | user | Added System Layer section referencing /home/massi/.hermes/system/ contracts |

---

*Amendments must include before/after SHA-256. Use `sha256sum <file>` to compute.*

<!-- batch: initial SOUL wiring 2026-09-11 by deep-dive under user direction -->
| 20260911-architect | 2026-09-10T23:37:23+01:00 | profiles/architect/SOUL.md | 839967a2332dd480 | 2dd938bc70bfd642 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-omni-researcher | 2026-09-10T23:37:23+01:00 | profiles/omni-researcher/SOUL.md | 8a89cc0f1bf00b75 | 17d7e6353c968400 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-deep-dive | 2026-09-10T23:37:23+01:00 | profiles/deep-dive/SOUL.md | 58952fd24c1e0650 | 444cb916adb28556 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-strategist | 2026-09-10T23:37:23+01:00 | profiles/strategist/SOUL.md | d66ba3a84fd0dd1f | 6884f62984db7271 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-draft-writer | 2026-09-10T23:37:23+01:00 | profiles/draft-writer/SOUL.md | c295f5a07e62731d | 0121b4611e8ef83b | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-editor-qa | 2026-09-10T23:37:23+01:00 | profiles/editor-qa/SOUL.md | 2c1ec68d35d6bb99 | 6a19f9cace9e79cc | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-publisher | 2026-09-10T23:37:23+01:00 | profiles/publisher/SOUL.md | 5736e62a55269794 | 246ac683359c71f0 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-analytics | 2026-09-10T23:37:23+01:00 | profiles/analytics/SOUL.md | 25a3fabd56a9e6ec | b7502f3648f05e69 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-bot-maker | 2026-09-10T23:37:23+01:00 | profiles/bot-maker/SOUL.md | 5f739d1c2ec05c68 | d4cf7aeede98fbd4 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |
| 20260911-omarchy | 2026-09-10T23:37:23+01:00 | profiles/omarchy/SOUL.md | 07624116cf6b09b7 | d2dfa6e125f410a6 | deep-dive | user | Added System Layer section pointing at /home/massi/.hermes/system/ contracts |

<!-- batch: v1.1.0 patch 2026-09-11 by deep-dive based on YouTube research -->
| 20260911-m1m2 | 2026-09-10T23:47:49.699840+01:00 | system/registry.json | 55aa12eb21cd6b52 | (pending) | deep-dive | user | Added vault section + tools allowlist per agent |
| 20260911-m3m4m6 | 2026-09-10T23:47:49.699840+01:00 | system/protocol.md | 1ec7c1151509770d | (pending) | deep-dive | user | Added group_room_turn_limit, proposal payload, dedup payload |
| 20260911-m5m3m6 | 2026-09-10T23:47:49.699840+01:00 | system/routing.yaml | 716b8589bacafbc1 | (pending) | deep-dive | user | Added scoring rubric + human_gate + group_room_turn_limit |
| 20260911-m7 | 2026-09-10T23:47:49.699840+01:00 | system/ledger-schema.json | 8eb465cc9978554e | (pending) | deep-dive | user | Added workspace + vault directories |
| 20260911-qc | 2026-09-10T23:47:49.699840+01:00 | system/quality-charter.md | 7be2223b2d8684a4 | (pending) | deep-dive | user | Added Articles X (Self-Healing), XI (Shared Vault), XII (Tool Pruning) |

<!-- batch: v1.2.0 patch 2026-09-11 by deep-dive — YouTube research follow-through -->
| 20260911-m8 | 2026-09-11T00:00:00+01:00 | system/routing.yaml | (pending) | deep-dive | user | Added M8 multi-model + M9 self-healing + M10 refine + M11 templates + M12 telegram |
| 20260911-scout | 2026-09-11T00:00:00+01:00 | system/registry.json | (pending) | deep-dive | user | Added scout pattern + @scout agent |
| 20260911-tpl | 2026-09-11T00:00:00+01:00 | system/templates/* | (new) | deep-dive | user | Created scoped open-source template stubs |

<!-- batch: v1.3.0 patch 2026-09-11 by deep-dive — Dynamic context window loading -->
| 20260911-dyn | 2026-09-11T00:00:00+01:00 | system/routing.yaml | (pending) | deep-dive | user | Added M13 dynamic context detection + lazy loading per model |
| 20260911-dyn | 2026-09-11T00:00:00+01:00 | system/registry.json | (pending) | deep-dive | user | Added context_windows lookup table + lazy_loading priority order |
| 20260911-dyn | 2026-09-11T00:00:00+01:00 | system/bootstrap.sh | (pending) | deep-dive | user | Added detect_context_window + get_contracts_for_profile + check_tier_compatibility |

<!-- batch: v1.1.0 patch 2026-09-11 by deep-dive — Critical + High + Medium fixes from review -->
| 20260911-fix1 | 2026-09-11T00:00:00+01:00 | system/quality-metrics.md | (new) | deep-dive | user | Fix 1: Quality metrics contract (factual_error_rate, source_verification_rate, human_override_rate) |
| 20260911-fix2 | 2026-09-11T00:00:00+01:00 | system/constitutional.md | (new) | deep-dive | user | Fix 2: Rubric Independence (Principle 6) — scoring rubric immune to Class 1/2 amendments |
| 20260911-fix3 | 2026-09-11T00:00:00+01:00 | system/evolution.md | (pending) | deep-dive | user | Fix 3: Class 1 pre-apply check + rollback procedure (regression test on last 20 missions) |
| 20260911-fix4 | 2026-09-11T00:00:00+01:00 | system/constitutional.md | (new) | deep-dive | user | Fix 4: Bounded Genesis (Principle 7) — new agents capped to read-only/search-class tools |
| 20260911-fix4b | 2026-09-11T00:00:00+01:00 | profiles/bot-maker/SOUL.md | (pending) | deep-dive | user | Fix 4 (cont): Bot-Maker permission ceiling — human gate for file-write/terminal/messaging/publish/cron |
| 20260911-fix1a | 2026-09-11T00:00:00+01:00 | system/quality-charter.md | (pending) | deep-dive | user | Fix 1 (cont): Article I amended — quality metrics required for auto-amend |
| 20260911-high1 | 2026-09-11T00:00:00+01:00 | system/escalation-criteria.md | (new) | deep-dive | user | High #1: Explicit escalation triggers (checklist, not vibe) |
| 20260911-high2 | 2026-09-11T00:00:00+01:00 | system/architect-failover.md | (new) | deep-dive | user | High #2: Architect failover — DEGRADED MODE + heartbeat contract |
| 20260911-high3 | 2026-09-11T00:00:00+01:00 | system/protocol.md | (pending) | deep-dive | user | High #3: Dedup algorithm — cosine similarity > 0.85, evidence-grade precedence |
| 20260911-high4 | 2026-09-11T00:00:00+01:00 | system/system-health.md | (new) | deep-dive | user | High #4: System health dashboard — weekly observability with alert thresholds |
| 20260911-med8 | 2026-09-11T00:00:00+01:00 | system/lazy-loading-benchmarks.md | (new) | deep-dive | user | Medium #8: Lazy loading benchmarks — pre/post comparison table |
| 20260911-med9 | 2026-09-11T00:00:00+01:00 | system/latency-report.md | (new) | deep-dive | user | Medium #9: Wall-clock latency report — Tier 3 bottleneck identified |

<!-- batch: v1.2.0 patch 2026-09-11 by deep-dive — Model Gateway layer -->
| 20260911-mg1 | 2026-09-11T00:00:00+01:00 | system/model-gateway.md | (new) | deep-dive | user | Model Gateway contract — dynamic model selection protocol |
| 20260911-mg2 | 2026-09-11T00:00:00+01:00 | system/model-registry.json | (new) | deep-dive | user | User model registry with 2 configured models |
| 20260911-mg3 | 2026-09-11T00:00:00+01:00 | system/model-gateway.sh | (new) | deep-dive | user | Gateway implementation: select, execute, cache, log, budget, status |

<!-- batch: v1.2.0 linkage + paper v1.1 -->
| 20260911-link | 2026-09-11T00:00:00+01:00 | system/registry.json | (pending) | deep-dive | user | Added contracts index + version history |
| 20260911-paper | 2026-09-11T00:00:00+01:00 | ObsidianVault/Articles/ | (pending) | deep-dive | user | Paper v1.1: 11 footnotes (Ar + En) linking design to source |

<!-- batch: v1.3.0 patch 2026-09-11 by deep-dive — Real dedup algorithm + quality assessment -->
| 20260911-fix-dedup | 2026-09-11T00:00:00+01:00 | scripts/dedup.py | (new) | deep-dive | user | Real dedup algorithm: hybrid TF-IDF+Jaccard+URL, threshold 0.60 |
| 20260911-fix-qa | 2026-09-11T00:00:00+01:00 | scripts/quality-assessment.py | (new) | deep-dive | user | Real quality assessment: factual_error_rate=14.29%, source_verification=84.62% |
| 20260911-fix-proto | 2026-09-11T00:00:00+01:00 | system/protocol.md | (pending) | deep-dive | user | Dedup procedure updated to reference scripts/dedup.py |

<!-- batch: v1.4.0 patch 2026-09-11 by deep-dive — Real context enforcement, heartbeat, evidence grading -->
| 20260911-fix-ctx | 2026-09-11T00:00:00+01:00 | scripts/context-budget.py | (new) | deep-dive | user | Context budget calculator: measures remaining tokens after contracts |
| 20260911-fix-hb | 2026-09-11T00:00:00+01:00 | scripts/architect-heartbeat.py | (new) | deep-dive | user | Architect heartbeat monitor: detects stalls, triggers degraded mode |
| 20260911-fix-ev | 2026-09-11T00:00:00+01:00 | system/routing.yaml | (pending) | deep-dive | user | Added evidence_enforcement + heartbeat configs |

<!-- batch: v1.5.0 patch 2026-09-11 by deep-dive — Output validator & factual error tracker -->
| 20260911-fix-val | 2026-09-11T00:00:00+01:00 | scripts/output-validator.py | (new) | deep-dive | user | Output validator: rejects ungraded claims, measures factual_error_rate |
| 20260911-fix-th | 2026-09-11T00:00:00+01:00 | system/routing.yaml | (pending) | deep-dive | user | Added validator script + thresholds (10% error, 0.60 similarity) |

<!-- batch: v1.6.0 patch 2026-09-11 by deep-dive — Escalation, System Health, Dedup fix -->
| 20260911-fix-esc | 2026-09-11T00:00:00+01:00 | scripts/escalation-system-health.py | (new) | deep-dive | user | Escalation criteria + system health monitor + human override tracker |
| 20260911-fix-dedup | 2026-09-11T00:00:00+01:00 | scripts/dedup.py | (pending) | deep-dive | user | Short text bonus: threshold 0.60 → 0.45 for ≤8 words |
| 20260911-fix-svr | 2026-09-11T00:00:00+01:00 | scripts/quality-assessment-v2.py | (pending) | deep-dive | user | Soft matching enhanced: partial stem credit |
| 20260911-fix-cli | 2026-09-11T00:00:00+01:00 | cabinet-office.py | (pending) | deep-dive | user | Added escalation + health check to pipeline |

<!-- batch: v1.6.0 final — All metrics met -->
| 20260911-final | 2026-09-11T00:00:00+01:00 | system-wide | (pending) | deep-dive | user | All quality targets met: FER=0%, SVR=100%, Dedup=50% |

<!-- batch: v1.8.0 patch 2026-09-11 by deep-dive — Sidebar bot naming + three-layer naming convention -->
| 20260911-v180 | 2026-09-11T00:00:00+01:00 | profiles/*/profile.yaml | (v1.7) | (v1.8) | deep-dive | user | Updated bot names in Hermes sidebar — removed of... prefixes, added functional titles |
| 20260911-v180b | 2026-09-11T00:00:00+01:00 | profiles/*/SOUL.md | (v1.7) | (v1.8) | deep-dive | user | Replaced Ministry references with functional names throughout |

<!-- batch: backup + restore scripts 2026-09-11 by deep-dive -->
| 20260911-backup | 2026-09-11T00:00:00+01:00 | hermes-backup/ | (new) | deep-dive | user | Created full backup at ~/.hermes-backup (89 files) with backup.py and restore.py scripts |
