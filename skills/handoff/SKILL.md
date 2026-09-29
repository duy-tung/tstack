---
name: handoff
description: "Compact the conversation into a handoff document for another agent, with an optional background launch."
argument-hint: "What will the next session be used for? Add --bg to launch it now."
disable-model-invocation: true
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save it to the temporary directory of the user's OS (`$TMPDIR`, falling back to `/tmp`; `%TEMP%` on Windows), not the current workspace, as `handoff-<slug>-<timestamp>.md`. Tell the user the absolute path.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for (`tstack:<name>`), and which slash commands the user should type.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead. Only reference files that will outlive the temp directory.

Mark every claim you did not check this session as **unverified** ("unverified: the export job is not built yet"). The next agent treats the document as a contract and will not re-check it, so a belief written as a fact becomes a false premise.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

## Launch line

End by printing the line that starts the next session in the background:

```
claude --bg --name "<descriptive name>" "Read <handoff path> and continue"
```

Run it yourself only when the user passed `--bg` or asked you to start the next session. Always pass `--name` with a descriptive name (`--name "Fix login bug"`); the user manages the session with `claude agents`. Pass the file path, never the summary: backticks and `$(...)` in an inline prompt are expanded or mangled by the shell, and the usual failure is silent truncation.

If the next session will not start soon, or runs in another harness, tell the user to copy the file somewhere durable: some environments clear temp between sessions.
