# 🦊 CLARISSA GitLab Workflow - Tờ Ghi Nhớ

> **TL;DR:** Issue → Branch → Commit → MR → Merge → Issue tự động đóng

---

## 🔄 Workflow trong 5 Bước

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Chọn   │───▶│  2. Tạo    │───▶│ 3. Commit  │───▶│  4. Tạo    │───▶│ 5. Review  │
│   Issue    │    │   Branch   │    │   & Push   │    │    MR      │    │  & Merge   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 1️⃣ Chọn Issue từ Board

```
Project → Plan → Issue Boards
```

- Lấy issue từ cột **Ready**
- Chuyển sang **In Progress**

---

## 2️⃣ Tạo Branch

```bash
# LUÔN bắt đầu bằng số issue!
git checkout -b 42-mo-ta-ngan
```

| ✅ Tốt | ❌ Xấu |
|--------|--------|
| `42-add-login` | `my-branch` |
| `12-fix-bug` | `test123` |
| `7-update-docs` | `changes` |

---

## 3️⃣ Commit với tham chiếu Issue

```bash
git commit -m "type: mô tả #42"
```

### Các prefix Conventional Commits:

| Prefix | Sử dụng |
|--------|---------|
| `feat:` | Tính năng mới |
| `fix:` | Sửa lỗi |
| `docs:` | Tài liệu |
| `chore:` | Bảo trì |
| `refactor:` | Tái cấu trúc |
| `test:` | Tests |

### Ví dụ:

```bash
git commit -m "feat: thêm xác thực user #42"
git commit -m "fix: sửa lỗi null pointer #15"
git commit -m "docs: cập nhật hướng dẫn #7"
```

---

## 4️⃣ Tạo Merge Request

```bash
git push -u origin 42-mo-ta-ngan
```

### Template mô tả MR:

```markdown
## Tóm tắt
Mô tả ngắn về thay đổi.

## Thay đổi
- Mục 1
- Mục 2

## Liên quan
Closes #42

## Checklist
- [ ] Code đã test
- [ ] Tài liệu đã cập nhật
```

**Quan trọng:** `Closes #42` tự động đóng issue khi merge!

---

## 5️⃣ Review & Merge

1. Reviewer kiểm tra code
2. Khi approve: Click **Merge**
3. ✅ Issue tự động đóng!

---

## 🔗 Từ khóa kỳ diệu

Những từ này trong commit hoặc MR tự động đóng issues:

| Từ khóa | Hiệu quả |
|---------|----------|
| `Closes #42` | Đóng issue khi merge |
| `Fixes #42` | Đóng issue khi merge |
| `Resolves #42` | Đóng issue khi merge |
| `#42` | Chỉ liên kết |

---

## 🚫 Những điều cấm kỵ

1. ❌ Push trực tiếp vào `main`
2. ❌ Commit không có tham chiếu issue (`#42`)
3. ❌ Commit secrets/mật khẩu
4. ❌ MR khổng lồ với 50 files
5. ❌ MR không có `Closes #X`

---

## ✅ Checklist trước Merge

- [ ] Tên branch có số issue
- [ ] Commits theo Conventional Commits
- [ ] Commits tham chiếu issue (`#42`)
- [ ] MR có `Closes #42`
- [ ] CI pipeline xanh
- [ ] Label issue đặt thành `workflow::review`

---

## 🔗 Links nhanh

| Tài nguyên | URL |
|------------|-----|
| Issue Board | `/-/boards` |
| Tất cả Issues | `/-/issues` |
| Merge Requests | `/-/merge_requests` |
| Slides tương tác | `docs/guides/contributing/workflow-slides-vi.html` |

---

*Có câu hỏi? Tạo issue với label `help-wanted`*
