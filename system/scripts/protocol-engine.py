#!/usr/bin/env python3
"""
Protocol Engine — Cabinet-Office System
Envelope wrapping, budget enforcement, escalation validation.
"""
import json
import pathlib
import re


MISSION_ID_FORMAT = re.compile(r'^\d{8}_[a-z0-9]{12}$')

VALID_PAYLOAD_TYPES = [
    "handoff",
    "blocker",
    "revision_request",
    "clarification_request",
    "video_request",
    "hypothesis_update",
    "escalation",
    "registry_notice",
    "proposal",
    "dedup",
]

MAX_MESSAGES_PER_MISSION = 12
MAX_GROUP_ROOM_TURNS = 8


class ProtocolEngine:
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.message_count = 0
        self.escalation_count = 0

    def wrap(self, sender: str, recipient: str, stage: str, urgency: str, payload: dict) -> str:
        """Wrap message in envelope"""
        self.message_count += 1

        header = f"""[MISSION:{self.mission_id}]
[FROM:{sender}]
[TO:{recipient}]
[STAGE:{stage}]
[URGENCY:{urgency}]
---PAYLOAD---
{json.dumps(payload, indent=2)}
---END---"""

        return header

    def validate(self, message: str) -> dict:
        """Validate message format"""
        errors = []

        if not message.startswith("[MISSION:"):
            errors.append("Missing MISSION header")

        if "[FROM:" not in message:
            errors.append("Missing FROM header")

        if "[TO:" not in message:
            errors.append("Missing TO header")

        if "---PAYLOAD---" not in message:
            errors.append("Missing PAYLOAD delimiter")

        if "---END---" not in message:
            errors.append("Missing END delimiter")

        return {"valid": len(errors) == 0, "errors": errors}

    def check_budget(self) -> dict:
        """Check message budget"""
        remaining = MAX_MESSAGES_PER_MISSION - self.message_count
        return {
            "used": self.message_count,
            "remaining": remaining,
            "exhausted": remaining <= 0
        }

    def can_escalate(self) -> bool:
        """Check if escalation is allowed"""
        return self.escalation_count < 3


if __name__ == "__main__":
    engine = ProtocolEngine("20260911_abc123def456")
    msg = engine.wrap(
        sender="orchestrator-agent",
        recipient="research-agent-multi",
        stage="research",
        urgency="normal",
        payload={"type": "handoff", "data": "test"}
    )
    result = engine.validate(msg)
    print(f"✓ Protocol Engine: valid={result['valid']}, messages={engine.message_count}")
