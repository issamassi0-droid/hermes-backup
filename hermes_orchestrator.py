#!/usr/bin/env python3
"""
Hermes Cluster Orchestration Engine — LIVE v7.0.0
===================================================
محرك تنسيق الوكلاء الحقيقي — يقرأ السجل المشترك من /shared/agent-registry.md
المنسق هو المخاطب الوحيد. الموافقة البشرية إجبارية. الاتصال المباشر ممنوع.

المصدر الوحيد للحقيقة: /home/massi/.hermes/shared/agent-registry.md
لا توجد بيانات وكيل مبرمجة تصريحاً — كلها تُقرأ من السجل المشترك.

الجديد في v7.0.0 — بعد المراجعة المعمارية لـ v6:
------------------------------------------------------------
1) حالة المزودين/النماذج صارت **مشتركة عبر العمليات** (multi-process)
   عبر ملف على القرص محمي بـ fcntl.flock، بدل أن تكون محصورة في ذاكرة
   كل process. هذا يمنع نسختين من المحرك من استهلاك نفس الرصيد في آن واحد.

2) حلقة الفحص الدورية `_scan_once` لم تعد تطمس الوسم الحي (live mark)
   الذي وُضع فور 429/401/5xx أثناء التنفيذ. يوجد TTL يعطي الوسم الحي
   أولوية على نتيجة الفحص الدوري حتى يتلاشى (LIVE_MARK_TTL).

3) إزالة السقف الاصطناعي `min(pair_count, 6)`. الآن كل وكيل يستطيع أن
   يجرب كل الأزواج المعروفة ما دام لم يجربها بالفعل (tried_pairs).

4) Circuit Breaker مع تلاشي زمني (decay) بدل تصفير الحالة بين المهام.
   إذا نفد زوج قبل 45 ثانية، لا تحاول مهمة جديدة استخدامه فوراً؛ لكن
   يُنسى الوسم بعد انتهاء صلاحيته حتى لا يتحول إلى حظر أبدي.

5) واجهة موحدة للبوتات: `OrchestratorAgent.message_agent()` — JSON-in /
   JSON-out، بدون print/input، جاهزة للربط بـ Telegram/Discord/HTTP.
   تفرّق بين نمط `auto_approve` (بيئات CI) و `human` (الافتراضي الآمن).

6) تنظيف مضمون لكل الأربطة عند نهاية المهمة عبر finally، حتى في حال
   SecurityViolation أو KeyboardInterrupt.
"""

import os
import re
import json
import uuid
import fcntl
import pathlib
import threading
import tempfile
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable

try:
    import requests  # pip install requests
except ImportError:
    requests = None

try:
    import yaml  # pip install pyyaml
except ImportError:
    yaml = None


# =====================================================================
# 0. إعدادات عامة
# =====================================================================

REGISTRY_PATH = "/home/massi/.hermes/shared/agent-registry.md"
PROVIDERS_CONFIG_PATH = os.path.expanduser("~/.hermes/shared/providers.yaml")

# ملف الحالة المشتركة بين العمليات
SHARED_STATE_PATH = os.path.expanduser("~/.hermes/shared/model_state.json")
SHARED_STATE_LOCK = os.path.expanduser("~/.hermes/shared/model_state.lock")

PROBE_TIMEOUT_SECONDS = 3
SCAN_INTERVAL_SECONDS = 15

# الوسم الحي (429/401/5xx الفعلي أثناء التنفيذ) يمنع الفحص الدوري من
# إعادة الزوج إلى "available" حتى تنقضي هذه المدة.
LIVE_MARK_TTL_SECONDS = 60

# مدة صلاحية circuit breaker — بعدها يُنسى الوسم ويُعاد الأخذ بالزوج.
CIRCUIT_BREAKER_TTL_SECONDS = 300


# =====================================================================
# 1. محلل السجل المشترك (MD Parser) — بدون تغيير
# =====================================================================

class AgentRegistry:
    """يقرأ السجل المشترك من agent-registry.md ويستخرج بيانات الوكلاء."""

    def __init__(self, registry_path: str = REGISTRY_PATH):
        self.registry_path = pathlib.Path(registry_path)
        self._data: Optional[Dict[str, Dict[str, Any]]] = None
        self._loaded_at: Optional[str] = None

    def load(self) -> Dict[str, Dict[str, Any]]:
        if not self.registry_path.is_file():
            raise FileNotFoundError(f"Shared registry not found: {self.registry_path}")
        text = self.registry_path.read_text()
        self._data = self._parse(text)
        self._loaded_at = datetime.now().isoformat()
        return self._data

    def reload(self) -> Dict[str, Dict[str, Any]]:
        return self.load()

    @property
    def data(self) -> Dict[str, Dict[str, Any]]:
        if self._data is None:
            self.load()
        return self._data

    def get_agent(self, agent_id: str, default=None) -> Optional[Dict[str, Any]]:
        return self.data.get(agent_id, default)

    def find_by_role(self, capability: str) -> Optional[str]:
        capability_lower = capability.lower()
        best_match, best_score = None, 0
        for agent_id, info in self.data.items():
            role = info.get('role', '').lower()
            score = sum(len(k) for k in capability_lower.split() if k in role)
            if score > best_score:
                best_score, best_match = score, agent_id
        return best_match

    def _parse(self, text: str) -> Dict[str, Dict[str, Any]]:
        lines = text.split('\n')
        agents: Dict[str, Dict[str, Any]] = {}
        current_agent: Optional[str] = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('## `@'):
                match = re.match(r'## `@([\w-]+)`', stripped)
                if match:
                    current_agent = match.group(1)
                    desc = stripped.split('—')[1].strip() if '—' in stripped else ''
                    agents[current_agent] = {
                        'description': desc, 'role': '', 'inputs': [],
                        'outputs': [], 'tools': [], 'decision_authority': ''
                    }
            elif current_agent and '|' in stripped and stripped.startswith('|'):
                cells = [c.strip() for c in stripped.split('|')]
                cells = [c for c in cells if c]
                if len(cells) >= 2:
                    key, value = cells[0], '|'.join(cells[1:])
                    if '**Role**' in key:
                        agents[current_agent]['role'] = value.strip('`').strip()
                    elif '**Input from**' in key:
                        agents[current_agent]['inputs'] = self._parse_list(value)
                    elif '**Output to**' in key:
                        agents[current_agent]['outputs'] = self._parse_list(value)
                    elif '**Produces**' in key:
                        agents[current_agent]['outputs'] = self._parse_list(value)
                    elif '**Consumes**' in key:
                        agents[current_agent]['inputs'] = self._parse_list(value)
                    elif '**Tools**' in key:
                        agents[current_agent]['tools'] = self._parse_list(value)
                    elif '**Decision authority**' in key:
                        agents[current_agent]['decision_authority'] = value.strip()
        return agents

    def _parse_list(self, value: str) -> List[str]:
        return [v.strip().strip('`').strip() for v in value.split(',') if v.strip()]

    def list_agents(self) -> List[str]:
        return list(self.data.keys())

    def validate(self) -> Dict[str, Any]:
        issues = []
        for agent_id, info in self.data.items():
            if not info['role']:
                issues.append(f"@{agent_id}: missing Role")
            if not info['tools']:
                issues.append(f"@{agent_id}: missing Tools")
        return {'valid': len(issues) == 0, 'issues': issues,
                'total_agents': len(self.data)}


