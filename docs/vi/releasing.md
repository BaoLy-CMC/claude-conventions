# Sửa convention, phát hành, và cập nhật

English: [../en/releasing.md](../en/releasing.md) | Về [README](../../README.vi.md)

## Cách sửa một convention

1. Xác định thay đổi thuộc đâu:
   - Rule trong baseline always-on -> sửa `plugins/finx-core/canonical/conventions.json`. Không bao giờ sửa tay `hooks/baseline-rules.md` hay `canonical/out/` - chúng được sinh ra.
   - Một skill -> `plugins/finx-core/skills/<name>/SKILL.md`.
   - Một hook -> `plugins/finx-core/hooks/`.
2. Regenerate (chỉ cần khi sửa canonical; `release.sh` cũng làm việc này):
   ```bash
   python3 plugins/finx-core/canonical/generate.py
   ```
3. Phát hành (mục kế).

Mỗi section canonical mang một danh sách `kiro` quyết định nó xuất hiện ở file Kiro steering nào; danh sách rỗng nghĩa là chỉ vào Claude baseline (dùng cho phần communication style, vốn không phải convention code của Kiro).

## Versioning

Semantic versioning `MAJOR.MINOR.PATCH`:

- `MAJOR` - thay đổi breaking một rule, hành vi hook, hoặc lệnh mà team phải phản ứng.
- `MINOR` - thêm skill, hook, hoặc rule mới; tương thích ngược.
- `PATCH` - chỉnh câu chữ, sửa lỗi, chỉnh ngưỡng.

Version nằm ở hai file và phải khớp: `plugins/finx-core/.claude-plugin/plugin.json` và entry `finx-core` trong `.claude-plugin/marketplace.json`. Dùng `release.sh` để không lệch.

## Quy trình release (maintainer)

1. Sửa (như trên).
2. Bump + regenerate trong một bước:
   ```bash
   ./release.sh 0.21.0
   ```
   Nó đặt version ở cả hai manifest và chạy generator.
3. Thêm section `[0.21.0]` vào `CHANGELOG.md` mô tả sửa gì và vì sao.
4. Commit, tag, push:
   ```bash
   git add -A
   git commit -m "feat: <sửa gì> (finx-core 0.21.0)"
   git tag v0.21.0
   git push && git push --tags
   ```
5. Thông báo version và lý do một dòng.

## Quy trình update (engineer)

Claude Code tự cập nhật plugin lúc khởi động: khi restart nó `git pull` marketplace và lấy version mới (vì mỗi release đều bump version). Nên cách thường là chỉ cần **restart Claude Code**. Hook `version-notice` sẽ in ở đầu phiên rằng finx-core đã lên version mới và thay đổi gì.

Muốn lấy ngay, không đợi restart:

```
/plugin marketplace update finx-conventions
/plugin update finx-core
/reload-plugins
```

Sau cả hai cách, mở session mới (hoặc `/clear`) để hook `SessionStart` nạp lại baseline mới. Việc đọc hook và config (`flow-gate`, `context-watch`) có hiệu lực ở tool call kế tiếp, không cần reload.

## Cài đặt lần đầu

```
/plugin marketplace add <internal-git-url>
/plugin install finx-core@finx-conventions
```

Có thể chạy `/flow-setup`; không thì dùng mặc định chuẩn.

## Update không tự làm được gì

- Baseline `SessionStart` chỉ refresh ở phiên mới/clear/resume, không giữa phiên.
- Override `flow-config.json` cá nhân không bị đụng; khóa config mới fallback về mặc định tới khi kỹ sư opt-in.
- Lệnh cá nhân đã archive (`~/.claude/_archived-commands/`) không được khôi phục.

## Rollback

Revert commit release và cắt patch version mới, hoặc pin tag cũ. Không xóa tag đã publish.
