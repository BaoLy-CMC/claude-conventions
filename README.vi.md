# FinX Claude Conventions

English: [README.md](README.md)

Một plugin [Claude Code](https://claude.com/claude-code) dùng chung (`finx-core`) mã hóa bộ chuẩn kỹ thuật backend của FinX thành các rule, skill và hook máy kiểm được, để Claude Code của mọi kỹ sư hành xử như nhau. Java 21/25, Spring Boot 3/4, ngân hàng tuân thủ SBV.

## Bắt đầu nhanh

```
/plugin marketplace add <internal-git-url>
/plugin install finx-core@finx-conventions
/reload-plugins
```

Mở session mới để nạp baseline always-on. Có thể chạy `/flow-setup` để tùy biến; không thì dùng mặc định chuẩn.

## Nhìn tổng thể

| Tầng | Làm gì | Ở đâu |
|------|--------|-------|
| Baseline | Rule always-on nạp mỗi phiên | Hook `SessionStart` (sinh từ canonical) |
| Guard | Chặn edit sai trước khi ghi | Các hook `PreToolUse` |
| Skills | Playbook theo nhu cầu (review, flow, tạo/soạn) | `skills/` |
| Flow | `explore -> plan -> execute -> review -> reset` | Skill `flow` + state `.finx/` |
| Theo kỹ sư | Trình bày opt-in: 3 output style + statusline theo flow | `output-styles/`, `statusline-setup` |

## Kiến trúc (một hình)

```
Confluence space EN            <- nguồn chuẩn (người đọc)
        |
        v
canonical/conventions.json --generate.py--> Kiro steering (canonical/out/kiro/*.md)
        |                                    Claude baseline (hooks/baseline-rules.md)
        v
+------------------- plugin finx-core -------------------+
|  baseline : SessionStart nạp rule mỗi phiên            |
|  hooks    : PreToolUse guard + flow-gate;              |
|             UserPromptSubmit context-watch; PreCompact |
|  skills   : review / flow / tạo-soạn (theo nhu cầu)    |
|  flow     : explore->plan->execute->review->reset      |
+--------------------------------------------------------+
```

## Tài liệu

- [Tổng quan](docs/vi/overview.md) - mô hình tư duy và cách các mảnh ghép lại.
- [Rules](docs/vi/rules.md) - bộ rule baseline always-on.
- [Reference](docs/vi/reference.md) - từng skill và hook.
- [Flow](docs/vi/flow.md) - quy trình phát triển, gate, context-watch, quản lý plan.
- [Releasing](docs/vi/releasing.md) - cách sửa convention, phát hành, và cập nhật.

## Nguồn chuẩn

Văn bản chuẩn nằm ở Confluence, space `EN` (Engineering), trang hub "Backend - Conventions & Standards". Plugin mã hóa phần ép buộc được và trích dẫn trang nguồn. Muốn sửa rule: sửa `canonical/conventions.json`, chạy generator, phát hành - xem [Releasing](docs/vi/releasing.md).

## Trạng thái

`0.24.0`. 18 skill, 4 hook event, flow đầy đủ với gate tool-agnostic, quản lý plan, thông báo cập nhật version, generator canonical -> Kiro/Claude, cùng phần trình bày opt-in theo kỹ sư (3 output style + statusline theo flow). Lịch sử trong [CHANGELOG.md](CHANGELOG.md).
