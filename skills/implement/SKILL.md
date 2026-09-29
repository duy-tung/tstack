---
name: implement
description: "Build a ticket or a small spec: data shape first, TDD at agreed seams, proven on the real artifact, reviewed, committed, ticket closed."
disable-model-invocation: true
argument-hint: "<ticket number, URL or path | spec>"
---

# Implement

Build the work the user named by following the build playbook at `${CLAUDE_SKILL_DIR}/../work/playbooks/build.md`. Read it now and copy its steps into the task list before any task-specific todo. A step you skip stays in the list as `skip: <reason>`.

## Scope per run

- **One ticket:** build it.
- **Several tickets or a spec with tickets:** work the frontier (tickets whose blockers are all closed), one ticket per run. When it lands, stop and recommend the phase-boundary move for the next one: usually `/clear`, then `/tstack:implement <next ticket>`. The spec, tickets and commits hold the context.
- **A small spec with no tickets that fits one smart zone:** treat its user stories as the acceptance criteria and build it in one run.
- **A spec too big for one session:** stop and tell the user to run `/tstack:to-tickets` first.
- **The user will be away, or wants tickets built in parallel:** stop and tell the user to run `/tstack:afk`.

If the ticket source needs the issue tracker doc and it is missing, tell the user to run `/tstack:setup`.
