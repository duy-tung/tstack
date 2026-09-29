# Skill mechanics

The skill-specific branch of [writing-for-agents](SKILL.md): what changes when the document is a skill (frontmatter, the invocation choice, how skills call each other, and router skills). Everything else about writing it is the universal reference in `SKILL.md`.

## Invocation

Two choices, trading the two loads:

- A **model-invoked** skill keeps a `description`, so the agent can fire it autonomously, and other skills can reach it. You can still type its name: model-invocation always _includes_ user reach; a description only ever adds agent discovery, never removes the human's. The description is the skill's top-level context pointer, forced to stay loaded at all times: permanent context load in exchange for discoverability. A model-invoked skill whose content is all reference is also one home for shared reference: another skill can invoke it, so reference needed by several skills lives in one place. Mechanics: omit `disable-model-invocation`, and write a model-facing description carrying the trigger branches (the pointer-writing rules in `SKILL.md` apply in full).
- A **user-invoked** skill strips the description from the agent's reach: only the human typing its name can invoke it, and no other skill can. Zero context load, but it spends cognitive load: you are the index that must remember it exists. Mechanics: set `disable-model-invocation: true`; the `description` becomes human-facing: a one-line summary, trigger lists stripped.

Pick model-invocation only when the agent must reach the skill on its own, or another skill must. If it only ever fires by hand, make it user-invoked and pay no context load. The test is "could the model usefully reach for this autonomously?"; reuse is the reason to extract a skill, not the test.

The model never sees a user-invoked skill, so an agent asked about one may report it as not installed. Routers and wrappers name user-invoked skills for the human; nothing else can reach them.

Shared reference that two user-invoked skills both need can live in neither: with no descriptions, neither can fire the other. Push it to a plain file outside the skill system, or into a model-invoked skill both can call.

## Frontmatter

- `name`: kebab-case, equal to the folder name.
- `description`: for a user-invoked skill, a one-line human summary under 120 characters. For a model-invoked skill, what it does and when to use it, trigger cases front-loaded, under 300 characters. Quote a description that contains `: `, or YAML reads it as a mapping.
- `disable-model-invocation: true` on user-invoked skills only.
- Optional: `argument-hint`; `effort: high`, only for judgment-heavy skills (interviews, design, diagnosis, adversarial review, reflection); `allowed-tools`; `paths`, for stack packs only.

## Calling other skills

- **The call rule.** A user-invoked skill may call model-invoked skills. It never calls another user-invoked skill: it tells the user to run it instead (tell the user to run `/tstack:setup`). A model-invoked skill may call other model-invoked skills.
- **Name the tool.** An operative dependency is an explicit instruction: `Call the Skill tool with "tstack:grilling"`. Plugin skills carry their namespace (`tstack:<name>`). A bare `/tstack:<name>` in prose is a label for the human, not a call.
- **One skill per call.** A step that needs two skills is two calls: `Call the Skill tool twice, for "tstack:grilling" and "tstack:domain-modeling"`, never "call it with X and Y".
- **Reach material by calling its skill.** Links point at sibling files in the skill's own folder (a relative link to `RUBRIC.md`); never link `../other-skill/FILE.md`. The one exception is a file two user-invoked skills share, since neither can call the other: point at it as `${CLAUDE_SKILL_DIR}/../<skill>/<file>`, the way `implement` and `afk` reach the build playbook in `work`. Scripts run from `${CLAUDE_SKILL_DIR}/scripts/<file>`, which Claude Code resolves to the skill's folder in `SKILL.md`. A supporting file read later is plain text, so when a subagent needs one of the skill's files, pass the absolute path built in `SKILL.md`.
- **Check the load.** Naming a skill does not reliably load it. A wrapper that depends on another skill's behaviour names the tell that it loaded ("if your questions come without recommended answers, grilling did not load").
- **Reading is not calling.** Merely reading `CONTEXT.md` for vocabulary is a one-line prose pointer, not the domain-modeling skill.

## Subagents

- Spawn a named agent (`spawn the tstack:verifier agent`) or a built-in (`Explore`, `general-purpose`). Brief with file pointers, not pasted dumps. Each brief stands alone: goal, scope, context pointers, acceptance, verify, forbidden, report format.
- The main thread is the only spawner. End every brief with: "Do not invoke tstack skills or spawn agents. Do the work directly."
- You own each subagent's output: read its diff or file yourself, never pass its summary through.

## Per-repo config

Skills find the repo's tracker, labels, and domain docs through the `## Agent skills` block in `AGENTS.md` (or `CLAUDE.md`). A skill that cannot work without that config (it publishes to a tracker or applies labels) says so in one line: tell the user to run `/tstack:setup`. Every other skill proceeds silently when a doc is missing, and names "the project's domain glossary" and "ADRs in the area" in plain prose.

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `SKILL.md`): split off a model-invoked skill when you have a distinct leading word that should trigger it on its own (a trigger word you actually use in your prompts), or another skill must reach it. You pay context load for the new always-loaded description, so that independent reach has to be worth it.

## Router skills

When user-invoked skills multiply past what you can remember, that piled-up cognitive load is cured by a **router skill**: one user-invoked skill that names the others and when to reach for each, so the human has one skill to remember instead of many (tstack's is `/tstack:work`). It can only hint, never fire them: user-invoked skills have no description, so nothing but the human can reach them. Adding, renaming, or removing a user-reachable skill means updating the router, or it becomes a router that lies.