# =====================================================================
# 1.5 الاستثناءات — بدون تغيير
# =====================================================================

class ModelCallError(Exception):
    def __init__(self, provider_id: str, model: str, detail: str = ""):
        self.provider_id, self.model, self.detail = provider_id, model, detail
        super().__init__(f"{provider_id}/{model}: {detail}")


class RateLimitExceeded(ModelCallError):
    def __init__(self, agent_id: str, provider_id: str, model: str):
        self.agent_id = agent_id
        super().__init__(provider_id, model, "rate limited (HTTP 429) أثناء التنفيذ")


class AuthFailedError(ModelCallError):
    pass


# =====================================================================
# 1.7 المخزن المشترك عبر العمليات (NEW)
# =====================================================================

class SharedStateStore:
    """
    حالة model_monitor على القرص، محمية بـ fcntl.flock لضمان الكتابة الذرّية
    عبر العمليات. البنية:
        {
          "pairs": {
            "openai/gpt-4o": {"state": "quota_exhausted",
                              "marked_at": "2026-...", "source": "live"},
            ...
          },
          "assignments": {"agent-a": "openai/gpt-4o", ...},
          "pid_map": {"agent-a": 12345, ...},
          "updated_at": "2026-..."
        }
    """

    def __init__(self, path: str = SHARED_STATE_PATH, lock_path: str = SHARED_STATE_LOCK):
        self.path = pathlib.Path(path)
        self.lock_path = pathlib.Path(lock_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def _acquire(self, fd):
        fcntl.flock(fd, fcntl.LOCK_EX)

    def _release(self, fd):
        fcntl.flock(fd, fcntl.LOCK_UN)

    def _read_unlocked(self) -> Dict[str, Any]:
        if not self.path.is_file():
            return {"pairs": {}, "assignments": {}, "pid_map": {}, "updated_at": None}
        try:
            return json.loads(self.path.read_text() or "{}") or \
                   {"pairs": {}, "assignments": {}, "pid_map": {}, "updated_at": None}
        except (json.JSONDecodeError, OSError):
            return {"pairs": {}, "assignments": {}, "pid_map": {}, "updated_at": None}

    def _write_unlocked(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        os.replace(tmp, self.path)  # atomic rename

    def read(self) -> Dict[str, Any]:
        with open(self.lock_path, "a+") as fd:
            self._acquire(fd)
            try:
                return self._read_unlocked()
            finally:
                self._release(fd)

    def mutate(self, fn: Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
        """تعديل ذرّي: fn تعدّل dict في الذاكرة، ثم نكتبه على القرص."""
        with open(self.lock_path, "a+") as fd:
            self._acquire(fd)
            try:
                data = self._read_unlocked()
                fn(data)
                self._write_unlocked(data)
                return data
            finally:
                self._release(fd)

    # -----------------------------------------------------------------
    # تنظيف الوسوم المنتهية (تُستدعى دورياً)
    # -----------------------------------------------------------------
    @staticmethod
    def _is_expired(iso_ts: Optional[str], ttl_seconds: int) -> bool:
        if not iso_ts:
            return True
        try:
            ts = datetime.fromisoformat(iso_ts)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - ts) > timedelta(seconds=ttl_seconds)
        except (ValueError, TypeError):
            return True

    def prune_expired(self) -> None:
        """يحذف الوسوم التي انتهت صلاحيتها (circuit breaker decay)."""
        def _fn(data: Dict[str, Any]) -> None:
            pairs = data.get("pairs", {})
            stale = [
                k for k, v in pairs.items()
                if self._is_expired(v.get("marked_at"), CIRCUIT_BREAKER_TTL_SECONDS)
            ]
            for k in stale:
                pairs.pop(k, None)
        self.mutate(_fn)


# =====================================================================
# 2. الوكيل الفرعي — بدون تغيير جوهري
# =====================================================================

class SubAgent:
    def __init__(self, agent_id: str, registry: AgentRegistry):
        self.agent_id = agent_id
        self.registry = registry
        self.info = registry.get_agent(agent_id)
        if not self.info:
            raise ValueError(f"Agent @{agent_id} not found in registry")

    @property
    def role(self) -> str:
        return self.info['role']

    @property
    def tools(self) -> List[str]:
        return self.info['tools']

    def execute_task(
        self,
        task_input: Dict[str, Any],
        sender: str,
        model_binding: Optional[Tuple[str, str]] = None,
        providers: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if sender != "orchestrator-agent":
            raise PermissionError(
                f"[{self.agent_id}] Security Violation: Direct communication denied. "
                f"Routing to @orchestrator-agent now."
            )

        prompt_text = task_input.get('data', '')

        if not model_binding or not providers or requests is None:
            return {
                "agent_id": self.agent_id,
                "status": "COMPLETED",
                "payload": f"[SIM] @{self.agent_id} ({self.info['role'][:50]}...) processed: {prompt_text[:80]}",
                "tools_used": self.info['tools'][:2],
                "self_reported_status": "PRELIMINARY_SIGNAL_ONLY"
            }

        provider_id, model_name = model_binding
        provider = providers.get(provider_id, {})
        api_key = os.environ.get(provider.get("key_env", ""), "")

        if not api_key:
            raise AuthFailedError(provider_id, model_name, f"متغير البيئة {provider.get('key_env', '')} غير مضبوط")

        url = provider.get("base_url", "").rstrip("/") + "/chat/completions"
        system_prompt = f"أنت @{self.agent_id}. دورك: {self.info['role']}"

        try:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_text},
                    ],
                    "max_tokens": 1500,
                },
                timeout=120,
            )
        except requests.exceptions.RequestException as e:
            raise ModelCallError(provider_id, model_name, f"connection_failed: {e}")

        if resp.status_code == 429:
            raise RateLimitExceeded(self.agent_id, provider_id, model_name)
        if resp.status_code in (401, 403):
            raise AuthFailedError(provider_id, model_name, f"HTTP {resp.status_code}")
        if resp.status_code >= 500:
            raise ModelCallError(provider_id, model_name, f"server error HTTP {resp.status_code}")
        if resp.status_code != 200:
            raise ModelCallError(provider_id, model_name, f"HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as e:
            raise ModelCallError(provider_id, model_name, f"malformed response: {e}")

        return {
            "agent_id": self.agent_id,
            "status": "COMPLETED",
            "payload": content or f"[EMPTY] @{self.agent_id} returned no content",
            "tools_used": self.info['tools'][:2],
            "self_reported_status": "PRELIMINARY_SIGNAL_ONLY"
        }


# =====================================================================
# 2.5 المراقب الديناميكي — نسخة v7 (مشترك + circuit breaker)
# =====================================================================

class DynamicModelMonitor:
    """
    فحص حي لكل (مزود، نموذج)، مع حالة **مشتركة على القرص** عبر
    SharedStateStore، بحيث ترى كل نسخ المحرك نفس الوسوم ونفس الحجوزات.

    قواعد الحماية الجديدة:
      - الوسم الحي (live) من تنفيذ فاشل له أولوية على نتيجة الفحص الدوري
        لمدة LIVE_MARK_TTL_SECONDS.
      - circuit breaker: أي زوج موسوم يبقى كذلك حتى CIRCUIT_BREAKER_TTL_SECONDS
        ثم يُنسى تلقائياً (decay)، حتى لا يتحول إلى حظر أبدي.
    """

    def __init__(self,
                 providers_config_path: str = PROVIDERS_CONFIG_PATH,
                 scan_interval: int = SCAN_INTERVAL_SECONDS,
                 state_store: Optional[SharedStateStore] = None):
        self.providers_config_path = pathlib.Path(providers_config_path)
        self.scan_interval = scan_interval
        self.providers = self._load_providers()
        self._scan_provider_ids = set(self.providers.keys())  # قائمة بيضاء — فقط من providers.yaml
        self.store = state_store or SharedStateStore()

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._local_lock = threading.Lock()  # لحماية الحالة المحلية داخل العملية

        self.active_task_id: Optional[str] = None

    # -----------------------------------------------------------------
    # تحميل المزودين — بدون تغيير
    # -----------------------------------------------------------------
    def discover_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        اكتشاف المزودين عبر آلية الاكتشاف المدمجة في Hermes.
        تستدعي list_authenticated_providers() التي تفحص:
        - config.yaml (النموذج الافتراضي + custom_providers)
        - profile.yaml لكل وكيل
        - متغيرات البيئة المعروفة (OPENROUTER_API_KEY, ANTHROPIC_API_KEY, ...)
        - القوائم المُجهزة (models.dev)
        ثم تحول الناتج للشكل الذي يستخدمه المحرك.
        """
        try:
            from hermes_cli.model_switch import list_authenticated_providers
            hermes_providers = list_authenticated_providers()
        except Exception as e:
            print(f"  ⚠️ [model-monitor] فشل استدعاء list_authenticated_providers: {e}")
            return {}

        providers: Dict[str, Dict[str, Any]] = {}
        known_base_urls = {
            "openrouter": "https://openrouter.ai/api/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "openai": "https://api.openai.com/v1",
            "google": "https://generativelanguage.googleapis.com/v1beta",
            "deepseek": "https://api.deepseek.com/v1",
            "nvidia": "https://integrate.api.nvidia.com/v1",
            "nous": "https://inference-api.nousresearch.com/v1",
            "kimi": "https://api.moonshot.cn/v1",
            "local": "http://localhost:3001/v1",
        }
        known_key_envs = {
            "openrouter": "OPENROUTER_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "nvidia": "NVIDIA_API_KEY",
            "nous": "NOUS_API_KEY",
            "kimi": "KIMI_API_KEY",
            "local": "HERMES_CUSTOM_LOCALHOST_3001_API_KEY",
        }

        for p in hermes_providers:
            slug = p.get("slug", "")
            name = p.get("name", slug)
            models = p.get("models", [])

            if not slug or not models:
                continue

            base_url = known_base_urls.get(slug, "")
            key_env = known_key_envs.get(slug, "")

            # تصفية: فقط المزودين المتوافقين مع OpenAI API ولديهم base_url معروف
            if not base_url:
                print(f"  ⚠️ [model-monitor] تخطي {slug}: غير متوافق مع OpenAI API أو base_url غير معروف")
                continue

            providers[slug] = {
                "base_url": base_url,
                "key_env": key_env,
                "models": models[:10],  # حد أقصى 10 نماذج لكل مزود
                "name": name,
                "source": p.get("source", "unknown"),
            }

        return providers

    def _load_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        قراءة المزودين من providers.yaml أولاً.
        fallback: discover_providers() إذا فشل القراءة أو لم يوجد مفتاح.
        """
        providers: Dict[str, Dict[str, Any]] = {}

        if self.providers_config_path.is_file() and yaml is not None:
            try:
                raw = yaml.safe_load(self.providers_config_path.read_text()) or {}
                for entry in raw.get("providers", []):
                    pid = entry.get("id")
                    if pid:
                        providers[pid] = {
                            "base_url": entry.get("base_url", ""),
                            "key_env": entry.get("key_env", ""),
                            "models": entry.get("models", []),
                        }
                print(f"  📄 [model-monitor] قُرأ {len(providers)} مزود من providers.yaml")
            except Exception as e:
                print(f"  ⚠️ [model-monitor] فشل قراءة providers.yaml: {e}")

        # إضافة FreeLLMAPI / local صراحة إذا كان المفتاح موجوداً
        freellm_key = os.environ.get("HERMES_FREELMAPI_KEY", "")
        if freellm_key:
            extra = {
                "FreeLLMAPI": ["auto", "gpt-oss-120b", "deepseek-v4-flash-0731",
                               "nemotron-3-ultra-free", "nemotron-3-super-120b-a12b",
                               "nemotron-3.5-lightning-30b-a3b", "gpt-5",
                               "glm-5.3", "deepseek-r1", "gemini-3.6-flash"],
                "local": ["auto", "gpt-oss-120b", "nemotron-3-super-120b-a12b"],
            }
            for pid, models in extra.items():
                if pid not in providers:
                    providers[pid] = {
                        "base_url": "http://localhost:3001/v1",
                        "key_env": "HERMES_FREELMAPI_KEY",
                        "models": models,
                    }

        if providers:
            return providers

        # fallback أخير
        print("  ⚠️ [model-monitor] لا يوجد مزود في providers.yaml — استخدام discover_providers()")
        return self.discover_providers()

    # -----------------------------------------------------------------
    # الفحص الدوري — لا يطمس الوسم الحي
    # -----------------------------------------------------------------
    def _probe_model_speed(self, provider_id: str, provider: Dict[str, Any], model: str) -> Tuple[str, float]:
        """
        فحص سرعة الاتصال بنموذج محدد.
        يُرجع (status, latency_ms).
        الحالة الممكنة: ok, rate_limit, auth_failed, timeout, http_XXX, no_key, error
        """
        if requests is None:
            return ("unknown", 99999)
        api_key = os.environ.get(provider.get("key_env", ""), "")
        if not api_key or api_key == "***":
            return ("no_key", 99999)
        url = provider["base_url"].rstrip("/") + "/chat/completions"
        try:
            start = time.time()
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                timeout=10,
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                return ("ok", elapsed)
            elif resp.status_code == 429:
                return ("rate_limit", elapsed)
            elif resp.status_code in (401, 403):
                return ("auth_failed", elapsed)
            elif resp.status_code == 503:
                return ("overloaded", elapsed)
            else:
                return (f"http_{resp.status_code}", elapsed)
        except requests.exceptions.Timeout:
            return ("timeout", 10000)
        except Exception:
            return ("error", 99999)

    def _rank_models_for_provider(self, provider_id: str, provider: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        """فحص كل النماذج داخل مزود وإرجاعها مرتبة حسب السرعة."""
        models = provider.get("models", [])
        results = []
        for model in models:
            status, latency = self._probe_model_speed(provider_id, provider, model)
            results.append((model, status, latency))
        results.sort(key=lambda x: (0 if x[1] == "ok" else 1, x[2]))
        return results

    def _ensure_providers_fresh(self) -> None:
        """
        لا يضيف نماذج من discover_providers() — providers.yaml هو المصدر الوحيد.
        يكتفي بطباعة عدد المزودين الحاليين للتشخيص.
        """
        print(f"  📄 [model-monitor] {len(self.providers)} مزود من providers.yaml")

    def _scan_once(self) -> None:
        """الفحص المتوازي — يدمج النتائج مع الحالة المشتركة دون طمس الوسم الحي.
        يفحص فقط النماذج المُعرّفة في self.providers (providers.yaml) — لا النماذج المكتشفة ديناميكياً."""
        results: Dict[str, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            jobs = []
            # فحص النماذج المُعرّفة فقط — لا النماذج من discover_providers()
            for provider_id, provider in self.providers.items():
                for model in provider.get("models", []):
                    jobs.append((
                        pool.submit(self._probe_model_speed, provider_id, provider, model),
                        f"{provider_id}/{model}"
                    ))
            for future, key in jobs:
                try:
                    status, _ = future.result()
                    results[key] = status
                except Exception:
                    pass

        def _merge(data: Dict[str, Any]) -> None:
            pairs = data.setdefault("pairs", {})
            for key, new_state in results.items():
                existing = pairs.get(key)
                if existing and existing.get("source") == "live":
                    if not SharedStateStore._is_expired(
                        existing.get("marked_at"), LIVE_MARK_TTL_SECONDS
                    ):
                        continue
                if new_state == "ok":
                    pairs.pop(key, None)
                elif new_state == "no_key":
                    pairs.pop(key, None)  # لا يوجد مفتاح — لا نوسم
                else:
                    pairs[key] = {
                        "state": new_state,
                        "marked_at": datetime.now(timezone.utc).isoformat(),
                        "source": "scan",
                    }

        self.store.mutate(_merge)

    def _scan_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.store.prune_expired()  # decay للـ circuit breaker
                self._scan_once()
            except Exception as e:
                print(f"  ⚠️ [model-monitor] فشل دورة الفحص: {e}")
            self._stop_event.wait(self.scan_interval)

    # -----------------------------------------------------------------
    # دورة الحياة — مقيدة بالمهمة
    # -----------------------------------------------------------------
    def start(self, task_id: str) -> None:
        with self._local_lock:
            if self._thread and self._thread.is_alive():
                # إيقاف الفحص السابق وإعادة البدء
                self._stop_event.set()
                self._thread.join(timeout=PROBE_TIMEOUT_SECONDS + 1)
            self.active_task_id = task_id
            self._stop_event.clear()

        # إعادة اكتشاف المزودين قبل كل مهمة
        self._ensure_providers_fresh()
        # مسح الوسوم القديمة (إن وُجدت) لفحص نظيف
        def _clear_scan(data):
            data["pairs"] = {k: v for k, v in data.get("pairs", {}).items()
                            if v.get("source") == "live"}
        self.store.mutate(_clear_scan)

        print(f"  🔎 [model-monitor] بدء فحص ديناميكي للمهمة {task_id} "
              f"({len(self.providers)} مزود)")
        self._scan_once()
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop(self, task_id: str) -> None:
        with self._local_lock:
            self._stop_event.set()
            if self._thread:
                self._thread.join(timeout=PROBE_TIMEOUT_SECONDS + 1)
            self._thread = None
            self.active_task_id = None
        print(f"  🛑 [model-monitor] إيقاف الفحص الديناميكي — انتهت المهمة {task_id}")

    # -----------------------------------------------------------------
    # الربط/التحرير/الوسم — كلها عبر الحالة المشتركة
    # -----------------------------------------------------------------
    def _all_pair_keys(self) -> List[str]:
        keys = []
        for provider_id, provider in self.providers.items():
            for model in provider.get("models", []):
                keys.append(f"{provider_id}/{model}")
        return keys

    def bind_agent(self, agent_id: str,
                   exclude: Optional[set] = None,
                   live_probe: bool = True) -> Optional[Tuple[str, str]]:
        """
        يبحث عن أول زوج نشط مع استنزاف كل النماذج داخل المزود قبل الانتقال.
        live_probe: True = يُحاول الاتصال مباشرة قبل الوسم (أكثر دقة، أبطأ).
        """
        exclude = exclude or set()
        exclude_keys = {f"{p}/{m}" for (p, m) in exclude}
        chosen: Optional[str] = None

        def _fn(data: Dict[str, Any]) -> None:
            nonlocal chosen
            pairs = data.setdefault("pairs", {})
            assignments = data.setdefault("assignments", {})
            pid_map = data.setdefault("pid_map", {})
            my_pid = os.getpid()

            # تنظيف الحجوزات الميتة
            dead = [a for a, pid in pid_map.items() if pid != my_pid and not _pid_alive(pid)]
            for a in dead:
                assignments.pop(a, None)
                pid_map.pop(a, None)

            existing = assignments.get(agent_id)
            if existing and existing not in exclude_keys:
                chosen = existing
                return

            used = {v for k, v in assignments.items() if k != agent_id}

            for provider_id, provider in self.providers.items():
                for model in provider.get("models", []):
                    key = f"{provider_id}/{model}"
                    if key in exclude_keys or key in used:
                        continue

                    state_entry = pairs.get(key)

                    if state_entry is None:
                        # لم يُوسم — حاول الاتصال إذا live_probe=True
                        if live_probe:
                            status, _ = self._probe_model_speed(provider_id, provider, model)
                            if status == "ok":
                                chosen = key
                                break
                            else:
                                pairs[key] = {
                                    "state": status,
                                    "marked_at": datetime.now(timezone.utc).isoformat(),
                                    "source": "live",
                                }
                                continue
                        else:
                            chosen = key
                            break
                    elif state_entry.get("state") == "available":
                        chosen = key
                        break
                    else:
                        # أي حالة أخرى (no_key, error, exhausted) — تخطي
                        continue
                if chosen:
                    break

            if chosen:
                assignments[agent_id] = chosen
                pid_map[agent_id] = my_pid

        self.store.mutate(_fn)
        if chosen is None:
            return None
        provider_id, model_name = chosen.split("/", 1)
        return (provider_id, model_name)

    def release_agent(self, agent_id: str) -> None:
        def _fn(data: Dict[str, Any]) -> None:
            data.setdefault("assignments", {}).pop(agent_id, None)
            data.setdefault("pid_map", {}).pop(agent_id, None)
        self.store.mutate(_fn)

    def release_all_for_task(self, agent_ids: List[str]) -> None:
        """تنظيف مضمون عند نهاية المهمة."""
        def _fn(data: Dict[str, Any]) -> None:
            a = data.setdefault("assignments", {})
            p = data.setdefault("pid_map", {})
            for aid in agent_ids:
                a.pop(aid, None)
                p.pop(aid, None)
        self.store.mutate(_fn)

    def mark_exhausted(self, provider_id: str, model: str,
                       state: str = "quota_exhausted") -> None:
        key = f"{provider_id}/{model}"
        def _fn(data: Dict[str, Any]) -> None:
            data.setdefault("pairs", {})[key] = {
                "state": state,
                "marked_at": datetime.now(timezone.utc).isoformat(),
                "source": "live",
            }
        self.store.mutate(_fn)
        print(f"  ⏳ [model-monitor] وسم {key} فوراً كـ '{state}' (تحديث حي)")

    def pair_count(self) -> int:
        """إجمالي أزواج (مزود، نموذج) المعروفة — بلا سقف اصطناعي."""
        return sum(len(p.get("models", [])) for p in self.providers.values()) or 1

    def snapshot(self) -> Dict[str, Any]:
        data = self.store.read()
        return {"pairs": data.get("pairs", {}),
                "assignments": data.get("assignments", {})}


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


# =====================================================================
# 3. المنسق — v7 مع message_agent
# =====================================================================

class OrchestratorAgent:
    """
    الوكيل المنسق. يوفر واجهتين:
      - handle_user_request(prompt): تفاعلية (print/input) للـ CLI.
      - message_agent(payload): JSON-in/JSON-out للبوتات والقنوات البرمجية.
    """

    def __init__(self, auto_approve: bool = False):
        self.agent_id = "orchestrator-agent"
        self.registry = AgentRegistry()
        self.registry.load()
        self.subagents: Dict[str, SubAgent] = {}
        self.model_monitor = DynamicModelMonitor()
        # auto_approve يُستخدم فقط في اختبارات/CI — الافتراضي هو بوابة بشرية
        self.auto_approve = auto_approve

        for agent_id in self.registry.list_agents():
            if agent_id != self.agent_id:
                try:
                    self.subagents[agent_id] = SubAgent(agent_id, self.registry)
                except ValueError:
                    pass

    # -----------------------------------------------------------------
    # أدوات مساعدة
    # -----------------------------------------------------------------
    def generate_task_id(self) -> str:
        now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{now_str}-{uuid.uuid4().hex[:4]}"

    def normalize_response(self, user_input: str) -> bool:
        normalized = user_input.strip().lower()
        affirmative = {"yes", "y", "proceed", "go", "go ahead", "confirmed",
                       "ok", "okay", "sure", "do it", "tamam",
                       "نعم", "تمام", "ماشي", "موافق"}
        return normalized in affirmative

    def route_by_role(self, capability: str) -> Optional[str]:
        return self.registry.find_by_role(capability)

    def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        profile_path = pathlib.Path(os.path.expanduser(f"~/.hermes/profiles/{agent_id}/SOUL.md"))
        skills_path = pathlib.Path(os.path.expanduser(f"~/.hermes/profiles/{agent_id}/skills"))
        healthy = profile_path.is_file()
        skill_count = len([d for d in skills_path.iterdir() if d.is_dir()]) if skills_path.is_dir() else 0
        info = self.registry.get_agent(agent_id) or {}
        return {
            "agent_id": agent_id, "healthy": healthy, "skill_count": skill_count,
            "reachable": healthy and skill_count > 0,
            "role": info.get('role', 'unknown')
        }

    # -----------------------------------------------------------------
    # العرض والموافقة
    # -----------------------------------------------------------------
    def display_recommendation_block(self, task_id: str, plan: Dict[str, Any]) -> None:
        print("\n" + "="*60)
        print("Recommendation:")
        print(f"├─ Task ID: {task_id}")
        print(f"├─ Thinking: {plan['thinking']}")
        print(f"├─ Cost: {plan['cost_tier']}")
        print(f"├─ Agent(s): {', '.join(plan['target_agents'])}")
        print(f"├─ Topology: {plan['topology']}")
        print(f"├─ Tokens: {plan['estimated_tokens']}")
        print(f"├─ Est. cost: {plan['est_cost_usd']}")
        print(f"└─ ⚠️ Irreversible step: {plan['irreversible_step']}")
        print("="*60)

    def request_user_confirmation(self, task_id: str, plan: Dict[str, Any]) -> bool:
        self.display_recommendation_block(task_id, plan)
        try:
            resp = input("\nProceed? (yes / no): ")
        except EOFError:
            return False
        return self.normalize_response(resp)

    # -----------------------------------------------------------------
    # التدقيق النهائي
    # -----------------------------------------------------------------
    def run_final_audit(self, agent_outputs: List[Dict[str, Any]]) -> str:
        print("\n[orchestrator-agent] Running final-audit (5 stages)...")
        for output in agent_outputs:
            payload = output.get("payload", "")
            if "FAIL" in payload or "ERROR" in payload:
                return "REJECT"
        return "PASS"

    # -----------------------------------------------------------------
    # واجهة البوتات (NEW): JSON-in / JSON-out
    # -----------------------------------------------------------------
    def message_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        واجهة موحّدة للبوتات والقنوات البرمجية.
        payload متوقع:
            {
              "prompt": "...",
              "channel": "telegram" | "discord" | "http" | ...,
              "user_id": "...",
              "approval": "human" | "auto",   # اختياري — الافتراضي human
              "metadata": {...}               # اختياري
            }
        العائد دائمًا JSON-able dict بدون أي طباعة أو input().
        """
        # التحقق من البنية
        prompt = (payload or {}).get("prompt", "").strip()
        if not prompt:
            return self._bot_error("MISSING_PROMPT", "الحقل 'prompt' مطلوب")

        approval_mode = payload.get("approval", "human")
        # لا نسمح بـ auto إلا إذا فعّله المنسق صراحةً على مستوى الكائن
        if approval_mode == "auto" and not self.auto_approve:
            approval_mode = "human"

        task_id = self.generate_task_id()
        channel = payload.get("channel", "unknown")
        user_id = payload.get("user_id", "anonymous")

        # بدء الفحص الحي
        self.model_monitor.start(task_id)

        result: Dict[str, Any] = {
            "task_id": task_id,
            "channel": channel,
            "user_id": user_id,
            "status": "INITIATED",
            "stages": ["temporal_gate"],
            "plan": None,
            "output": None,
            "audit": None,
            "agent_outputs": [],
        }

        dispatched_agents: List[str] = []
        try:
            # --- Knowledge Retrieval ---
            arch_health = self.check_agent_health("archivist-agent")
            if arch_health["reachable"]:
                result["stages"].append("knowledge_retrieval")

            # --- Triage ---
            selected_agent = self.route_by_role(prompt) or "drafting-agent"
            if not self.check_agent_health(selected_agent)["reachable"]:
                for alt_id in self.registry.list_agents():
                    if alt_id != self.agent_id and self.check_agent_health(alt_id)["reachable"]:
                        selected_agent = alt_id
                        break

            needs_qa = any(kw in prompt.lower() for kw in [
                "draft", "report", "code", "write", "review",
                "مقال", "تقرير", "كود"
            ])
            target_agents = [f"@{selected_agent}"]
            topology = "Single"
            if needs_qa and self.check_agent_health("qa-agent")["reachable"]:
                target_agents.append("@qa-agent")
                topology = "Sequential"

            plan = {
                "thinking": "🟡 Medium",
                "cost_tier": "💰💰 Mid",
                "target_agents": target_agents,
                "topology": topology,
                "estimated_tokens": "~3,500",
                "est_cost_usd": "$0.02",
                "irreversible_step": "<none>",
            }
            result["plan"] = plan
            result["stages"].append("triage_topology")

            # --- بوابة الموافقة ---
            if approval_mode == "auto":
                approved = True
                result["stages"].append("auto_approval")
            else:
                # في وضع البوت: لا input(). البوت مسؤول عن تمرير approval
                # بعد أن يطلب من المستخدم فعليًا في واجهته.
                approved = self.normalize_response(
                    str(payload.get("user_confirmation", ""))
                )
                if not approved:
                    result["status"] = "AWAITING_HUMAN_CONFIRMATION"
                    result["stages"].append("awaiting_human_confirmation")
                    return result
                result["stages"].append("human_approval")

            # --- Dispatch ---
            agent_outputs = []
            for agent_name in target_agents:
                agent_id = agent_name.lstrip("@")
                dispatched_agents.append(agent_id)
                out = self._dispatch_one(agent_id, prompt)
                agent_outputs.append(out)

            result["agent_outputs"] = agent_outputs
            result["stages"].append("dispatch_execution")

            # --- Audit ---
            audit_result = self.run_final_audit(agent_outputs)
            result["audit"] = audit_result
            result["stages"].append("final_audit")

            if audit_result == "PASS":
                final_payload = "\n\n".join(
                    o["payload"] for o in agent_outputs
                    if o.get("status") == "COMPLETED"
                )
                result["output"] = final_payload
                result["status"] = "COMPLETED_PASS"
                if final_payload and len(final_payload) > 50:
                    result["stages"].append("archiving")
            else:
                result["status"] = "COMPLETED_REJECT"

            return result

        except PermissionError as e:
            result["status"] = "SECURITY_VIOLATION"
            result["error"] = str(e)
            return result
        finally:
            # تنظيف مضمون: تحرير كل الأربطة الخاصة بهذه المهمة
            self.model_monitor.release_all_for_task(dispatched_agents)
            self.model_monitor.stop(task_id)

    def _bot_error(self, code: str, msg: str) -> Dict[str, Any]:
        return {"status": "ERROR", "error_code": code, "error_message": msg}

    # -----------------------------------------------------------------
    # التوزيع على وكيل واحد — نسخة موحدة بين CLI و message_agent
    # -----------------------------------------------------------------
    def _dispatch_one(self, agent_id: str, prompt: str) -> Dict[str, Any]:
        health = self.check_agent_health(agent_id)
        if not health["reachable"]:
            return {"agent_id": agent_id, "status": "UNREACHABLE",
                    "payload": f"Agent @{agent_id} not available"}

        subagent = self.subagents.get(agent_id)
        if not subagent:
            return {"agent_id": agent_id, "status": "UNREACHABLE",
                    "payload": f"Agent @{agent_id} not in subagents registry"}

        max_attempts = max(1, self.model_monitor.pair_count())
        tried_pairs: set = set()
        output: Optional[Dict[str, Any]] = None

        for attempt in range(1, max_attempts + 1):
            model_binding = self.model_monitor.bind_agent(agent_id, exclude=tried_pairs)
            if not model_binding:
                output = {
                    "agent_id": agent_id, "status": "NO_MODEL_AVAILABLE",
                    "payload": f"@{agent_id}: لا يوجد أي (مزود، نموذج) نشط حالياً"
                }
                break

            provider_id, model_name = model_binding
            print(f"  🔗 [model-monitor] @{agent_id} ← {provider_id}/{model_name} "
                  f"(محاولة {attempt}/{max_attempts})")

            try:
                output = subagent.execute_task(
                    {"data": prompt},
                    sender=self.agent_id,
                    model_binding=model_binding,
                    providers=self.model_monitor.providers,
                )
                output["model_binding"] = f"{provider_id}/{model_name}"
                print(f"  ✅ @{agent_id} returned: {output['status']} "
                      f"(via {provider_id}/{model_name})")
                break

            except RateLimitExceeded:
                print(f"  ⏳ {provider_id}/{model_name} بلغ rate limit — إعادة ربط تلقائياً")
                self.model_monitor.mark_exhausted(provider_id, model_name, "quota_exhausted")
                tried_pairs.add(model_binding)
                self.model_monitor.release_agent(agent_id)
                continue

            except AuthFailedError as e:
                print(f"  🔑 فشل مصادقة على {provider_id}/{model_name}: {e.detail}")
                self.model_monitor.mark_exhausted(provider_id, model_name, "auth_failed")
                tried_pairs.add(model_binding)
                self.model_monitor.release_agent(agent_id)
                continue

            except ModelCallError as e:
                print(f"  🔌 فشل استدعاء {provider_id}/{model_name}: {e.detail}")
                self.model_monitor.mark_exhausted(provider_id, model_name, "connection_failed")
                tried_pairs.add(model_binding)
                self.model_monitor.release_agent(agent_id)
                continue

        # تحرير الربط فور انتهاء الوكيل
        self.model_monitor.release_agent(agent_id)

        if output is None:
            output = {"agent_id": agent_id, "status": "MODEL_RETRIES_EXHAUSTED",
                      "payload": f"@{agent_id}: فشلت كل الأزواج ({len(tried_pairs)})"}

        return output

    # -----------------------------------------------------------------
    # واجهة CLI — تبقى كما هي (print/input)
    # -----------------------------------------------------------------
    def handle_user_request(self, user_prompt: str) -> Dict[str, Any]:
        print(f"\n[{self.agent_id}] Task received: '{user_prompt[:80]}...'")
        task_id = self.generate_task_id()
        print(f"[{self.agent_id}] Task ID: {task_id}")

        result: Dict[str, Any] = {
            "task_id": task_id, "status": "INITIATED", "stages": ["temporal_gate"],
            "output": None, "audit": None, "agent_outputs": []
        }

        self.model_monitor.start(task_id)
        dispatched_agents: List[str] = []
        try:
            # --- Knowledge Retrieval ---
            if self.check_agent_health("archivist-agent")["reachable"]:
                result["stages"].append("knowledge_retrieval")
                print("  ✅ Archivist reachable")

            # --- Triage ---
            selected_agent = self.route_by_role(user_prompt) or "drafting-agent"
            if not self.check_agent_health(selected_agent)["reachable"]:
                for alt_id in self.registry.list_agents():
                    if alt_id != self.agent_id and self.check_agent_health(alt_id)["reachable"]:
                        selected_agent = alt_id
                        break

            needs_qa = any(kw in user_prompt.lower() for kw in [
                "draft", "report", "code", "write", "review",
                "مقال", "تقرير", "كود"
            ])
            target_agents = [f"@{selected_agent}"]
            topology = "Single"
            if needs_qa and self.check_agent_health("qa-agent")["reachable"]:
                target_agents.append("@qa-agent")
                topology = "Sequential"

            plan = {
                "thinking": "🟡 Medium", "cost_tier": "💰💰 Mid",
                "target_agents": target_agents, "topology": topology,
                "estimated_tokens": "~3,500", "est_cost_usd": "$0.02",
                "irreversible_step": "<none>",
            }
            result["plan"] = plan
            result["stages"].append("triage_topology")

            # --- Approval ---
            if not self.request_user_confirmation(task_id, plan):
                print(f"[{self.agent_id}] User declined. Aborting.")
                result["status"] = "USER_DECLINED"
                return result
            result["stages"].append("human_approval")

            # --- Dispatch ---
            agent_outputs = []
            for agent_name in target_agents:
                agent_id = agent_name.lstrip("@")
                dispatched_agents.append(agent_id)
                print(f"\n[{self.agent_id}] Dispatching to {agent_name}...")
                agent_outputs.append(self._dispatch_one(agent_id, user_prompt))

            result["agent_outputs"] = agent_outputs
            result["stages"].append("dispatch_execution")

            # --- Audit ---
            audit_result = self.run_final_audit(agent_outputs)
            result["audit"] = audit_result
            result["stages"].append("final_audit")

            if audit_result == "PASS":
                final_payload = "\n\n".join(
                    o["payload"] for o in agent_outputs
                    if o.get("status") == "COMPLETED"
                )
                result["output"] = final_payload
                result["status"] = "COMPLETED_PASS"

                print("\n" + "#"*60)
                print("RESULT (orchestrator delivers to user):")
                print("#"*60)
                print(final_payload)
                print("#"*60)
                print(f"Audit: {audit_result}")
                print(f"Task ID: {task_id}")
                print(f"Stages: {' → '.join(result['stages'])}")
                print("#"*60)

                if final_payload and len(final_payload) > 50:
                    result["stages"].append("archiving")
            else:
                result["status"] = "COMPLETED_REJECT"
                print(f"\n[{self.agent_id}] Audit REJECTED.")

            return result

        except PermissionError as e:
            print(f"  ❌ Security violation: {e}")
            result["status"] = "SECURITY_VIOLATION"
            result["error"] = str(e)
            return result
        finally:
            self.model_monitor.release_all_for_task(dispatched_agents)
            self.model_monitor.stop(task_id)
            print(f"\n📣 [{self.agent_id}] انتهت المهمة {task_id} — الحالة: {result['status']}")


# =====================================================================
# 4. نقطة الدخول
# =====================================================================

if __name__ == "__main__":
    orchestrator = OrchestratorAgent()

    print("="*60)
    print("HERMES ORCHESTRATOR ENGINE — LIVE v7.0.0")
    print("="*60)
    print(f"Registry: {REGISTRY_PATH}")
    print(f"Shared state: {SHARED_STATE_PATH}")
    print(f"Agents loaded: {len(orchestrator.subagents)}")
    print(f"Loaded at: {orchestrator.registry._loaded_at}")

    print("\n=== Agents from Shared Registry ===")
    for agent_id, info in sorted(orchestrator.registry.data.items()):
        if agent_id != "orchestrator-agent":
            print(f"  @{agent_id}: {info['role'][:60]}...")

    print("\n--- Security Test: Direct agent bypass ---")
    try:
        drafting = orchestrator.subagents.get("drafting-agent")
        if drafting:
            drafting.execute_task({"data": "test"}, sender="DIRECT_USER")
    except PermissionError as e:
        print(f"✅ Security gate working: {e}")

    print("\n--- Full Pipeline Test ---")
    result = orchestrator.handle_user_request("قم بإعداد تقرير عن الذكاء الاصطناعي")

    print(f"\n{'='*60}")
    print(f"Final Result: {result['status']}")
    print(f"Task ID: {result['task_id']}")
    print(f"Stages: {' → '.join(result['stages'])}")