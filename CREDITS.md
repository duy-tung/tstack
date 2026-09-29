# Nguồn gốc

tstack là bản phái sinh, viết lại cho Claude Code, từ hai dự án mã nguồn mở theo giấy phép MIT. Toàn văn thông báo bản quyền gốc nằm trong [LICENSE](LICENSE).

| Dự án | Tác giả | Phiên bản dùng làm nguồn | Giấy phép |
|---|---|---|---|
| [`skills`](https://github.com/mattpocock/skills) (Claude Code plugin) | Matt Pocock | 1.2.3 | MIT, Copyright (c) 2026 Matt Pocock |
| [`pstack`](https://github.com/cursor/plugins/tree/main/pstack) (Cursor plugin) | Lauren Tan | 0.15.5 | MIT, Copyright (c) 2026 Lauren Tan |

Tư liệu tham khảo thêm (không sao chép nội dung): bài nói "How I Shipped 2000 PRs" của Lauren Tan, khoá AI Hero của Matt Pocock (các phần Concepts, Fundamentals, Steering, Shipping), và repo `dictionary-of-ai-coding` dùng quy ước của Matt.

## Từng phần lấy từ đâu

"Gộp" nghĩa là ý tưởng của cả hai nguồn được hợp lại và viết lại. "Chuyển" nghĩa là bám sát một nguồn, đổi cho Claude Code (Agent tool thay Task tool, `.claude/` thay `.cursor/`, `gh` thay Graphite, `AskUserQuestion` thay `AskQuestion`, transcript ở `~/.claude/projects/`).

### Lệnh

| tstack | Nguồn | Cách làm |
|---|---|---|
| `work` + `playbooks/` + `PHASE-BOUNDARIES.md` | Matt `ask-matt`, bài Steering (năm lựa chọn ở ranh giới pha); pstack `poteto-mode` và các playbook | Gộp |
| `grill-me`, `grill-with-docs` | Matt | Chuyển |
| `to-spec` | Matt `to-spec`; mục Verification từ pstack | Gộp |
| `to-tickets` | Matt `to-tickets`; pstack `sequence-verifiable-units` | Gộp |
| `implement` + `playbooks/build.md` | Matt `implement`, `implement-spec`; pstack feature playbook, `architect` | Gộp |
| `afk` | pstack `figure-it-out`, `autonomous-run`, `orchestrate`; Matt (AFK, Shipping) | Gộp |
| `ship` + `BOT-TRIAGE.md` | pstack `opening-a-pr`, `babysit`, `shipping`; checklist deslop từ cursor-team-kit; Matt (PR) | Gộp |
| `reflect` | pstack `reflect` (thang cơ chế); Matt `retro` | Gộp |
| `setup` | Matt `setup-matt-pocock-skills`, `setup-pre-commit`, git guardrails; pstack (đề nghị setup) | Gộp |
| `create-verify`, `maintain-verify` | pstack `create-verification-skill`, `maintain-verification-skill`, `control-ui`, `control-cli` | Chuyển |
| `context-audit` | Matt (killing bloat, pruning) | Chuyển, thêm script đo |
| `improve-architecture`, `wayfinder`, `triage`, `handoff` | Matt | Chuyển |
| `wait-what` | Matt `wait-what`; pstack `bro` | Gộp |

### Kỷ luật

| tstack | Nguồn | Cách làm |
|---|---|---|
| `grilling` | Matt; nguyên tắc "observe, don't ask" của pstack | Gộp |
| `domain-modeling`, `research`, `resolving-merge-conflicts`, `wizard` | Matt | Chuyển |
| `codebase-design` | Matt `codebase-design`; pstack `architect` (ARCHITECT.md) | Gộp |
| `principles` | 23 nguyên tắc `principle-*` của pstack rút còn 14; Matt Fundamentals | Gộp |
| `tdd` | Matt `tdd`; pstack `tdd`, nguyên tắc test behavior | Gộp |
| `diagnose` | Matt `diagnosing-bugs`; pstack bug-fix, perf, forensics, fix-root-causes | Gộp |
| `prove` + `BLAST-RADIUS.md` | pstack `prove-it-works`, `blast-radius`; chuẩn tái hiện của gói benny | Gộp |
| `interrogate` + agents `standards-reviewer`, `spec-reviewer`, `adversary` | Matt `code-review` (hai trục); pstack `interrogate` (lead judgment, trục đối kháng) | Gộp |
| `how`, `why`, `decision-log` (`show-me-your-work`), `unslop` | pstack | Chuyển |
| `prototype` | Matt `prototype`; pstack prototype playbook | Gộp |
| `writing-for-agents` | Matt `writing-for-agents`; pstack `authoring-a-skill`, eval | Gộp |
| `typescript` | pstack `typescript-best-practices`; Matt `setup-ts-deep-modules` | Gộp |
| `python`, `mobile` | Cùng nguyên tắc, viết mới cho Python và Swift, Kotlin, Dart | Mới |

### Agent, hook, script

| tstack | Nguồn | Cách làm |
|---|---|---|
| `verifier` | pstack (người viết không tự chấm) | Chuyển |
| `ticket-worker` | pstack `orchestrate` (brief bảy trường) | Chuyển |
| `hooks/guard_git.py` | Ý tưởng git guardrails của Matt; viết mới với bộ phân tích lệnh kiểu shell, 165 ca kiểm thử | Mới |
| `hooks/precompact_notice.py`, `bin/statusline.py`, `bin/merge_settings.py`, `bin/claude_md.py`, `install.sh`, `tests/` | Viết mới cho tstack | Mới |

Mọi lỗi phát sinh trong phần viết lại là của tstack, không phải của các tác giả gốc.
