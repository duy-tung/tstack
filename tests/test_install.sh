#!/usr/bin/env bash
# End-to-end test of install.sh with the real `claude` CLI, inside a throwaway
# HOME under a temp directory. Your real ~/.claude is never read or written.
#
#   bash tests/test_install.sh
set -u
P="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT
pass=0 fail=0
ok() { echo "ok   $*"; pass=$((pass + 1)); }
bad() { echo "FAIL $*"; fail=$((fail + 1)); }
fresh() {
  rm -rf "$ROOT/home"
  mkdir -p "$ROOT/home/.claude" "$ROOT/home/tmp"
  export HOME="$ROOT/home" CLAUDE_CONFIG_DIR="$ROOT/home/.claude" TMPDIR="$ROOT/home/tmp"
  C="$CLAUDE_CONFIG_DIR"
}
inst() { (cd "$ROOT" && "$P/install.sh" "$@") > "$ROOT/last.log" 2>&1; }
check() { python3 -c "import json,sys; d=json.load(open('$C/settings.json')); sys.exit(0 if ($1) else 1)"; }

if ! command -v claude >/dev/null 2>&1; then
  echo "claude CLI not found: this test drives the real plugin commands." >&2
  exit 1
fi

# 1. Existing files with their own formatting survive a round trip.
fresh
printf '{\n  "model": "opus",\n  "env": {},\n  "permissions": {"deny": ["WebFetch"]}\n}\n' > "$C/settings.json"
printf '# Mine\n\n- be brief' > "$C/CLAUDE.md"
cp "$C/settings.json" "$ROOT/s0"; cp "$C/CLAUDE.md" "$ROOT/c0"
inst && ok "1 install" || { bad "1 install"; cat "$ROOT/last.log"; }
inst && ok "1 re-run" || bad "1 re-run"
[ "$(grep -c 'tstack:begin' "$C/CLAUDE.md")" = 1 ] && ok "1 one CLAUDE.md block" || bad "1 CLAUDE.md block"
check "d['enabledPlugins']['tstack@tstack'] and d['autoMemoryEnabled'] is False and 'EnterPlanMode' in d['permissions']['deny'] and 'statusLine' in d" \
  && ok "1 settings merged" || bad "1 settings merged"
inst --uninstall && ok "1 uninstall" || bad "1 uninstall"
cmp -s "$ROOT/s0" "$C/settings.json" && ok "1 settings.json byte-identical" || bad "1 settings.json differs"
cmp -s "$ROOT/c0" "$C/CLAUDE.md" && ok "1 CLAUDE.md byte-identical" || bad "1 CLAUDE.md differs"
[ ! -d "$C/tstack" ] && ok "1 state folder removed" || bad "1 state folder left"

# 2. Nothing existed before: nothing is left after.
fresh
inst && ok "2 install" || { bad "2 install"; cat "$ROOT/last.log"; }
inst --uninstall && ok "2 uninstall" || bad "2 uninstall"
[ ! -e "$C/settings.json" ] && ok "2 no settings.json" || bad "2 settings.json left"
[ ! -e "$C/CLAUDE.md" ] && ok "2 no CLAUDE.md" || bad "2 CLAUDE.md left"

# 3. Edits made after install are respected by re-runs and by uninstall.
fresh
printf '{\n  "model": "opus"\n}\n' > "$C/settings.json"
inst || bad "3 install"
python3 - <<'PY'
import json, os
p = os.environ["CLAUDE_CONFIG_DIR"] + "/settings.json"
d = json.load(open(p))
d["permissions"]["allow"] = ["Bash(pnpm test *)"]
d["permissions"]["deny"].remove("EnterPlanMode")
d["effortLevel"] = "high"
json.dump(d, open(p, "w"), indent=2)
PY
inst || bad "3 re-run"
check "'EnterPlanMode' not in d['permissions']['deny']" && ok "3 a removed item is not re-added" || bad "3 removed item came back"
inst --uninstall || bad "3 uninstall"
check "d['permissions'] == {'allow': ['Bash(pnpm test *)']} and d['effortLevel'] == 'high' and 'autoMemoryEnabled' not in d and 'statusLine' not in d" \
  && ok "3 user edits kept, tstack entries gone" || bad "3 uninstall result"

# 4. Invalid settings.json stops the install before any change.
fresh
printf '{\n  "model": "opus", // comment\n}\n' > "$C/settings.json"
cp "$C/settings.json" "$ROOT/s0"
inst; [ $? != 0 ] && ok "4 install refuses" || bad "4 install should fail"
cmp -s "$ROOT/s0" "$C/settings.json" && [ ! -e "$C/CLAUDE.md" ] && ok "4 nothing changed" || bad "4 something changed"
grep -q "not valid JSON (line 2" "$ROOT/last.log" && ok "4 message names the line" || bad "4 message"

# 5. --dry-run changes nothing.
fresh
printf '{"model":"opus"}\n' > "$C/settings.json"
snap() { (cd "$C" && find . -maxdepth 2 \( -name 'settings.json*' -o -name 'CLAUDE.md*' -o -path './tstack*' -o -path './plugins*' \) | sort | xargs cksum 2>/dev/null); }
before="$(snap)"
inst --dry-run && ok "5 dry-run exits 0" || bad "5 dry-run"
[ "$before" = "$(snap)" ] && ok "5 dry-run changed nothing" || bad "5 dry-run changed files"

# 6. --no-statusline sets no status line and leaks no temp file.
fresh
inst --no-statusline || bad "6 install"
check "'statusLine' not in d" && ok "6 no statusLine" || bad "6 statusLine set"
[ -z "$(ls "$TMPDIR" | grep '^tmp\.')" ] && ok "6 no temp file left" || bad "6 temp file left"
inst --uninstall

# 7. Deleting settings.json and re-running applies the settings again.
fresh
inst || bad "7 install"
rm -f "$C/settings.json"
inst || bad "7 re-run"
check "d.get('autoMemoryEnabled') is False and 'EnterPlanMode' in d['permissions']['deny']" \
  && ok "7 settings re-applied after the file was deleted" || bad "7 settings not re-applied"
inst --uninstall

# 8. A symlinked path is the same folder; a moved folder is re-pointed.
fresh
ln -s "$P" "$ROOT/link"
inst || bad "8 install"
(cd "$ROOT" && "$ROOT/link/install.sh") > "$ROOT/last.log" 2>&1 || bad "8 re-run via symlink"
grep -q "pointing it here instead" "$ROOT/last.log" && bad "8 symlink treated as a move" || ok "8 symlink is the same folder"
mkdir -p "$ROOT/moved" && cp -R "$P" "$ROOT/moved/tstack"
(cd "$ROOT" && "$ROOT/moved/tstack/install.sh") > "$ROOT/last.log" 2>&1 || bad "8 install from moved folder"
grep -q "pointing it here instead" "$ROOT/last.log" && ok "8 moved folder re-pointed" || bad "8 moved folder not re-pointed"
claude plugin list 2>/dev/null | grep -q "tstack@tstack" && ok "8 plugin still installed" || bad "8 plugin missing"
(cd "$ROOT" && "$ROOT/moved/tstack/install.sh" --uninstall) > /dev/null 2>&1
rm -f "$ROOT/link"

echo
echo "passed $pass, failed $fail"
[ "$fail" = 0 ]
