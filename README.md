# tstack

Bộ setup hợp nhất cho **Claude Code**, gom những phần tốt nhất của hai bộ:

- **`skills` của Matt Pocock** (v1.2.3): căn chỉnh trước khi build (grilling), giữ context trong "smart zone", spec → tickets → TDD, review tách trục, ngôn ngữ domain (CONTEXT.md, ADR).
- **`pstack` của Lauren Tan** (v0.15.5) và bài nói "How I Shipped 2000 PRs": chứng minh trên sản phẩm thật (verify skill + feature map), kỷ luật bằng chứng, mã hoá bài học vào cấu trúc, chạy không giám sát có hợp đồng, review đối kháng.

Tên gọi theo kiểu pstack: **t**stack = stack của Tùng. Mọi lệnh có tiền tố `/tstack:`.

## Năm trụ cột

| # | Trụ cột | Nguồn | Trong tstack là gì |
|---|---|---|---|
| 1 | **Căn chỉnh trước khi build** | Matt | `grill-with-docs` / `grill-me` hỏi từng vòng tới khi người và agent chung một thiết kế. Sự thật (facts) là việc của agent, quyết định là việc của người. Câu hỏi "cách nào tốt hơn" mà chạy thử được thì agent tự làm `prototype`. |
| 2 | **Ở trong smart zone** (~150k token đầu) | Matt | Context luôn-bật chỉ ~2,1k token. Chỉ đường (pointer) thay vì nhồi nội dung. Việc đọc rộng giao subagent. Người quyết định ranh giới pha: tiếp tục, `/clear`, handoff, subagent hay `/compact`. Status line đổi màu khi gần mép. |
| 3 | **Chứng minh trên artifact thật** | pstack | Mỗi app có verify skill + feature map (`/tstack:create-verify`). Người viết không tự chấm: agent `verifier` với context sạch kiểm lại. Kết luận VERIFIED / NOT VERIFIED / INCONCLUSIVE, kèm đường dẫn bằng chứng. Inconclusive không phải là pass. |
| 4 | **Mã hoá bài học vào cấu trúc** | pstack | Thang ưu tiên: không thể sai (type, kiến trúc) > phân tích tĩnh (lint, hook, CI) > chuẩn review (`CODING_STANDARDS.md`) > skill hoặc pointer doc > một dòng trong AGENTS.md. `/tstack:reflect` đưa mỗi bài học lên nấc cao nhất có thể. |
| 5 | **Tự chủ có hợp đồng** | pstack | Việc đảo ngược được thì cứ làm. Force-push nhánh chung, deploy, xoá dữ liệu, nhắn tin cho người khác thì luôn dừng. Chạy qua đêm (`/tstack:afk`) cần hợp đồng viết (mục tiêu, điều kiện xong kiểm được, cách ly, quyền cấp trước, lối thoát, danh sách luôn dừng, chỉ thị thường trực), decision log và báo cáo buổi sáng. Hook `guard_git.py` chặn các lệnh git phá huỷ. |

## Cài đặt

Cần: Claude Code (đã kiểm trên 2.1.283), `python3`, `git`. Dùng GitHub thì cần thêm `gh`.

```bash
cd ~/Desktop/plugins/tstack
./install.sh --dry-run    # xem trước, không đổi gì
./install.sh              # cài hoặc cập nhật; chạy lại bao nhiêu lần cũng an toàn
```

Khởi động lại Claude Code, rồi trong từng repo:

```text
/tstack:setup            một lần mỗi repo: tracker, AGENTS.md, CODING_STANDARDS.md, hook theo stack
/tstack:create-verify    một lần mỗi app: verify skill + feature map
/tstack:work ?           bất cứ lúc nào: "giờ nên chạy lệnh gì?"
```

Installer làm bốn việc, việc nào cũng tắt được:

| Phần | Làm gì | Bỏ qua bằng |
|---|---|---|
| Plugin | Thêm marketplace từ thư mục này và cài `tstack@tstack` (scope user). Plugin được nạp **tại chỗ** từ thư mục này: đừng xoá hay di chuyển nó sau khi cài (nếu đã di chuyển, chạy lại `./install.sh` từ chỗ mới). | `--no-plugin` |
| Status line | Chép `statusline.py` vào `~/.claude/tstack/`: số token context, %, model, effort, màu smart zone. | `--no-statusline` |
| Settings | Merge `templates/user/settings.json` vào `~/.claude/settings.json`. Giá trị bạn đã đặt luôn thắng (báo "kept yours"), danh sách được hợp nhất, mục bạn đã tự xoá sẽ không bị thêm lại khi chạy lại, có backup `settings.json.tstack-backup-<thời điểm>`. File không phải JSON hợp lệ thì installer dừng trước khi đổi bất cứ gì. | `--no-settings` |
| CLAUDE.md | Chèn 7 "working agreements" vào `~/.claude/CLAUDE.md`, giữa `<!-- tstack:begin -->` và `<!-- tstack:end -->`. | `--no-claude-md` |

Gỡ: `./install.sh --uninstall` gỡ plugin và chỉ xoá đúng những gì tstack đã thêm; những gì bạn tự thêm sau khi cài vẫn giữ nguyên. Nếu từ lúc cài bạn chưa sửa gì khác, `settings.json` và `CLAUDE.md` trở về giống hệt từng byte (kể cả phần plugin CLI đã ghi vào). Các file backup `*.tstack-backup-*` được để lại.

Kiểm thử installer: `bash tests/test_install.sh` chạy toàn bộ cài, chạy lại, gỡ bằng `claude` CLI thật trong một HOME tạm, không đụng tới `~/.claude` của bạn.

Cài tay, không qua script: trong Claude Code gõ `/plugin marketplace add <đường dẫn tới thư mục tstack>` rồi `/plugin install tstack@tstack`.

### Settings được thêm, và vì sao

| Khoá | Giá trị | Lý do |
|---|---|---|
| `autoMemoryEnabled` | `false` | Trí nhớ nằm trong code, type, `CODING_STANDARDS.md` và skill, nơi ai cũng đọc và review được, không nằm trong ghi chú ẩn (trụ 4). |
| `disableClaudeAiConnectors` | `true` | Bớt tool luôn-bật (trụ 2). Nếu bạn dùng connector claude.ai (Linear, Sentry, Slack...) cho tracker hoặc `tstack:why`, xoá dòng này khỏi `~/.claude/settings.json` (hoặc đặt `false`, với điều kiện không nơi nào khác đặt `true`). |
| `disableWorkflows`, `enableArtifact` | `true`, `false` | Bớt tool không dùng khi code. Bật lại khi cần. |
| `effortLevel` | `"medium"` | Mặc định tiết kiệm. Các skill cần phán đoán (grilling, codebase-design, diagnose, interrogate, reflect) tự nâng lên `high`. |
| `cleanupPeriodDays` | `60` | Giữ transcript đủ lâu cho `/tstack:reflect` và playbook pickup. |
| `permissions.deny` | DesignSync, PushNotification, RemoteTrigger, ReportFindings, EnterPlanMode | Tool không dùng trong luồng này. Grilling thay cho plan mode; bạn vẫn bật plan mode tay bằng Shift+Tab được. Cố ý **không** chặn NotebookEdit (Python), CronCreate và ScheduleWakeup (`/loop` cần), AskUserQuestion. |
| `statusLine` | status line tstack | Chỉ đặt khi bạn chưa có status line riêng. |

## Luồng hằng ngày

**Luồng chính: ý tưởng → PR**

```text
/tstack:grill-with-docs <ý tưởng>      căn chỉnh; CONTEXT.md và ADR cập nhật ngay trong lúc hỏi
  ├─ vừa một smart zone  → /tstack:implement
  └─ lớn hơn             → /tstack:to-spec → /tstack:to-tickets
                            → mỗi ticket: /clear rồi /tstack:implement <ticket>
/tstack:ship                            PR: commit có thứ tự, body kiểu briefing, bằng chứng
/tstack:ship babysit <PR>               conflict → review thread → CI; không bao giờ tự merge
/tstack:reflect                         sau task dài hoặc gập ghềnh: lỗi lặp → type, lint, hook, chuẩn
```

