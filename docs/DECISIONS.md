# Các quyết định thiết kế

Tài liệu này ghi lại chỗ hai nguồn (Matt Pocock `skills` và Lauren Tan `pstack`) khác nhau hoặc mâu thuẫn, tstack chọn gì và vì sao. Đọc trước khi sửa một skill: phần lớn các "tại sao không làm X" đã có câu trả lời ở đây.

## Tiêu chí chọn

Một ý tưởng được đưa vào khi nó phục vụ ít nhất một trong năm trụ cột (xem README) **và** qua được ba phép thử:

1. **Chạy được trên Claude Code hôm nay.** Mọi khoá settings, trường frontmatter, sự kiện hook đều kiểm trực tiếp trên Claude Code 2.1.283, không dựa vào trí nhớ. Thứ gì phụ thuộc Cursor (Automations, Graphite `gt`, `/goal`, slug model riêng) được chuyển nghĩa hoặc bỏ.
2. **Đáng giá context của nó.** Mỗi token luôn-bật phải trả được tiền thuê. Đo bằng `/context`, không ước.
3. **Thay đổi một quyết định.** Câu nào model đằng nào cũng làm theo (no-op) thì xoá.

## Các xung đột và lựa chọn

### 1. Gọn nhẹ mặc định hay chặt chẽ tối đa

- **Matt:** giữ context gọn, ít nghi thức, người lái.
- **pstack:** quy trình nặng: panel ba model, bốn agent reflect ở mức cao nhất, arena, quét bảy nguồn cho `why`.
- **tstack chọn:** nền gọn, phần nặng là tuỳ chọn. `effortLevel` mặc định `medium`; chỉ các skill cần phán đoán (grilling, codebase-design, diagnose, interrogate, reflect) tự lên `high`. Trục review đối kháng chỉ chạy với diff rủi ro (auth, dữ liệu, concurrency, API công khai, >400 dòng, sửa bug không có test hồi quy) hoặc khi được yêu cầu. `why` mặc định chỉ đào git; quét MCP khi bạn yêu cầu.
- **Vì sao:** sự chặt chẽ đặt đúng chỗ (diff rủi ro, câu hỏi khó) mang lại gần hết lợi ích mà không trả giá trên mọi task.

### 2. Lên kế hoạch trước hay "code chính là spec"

- **Matt:** grill → spec → tickets → implement; kế hoạch viết ra là tài sản.
- **pstack:** prototype và bằng chứng chạy thật thắng tranh luận; "observe, don't ask".
- **tstack chọn:** cả hai, chia theo loại câu hỏi. Câu hỏi về **sản phẩm hoặc sở thích** thì hỏi người (grilling). Câu hỏi "cách nào tốt hơn" mà **chạy thử trả lời được** thì agent tự làm `prototype` rồi báo kết quả. Spec và tickets chỉ cần khi việc vượt một smart zone; việc nhỏ đi thẳng từ grilling sang `implement`.
- **Vì sao:** hỏi người một câu mà máy tự trả lời được là lãng phí thời gian của người; để máy tự quyết chuyện sản phẩm là lãng phí cả dự án.

### 3. Người giữ ranh giới pha hay agent tự chủ

- **Matt:** người quyết định ở mỗi ranh giới pha (continue, clear, handoff, subagent, compact).
- **pstack:** chạy dài không giám sát, có hợp đồng.
- **tstack chọn:** hai chế độ tách bạch. Khi bạn ngồi đó: cây quyết định năm lựa chọn trong `work/PHASE-BOUNDARIES.md`, hook nhắc khi auto-compact bắn (nghĩa là một ranh giới đã bị bỏ lỡ), status line đổi màu khi gần 150k. Khi bạn vắng: `/tstack:afk` với hợp đồng viết: năm phần của hợp đồng qua đêm trong pstack (mục tiêu, điều kiện xong kiểm được, cách ly, quyền cấp trước, lối thoát) cộng danh sách luôn dừng và chỉ thị thường trực, trạng thái lưu trong `.tstack/<slug>/` nên sống sót qua compaction, và mỗi quyết định mặc định được ghi kèm "từ để đảo ngược".
- **Vì sao:** tự chủ không có hợp đồng thì sáng ra bạn không tin được kết quả; hợp đồng làm cho kết quả kiểm toán được.

