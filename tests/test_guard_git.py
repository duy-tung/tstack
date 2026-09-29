#!/usr/bin/env python3
"""Table test for hooks/guard_git.py. Run: python3 tests/test_guard_git.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "guard_git.py")
TMP = tempfile.mkdtemp(prefix="tstack-guard-test-")


def run(command, cwd, env=None):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd, "hook_event_name": "PreToolUse"})
    e = dict(os.environ)
    for key in ("TSTACK_GIT_GUARD", "TSTACK_PROTECTED_BRANCHES"):
        e.pop(key, None)
    if env:
        e.update(env)
    r = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, env=e)
    return r.returncode, r.stderr.strip()


def repo(name, branch):
    d = os.path.join(TMP, name)
    subprocess.run(["git", "init", "-q", "-b", branch, d], check=True)
    return d


feature = repo("feature", "feature/x")
main = repo("main", "main")
custom = repo("custom", "staging")
subprocess.run(["git", "-C", custom, "config", "tstack.protectedBranches", "main,staging"], check=True)
os.makedirs(os.path.join(feature, ".githooks"))
with open(os.path.join(feature, ".githooks", "pre-commit"), "w") as fh:
    fh.write("#!/bin/sh\nexit 0\n")
os.makedirs(os.path.join(feature, "docs"))
with open(os.path.join(feature, "docs", "README.md"), "w") as fh:
    fh.write("# docs\n")
subdir = os.path.join(feature, "sub")
os.makedirs(subdir)

CLAUDE_COMMIT = """git commit -m "$(cat <<'EOF'
fix(guard): stop treating quoted text as commands