Grill, spec và tickets nên nằm trong cùng một cửa sổ context liền mạch. Giữa các ticket thì `/clear`: spec, ticket và commit đã giữ đủ ngữ cảnh.

`/tstack:implement` đi theo build playbook: đặt tên hình dạng dữ liệu trước → kiểm thiết kế ở ranh giới module → TDD tại các seam đã thống nhất → `verifier` chứng minh trên app thật → commit nhỏ kiểu Conventional → `interrogate` review bằng các subagent sạch → sửa mục "Act on" → đóng ticket kèm SHA, kết luận và bằng chứng.

**Các tình huống khác**

| Tình huống | Lệnh |
|---|---|
| Không biết bắt đầu từ đâu | `/tstack:work <mô tả>` (tự chọn playbook) hoặc `/tstack:work ?` |
| Có bug | `/tstack:work <triệu chứng>`: diagnose → commit test đỏ trước → sửa tận gốc → prove (tái hiện hai lần trước, hai lần sau) |
| Chậm một lần / tối ưu một chỉ số qua nhiều lần thử | `/tstack:work`: playbook perf / hillclimb |
| Refactor, đổi hàng loạt, migration | `/tstack:work`: playbook refactor / wide-change |
| Đi ngủ, để agent tự chạy | `/tstack:afk <mục tiêu hoặc tickets> done: <điều kiện kiểm được>` |
| Việc lớn, còn mù mờ | `/tstack:wayfinder` |
| Issue và PR người khác gửi | `/tstack:triage` |
| Chuyển việc sang session hoặc người khác | `/tstack:handoff` |
| Tin nhắn của agent khó hiểu | `/tstack:wait-what` |
| Session chậm, ồn, tốn token | `/tstack:context-audit` |
| App đã đổi, verify skill lệch | `/tstack:maintain-verify` |
| Lúc rảnh | `/tstack:improve-architecture` |

**Ranh giới pha.** Hết một pha thì chọn một trong năm: tiếp tục; `/clear` (mặc định giữa các ticket, và khi phân vân 50/50); `/tstack:handoff`; giao phần còn lại cho subagent; `/compact <chỉ dẫn>` (cách cuối, không phải phản xạ đầu). Nếu auto-compact tự bắn, hook sẽ nhắc: một ranh giới đã bị bỏ lỡ.

**Status line.** Xanh dưới 2/3 mép smart zone (100k với mặc định); vàng tới mép 150k ("near edge"); đỏ khi quá mép ("dumb zone: clear, hand off or compact at the next boundary"). Đổi mép bằng biến môi trường, ví dụ `TSTACK_SMART_ZONE=200k`.

## Danh mục

### 18 lệnh (user-invoked: 0 token cho tới khi bạn gọi)