### 3b. Chạy dài: một cửa sổ hay nhiều smart zone

- **pstack:** `/goal` kèm hợp đồng, `/loop` tới khi xong.
- **Matt (Shipping):** `/goal` trong một cửa sổ context chỉ có một chút smart zone ở đầu rồi rất nhiều dumb zone, vì dựa vào auto-compaction. Spec và tickets giữ công việc trong nhiều smart zone và thường rẻ hơn.
- **tstack chọn:** `afk` giữ hợp đồng của pstack nhưng chạy theo cách của Matt: người điều phối không viết code; mỗi đơn vị việc là một `ticket-worker` **mới** (context sạch), một `verifier` độc lập kiểm lại. Điều phối viên đọc lại `contract.md` và `ledger.tsv` mỗi vòng, nên compaction của chính nó không làm mất trạng thái. Ngừng nhận đơn vị mới khi dùng khoảng 70% ngân sách.

### 4. Chứng minh bằng test hay bằng app thật

- **Matt:** TDD tại các seam đã thống nhất.
- **pstack:** chỉ tin bằng chứng trên artifact thật; người viết không tự chấm.
- **tstack chọn:** cả hai, mỗi thứ một việc. TDD giữ logic đúng và chống hồi quy. Hành vi người dùng thấy được thì phải `prove` trên app thật qua verify skill, do `verifier` (context sạch, không được sửa code) thực hiện. Typecheck xanh, CI xanh, unit test hay một diff "trông hợp lý" đều không phải bằng chứng. Bug thì tái hiện hai lần trước khi sửa và hai lần sau khi sửa.
- **Vì sao:** test chứng minh code làm điều test nói; chỉ app thật chứng minh người dùng nhận được điều họ cần.

### 5. Review: tách trục hay một người đánh giá tổng

- **Matt:** hai trục (Standards, Spec) chạy song song, không bao giờ trộn.
- **pstack:** một "lead" phán xử phát hiện, có trục đối kháng.
- **tstack chọn:** giữ trục tách biệt của Matt, thêm trục đối kháng của pstack cho diff rủi ro, và dùng phán xử của lead **bên trong từng trục** (Act on / Consider / Noted / Dismissed). Không xếp hạng chéo trục, không chọn "vấn đề tệ nhất" chung.
- **Vì sao:** code có thể theo đúng mọi chuẩn mà build sai thứ, hoặc build đúng thứ mà sai mọi chuẩn; trộn trục thì trục này che trục kia.

### 6. Reviewer khác họ model

- **pstack:** panel nhiều hãng model là mặc định cho review quan trọng.
- **tstack chọn:** **opt-in**, cùng một quy tắc ở cả bốn chỗ có thể dùng (reviewer của `interrogate`, người soát decision log, một ghế trong design it twice, giám khảo eval): chỉ gửi dữ liệu sang `codex` hoặc `gemini` khi bạn yêu cầu trong task, hoặc AGENTS.md / CODING_STANDARDS.md của repo cho phép rõ ràng. Không có seat ngoài thì báo cáo nói thẳng: mọi reviewer cùng một họ model nên điểm mù tương quan.
- **Vì sao:** gửi code sang hãng khác là quyết định về dữ liệu, không phải chi tiết kỹ thuật. Mặc định không có code nào rời máy.

### 7. Migration: migrate-then-delete hay expand-contract

- **pstack:** tự sửa mọi caller rồi xoá đường cũ trong cùng một thay đổi.
- **Matt:** expand-contract qua nhiều ticket.
- **tstack chọn:** migrate-then-delete khi bạn sở hữu mọi caller và thay đổi vừa một phiên; expand-contract (qua `/tstack:to-tickets`) khi có caller bên ngoài hoặc việc kéo dài nhiều phiên. Playbook `wide-change` bắt đầu bằng "xây đòn bẩy" (codemod, script đếm) trước khi sửa tay.

