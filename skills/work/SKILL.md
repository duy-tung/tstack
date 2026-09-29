---
name: work
description: "One entry point. Classify any task, pick the flow or playbook that fits, and run it with visible steps. `/tstack:work ?` answers which skill fits."
disable-model-invocation: true
argument-hint: "<task> | ?"
---

# Work

Route the task, then run the route with every step visible in the task list.

## 1. Route

Pick the first row that fits and say which one in a single line.

| The task | Route |
|---|---|
| `?`, "which skill", "what next", "where am I in the flow" | Answer from the flow map below: name the next command and why. Stop. |
| Resume or take over earlier work | [playbooks/pickup.md](playbooks/pickup.md) |
| An explicit pause ("stop for now"). Never on "keep going" | [playbooks/pause.md](playbooks/pause.md) |
| A read-only question: how does X work, why is Y like this, are we sure | [playbooks/investigation.md](playbooks/investigation.md) |
| Something is broken or behaves wrong | [playbooks/bug.md](playbooks/bug.md) |
| A measured slowness, fixed once | [playbooks/perf.md](playbooks/perf.md) |
| Improve one metric toward a target over many attempts | [playbooks/hillclimb.md](playbooks/hillclimb.md) |
| Change the structure, keep the behavior | [playbooks/refactor.md](playbooks/refactor.md) |
| One mechanical change across many call sites, or a migration | [playbooks/wide-change.md](playbooks/wide-change.md) |
| A design question that needs something runnable to settle | Call the Skill tool with "tstack:prototype". |
| New or changed behavior | [playbooks/feature.md](playbooks/feature.md) |
| The user will be away ("going to bed", "run until done", "trust it when I'm back") | Tell the user to run `/tstack:afk` with the task. Stop. |
| Nothing above fits | [playbooks/figure-it-out.md](playbooks/figure-it-out.md) |

## 2. Run the playbook visibly

1. Read the playbook file.
2. Before any task-specific todo, add each playbook step to the task list (TaskCreate or TodoWrite, whichever this harness has), wording copied verbatim.
3. A step you decide not to do stays in the list as `skip: <reason>`. Never drop a step silently.
4. Work the steps in order. Each step ends in a check before the next begins.
5. Finish with the playbook's Reply section.

## 3. Rules on every route

- **Data shape first.** Before writing logic, name the data shape and the structure the code hangs on (state machine, registry, typed model).
- **Observe, don't ask.** A "which approach" fork whose answer you could observe by running something is yours: settle it with tstack:prototype or a quick experiment and report the result. Ask the user only for product or preference calls no experiment can settle.
- **Prove before done.** Call the Skill tool with "tstack:prove" before declaring any change done. Report VERIFIED, NOT VERIFIED or INCONCLUSIVE with evidence.
- **Principles as vocabulary.** For a design or trade-off decision, call the Skill tool with "tstack:principles" and name the principle that changed each decision.
- **Own your subagents.** Brief them with pointers, read their diffs yourself, write your own summary.
- **Phase boundaries.** When a phase ends, choose continue, clear, handoff, subagent or compact with [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md). Mid-phase, continue or split the rest into subagents.
- **Candor.** "Not worth doing" is an acceptable answer. Say it with the reason.

## Flow map

Answer `?` from this map. Name commands exactly as written.

**Main flow: idea to ship.**

1. `/tstack:grill-with-docs` in a repo (`/tstack:grill-me` outside one) until you and the agent share one design. Questions that need running code detour through tstack:prototype.
2. Fits in one smart zone (about 150k tokens)? Build it now with `/tstack:implement`. Bigger? `/tstack:to-spec`, then `/tstack:to-tickets`, then `/tstack:implement <ticket>` once per ticket, clearing context between tickets. Keep grilling, spec and tickets in one unbroken window.
3. `/tstack:ship` opens the PR and babysits it.
4. `/tstack:reflect` after a long or bumpy task: turn each repeated correction into a type, lint rule, hook or standard.

**Unattended.** `/tstack:afk` runs tickets or a goal under a written contract, with an independent verifier, a decision log and a morning report.

**On-ramps.** Something broken: `/tstack:work <symptom>` (bug playbook). A huge, foggy effort: `/tstack:wayfinder`. Incoming issues you did not write: `/tstack:triage`. A spare moment: `/tstack:improve-architecture`.

**Setup and upkeep.** `/tstack:setup` once per repo. `/tstack:create-verify` once per app, `/tstack:maintain-verify` when the app drifts from its feature map. `/tstack:context-audit` when sessions feel slow, noisy or expensive.

**Anytime.** `/tstack:handoff` moves work to another session, harness or person. `/tstack:wait-what` when a message did not land.

**Disciplines the agent loads on its own** (you can name them too): grilling, domain-modeling, codebase-design, principles, tdd, diagnose, prove, interrogate, how, why, prototype, research, decision-log, unslop, writing-for-agents, resolving-merge-conflicts, wizard, typescript, python, mobile.
