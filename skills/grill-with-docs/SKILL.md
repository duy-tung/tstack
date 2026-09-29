---
name: grill-with-docs
description: "A relentless interview to sharpen a plan or design, updating CONTEXT.md and ADRs as decisions settle."
disable-model-invocation: true
---

Call the Skill tool twice, for "tstack:grilling" and "tstack:domain-modeling".

Check both loaded: if your questions come without recommended answers, grilling did not load; if `CONTEXT.md` is never touched when a term settles, domain-modeling did not load. Call the Skill tool again for whichever is missing.

When the user confirms the shared understanding, name the next step and stop: `/tstack:to-spec` for work that spans sessions, `/tstack:implement` when it fits in this one. Both belong in this same conversation: tell the user not to clear or compact first.
