# Architect Failover

The Architect is a single coordinator. This contract defines what happens when it fails.

---

## DEGRADED MODE

If the Architect does not emit a heartbeat within N minutes of accepting a mission, or its context window exceeds a safety threshold mid-mission:

1. **All in-flight missions pause** and are logged as `blocker`
2. **Human is notified directly** (not routed through the stalled Architect)
3. **No new missions accepted** until human resumes or backup takes over

## Heartbeat Contract

- Architect emits a `heartbeat` payload to system log every 5 minutes during active missions
- Timeout: 15 minutes (3 missed heartbeats)
- Backup: A designated secondary Architect instance may take over

## Recovery

```
stalled → DEGRADED MODE → human notified → human resumes or backup takes over → normal
```

---

## Architect Failover v1.0 — added 2026-09-11 by deep-dive (v1.1 patch, high-priority #2).