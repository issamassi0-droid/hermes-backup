#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           Orchestrator Agent Runtime (OAR) v1.0                            ║
║           Runtime مستقل يعمل خارج Hermes — SOUL.md + Tools + Loop        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# 1. الثوابت
# ──────────────────────────────────────────────────────────────────────────────

SOUL_PATH = Path("/home/massi/.hermes/profiles/orchestrator-agent/SOUL.md")
REGISTRY_PATH = Path("/home/massi/.hermes/shared/agent-registry.md")

MAX_CONNECTION_RETRIES = 3
AGENT_TIMEOUT_LIGHT = 120     # 🟢 2 min
AGENT_TIMEOUT_MEDIUM = 300   # 🟡 5 min
AGENT_TIMEOUT_DEEP = 900     # 🟠 15 min
BUDGET_WARNING_THRESHOLD = 0.80  # 80%


# ──────────────────────────────────────────────────────────────────────────────
# 2. أنواع البيانات
# ──────────────────────────────────────────────────────────────────────────────

class TurnPhase(str, Enum):
    IDLE = "idle"
    AWAITING_APPROVAL = "awaiting_approval"
    DISPATCHING = "dispatching"
    AWAITING_RESULTS = "awaiting_results"
    AUDITING = "auditing"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AGENT_WORKING = "agent_working"
    AGENT_RETURNED = "agent_returned"
    AUDIT_PASS = "audit_pass"
    AUDIT_REJECT = "audit_reject"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    task_id: str
    agent_name: str
    instructions: str
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None


@dataclass
class TaskPlan:
    task_id: str
    user_request: str
    thinking: str = ""                    # 🟢 🟡 🟠
    cost_tier: str = ""                   # 💰 💰💰 💰💰💰
    agents: List[str] = field(default_factory=list)
    topology: str = ""                    # single / sequential / parallel
    estimated_tokens: int = 0
    commitment: str = ""                  # confirmed / accepted / probable / persuasive
    irreversible_step: Optional[str] = None
    justification: str = ""
    phase: TurnPhase = TurnPhase.IDLE
    agent_tasks: Dict[str, AgentTask] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ──────────────────────────────────────────────────────────────────────────────
# 3. سجل الوكلاء
# ──────────────────────────────────────────────────────────────────────────────

class AgentRegistry:
    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.path = registry_path
        self.agents: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self):
        if not self.path.is_file():
            print(f"⚠️ Registry not found: {self.path}")
            return
        text = self.path.read_text(encoding="utf-8")
        current = None
        # استخراج أسماء الوكلاء باستخدام regex
        for line in text.splitlines():
            # ## @agent-name — Description أو ## @agent-name - Description
            agent_match = re.match(r'^##\s+`?@([a-zA-Z0-9_-]+)`?\s*[—-]?\s*(.*)', line)
            if agent_match:
                name = agent_match.group(1)
                if name and name != "orchestrator-agent":
                    current = name
                    self.agents[current] = {"role": "", "inputs": "", "outputs": "", "tools": ""}
            elif current and "|" in line and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    key = parts[1].lower().replace(" ", "_").replace("*", "")
                    val = parts[2]
                    if "role" in key:
                        self.agents[current]["role"] = val
                    elif "input" in key:
                        self.agents[current]["inputs"] = val
                    elif "output" in key or "produces" in key:
                        self.agents[current]["outputs"] = val
                    elif "tool" in key:
                        self.agents[current]["tools"] = val

    def get_agents_for_task(self, task_description: str) -> List[str]:
        """البحث عن الوكلاء المناسبين حسب Role — يطابق الكلمات المفتاحية مع نص الـ role"""
        # كل  role يُطابق ضد النص الفعلي في agent-registry.md
        role_keywords = {
            "research-agent-multi": ["بحث", "معلومات", "sources", "web", "academic", "deep-web"],
            "research-agent-youtube": ["يوتيوب", "youtube", "فيديو", "video", "transcript"],
            "strategy-agent": ["استراتيجية", "strategy", "plan", "approach", "argument structure", "triage"],
            "drafting-agent": ["كتابة", "مقال", "article", "write", "draft", "text", "reports", "messages", "رسالة", "تقرير", "humanizer", "produce text"],
            "coder-agent": ["كود", "code", "programming", "git", "script", "python", "javascript", "برنامج", "تطبيق", "bug fix"],
            "qa-agent": ["تدقيق", "review", "audit", "اختبار", "test", "quality", "verification"],
            "marketing-strategist-agent": ["تسويق", "marketing", "campaign", "promotion", "seo"],
            "analytics-agent": ["تحليل", "analytics", "data", "statistics", "إحصاء", "spreadsheet"],
            "distribution-agent": ["نشر", "publish", "distribution", "send", "package"],
            "archivist-agent": ["أرشفة", "archive", "حفظ", "obsidian", "knowledge", "vault"],
        }
        desc_lower = task_description.lower()
        results = []
        for name, kws in role_keywords.items():
            if any(kw.lower() in desc_lower for kw in kws):
                if name in self.agents:
                    results.append(name)
        return results

    def __repr__(self):
        return f"AgentRegistry({len(self.agents)} agents)"