| Lệnh | Việc | Lấy từ |
|---|---|---|
| `work` | Cổng vào duy nhất: phân loại task, chọn playbook (feature, bug, perf, hillclimb, refactor, wide-change, investigation, pickup, pause, figure-it-out), chép từng bước vào task list; bước bỏ qua vẫn ghi `skip: <lý do>`. `?` trả lời "lệnh nào tiếp theo". | Matt ask-matt + pstack poteto-mode và playbooks |
| `grill-me`, `grill-with-docs` | Phỏng vấn tới khi chung thiết kế (ngoài repo / trong repo có cập nhật CONTEXT.md, ADR). | Matt |
| `to-spec` | Tổng hợp hội thoại thành spec trên tracker, có mục Verification. Không phỏng vấn thêm. | Matt to-spec + pstack |
| `to-tickets` | Cắt spec thành ticket dọc (tracer bullet) có quan hệ chặn, tiêu chí chấp nhận fail ở commit xuất phát, dòng `Verify:`. | Matt to-tickets + pstack sequence-verifiable-units |
| `implement` | Build một ticket hoặc spec nhỏ theo build playbook. | Matt implement + pstack feature playbook |
| `afk` | Chạy không giám sát theo hợp đồng: mỗi đơn vị một `ticket-worker` mới, `verifier` độc lập, review, decision log, ledger, báo cáo buổi sáng. | pstack figure-it-out, autonomous-run, orchestrate + Matt AFK |
| `ship` | Mở PR (deslop, commit có thứ tự, body briefing), babysit, land khi được yêu cầu. | pstack opening-a-pr, babysit, shipping + Matt |
| `reflect` | Bài học lặp lại → nấc mạnh nhất của thang; chỉ áp dụng dòng bạn duyệt. | pstack reflect + Matt retro |
| `setup` | Cấu hình repo: tracker, domain docs, AGENTS.md gọn, `CODING_STANDARDS.md`, gitignore `.tstack/`, hook theo stack. | Matt setup + pstack |
| `create-verify`, `maintain-verify` | Tạo và giữ verify skill + feature map cho từng app (web, CLI, API, mobile). | pstack |
| `context-audit` | Đo context luôn-bật và cắt tỉa (ba phép thử: một nguồn sự thật, trầm tích, câu vô nghĩa). | Matt + tstack |
| `improve-architecture` | Khảo sát cơ hội "làm sâu module", xuất báo cáo HTML, rồi grill phương án bạn chọn. | Matt |
| `wayfinder` | Bản đồ ticket quyết định cho việc lớn hơn một spec. Tuỳ chọn. | Matt |
| `triage` | Máy trạng thái triage cho issue và PR bên ngoài. Tuỳ chọn. | Matt |
| `handoff` | Nén hội thoại thành tài liệu bàn giao. | Matt |
| `wait-what` | Nói lại tin nhắn cuối bằng lời đơn giản, kèm ngữ cảnh còn thiếu. | Matt wait-what + pstack bro |

### 20 kỷ luật (model-invoked: agent tự nạp khi cần; phần mô tả luôn nằm trong context, tổng ~1,4k token)

| Skill | Việc | Lấy từ |
|---|---|---|
| `grilling` | Hỏi theo vòng, mỗi câu có đáp án đề xuất; facts qua subagent. | Matt + pstack "observe, don't ask" |
| `domain-modeling` | CONTEXT.md và ADR, cập nhật ngay khi thuật ngữ chốt. | Matt |
| `codebase-design` | Deep module, bắt đầu từ cách gọi, design it twice, ARCHITECT.md cho ranh giới module. | Matt + pstack architect |
| `principles` | 14 nguyên tắc có tên làm từ vựng lái quyết định. | pstack (23 → 14) + Matt |
| `tdd` | Red-green tại seam đã thống nhất; khi nào bỏ qua; test nào đáng giữ. | Matt + pstack |
| `diagnose` | Vòng phản hồi đỏ trước, giả thuyết xếp hạng, sửa tận gốc; nhánh perf và forensics. | Matt diagnosing-bugs + pstack |
| `prove` | Chứng minh trên artifact thật, kết luận ba mức, blast radius. | pstack prove-it-works + blast-radius |
| `interrogate` | Review song song theo trục (standards, spec, adversarial) rồi phân loại Act on / Consider / Noted / Dismissed. | Matt code-review + pstack interrogate |
| `how`, `why` | Giải thích code chạy thế nào; vì sao code có hình dạng này (git archaeology, MCP khi được yêu cầu). | pstack |
| `prototype` | Code dùng một lần để trả lời một câu hỏi thiết kế. | Matt + pstack |
| `research` | Nghiên cứu nguồn gốc trong agent chạy nền, lưu một file Markdown có trích dẫn. | Matt |
| `decision-log` | Nhật ký quyết định TSV chỉ-ghi-thêm, kiểm toán cuối run. | pstack show-me-your-work |
| `unslop` | Văn xuôi cho người đọc, bỏ dấu vết "văn AI". | pstack |
| `writing-for-agents` | Viết và cắt tỉa skill, AGENTS.md, CLAUDE.md; eval mù cho thay đổi skill. | Matt + pstack |
| `resolving-merge-conflicts` | Giải conflict theo ý định của mỗi bên. | Matt |
| `wizard` | Sinh wizard bash cho bước chỉ người làm được. | Matt |
| `typescript`, `python`, `mobile` | Kỷ luật type theo stack: parse ở biên, sum type vét cạn, brand/NewType, kiểm tra review; mobile có phần lái simulator/emulator. | pstack typescript-best-practices + Matt, mở rộng cho Python và Swift/Kotlin/Dart |

