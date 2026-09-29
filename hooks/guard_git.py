#!/usr/bin/env python3
"""tstack PreToolUse guard for the Bash tool.

Blocks git operations that destroy work, rewrite shared history, push straight
to a protected branch, or bypass the repo's own checks, plus a few
catastrophic rm invocations. Everything else passes untouched.

Contract: reads the hook JSON on stdin. Exit 0 allows. Exit 2 blocks, and
stderr is shown to the model as the reason. Anything unexpected allows: this is
a seatbelt against accidents, not a sandbox.

The command is parsed like a shell would split it: quotes, escapes, heredocs,
comments, pipelines, lists, subshells, command and process substitution,
`bash -c`, `eval`, text piped or heredoc'd into a shell, and common wrappers
(sudo, env, timeout, nice, xargs, flock...). Text inside quotes, quoted
heredocs or comments is data, never a command.

Protected branches default to main, master, trunk, develop, production, prod,
release and release/*. A repo can add branches (never remove them) with
    git config --add tstack.protectedBranches staging
which the user runs: the guard blocks the agent from writing tstack.* keys.
TSTACK_PROTECTED_BRANCHES="main,staging" in the launch environment replaces
the whole list.

The user (not the agent) can disable the guard for one Claude Code launch with
TSTACK_GIT_GUARD=off in the environment that starts claude. Inline
assignments inside the command are ignored on purpose.
"""

import fnmatch
import json
import os
import re
import subprocess
import sys

DEFAULT_PROTECTED = ["main", "master", "trunk", "develop", "production", "prod", "release", "release/*"]

GIT_GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}

# Environment values that make git hooks a no-op.
BYPASS_ENV = {"HUSKY": {"0"}, "HUSKY_SKIP_HOOKS": {"1", "true"}, "SKIP_HOOKS": {"1", "true"}}
HOOK_RUNNING = {"commit", "push", "merge", "rebase", "am", "cherry-pick", "revert"}

SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
KEYWORDS = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "!", "{", "}", "coproc"}
CLAUSES = {"for", "select", "case", "esac", "in"}

# Wrapper commands: options that take a separate value, and how many
# positional words to skip before the wrapped command starts.
WRAPPERS = {
    "sudo": ({"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U", "-T"}, 0),
    "doas": ({"-u", "-C"}, 0),
    "env": ({"-u", "-C", "-S", "--unset", "--chdir"}, 0),
    "command": (set(), 0),
    "builtin": (set(), 0),
    "exec": ({"-a"}, 0),
    "nohup": (set(), 0),
    "time": ({"-f", "-o", "--format", "--output"}, 0),
    "timeout": ({"-s", "-k", "--signal", "--kill-after"}, 1),
    "nice": ({"-n", "--adjustment"}, 0),
    "ionice": ({"-c", "-n", "-p", "-P", "-u"}, 0),
    "stdbuf": ({"-i", "-o", "-e"}, 0),
    "xargs": ({"-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a", "--arg-file", "--delimiter",
               "--max-args", "--max-procs", "--max-lines", "--replace", "--eof", "--max-chars"}, 0),
    "watch": ({"-n", "--interval", "-d"}, 0),
    "chronic": (set(), 0),
    "caffeinate": ({"-t", "-w"}, 0),
    "flock": ({"-w", "--wait", "--timeout", "-E", "--conflict-exit-code"}, 1),
}

ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SUB = "\x00sub\x00"  # placeholder for the unknown output of a substitution


class Blocked(Exception):
    pass


def block(reason, alternative):
    raise Blocked(f"BLOCKED by tstack guard: {reason}. {alternative} "
                  "If the user really wants this, ask them to run it themselves.")


# --------------------------------------------------------------------------
# Shell parsing
# --------------------------------------------------------------------------

def find_backtick_end(text, i):
    n = len(text)
    while i < n:
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            return i
        i += 1
    return n


