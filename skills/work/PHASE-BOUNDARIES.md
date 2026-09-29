# Phase boundaries

A **phase** is a chunk of work inside a session: the grilling, the implementation, the QA. A phase ends when you think "ok, we're done with that".

The **phase boundary** is the gap between two phases, and it is the only place this decision belongs. Mid-phase there is no decision to make: continue, or split the work that's left into subagents. Compacting mid-phase makes the agent lose the thread. If auto-compact fires, the boundary went unclaimed.

## The five options

| Option | What it does |
|---|---|
| **Continue** | Stay in the session. No context switch at all. |
| **`/clear`** | Empty the context window and start from nothing. |
| **`/tstack:handoff`** | Write a portable markdown file and seed a session anywhere with it. |
| **Subagent** | Send the task to its own context window and get a report back. |
| **`/compact`** | Compress this context and seed a fresh session with the summary. |

## The tree

Work top to bottom at the boundary. The first **yes** wins.

**1. Can you continue in this session?** Two things make the answer yes: the next phase needs this phase as a **primary source**, or enough smart zone is left (the first ~150k tokens) for the next phase to fit. Grilling to implementation is the standard yes: the implementation wants the reasoning verbatim, not a summary of it. Continue costs nothing and loses nothing, so rule it out before anything else.

**2. Is the context irrelevant to what comes next?** Is everything in this session (the exploration, the decisions, the dead ends) disposable, or already written down in a spec, ticket, commit or decision log? If so, **`/clear`**. It is the cheapest move: it takes no time and hands back the whole window. The old session stays resumable.

Getting this wrong is one-way. Clear a *relevant* context and you lose the **why** behind what you built, and reading the diff back does not return it.

**3. Do you need to hand off?** `/tstack:handoff` is narrow. You need it only when you are:

- swapping to a **new harness** (Claude Code to Codex),
- moving to a **new directory** or repo,
- sending the work to a **colleague**,
- or forking a side task you found **mid-phase** without derailing what you are doing.

That list is the whole clause. What a handoff buys is **portability**: a file that travels.

**4. Can the task be done AFK?** Is it scoped tightly enough to run with you away from the keyboard? Then send it to a **subagent** and leave this session untouched: a scoped investigation, a research question, a migration batch. Review and verification already work this way: tstack:interrogate and tstack:prove spawn their own fresh agents, so call them from this thread, never from inside a subagent.

**5. Otherwise, `/compact`.** Relevant context, same harness, same directory, and you need to stay in the loop. Pass it an instruction (`/compact we're going to QA this area`) so the summary keeps what the next phase needs.

`/compact` is the **default, not the first reach**. The failure mode when people start here is a fresh session that is confidently wrong about a decision the summary flattened.

## Primary and secondary sources

Every move except **Continue** turns a **primary source** into a **secondary source**: the session as it happened, replaced by a summary of it.

| Source | Information | Noise | Room to move |
|---|---|---|---|
| Primary (Continue) | Full | Lots | Little |
| Secondary (`/compact`, handoff) | Lossy | Less | Lots |

This is why question 1 comes first. Pay the lossiness only when staying costs more than it saves.

## Rules of thumb

- Between tickets of one spec: **clear**. The spec, the tickets and the commits hold the context.
- If clear and compact feel 50/50, **clear**: it is faster and cheaper.
- These are judgement calls. The value is in asking the questions in order, at the boundary.
