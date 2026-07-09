# Reference: skills và hooks

English: [../en/reference.md](../en/reference.md) | Về [README](../../README.vi.md)

## Skills

Skill nạp theo nhu cầu: Claude tự gọi khi ngữ cảnh khớp `description`, hoặc bạn gọi theo tên.

### Review

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `logging-review` | Kiểm logging theo checklist 14 điểm (PII/mask, SLF4J tham số hóa, mặc định DEBUG, không log-and-throw, không empty catch) | Review/viết log; "review logging" |
| `error-handling-review` | Kiểm error code (`DOMAIN.CODE`), HTTP mapping (nghiệp vụ -> 4xx), log-once, envelope đúng cụm | Review exception, error handler, envelope |
| `pre-ship` | Một cổng verify: compile, Checkstyle, test + coverage, các review skill, SonarQube quality gate, diff-sanity -> một PASS/FAIL | Trước PR/ship; phase review của flow |

### Flow

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `flow` | Điều `explore -> plan -> execute -> review -> reset` với state ở `.finx/flow.json` | `/flow <phase>`; bắt đầu việc non-trivial |
| `plans` | Quản lý plan trong `.finx/plans/` (lifecycle, một active plan, guard) | "list plans", "new plan", "too many plans" |
| `plan-tidy` | Gom `plan*.md` rải rác ở root vào cấu trúc, có xác nhận | "tidy plans", file plan lỏng lẻo ở root |
| `flow-setup` | Cấu hình flow theo kỹ sư/project (enforcement, ngưỡng) | "flow setup", "configure flow" |

### Tạo/soạn

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `create-liquibase-changeset` | Scaffold changeset trong `non-prod-liquibase` đúng format ép | "create migration/changeset" |
| `cross-repo-operations` | Định tuyến thay đổi hạ tầng vào đúng repo GitOps non-prod; confirm-gate cho env quan trọng | Thêm topic Kafka, env var, hoặc API public |
| `new-service-scaffold` | Dựng service/module mới (hỏi kiến trúc trước) | "new service", "scaffold" |
| `write-docs` | Viết docs theo format và nơi lưu chọn; hỏi tiếng Anh hay tiếng Việt; không icon | "write docs", "document this" |
| `runtime-stack` | Detect version Java + Spring Boot và áp rule theo version | Viết/upgrade code; nhắc tới Java 21/25 hoặc Spring Boot 3/4 |

## Hooks

Bốn sự kiện lifecycle. Tất cả fail-open (không làm hỏng tool call khi lỗi). Lối thoát khi chặn nhầm: `FINX_SKIP_HOOKS=1`.

| Sự kiện | Script | Làm gì |
|---------|--------|--------|
| `SessionStart` | `session-start.py` | Nạp baseline; nếu `.finx/state_summary.md` còn mới thì append kèm banner RESUME |
| `PreToolUse` (Write/Edit) | `precheck.py` | Chặn cứng vi phạm xác định cao: `var` trong code mới, `double`/`float` cho tiền, `System.out`/`printStackTrace`, secret hardcode |
| `PreToolUse` (Write/Edit) | `flow-gate.py` | Chặn edit production Java non-trivial trừ khi có tín hiệu sẵn-sàng-execute (xem [Flow](flow.md)) |
| `UserPromptSubmit` | `context-watch.py` | Ước lượng % context; quanh ~65% hỏi nên compact, save+reset, hay tiếp tục |
| `PreCompact` | `flow-reset.py` | Chụp nhanh phase + active plan + `git diff --stat` vào `.finx/state_summary.md` trước compact |

### Force-guard và flow-gate

- **Force-guard** (`precheck.py`) về nội dung code, luôn áp cho mọi lần ghi production Java.
- **Flow-gate** (`flow-gate.py`) về trạng thái quy trình, chỉ áp khi repo chạy flow (`.finx/flow.json` có mặt) với `enforcement` khác `off`/`guided`.
