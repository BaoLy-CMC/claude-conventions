# Flow

English: [../en/flow.md](../en/flow.md) | Về [README](../../README.vi.md)

Vòng lặp phát triển được ép: `explore -> plan -> execute -> review -> reset`. Nó giữ việc non-trivial có kỷ luật (plan được duyệt trước khi code) và sống sót qua phiên dài (lưu và resume theo context).

## Các phase

Điều bằng một lệnh, `/flow <phase>` - một lệnh duy nhất để không đụng các lệnh `explore/plan/execute/reset` cá nhân.

| Phase | Lệnh | Diễn ra |
|-------|------|---------|
| explore | `/flow explore [task]` | Vẽ scope (controller -> service -> repository, việc tương tự trước, file ảnh hưởng). Không edit. |
| plan | `/flow plan` | Tạo/kích hoạt plan trong `.finx/plans/`, viết kiến trúc + blueprint từng bước, xin duyệt. |
| execute | `/flow execute` | Cần tín hiệu sẵn-sàng-execute (bên dưới). Hiện thực theo plan, 1-2 file mỗi batch. |
| review | `/flow review` | Chạy cổng `pre-ship`. Sửa CRITICAL/HIGH. |
| reset | `/flow reset` | Lưu `state_summary.md` + MemPalace, archive plan đã xong, về idle. |
| status | `/flow status` | Hiện phase, active plan, task. |

## State (trong `.finx/`)

- `flow.json` - `{ phase, activePlan, task, updated }`. Flow-gate đọc file này.
- `plans/NNN-slug/plan.md` - mỗi plan một thư mục, frontmatter `status: draft|approved|in-progress|done|abandoned`. Một active plan tại một thời điểm; guard tối đa 3 active với auto-archive plan đã xong (xem skill `plans`).
- `state_summary.md` - con trỏ resume dễ bay hơi (phase, done, remaining, next action). State bền nằm ở `plan.md`, `git diff`, và code.

## Ép buộc (flow-gate)

Một hook `PreToolUse` chặn edit production Java (`**/src/main/**/*.java`) khi flow đang chạy nhưng chưa sẵn sàng và thay đổi là non-trivial (nhiều hơn `trivialMaxLines`, mặc định 30). Các mức (đặt qua `/flow-setup`):

- `hybrid` (mặc định) - chặn edit production non-trivial khi chưa sẵn sàng; edit nhỏ cho qua.
- `hard` - chặn mọi edit production khi chưa sẵn sàng.
- `guided` - theo dõi flow, không bao giờ chặn.
- `off` - tắt.

Opt-in: repo không có `.finx/flow.json` không bao giờ bị gate. Thoát chặn nhầm bằng `FINX_SKIP_HOOKS=1`.

## Phiên dài: context-watch và reset

- `UserPromptSubmit` ước lượng % context từ transcript. Ở ngưỡng (mặc định 65%) nó hỏi nên `/compact`, save-and-clear-and-reload, hay tiếp tục. Cảnh báo một lần mỗi bucket 10%.
- Save-and-reload ghi `state_summary.md`; sau `/clear`, hook `SessionStart` nạp lại kèm banner RESUME để phiên mới tiếp đúng phase.
- `PreCompact` ghi snapshot dự phòng trước khi auto-compact ngoài ý muốn.

Ưu tiên `/compact` ở ngưỡng khi được (native, tự giữ phase); dùng clear-and-reload khi context bị nhiễu.

## Tích hợp với công cụ plan/execute khác

Flow tích hợp qua artifact state dùng chung, không phải bằng cách sở hữu các lệnh, nên plugin và tool cá nhân sống chung được.

- **Opt-in**: không có `.finx/flow.json` nghĩa là không gate.
- **Tính năng độc lập flow** chạy bất kể bạn plan/execute bằng gì: baseline rules, force-guard, review skill, context-watch, `write-docs`, `runtime-stack`.
- **Contract của gate** - gate mở khi có bất kỳ tín hiệu nào, do tool nào tạo cũng được:
  - `.finx/flow.json` có `"phase": "execute"`;
  - `.finx/flow.json` có `"approved": true`;
  - `.finx/flow.json.activePlan` trỏ tới `plan.md` có `status` là `approved` hoặc `in-progress` (nguồn nào cũng được).
- **Tắt theo kỹ sư**: `enforcement: guided` hoặc `off` trong `~/.finx/flow-config.json`.

Tool khác tích hợp bằng cách ghi artifact `.finx/flow.json` / `.finx/plans/` dùng chung; không cần là lệnh của finx-core.

## Cấu hình

`/flow-setup` ghi `~/.finx/flow-config.json` (theo kỹ sư) và/hoặc `<repo>/.finx/flow-config.json` (theo project, project thắng). Khóa: `enforcement`, `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. Không có file thì dùng mặc định chuẩn.

## Skill liên quan

`plans`, `plan-tidy` (lifecycle và migrate plan), `pre-ship` (cổng review), `logging-review` và `error-handling-review` (review dùng trong phase review).
