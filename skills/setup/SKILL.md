---
name: setup
description: "Configure this repo for tstack: tracker, domain docs, AGENTS.md pointers, coding standards, stack hooks."
disable-model-invocation: true
---

# Setup

Write the per-repo files the tstack skills read. Explore first, ask one section at a time, show drafts, write only what the user approved.

In every step:

- Never overwrite an existing file without showing the diff and getting approval.
- Re-runs update in place: one `## Agent skills` block, one `.tstack/` ignore line, one hook entry, no duplicate allow rules. A file that already matches its draft is reported as unchanged.

## 1. Explore

Read what exists. Ask nothing yet.

- **Remote**: `git remote -v`. Run `gh auth status` for a GitHub remote, `glab auth status` for a GitLab one.
- **Instruction files**: `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`. Note whether `CLAUDE.md` imports `@AGENTS.md`, whether an `## Agent skills` block exists, and which paths it points to.
- **Prior setup**: `docs/agents/`, `CODING_STANDARDS.md`, `.claude/settings.json`, `.claude/hooks/`, `.claude/skills/verify-*/`.
- **Domain docs**: `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, `src/*/docs/adr/`. A `.scratch/` folder hints at a local tracker.
- **Stack**: `package.json` and its lockfile, `tsconfig.json`, `pyproject.toml`, `requirements*.txt`, `uv.lock`, `poetry.lock`, `Podfile`, `*.xcodeproj`, `Package.swift`, `build.gradle` or `build.gradle.kts`, `pubspec.yaml`.
- **Monorepo signals**: `pnpm-workspace.yaml`, `workspaces` in `package.json`, `turbo.json`, `nx.json`, several `packages/*` with their own `src/`.
- **Checks**: the typecheck, lint, test and format commands (manifest scripts, `Makefile`, `justfile`, the CI workflow), formatter and linter configs, and existing gates (`.husky/`, `.pre-commit-config.yaml`, `lefthook.yml`, `.githooks/`).
- **Runnable surface**: a dev server or start script, a CLI entry point, an app target, a deployable service.
- **Ignore state**: `git check-ignore -q .tstack/probe` succeeds when `.tstack/` is already ignored.

Show the findings as a short found/missing list.

## 2. Ask, one section at a time

Lead each question with the recommendation so the user can accept it in a word. Use AskUserQuestion when available: one question per call, recommended option first. Skip a section that exploration already settled.

- **A. Issue tracker.** Recommend from the remote with [ISSUE-TRACKERS.md](ISSUE-TRACKERS.md).
- **B. Triage labels.** Ask whether to use them. Recommend yes for a shared repo that receives issues from others, no for a solo repo or a local tracker. On yes, ask whether to keep the default names (recommended: yes).
- **C. Domain docs.** Use single-context (one `CONTEXT.md` and `docs/adr/` at the root) without asking. Only with monorepo signals, offer multi-context (a root `CONTEXT-MAP.md` pointing to per-context `CONTEXT.md` files).
- **D. Instruction file.** Decide by this table. Ask only in the first row.

| Found | The block goes in |
|---|---|
| Neither file | A new `AGENTS.md` (recommended) or a new `CLAUDE.md` |
| `AGENTS.md` only | `AGENTS.md` |
| `CLAUDE.md` only | `CLAUDE.md`. Never create `AGENTS.md` beside it. |
| Both, and `CLAUDE.md` imports `@AGENTS.md` | `AGENTS.md` |
| Both, no import | `CLAUDE.md`, the file Claude Code loads. Tell the user `AGENTS.md` is not loaded while `CLAUDE.md` exists, and that `/tstack:context-audit` can merge them. |

## 3. Draft, confirm, write

Draft every file below, show the drafts, let the user edit, then write.

- **`docs/agents/issue-tracker.md`**: the chosen template, or prose for another tracker, per ISSUE-TRACKERS.md.
- **`docs/agents/triage-labels.md`**: only when B is yes, from [triage-labels.md](../../templates/project/docs/agents/triage-labels.md). After writing it, create the labels per ISSUE-TRACKERS.md.
- **`docs/agents/domain.md`**: from [domain.md](../../templates/project/docs/agents/domain.md).
- **The `## Agent skills` block**, in the file D chose. Copy the format of the `## Agent skills` section in [AGENTS.md](../../templates/project/AGENTS.md) and fill each one-line summary. Keep `### Triage labels` only when B is yes, and `### Verification` only when `.claude/skills/verify-*/` exists (name each one). When a block already exists, rewrite only its tstack sub-blocks (Issue tracker, Triage labels, Domain docs, Verification, Coding standards), keep any other sub-block, and keep the paths it already uses: a block pointing at `internal/issue-tracker.md` keeps that path, and that file gets the update.
- **A new instruction file** (first row of D only): the whole [AGENTS.md](../../templates/project/AGENTS.md) template. Fill every `<placeholder>` from exploration or delete its section; a written file never contains a placeholder. Write the request-flow line from the entry points you read. Keep `## Navigation` only for hard-to-find, critical files. Seed `## When something breaks` from what exploration found (required services, env files, codegen steps) and ask the user for the symptom agents hit most; drop the section when there is none.
- **`CODING_STANDARDS.md`**: only when absent, from [CODING_STANDARDS.md](../../templates/project/CODING_STANDARDS.md), with the language examples cut to the repo's languages. Leave an existing one untouched.
- **`.gitignore`**: append `.tstack/` unless it is already ignored.

## 4. Stack hooks

Follow [STACK-HOOKS.md](STACK-HOOKS.md). Say its ladder line, then propose the four items in one message, each with what it adds and a recommendation, and ask which to add (one multi-select question when AskUserQuestion is available):

1. `permissions.allow` rules for the repo's own check commands, so the agent is not prompted for them. Recommended when the repo has check commands.
2. The format-on-edit hook. Recommended when the repo has a formatter or linter.
3. A pre-commit gate for the stack. Recommended when the repo has no pre-commit hook and no CI job running its checks.
4. Module-boundary enforcement. Opt-in.

Draft the approved items, show the diffs, write, then run each proof STACK-HOOKS.md gives. The hook script to copy is `${CLAUDE_SKILL_DIR}/scripts/format-edited-file.sh`.

## 5. Verification

When the repo has a runnable surface and no `.claude/skills/verify-*/`, tell the user to run `/tstack:create-verify` next. Do not call it.

## 6. Report

List every file as created, updated, unchanged or skipped (with the reason), the labels created, the settings entries added, and each proof with its result. Leave the changes uncommitted for the user to review. Tell the user they can edit `docs/agents/*.md` directly, and re-run `/tstack:setup` to switch trackers or after upgrading tstack. Name the next step: `/tstack:create-verify` when step 5 applies, and `/tstack:context-audit` when the instruction file runs past about 100 lines.
