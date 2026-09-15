#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           Orchestrator Validation Layer (OVL) v1.0                          ║
║          طبقة التحقق الإجبارية — تعمل خارج Hermes                           ║
║                                                                              ║
║  تمنع المنسق من الرد مباشرة وتجبره على التفويض أولاً                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# 1. الأنواع والثوابت
# ──────────────────────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    DELEGATE = "delegate"
    RECOMMEND = "recommend"           # عرض توصية (في الدور الأول فقط)
    RESPOND_DIRECT = "respond_direct" # — ممنوع — يُرفض تلقائياً


class TurnPhase(str, Enum):
    ANALYZE = "analyze"               # الدور الأول: تحليل + توصية فقط
    EXECUTE = "execute"               # الدور الثاني: تنفيذ بعد الموافقة


class ValidationResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    RETRY = "retry"


@dataclass
class OrchestratorOutput:
    """هيكل مخرجات المنسق المتوقعة"""
    action: str
    task_id: Optional[str] = None
    thinking: Optional[str] = None           # 🟢 🟡 🟠
    cost_tier: Optional[str] = None         # 💰 💰💰 💰💰💰
    target_agents: List[str] = field(default_factory=list)
    topology: Optional[str] = None          # single / sequential / parallel
    estimated_tokens: Optional[int] = None
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    justification: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "OrchestratorOutput":
        return cls(
            action=data.get("action", ""),
            task_id=data.get("task_id"),
            thinking=data.get("thinking"),
            cost_tier=data.get("cost_tier"),
            target_agents=data.get("target_agents", []),
            topology=data.get("topology"),
            estimated_tokens=data.get("estimated_tokens"),
            tasks=data.get("tasks", []),
            justification=data.get("justification"),
        )


@dataclass
class ValidationReport:
    """تقرير التحقق"""
    result: ValidationResult
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    phase: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "result": self.result.value,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "phase": self.phase,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskState:
    """حالة المهمة — تتبع عبر الأدوار"""
    task_id: str
    phase: TurnPhase = TurnPhase.ANALYZE
    user_approved: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    agents_dispatched: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# 2. مُحقق المخرجات
# ──────────────────────────────────────────────────────────────────────────────

