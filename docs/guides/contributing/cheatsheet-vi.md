# 🦊 CLARISSA GitLab Workflow - Tờ ghi nhớ

> **TL;DR:** Issue → Branch → Commit → MR → Merge → Issue tự động đóng

---

## 🔄 Workflow trong 5 bước

## 1️⃣ Chọn Issue từ Board

```
Project → Plan → Issue Boards
```

- Lấy issue từ cột **Ready**
- Chuyển sang **In Progress**

## 2️⃣ Tạo Branch

```bash
git checkout -b 42-short-description
```

## 3️⃣ Commit với tham chiếu Issue

```bash
git commit -m "type: description #42"
```

| Prefix | Usage |
|--------|-------|
| `feat:` | Tính năng mới |
| `fix:` | Sửa lỗi |
| `docs:` | Tài liệu |
| `chore:` | Bảo trì |
| `refactor:` | Tái cấu trúc code |
| `test:` | Tests |

## 4️⃣ Tạo Merge Request

```bash
git push -u origin 42-short-description
```

**Closes #42 tự động đóng issue khi merge!**

## 5️⃣ Review & Merge

1. Reviewer kiểm tra code
2. Khi được duyệt: Nhấn **Merge**
3. Issue tự động đóng!

---

## 🔗 Từ kỳ diệu

| Keyword | Effect |
|---------|--------|
| `Closes #42` | Auto-close on merge |
| `Fixes #42` | Auto-close on merge |
| `#42` | Link only |

---

## 🚫 Những điều cấm kỵ


---

## ✅ Checklist trước khi Merge


---

*Có câu hỏi? Tạo issue với label help-wanted*