### 8. Comment trong code

- **tstack chọn:** chỉ giữ comment giải thích "vì sao" không hiển nhiên hoặc ràng buộc bên ngoài. Comment kể lại code làm gì thì xoá (checklist deslop trong `ship`). Ràng buộc kiểu "đừng xoá dòng này" thì mã hoá thành type, test hoặc lint thay vì viết comment.
- **Vì sao:** agent sao chép những gì code đang làm; comment không có cơ chế ép buộc thì trôi.

### 9. Nơi lưu trí nhớ

- **tstack chọn:** tắt auto memory (`autoMemoryEnabled: false`). Bài học đi theo thang của pstack: type/kiến trúc > lint/hook/CI > `CODING_STANDARDS.md` > skill/pointer doc > AGENTS.md. Git guard là một hook chứ không phải một dòng "đừng force-push" trong CLAUDE.md.
- **Vì sao:** ghi chú ẩn không được review, không chia sẻ với đồng đội, và không ép buộc được gì. Codebase là trí nhớ.

### 10. File hướng dẫn: AGENTS.md hay CLAUDE.md

- **Sự thật đã kiểm:** Claude Code chỉ đọc AGENTS.md khi project **không** có CLAUDE.md.
- **tstack chọn:** một file duy nhất là AGENTS.md (dùng chung được cho Codex, Cursor...). Nếu buộc phải có CLAUDE.md thì nó chỉ chứa `@AGENTS.md`. AGENTS.md giữ gọn: một đoạn mô tả luồng request, Navigation, "When something breaks", khối `## Agent skills` trỏ tới doc cấu hình.

### 11. Skill nào luôn hiện, skill nào chỉ chạy khi gọi

- **Matt (ADR):** skill người gọi (`disable-model-invocation: true`) điều phối; skill model tự gọi chứa kỷ luật. Skill người gọi được gọi skill model; không bao giờ gọi skill người gọi khác (bảo người dùng chạy).
- **tstack chọn:** giữ nguyên quy tắc. 18 luồng là user-invoked (0 token cho tới khi gọi), 20 kỷ luật là model-invoked với mô tả được siết lại. Plugin tốn ≈ 1,8k token luôn-bật, cộng ≈ 0,34k cho khối working agreements trong `~/.claude/CLAUDE.md` (đều đo bằng `/context`).
- **Đã kiểm:** trường `paths:` của skill **không** gỡ skill khỏi danh sách luôn-bật, nên không dựa vào nó để tiết kiệm context.

### 12. Cổng vào: một router hay nhiều lệnh rời

- **Matt `ask-matt`:** trả lời "nên dùng skill nào".
- **pstack `poteto-mode`:** phân loại task, chọn playbook, bước hiện rõ.
- **tstack chọn:** `/tstack:work` làm cả hai. `?` trả lời từ bản đồ luồng. Còn lại: chọn playbook, chép từng bước vào task list nguyên văn; bước bỏ qua vẫn nằm đó với `skip: <lý do>`, không bao giờ bỏ im lặng.

### 13. Ticket

- **Matt:** ticket dọc (tracer bullet), vừa một context mới, khai báo quan hệ chặn.
- **pstack:** đơn vị kiểm chứng được, tiêu chí phải fail ở commit xuất phát.
- **tstack chọn:** gộp. Mỗi ticket có tiêu chí chấp nhận fail ở commit xuất phát và một dòng `Verify:` (unit + live). Spec cha mang nhãn `spec` để `afk` không build nguyên spec trong một lần. Nhãn triage chỉ áp khi repo có `docs/agents/triage-labels.md`.

### 14. Nguyên tắc

- **pstack:** 23 skill `principle-*`.
- **tstack chọn:** rút còn 14, gộp các cặp trùng nhau, mỗi nguyên tắc một file (quy tắc, cách áp dụng, phép thử) sau một bảng chỉ mục. Khi trích một nguyên tắc phải nói nó đã đổi quyết định nào; nêu tên mà không có quyết định đi kèm là "name-drop".