class OutputValidator:
    """
    يتحقق من أن مخرجات المنسق تحتوي على action: "delegate"
    ويرفض أي مخرجات بدون تفويض
    """

    REQUIRED_DELEGATE_FIELDS = ["action", "target_agents", "tasks"]
    REQUIRED_RECOMMEND_FIELDS = ["action", "thinking", "cost_tier", "target_agents"]

    # أنماط النص العادي المشبوه (محاولة للإجابة المباشرة)
    SUSPICIOUS_PATTERNS = [
        r"^إليك\s+(الإجابة|الجواب|الحل)",
        r"^الإجابة\s+(هي|على)",
        r"^الجواب\s+(هو|على)",
        r"^إليك\s+تحليلي",
        r"^بناءً\s+على\s+معرفتي",
        r"^سأشرح\s+لك",
        r"^دعني\s+أوضح",
        r"^التحليل\s+التالي",
        r"^إليك\s+النتيجة",
        r"^الحل\s+(هو|التالي)",
    ]

    def validate_structured(self, output: dict, phase: TurnPhase) -> ValidationReport:
        """التحقق من مخرجات JSON المهيكلة"""
        errors: List[str] = []
        warnings: List[str] = []

        # ── 1. فحص action ──
        action = output.get("action", "")
        if not action:
            errors.append("حقل 'action' مفقود — يجب أن يكون 'delegate' أو 'recommend'")
            return ValidationReport(ValidationResult.FAIL, False, errors, warnings, phase.value)

        if action == ActionType.RESPOND_DIRECT.value:
            errors.append(
                f"action='respond_direct' ممنوع — المنسق لا يجيب مباشرة. "
                f"يجب تفويض المهمة"
            )
            return ValidationReport(ValidationResult.FAIL, False, errors, warnings, phase.value)

        # ── 2. في الدور الأول: يُسمح فقط بـ recommend ──
        if phase == TurnPhase.ANALYZE:
            if action != ActionType.RECOMMEND.value:
                errors.append(
                    f"في الدور الأول (analyze) يُسمح فقط بـ action='recommend'. "
                    f"حصلنا على: '{action}'"
                )
                return ValidationReport(ValidationResult.FAIL, False, errors, warnings, phase.value)

        # ── 3. في الدور الثاني: يجب أن يكون delegate ──
        if phase == TurnPhase.EXECUTE:
            if action != ActionType.DELEGATE.value:
                errors.append(
                    f"في الدور الثاني (execute) يجب أن يكون action='delegate'. "
                    f"حصلنا على: '{action}'"
                )
                return ValidationReport(ValidationResult.FAIL, False, errors, warnings, phase.value)

        # ── 4. فحص الحقول الإجبارية ──
        if action == ActionType.DELEGATE.value:
            for f in self.REQUIRED_DELEGATE_FIELDS:
                if f not in output or not output[f]:
                    errors.append(f"حقل إجبارى مفقود: '{f}'")

        if action == ActionType.RECOMMEND.value:
            for f in self.REQUIRED_RECOMMEND_FIELDS:
                if f not in output or not output[f]:
                    errors.append(f"حقل إجبارى مفقود في التوصية: '{f}'")

        # ── 5. فحص الوكلاء المستهدفين ──
        targets = output.get("target_agents", [])
        if isinstance(targets, list):
            for agent in targets:
                if not agent.startswith("@"):
                    warnings.append(
                        f"اسم الوكيل '{agent}' يجب أن يبدأ بـ '@'"
                    )

        # ── 6. فحص المهام المُفوضة ──
        tasks = output.get("tasks", [])
        if isinstance(tasks, list) and tasks:
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    errors.append(f"المهمة {i} يجب أن تكون dict")
                    continue
                if "agent" not in task:
                    errors.append(f"المهمة {i}: حقل 'agent' مفقود")
                if "task_description" not in task:
                    errors.append(f"المهمة {i}: حقل 'task_description' مفقود")

        # ── 7. فحص المبرر ──
        justification = output.get("justification", "")
        if action == ActionType.RECOMMEND.value and not justification:
            warnings.append("حقل 'justification' مُفضّل في التوصية")

        is_valid = len(errors) == 0
        result = ValidationResult.PASS if is_valid else ValidationResult.FAIL
        return ValidationReport(result, is_valid, errors, warnings, phase.value)

    def validate_text(self, text: str, phase: TurnPhase) -> ValidationReport:
        """التحقق من نص عادي (fallback) — يبحث عن JSON مُضمَّن"""
        errors: List[str] = []
        warnings: List[str] = []

        # ── 1. محاولة استخراج JSON من النص ──
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self.validate_structured(data, phase)
            except json.JSONDecodeError:
                pass

        # محاولة استخراج من كتلة markdown
        md_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if md_match:
            try:
                data = json.loads(md_match.group(1))
                return self.validate_structured(data, phase)
            except json.JSONDecodeError:
                pass

        # ── 2. فحص الأنماط المشبوهة (محاولة إجابة مباشرة) ──
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                errors.append(
                    f"محاولة إجابة مباشرة مكتشفة: النمط '{pattern}'. "
                    f"المنسق لا يجيب مباشرة"
                )

        # ── 3. إذا لم يوجد JSON صالح → رفض ──
        if not errors:
            errors.append(
                "لا يوجد JSON صالح في المخرجات. "
                "يجب أن يخرج المنسق بصيغة JSON تحتوي على 'action'"
            )

        is_valid = len(errors) == 0
        result = ValidationResult.FAIL if not is_valid else ValidationResult.PASS
        return ValidationReport(result, is_valid, errors, warnings, phase.value)


# ──────────────────────────────────────────────────────────────────────────────
# 3. حلقة التحقق (Validation Loop)
# ──────────────────────────────────────────────────────────────────────────────