It doesn't block `git reset --hard` (or rm -rf /) inside a message anymore.
EOF
)\""""

HEREDOC_FILE = """git commit -F - <<'EOF'
git reset --hard is now blocked; see tests.
EOF"""

HEREDOC_UNQUOTED = """cat <<EOF
$(git reset --hard)
EOF"""

BLOCK, ALLOW = 2, 0
cases = [
    # (command, cwd, expected)
    ("git status", feature, ALLOW),
    ("git push -u origin feature/x", feature, ALLOW),
    ("git push --force-with-lease origin feature/x", feature, ALLOW),
    ("git push --force origin feature/x", feature, BLOCK),
    ("git push -f", feature, BLOCK),
    ("git push -uf origin feature/x", feature, BLOCK),
    ("git push origin +feature/x", feature, BLOCK),
    ("git push origin :old-branch", feature, BLOCK),
    ("git push --delete origin old", feature, BLOCK),
    ("git push origin HEAD:main", feature, BLOCK),
    ("git push origin main", feature, BLOCK),
    ("git push origin release/1.2", feature, BLOCK),
    ("git push", main, BLOCK),
    ("git push origin", main, BLOCK),
    ("git push", feature, ALLOW),
    ("git push --no-verify", feature, BLOCK),
    ("git -C sub push --force", feature, BLOCK),
    ("cd app && git push --force", feature, BLOCK),
    ("git reset --hard HEAD~1", feature, BLOCK),
    ("git reset --soft HEAD~1", feature, ALLOW),
    ("git reset HEAD file.txt", feature, ALLOW),
    ("git clean -fd", feature, BLOCK),
    ("git clean -xdf", feature, BLOCK),
    ("git clean -n -fd", feature, ALLOW),
    ("git clean -nd", feature, ALLOW),
    ("git branch -D old", feature, BLOCK),
    ("git branch -d old", feature, ALLOW),
    ("git branch --delete --force old", feature, BLOCK),
    ("git checkout .", feature, BLOCK),
    ("git checkout -- .", feature, BLOCK),
    ("git checkout -- src/a.ts", feature, ALLOW),
    ("git checkout -b new-branch", feature, ALLOW),
    ("git checkout -f main", feature, BLOCK),
    ("git restore .", feature, BLOCK),
    ("git restore --staged .", feature, ALLOW),
    ("git restore src/a.ts", feature, ALLOW),
    ("git stash drop", feature, BLOCK),
    ("git stash clear", feature, BLOCK),
    ("git stash push -u -m wip", feature, ALLOW),
    ("git commit -m 'fix: thing'", feature, ALLOW),
    ("git commit -n -m 'skip hooks'", feature, BLOCK),
    ("git commit --no-verify -m x", feature, BLOCK),
    ("HUSKY=0 git commit -m x", feature, BLOCK),
    ("git -c core.hooksPath=/dev/null commit -m x", feature, BLOCK),
    ("git config core.hooksPath .nohooks", feature, BLOCK),
    ("git filter-branch --tree-filter x", feature, BLOCK),
    ("git gc --prune=now", feature, BLOCK),
    ("git gc", feature, ALLOW),
    ("git commit -m 'docs: explain why git push --force is banned'", feature, ALLOW),
    ("echo 'git reset --hard'", feature, ALLOW),
    ("rm -rf node_modules dist", feature, ALLOW),
    ("rm -rf .", feature, BLOCK),
    ("rm -rf /", feature, BLOCK),
    ("rm -rf ~", feature, BLOCK),
    ("rm -rf ./*", feature, BLOCK),
    ("rm file.txt", feature, ALLOW),
    ("npm run format", feature, ALLOW),
    # HEAD, --all, tags, branch names
    ("git push -u origin HEAD", main, BLOCK),
    ("git push -u origin HEAD", feature, ALLOW),
    ("git push origin @", main, BLOCK),
    ("git push --all origin", feature, BLOCK),
    ("git push origin --tags", main, ALLOW),
    ("git push origin v1.2.3", main, ALLOW),
    ("git push --follow-tags", main, BLOCK),
    ("git push -u origin hotfix/login-crash", feature, ALLOW),
    ("git push -u origin release-notes-typo", feature, ALLOW),
    ("git push origin refs/heads/main", feature, BLOCK),
    ("git push", custom, BLOCK),
    ("git push origin main", custom, BLOCK),
    ("git push origin develop", custom, BLOCK),
    ("git push origin feature/y", custom, ALLOW),
    # core.hooksPath
    ("git config core.hooksPath .githooks", feature, ALLOW),
    ("git config --get core.hooksPath", feature, ALLOW),
    ("git config core.hooksPath", feature, ALLOW),
    ("git config core.hooksPath /dev/null", feature, BLOCK),
    ("git config --unset core.hooksPath", feature, BLOCK),
    ("git config --global core.hooksPath .githooks", feature, BLOCK),
    ("git config core.hooksPath ''", feature, BLOCK),
    # quoted text, heredocs and messages are data
    ('gh pr create --body "Replaces \\`git clean -fd\\` in CI"', feature, ALLOW),
    (CLAUDE_COMMIT, feature, ALLOW),
    (HEREDOC_FILE, feature, ALLOW),
    ('git commit -m "-n is not a flag here"', feature, ALLOW),
    ("git commit -nm 'x'", feature, BLOCK),
    ("git commit -am 'x'", feature, ALLOW),
    ('grep -rn "reset --hard" .', feature, ALLOW),
    ("git log --oneline | head", feature, ALLOW),
    ("git log --oneline # then git push -f", feature, ALLOW),
    ("git diff 2>&1 | tee /tmp/out.txt", feature, ALLOW),
    ("git push origin feature/x > /dev/null 2>&1", feature, ALLOW),
    # substitutions really execute
    ('gh pr create --body "Replaces `git clean -fd` in CI"', feature, BLOCK),
    ('echo "$(git reset --hard)"', feature, BLOCK),
    (HEREDOC_UNQUOTED, feature, BLOCK),
    ("diff <(git stash drop) b", feature, BLOCK),
    # wrappers, lists, subshells, loops
    ("sudo rm -rf /", feature, BLOCK),
    ("sudo -u root rm -rf ~", feature, BLOCK),
    ("FOO=1 rm -rf ~", feature, BLOCK),
    ("for b in $(git branch --merged); do git branch -D $b; done", feature, BLOCK),
    ("if true; then git reset --hard; fi", feature, BLOCK),
    ("(git reset --hard)", feature, BLOCK),
    ("{ git reset --hard; }", feature, BLOCK),
    ("git branch --merged | xargs git branch -D", feature, BLOCK),
    ("git branch --merged | xargs -n 1 git branch -d", feature, ALLOW),
    ("timeout 60 git push --force", feature, BLOCK),
    ("nice -n 10 git push -f", feature, BLOCK),
    ("sleep 1 & git push -f", feature, BLOCK),
    ('bash -c "git reset --hard"', feature, BLOCK),
    ("bash -lc 'git push -f'", feature, BLOCK),
    ("eval 'git reset --hard'", feature, BLOCK),
    ("export HUSKY=0; git commit -m x", feature, BLOCK),
    ("env HUSKY=0 git commit -m x", feature, BLOCK),
    ("SKIP=eslint git commit -m x", feature, BLOCK),
    ("git push \\\n  --force", feature, BLOCK),
    ("git switch -f main", feature, BLOCK),
    ("git switch --discard-changes main", feature, BLOCK),
    ("git switch -c new-thing", feature, ALLOW),
    ("git worktree remove --force ../wt", feature, BLOCK),
    ("git worktree remove ../wt", feature, ALLOW),
    ("rm -rf .git", feature, BLOCK),
    ("rm -rf -- /", feature, BLOCK),
    ('rm -rf "$HOME"', feature, BLOCK),
    ("rm -rf ${HOME}/*", feature, BLOCK),
    ("rm -rf build/ .cache", feature, ALLOW),
    ("rm -rf ./dist", feature, ALLOW),
    # second review round
    ("git config tstack.protectedBranches none", feature, BLOCK),
    ("git config --unset tstack.protectedBranches", feature, BLOCK),
    ("git config --get tstack.protectedBranches", feature, ALLOW),
    ("git push -u origin $(git branch --show-current)", main, BLOCK),
    ("git push -u origin $(git branch --show-current)", feature, ALLOW),
    ('git push origin "$(git rev-parse --abbrev-ref HEAD)"', main, BLOCK),
    ('BRANCH=main; git push origin "$BRANCH"', feature, BLOCK),
    ('git push origin "$SOME_BRANCH"', feature, ALLOW),
    ("git config core.hooksPath docs", feature, BLOCK),
    ("git config core.hooksPath src/../../outside", feature, BLOCK),
    ("git config core.hooksPath .githooks", subdir, ALLOW),
    ("bash <<'EOF'\ngit reset --hard\nEOF", feature, BLOCK),
    ("sh -s <<EOF\ngit push -f\nEOF", feature, BLOCK),
    ("echo 'git reset --hard' | bash", feature, BLOCK),
    ("printf 'git status\\ngit clean -fd\\n' | sh", feature, BLOCK),
    ("cat <<'EOF' | grep reset\ngit reset --hard\nEOF", feature, ALLOW),
    ("echo 'git reset --hard' | grep reset", feature, ALLOW),
    ("function nuke { git reset --hard; }; nuke", feature, BLOCK),
    ("git stash -q drop", feature, BLOCK),
    ("git rm -rf .", feature, BLOCK),
    ("git rm -r --cached .", feature, ALLOW),
    ("git rm -f src/a.ts", feature, ALLOW),
    ("flock /tmp/l git push -f", feature, BLOCK),
    # ordinary developer commands
    ('python3 -c "print(\'git reset --hard\')"', feature, ALLOW),
    ("git fetch --prune", feature, ALLOW),
    ("git remote prune origin", feature, ALLOW),
    ("git pull --rebase", feature, ALLOW),
    ("git log -p -- src/", feature, ALLOW),
    ("git status --porcelain && git diff --stat", feature, ALLOW),
    ("ls -la | grep git", feature, ALLOW),
    ("npm test -- --watch=false", feature, ALLOW),
    ("docker compose up -d && git log -1", feature, ALLOW),
    ("git rebase -i HEAD~3", feature, ALLOW),
    ("git commit --amend --no-edit", feature, ALLOW),
    ("git tag -a v1.0.0 -m 'release 1.0.0' && git push origin v1.0.0", feature, ALLOW),
    ("git switch -c fix/login && git push -u origin fix/login", main, ALLOW),
]

fails = 0
try:
    for cmd, cwd, expected in cases:
        code, err = run(cmd, cwd)
        ok = code == expected
        fails += not ok
        label = cmd.replace("\n", "\\n")
        print(f"{'ok  ' if ok else 'FAIL'} {expected} got {code}  {label}" + ("" if ok else f"   <{err}>"))

    extra = 0
    code, _ = run("git push --force", feature, env={"TSTACK_GIT_GUARD": "off"})
    print(("ok  " if code == 0 else "FAIL") + " guard off via environment allows")
    fails += code != 0
    extra += 1
    code, _ = run("TSTACK_GIT_GUARD=off git push --force", feature)
    print(("ok  " if code == 2 else "FAIL") + " inline assignment does not disable the guard")
    fails += code != 2
    extra += 1
    code, _ = run("git push origin develop", feature, env={"TSTACK_PROTECTED_BRANCHES": "develop"})
    print(("ok  " if code == 2 else "FAIL") + " TSTACK_PROTECTED_BRANCHES protects its branches")
    fails += code != 2
    extra += 1
    code, _ = run("git push origin main", feature, env={"TSTACK_PROTECTED_BRANCHES": "develop"})
    print(("ok  " if code == 0 else "FAIL") + " TSTACK_PROTECTED_BRANCHES replaces the defaults")
    fails += code != 0
    extra += 1

    non_bash = subprocess.run([sys.executable, HOOK], input=json.dumps({"tool_name": "Edit", "tool_input": {}}), capture_output=True, text=True)
    print(("ok  " if non_bash.returncode == 0 else "FAIL") + " non-Bash tool passes")
    fails += non_bash.returncode != 0
    extra += 1
    garbage = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True)
    print(("ok  " if garbage.returncode == 0 else "FAIL") + " malformed input passes")
    fails += garbage.returncode != 0
    extra += 1

    total = len(cases) + extra
    print(f"\n{total - fails}/{total} passed")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if fails else 0)
