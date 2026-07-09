# FinX Claude Conventions — Tổng quan (Tiếng Việt)

Một plugin Claude Code dùng chung (`finx-core`) mã hóa bộ chuẩn kỹ thuật backend của FinX thành các rule, skill và hook máy kiểm được, để Claude Code của mọi kỹ sư hành xử nhất quán.

Bản tiếng Anh: [`overview.en.md`](overview.en.md).

## Mục đích

- Một nguồn convention kỹ thuật duy nhất cho nền tảng ngân hàng FinX / Vikki (Java 21 + Spring Boot).
- Văn bản chuẩn nằm ở Confluence, space `EN` (Engineering). Plugin không sao chép lại — nó mã hóa phần có thể ép buộc để áp dụng tự động và nhất quán.

## Cài đặt lần đầu

```
/plugin marketplace add <internal-git-url>
/plugin install finx-core@finx-conventions
/reload-plugins
```

Sau đó mở session mới để nạp baseline always-on. Có thể chạy `/flow-setup` để tùy biến mức enforcement và các ngưỡng; không chạy thì dùng giá trị mặc định chuẩn.

## Bạn nhận được gì

### 1. Baseline always-on (nạp mỗi phiên)

Một khối rule cô đọng được nạp lúc bắt đầu phiên qua hook (plugin không tự nạp `CLAUDE.md`). Nội dung:

- Nguyên tắc làm việc: nghĩ trước và không bao giờ tự suy diễn im lặng (có concern thì nêu kèm khuyến nghị), ưu tiên KISS thay vì over-engineer, nghĩ sâu và giao đơn giản, chỉ sửa đúng phạm vi, có tiêu chí thành công kiểm chứng được, báo cáo trung thực, ưu tiên thao tác đảo ngược được.
- Giao tiếp: trả lời vào thẳng vấn đề, ngắn gọn dễ đọc, có trích dẫn nguồn.
- Nguyên tắc bắt buộc: Google Java Style, cho phép Lombok, cấm `var` trong code mới, dùng `BigDecimal` cho tiền tệ, chỉ inject qua constructor, externalize config, secret đi qua env/secret manager.
- Envelope response theo cụm: `fsap-*` → `com.finx.common.fsap.pojo.FsapApiResponse`; non-fsap → `com.finx.spring.service.api.ResponseApi`.
- Lỗi và logging: enum `ErrorCode` dạng `DOMAIN.CODE`, lỗi nghiệp vụ map về 4xx, log một lần tại `GlobalExceptionHandler`, SLF4J tham số hóa, mặc định DEBUG, không log PII, che (mask) định danh nhạy cảm.
- API versioning: `/{resource}/v{N}/...`, không dùng chung DTO giữa các version.
- Nghiệp vụ ngân hàng: đổi số dư chỉ qua ledger, mọi thao tác mutating cần idempotency key, giao dịch phân tán dùng saga/outbox, OTP/SBV chặn sau N lần thất bại và audit đầy đủ.
- Thao tác cross-repo (non-prod): migration DB vào `non-prod-liquibase`, env quan trọng vào `non-prod-application-workload` (có xác nhận), topic Kafka vào `non-prod-kafka-gitops`, API public vào `non-prod-apigw-configs` và `non-prod-openapi-configs`.
- Quyết định kiến trúc (hexagonal / onion / layered, sync hay event, saga hay 2PC) phải hỏi kèm trade-off và khuyến nghị.

### 2. Skills (nạp theo nhu cầu)

- Review: `logging-review`, `error-handling-review`, `pre-ship` (cổng verify đầy đủ: build, Checkstyle, test/coverage, review, SonarQube).
- Flow: `flow` (`/flow <phase>`), `plans`, `plan-tidy`, `flow-setup`.
- Tạo/soạn: `create-liquibase-changeset`, `cross-repo-operations`, `new-service-scaffold`, `write-docs`.

### 3. Hooks (bốn sự kiện)

- `SessionStart`: nạp baseline và resume `.finx/state_summary.md`.
- `PreToolUse`: force-guard (chặn `var` trong code mới, `double`/`float` cho biến tiền, `System.out`/`printStackTrace`, secret hardcode) và flow-gate (chặn sửa code production Java non-trivial khi chưa ở phase `execute`).
- `UserPromptSubmit`: context-watch — quanh mức 65% context sẽ hỏi nên compact, lưu-và-reset, hay tiếp tục.
- `PreCompact`: chụp nhanh trạng thái flow trước khi compact.

Lối thoát khi bị chặn nhầm: `FINX_SKIP_HOOKS=1`.

## Quy trình phát triển

`explore → plan → execute → review → reset`, điều khiển bằng `/flow <phase>`. Việc production non-trivial phải có plan được duyệt trước khi code (flow-gate ép). Xem [`flow.md`](flow.md) để biết các phase, state và mức enforcement.

## Cấu hình

`/flow-setup` ghi `~/.finx/flow-config.json` (theo từng kỹ sư) và/hoặc `<repo>/.finx/flow-config.json` (theo project, project thắng). Khóa: `enforcement` (hybrid/hard/guided/off), `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. Không có file thì dùng mặc định chuẩn.

## Cập nhật

Maintainer phát hành bằng `./release.sh <version>` (bump cả hai manifest và regenerate artifact), rồi commit, tag, push. Kỹ sư cập nhật bằng `/plugin marketplace update finx-conventions`, `/plugin update finx-core`, `/reload-plugins`, rồi mở session mới. Chi tiết trong [`releasing.md`](releasing.md).

## Nguồn chuẩn

Confluence space `EN`, trang hub "Backend - Conventions & Standards". Mỗi skill và rule đều trích dẫn trang nguồn. Khi chuẩn trên Confluence thay đổi, cập nhật `canonical/conventions.json` (hoặc skill liên quan) rồi phát hành version mới.
