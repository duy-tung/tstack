# Evaluating a skill change

When in doubt, delete. Keep only prose that changes a decision. Tell the agent to do the thing and skip the reason, unless the rule is confusing without one. Point at structural sources (types, config, READMEs) instead of restating them, and reach other skills by calling them, not by copying their text.

## Validate every change

- The frontmatter parses, has `name` and `description`, and `name` equals the folder.
- Every referenced file exists and every relative link resolves.
- Every skill it calls exists and is reachable under the call rule ([SKILL-MECHANICS.md](SKILL-MECHANICS.md)).
- It runs once on a real task, and you read what the agent actually did.

Change a skill in its own commit or PR, never tangled into feature work: a skill edit hidden in a feature diff cannot be reviewed or evaluated. A skill that misbehaves mid-task gets noted and fixed after the task.

## Blind eval for structural changes

A structural change (new or reordered steps, a moved pointer, a rewritten description, a split or merge) changes how every future session behaves, so test it as an experiment. Skip the eval for wording no rubric could grade.

The failure mode it guards against is the observer effect: an agent that knows it is being evaluated behaves differently.

**Blinding rules:**

- None of these words appears in any directory, file, or prompt a candidate sees: `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, `arena`.
- The candidate prompt reads as an organic user request: the goal, not the meta.
- No chain-eliciting cues. Don't ask a candidate which skills, principles, or files it used; ask for design notes generally.
- Directory and slug names are project-shaped, the kind a user would pick.
- A candidate never learns that other candidates exist.
- The judge knows it is judging, but sees outputs only under sanitized labels: never a model name, never which variant produced them.

**Steps:**

1. **Frame.** Name the variant under test and the behaviour that counts as success. Write a rubric of 3 to 6 concrete, gradeable criteria. Only the judge sees it.
2. **Set up sanitized directories**, one per candidate, with the variant in place. When comparing a change against the current version, give half the candidates each. Plant what an organic task would have: a project skeleton, and the skill files where a session would find them.
3. **Write one organic prompt**: what a user would type, with nothing about what is being measured.
4. **Run the candidates.** In Claude Code, candidates are fresh `general-purpose` subagents spawned in one message, same prompt to each, each told to work only in its own directory, each brief ending with "Do not invoke tstack skills or spawn agents. Do the work directly." When the variant must load the way a real session loads it (a skill description, an `AGENTS.md`), run each candidate instead as a headless session started in its directory: `claude -p "<prompt>"`.
5. **Judge blind.** Spawn one separate fresh agent as the judge; it reads and scores, and never edits. It gets the rubric and the outputs by sanitized label. When comparing two variants, it scores both sets in one pass on one scale.
6. **Grade from files actually read, never from the candidate's claims.** Read each candidate's transcript (Claude Code keeps transcripts under `~/.claude/projects/<encoded-cwd>/`, subagent transcripts included) and list the files it opened. Grade chain-following from those reads and the shape of the output.
7. **Read every output yourself**, end to end, and compare with the judge. Disagreement means the rubric is ambiguous or one of you is biased: suspect the rubric first.

**Same-family limitation.** Every seat above is Claude, so candidates and judge share blind spots, and a unanimous result is weaker than it looks. Say so in the verdict. When an external seat is allowed (the user asked for an external seat in this task, or the repo's AGENTS.md or CODING_STANDARDS.md allows external reviewers) and `codex` or `gemini` is installed, give the judge seat to that CLI (`codex exec --sandbox read-only`) under the same blinding.

**Reply:** the variant under test, the rubric, per-candidate notes, the judge's verdict, your synthesis, and whether to promote the variant.