class ValidationLoop:
    """
    حلقة تحقق كاملة:
    1. استقبال رد المنسق
    2. التحقق من البنية
    3. التحقق من وجود تفويض
    4. الرفض/القبول/إعادة المحاولة
    """

    MAX_RETRIES = 3

    def __init__(self, registry_path: Optional[str] = None):
        self.validator = OutputValidator()
        self.state_store: Dict[str, TaskState] = {}
        self.registry_path = Path(registry_path) if registry_path else None

    def process_response(
        self,
        raw_output: Any,
        task_id: Optional[str] = None,
        user_approved: bool = False,
    ) -> Tuple[ValidationReport, dict]:
        """
        معالجة رد المنسق.
        raw_output: نص أو dict
        task_id: معرف المهمة
        user_approved: هل وافق المستخدم على التوصية؟

        يُرجع: (تقرير التحقق, بيانات للاستخدام)
        """

        # ── 1. تحديد المرحلة ──
        phase = TurnPhase.EXECUTE if user_approved else TurnPhase.ANALYZE
        if task_id and task_id in self.state_store:
            state = self.state_store[task_id]
            if state.user_approved:
                phase = TurnPhase.EXECUTE

        # ── 2. التحقق من المخرجات ──
        if isinstance(raw_output, dict):
            report = self.validator.validate_structured(raw_output, phase)
        elif isinstance(raw_output, str):
            report = self.validator.validate_text(raw_output, phase)
        else:
            report = ValidationReport(
                ValidationResult.FAIL, False,
                [f"نوع المخرجات غير مدعوم: {type(raw_output).__name__}"],
                [], phase.value,
            )

        # ── 3. إنشاء task_id إذا لم يوجد ──
        if task_id is None:
            task_id = f"task-{uuid.uuid4().hex[:8]}"

        # ── 4. إنشاء/تحديث الحالة ──
        if task_id not in self.state_store:
            self.state_store[task_id] = TaskState(task_id=task_id, phase=phase)

        return report, {"task_id": task_id, "phase": phase.value}

    def approve_task(self, task_id: str) -> Optional[TaskState]:
        """موافقة المستخدم على التوصية"""
        if task_id in self.state_store:
            state = self.state_store[task_id]
            state.user_approved = True
            state.phase = TurnPhase.EXECUTE
            return state
        return None

    def mark_agent_dispatched(self, task_id: str, agent_id: str):
        """تسجيل إرسال مهمة لوكيل"""
        if task_id in self.state_store:
            self.state_store[task_id].agents_dispatched.append(agent_id)

    def mark_agent_completed(self, task_id: str, agent_id: str, output: Any):
        """تسجيل اكتمال مهمة وكيل"""
        if task_id in self.state_store:
            self.state_store[task_id].outputs[agent_id] = output

    def get_recommendation_block(self, task_id: str) -> Optional[str]:
        """بناء كتلة التوصية من المخرجات"""
        state = self.state_store.get(task_id)
        if not state or state.phase != TurnPhase.ANALYZE:
            return None
        return None  # يُبنى من قبل المنسق


# ──────────────────────────────────────────────────────────────────────────────
# 4. أدوات مساعدة للأنظمة الخارجية
# ──────────────────────────────────────────────────────────────────────────────

def build_system_prompt(registry_agents: Dict[str, str]) -> str:
    """بناء الـ System Prompt القسري للمنسق"""
    agents_list = "\n".join(
        f"  - @{name}: {role}" for name, role in registry_agents.items()
    )

    return f"""[ROLE]
You are a Strict Master Orchestrator. You DO NOT execute tasks yourself.
You DO NOT answer user questions directly using your internal knowledge.

[RULES]
1. NEVER answer the user's request directly.
2. ALWAYS respond with structured JSON only — no prose, no explanation outside JSON.
3. In the FIRST response (before user approval), use action: "recommend".
4. After user says "yes", use action: "delegate" with specific agent assignments.
5. Each delegated task MUST include "agent" and "task_description" fields.
6. If no sub-agent is suitable, state that clearly in "justification".

[AVAILABLE AGENTS]
{agents_list}

[OUTPUT FORMAT]
{{
  "action": "recommend" | "delegate",
  "task_id": "unique-task-id",
  "thinking": "🟢 Light | 🟡 Medium | 🟠 Deep",
  "cost_tier": "💰 Budget | 💰💰 Mid | 💰💰💰 Premium",
  "target_agents": ["@agent-name"],
  "topology": "single | sequential | parallel",
  "estimated_tokens": 5000,
  "tasks": [
    {{
      "agent": "@agent-name",
      "task_description": "Detailed instructions for this agent"
    }}
  ],
  "justification": "Why this delegation is necessary"
}}

[CRITICAL]
- You MUST output ONLY valid JSON.
- No markdown outside the JSON block.
- No explanations before or after the JSON.
- If you output anything else, the system will reject your response.
"""


