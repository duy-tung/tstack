# Chuyển tstack sang Pi và tích hợp vào pi-config: khảo sát

Tài liệu nghiên cứu, chưa đổi code. Mục tiêu: tstack chạy trên **Pi 0.87.1** thay cho Claude Code và được cài qua [pi-config](https://github.com/duy-tung/pi-config). Mọi khẳng định về Pi được kiểm trên mã và tài liệu của bản đã ghim: `@earendil-works/pi-coding-agent@0.87.1`, `@tintinweb/pi-subagents@0.19.0`, `rpiv-todo`, `rpiv-ask-user-question` 2.11.0, `pi-open-tui@0.3.8` và pi-config ở commit `94d8418`. Chỗ nào còn phải chạy thật mới biết thì ghi **(cần kiểm)**.

> **Đã triển khai (khác đề xuất ở §5):** theo mục tiêu "một bộ setup all-in-one", tstack không được ghim như một package riêng. Bộ skill đã chuyển sang Pi nằm thẳng trong pi-config (`assets/skills/`, thay nguồn mattpocock), kèm:
> - vai `verifier` trong model-roles;
> - git guard trong pi-auto-mode, cùng quyết định với `guard_git.py` trên hơn 5.000 lệnh;
> - extension `smart-zone` (footer, nhắc compaction, `/context-budget`);
> - `afk` chạy trên pi-goal-x.
>
> Xem nhánh `claude/gracious-allen-88a1r0` của pi-config và `docs/workflow.md` ở đó. Repo này giữ bản cho Claude Code (1.0.0).

## Kết luận ngắn

1. **Phần lớn chuyển được, chủ yếu là thay chữ.** Pi theo chuẩn Agent Skills: `SKILL.md` với `name`, `description`, `disable-model-invocation`. Skill có cờ này bị ẩn khỏi danh sách của model, giống hệt ngữ nghĩa "user-invoked" của tstack. Pi tự giải đường dẫn tương đối theo thư mục skill. Các khoá lạ (`effort`, `paths`, `argument-hint`) bị bỏ qua, không báo lỗi. Trong 38 skill: 5 chạy nguyên, 15 chỉ cần thay chữ, 18 cần sửa ngữ nghĩa (subagent, hỏi người dùng, transcript, hook).
2. **Vướng lớn nhất khi tích hợp: trùng tên.** pi-config đang cài `mattpocock/skills/engineering`, và 13 tên trùng với tstack. Khi trùng, Pi giữ skill tìm thấy đầu tiên. tstack vốn là bản kế thừa của bộ này, nên **đề xuất thay hẳn nguồn mattpocock bằng tstack**.
3. **Hook và status line phải viết lại thành extension TypeScript.** Không gọi `python3` được: pi-config chạy cả Windows, nơi không chắc có Python. `guard_git.py` chuyển sang `tool_call` (trả `{block:true}`), PreCompact chuyển sang `session_before_compact`, status line chuyển sang `ctx.ui.setStatus`. pi-open-tui đã hiển thị status của extension ở footer.
4. **pi-config đã có sẵn nhiều thứ tstack cần.** `todo` thay TaskCreate, `ask_user_question` thay AskUserQuestion, `Agent`/`get_subagent_result` thay Agent tool, `bg_run` (tự đánh thức phiên khi job xong) thay background Bash và `/loop`, `$PI_SESSION_ID`/`$PI_SESSION_FILE` thay `${CLAUDE_SESSION_ID}` và `~/.claude/projects`. pi-config cũng có sẵn auto mode, goal kèm auditor và advisor. Việc còn lại là quyết định cho các phần trùng vai: `afk` với `/goal`, git guard với auto mode.
5. **Đề xuất kiến trúc:** tstack 2.0 thành Pi-native và đóng gói như một Pi package (skills, extension, agents). pi-config ghim nó theo commit trong `sources.lock.json`, nạp qua `settings.packages` và sinh file role cho 5 agent từ model-roles. Giữ `v1.0.0` làm bản Claude Code cuối cùng (tag). Không duy trì song song hai harness (lý do ở §6).

## 1. Đối chiếu khái niệm

| Claude Code (tstack 1.0) | Pi 0.87.1 + pi-config | Ghi chú |
|---|---|---|
| Plugin `tstack@tstack`, lệnh `/tstack:<name>` | Pi package; skill gọi bằng `/skill:<name>` (`enableSkillCommands` mặc định bật) | Pi không có namespace plugin. Tên skill không được chứa `:` (chỉ `a-z0-9-`). |
| Skill tool ("Call the Skill tool with tstack:X") | Model tự `read` `SKILL.md` theo `<location>` trong `<available_skills>` | Pi không có Skill tool. Đổi thành "Load the `X` skill (read its SKILL.md)". |
| `disable-model-invocation: true` | Như nhau: skill bị ẩn khỏi prompt, chỉ `/skill:name` gọi được | Model không thấy đường dẫn của skill user-invoked, nên luật "user-invoked không gọi user-invoked" nay được runtime ép luôn. |
| `${CLAUDE_SKILL_DIR}/x` | Đường dẫn tương đối `x` | Pi chèn "References are relative to `<baseDir>`" khi mở rộng `/skill:` và dặn model giải đường dẫn tương đối theo thư mục skill. |
| `effort: high` | Không có. Thinking đặt theo phiên hoặc theo role | Parent của pi-config đã chạy Opus/high, nên bỏ khoá này là đủ. |
| `paths:` | Bị bỏ qua | tstack vốn không dựa vào khoá này (DECISIONS §11). |
| `argument-hint` | Chỉ prompt template dùng; skill bỏ qua | Đối số sau `/skill:name` được nối vào cuối skill như một yêu cầu của người dùng. |
| `agents/*.md` (`tools: Read, Grep, Glob, Bash`, `disallowedTools`, `model: inherit`) | Agent file của pi-subagents: `tools: "read, grep, find, ls, bash"`, `disallowed_tools`, `extensions: [...]`, `model`/`thinking` | pi-config sinh model/thinking từ `model-roles.json`. Role phải nạp `pi-auto-mode` và `pi-anthropic-auth`, nếu không auto mode chặn spawn. |
| `tstack:verifier` (subagent_type) | `verifier` | pi-subagents bỏ qua file có `name` chứa `:`. |
| `Explore`, `general-purpose` | Bị tắt (`disableDefaultAgents: true`) | Explore thay bằng `researcher` (chỉ đọc, GLM flash). General-purpose thay bằng `worker` hoặc `researcher` tuỳ việc có ghi file không. |
| Spawn song song "in one message" | Nhiều lời gọi `Agent` trong một lượt; mặc định chạy nền, lấy kết quả bằng `get_subagent_result` | Tối đa 4 agent nền và 2 foreground; vượt thì xếp hàng. |
| Subagent không spawn được subagent | Như nhau khi không đặt `allowed_subagents` | Giữ nguyên bất biến "main thread là nơi duy nhất spawn". |
| `isolation: worktree` | Có, nhưng pi-config đặt `worktreeIsolation: false` | Ảnh hưởng `afk` (chạy unit song song) và `hillclimb`. Xem §4.6. |
| TaskCreate / TodoWrite | Tool `todo` (rpiv-todo) | AGENTS.md của pi-config dặn: khi có goal thì goal là nguồn tiến độ. |
| AskUserQuestion | `ask_user_question` (`{questions:[{question, header, options}]}`) | |
| Background Bash, `/loop`, `gh pr checks --watch` | `bg_run {command, triggerOnCompletion:true}` | Job xong thì Pi tự mở lượt mới, thay được cả `/loop`. |
| `claude --bg` (handoff) | Không có | AGENTS.md của pi-config cấm dùng `bg_run` để mở CLI agent khác. Bỏ `--bg`; hướng dẫn `/clear` rồi `/skill:... Read <path>`. |
| `claude -p "/context"` | Không có `/context`. `before_agent_start` cho `systemPromptOptions` (sections, contextFiles, skills, selectedTools); `ctx.getContextUsage()` | Cần một lệnh extension `/context-budget` để đo. Xem §4.4. |
| `${CLAUDE_SESSION_ID}`, `~/.claude/projects/<cwd>/<id>.jsonl` | `$PI_SESSION_ID`, `$PI_SESSION_FILE`; `<agent-dir>/sessions/--<path>--/<ts>_<id>.jsonl` | Pi chỉ tiêm hai biến này vào tool `bash`. Định dạng JSONL khác (session v3), nên chỉ dẫn đọc transcript trong `reflect` và `pickup` phải viết lại. |
| PreToolUse hook (exit 2 + stderr) | `pi.on("tool_call")` trả `{block:true, reason}` | Handler ném lỗi thì tool bị chặn (fail-safe). Guard hiện tại làm ngược lại: lỗi parser thì cho qua. Phải bắt lỗi bên trong để giữ hành vi. |
| PreCompact `trigger: auto` | `session_before_compact` với `reason: "threshold" \| "overflow"` | Chỉ báo `ctx.ui.notify`, không huỷ compaction. |
| statusLine command | `ctx.ui.setStatus("tstack", text)` + `ctx.getContextUsage()` | pi-open-tui vẽ extension status ở footer (`footer.ts:388`). Footer đã hiện context %, nên tstack chỉ thêm nhãn smart zone. |
| `~/.claude/CLAUDE.md` (7 working agreements) | `<agent-dir>/AGENTS.md` do pi-config quản lý | Xem §5.4. |
| `~/.claude/settings.json` (autoMemory, connectors, EnterPlanMode deny...) | Phần lớn không có tương đương | Xem §3.3. |
| `.claude/skills/verify-<app>/` | `.agents/skills/verify-<app>/` (đề xuất) hoặc `.pi/skills/` | `.agents/skills` là vị trí chuẩn Agent Skills. Pi và pi-subagents đều quét, và cách này không gắn với harness. Nạp project skill cần project trust **(cần kiểm với `.agents/`)**. |
| `.claude/settings.json` của repo (`permissions.allow`, hook format) | Không có tương đương | Auto mode của pi-config chỉ đọc settings trong agent-dir; settings của project không thêm được luật allow. Xem §4.5. |

## 2. Hiện trạng tstack: đo được

- 38 skill (18 user-invoked, 20 model-invoked), 128 file, khoảng 78,6k từ. 5 agent, 2 hook, 3 script trong `bin/`, installer và 3 bộ test.
- Các điểm cần thay:

  | Mẫu | Số lần |
  |---|---|
  | "Call the Skill tool" | 70 (32 file) |
  | `/tstack:<name>` | 96 |
  | `tstack:<name>` trần | 146 |
  | `${CLAUDE_SKILL_DIR}` | 21 |
  | `.claude/` | 43 |
  | `CLAUDE.md` | 29 |
  | `AskUserQuestion` | 7 |
  | `${CLAUDE_SESSION_ID}` | 3 |
  | `$CLAUDE_PROJECT_DIR` | 2 |
  | `claude -p` | 5 |
  | `/compact`, `/clear`, `/context`, `/loop` | khoảng 25 |

- Không skill nào dùng `$ARGUMENTS`, `` !`cmd` ``, `@file` import, `allowed-tools` hay `context: fork`. Mấy cơ chế này mà có thì mới khó chuyển.
- Phân loại:
  - **Chạy nguyên (5):** domain-modeling, principles, resolving-merge-conflicts, unslop, wait-what.
  - **Chỉ thay chữ (15):** diagnose, grill-me, grill-with-docs, grilling, implement, mobile, prototype, python, tdd, to-spec, to-tickets, triage, typescript, wayfinder, wizard.
  - **Sửa ngữ nghĩa (18):**

    | Mức | Skill | Phần phải sửa |
    |---|---|---|
    | Nặng | `interrogate`, `afk`, `context-audit`, `create-verify` / `maintain-verify` | Subagent song song, adapter MCP, đo context |
    | Nặng | `setup` | Ghi `.claude/settings.json` |
    | Vừa | `reflect`, `decision-log` | Transcript |
    | Vừa | `why`, `how`, `research`, `prove` | Loại agent |
    | Vừa | `work` | Task list, ranh giới pha |
    | Vừa | `writing-for-agents` | Tài liệu cơ chế skill và eval |
    | Nhẹ | `codebase-design`, `handoff`, `improve-architecture`, `ship` | |

## 3. Chuyển tstack sang Pi

### 3.1 Skill: codemod cơ học rồi sửa tay

Viết `scripts/port-pi.mjs` chạy một lần, rồi review diff. Luật thay:

| Tìm | Thay | Ghi chú |
|---|---|---|
| `Call the Skill tool with "tstack:X"` | `Load the \`X\` skill (read its SKILL.md)` | Có cả dạng "twice, for A and B" và dạng "with the arguments `<a> b`". Với dạng có đối số: "…and apply it to `<a> b`". |
| `/tstack:X` | `/skill:X` | Là nhãn cho người đọc, không phải lời gọi. |
| `tstack:X` (agent) | `X` | verifier, ticket-worker, standards-reviewer, spec-reviewer, adversary |
| `tstack:X` (skill) | `` the `X` skill `` | |
| `${CLAUDE_SKILL_DIR}/` | (bỏ, dùng đường dẫn tương đối) | Chỗ nào đưa đường dẫn cho subagent thì thêm "as an absolute path". |
| `${CLAUDE_SESSION_ID}` | `$PI_SESSION_ID` | |
| `$CLAUDE_PROJECT_DIR` | `$PWD` hoặc `git rev-parse --show-toplevel` | |
| `.claude/skills/verify-` | `.agents/skills/verify-` | |
| `AskUserQuestion` | `ask_user_question` | |
| `TaskCreate or TodoWrite` / "task list" | "the `todo` tool" | |
| `Explore` agent | `researcher` agent | |
| `general-purpose` (việc chỉ đọc) | `researcher` | |
| `general-purpose` (việc ghi hoặc chạy code, ví dụ prototype) | `worker` | |
| `CLAUDE.md` | `AGENTS.md` | Bỏ các nhánh "or CLAUDE.md". Pi đọc cả hai file, nên luật DECISIONS §10 ("CLAUDE.md chỉ chứa `@AGENTS.md`") không còn cần. |

Phần phải sửa tay:

- **`work/PHASE-BOUNDARIES.md`:**
  - `/clear` giữ nguyên. Với pi-rewind, `/clear` = `/new`, và phiên cũ vẫn quay lại được.
  - `/compact <chỉ dẫn>` giữ nguyên.
  - Thêm `/fork` và `/tree` là lựa chọn mới. Pi có cây phiên nên "quay lại điểm trước" rẻ hơn compact.
  - Sửa ngưỡng: pi-config cho Opus cửa sổ 1M với `reserveTokens` 16.384, nên auto-compaction chỉ bắn khi gần 984k. Câu "nếu auto-compact bắn thì ranh giới đã bị bỏ lỡ" vẫn đúng nhưng gần như không bao giờ xảy ra. Tín hiệu chính giờ là nhãn smart zone ở footer (§4.3).
- **`interrogate`:**
  - Reviewer là agent `standards-reviewer`, `spec-reviewer` và `adversary`. Spawn nền cả ba trong một lượt rồi `get_subagent_result {wait:true}`.
  - Bỏ mẫu "background Bash chạy `codex exec`". Seat khác họ model giờ là chính role của pi-config (§5.3), không cần CLI ngoài.
  - Dòng "Report: in the format your agent definition gives" giữ được, vì body của agent file là system prompt (`prompt_mode: replace`).
- **`afk`:** xem §4.6. Phần `/loop` và `gh pr checks --watch` đổi sang `bg_run … triggerOnCompletion:true`.
- **`context-audit`:** viết lại quanh lệnh `/context-budget` (§4.4). Bảng deny tool của Claude Code (`CHECKLIST.md`) được thay bằng danh sách tool của pi-config và cách tắt: `/agents` → Settings, `lens.json`, `pi config` để bật/tắt resource. Bỏ `context-probe.sh`.
- **`create-verify` / `CONTROL-ADAPTERS.md`:**
  - `claude mcp add playwright` không dùng được, vì pi-config đặt `allowInstall: false` và agent không tự thêm MCP server.
  - Đề xuất ưu tiên script Node/Playwright nằm trong `verify-<app>/scripts/`, vốn trung lập với harness. MCP chỉ dùng khi người dùng đã tự thêm vào `mcp.json`.
  - Tên tool MCP qua `pi-mcp-adapter` là một proxy `mcp {tool, args}`, không phải `mcp__server__tool`.
- **`reflect`, `pickup`, `decision-log`, `writing-for-agents/EVAL.md`:**
  - Transcript lấy từ `$PI_SESSION_FILE` (phiên hiện tại) hoặc `<agent-dir>/sessions/--<cwd>--/`.
  - Mô tả lại định dạng entry (`type: "message"`, `role`…) theo `docs/session-format.md` của Pi.
  - Eval headless dùng `pi -p` thay `claude -p` **(cần kiểm cách launcher của pi-config truyền cờ)**.
- **`why`:**
  - Bỏ `model: sonnet`: pi-config cấm đổi model theo tham số, vì role file là nguồn quyết định model.
  - Investigator dùng role `researcher`, vốn có web tools qua `ext:pi-web-access`. Nhưng researcher **không nạp** `pi-mcp-adapter`, nên nguồn MCP (Linear, Sentry…) phải để parent đọc, hoặc thêm một role riêng.
  - `sources/*.md` giữ nguyên tên tool của server, chỉ đổi cách gọi sang proxy `mcp`.
- **`handoff`:** bỏ `--bg`. Tài liệu bàn giao ghi `/skill:<name>` thay cho `/tstack:<name>`.
- **`setup`:** xem §4.5.
- **`writing-for-agents/SKILL-MECHANICS.md`:** viết lại theo cơ chế Pi:
  - danh sách `<available_skills>` gồm name, description và location;
  - `/skill:` nối đối số vào cuối skill;
  - không có namespace;
  - trùng tên thì skill tìm thấy trước thắng;
  - `/reload` nạp lại.

  Giới hạn độ dài description giữ nguyên (Pi cho tối đa 1024 ký tự).

### 3.2 Agent

Chuyển 5 file sang frontmatter của pi-subagents, body giữ gần nguyên:

```yaml
---
name: adversary
description: "Read-only adversarial reviewer … Spawned by interrogate for risky diffs."
tools: "read, grep, find, ls, bash"
disallowed_tools: "edit, write"
extensions: ["pi-anthropic-auth", "pi-auto-mode", "tstack"]
inherit_context: false
prompt_mode: replace
isolated: false
persist_session: true
max_turns: 0
---
```

- Không ghi `model`/`thinking` trong tstack. pi-config chèn hai khoá này từ model-roles (§5.3).
- `adversary` và `standards-reviewer` đang tìm `RUBRIC.md`/`SMELLS.md` bằng glob dưới `~/.claude/plugins`. Đổi thành: `interrogate` đưa đường dẫn tuyệt đối trong brief. Brief đã có dòng "Read first" nên chỉ cần bỏ đoạn tìm kiếm.
- `verifier` hiện không có `tools` để giữ tool MCP. Trên Pi thì ghi `tools: "*, ext:pi-mcp-adapter/mcp"` và `extensions` có `pi-mcp-adapter` **(cần kiểm tên extension của package)**.
- `ticket-worker` chạy foreground (`run_in_background: false`), giống `worker` của pi-config.
- Mọi role mở đầu bằng "Đọc AGENTS.md…", vì `prompt_mode: replace` không kế thừa context file (pi-subagents đặt `noContextFiles: true`).
- Skill: không đặt `skills:`. Mặc định `true` thì subagent nạp danh sách skill theo `settings.json` của agent-dir, gồm cả đường dẫn của package. Không dùng dạng preload `skills: a, b`: dạng này chỉ tìm ở `.pi/skills`, `.agents/skills`, `<agent-dir>/skills`…, không tìm ở đường dẫn trong settings.

### 3.3 Settings của Claude Code: khoá nào còn nghĩa

| Khoá tstack 1.0 | Trên Pi |
|---|---|
| `autoMemoryEnabled: false` | Không cần: Pi không có auto memory. pi-subagents có `memory:` theo agent nhưng mặc định tắt. |
| `disableClaudeAiConnectors`, `disableWorkflows`, `enableArtifact` | Không có. pi-config đã đặt `workflowsEnabled: false`. |
| `effortLevel: medium` + `effort: high` theo skill | Bỏ. pi-config chọn Opus/high. Muốn tiết kiệm thì `pi-models set main … medium`. Có thể thêm extension nâng thinking khi model `read` một SKILL.md trong danh sách "high". Không đề xuất: đổi thinking giữa phiên làm mất prompt cache. |
| `cleanupPeriodDays: 60` | Không có khoá tương ứng; tài liệu Pi 0.87.1 không nhắc việc tự dọn phiên (phiên là file JSONL dưới `sessions/`). |
| `permissions.deny` (EnterPlanMode…) | Không có plan mode, không cần. |
| `statusLine` | Extension (§4.3). |

### 3.4 Phần bỏ đi

`.claude-plugin/`, `install.sh`, `bin/merge_settings.py`, `bin/claude_md.py`, `bin/statusline.py`, `hooks/*.py`, `tests/test_install.sh` và `templates/user/settings.json`. Việc cài đặt thuộc về pi-config; tstack chỉ cung cấp tài nguyên. `tests/check_refs.py` được viết lại (§4.7).

## 4. Phần phải viết mới: extension `tstack`

Một extension, thư mục `extensions/tstack/` (TypeScript, không phụ thuộc runtime ngoài typebox và các package Pi cung cấp).

### 4.1 Git guard

- Chuyển `guard_git.py` (789 dòng, chỉ dùng stdlib) sang `extensions/tstack/lib/git-guard.ts` dưới dạng hàm thuần `check(command, cwd): {block, reason} | null`. Chuyển luôn 165 ca trong `tests/test_guard_git.py` sang `node --test`, đối chiếu từng ca với bản Python trước khi xoá nó.
- Gắn vào `pi.on("tool_call")` cho `bash` và `bg_run` (cả `powershell` nếu bật). Mọi ngoại lệ bị bắt bên trong và trả `undefined`, để giữ nguyên tắc "lỗi parser không được phá shell". Pi sẽ **chặn** nếu handler ném lỗi.
- `git config` và `git rev-parse` vẫn gọi qua `child_process` với timeout 3 giây.
- `TSTACK_GIT_GUARD=off` và `TSTACK_PROTECTED_BRANCHES` đọc từ môi trường của tiến trình Pi, như trước.
- Câu gợi ý "open a PR with /tstack:ship" đổi thành `/skill:ship`.

Quan hệ với auto mode của pi-config:
- Auto mode có soft-deny cho force-push, `reset --hard`, `clean -f`, `--no-verify`. Nhưng quyết định do bộ phân loại, tức là xác suất. Ở bypass mode thì mọi thứ chạy. Và không có khái niệm **nhánh bảo vệ**.
- Guard của tstack là tất định, chạy ở cả hai mode và có nhánh bảo vệ. Hai lớp bổ sung cho nhau, không trùng.
- Thứ tự: extension `tstack` phải nạp **trước** `pi-auto-mode`. Handler `tool_call` đầu tiên trả `block` sẽ dừng chuỗi, nên lệnh bị guard chặn không tốn một lần gọi classifier. `runtime/merge.mjs` của pi-config luôn đẩy `pi-auto-mode` xuống cuối nên điều kiện này tự thoả **(cần kiểm thứ tự giữa extension của `packages` và `extensions` trong settings)**.
- Lỗ hổng: goal auditor chỉ nạp `pi-auto-mode` (bản vá `auditorPermissionGate`), và subagent chỉ nạp extension có tên trong `extensions:` của role. Cách vá: thêm `"tstack"` vào mọi role, cộng vài luật deny tất định trong `lib/config.mjs` của pi-config làm lớp chặn cuối cho auditor, ví dụ `Bash(git push --force *)`, `Bash(git push -f *)`, `Bash(git reset --hard *)`.

Phương án khác đã cân nhắc: nhúng guard vào `pi-auto-mode/lib/policy.ts` của pi-config. Một cổng duy nhất phủ cả parent, subagent và auditor, nhưng gắn chặt tstack vào mã của pi-config và bắt import chéo repo lúc chạy. Để dành nếu lỗ hổng auditor quan trọng hơn dự kiến.

### 4.2 Nhắc ranh giới pha

`pi.on("session_before_compact", (e, ctx) => { if (e.reason !== "manual") ctx.ui.notify(<thông điệp cũ, đổi /tstack:handoff thành /skill:handoff>, "warning") })`. Không trả `cancel`.

### 4.3 Nhãn smart zone

- Ở `turn_end` và `session_start`, đọc `ctx.getContextUsage()` rồi `ctx.ui.setStatus("tstack", …)`:
  - xanh dưới 2/3 mép;
  - vàng tới mép ("near edge");
  - đỏ khi quá mép ("dumb zone: clear, hand off or compact").
- Mép mặc định 150k, đổi bằng `TSTACK_SMART_ZONE`.
- Footer của pi-open-tui đã hiện % theo cửa sổ 1M, nên con số 15% chẳng nói lên gì. Nhãn theo smart zone mới thật sự có ích trên Pi.

### 4.4 Lệnh `/context-budget`

`registerCommand("context-budget")`. Ở `before_agent_start` gần nhất, extension lưu `systemPromptOptions` (sections, contextFiles, skills, selectedTools). Lệnh ước lượng token cho từng phần: prompt gốc, `AGENTS.md`, danh sách skill, định nghĩa tool của từng extension. Đây là thay thế cho `claude -p "/context"`, và `context-audit` sẽ dựa trên nó **(`pi.getAllTools()` có trong types.d.ts; cần kiểm nó trả đủ description và schema để ước lượng)**.

### 4.5 `setup` trên Pi

- **Tracker, domain docs, `AGENTS.md`, `CODING_STANDARDS.md`, `.gitignore` `.tstack/`:** giữ nguyên, vốn trung lập.
- **`permissions.allow` cho lệnh kiểm của repo:** bỏ. Auto mode không nhận luật allow từ project. Lệnh chỉ đọc hoặc test thường đi fast path hoặc được classifier cho qua.
- **Hook format sau khi sửa file:** hai phương án.
  1. **(đề xuất)** Dùng git pre-commit, lint-staged hoặc `.pre-commit-config.yaml`. Đây là nấc 2 của thang, không phụ thuộc harness, và `setup` đã biết cài.
  2. Bật format của pi-lens ở cấu hình project. Hiện pi-config tắt global: `lens.json` có `format.enabled: false` **(cần kiểm tên file cấu hình project của pi-lens)**.

  Không sinh `.pi/extensions/…` cho từng repo: extension của project cần trust, lại chạy code tuỳ ý.
- **Verify skill:** ghi vào `.agents/skills/verify-<app>/`.

### 4.6 `afk` trên Pi

- **Coordinator giữ nguyên thiết kế:** hợp đồng; mỗi unit một `ticket-worker` mới; `verifier` độc lập; ledger và decision log trong `.tstack/<slug>/`.
- **Chạy tiếp không cần người:** trên Claude Code, afk dựa vào việc model tự làm tiếp trong một lượt dài. Trên Pi có `pi-goal-x`. Đề xuất: sau khi người dùng "go", `afk` gọi `create_goal` với objective là predicate Done của hợp đồng. Lợi ích:
  - auto-continue giữ coordinator chạy qua các lượt;
  - auditor GPT-6 Astra kiểm độc lập khi coordinator báo xong. Đó đúng là lớp "người viết không tự chấm" ở cấp run.

  Giới hạn: mặc định 10 lượt tự tiếp tục mỗi lần create/resume. Run qua đêm phải nâng `maxAutonomousRuns` trong `.pi/pi-goal-x-settings.json` của project; file này nằm trong luật `ask`, nên người dùng duyệt đúng một lần lúc ký hợp đồng. Việc gọi `afk` đã là "người dùng yêu cầu goal" theo AGENTS.md của pi-config **(cần kiểm hành vi thật của goal khi coordinator chờ `get_subagent_result`)**.
- **Unit song song:** cần `isolation: worktree`, mà pi-config đang tắt `worktreeIsolation`. Hai phương án:
  1. **(đề xuất)** `afk` mặc định chạy tuần tự. Hợp đồng có mục "parallel: yes" chỉ khi project bật `worktreeIsolation` trong `.pi/subagents.json`.
  2. Bật global trong pi-config.

  Lưu ý của pi-subagents: agent trong worktree không thấy thay đổi chưa commit, nên phải commit run branch trước khi spawn.
- **Chờ CI:** `bg_run "gh pr checks <n> --watch" triggerOnCompletion:true`.

### 4.7 Kiểm thử trong tstack

- Viết lại `tests/check_refs.py`:
  - đổi regex sang `/skill:<name>` và "the `<name>` skill";
  - kiểm tên agent tồn tại trong `agents/`;
  - kiểm đường dẫn tương đối trong skill;
  - cấm các token Claude Code còn sót (`${CLAUDE_`, `.claude/`, `Skill tool`, `AskUserQuestion`, `TodoWrite`, `claude -p`, `tstack:`);
  - kiểm frontmatter theo luật tên của Pi (`^[a-z0-9]+(-[a-z0-9]+)*$`, tối đa 64 ký tự, description tối đa 1024).
- `node --test` cho `git-guard.ts` (165 ca) và cho extension, dùng fake `ExtensionAPI`.
- CI của tstack: Node 24, chạy `check_refs` và `node --test`, chưa cần ba hệ điều hành. Kiểm thật với Pi nằm ở CI của pi-config.

## 5. Tích hợp vào pi-config

### 5.1 Ghim nguồn và thay mattpocock

- `sources.lock.json`:
  - thay mục `mattpocock-skills` bằng `{name:"tstack", repo:"duy-tung/tstack", commit, url: codeload tar.gz, sha256}`;
  - repo đang public, nên `installSource` tải không cần đăng nhập;
  - số nguồn vẫn là 3, nên `install-smoke.mjs:158` và `config.test.mjs:47` không đổi nếu thay 1-đổi-1.
- Vì sao thay hẳn chứ không lọc bằng `!`:
  - 13 tên trùng: codebase-design, domain-modeling, grill-with-docs, implement, prototype, research, resolving-merge-conflicts, tdd, to-spec, to-tickets, triage, wayfinder, wizard;
  - 5 skill còn lại của mattpocock đều có bản kế thừa trong tstack: ask-matt → `work ?`, code-review → `interrogate`, diagnosing-bugs → `diagnose`, improve-codebase-architecture → `improve-architecture`, setup-matt-pocock-skills → `setup`;
  - giữ cả hai bộ thì mỗi phiên có thêm khoảng 10 mô tả model-invoked gần trùng.
- Khi gỡ nguồn cũ: `reconcileResources` không quét `<root>/sources/`, nên thư mục `mattpocock-skills` và khoá `state.sources` cũ vẫn còn. `doctor.mjs:92` chỉ kiểm khoá có tồn tại trên đĩa nên không lỗi, nhưng để rác. Cần thêm bước dọn: nguồn không còn trong lock thì chuyển vào `backups/`.

### 5.2 Nạp tstack: package hay đường dẫn

- **Đề xuất: package cục bộ.** Thêm `"<root>/sources/tstack"` vào `settings.packages`, và tstack có `package.json`:
  ```json
  { "name": "tstack", "keywords": ["pi-package"],
    "pi": { "skills": ["./skills"], "extensions": ["./extensions/tstack/index.ts"] } }
  ```
  Một mục settings nạp đủ skill và extension. Pi coi package cục bộ là "loaded from the resolved path without copying". `resources.mjs` đã tính `packages` là tham chiếu nên không lưu trữ nhầm. Ngoài pi-config, người khác cài được bằng `pi install git:github.com/duy-tung/tstack@<commit>`.
- **Phương án thay thế:** thêm `<root>/sources/tstack/skills` vào `settings.skills` và extension vào `settings.extensions`. Cách này đúng với mẫu hiện tại của pi-config, nhưng phải sửa `config.test.mjs:48-49` (danh sách extension đúng 5 mục).
- Tên extension trong `extensions:` của role: pi-subagents so theo tên package (`tstack`) **(cần kiểm với package cục bộ)**.

### 5.3 Năm agent của tstack trong model-roles

`runtime/model-roles.mjs` hiện cứng hai danh sách: `SUBAGENT_ROLES = [researcher, worker, debugger, reviewer]` và `ROLES`. Preset phải khai đủ mọi role, và doctor, `nativeKind`, test đều giả định bốn file agent. Có hai phương án:

1. **(đề xuất)** Mở rộng `SUBAGENT_ROLES` thành 9 role, cả hai preset đều khai. Body lấy từ `<root>/sources/tstack/agents/*.md`, còn frontmatter vận hành (`tools`, `extensions`, `prompt_mode`…) do pi-config quyết. tstack giữ quyền trên nội dung prompt, pi-config giữ quyền trên model và quyền truy cập.

   | Role | Preset `default` | Preset `claude` | Lý do |
   |---|---|---|---|
   | `standards-reviewer`, `spec-reviewer` | GPT-6 Astra/high | Opus/high | Cùng hạng với `reviewer` |
   | `adversary` | GPT-6 Astra/high | Opus/high | Khác họ với parent (Opus). Đúng tinh thần "review đối kháng". |
   | `verifier` | GPT-6 Sol/high | Opus/high | Cần chạy app và thu bằng chứng |
   | `ticket-worker` | GPT-6 Sol/max | Opus/high | Như `worker` |

   Hệ quả với DECISIONS §6 ("gửi code sang hãng khác là opt-in"): preset `default` của pi-config **đã** giao review, advisor và auditor cho OpenAI. Tức là người dùng đã chọn điều đó ở cấp cấu hình. Trên pi-config, §6 viết lại thành "seat ngoài là role của preset; muốn chỉ một hãng thì `pi-models preset claude`". Còn `codex exec`/`gemini -p` bỏ hẳn.
2. Cài 5 agent như tập riêng, model ghim cứng. Ít đụng mã, nhưng `/models` và `pi-models` không quản được, trái với nguyên tắc "model/thinking của mọi vai đặt trong model-roles.json".

Phải sửa theo:
- `config.test.mjs:82` và `agent-integration.mjs:177` (số agent);
- `doctor.mjs:62-75`;
- `docs/models.md`, `docs/subagents.md`;
- `assets/AGENTS.md`: thêm placeholder cho role mới và dòng "khi nào dùng agent nào".

### 5.4 Working agreements và AGENTS.md toàn cục

- `assets/AGENTS.md` của pi-config được quản lý bằng checksum, không gộp. Khi người dùng đã sửa, file được giữ và không cập nhật nữa.
- Đề xuất: `buildConfiguration` ghép thêm khối working agreements từ `<root>/sources/tstack/templates/user/AGENTS.md` (đổi tên từ `CLAUDE.md`). Như vậy tstack vẫn là nguồn sự thật, không phải chép tay giữa hai repo. Nguồn đã được tải xong trước bước sinh cấu hình (install.mjs: bước 5 trước bước 8).
- Sửa dòng 14 của `assets/AGENTS.md` ("Skills mattpocock đã cài…") thành con trỏ tới `/skill:work ?`.
- Xung đột nội dung phải xử lý khi ghép:
  - "Keep the main thread lean: send exploration … to subagents" khớp với vai `researcher`;
  - "Dùng todo… khi có goal thì dùng goal" khớp với §4.6.
  - Không thấy mâu thuẫn trực tiếp.

### 5.5 Việc còn lại trong pi-config

- `THIRD_PARTY_NOTICES.md`: thay mục mattpocock bằng tstack. tstack là MIT, và `CREDITS.md` của tstack đã ghi nguồn Matt và pstack.
- README (bảng phiên bản, mục skills) và `docs/`: thêm `docs/tstack.md` (luồng hằng ngày trên Pi, `/skill:work`, bảng lệnh).
- `assets/extensions/pi-auto-mode`: `readRoots` đã coi thư mục skill trong settings là vùng đọc tự do. Nếu nạp qua `packages` thì phải kiểm `readRoots` có gồm thư mục package không. Nếu không, `read` một SKILL.md sẽ đi qua classifier **(cần kiểm)**.
- Luật deny dự phòng cho auditor (§4.1).
- Test mới:
  - `/skill:work ?` mở rộng đúng;
  - danh sách skill có 20 model-invoked của tstack và không có mattpocock;
  - 9 agent có model/thinking;
  - guard chặn `git push --force` ở parent và subagent (provider giả).

## 6. Vì sao không giữ song song Claude Code và Pi

- Phần chữ (khoảng 280 chỗ) phải phân nhánh theo harness: tên lệnh, cách nạp skill, loại agent, tool hỏi người dùng, transcript. Hai lựa chọn khi giữ song song:
  - viết trung tính kiểu "load the X skill", khiến Claude Code không còn gọi đúng `tstack:X`;
  - sinh hai cây từ một nguồn bằng template, khiến mỗi lần sửa skill phải chạy build và kiểm hai harness.
- Hook và status line vẫn phải viết hai lần (Python cho Claude Code, TypeScript cho Pi).
- pi-config đã là nơi cài đặt duy nhất người dùng dùng hằng ngày. Theo DECISIONS, test 1 ("chạy được trên harness hôm nay") chỉ đúng cho một harness được kiểm thật.

Nếu sau này cần lại Claude Code: dùng tag `v1.0.0`, hoặc viết build ngược từ nguồn Pi (dễ hơn chiều xuôi, vì Pi dùng chuẩn Agent Skills).

## 7. Lộ trình đề xuất

| Pha | Repo | Việc | Xong khi |
|---|---|---|---|
| 0 | cả hai | Chốt các quyết định ở §8. Tag `tstack v1.0.0`. | Có câu trả lời |
| 1 | tstack | Codemod §3.1 và sửa tay 18 skill C. Chuyển 5 agent. Viết lại `check_refs`. Bỏ phần Claude Code (§3.4). README và DECISIONS bản Pi. | `check_refs` xanh, không còn token Claude Code |
| 2 | tstack | Extension `tstack`: guard (port và 165 ca), nhắc compaction, smart zone, `/context-budget`. `package.json` với khoá `pi`. | `node --test` xanh; `pi -e ./` nạp được trong một repo mẫu |
| 3 | pi-config | Nguồn tstack thay mattpocock, `packages`, 9 role, ghép AGENTS.md, dọn nguồn cũ, deny dự phòng, docs, test. | `npm run check`, `npm test`, `npm run smoke` xanh trên CI 3 hệ điều hành |
| 4 | thật | Một phiên thật: `/skill:setup`, `/skill:create-verify`, một ticket qua `/skill:implement` (có interrogate và verifier), một afk nhỏ có goal. Đo lại context luôn-bật. | Báo cáo VERIFIED kèm bằng chứng; số token đo được |

Ước lượng thô: pha 1 lớn nhất (khoảng 280 chỗ thay và 18 skill đọc lại). Pha 2 chủ yếu là chuyển guard. Pha 3 tốn công ở test và model-roles.

## 8. Quyết định cần chủ repo chốt

1. **Bỏ hỗ trợ Claude Code, tag `v1.0.0`?** Đề xuất: có (§6).
2. **Thay hẳn mattpocock skills trong pi-config?** Đề xuất: có (§5.1).
3. **Tên lệnh:** giữ `/skill:work` (có sẵn, không cần mã), hay thêm alias `/work`, `/ship`… bằng `registerCommand` trong extension? Đề xuất: pha đầu dùng `/skill:`, xem lại sau khi dùng thật.
4. **5 agent vào model-roles** theo bảng §5.3?
5. **afk dùng `/goal` làm động cơ chạy tiếp và auditor** (§4.6)?
6. **`worktreeIsolation`:** giữ tắt global, bật theo project khi afk cần song song?
7. **Git guard:** extension riêng cộng luật deny dự phòng (đề xuất), hay nhúng vào pi-auto-mode?

## 9. Việc phải kiểm thật trước khi làm (tổng hợp)

- Thứ tự nạp extension giữa `settings.packages` và `settings.extensions`: guard phải chạy trước pi-auto-mode.
- pi-subagents có nhận tên `tstack` cho extension của package cục bộ trong `extensions:` của role không.
- `readRoots` của pi-auto-mode có gồm thư mục skill nạp qua package không.
- `.agents/skills/` của project được Pi nạp khi nào (có cần trust không), và pi-subagents có thấy không.
- Goal auto-continue khi coordinator chờ `get_subagent_result`; cách nâng `maxAutonomousRuns` cho một run.
- Extension đọc được định nghĩa tool để đo context (`/context-budget`).
- Tên file cấu hình project của pi-lens để bật format.
- `pi -p` qua launcher của pi-config cho eval headless.
