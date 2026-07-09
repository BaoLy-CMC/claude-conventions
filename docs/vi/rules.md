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

- Google Java Style (Checkstyle ép). Cho phép Lombok. Cấm `var` trong code mới/sửa - dùng kiểu tường minh.
- Tiền tệ dùng `BigDecimal`, không bao giờ `double` hay `float`.
- Chỉ inject qua constructor; không `@Autowired` field injection.
- Config externalize (`${ENV_VAR:default}`), không hardcode. Secret đi qua env hoặc secret manager.

## Envelope response (theo cụm)

- Repo `fsap-*` dùng `com.finx.common.fsap.pojo.FsapApiResponse` và các helper `common.fsap` (controller advice, header context, JWT).
- Repo non-fsap dùng `com.finx.spring.service.api.ResponseApi`. Không định nghĩa `ResponseApi` local mới.

## Lỗi và logging

- Error code dùng enum `ErrorCode` dạng `DOMAIN.CODE` (vd `PAYMENT.INSUFFICIENT_FUNDS`); không dùng chuỗi tự do. Vi phạm nghiệp vụ map về 4xx (422/429), không phải 500.
- "Log once, handle once" tại `GlobalExceptionHandler`.
- Logging dùng SLF4J tham số hóa, mặc định DEBUG. Không bao giờ log PII, secret, OTP, token, số thẻ hay số tài khoản đầy đủ - che (mask) định danh nhạy cảm. Không log object hay collection đầy đủ. Không log-and-throw.

## API versioning

- Mọi endpoint mang major version trong path: `/{resource}/v{N}/...`; nội bộ là `/{resource}/v{N}/internal/...`.
- Không dùng chung DTO giữa các version. Breaking change nghĩa là major version mới.

## Nghiệp vụ ngân hàng

- Đổi số dư đi qua ledger; không sửa số dư trực tiếp.
- Mọi thao tác mutating hoặc external cần idempotency key và phải retry an toàn. Giao dịch phân tán dùng saga/outbox.
- OTP / SBV: chặn sau N lần thất bại và audit mọi lần thử.

## Thao tác cross-repo (non-prod; prod là release riêng)

- Migration DB vào `non-prod-liquibase` (format changeset chặt; bắt buộc rollback; `make lint`).
- Env quan trọng (secret, endpoint ngoài, hoặc flag đổi hành vi production) cần xác nhận, rồi vào `non-prod-application-workload`.
- Topic Kafka mới vào `non-prod-kafka-gitops`.
- API public (mobile/partner) đăng ký ở `non-prod-apigw-configs` và `non-prod-openapi-configs`.

## Quyết định kiến trúc

- Lựa chọn lớn (hexagonal vs onion vs layered, ranh giới module/bounded-context, sync vs event-driven, saga vs 2PC, share vs duplicate) phải nêu với người dùng, kèm trade-off và khuyến nghị - không tự chọn im lặng.
- Khuyến nghị mặc định cho service mới: multi-module hexagonal, khớp fleet hiện có; lệch phải có lý do nêu rõ.

## Kỷ luật

- `@Transactional` ở tầng service, scope tối thiểu. Tái dùng `common-libs` / `common.fsap` trước khi viết bản local.
