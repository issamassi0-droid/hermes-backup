# النظام الوزاري متعدد الوكلاء v1.6.0

> نظام ذكاء اصطناعي متعدد الوكلاء — بنية من ثلاث طبقات

---

## التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/issamassi0-droid/hermes-pipeline-dotfiles.git
cd hermes-pipeline-dotfiles

# تشغيل الإعداد (سحب + دمج + تحقق)
bash setup.sh --import
```

---

## الاستخدام

### تشغيل مهمة كاملة

```bash
# Tier 2 — بحث + استراتيجية + كتابة + تدقيق + نشر
python3 system/cabinet-office.py run "ابحث عن تطورات الذكاء الاصطناعي" --tier tier_2

# Tier 3 — تحليل شامل مع فيديو
python3 system/cabinet-office.py run "حلل تجارب المستخدمين مع herdr" --tier tier_3

# Tier 1 — بحث سريع
python3 system/cabinet-office.py run "ما هو نموذج ling-3.0-flash؟" --tier tier_1
```

### أوامر النظام

```bash
# حالة النظام
python3 system/cabinet-office.py status

# فحص صحي شامل
python3 system/cabinet-office.py health

# تقييم الجودة
python3 system/cabinet-office.py quality

# إزالة التكرار
python3 system/cabinet-office.py dedup findings.json

# حالة الميزانية
python3 system/cabinet-office.py budget

# نبض الموجه
python3 system/cabinet-office.py heartbeat --check

# التحقق من ملف
python3 system/cabinet-office.py validate output.json --agent writer --stage draft

# فحص تصعيد
python3 system/cabinet-office.py escalation high_factual_error

# تتبع تجاوز بشري
python3 system/cabinet-office.py override --mission m001 --reason "rejected draft"
```

---

## المستويات

| المستوى | الاستخدام | الوقت المُقدَّر |
|---|---|---|
| Tier 0 | قرار فوري (المنظّم فقط) | ~11 ثانية |
| Tier 1 | بحث سريع ونشر | ~44 ثانية |
| Tier 2 | بحث + استراتيجية + تدقيق | ~2 دقيقة 40 ثانية |
| Tier 3 | تحليل شامل مع فيديو وتغذية راجعة | ~5 دقائق 20 ثانية |

---

## البنية

```
system/
├── registry.json # سجل 11 وكيل
├── protocol.md # بروتوكول التواصل
├── routing.yaml # قواعد التوجيه
├── quality-charter.md # ميثاق الجودة
├── ledger-schema.json # مخطط المهام
├── evolution.md # حلقة التطور
├── constitutional.md # المبادئ السبعة
├── quality-metrics.md # مقاييس الجودة
├── escalation-criteria.md # محفزات التصعيد
├── architect-failover.md # تجاوز فشل المنظّم
├── system-health.md # لوحة الصحة
├── model-gateway.md + .sh # بوابة النماذج
├── model-registry.json # سجل النماذج
├── cabinet-office.py # واجهة موحدة (12 أمر)
├── bootstrap.sh # تشغيل/تحقق
└── scripts/
 ├── protocol-engine.py # محرك البروتوكول
 ├── context-budget.py # حاسبة السياق
 ├── architect-heartbeat.py # نبض الموجه
 ├── output-validator.py # مُحقّق المخرجات
 ├── dedup.py + dedup-v2.py # إزالة التكرار
 ├── quality-assessment-v2.py # تقييم الجودة
 └── escalation-system-health.py # تصعيد + صحة
```

---

## الوكلاء الأحد عشر

| الوكيل | الدور |
|---|---|
| @architect | المُنسِّق الوحيد |
| @omni-researcher | البحث الشامل |
| @deep-dive | البحث في يوتيوب |
| @strategist | تحويل البحث لخطة |
| @draft-writer | كتابة المسودة |
| @editor-qa | التحقق المستقل |
| @publisher | النشر |
| @analytics | قياس الأداء |
| @bot-maker | إنشاء وكلاء جدد |
| @omarchy | إدارة النظام |
| @scout | مراقبة المصادر |

---

## المقاييس

| المقياس | القيمة | الهدف |
|---|---|---|
| factual_error_rate | 0.0% | < 5% |
| source_verification_rate | 100% | > 90% |
| human_override_rate | 2 | < 20 |

> ⚠️ المقاييس الحالية محسوبة على بيانات اصطناعية — تحتاج قياساً مستقلاً.

---

## الترخيص

MIT — مفتوح المصدر، بدون رسوم.
