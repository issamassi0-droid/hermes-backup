#!/usr/bin/env python3
"""
Agent Init Supervisor — Cabinet-Office System
Manages agent initialization, health checks, and recovery.
"""
import json
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

SYSTEM_ROOT = pathlib.Path(__file__).parent.parent
SCRIPTS_DIR = SYSTEM_ROOT / "scripts"
LEDGER_DIR = SYSTEM_ROOT / "ledger"
INIT_DIR = LEDGER_DIR / "init"
LOG_DIR = LEDGER_DIR / "model-logs"

# Ensure directories exist
for d in [INIT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class AgentInitStatus:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.status_file = INIT_DIR / f"{agent_name}.json"
        self._load()
    
    def _load(self):
        if self.status_file.exists():
            data = json.loads(self.status_file.read_text())
            self.status = data.get("status", "unknown")
            self.last_init = data.get("last_init")
            self.init_count = data.get("init_count", 0)
            self.failures = data.get("failures", [])
        else:
            self.status = "not_initialized"
            self.last_init = None
            self.init_count = 0
            self.failures = []
    
    def record_success(self):
        self.status = "healthy"
        self.last_init = datetime.now(timezone.utc).isoformat()
        self.init_count += 1
        self.failures = []  # Reset failures on success
        self._save()
    
    def record_failure(self, error: str):
        self.status = "failed"
        self.failures.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error
        })
        # Keep only last 10 failures
        self.failures = self.failures[-10:]
        self._save()
    
    def _save(self):
        data = {
            "agent": self.agent_name,
            "status": self.status,
            "last_init": self.last_init,
            "init_count": self.init_count,
            "failures": self.failures,
            "updated": datetime.now(timezone.utc).isoformat()
        }
        self.status_file.write_text(json.dumps(data, indent=2))


