# Reference: skills và hooks

English: [../en/reference.md](../en/reference.md) | Về [README](../../README.vi.md)

## Skills

Skill nạp theo nhu cầu: Claude tự gọi khi ngữ cảnh khớp `description`, hoặc bạn gọi theo tên.

### Bắt đầu

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `onboarding` | Tour lần đầu: cái gì luôn bật, cái gì nạp theo nhu cầu, flow chạy ra sao, rồi cấu hình các tuỳ chọn được chọn | Ngay sau khi cài; khi có thông báo onboarding lúc mở phiên; "dùng finx-core sao", "getting started" |

### Review

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `logging-review` | Kiểm logging theo checklist 14 điểm (PII/mask, SLF4J tham số hóa, mặc định DEBUG, không log-and-throw, không empty catch) | Review/viết log; "review logging" |
| `error-handling-review` | Kiểm error code (`DOMAIN.CODE`), HTTP mapping (nghiệp vụ -> 4xx), log-once, envelope đúng cụm | Review exception, error handler, envelope |
| `api-response-standards` | Hợp đồng theo ARB: envelope status/payload/meta, map 422/409/428, empty vs 404, replay idempotent, xử lý downstream timeout, tracing W3C | Viết/review controller hay endpoint tiền; chọn status code |
| `integration-test` | Chuẩn integration test của tổ chức: source set opt-in tự skip khi chưa cấu hình, container thay vì hạ tầng dùng chung, assertion value/shape/behaviour, cleanup marker+watermark, gate coverage riêng | Thêm/review integration test; test flaky hoặc bị drop vì trùng |
| `pre-ship` | Một cổng verify: compile, Checkstyle, test + coverage, các review skill, SonarQube quality gate, diff-sanity -> một PASS/FAIL | Trước PR/ship; phase review của flow |

### Flow

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `flow` | Điều `explore -> plan -> execute -> review -> reset` với state theo session ở `<hub>/sessions/` | `/flow <phase>`; bắt đầu việc non-trivial |
| `plans` | Quản lý plan trong `<hub>/plans/` (lifecycle, một active plan, guard) | "list plans", "new plan", "too many plans" |
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
| `ops-runtime` | `values.yaml` của workload (probe, heap flag, HPA, drain), cấu hình actuator/metrics, và tạo index trên bảng production | Sửa workload; OOMKill/rollout downtime; `CREATE INDEX` trên prod |
| `release-workload` | Ba giai đoạn release trong `platform-release-processes`, idempotency `.done`, tag bất biến và roll-forward | Release lên production; giai đoạn không chạy gì sau khi merge |

### Trình bày (theo từng kỹ sư)

| Skill | Mục đích | Kích hoạt |
|-------|----------|-----------|
| `statusline-setup` | Nối statusline powerline theo flow vào `~/.claude/settings.json` của chính kỹ sư (hỏi trước; không đè statusline sẵn có) | "finx statusline", "setup statusline", "hiện flow phase trên bar" |

## Output styles

Opt-in theo từng kỹ sư. Mỗi style là một lựa chọn trong `/config` -> **Output style**; chọn một cái sẽ đổi *cách* Claude trình bày (không đổi kiến thức). Không cái nào bị ép (`force-for-plugin` không đặt), nên ai không chọn thì không bị ảnh hưởng. Tất cả giữ hành vi code của Claude (`keep-coding-instructions: true`), chỉ đổi độ sâu giải thích. Có hiệu lực sau `/clear` hoặc phiên mới.

| Style (trong `/config`) | Dành cho | Hành vi |
|------|----------|---------|
| `FinX Quick` | Việc gấp | Chỉ kết quả + diff; không option/phân tích trừ khi được hỏi. |
| `FinX Standard` | Đã rõ nguyên lý, làm nhanh | Implement thẳng, chỉ thêm option/trade-off 1-2 dòng ở chỗ có quyết định thật. |
| `FinX Deep` | Vừa học vừa làm | Giải thích lý do, liệt kê options + trade-off cụ thể, cite convention/Confluence FinX. |

