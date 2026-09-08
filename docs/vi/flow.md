# Flow

English: [../en/flow.md](../en/flow.md) | Về [README](../../README.vi.md)

Vòng lặp phát triển được ép: `explore -> plan -> execute -> review -> reset`. Nó giữ việc non-trivial có kỷ luật (plan được duyệt trước khi code) và sống sót qua phiên dài (lưu và resume theo context).

## Các phase

Điều bằng một lệnh, `/flow <phase>` - một lệnh duy nhất để không đụng các lệnh `explore/plan/execute/reset` cá nhân.

| Phase | Lệnh | Diễn ra |
|-------|------|---------|
| explore | `/flow explore [task]` | Vẽ scope (controller -> service -> repository, việc tương tự trước, file ảnh hưởng). Không edit. |
| plan | `/flow plan` | Tạo/kích hoạt plan trong `<hub>/plans/<group>/<repo>/`, viết kiến trúc + blueprint từng bước, xin duyệt. |
| execute | `/flow execute` | Cần tín hiệu sẵn-sàng-execute (bên dưới). Hiện thực theo plan, 1-2 file mỗi batch. |
| review | `/flow review` | Chạy cổng `pre-ship`. Sửa CRITICAL/HIGH. |
| reset | `/flow reset` | Lưu breadcrumb resume + MemPalace, archive plan đã xong, về idle. |
| status | `/flow status` | Hiện phase, active plan, task. |

## State (trong hub)

Mọi thứ nằm trong một thư mục hub, đặt bằng key `hub` trong `flow-config.json` (mặc định `~/.finx/hub`). Repo làm việc không giữ gì cả.

- `sessions/<session_id>.json` - `{ sessionId, repo, phase, activePlan, task, approved, updated }`. Flow-gate đọc file này.
- `plans/<group>/<repo>/NNN-slug/plan.md` - mỗi plan một thư mục, frontmatter `status: draft|approved|in-progress|done|abandoned`. `activePlan` lưu tương đối so với `plans/`. Tối đa 3 active mỗi repo, auto-archive plan đã xong (xem skill `plans`).
- `state/<repo-slug>.md` - con trỏ resume dễ bay hơi (phase, done, remaining, next action). State bền nằm ở `plan.md`, `git diff`, và code.

### Vì sao theo session, không theo repo

Trước đây state là một `.finx/flow.json` cho mỗi repo, tìm bằng cách leo ngược cây thư mục. Hai thứ vỡ:

- **Thừa kế.** Repo không có `.finx/` riêng thì nhặt của thư mục cha gần nhất, nên hàng chục repo không liên quan hiển thị và bị gate bởi plan của người khác.
- **Đụng nhau.** Kỹ sư thường chạy nhiều session cùng lúc; mọi session trong một repo dùng chung một file, nên session ghi sau thắng, các session còn lại hiện sai plan.

Công việc được giới hạn bởi session chứ không phải thư mục, nên state giờ khoá theo session. Nhiều plan mở cùng lúc ở nhiều repo là chuyện bình thường. Việc phân giải không bao giờ leo lên trên repo root (`git rev-parse --show-toplevel`).

Session id lấy từ dòng `FINX_SESSION_ID` do hook `SessionStart` inject - skill chỉ là prompt, không có cách nào khác để biết mình đang ở session nào.

File session được dọn rác lúc `SessionStart`: xoá khi transcript tương ứng trong `~/.claude/projects/` biến mất, hoặc quá 30 ngày. Session hiện tại và file dưới 1 ngày tuổi luôn được giữ.

> **Tương thích ngược.** `.finx/flow.json` cũ trong repo vẫn được *đọc* (chỉ ở repo root, không bao giờ ghi) để flow đang dở không mất khi nâng cấp. Bỏ hẳn sau hai release.

## Ép buộc (flow-gate)

Một hook `PreToolUse` chặn edit production Java (`**/src/main/**/*.java`) khi flow đang chạy nhưng chưa sẵn sàng và thay đổi là non-trivial (nhiều hơn `trivialMaxLines`, mặc định 30). Các mức (đặt qua `/flow-setup`):

- `hybrid` (mặc định) - chặn edit production non-trivial khi chưa sẵn sàng; edit nhỏ cho qua.
- `hard` - chặn mọi edit production khi chưa sẵn sàng.
- `guided` - theo dõi flow, không bao giờ chặn.
- `off` - tắt.

Opt-in: session không có flow state thì không bao giờ bị gate. Thoát chặn nhầm bằng `FINX_SKIP_HOOKS=1`.

**Thiếu session id thì chặn, không thả.** `session_id` do harness cấp, không phải plugin. Nếu nó ngừng đến, state không đọc cũng không ghi được, và một cái gate lặng lẽ cho qua mọi thứ sẽ trông như đang cài mà thực tế không bảo vệ gì. Ở mức `hybrid`/`hard`, gate chặn edit production Java non-trivial kèm thông điệp "no session id". `guided`, `off`, `FINX_SKIP_HOOKS=1` và ngoại lệ thay đổi nhỏ không bị ảnh hưởng.

## Phiên dài: context-watch và reset

- `UserPromptSubmit` ước lượng % context từ transcript. Ở ngưỡng (mặc định 65%) nó hỏi nên `/compact`, save-and-clear-and-reload, hay tiếp tục. Cảnh báo một lần mỗi bucket 10%.
- Save-and-reload ghi `<hub>/state/<repo-slug>.md`; sau `/clear`, hook `SessionStart` nạp lại kèm banner RESUME để phiên mới tiếp đúng phase. Breadcrumb khoá theo repo chứ không theo session, chính vì `/clear` sinh session id mới.
- `PreCompact` ghi snapshot dự phòng trước khi auto-compact ngoài ý muốn.

Ưu tiên `/compact` ở ngưỡng khi được (native, tự giữ phase); dùng clear-and-reload khi context bị nhiễu.

## Tích hợp với công cụ plan/execute khác

Flow tích hợp qua artifact state dùng chung, không phải bằng cách sở hữu các lệnh, nên plugin và tool cá nhân sống chung được.

- **Opt-in**: không có session state nghĩa là không gate.
- **Tính năng độc lập flow** chạy bất kể bạn plan/execute bằng gì: baseline rules, force-guard, review skill, context-watch, `write-docs`, `runtime-stack`.
- **Contract của gate** - gate mở khi có bất kỳ tín hiệu nào, do tool nào tạo cũng được:
  - session state có `"phase": "execute"`;
  - session state có `"approved": true`;
  - `activePlan` trỏ tới `plan.md` có `status` là `approved` hoặc `in-progress` (nguồn nào cũng được).
- **Tắt theo kỹ sư**: `enforcement: guided` hoặc `off` trong `~/.finx/flow-config.json`.

Tool khác tích hợp bằng cách ghi artifact `<hub>/sessions/<id>.json` / `<hub>/plans/` dùng chung; không cần là lệnh của finx-core.

## Cấu hình

`/flow-setup` ghi `~/.finx/flow-config.json` (theo kỹ sư) và/hoặc `<repo>/.finx/flow-config.json` (theo project, project thắng). Khóa: `enforcement`, `contextThreshold`, `contextLimit`, `trivialMaxLines`, `maxActivePlans`, `autoArchiveDays`. Không có file thì dùng mặc định chuẩn.

## Skill liên quan

`plans`, `plan-tidy` (lifecycle và migrate plan), `pre-ship` (cổng review), `logging-review` và `error-handling-review` (review dùng trong phase review).
