# Pickup

**You own the resume point. Read the prior trail. Do not redo it.**

1. **Find the trail**, newest first: a handoff file the user names, `.tstack/*/resume.md`, `.tstack/*/report.md` and `decisions.tsv`, the branch and worktree (`git worktree list`), open PRs (`gh pr list --author @me`), and this project's transcripts under `~/.claude/projects/<encoded cwd>/` (never another project's). Parse a long transcript in a subagent and keep only a reduced timeline in the main thread.
2. **Reconstruct state**: the branch, what already landed (`git log`, the diff against the base), open todos, decisions made. The trail is authoritative for decisions. Resist re-deriving them.
3. **Diff done versus pending.** Name the resume point. Do not re-run completed work.
4. **Re-verify inherited outcomes** on the real artifact: call the Skill tool with "tstack:prove". A passing prior self-report is not proof.
5. **Route the rest** with the table in the work skill.

**Reply:** where the prior session stopped, what you inherited versus redid (ideally nothing redone), the resume point, the next action.