class InitSupervisor:
    def __init__(self):
        self.agents = []
        self.load_agent_definitions()
    
    def load_agent_definitions(self):
        """Load agent definitions from registry.json"""
        registry_file = SYSTEM_ROOT / "registry.json"
        if not registry_file.exists():
            print(json.dumps({"error": "registry.json not found"}))
            return
        
        try:
            registry = json.loads(registry_file.read_text())
            self.agents = registry.get("agents", [])
        except Exception as e:
            print(json.dumps({"error": f"failed_to_load_registry: {str(e)}"}))
    
    def check_agent_health(self, agent_name: str) -> dict:
        """Check if an agent is healthy and can be initialized"""
        status = AgentInitStatus(agent_name)
        
        # Check if agent exists in registry
        agent_def = None
        for agent in self.agents:
            if agent.get("technical_name") == agent_name:
                agent_def = agent
                break
        
        if not agent_def:
            return {
                "agent": agent_name,
                "status": "not_found",
                "error": f"agent {agent_name} not found in registry"
            }
        
        # Check last init status
        last_status = status.status
        
        return {
            "agent": agent_name,
            "status": last_status,
            "last_init": status.last_init,
            "init_count": status.init_count,
            "recent_failures": status.failures[-3:] if status.failures else [],
            "tools": agent_def.get("tools", []),
            "tiers_served": agent_def.get("tiers_served", [])
        }
    
    def initialize_agent(self, agent_name: str, mission_id: str = None, timeout: float = 30.0) -> dict:
        """
        Initialize an agent.
        
        This performs:
        1. Validation checks
        2. Health check
        3. Script execution (if any)
        4. Status update
        """
        start_time = time.time()
        
        # Check if agent exists
        agent_def = None
        for agent in self.agents:
            if agent.get("technical_name") == agent_name:
                agent_def = agent
                break
        
        if not agent_def:
            return {
                "status": "error",
                "error": f"agent {agent_name} not found in registry",
                "agent": agent_name,
                "elapsed_seconds": time.time() - start_time
            }
        
        # Check if agent is already healthy
        status = AgentInitStatus(agent_name)
        if status.status == "healthy" and status.last_init:
            # Check if last init was recent (within 5 minutes)
            if status.last_init:
                try:
                    last_time = datetime.fromisoformat(status.last_init)
                    age = (datetime.now(timezone.utc) - last_time).total_seconds()
                    if age < 300:  # 5 minutes
                        return {
                            "status": "already_initialized",
                            "agent": agent_name,
                            "last_init": status.last_init,
                            "message": "Agent is already initialized and healthy"
                        }
                except:
                    pass
        
        # Run health check script if available
        health_result = {
            "agent": agent_name,
            "tools_available": agent_def.get("tools", []),
            "entrypoint": agent_def.get("entrypoint", False),
            "tiers": agent_def.get("tiers_served", [])
        }
        
        # Try to run any initialization scripts
        init_scripts = [
            "architect-heartbeat.py",
            "context-budget.py",
        ]
        
        for script in init_scripts:
            script_path = SCRIPTS_DIR / script
            if script_path.exists():
                try:
                    result = subprocess.run(
                        ["python3", str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=SYSTEM_ROOT
                    )
                    health_result[f"script_{script}"] = {
                        "returncode": result.returncode,
                        "output": result.stdout[:200] if result.stdout else None,
                        "stderr": result.stderr[:200] if result.stderr else None
                    }
                except subprocess.TimeoutExpired:
                    health_result[f"script_{script}"] = {"error": "timeout"}
                except Exception as e:
                    health_result[f"script_{script}"] = {"error": str(e)}
        
        # Record initialization result
        elapsed = time.time() - start_time
        
        if health_result.get("script_architect-heartbeat.py", {}).get("returncode") == 0:
            status.record_success()
            return {
                "status": "initialized",
                "agent": agent_name,
                "elapsed_seconds": round(elapsed, 2),
                "health_check": health_result,
                "message": f"Agent {agent_name} initialized successfully"
            }
        else:
            # Still record as attempt, even if not fully successful
            status.record_failure("health_check_failed")
            return {
                "status": "degraded",
                "agent": agent_name,
                "elapsed_seconds": round(elapsed, 2),
                "health_check": health_result,
                "message": f"Agent {agent_name} initialized with warnings"
            }
    
    def initialize_all_agents(self, mission_id: str = None, timeout: float = 30.0) -> dict:
        """Initialize all agents in the system"""
        results = []
        total_start = time.time()
        
        for agent in self.agents:
            agent_name = agent.get("technical_name")
            if agent_name:
                result = self.initialize_agent(agent_name, mission_id, timeout)
                results.append(result)
        
        total_elapsed = time.time() - total_start
        
        healthy = sum(1 for r in results if r.get("status") in ["initialized", "already_initialized"])
        failed = sum(1 for r in results if r.get("status") == "error")
        degraded = sum(1 for r in results if r.get("status") == "degraded")
        
        return {
            "mission_id": mission_id,
            "total_agents": len(results),
            "healthy": healthy,
            "failed": failed,
            "degraded": degraded,
            "total_elapsed_seconds": round(total_elapsed, 2),
            "results": results,
            "status": "healthy" if failed == 0 else "degraded" if degraded > 0 else "error"
        }
    
    def get_init_summary(self) -> dict:
        """Get summary of all agent initialization statuses"""
        summary = {
            "total_agents": len(self.agents),
            "by_status": {},
            "agents": []
        }
        
        for agent in self.agents:
            agent_name = agent.get("technical_name")
            if agent_name:
                status = AgentInitStatus(agent_name)
                summary["by_status"][status.status] = summary["by_status"].get(status.status, 0) + 1
                summary["agents"].append({
                    "name": agent_name,
                    "status": status.status,
                    "last_init": status.last_init,
                    "init_count": status.init_count,
                    "failures": len(status.failures)
                })
        
        return summary


if __name__ == "__main__":
    supervisor = InitSupervisor()
    
    if len(sys.argv) < 2:
        print("Usage: init-supervisor.py <command> [args...]")
        print("Commands: status, init <agent>, init-all, health <agent>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        # Show initialization status summary
        summary = supervisor.get_init_summary()
        print(json.dumps(summary, indent=2))
    
    elif command == "init":
        # Initialize a specific agent
        if len(sys.argv) < 3:
            print(json.dumps({"error": "usage: init <agent_name>"}))
            sys.exit(1)
        
        agent_name = sys.argv[2]
        result = supervisor.initialize_agent(agent_name)
        print(json.dumps(result, indent=2))
    
    elif command == "init-all":
        # Initialize all agents
        mission_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = supervisor.initialize_all_agents(mission_id)
        print(json.dumps(result, indent=2))
    
    elif command == "health":
        # Check health of a specific agent
        if len(sys.argv) < 3:
            print(json.dumps({"error": "usage: health <agent_name>"}))
            sys.exit(1)
        
        agent_name = sys.argv[2]
        result = supervisor.check_agent_health(agent_name)
        print(json.dumps(result, indent=2))
    
    else:
        print(json.dumps({"error": f"unknown command: {command}"}))
        sys.exit(1)
