# 🦊 CLARISSA GitLab Workflow - ورقة مرجعية

> **TL;DR:** Issue ← Branch ← Commit ← MR ← Merge ← الـ Issue يُغلق تلقائياً

---

## 🔄 سير العمل في ٥ خطوات

## 1️⃣ اختيار Issue من اللوحة

```
Project → Plan → Issue Boards
```

- خذ issue من عمود **Ready**
- انقله إلى **In Progress**

## 2️⃣ إنشاء Branch

```bash
git checkout -b 42-short-description
```

## 3️⃣ Commit مع إشارة للـ Issue

```bash
git commit -m "type: description #42"
```

| Prefix | Usage |
|--------|-------|
| `feat:` | ميزة جديدة |
| `fix:` | إصلاح خطأ |
| `docs:` | توثيق |
| `chore:` | صيانة |
| `refactor:` | إعادة هيكلة |
| `test:` | اختبارات |

## 4️⃣ إنشاء Merge Request

```bash
git push -u origin 42-short-description
```

**Closes #42 يُغلق الـ issue تلقائياً عند الدمج!**

## 5️⃣ مراجعة ودمج

1. المراجع يفحص الكود
2. عند الموافقة: اضغط **Merge**
3. الـ Issue يُغلق تلقائياً!

---

## 🔗 الكلمات السحرية

| Keyword | Effect |
|---------|--------|
| `Closes #42` | Auto-close on merge |
| `Fixes #42` | Auto-close on merge |
| `#42` | Link only |

---

## 🚫 الممنوعات


---

## ✅ قائمة التحقق قبل الدمج


---

*هل لديك سؤال؟ أنشئ issue بالوسم help-wanted*