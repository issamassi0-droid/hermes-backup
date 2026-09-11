#!/usr/bin/env python3
"""
Architect Heartbeat — Cabinet-Office System
Detects architect stalls and triggers degraded mode.
"""
import json
import pathlib
import time
from datetime import datetime, timezone


SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
LEDGER_DIR = SYSTEM_ROOT / "ledger"
HEARTBEAT_FILE = LEDGER_DIR / "architect-heartbeat.json"
LOG_FILE = LEDGER_DIR / "architect-heartbeat.log"


class ArchitectHeartbeat:
    def __init__(self):
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)
        self.heartbeat = {}

    def beat(self, status: str = "active"):
        """Record heartbeat"""
        hb = {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epoch": time.time()
        }
        self.heartbeat = hb
        self._save(hb)
        self._log(hb)
        return hb

    def check(self) -> dict:
        """Check architect health"""
        if not self.heartbeat:
            return {"status": "no_data"}

        last_beat = self.heartbeat.get("epoch", 0)
        delta = time.time() - last_beat
        delta_min = delta / 60

        status = "healthy"
        if delta > 300:
            status = "stalled"
        elif delta > 60:
            status = "delayed"

        return {
            "status": status,
            "delta_minutes": round(delta_min, 1),
            "last_beat": self.heartbeat.get("timestamp")
        }

    def degrade(self) -> dict:
        """Activate degraded mode"""
        return {
            "mode": "DEGRADED",
            "actions": [
                "skip_non_critical_agents",
                "use_cached_results",
                "reduce_verification_depth"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _save(self, hb: dict):
        HEARTBEAT_FILE.write_text(json.dumps(hb, indent=2))

    def _log(self, hb: dict):
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(hb) + "\n")


if __name__ == "__main__":
    ah = ArchitectHeartbeat()
    ah.beat("active")
    check = ah.check()
    print(f"✓ Heartbeat: status={check['status']}, delta={check['delta_minutes']}min")
    degraded = ah.degrade()
    print(f"✓ Degraded mode: {len(degraded['actions'])} actions")