# ──────────────────────────────────────────────────────────────────────────────
# 4. المدقق
# ──────────────────────────────────────────────────────────────────────────────

class OrchestratorValidator:
    """يتحقق من أن المنسق لم يُجب مباشرة"""

    SUSPICIOUS_PATTERNS = [
        r"^إليك\s+(الإجابة|الجواب|الحل)",
        r"^الإجابة\s+(هي|على)",
        r"^إليك\s+تحليلي",
        r"^بناءً\s+على\s+معرفتي",
        r"^سأشرح\s+لك",
        r"^دعني\s+أوضح",
    ]

    def validate_recommendation(self, text: str) -> Tuple[bool, List[str]]:
        errors = []
        has_recommendation = "Recommendation:" in text or "Recommendation:" in text
        has_task_id = "Task ID:" in text
        has_agent_line = "Agent(s):" in text
        has_proceed = "Proceed?" in text or "Proceed? (yes / no)" in text

        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                errors.append(f"محاولة إجابة مباشرة: {pattern}")

        if not has_recommendation:
            errors.append("لا يوجد كتلة Recommendation:")
        if not has_task_id:
            errors.append("لا يوجد Task ID")
        if not has_agent_line:
            errors.append("لا يوجد Agent(s)")
        if not has_proceed:
            errors.append("لا يوجد Proceed?")

        return len(errors) == 0, errors

    def validate_yes(self, text: str) -> bool:
        normalized = text.strip().lower()
        return normalized in [
            "yes", "y", "proceed", "go", "go ahead", "confirmed",
            "ok", "okay", "sure", "do it", "tamam", "نعم", "تمام",
            "ماشي", "موافق",
        ]


# ──────────────────────────────────────────────────────────────────────────────
# 5. Runtime المنسق
# ──────────────────────────────────────────────────────────────────────────────

