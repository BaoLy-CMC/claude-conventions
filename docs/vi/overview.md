# Tổng quan

English: [../en/overview.md](../en/overview.md) | Về [README](../../README.vi.md)

Trang này là mô hình tư duy: plugin gồm những gì và các phần ghép với nhau ra sao.

## Ý tưởng

Confluence giữ chuẩn gốc (văn bản, cho người đọc). Plugin không sao chép lại văn bản đó; nó **mã hóa phần ép buộc được** để Claude Code áp dụng tự động và giống nhau cho mọi người. Một nguồn sinh ra hai đầu tiêu thụ: Claude baseline và file steering của AWS Kiro.

```
Confluence space EN            <- nguồn chuẩn (người đọc)
        |
        v
canonical/conventions.json
        |
        +-- generate.py --> canonical/out/kiro/*.md      (Kiro steering)
        |               --> hooks/baseline-rules.md      (Claude baseline always-on)
        v
plugin finx-core
```

Sửa convention một lần trong `canonical/conventions.json`; generator giữ Claude baseline và file Kiro đồng bộ. Không lệch giữa hai kênh AI.

## Bốn tầng

```
+------------------------------------------------------------+
| 1. BASELINE (always-on)                                    |
|    Khối rule ngắn được nạp đầu mỗi phiên bởi hook          |
|    SessionStart. Principles, rule code, rule ngân hàng,    |
|    rule theo version runtime.                              |
+------------------------------------------------------------+
| 2. GUARD (hook, tự động)                                   |
|    PreToolUse chặn edit sai trước khi ghi (var trong code  |
|    mới, double cho tiền, System.out, secret) và ép flow    |
|    (flow-gate). UserPromptSubmit theo dõi context;         |
|    PreCompact chụp nhanh state.                            |
+------------------------------------------------------------+
| 3. SKILLS (theo nhu cầu)                                   |
|    Playbook Claude nạp theo ngữ cảnh: review, flow,        |
|    tạo-soạn (scaffold, docs, changeset).                   |
+------------------------------------------------------------+
| 4. FLOW (opt-in theo repo)                                 |
|    explore -> plan -> execute -> review -> reset, state ở  |
|    .finx/ và gate đòi plan được duyệt trước khi viết code  |
|    production non-trivial.                                 |
+------------------------------------------------------------+
```

## Vì sao dùng hook, không dùng CLAUDE.md

Plugin Claude Code không tự nạp `CLAUDE.md`. Nên baseline always-on được giao bởi hook `SessionStart` - nó in `baseline-rules.md` (đã sinh) vào phiên. Phần chi tiết không always-on; chỉ nạp khi một skill được kích hoạt, giữ context nhỏ.

## Always-on và theo nhu cầu

- **Always-on** (mỗi phiên): rule baseline.
- **Tự động** (khi có hành động liên quan): các hook guard và context-watch.
- **Theo nhu cầu** (khi liên quan hoặc được yêu cầu): các skill.

## Opt-in và tích hợp

Flow là opt-in theo session: session không có flow state không bao giờ bị gate, nên tool cá nhân và plugin khác sống chung được. Các tính năng ngoài flow (baseline, guard, review, docs, rule runtime) áp bất kể bạn plan/execute bằng gì. Xem [Flow](flow.md), mục "Tích hợp với công cụ plan/execute khác".

## Đi tiếp

- Bản thân các rule: [Rules](rules.md).
- Từng skill và hook: [Reference](reference.md).
- Quy trình phát triển: [Flow](flow.md).
- Sửa convention và phát hành: [Releasing](releasing.md).