def read_heredoc_body(text, i, delim, strip_tabs):
    """Return (body, index after the delimiter line) for a heredoc body at i."""
    n, start = len(text), i
    while i < n:
        j = text.find("\n", i)
        line_end = n if j == -1 else j
        line = text[i:line_end]
        if (line.lstrip("\t") if strip_tabs else line) == delim:
            return text[start:i], (n if j == -1 else j + 1)
        i = n if j == -1 else j + 1
    return text[start:], n


def skip_heredoc_bodies(text, i, pending):
    """Skip the heredoc bodies that start at i. Return the index after them."""
    for entry in pending:
        _, i = read_heredoc_body(text, i, entry[0], entry[2])
    return i


HEREDOC_OP = re.compile(r"<<(-?)[ \t]*(?:'([^']*)'|\"([^\"]*)\"|(\\?)([^\s;&|()<>'\"]+))")


def find_paren_end(text, i):
    """Index of the ')' closing a '$(' or '(' whose body starts at i."""
    depth, n, pending = 1, len(text), []
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            j = text.find("'", i + 1)
            i = n if j == -1 else j + 1
            continue
        if c == '"':
            i = skip_double(text, i + 1)
            continue
        if c == "`":
            i = find_backtick_end(text, i + 1) + 1
            continue
        if c == "$" and text.startswith("$(", i):
            i = find_paren_end(text, i + 2) + 1
            continue
        if c == "<" and text.startswith("<<", i) and not text.startswith("<<<", i):
            m = HEREDOC_OP.match(text, i)
            if m:
                delim = m.group(2) if m.group(2) is not None else m.group(3) if m.group(3) is not None else m.group(5)
                pending.append((delim, True, m.group(1) == "-"))
                i = m.end()
                continue
        if c == "\n" and pending:
            i = skip_heredoc_bodies(text, i + 1, pending)
            pending = []
            continue
        if c == "#" and (i == 0 or text[i - 1] in " \t\n;&|("):
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n


def skip_double(text, i):
    """Index after the '"' that closes a double-quoted string starting at i."""
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i + 1
        if c == "$" and text.startswith("$(", i):
            i = find_paren_end(text, i + 2) + 1
            continue
        if c == "`":
            i = find_backtick_end(text, i + 1) + 1
            continue
        i += 1
    return n