class OrchestratorRuntime:
    def __init__(self, soul_path: Path = SOUL_PATH):
        self.soul_path = soul_path
        self.soul_content = self._load_soul()
        self.registry = AgentRegistry()
        self.validator = OrchestratorValidator()
        self.active_plan: Optional[TaskPlan] = None
        self.model_call_fn: Optional[Callable] = None
        self.agent_call_fn: Optional[Callable] = None
        self._pending_yes: bool = False
        self._waiting_for_user: bool = False

    def _load_soul(self) -> str:
        if not self.soul_path.is_file():
            raise FileNotFoundError(f"SOUL.md not found: {self.soul_path}")
        return self.soul_path.read_text(encoding="utf-8")

    def _system_prompt(self) -> str:
        return self.soul_content

    def set_model_caller(self, fn: Callable):
        """تعريف دالة استدعاء النموذج (API خارجي)"""
        self.model_call_fn = fn

    def set_agent_caller(self, fn: Callable):
        """تعريف دالة استدعاء وكيل"""
        self.agent_call_fn = fn

    # ── دورة الحياة ──

    def receive_user_request(self, request: str) -> str:
        """1. استقبال طلب المستخدم وإنشاء خطة"""
        task_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"

        # تحليل بسيط لتحديد المستوى
        thinking = self._estimate_thinking(request)
        cost_tier = self._estimate_cost(request)
        agents = self.registry.get_agents_for_task(request)
        topology = "single" if len(agents) <= 1 else "sequential"

        plan = TaskPlan(
            task_id=task_id,
            user_request=request,
            thinking=thinking,
            cost_tier=cost_tier,
            agents=agents if agents else ["@coder-agent"],
            topology=topology,
            estimated_tokens=self._estimate_tokens(request),
            justification=f"تحليل تلقائي: {len(agents)} وكيل مناسب",
        )
        self.active_plan = plan

        # بناء Recommendation block
        block = self._build_recommendation_block(plan)
        plan.phase = TurnPhase.AWAITING_APPROVAL
        self._waiting_for_user = True
        return block

    def receive_user_approval(self, response: str) -> str:
        """2. استلام موافقة المستخدم → تفريع المهام"""
        if not self.validator.validate_yes(response):
            return "⚠️ الرجاء الرد بـ 'نعم' أو 'yes' للمتابعة، أو اطلب تغيير الخطة."

        self._waiting_for_user = False
        assert self.active_plan is not None
        self.active_plan.phase = TurnPhase.DISPATCHING

        # بناء المهام لكل وكيل
        for agent in self.active_plan.agents:
            task = AgentTask(
                task_id=self.active_plan.task_id,
                agent_name=agent,
                instructions=self._build_agent_instructions(agent, self.active_plan),
            )
            self.active_plan.agent_tasks[agent] = task

        # إرسال المهام (sequential or parallel)
        if self.active_plan.topology == "parallel":
            return self._dispatch_parallel()
        else:
            return self._dispatch_sequential()

    def receive_agent_result(self, agent_name: str, result: str, error: Optional[str] = None) -> str:
        """3. استلام نتيجة وكيل"""
        if not self.active_plan or agent_name not in self.active_plan.agent_tasks:
            return f"⚠️ لا توجد مهمة نشطة للوكيل {agent_name}"

        task = self.active_plan.agent_tasks[agent_name]
        if error:
            task.status = TaskStatus.FAILED
            task.error = error
            return f"❌ فشل {agent_name}: {error}"

        task.status = TaskStatus.AGENT_RETURNED
        task.output = result
        task.completed_at = time.time()

        # التحقق من اكتمال الكل
        all_done = all(
            t.status in (TaskStatus.AGENT_RETURNED, TaskStatus.FAILED)
            for t in self.active_plan.agent_tasks.values()
        )
        if all_done:
            self.active_plan.phase = TurnPhase.AUDITING
            return self._run_final_audit()
        return f"✅ تم استلام نتيجة {agent_name} — بانتظار البقية..."

    # ── المنطق الداخلي ──

    def _build_recommendation_block(self, plan: TaskPlan) -> str:
        agents_str = ", ".join(plan.agents) if plan.agents else "N/A"
        return f"""
Recommendation:
├─ Task ID: {plan.task_id}
├─ Thinking: {plan.thinking}
├─ Cost: {plan.cost_tier}
├─ Agent(s): {agents_str}
├─ Topology: {plan.topology.capitalize()}
├─ Tokens: ~{plan.estimated_tokens}
├─ Est. cost: ${plan.estimated_tokens * 0.00001:.4f}
├─ Commitment: {plan.commitment or 'accepted'}
└─ ⚠️ Irreversible step: {plan.irreversible_step or '<none>'}

Proceed? (yes / no)
"""

    def _build_agent_instructions(self, agent: str, plan: TaskPlan) -> str:
        """بناء تعليمات الوكيل"""
        return f"""Task ID: {plan.task_id}
Original Request: {plan.user_request}
Your Role: Execute your portion of this task.
Output Format: Structured output as defined in agent-registry.md
Constraints: Follow your SOUL.md. Return only your deliverable.
"""

    def _dispatch_sequential(self) -> str:
        """إرسال المهام تسلسلياً"""
        if not self.active_plan:
            return "❌ لا توجد خطة نشطة"

        agents = list(self.active_plan.agent_tasks.keys())
        if not agents:
            return "❌ لا يوجد وكلاء"

        # إرسال أول وكيل فقط — الباقي يُرسل بعد النتيجة
        first_agent = agents[0]
        task = self.active_plan.agent_tasks[first_agent]
        task.status = TaskStatus.AGENT_WORKING
        task.started_at = time.time()

        if self.agent_call_fn:
            self.agent_call_fn(task.agent_name, task.instructions, task.task_id)

        return f"🔄 تم إرسال المهمة إلى {first_agent} — بانتظار النتيجة..."

    def _dispatch_parallel(self) -> str:
        """إرسال المهام بالتوازي"""
        if not self.active_plan:
            return "❌ لا توجد خطة نشطة"

        for agent, task in self.active_plan.agent_tasks.items():
            task.status = TaskStatus.AGENT_WORKING
            task.started_at = time.time()
            if self.agent_call_fn:
                self.agent_call_fn(task.agent_name, task.instructions, task.task_id)

        agents_list = ", ".join(self.active_plan.agent_tasks.keys())
        return f"🔄 تم إرسال المهام بالتوازي إلى: {agents_list}"

    def _run_final_audit(self) -> str:
        """4. تشغيل final-audit"""
        if not self.active_plan:
            return "❌ لا توجد خطة نشطة"

        outputs = {
            agent: task.output
            for agent, task in self.active_plan.agent_tasks.items()
            if task.output
        }

        if not outputs:
            return "❌ لا توجد مخرجات للتدقيق"

        # تدقيق بسيط
        audit_results = []
        for agent, output in outputs.items():
            issues = self._audit_output(output)
            audit_results.append({
                "agent": agent,
                "pass": len(issues) == 0,
                "issues": issues,
            })

        all_passed = all(r["pass"] for r in audit_results)

        if all_passed:
            self.active_plan.phase = TaskStatus.COMPLETED
            result_text = "\n\n".join(
                f"## Output from {agent}\n{output}"
                for agent, output in outputs.items()
            )
            return f"""
✅ Final Audit: PASS

{'='*60}
RESULT
{'='*60}

{result_text}

{'='*60}
Task ID: {self.active_plan.task_id}
Audit: All agents passed
"""
        else:
            issues_text = "\n".join(
                f"- {r['agent']}: {', '.join(r['issues'])}"
                for r in audit_results if not r["pass"]
            )
            return f"""
⚠️ Final Audit: ISSUES FOUND

{issues_text}

Options:
├─ Fix → "Return to agents"
├─ Accept as-is → "Accept with warnings"
└─ Cancel → "Cancel"
"""

    def _audit_output(self, output: str) -> List[str]:
        """تدقيق بسيط للمخرجات"""
        issues = []
        if not output or len(output.strip()) < 10:
            issues.append("مخرجات فارغة أو قصيرة جداً")
        if "FAIL" in output.upper():
            issues.append("تحتوي على FAIL")
        if "ERROR" in output.upper():
            issues.append("تحتوي على ERROR")
        if len(output) > 50000:
            issues.append("مخرجات طويلة جداً (>50K chars)")
        return issues

    # ── أدوات التقدير ──

    def _estimate_thinking(self, request: str) -> str:
        if len(request) < 50:
            return "🟢 Light"
        elif len(request) < 200:
            return "🟡 Medium"
        return "🟠 Deep"

    def _estimate_cost(self, request: str) -> str:
        if len(request) < 50:
            return "💰 Budget"
        elif len(request) < 200:
            return "💰💰 Mid"
        return "💰💰💰 Premium"

    def _estimate_tokens(self, request: str) -> int:
        return max(500, len(request) * 3)

    def __repr__(self):
        return f"OrchestratorRuntime(soul={len(self.soul_content)} chars, registry={len(self.registry.agents)} agents)"