### 5 subagent

| Agent | Việc |
|---|---|
| `standards-reviewer` | Trục chuẩn: chuẩn của repo + baseline (code smell, comment nên giữ). Không có Edit/Write. |
| `spec-reviewer` | Trục spec: thiếu, làm nửa vời, làm quá phạm vi, làm sai. Không có Edit/Write. |
| `adversary` | Trục đối kháng: cố làm hỏng diff (đúng/sai, nguyên nhân gốc, lỗ hổng kiểm chứng, bảo mật). Không có Edit/Write. |
| `verifier` | Chứng minh trên app thật bằng verify skill của repo; không bao giờ sửa code sản phẩm. Dùng được cả tool trình duyệt MCP nếu có. |
| `ticket-worker` | Build một đơn vị việc trong context mới, theo brief của `afk`. |

### Hook và script

- **`hooks/guard_git.py`** (PreToolUse, Bash). Chặn:
  - `git push --force` (cho phép `--force-with-lease`), `push --all`, `--mirror`, `--delete`, refspec `+x` hoặc `:x`;
  - push thẳng lên nhánh bảo vệ, kể cả `git push origin HEAD`, tên nhánh tính lúc chạy (`$(git branch --show-current)`, `"$BRANCH"`), hay `git push` trơn khi đang đứng trên nhánh đó. Mặc định: `main`, `master`, `trunk`, `develop`, `production`, `prod`, `release`, `release/*`. Thêm nhánh cho một repo: `git config --add tstack.protectedBranches staging` (bạn tự chạy; git config chỉ thêm được, không bớt được, và agent không được sửa khoá `tstack.*`). Thay hẳn danh sách: biến `TSTACK_PROTECTED_BRANCHES="main,staging"` khi khởi động Claude Code;
  - bỏ qua hook: `--no-verify`, `commit -n`, `HUSKY=0`, `SKIP=...`, `-c core.hooksPath=...`, trỏ `core.hooksPath` ra ngoài repo hoặc vào thư mục không có file hook (trỏ vào thư mục trong repo đã có `pre-commit`, `pre-push`... như `.githooks` thì được);
  - vứt việc: `reset --hard`, `clean -f`, `branch -D`, `checkout -f`, `switch --discard-changes`, `checkout .` / `restore .` / `rm -f .` (cả cây làm việc; thao tác trên file có tên thì được), `stash drop/clear`, `worktree remove --force`;
  - viết lại hoặc xoá lịch sử: `filter-branch`/`filter-repo`, `update-ref -d`, `reflog expire`, `gc --prune=now`;
  - `rm -r` trên `/`, `~`, `$HOME`, `.`, `..`, `*`, `.git`.

  Guard đọc lệnh như shell: chữ trong nháy, trong heredoc có delimiter trong nháy, hay trong comment là dữ liệu, không phải lệnh (commit message nhắc tới `git reset --hard` vẫn qua). Còn `$(...)`, backtick, heredoc hay `echo ... |` đưa vào `bash`/`sh` thì shell chạy thật, nên được kiểm như lệnh; `sudo`, `env`, `timeout`, `xargs`, `flock`, `bash -c`, `eval`, hàm, vòng lặp, subshell cũng vậy. Đây là dây an toàn chống tai nạn, không phải hàng rào chống người cố tình lách. Agent bị chặn sẽ được bảo nhờ bạn tự chạy nếu thật sự cần. Tắt cho một lần khởi động: `TSTACK_GIT_GUARD=off claude`. Kiểm thử: `python3 tests/test_guard_git.py` (165 ca, gồm cả các lệnh thường ngày phải được cho qua).
- **`hooks/precompact_notice.py`** (PreCompact, auto). Nhắc rằng một ranh giới pha đã bị bỏ lỡ.
- **`bin/statusline.py`**, **`bin/merge_settings.py`**, **`bin/claude_md.py`**, **`install.sh`**.
- **`tests/check_refs.py`**: sau khi sửa skill, kiểm mọi `tstack:<tên>`, link và đường dẫn còn trỏ đúng, và không skill nào gọi nhầm một lệnh chỉ-người-gọi.

