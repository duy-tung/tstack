# Context audit checklist

## Reading the numbers

- The total counts only categories without `(deferred)`. Deferred tools load on demand through tool search, so turning them off saves little per session.
- The headless probe loads the user's settings, plugins and MCP config but skips interactive-only tools (plan mode, AskUserQuestion) and servers that need a login. Price those from the user's `/context`, or write "not measured".
- Price a plugin with `claude plugin details <name>` (its "Always-on" line), then check it against the snapshot's Skills table. That projection counts user-invoked skills (`disable-model-invocation: true`), which measure at zero, and skips MCP servers: price a server by summing its rows in the MCP Tools table.
- Keys interact. In one measured setup, `disableBundledSkills: true` alone raised system tools by about 8k while the Artifact tool was on. Price each candidate, then the chosen set together.

## Settings

| Change | Removes | You lose |
|---|---|---|
| `"disableClaudeAiConnectors": true` | claude.ai connectors, auto-loaded as MCP servers | connectors added on claude.ai (mail, drive, chat) inside Claude Code |
| `"disableWorkflows": true` | the Workflows feature | workflow scripts |
| `"disableBundledSkills": true` | skills and workflows that ship with Claude Code | those skills; built-in slash commands stay typable but hidden from the model |
| `"enableArtifact": false` | the Artifact tool | publishing pages from Claude Code |
| `"autoMemoryEnabled": false` | the memory-system instructions and the `MEMORY.md` index | notes Claude writes for itself across sessions |
| `claude plugin disable <name>` | the plugin's skills, agents, hooks and MCP servers | that plugin |
| `claude mcp remove <name>` | the server's tool definitions | that server |
| a `permissions.deny` entry | the tool's definition | that tool (see Tools) |

Recommend auto memory off: it is sediment that writes itself. Before turning it off, route each memory worth keeping into a file the user owns (step 3 verdicts).

## Tools

Deny with `"permissions": {"deny": ["<Tool>"]}`, appended to any existing list. A denied tool's definition leaves the prompt.

| Tool | You lose | Keep it when |
|---|---|---|
| `NotebookEdit` | editing Jupyter notebook cells | you work in `.ipynb` files |
| `DesignSync` | reading and updating claude.ai design systems | you sync design systems |
| `CronCreate`, `CronDelete`, `CronList` | scheduled prompts inside a session | you run `/loop` at an interval |
| `ScheduleWakeup` | self-paced wakeups | you run `/loop` without an interval |
| `EnterPlanMode`, `ExitPlanMode` | plan mode's propose-and-approve step | you use plan mode |
| `PushNotification` | notifications when a long run needs you | you leave runs unattended |
| `RemoteTrigger` | managing scheduled remote agents (routines) | you schedule remote runs |
| `ReportFindings` | review findings rendered in a host UI | a host renders your reviews |
| `AskUserQuestion` | clickable multiple-choice questions | you prefer clicking; grilling works in plain text too |

## Line tests

Tests 1 to 3 decide whether a line lives at all; test 4 decides where it lives.

1. **Single source of truth.** A fact lives in one place, and executable sources win. A line that restates the environment (manifest scripts, config files, directory layout, `--help` output) fails. When two steering files say the same thing, keep the copy in the narrowest file that still loads in every session that needs it.
2. **Sediment.** Once true, not now. Check every path, command, name and claim against the repo today (`ls`, `grep`, `--help`). A stale line fails; fix it instead only when the rule behind it still holds.
3. **No-op.** The line must change behavior versus the default. "Write clean code", "be thorough" and "follow best practices" fail. So does a leading word too weak to beat the default.
4. **Push or point.** Point by default. A line stays inline only when it changes behavior in every session, or its trigger is unpredictable (a "When something breaks" symptom and cause table).

## Verdicts

Take the first row that matches.

| The line is | Verdict |
|---|---|
| failing test 1, 2 or 3 | delete |
| a mechanical rule a tool could check (banned import or call, file location, naming) | encode as lint/hook |
| a judgment call a reviewer applies to a diff | move to CODING_STANDARDS.md |
| a procedure with a predictable trigger ("when releasing", "when adding a migration") | move to skill |
| reference that only some sessions need | move behind pointer |
| a navigation pointer to a hard-to-find, critical file that exists today | keep |
| any other navigation pointer | delete |
| passing test 4 | keep |

Stale pointers are worse than none: a pointer whose target is gone gets deleted, not kept "for later".

## Also flag

- `CLAUDE.md` beside `AGENTS.md` with no `@AGENTS.md` import: Claude Code loads only `CLAUDE.md`, so `AGENTS.md` is dead for Claude and drifts. Propose one canonical file: `AGENTS.md`, with `CLAUDE.md` reduced to `@AGENTS.md` when a `CLAUDE.md` must exist.
- An `@` import pulls the whole file into every session. Keep it only when all of that file passes the tests.
- A `.claude/rules/*.md` file without `paths:` frontmatter loads in every session. A rule for one area gets `paths:` so it loads only there.
- A parent-directory `CLAUDE.md` that does not apply to this repo: exclude it with `claudeMdExcludes`.