# ──────────────────────────────────────────────────────────────────────────────
# 6. اختبار شامل
# ──────────────────────────────────────────────────────────────────────────────

def test_full_flow():
    print("=" * 70)
    print("🧪 اختبار دورة حياة المنسق الكاملة")
    print("=" * 70)

    runtime = OrchestratorRuntime()
    print(f"✅ المنسق: {runtime}")
    print(f"   الوكلاء: {list(runtime.registry.agents.keys())[:5]}...")

    # ── الخطوة 1: استقبال طلب المستخدم ──
    print("\n" + "─" * 70)
    print("📌 الخطوة 1: استقبال طلب المستخدم")
    print("─" * 70)
    user_request = "اكتب مقالاً عن الذكاء الاصطناعي في التعليم"
    print(f"   الطلب: '{user_request}'")
    recommendation = runtime.receive_user_request(user_request)
    print(recommendation)

    # ── التحقق ──
    is_valid, errors = runtime.validator.validate_recommendation(recommendation)
    if not is_valid:
        print(f"   ⚠️ تحذيرات: {errors}")

    # ── الخطوة 2: موافقة المستخدم ──
    print("─" * 70)
    print("📌 الخطوة 2: موافقة المستخدم")
    print("─" * 70)
    user_response = "yes"
    print(f"   الرد: '{user_response}'")
    dispatch_result = runtime.receive_user_approval(user_response)
    print(f"   {dispatch_result}")

    # ── الخطوة 3: محاكاة عودة الوكيل ──
    print("─" * 70)
    print("📌 الخطوة 3: عودة الوكيل بالنتيجة")
    print("─" * 70)
    if runtime.active_plan:
        for agent in runtime.active_plan.agent_tasks:
            sample_result = f"## Research Results\n\nThis is a sample output from {agent} for task {runtime.active_plan.task_id}.\n\n- Point 1: AI improves education\n- Point 2: Personalized learning\n- Point 3: Automated grading"
            result = runtime.receive_agent_result(agent, sample_result)
            print(f"   {result}")

    print("\n✅ اكتمل الاختبار")


if __name__ == "__main__":
    test_full_flow()
