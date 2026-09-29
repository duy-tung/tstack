---
name: afk
description: "Run work unattended under a written contract: fresh worker per unit, independent verifier, review, decision log, morning report."
disable-model-invocation: true
argument-hint: "<goal, spec or tickets> [done: <predicate>]"
---

# AFK

You are the coordinator. You never write product code. Workers build, verifiers check, reviewers judge. You keep the contract, the queue, the ledger and the log, and you read every diff.

Run state lives in `.tstack/<slug>/` (gitignored): `contract.md`, `ledger.tsv`, `decisions.tsv`, `evidence/`, `report.md`.

## 1. Contract, while the user is still here

Write `.tstack/<slug>/contract.md` with these parts. A part you cannot fill means the run is not scoped yet: ask now.

1. **Goal.** One sentence.
2. **Done.** A checkable predicate: "all tickets under #12 closed and VERIFIED", "zero old callers, all tests green, old API deleted", "p95 under 200 ms and at least 10 attempts". A duration is not a done condition.
3. **Isolation.** A fresh run branch off `<base>`, in this checkout or a worktree. Never the default branch. Units merge into the run branch as part of the run.
4. **Granted in advance.** Commit without asking (yes). Push the run branch (yes or no). Open PRs (yes or no). Merge into `<base>` or merge PRs (default no).
5. **Budget.** A limit you can check during the run: an end time, a number of units, or a number of attempts. A budget is not a done condition.
6. **Escape hatch.** When truly stuck (the same gate failing after three distinct attempts, or a call only the user can make), stop and write up why. Never reinterpret the goal to finish.
7. **Always stop for** force-pushes to shared branches, deploys, data deletion, messages to people, and anything the user names. The grant does not cover these.
8. **Standing orders.** The user's numbered preferences. Every brief carries them verbatim.

Read the contract back and get an explicit go. Asking to see the plan is not a go.

## 2. Queue and trail

- **Tickets:** fetch the frontier with the issue tracker doc. Skip issues labelled `spec`. Order by blocking edges.
- **A goal without tickets:** design the units with the figure-it-out playbook at `${CLAUDE_SKILL_DIR}/../work/playbooks/figure-it-out.md`: riskiest unknown first, verification harness first.
- **Ledger:** `.tstack/<slug>/ledger.tsv` with columns `unit, status, head_sha, verdict, evidence, note`. Status is one of queued, building, built, verified, failed, blocked. A new head SHA voids the verdict on that row.
- **Decision log:** call the Skill tool with "tstack:decision-log" and log to `.tstack/<slug>/decisions.tsv`.

## 3. Pilot one unit end to end

Run the first unit through the whole loop below before scaling. A vague brief fails quietly because a worker cannot ask you a question. Tighten the brief template after the pilot.

## 4. Loop

Start every iteration by re-reading `contract.md` and the last rows of the ledger and log. This survives compaction. Write every `.tstack/<slug>/` path in a brief as an absolute path: `.tstack/` is gitignored, so it does not exist inside a worktree.

1. **Brief a fresh `tstack:ticket-worker`** (never resume one). Fields: GOAL, SCOPE (paths), CONTEXT (pointers: ticket URL, spec, the build playbook path `${CLAUDE_SKILL_DIR}/../work/playbooks/build.md`, and the absolute evidence directory `<run checkout>/.tstack/<slug>/evidence/<unit>/`), ACCEPTANCE, VERIFY (the ticket's `Verify:` line), FORBIDDEN, REPORT, STANDING ORDERS. "A field you cannot fill is a unit you have not scoped yet." Coupled units run one at a time and commit straight onto the run branch: record the run branch's head as `<before>` before you brief one. Units with no shared files may run in parallel, each spawned with `isolation: worktree`; each then commits on its own worktree branch.
2. **Read the report and the diff yourself.** A worker's DONE is a claim. For a worktree unit, diff from here: `git diff <run branch>...<unit branch>`.
3. **Integrate.** A worktree unit merges into the run branch now, one unit at a time: record the run branch's head as `<before>`, then `git merge --no-ff <unit branch>`. Everything below runs on the run branch, in its checkout (`cd` there first when the run branch lives in a worktree), so the verifier and the reviewers see the integrated code.
4. **Verify independently.** Spawn `tstack:verifier` with the commits since `<before>`, the acceptance criteria and the VERIFY line. The author never verifies its own work. Record verdict, head SHA and evidence path in the ledger.
5. **Review.** Call the Skill tool with "tstack:interrogate" with the arguments `<before> fix`. Under afk the coordinator does not edit: interrogate hands its Act-on list to you, and you give it to a fresh `tstack:ticket-worker` as a full brief whose GOAL is the Act-on list and whose SCOPE is the files it names. Verify again when a fix changed behavior.
6. **Settle the unit.** VERIFIED: close the ticket with the commit SHAs, verdict and evidence path. NOT VERIFIED or INCONCLUSIVE: a fresh worker gets the verifier's findings; at the escape hatch, revert the unit (`git revert -m 1 <merge>` for a merge, `git revert <shas>` otherwise), mark it failed in the ledger, and move on.
7. **Log** one decision-log row per unit, per pivot and per default you applied.
8. **Recompute the frontier.** Stop starting new units at about 70% of the budget, so the run can finish cleanly.

**Mid-run discoveries are yours.** Flaky tests, broken tools, related bugs, drift: fix them as their own unit and log it, then return to the predicate. Do not park reversible work for the user.

**Decisions only the user can make:** apply your recommended default, log it, and list it in the report with the one word that reverses it. Items on the always-stop list wait for the user.

**Waiting on something external** (CI, a deploy preview): watch it with a background Bash command (`gh pr checks <n> --watch`) or `/loop`. Never stack a second sleep loop.

## 5. Stop

- **Predicate met:** check the whole against the predicate on the real artifact (call the Skill tool with "tstack:prove"), then report.
- **Escape hatch hit:** stop and write up why, with what was tried.
- Never relax the predicate. A plateau is not a stop: pivot the approach.

## 6. Morning report

Write `.tstack/<slug>/report.md` and reply with it:

- The contract and the predicate's final state.
- Units: verified, not verified, blocked, each with evidence paths.
- Commits, branches and PRs.
- Defaults you applied, each with the word that reverses it.
- Open items and the next action.
- **Attention.** Run the decision-log end-of-run audit (its reviewer reads the trail) and put its flags here. "No flags" is a valid value.