### 15. Ship và merge

- **tstack chọn:** mở PR không đồng nghĩa với babysit; babysit không đồng nghĩa với được merge. `land` chỉ chạy khi bạn yêu cầu, và mỗi PR cần kết luận VERIFIED từ agent không viết code đó, tại đúng head SHA hiện tại (ghi kèm base SHA và `git patch-id`; rebase hoặc commit mới làm kết luận mất hiệu lực). Chỉ dùng `gh`.

### 16. Plan mode

- **tstack chọn:** chặn tool `EnterPlanMode` để model không tự vào plan mode; grilling thay thế nó. Bạn vẫn bật plan mode tay bằng Shift+Tab khi muốn.

## Bỏ ra và lý do

| Thứ bị bỏ | Nguồn | Lý do |
|---|---|---|
| `make-bot-ui`, `setup-pstack`, `poteto-agent` | pstack | Gắn chặt với Cursor. |
| Gói benny (Slack triage tự động) | pstack | Gắn với Cursor Automations và Slack. Giữ lại ý tưởng: chuẩn tái hiện hai lần, trạng thái phân biệt, kiểm chéo chỉ đọc (nằm trong `prove` và `create-verify`). |
| arena, swarm, panel ba model, quét bảy nguồn mặc định | pstack | Đắt và cần nhiều hãng model. Phần hữu ích còn lại: "gap không phải là pass", seat ngoài opt-in, quét MCP khi được yêu cầu. |
| `teach`, `recall`, `automate-me` | pstack | Ưu tiên thấp, trùng tên, hoặc không thuộc kỹ thuật phần mềm. |
| `scaffold-exercises`, `writing-fragments/shape/beats`, `loop-me`, `teach`, `migrate-to-shoehorn` | Matt | Công cụ khoá học, viết bài, hoặc gắn một thư viện. |
| Graphite `gt`, CLI `origin` | pstack | Thay bằng `gh`. |

## Sự thật về Claude Code đã kiểm (2.1.283)

- `autoCompactWindow` tính bằng token (100000 đến 1000000), không phải phần trăm.
- `statusLine` là object `{"type": "command", "command": "..."}`. Payload có `context_window.total_input_tokens`, `context_window.context_window_size`, `used_percentage`, `model.display_name`, `effort.level`, `workspace.current_dir`.
- Hook PreCompact nhận `trigger: manual | auto`.
- Agent của plugin bỏ qua `hooks`, `mcpServers`, `permissionMode` trong frontmatter; `tools` và `disallowedTools` vẫn có hiệu lực. Vì thế `verifier` không có danh sách `tools` (để dùng được tool trình duyệt MCP) mà chỉ cấm Edit, Write, NotebookEdit.
- Subagent không spawn được subagent: mọi fan-out (review, verify, worker) chạy từ luồng chính.
- `/loop` cần `CronCreate` và `ScheduleWakeup`, nên hai tool này không bị chặn.
- `${CLAUDE_SKILL_DIR}` và `${CLAUDE_PLUGIN_ROOT}` dùng được trong skill và hook; tstack dùng `${CLAUDE_SKILL_DIR}/../<skill>/...` để trỏ chéo giữa các skill.
- Marketplace kiểu thư mục (`source: directory`) được nạp **tại chỗ**: sửa file trong thư mục plugin có hiệu lực ở session mới hoặc sau `/reload-plugins`, không cần cài lại. Vì thế thư mục phải ở yên sau khi cài.
- Claude Code từ chối `settings.json` không phải JSON chuẩn (có comment, dấu phẩy thừa): cả plugin CLI cũng lỗi. Installer kiểm trước và dừng sớm.
- Khi gỡ, plugin CLI để lại `"enabledPlugins": {}` và `"extraKnownMarketplaces": {}`. Installer chụp `settings.json` trước khi CLI đụng vào, nên vẫn trả về đúng từng byte khi bạn không sửa gì khác.
- `claude -p "/context"` chạy được ở chế độ headless: đây là cách đo ngân sách context.
