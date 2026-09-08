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

1. Sửa (như trên) và **commit với message conventional** (`feat:`, `fix:`, `docs:`, ...) - CHANGELOG được sinh nháp từ đây.
2. Bump + regenerate + sinh nháp CHANGELOG + commit + tag, trong một bước:
   ```bash
   ./release.sh 0.23.0
   ```
   Đặt version ở cả hai manifest, chạy generator, sinh nháp entry `[0.23.0]` từ các conventional commit kể từ tag gần nhất, commit đúng những file đó với message `chore: release finx-core 0.23.0`, và tạo tag `v0.23.0`.

   **Nó không push.** Chưa push thì chưa release.
3. **Tinh chỉnh** entry nháp bằng skill `write-changelog` - biến dòng commit cụt thành ghi chú user-facing nói rõ sửa gì và vì sao. Amend vào commit release.
4. Release khi sẵn sàng:
   ```bash
   git push origin main && git push origin v0.23.0
   ```

> **Push `main` mới là release.** Bản clone marketplace trên máy mỗi engineer bám nhánh mặc định chứ không bám tag — nó đọc version từ `.claude-plugin/marketplace.json` trên `main`. Tag chưa push, hoặc giữ lại chưa push, nghĩa là chưa ai có. Ngược lại, bất kỳ push nào lên `main` mang theo `marketplace.json` đã bump là ship ngay lập tức.

Nếu entry CHANGELOG được viết tay dưới `## [Unreleased]`, đổi tiêu đề thành `## [<version>] - <ngày>` **trước** khi chạy `release.sh` — `changelog.sh` bỏ qua version đã tồn tại, nhờ vậy phần viết tay không bị bản sinh tự động đè lên.

CHANGELOG là hybrid: `changelog.sh` sinh nháp deterministic từ commit; skill `write-changelog` thêm văn xuôi. Chạy `./changelog.sh <version>` riêng để (tái) sinh nháp mà không bump.

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

Rồi mở phiên mới và chạy `/finx-core:onboarding` — tour có hướng dẫn về plugin làm gì và tuỳ chọn nào là opt-in. Cuối tour skill này cũng mời chạy `flow-setup` và `statusline-setup`; không chạy thì dùng mặc định chuẩn.

## Update không tự làm được gì

- Baseline `SessionStart` chỉ refresh ở phiên mới/clear/resume, không giữa phiên.
- Override `flow-config.json` cá nhân không bị đụng; khóa config mới fallback về mặc định tới khi kỹ sư opt-in.
- Lệnh cá nhân đã archive (`~/.claude/_archived-commands/`) không được khôi phục.

## Rollback

Revert commit release và cắt patch version mới, hoặc pin tag cũ. Không xóa tag đã publish.
