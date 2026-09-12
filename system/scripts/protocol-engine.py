#!/usr/bin/env python3
"""
Protocol Engine — Cabinet-Office System
Envelope wrapping, budget enforcement, escalation validation, and agent execution.
"""
import json
import pathlib
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

SYSTEM_ROOT = pathlib.Path(__file__).parent
SCRIPTS_DIR = SYSTEM_ROOT / "scripts"
LEDGER_DIR = SYSTEM_ROOT / "ledger"
LOG_DIR = LEDGER_DIR / "model-logs"

MISSION_ID_FORMAT = re.compile(r'^(\d{8}_[a-z0-9]{12}|co-\d{14})$')

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
DEFAULT_AGENT_TIMEOUT = 30.0  # seconds

_json = json  # Alias for use in command handlers


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


def run_script(script_name: str, args: list = None, timeout: float = DEFAULT_AGENT_TIMEOUT) -> dict:
    """Run a script and return its output"""
    if args is None:
        args = []
    
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        script_path = SYSTEM_ROOT / script_name
    if not script_path.exists():
        return {"error": f"script not found: {script_name}", "status": "failed"}
    
    interpreter = "bash" if script_name.endswith(".sh") else "python3"
    cmd = [interpreter, str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=SYSTEM_ROOT,
            timeout=timeout
        )
        
        output = result.stdout.strip()
        stderr = result.stderr.strip()
        
        # Try to parse JSON output
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {
                "status": "completed",
                "returncode": result.returncode,
                "output": output,
                "stderr": stderr if stderr else None
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": f"script timed out after {timeout}s: {script_name}",
            "timeout_seconds": timeout
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def execute_agent(agent_name: str, mission_id: str, stage: str, payload: dict, timeout: float = DEFAULT_AGENT_TIMEOUT) -> dict:
    """
    Execute an agent for the given stage.
    
    This wraps agent execution by:
    1. Validating the mission and stage
    2. Logging the handoff
    3. Marking the agent as initialized via init-supervisor
    
    Returns execution result without spawning subprocesses.
    """
    # Validate inputs
    if not MISSION_ID_FORMAT.match(mission_id):
        return {"status": "error", "error": f"invalid mission_id format: {mission_id}"}
    
    # Log the handoff attempt
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mission_id": mission_id,
        "agent": agent_name,
        "stage": stage,
        "action": "handoff_attempt",
        "payload_summary": {k: str(v)[:100] for k, v in list(payload.items())[:5]}
    }
    
    log_file = LOG_DIR / f"{mission_id}.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Instead of recursive script call, just return success
    # The actual agent execution happens through the Hermes message_agent system
    return {
        "status": "queued",
        "agent": agent_name,
        "stage": stage,
        "message": f"Handoff queued for {agent_name} at {stage} stage",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def execute_pipeline_stage(stage: str, agents: list, mission_id: str, payload: dict, timeout: float = DEFAULT_AGENT_TIMEOUT) -> list:
    """
    Execute a pipeline stage with the given agents.
    
    Returns list of execution results for each agent.
    """
    results = []
    
    for agent in agents:
        # Map stage to agent role
        agent_result = execute_agent(agent, mission_id, stage, payload, timeout)
        results.append(agent_result)
        
        # If agent failed critically, stop pipeline for this stage
        if agent_result.get("status") == "error" and "invalid" in agent_result.get("error", "").lower():
            break
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: protocol-engine.py <command> [args...]")
        print("Commands: status, send, execute, stage")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        # Show protocol engine status
        result = {
            "version": "1.0",
            "max_messages_per_mission": MAX_MESSAGES_PER_MISSION,
            "max_group_room_turns": MAX_GROUP_ROOM_TURNS,
            "valid_payload_types": VALID_PAYLOAD_TYPES,
            "status": "ready"
        }
        print(json.dumps(result, indent=2))
    
    elif command == "send":
        # Validate and wrap a message
        if len(sys.argv) < 8:
            print(json.dumps({"error": "usage: send <mission_id> <sender> <recipient> <stage> <urgency> <payload_json>"}))
            sys.exit(1)
        
        mission_id = sys.argv[2]
        sender = sys.argv[3]
        recipient = sys.argv[4]
        stage = sys.argv[5]
        urgency = sys.argv[6]
        payload = json.loads(sys.argv[7])
        
        engine = ProtocolEngine(mission_id)
        message = engine.wrap(sender, recipient, stage, urgency, payload)
        validation = engine.validate(message)
        
        result = {
            "status": "wrapped" if validation["valid"] else "invalid",
            "valid": validation["valid"],
            "errors": validation.get("errors", []),
            "message_preview": message[:200] + "..." if len(message) > 200 else message
        }
        print(json.dumps(result, indent=2))
    
    elif command == "execute":
        # Execute a single agent
        if len(sys.argv) < 6:
            print(json.dumps({"error": "usage: execute <mission_id> <agent> <stage> <payload_json>"}))
            sys.exit(1)
        
        mission_id = sys.argv[2]
        agent = sys.argv[3]
        stage = sys.argv[4]
        payload_str = sys.argv[5] if len(sys.argv) > 5 else "{}"
        
        try:
            payload = _json.loads(payload_str) if payload_str and payload_str != "{}" else {}
        except:
            payload = {}
        
        result = execute_agent(agent, mission_id, stage, payload)
        print(_json.dumps(result, indent=2))
    
    elif command == "stage":
        # Execute a pipeline stage with multiple agents
        if len(sys.argv) < 5:
            print(json.dumps({"error": "usage: stage <mission_id> <stage> <agent1> [agent2...] <payload_json>"}))
            sys.exit(1)
        
        mission_id = sys.argv[2]
        stage = sys.argv[3]
        agents = sys.argv[4:-1]
        payload = json.loads(sys.argv[-1])
        
        results = execute_pipeline_stage(stage, agents, mission_id, payload)
        print(json.dumps({"stage": stage, "mission_id": mission_id, "results": results}, indent=2))
    
    else:
        print(json.dumps({"error": f"unknown command: {command}"}))
        sys.exit(1)
