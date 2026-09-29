---
name: context-audit
description: "Measure always-on context (settings, MCP, skills, CLAUDE.md, AGENTS.md, memory) and prune it with approval."
disable-model-invocation: true
---

# Context audit

Measure always-on context, propose cuts with their saving and what they cost the user, apply only what the user approves, then measure again. A line survives only when it changes behavior in every session, or its trigger is unpredictable.

Read [CHECKLIST.md](CHECKLIST.md) before step 2. It holds the settings and tool candidates, the line tests and the verdict routing.

## 1. Measure

- From the repo root, run `bash "${CLAUDE_SKILL_DIR}/scripts/context-probe.sh" save before`. It runs `claude -p "/context"` (a fresh session, so the numbers are the always-on baseline), prints tokens by category and saves the full breakdown: MCP tools per server, memory files, skills.
- If it fails, ask the user to run `/context` and paste the output, or read it if already pasted. Ask for it anyway when they rely on MCP servers that need an interactive login.
- Run `claude plugin list`, then `claude plugin details <name>` for each enabled plugin.
- Note the baseline total, each category and the five largest items.

## 2. Settings

Read `~/.claude/settings.json`, and the project's `.claude/settings.json` and `.claude/settings.local.json` when present. Build the candidates from CHECKLIST.md "Settings" and "Tools", skipping anything already off. Price each one:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/context-probe.sh" try '{"enableArtifact": false}'
```

A candidate that shows no change was not loaded in the probe: write "not measured". Price plugins and MCP servers as CHECKLIST.md "Reading the numbers" says. Price the chosen set together before applying it.

Show one table (Change, Saves, You lose) and ask which rows to apply, as one multi-select question when AskUserQuestion is available. Apply only the rows the user picked: copy the file to `settings.json.bak-<timestamp>` first, merge the keys (append to `permissions.deny`, never replace it), then validate with `python3 -m json.tool`.

## 3. Steering files

Read in full every file the Memory Files table lists, plus `~/.claude/CLAUDE.md`, the project's `CLAUDE.md` or `AGENTS.md`, `CLAUDE.local.md`, every `@` import and `.claude/rules/*.md`. When auto memory is on, also read `~/.claude/projects/<sanitized-cwd>/memory/`, starting at `MEMORY.md`.

Run every line through CHECKLIST.md "Line tests", route it with "Verdicts", and check "Also flag". Output one table:

| Where | Line or section | Verdict | Reason |
|---|---|---|---|

`Where` is `file:line`. Verdict is one of: keep, delete, move behind pointer, move to skill, move to CODING_STANDARDS.md, encode as lint/hook. Reason names the deciding test in a few words. Merge consecutive lines with the same verdict into one row. Ask which rows to apply; the rest stay as they are.

## 4. Apply and re-measure

Apply the approved rows only:

- **delete**: remove the line.
- **move behind pointer**: move the text into a doc beside the code it describes, and leave one line naming the doc and when to read it.
- **move to skill**: call the Skill tool with "tstack:writing-for-agents", write `.claude/skills/<name>/SKILL.md` with the trigger in its description, then remove the line.
- **move to CODING_STANDARDS.md**: append the rule, creating the file from [the template](../../templates/project/CODING_STANDARDS.md) when absent.
- **encode as lint/hook**: build it when it is a config change (a banned import, a restricted pattern, a hook). Otherwise list it as a follow-up and leave the line until the check exists.

Check that every pointer you left resolves. Re-measure and compare:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/context-probe.sh" save after
bash "${CLAUDE_SKILL_DIR}/scripts/context-probe.sh" diff before after
```

Report that table, then the rows applied, the rows declined and the follow-ups. Tell the user a new session carries the savings.