## Ngân sách context

Đo bằng `claude -p "/context"` trên Claude Code 2.1.283: tstack thêm khoảng **2,1k token luôn-bật**: 20 kỷ luật ≈ 1,4k, 5 agent ≈ 0,4k, và 7 working agreements trong `~/.claude/CLAUDE.md` ≈ 0,34k. 18 lệnh tốn 0 token cho tới khi gọi. (Lệnh `claude plugin details` báo cao hơn vì nó tính cả mô tả của skill chỉ-người-gọi.) Thân skill chỉ nạp khi dùng; file phụ (RUBRIC.md, playbooks, sources...) chỉ đọc khi skill trỏ tới.

Sau khi cài, chạy `/context` để tự kiểm, và `/tstack:context-audit` khi thấy session nặng.

## Trong repo của bạn

`/tstack:setup` và `/tstack:create-verify` tạo ra:

| Đường dẫn | Là gì |
|---|---|
| `AGENTS.md` | File hướng dẫn duy nhất (dùng được cho nhiều harness). Gọn: một đoạn mô tả luồng request, Navigation, "When something breaks", khối `## Agent skills` trỏ tới các doc bên dưới. Nếu repo buộc phải có `CLAUDE.md` thì nó chỉ chứa `@AGENTS.md`. |
| `CODING_STANDARDS.md` | Luật review. Agent review đọc; agent code không phải trả giá mỗi request. |
| `docs/agents/issue-tracker.md`, `domain.md`, `triage-labels.md` | Tracker (GitHub, GitLab hoặc file markdown cục bộ), cấu trúc domain, nhãn triage (tuỳ chọn). |
| `CONTEXT.md`, `docs/adr/` | Từ điển domain và quyết định kiến trúc. |
| `.claude/skills/verify-<app>/` | Verify skill + `features/` (feature map) của từng app. |
| `.claude/settings.json` | Hook và quyền theo stack (format, lint, typecheck). |
| `.tstack/<slug>/` | Trạng thái việc dài hoặc không giám sát: `contract.md`, `ledger.tsv`, `decisions.tsv`, `evidence/`, `report.md`. Được gitignore. |

## Tuỳ biến

- **Luật review mới:** thêm một dòng vào `CODING_STANDARDS.md` của repo. Luật mà regex hoặc type ép được thì làm lint, hook hoặc type thay vì viết thành chữ.
- **Model khác hãng:** mọi chỗ có thể dùng `codex` hoặc `gemini` (reviewer của `interrogate`, người soát decision log, một ghế trong design it twice, giám khảo eval) chỉ gửi dữ liệu đi khi bạn yêu cầu trong task (ví dụ `/tstack:work ... external`, hay nói thẳng) hoặc AGENTS.md / CODING_STANDARDS.md của repo cho phép rõ ràng. Mặc định không có code hay transcript nào rời máy.
- **Sửa skill:** sửa ngay trong thư mục này; mở session mới hoặc chạy `/reload-plugins` là có hiệu lực, không cần cài lại. Viết skill mới theo `tstack:writing-for-agents`.
- **Tắt guard git tạm thời:** `TSTACK_GIT_GUARD=off claude`.

## Cấu trúc

```text
tstack/
├── .claude-plugin/        plugin.json, marketplace.json
├── skills/                38 skill (18 lệnh + 20 kỷ luật), mỗi skill một thư mục
├── agents/                5 subagent
├── hooks/                 hooks.json, guard_git.py, precompact_notice.py
├── bin/                   statusline.py, merge_settings.py, claude_md.py
├── tests/                 test_guard_git.py, test_install.sh, check_refs.py
├── templates/user/        settings.json, CLAUDE.md (cho ~/.claude)
├── templates/project/     AGENTS.md, CODING_STANDARDS.md, docs/agents/* (cho repo)
├── docs/DECISIONS.md      các xung đột giữa hai bộ và lựa chọn của tstack
├── install.sh
├── CREDITS.md
└── LICENSE
```

Đọc thêm: [docs/DECISIONS.md](docs/DECISIONS.md) cho lý do của từng lựa chọn, [CREDITS.md](CREDITS.md) cho nguồn gốc từng phần.
