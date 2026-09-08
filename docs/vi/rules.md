# Rules (baseline always-on)

English: [../en/rules.md](../en/rules.md) | Về [README](../../README.vi.md)

Các rule này được nạp vào mọi phiên bởi hook `SessionStart`, sinh từ `canonical/conventions.json`. Muốn sửa: sửa file đó rồi phát hành (xem [Releasing](releasing.md)).

## Nguyên tắc làm việc

- Nghĩ trước; nêu giả định. Không bao giờ tự suy diễn im lặng: có concern (bảo mật, mất dữ liệu, breaking change, scope không rõ, thao tác không đảo ngược) thì dừng và hỏi, và luôn hỏi kèm khuyến nghị.
- KISS, không over-engineer: tối thiểu code giải đúng bài; không tính năng speculative, không abstraction cho một chỗ dùng.
- Nghĩ sâu, giao đơn giản: nghĩ thấu toàn bộ độ phức tạp rồi giao giải pháp đơn giản nhất mà vẫn đúng; độ sâu tư duy không được rò rỉ ra output.
- Surgical: chỉ sửa đúng phần yêu cầu; note issue kề bên, không tự sửa im lặng.
- Thành công kiểm chứng được: định tiêu chí kiểm cho mỗi bước trước khi làm.
- Báo cáo trung thực: build/test hỏng thì nói kèm output; không phóng đại/bịa kết quả.
- Ưu tiên đảo ngược được: thao tác không đảo ngược hoặc outward-facing cần xác nhận; không ghi đè/xóa file mình không tạo mà chưa nêu ra.

## Giao tiếp

- Trả lời vào thẳng vấn đề; ngắn, rõ, dễ đọc; không lan man.
- Trích dẫn nguồn cho các khẳng định (`file:line`, id trang Confluence, URL).

## Version runtime (theo project)

- Java (21 hoặc 25 LTS) và Spring Boot (3 hoặc 4) khác nhau theo project. Detect từ build files và theo rule của version đó. Không dùng feature/API mới hơn version project khai báo; muốn dùng thì flag và hỏi.
- Spring Boot 4: Jakarta EE 11 / Servlet 6.1 / Jackson 3, tối thiểu Java 21, bỏ hết deprecation của Boot-3, drop Undertow và JUnit 4. Spring Boot 3: Jakarta EE 9-10 (`jakarta.*`), Java 17+.
- Chi tiết và lộ trình upgrade: skill `runtime-stack` (xem [Reference](reference.md)).

## Convention Java và Spring

- Google Java Style (Checkstyle ép). Cho phép Lombok - dùng ở chỗ nó bỏ được boilerplate thật (`@RequiredArgsConstructor` cho constructor injection, `@Getter`, `@Builder`, `@Slf4j`); cấm `@Data` trên JPA entity. Cấm `var` trong code mới/sửa - dùng kiểu tường minh.
- Tiền tệ dùng `BigDecimal`, không bao giờ `double` hay `float`.
- Chỉ inject qua constructor; không `@Autowired` field injection.
- Config externalize (`${ENV_VAR:default}`), không hardcode. Secret đi qua env hoặc secret manager.

## Envelope response (theo cụm)

- Repo `fsap-*` dùng `com.finx.common.fsap.pojo.FsapApiResponse` và các helper `common.fsap` (controller advice, header context, JWT).
- Repo non-fsap dùng `com.finx.spring.service.api.ResponseApi`. Không định nghĩa `ResponseApi` local mới.

## Lỗi và logging

- Error code dùng enum `ErrorCode` dạng `DOMAIN.CODE` (vd `PAYMENT.INSUFFICIENT_FUNDS`); mọi giá trị `status.code` lấy từ catalog tập trung, mở rộng qua PR - không dùng chuỗi tự do. Vi phạm nghiệp vụ map về 4xx, không bao giờ 500.
- "Log once, handle once" tại `GlobalExceptionHandler`.
- Logging dùng SLF4J tham số hóa, mặc định DEBUG. Không bao giờ log PII, secret, OTP, token, số thẻ hay số tài khoản đầy đủ - che (mask) định danh nhạy cảm. Không log object hay collection đầy đủ. Không log-and-throw.
- Level phản chiếu response: lỗi nghiệp vụ trả 4xx thì log `WARN` (không bao giờ `ERROR`); lỗi hệ thống trả 5xx thì log `ERROR` với exception ở tham số cuối để giữ stack trace. Cấm `FATAL`.
- `INFO` chỉ dùng cho: lifecycle của service, cột mốc nghiệp vụ, tổng kết cronjob, kafka consumer, đổi state quan trọng; còn lại là `DEBUG`. Format message `<Action description>. [key1={}, key2={}]` bằng tiếng Anh: không nối chuỗi, không log trùng cùng một sự kiện (log một lần ở biên service), không catch rỗng.