def build_tool_definition() -> dict:
    """تعريف أداة التفويض (للتسجيل في منصة خارجية)"""
    return {
        "name": "delegate_to_agent",
        "description": "Delegate a task to a sub-agent. This is the ONLY way to execute work.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the sub-agent (e.g., @research-agent-multi)"
                },
                "task_description": {
                    "type": "string",
                    "description": "Detailed instructions for the sub-agent"
                },
                "input_data": {
                    "type": "string",
                    "description": "Optional: input data for the sub-agent"
                }
            },
            "required": ["agent_name", "task_description"]
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# 5. اختبار سريع
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    loop = ValidationLoop()

    # ── اختبار 1: مخرجات صحيحة (recommend) ──
    print("=" * 60)
    print("📌 اختبار 1: توصية صحيحة")
    print("=" * 60)
    good_recommend = {
        "action": "recommend",
        "task_id": "test-001",
        "thinking": "🟡 Medium",
        "cost_tier": "💰💰 Mid",
        "target_agents": ["@research-agent-multi", "@strategy-agent"],
        "topology": "sequential",
        "estimated_tokens": 5000,
        "justification": "هذه المهمة تحتاج بحثاً استراتيجياً متعمقاً",
    }
    report, data = loop.process_response(good_recommend, task_id="test-001")
    print(f"  النتيجة: {report.result.value} | صالح: {report.is_valid}")
    if report.errors:
        print(f"  أخطاء: {report.errors}")
    print()

    # ── اختبار 2: محاولة إجابة مباشرة ──
    print("=" * 60)
    print("📌 اختبار 2: إجابة مباشرة (يجب أن يُرفض)")
    print("=" * 60)
    bad_output = "إليك الإجابة على سؤالك: الذكاء الاصطناعي مهم لأنه..."
    report, data = loop.process_response(bad_output, task_id="test-002")
    print(f"  النتيجة: {report.result.value} | صالح: {report.is_valid}")
    if report.errors:
        print(f"  أخطاء: {report.errors}")
    print()

    # ── اختبار 3: JSON مع action خاطئ ──
    print("=" * 60)
    print("📌 اختبار 3: action خاطئ (يجب أن يُرفض)")
    print("=" * 60)
    wrong_action = {
        "action": "respond_direct",
        "text": "هذه إجابة مباشرة",
    }
    report, data = loop.process_response(wrong_action, task_id="test-003")
    print(f"  النتيجة: {report.result.value} | صالح: {report.is_valid}")
    if report.errors:
        print(f"  أخطاء: {report.errors}")
    print()

    # ── اختبار 4: تفويض صحيح (execute) ──
    print("=" * 60)
    print("📌 اختبار 4: تفويض صحيح")
    print("=" * 60)
    good_delegate = {
        "action": "delegate",
        "task_id": "test-004",
        "target_agents": ["@coder-agent"],
        "tasks": [
            {
                "agent": "@coder-agent",
                "task_description": "اكتب كود Python لتحليل ملف CSV"
            }
        ],
        "justification": "المهمة تتطلب كتابة كود",
    }
    report, data = loop.process_response(
        good_delegate, task_id="test-004", user_approved=True
    )
    print(f"  النتيجة: {report.result.value} | صالح: {report.is_valid}")
    if report.errors:
        print(f"  أخطاء: {report.errors}")
    print()

    # ── اختبار 5: JSON ناقص ──
    print("=" * 60)
    print("📌 اختبار 5: JSON ناقص (يجب أن يُرفض)")
    print("=" * 60)
    incomplete = {
        "action": "delegate",
        "task_id": "test-005",
        # missing: target_agents, tasks
    }
    report, data = loop.process_response(
        incomplete, task_id="test-005", user_approved=True
    )
    print(f"  النتيجة: {report.result.value} | صالح: {report.is_valid}")
    if report.errors:
        print(f"  أخطاء: {report.errors}")
    print()

    # ── اختبار 6: نص عادي يحوي JSON ──
    print("=" * 60)
    print("📌 اختبار 6: نص عادي + JSON مُضمَّن")
    print("=" * 60)
    mixed_output = """إليك التوصية:

```json
{
  "action": "recommend",
  "thinking": "🟢 Light",
  "cost_tier": "💰 Budget",
  "target_agents": ["@qa-agent"],
  "justification": "مهمة بسيطة للتحقق"
}
```
"""
    report, data = loop.process_response(mixed_output, task_id="test-006")
    print(f"  النتيجة: {report.result.value} | صالح: {report.is_valid}")
    if report.errors:
        print(f"  أخطاء: {report.errors}")
    if report.warnings:
        print(f"  تحذيرات: {report.warnings}")
    print()

    # ── اختبار 7: System Prompt Builder ──
    print("=" * 60)
    print("📌 اختبار 7: System Prompt")
    print("=" * 60)
    agents = {
        "research-agent-multi": "Deep web research",
        "strategy-agent": "Strategic analysis",
        "coder-agent": "Code generation",
        "qa-agent": "Quality assurance",
    }
    prompt = build_system_prompt(agents)
    print(f"  الطول: {len(prompt)} حرف")
    print(f"  السطر الأول: {prompt.splitlines()[0]}")
    print()

    print("✅ اكتمل اختبار طبقة التحقق")