def collect_substitutions(text, nested):
    """Command substitutions in text that the shell expands (heredoc bodies)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "$" and text.startswith("$((", i):
            i += 3
            continue
        if c == "$" and text.startswith("$(", i):
            j = find_paren_end(text, i + 2)
            nested.append(text[i + 2:j])
            i = j + 1
            continue
        if c == "`":
            j = find_backtick_end(text, i + 1)
            nested.append(text[i + 1:j].replace("\\`", "`"))
            i = j + 1
            continue
        i += 1


REDIRECT = re.compile(r"&>>|&>|<<<|<<-|<<|>>|>&|<&|>\||<>|>|<")


def parse_commands(text, depth=0):
    """Split shell text into simple commands: (words after quote removal,
    came_from_a_substitution). Commands inside substitutions come back too,
    as their own entries. Never executes anything."""
    if depth > 6:
        return []
    commands, words, nested, pending, ops, executed = [], [], [], [], [], []
    state = {"buf": [], "in_word": False, "quoted": False, "redirect": None}
    i, n = 0, len(text)

    def end_word():
        if state["in_word"]:
            word = "".join(state["buf"])
            op = state["redirect"]
            if op is not None:
                if op in ("<<", "<<-"):
                    pending.append((word, state["quoted"], op == "<<-", len(commands)))
                state["redirect"] = None
            else:
                words.append(word)
        state["buf"], state["in_word"], state["quoted"] = [], False, False

    def end_command(op=None):
        end_word()
        if words:
            commands.append((list(words), depth > 0))
            ops.append(op)
        words.clear()

    def add(s, quoted=False):
        state["buf"].append(s)
        state["in_word"] = True
        state["quoted"] = state["quoted"] or quoted

    while i < n:
        c = text[i]
        if c == "\\":
            if text.startswith("\\\n", i):
                i += 2
                continue
            if i + 1 < n:
                add(text[i + 1], quoted=True)
            i += 2
            continue
        if c == "'":
            j = text.find("'", i + 1)
            j = n if j == -1 else j
            add(text[i + 1:j], quoted=True)
            i = j + 1
            continue
        if c == '"':
            out, i = [], i + 1
            while i < n and text[i] != '"':
                d = text[i]
                if d == "\\" and i + 1 < n and text[i + 1] in '$`"\\\n':
                    if text[i + 1] != "\n":
                        out.append(text[i + 1])
                    i += 2
                    continue
                if d == "$" and text.startswith("$((", i):
                    out.append(SUB)
                    i = find_paren_end(text, i + 3) + 2
                    continue
                if d == "$" and text.startswith("$(", i):
                    j = find_paren_end(text, i + 2)
                    nested.append(text[i + 2:j])
                    out.append(SUB)
                    i = j + 1
                    continue
                if d == "`":
                    j = find_backtick_end(text, i + 1)
                    nested.append(text[i + 1:j].replace("\\`", "`"))
                    out.append(SUB)
                    i = j + 1
                    continue
                out.append(d)
                i += 1
            add("".join(out), quoted=True)
            i += 1
            continue
        if c == "`":
            j = find_backtick_end(text, i + 1)
            nested.append(text[i + 1:j].replace("\\`", "`"))
            add(SUB)
            i = j + 1
            continue
        if c == "$" and text.startswith("$((", i):
            add(SUB)
            i = find_paren_end(text, i + 3) + 2
            continue
        if c == "$" and text.startswith("$(", i):
            j = find_paren_end(text, i + 2)
            nested.append(text[i + 2:j])
            add(SUB)
            i = j + 1
            continue
        if c in "<>" and text.startswith("(", i + 1):
            j = find_paren_end(text, i + 2)
            nested.append(text[i + 2:j])
            add(SUB)
            i = j + 1
            continue
        if c in "<>" or (c == "&" and text.startswith(">", i + 1)):
            buf = "".join(state["buf"])
            if state["in_word"] and buf.isdigit() and not state["quoted"]:
                state["buf"], state["in_word"] = [], False
            else:
                end_word()
            op = REDIRECT.match(text, i).group(0)
            state["redirect"] = op
            i += len(op)
            continue
        if c == "\n":
            end_command("\n")
            i += 1
            for delim, quoted, strip_tabs, owner in pending:
                body, i = read_heredoc_body(text, i, delim, strip_tabs)
                if owner < len(commands) and stdin_shell(commands[owner][0]):
                    executed.append(body)  # the shell runs the body
                elif not quoted:
                    collect_substitutions(body, nested)
            pending.clear()
            continue
        if c in ";&|()":
            op = text[i:i + 2] if text.startswith(("&&", "||", ";;", "|&"), i) else c
            end_command(op)
            i += len(op)
            continue
        if c in " \t\r":
            end_word()
            i += 1
            continue
        if c == "#" and not state["in_word"]:
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        add(c)
        i += 1
    end_command()
    # `echo '...' | bash` runs the echoed text.
    for k in range(1, len(commands)):
        if ops[k - 1] in ("|", "|&") and stdin_shell(commands[k][0]):
            feeder = unwrap(commands[k - 1][0])
            if feeder and feeder[1] and os.path.basename(feeder[1][0]) in ("echo", "printf"):
                args = [a for a in feeder[1][1:] if not (a.startswith("-") and len(a) <= 3)]
                executed.append(" ".join(args).replace("\\n", "\n"))
    for body in executed:
        commands.extend((w, False) for w, _ in parse_commands(body, depth + 1))
    for inner in nested:
        commands.extend((w, True) for w, _ in parse_commands(inner, depth + 1))
    return commands


def stdin_shell(words):
    """True when words start a shell that reads its commands from stdin."""
    unwrapped = unwrap(words)
    if not unwrapped or not unwrapped[1]:
        return False
    rest = unwrapped[1]
    if os.path.basename(rest[0]) not in SHELLS:
        return False
    letters, _, positional = parse_opts(rest[1:], short_value="oO")
    return "c" not in letters and ("s" in letters or not positional)


def short_cluster(word):
    return word.startswith("-") and not word.startswith("--") and len(word) > 1


def unwrap(words):
    """Strip keywords, assignments and wrapper commands.
    Return (env, words) where words starts at the real command, or None."""
    env, i, n = {}, 0, len(words)
    while i < n:
        w = words[i]
        if w in KEYWORDS:
            i += 1
            continue
        if w == "function":
            i += 2  # the keyword and the function name; the body follows
            continue
        if w in CLAUSES:
            return None
        if ASSIGNMENT.match(w):
            key, _, value = w.partition("=")
            env[key] = value
            i += 1
            continue
        name = os.path.basename(w)
        if name in WRAPPERS:
            with_value, positional = WRAPPERS[name]
            i += 1
            while i < n:
                v = words[i]
                if v == "--":
                    i += 1
                    break
                if name == "env" and ASSIGNMENT.match(v):
                    key, _, value = v.partition("=")
                    env[key] = value
                    i += 1
                    continue
                if v.startswith("-") and len(v) > 1:
                    i += 2 if (v in with_value and "=" not in v) else 1
                    continue
                break
            i += positional
            continue
        break
    if i >= n:
        return env, []
    return env, words[i:]


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def git_output(cwd, *args):
    try:
        out = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def protected_patterns(cwd):
    """The launch environment replaces the list; repo git config only adds to
    it, so nothing written from inside a session can loosen protection."""
    replaced = os.environ.get("TSTACK_PROTECTED_BRANCHES")
    if replaced:
        return [p.strip() for p in replaced.split(",") if p.strip()]
    extra = git_output(cwd, "config", "--get-all", "tstack.protectedBranches")
    return DEFAULT_PROTECTED + [p.strip() for p in re.split(r"[,\n]", extra) if p.strip()]


VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def expand(word, env):
    """Expand $NAME and ${NAME} from assignments seen in this command."""
    def value(m):
        name = m.group(1) or m.group(2)
        return env[name] if name in env else m.group(0)
    return VARIABLE.sub(value, word)


def unknown(word):
    return SUB in word or "$" in word


def is_protected(branch, patterns):
    branch = branch[len("refs/heads/"):] if branch.startswith("refs/heads/") else branch
    return any(fnmatch.fnmatchcase(branch, p) for p in patterns)


def parse_opts(args, short_value="", long_value=()):
    """Return (short letters, long flags, positionals) for a git subcommand.
    short_value: letters whose option takes a value; long_value: long options
    that take a separate value when written without '='."""
    letters, longs, positional = set(), set(), []
    i, n = 0, len(args)
    while i < n:
        a = args[i]
        if a == "--":
            positional.extend(args[i + 1:])
            break
        if a.startswith("--"):
            name = a.split("=", 1)[0]
            longs.add(name)
            i += 2 if (name in long_value and "=" not in a) else 1
            continue
        if short_cluster(a):
            j = 1
            while j < len(a):
                letter = a[j]
                letters.add(letter)
                if letter in short_value:
                    if j == len(a) - 1:
                        i += 1  # value is the next word
                    break  # the rest of the cluster is the value
                j += 1
            i += 1
            continue
        positional.append(a)
        i += 1
    return letters, longs, positional


def split_git(words):
    """Return (globals, subcommand, args) for a git invocation."""
    i, n, globals_ = 1, len(words), []
    while i < n and words[i].startswith("-"):
        opt = words[i]
        globals_.append(opt)
        if opt in GIT_GLOBAL_OPTS_WITH_VALUE and i + 1 < n:
            globals_.append(words[i + 1])
            i += 2
        else:
            i += 1
    if i >= n:
        return globals_, "", []
    return globals_, words[i], words[i + 1:]


def repo_dir(globals_, cwd):
    if "-C" in globals_:
        idx = globals_.index("-C")
        if idx + 1 < len(globals_):
            return os.path.join(cwd, os.path.expanduser(globals_[idx + 1]))
    return cwd


def check_push(args, cwd, env):
    letters, longs, positional = parse_opts(args, short_value="o", long_value=("--push-option", "--repo", "--receive-pack", "--exec"))
    if "--no-verify" in longs:
        block("git push --no-verify skips the repo's pre-push checks", "Fix what the check reports.")
    if "--force" in longs or "f" in letters:
        block("force-push without a lease can overwrite other people's commits",
              "Use --force-with-lease on your own branch, or push a new branch.")
    if "--mirror" in longs or "--prune" in longs:
        block("push --mirror/--prune can delete remote branches", "Push named branches instead.")
    if "--all" in longs or "--branches" in longs:
        block("push --all also pushes protected branches such as main", "Push the branch you mean by name.")
    if "--delete" in longs or "d" in letters:
        block("pushing a branch deletion", "Delete remote branches only when the user asks, or let them do it.")
    patterns = protected_patterns(cwd)
    refspecs = [expand(spec, env) for spec in positional[1:]]
    for spec in refspecs:
        if spec.startswith("+"):
            block(f"refspec '{spec}' force-updates the remote", "Drop the leading '+'.")
        if spec.startswith(":"):
            block(f"refspec '{spec}' deletes a remote branch", "Ask the user to delete it.")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        if dst in ("HEAD", "@") or unknown(dst):
            # A name built at run time most likely names the current branch.
            dst = git_output(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
        if dst and is_protected(dst, patterns):
            block(f"direct push to protected branch '{dst}'", "Push a feature branch and open a PR with /tstack:ship.")
    if not refspecs and "--tags" not in longs:
        branch = git_output(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
        if branch and is_protected(branch, patterns):
            block(f"push while on protected branch '{branch}'", "Create a branch (git switch -c <name>) and push that.")


GIT_HOOKS = {
    "applypatch-msg", "pre-applypatch", "post-applypatch", "pre-commit", "pre-merge-commit",
    "prepare-commit-msg", "commit-msg", "post-commit", "pre-rebase", "post-checkout", "post-merge",
    "pre-push", "pre-receive", "update", "proc-receive", "post-receive", "post-update",
    "reference-transaction", "push-to-checkout", "pre-auto-gc", "post-rewrite", "sendemail-validate",
    "fsmonitor-watchman", "post-index-change",
}
CONFIG_READ = {"--get", "--get-all", "--get-regexp", "--list", "-l", "get", "list", "--show-origin", "--show-scope"}
CONFIG_UNSET = {"--unset", "--unset-all", "unset", "--remove-section", "remove-section", "--rename-section", "rename-section"}


def check_config(args, cwd):
    lowered = [a.lower() for a in args]
    for idx, key in enumerate(lowered):
        if key.startswith("tstack."):
            before = set(lowered[:idx])
            if not (before & CONFIG_READ) and (before & CONFIG_UNSET or idx + 1 < len(args)):
                block("tstack settings in git config belong to the user", "Ask the user to change them.")
    if "core.hookspath" not in lowered:
        return
    idx = lowered.index("core.hookspath")
    before = set(lowered[:idx])
    if before & CONFIG_READ:
        return
    if before & CONFIG_UNSET:
        block("unsetting core.hooksPath can switch off the repo's hook manager", "Leave it as the repo configured it.")
    value = args[idx + 1] if idx + 1 < len(args) else None
    if value is None:
        return  # plain read
    if before & {"--global", "--system"}:
        block("a global core.hooksPath changes hooks for every repo", "Set it per repo, or ask the user.")
    top = os.path.realpath(git_output(cwd, "rev-parse", "--show-toplevel") or cwd)
    target = os.path.realpath(os.path.join(top, os.path.expanduser(value))) if value else ""
    inside = bool(value) and not unknown(value) and (target == top or target.startswith(top + os.sep))
    has_hook = inside and os.path.isdir(target) and any(name in GIT_HOOKS for name in os.listdir(target))
    if not has_hook:
        block(f"core.hooksPath '{value}' would switch off the repo's hooks",
              "Point it at a directory inside the repo that already holds hook scripts (pre-commit, pre-push...): write them first.")


def check_git(words, env, cwd):
    globals_, sub, args = split_git(words)
    joined = " ".join(globals_).lower()
    if "core.hookspath" in joined:
        block("overriding core.hooksPath skips the repo's hooks", "Fix what the hook reports instead.")
    cwd = repo_dir(globals_, cwd)
    if sub in HOOK_RUNNING:
        for key, value in env.items():
            if value.lower() in BYPASS_ENV.get(key, set()):
                block(f"{key}={value} disables the repo's git hooks", "Fix what the hook reports.")
            if key == "SKIP" and value:
                block("SKIP=... skips pre-commit hooks", "Fix what the hook reports.")

    if sub == "commit":
        letters, longs, _ = parse_opts(args, short_value="mFCct", long_value=(
            "--message", "--file", "--reuse-message", "--reedit-message", "--template", "--author",
            "--date", "--fixup", "--squash", "--cleanup", "--trailer", "--pathspec-from-file"))
        if "--no-verify" in longs or "n" in letters:
            block("git commit --no-verify skips the repo's hooks", "Fix what the hook reports instead of skipping it.")
    elif sub in {"merge", "rebase", "am", "cherry-pick", "revert"}:
        _, longs, _ = parse_opts(args, short_value="msXS", long_value=("--message", "--strategy", "--strategy-option", "--onto", "--exec", "--file"))
        if "--no-verify" in longs:
            block(f"git {sub} --no-verify skips the repo's hooks", "Fix what the hook reports instead of skipping it.")
    elif sub == "push":
        check_push(args, cwd, env)
    elif sub == "reset":
        _, longs, _ = parse_opts(args, long_value=("--pathspec-from-file",))
        if "--hard" in longs:
            block("git reset --hard discards uncommitted work",
                  "Use git stash push -u -m '<why>', git restore <paths>, or git revert <sha>.")
    elif sub == "clean":
        letters, longs, _ = parse_opts(args, short_value="e", long_value=("--exclude",))
        dry = "n" in letters or "--dry-run" in longs
        if not dry and ("f" in letters or "--force" in longs):
            block("git clean -f deletes untracked files for good", "Run git clean -n first and delete named paths.")
    elif sub == "branch":
        letters, longs, _ = parse_opts(args, short_value="u", long_value=(
            "--set-upstream-to", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at", "--format", "--sort"))
        force = "f" in letters or "--force" in longs
        delete = "d" in letters or "--delete" in longs
        if "D" in letters or (delete and force):
            block("force-deleting a branch can lose unmerged commits", "Use git branch -d (refuses unmerged work).")
    elif sub == "checkout":
        letters, longs, positional = parse_opts(args, short_value="bB", long_value=("--orphan",))
        if "--force" in longs or "f" in letters:
            block("git checkout --force discards local changes", "Commit or stash first.")
        if any(p in {".", ":/", "*", ":/*", "./"} for p in positional):
            block("git checkout . discards every uncommitted change", "Restore named files, or stash.")
    elif sub == "switch":
        letters, longs, _ = parse_opts(args, short_value="cC", long_value=("--create", "--force-create", "--orphan"))
        if "--discard-changes" in longs or "--force" in longs or "f" in letters:
            block("git switch --discard-changes throws away local changes", "Commit or stash first.")
    elif sub == "restore":
        letters, longs, positional = parse_opts(args, short_value="s", long_value=("--source", "--pathspec-from-file"))
        staged_only = ("--staged" in longs or "S" in letters) and not ("--worktree" in longs or "W" in letters)
        if not staged_only and any(p in {".", ":/", "*", ":/*", "./"} for p in positional):
            block("git restore . discards every uncommitted change", "Restore named files, or stash.")
    elif sub == "stash":
        action = next((a for a in args if not a.startswith("-")), "")
        if action in {"drop", "clear"}:
            block(f"git stash {action} deletes stashed work", "Leave the stash; the user can drop it.")
    elif sub == "rm":
        letters, longs, positional = parse_opts(args, long_value=("--pathspec-from-file",))
        force = "f" in letters or "--force" in longs
        if force and "--cached" not in longs and any(p in {".", ":/", "*", ":/*", "./"} for p in positional):
            block("git rm -f . deletes every tracked file and any uncommitted change",
                  "Remove named paths, or use git rm -r --cached to untrack.")
    elif sub == "worktree":
        if args and args[0] == "remove":
            letters, longs, _ = parse_opts(args[1:])
            if "f" in letters or "--force" in longs:
                block("git worktree remove --force deletes uncommitted work in that worktree", "Commit or stash there first.")
    elif sub == "config":
        check_config(args, cwd)
    elif sub in {"filter-branch", "filter-repo"}:
        block(f"git {sub} rewrites history", "Ask the user; history rewrites need a human decision.")
    elif sub == "update-ref":
        letters, longs, _ = parse_opts(args, short_value="m")
        if "d" in letters or "--delete" in longs:
            block("deleting a ref directly", "Use git branch -d.")
    elif sub == "reflog" and args and args[0] in {"expire", "delete"}:
        block("expiring the reflog removes the recovery path", "Leave the reflog alone.")
    elif sub == "gc" and any(a.startswith("--prune=now") or a == "--prune=all" for a in args):
        block("git gc --prune=now removes the recovery path", "Run git gc without --prune=now.")


CATASTROPHIC = {"/", "~", "$HOME", "${HOME}", ".", "..", "*", ".*", ".git"}


def is_catastrophic(target):
    t = target
    for suffix in ("/*", "/.*"):
        if t.endswith(suffix):
            t = t[: -len(suffix)] or "/"
    if len(t) > 1:
        t = t.rstrip("/") or "/"
    if t.startswith("./") and len(t) > 2:
        t = t[2:]
    return t in CATASTROPHIC or t == os.path.expanduser("~").rstrip("/")


def check_rm(words):
    letters, longs, targets = parse_opts(words[1:])
    if not ("r" in letters or "R" in letters or "--recursive" in longs):
        return
    for t in targets:
        if SUB not in t and is_catastrophic(t):
            block(f"rm -r {t} would delete far more than intended", "Delete named paths inside the project.")


def check(words, session_env, cwd):
    unwrapped = unwrap(words)
    if unwrapped is None:
        return
    env, rest = unwrapped
    if not rest:
        return
    name = os.path.basename(rest[0])
    if name in SHELLS:
        letters, _, positional = parse_opts(rest[1:], short_value="oO")
        if "c" in letters and positional:
            for inner, _ in parse_commands(positional[0], 1):
                check(inner, session_env, cwd)
        return
    if name == "eval":
        for inner, _ in parse_commands(" ".join(rest[1:]), 1):
            check(inner, session_env, cwd)
        return
    if name == "git":
        check_git(rest, {**session_env, **env}, cwd)
    elif name == "rm":
        check_rm(rest)


def session_assignments(commands):
    """Variables set for the rest of the command by `export X=..` or `X=..`."""
    env = {}
    for words, _ in commands:
        if not words:
            continue
        if words[0] in {"export", "declare", "typeset"}:
            candidates = words[1:]
        elif all(ASSIGNMENT.match(w) for w in words):
            candidates = words
        else:
            continue
        for w in candidates:
            if ASSIGNMENT.match(w):
                key, _, value = w.partition("=")
                env[key] = value
    return env


def main():
    if os.environ.get("TSTACK_GIT_GUARD", "").lower() == "off":
        return 0
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "git" not in command and "rm" not in command:
        return 0
    cwd = payload.get("cwd") or os.getcwd()
    try:
        commands = parse_commands(command)
        session_env = session_assignments(commands)
        for words, substituted in commands:
            try:
                check(words, session_env, cwd)
            except Blocked as exc:
                if substituted:
                    raise Blocked(f"{exc} Note: that command sits inside backticks or $(...), which the shell "
                                  "runs. For literal text use single quotes, or write it to a file "
                                  "(for example gh pr create --body-file).") from None
                raise
    except Blocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:  # a parser bug must never break the user's shell
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