## API versioning

- Mọi endpoint mang major version trong path: `/{resource}/v{N}/...`; nội bộ là `/{resource}/v{N}/internal/...`.
- Không dùng chung DTO giữa các version. Breaking change nghĩa là major version mới.
- Layout package phản chiếu version trong URL (`controller/v{N}/`, `dto/v{N}/`); controller `v{N}` chỉ import DTO `v{N}`.
- Endpoint deprecated phải trả header `Deprecation` và `Sunset` ở mọi response, tới hạn sunset thì trả 410; thời gian thông báo tối thiểu 6 tháng cho API external, 3 tháng cho internal.
- Mọi endpoint đăng ký một `x-api-id` tĩnh (`X##`: chữ cái module + số thứ tự 2 chữ số) trong `internal-apis.yaml`.

## Hợp đồng API (quyết định ARB, 08/2026)

- Response envelope: đúng ba khối top-level - `status{code,message,errors}` / `payload` / `meta{requestId,nextCursor}`. Thành công thì message rỗng; lỗi thì có message, lỗi theo từng field, và payload `null`.
- HTTP status là phán quyết tầng transport, `status.code` là phán quyết nghiệp vụ: nghiệp vụ từ chối 422; trùng giao dịch/idempotency/version conflict 409; cần thêm bước (OTP/KYC/approval) 428; chỉ lỗi validation 400; chưa xác thực 401; thiếu quyền chức năng 403; rate limit 429 kèm `Retry-After`; lỗi code của mình 500; dependency chết 503. Nghiệp vụ không bao giờ là 400 hay 500.
- Empty là thành công: 200 với `[]` hoặc `null`, không bao giờ 404 cho collection. User cố xem resource của người khác nhận 404/empty, không phải 403, để không dò được id.
- Luồng tiền: endpoint tạo giao dịch bắt buộc có idempotency key. Cùng key cùng payload thì replay response đầu tiên; cùng key khác payload trả 409; thiếu key trả 400. Batch một phần: 200 + `PARTIAL` kèm lý do từng item. Async: 202 + `jobId` cùng một endpoint poll.
- Gọi downstream trên luồng tiền: rẽ theo việc side effect có thể đã xảy ra hay chưa, không rẽ theo có timeout hay không. Chưa gửi được - 503, retry an toàn. Đã gửi rồi timeout hoặc không rõ - persist intent trước, trả 200 với `PROCESSING`/`UNKNOWN` kèm transaction id, client poll trạng thái; không bao giờ `FAILURE`, không bao giờ gửi lại lệnh tạo.
- Tracing: `traceparent` chuẩn W3C (hex chữ thường) propagate sang mọi outgoing call kể cả publish Kafka và API đối tác; gateway tự sinh khi client ngoài không gửi; `trace-id` dùng luôn làm `meta.requestId`. Số tiền là `BigDecimal`, timestamp ISO 8601 UTC, `nextCursor` opaque, và `status.message` không lộ chi tiết nội bộ.
- Chi tiết và checklist review PR: skill `api-response-standards`.

## Nghiệp vụ ngân hàng

- Đổi số dư đi qua ledger; không sửa số dư trực tiếp.
- Mọi thao tác mutating hoặc external cần idempotency key và phải retry an toàn. Giao dịch phân tán dùng saga/outbox. Dedup phải dựa trên key hoặc unique constraint thật, không best-effort - nêu rõ cơ chế trong phần trade-off của plan.
- Downstream timeout trên luồng tiền không bao giờ trả FAILURE (client retry sẽ gây double-charge); trả pending/unknown rồi đối soát.
- OTP / SBV: chặn sau N lần thất bại và audit mọi lần thử.

## Concurrency và transaction

