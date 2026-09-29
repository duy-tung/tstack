---
name: research
description: "Investigate a question against primary sources in a background agent and save cited findings as one Markdown file. Use to gather docs or API facts, or to delegate reading legwork."
---

Spin up a **background agent** to do the research (a `general-purpose` agent run in the background), so you keep working while it reads. One agent per question; several questions go out in one message. The research agent must not spawn further agents: if you are already a subagent, do the research yourself in this context.

Scope each question first: one API, one behaviour, one version claim. Split a broad topic into narrow questions.

Brief each agent with its question, where to save, and this job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it. For library and API docs, prefer a documentation MCP server such as Context7 when one is available; when docs and the installed version's source disagree, the source wins.
2. Stop when each question has a primary-source citation or is marked unanswerable, with where you looked.
3. Write the findings to a single Markdown file, citing each claim's source. Head it with the date and the versions the findings apply to.
4. Save it where the caller said. Otherwise save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.
5. Report the file path and a three-line gist.
6. Do not invoke tstack skills or spawn agents. Do the work directly.
