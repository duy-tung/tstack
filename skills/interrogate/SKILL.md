---
name: interrogate
description: "Review a diff with parallel fresh reviewers per axis (standards, spec, adversarial), then judge findings into Act on, Consider, Noted, Dismissed. Use for any review or stress test of changes."
argument-hint: "[fixed point] [fix] [external]"
effort: high
---

# Interrogate

Review the changes since a fixed point along separate axes, each in its own fresh-context reviewer, then judge the findings as the lead. The axes stay separate so one cannot mask another: code can follow every standard and build the wrong thing, or build the right thing against every standard.

| Axis | Reviewer | Question | Runs |
|---|---|---|---|
| Standards | `tstack:standards-reviewer` | Does it follow the repo's documented standards and the baseline in SMELLS.md? | Always |
| Spec | `tstack:spec-reviewer` | Does it do what the spec asked, no more and no less? | When a spec exists |
| Adversarial | `tstack:adversary`, plus an external seat when opted in | Where does it break? | Risky diffs, or when asked |

**Mode.** Fix mode when the caller is tstack:implement or tstack:afk, or the arguments include `fix`: fix the Act-on items (step 7). Report mode otherwise: report only and apply nothing.

Run from the main thread. Reviewers are subagents, and a subagent cannot spawn them. If you have no Agent tool, stop and tell your caller that interrogate must run from the main thread.

## 1. Pin the fixed point

The fixed point is what the user or caller named: a SHA, branch, tag, `main`, `HEAD~5`. With none named on a feature branch, use the default branch (`git symbolic-ref --short refs/remotes/origin/HEAD`, else `main`) and say so. With none named on the default branch, ask.

Check before anything else:

1. `git rev-parse --verify <fixed-point>` resolves.
2. `git status --porcelain` for uncommitted changes. In fix mode, commit them first. In report mode, review the working tree too: the diff command becomes `git diff $(git merge-base <fixed-point> HEAD)`, and untracked files come from `git ls-files --others --exclude-standard`.
3. Otherwise the diff command is `git diff <fixed-point>...HEAD` (three dots: against the merge-base).
4. The diff is non-empty.

A bad ref or an empty diff fails here, not inside parallel reviewers. Note the commit list: `git log <fixed-point>..HEAD --oneline`.

## 2. State the intent

Write one paragraph of intent from the user's message, the commits, the PR body, the ticket and the code. If unsure in report mode, ask. Reviewers judge the execution against the intent; they do not question it.

## 3. Find the spec

In order:

1. Issue references in the commit messages (`#123`, `Closes #45`), fetched with the workflow in the issue tracker doc (the `## Agent skills` block in AGENTS.md or CLAUDE.md points to it, usually `docs/agents/issue-tracker.md`; without it, try `gh issue view`).
2. A path the user or caller gave.
3. A spec under `docs/`, `specs/` or `.scratch/` matching the branch or feature.
4. Ask the user (report mode only).

Save a fetched spec to a temp file and pass its path. With no spec, skip the spec axis and report "no spec available".

## 4. Find the standards

`CODING_STANDARDS.md` at the repo root, `CONTRIBUTING.md`, and any style doc the repo's AGENTS.md or CLAUDE.md points to. The baseline in [SMELLS.md](SMELLS.md) applies on top; a documented repo standard overrides it.

## 5. Pick the axes

Standards always. Spec when step 3 found one. Adversarial when the user asked for adversarial review, or the diff is risky: it touches auth, permissions, secrets or payments; data migrations, storage or wire formats; concurrency, retries or caching; a public API or config surface; it changes more than about 400 lines; or it fixes a bug without a regression test.

**External seat (opt-in).** A second model family catches what the first one misses, but it sends the diff to another vendor. Add it only when the arguments include `external`, or the repo's AGENTS.md or CODING_STANDARDS.md says external reviewers are allowed. With the adversarial axis on and the seat allowed, run `command -v codex gemini`. If either is installed, add one read-only external review with the adversary's brief:

1. Write a brief file `$BRIEF` under `/tmp/tstack-interrogate/`, with its output file `$OUT` beside it. The brief holds: the step 6 brief, then the contents of `${CLAUDE_SKILL_DIR}/RUBRIC.md`, then the output of the diff command (the external CLI may not be able to run git).
2. Run it with the Bash tool in the background, in the same message that spawns the reviewers: `codex exec --sandbox read-only - < "$BRIEF" > "$OUT" 2>&1`, or `gemini -p "Follow the review brief on stdin. Modify nothing." < "$BRIEF" > "$OUT" 2>&1`. Never add a flag that lifts the sandbox or auto-approves edits.
3. Read `$OUT` when the reviewers return. Wait up to about 10 minutes in all, then report the seat as timed out.

With no external seat, say in the report that every reviewer shares one model family, so their blind spots are correlated.

## 6. Spawn the reviewers

Spawn every selected reviewer in one message, in parallel. Brief each with pointers, not pasted content:

```
Goal: <axis> review of <fixed-point>...HEAD.
Intent: <paragraph from step 2>
Diff: `<diff command>`. Commits: `git log <fixed-point>..HEAD --oneline`. Untracked files: <paths or none>.
Read first: <standards axis: the standards files and ${CLAUDE_SKILL_DIR}/SMELLS.md | spec axis: the spec path | adversarial axis: ${CLAUDE_SKILL_DIR}/RUBRIC.md>
Forbidden: editing files, or running anything that writes to the repo.
Do not invoke tstack skills or spawn agents. Review directly. Under 400 words.
Report: in the format your agent definition gives.
```

## 7. Judge each axis

Read [LEAD-JUDGMENT.md](LEAD-JUDGMENT.md) before bucketing. You are the lead: a pragmatic senior engineer, not a neutral aggregator. Within each axis, put every finding in exactly one bucket, with its `file:line`, the reviewer that raised it, and a one-line rationale:

- **Act on.** A correctness, security or maintainability problem that would block a real PR.
- **Consider.** Legitimate, but the fix may not be worth its cost now.
- **Noted.** Valid, not actionable now.
- **Dismissed.** Wrong, a nitpick, or missing context. Say why.

Never merge or rerank findings across axes. Within the adversarial axis, dedupe the adversary and the external seat with attribution; a finding both model families raised carries the most weight. A finding raised on two axes stays on both, marked "also on <axis>".

**Fix mode.** Fix every Act-on item, rerun the affected tests, and commit. Under tstack:afk the coordinator does not edit: it gives the Act-on list to a fresh `tstack:ticket-worker` as a full brief (GOAL: the Act-on list; SCOPE: the files it names). Then re-run only the axes that had Act-on items, once. Whatever that re-run still flags is reported open. Do not loop until clean.

## 8. Report

```
## Interrogate: <fixed-point>...HEAD (<N> commits, plus working tree if reviewed)
Intent: <paragraph>
Reviewers: <axes run>; <external seat, or "one model family: blind spots are correlated">

### Standards
**Act on**
- `file:line` <finding> (<reviewer>). <one-line rationale>
**Consider** / **Noted** / **Dismissed**: the same shape
### Spec
<the same buckets, or "no spec available">
### Adversarial
<the same buckets, or "not run: <reason>">

Summary: findings per axis, and the worst issue within each axis.
```

Name no single winner across axes: that is the reranking the separation exists to prevent. In fix mode, add what was fixed (commit SHAs) and what stayed open.