- Spring bean mặc định stateless. Xác định shared mutable state trước khi sửa, rồi chặn tường minh (`synchronized`, `ReentrantLock`, `java.util.concurrent`).
- `@Transactional` ở tầng service, propagation mặc định `REQUIRED`; `REQUIRES_NEW` chỉ khi thật sự cần cô lập. Không bao giờ giữ lock (row DB hay in-process) khi gọi network.

## Bộ nhớ và truy cập dữ liệu

- Không allocate quá 512KB ở hot path. Không giữ collection lớn trong instance field của Spring bean.
- Luôn phân trang; không load full table hay result set không giới hạn vào bộ nhớ.
- Mỗi bảng có primary key tường minh dạng `BIGSERIAL`/`SERIAL`; UUID chỉ là column phụ kèm secondary index. Không dùng foreign key trong DB - giữ nhất quán ở tầng application.
- Mọi query phải có timeout riêng bên cạnh timeout query/connection toàn cục, và connection đi qua pool (client-side hoặc pgBouncer).

## Common libs (routing chặt)

- Mỗi cluster dùng lib của chính nó, không dùng của cluster khác: vikki dùng `finx/vikki/common-libs` (`com.finx.common-libs`); fsap dùng `finx/fsap/fsap-common-libs` (`com.finx.fsap`); bff/galaxy-g nằm trong repo fsap (`com.finx.galaxyg`).
- grep repo và lib của cluster trước khi viết util mới.

## Comment

- Mặc định là không comment; naming mang ý nghĩa. Chỉ comment để giải thích *tại sao* (workaround, business rule dị thường), trong một dòng ngắn.
- Không bao giờ comment *code làm gì*. Thấy comment thừa trong đoạn đang sửa thì xoá.

## Thao tác cross-repo (non-prod; prod là release riêng)

- Migration DB vào `non-prod-liquibase` (format changeset chặt; bắt buộc rollback; `make lint`).
- Env quan trọng (secret, endpoint ngoài, hoặc flag đổi hành vi production) cần xác nhận, rồi vào `non-prod-application-workload`.
- Topic Kafka mới vào `non-prod-kafka-gitops`.
- API public (mobile/partner) đăng ký ở `non-prod-apigw-configs` và `non-prod-openapi-configs`.

## Commit và PR

- Branch: `<type>/<JIRA-KEY>-<short-description>` (vd `feat/VRHE-66-user-authentication`); branch deploy: `release/<YYYY-MM-DD>-<short-description>`. Nguồn: Confluence EN/514556795.
- Commit: `<type>(<optional scope>): <description>` - thể mệnh lệnh hiện tại, chữ đầu không viết hoa, không dấu `.` ở cuối. Dấu `!` trước dấu hai chấm đánh dấu breaking change; issue id nằm ở body, không dùng làm scope. Types: feat, fix, refactor, perf, style, test, docs, build, cicd, ops, chore. Repo nào prefix thêm `[JIRA-KEY]` thì giữ một key duy nhất mỗi commit và không đoán key. Không thêm trailer attribution.
- Độ dài PR description tỷ lệ với diff: What & Why (1-2 câu), Notes (quyết định không hiển nhiên, breaking change, thứ tự deploy, phần cố ý chưa làm), Verification (lệnh đã chạy thật và kết quả thật; chưa test thì ghi rõ). Không liệt kê file, không chép commit log, không emoji, không checklist ảo.

## Quyết định kiến trúc

- Lựa chọn lớn (hexagonal vs onion vs layered, ranh giới module/bounded-context, sync vs event-driven, saga vs 2PC, share vs duplicate) phải nêu với người dùng, kèm trade-off và khuyến nghị - không tự chọn im lặng.
- Khuyến nghị mặc định cho service mới: multi-module hexagonal, khớp fleet hiện có; lệch phải có lý do nêu rõ.
- Mọi quyết định thiết kế - chọn library, data model, chiến lược retry - đều kèm pros/cons tường minh, không phán một chiều.

## Kỷ luật

- `@Transactional` ở tầng service, scope tối thiểu. Tái dùng `common-libs` / `common.fsap` trước khi viết bản local.
- Không viết code trước khi có plan được duyệt với mọi việc non-trivial - chạy skill `flow` (explore -> plan -> execute -> review).