Baseline always-on vẫn áp ở dưới; style chỉ chỉnh độ sâu/giọng cho kỹ sư đã opt-in.

## Statusline

Opt-in theo từng kỹ sư, bật qua skill `statusline-setup`. Plugin không thể tự đặt statusline chính (chỉ setting user/project mới đặt được), nên skill này nối `scripts/finx-statusline.sh` vào `~/.claude/settings.json` của chính kỹ sư và không đè statusline sẵn có (vd claude-hud) nếu chưa hỏi.

- Hiện (powerline, tô màu theo phase explore/plan/execute/review và mức dùng xanh < 60 < vàng < 80 < đỏ):
  - `full` = 2 dòng — dòng 1 (công việc) `repo · phase · active-plan · enforcement · context%`; dòng 2 (phiên) `model · session% · đếm ngược reset`. `session%` + reset lấy từ cửa sổ usage 5 tiếng (`rate_limits.five_hour`, chỉ Pro/Max; ẩn khi không có — lúc đó dòng 2 chỉ còn model).
  - `compact` = 1 dòng `repo · phase · context%`.
- Cần Nerd Font cho glyph; `--plain` fallback về ASCII.
- Session không có flow state thì phần flow tự ẩn (chỉ còn repo + context). Fail-safe: lỗi thì in dòng tối giản thay vì làm hỏng bar.

## Script

| Script | Làm gì | Chạy khi nào |
|--------|--------|--------------|
| `canonical/generate.py` | Sinh lại baseline + file steering Kiro từ `canonical/conventions.json` | Sau khi sửa convention |
| `scripts/check-skills.py` | Lint mọi `SKILL.md` theo giới hạn authoring của Agent Skills (name khớp thư mục, description <= 1024 ký tự và có nói khi nào dùng, body < 500 dòng, reference một cấp và có mục lục nếu quá 100 dòng, không chứa XML tag, viết ở ngôi thứ ba) | Trước khi release thay đổi skill; bước 7 của `pre-ship` |
| `scripts/finx-statusline.sh` | Render statusline powerline theo flow | Do `statusline-setup` cấu hình |

## Hooks

Bốn sự kiện lifecycle. Tất cả fail-open (không làm hỏng tool call khi lỗi). Lối thoát khi chặn nhầm: `FINX_SKIP_HOOKS=1`.

| Sự kiện | Script | Làm gì |
|---------|--------|--------|
| `SessionStart` | `session-start.py` | Nạp baseline + `FINX_SESSION_ID`; nếu breadcrumb `<hub>/state/` của repo còn mới thì append kèm banner RESUME; dọn rác file session chết |
| `SessionStart` | `version-notice.py` | Khi version finx-core cài đã đổi so với phiên trước, in version mới và changelog của nó |
| `SessionStart` | `onboarding-notice.py` | Khi chưa xong (hoặc chưa từ chối) tour onboarding, nhắc kỹ sư chạy `/finx-core:onboarding` — tối đa 3 phiên, state ở `~/.finx/.finx-core-onboarding` |
| `PreToolUse` (Write/Edit) | `precheck.py` | Chặn cứng vi phạm xác định cao: `var` trong code mới, `double`/`float` cho tiền, `System.out`/`printStackTrace`, secret hardcode |
| `PreToolUse` (Write/Edit) | `flow-gate.py` | Chặn edit production Java non-trivial trừ khi có tín hiệu sẵn-sàng-execute (xem [Flow](flow.md)) |
| `UserPromptSubmit` | `context-watch.py` | Ước lượng % context; quanh ~65% hỏi nên compact, save+reset, hay tiếp tục |
| `PreCompact` | `flow-reset.py` | Chụp nhanh phase + active plan + `git diff --stat` vào breadcrumb `<hub>/state/` của repo trước compact |

### Force-guard và flow-gate

- **Force-guard** (`precheck.py`) về nội dung code, luôn áp cho mọi lần ghi production Java.
- **Flow-gate** (`flow-gate.py`) về trạng thái quy trình, chỉ áp khi session chạy flow (có session state) với `enforcement` khác `off`/`guided`.
