#!/usr/bin/env bash
# tstack installer for Claude Code. Safe to re-run: it updates in place and
# never removes anything unless you pass --uninstall.
#
#   ./install.sh                 install or update everything
#   ./install.sh --dry-run       show what would change, change nothing
#   ./install.sh --uninstall     remove exactly what tstack added
#   --no-plugin --no-settings --no-claude-md --no-statusline   skip a part
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
STATE_DIR="$CLAUDE_HOME/tstack"
SETTINGS="$CLAUDE_HOME/settings.json"
SETTINGS_STATE="$STATE_DIR/installed-settings.json"
CLAUDEMD_STATE="$STATE_DIR/installed-claude-md.json"
DRY=0 UNINSTALL=0 DO_PLUGIN=1 DO_SETTINGS=1 DO_CLAUDEMD=1 DO_STATUSLINE=1

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --no-plugin) DO_PLUGIN=0 ;;
    --no-settings) DO_SETTINGS=0 ;;
    --no-claude-md) DO_CLAUDEMD=0 ;;
    --no-statusline) DO_STATUSLINE=0 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 1 ;;
  esac
done

say() { printf '\n==> %s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then echo "  would run: $*"; else "$@"; fi; }
has_claude() { command -v claude >/dev/null 2>&1; }

TMP_TEMPLATE=""
cleanup() { if [ -n "$TMP_TEMPLATE" ]; then rm -f "$TMP_TEMPLATE"; fi; }
trap cleanup EXIT

dry_flag=()
[ "$DRY" = 1 ] && dry_flag=(--dry-run)

# macOS ships a python3 stub that only offers to install the Command Line
# Tools, so run it instead of trusting `command -v`.
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
  echo "tstack needs python3 3.8 or newer: its hooks, status line and this installer use it." >&2
  echo "On macOS: xcode-select --install" >&2
  exit 1
fi

plugin_installed() {
  has_claude || return 1
  local out
  out="$(claude plugin list --json 2>/dev/null || true)"
  if printf '%s' "$out" | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1; then
    printf '%s' "$out" | python3 -c 'import json,sys; sys.exit(0 if any(isinstance(p, dict) and p.get("id") == "tstack@tstack" for p in json.load(sys.stdin)) else 1)'
  else
    claude plugin list 2>/dev/null | grep -Eq '^[[:space:]]*(>|❯)?[[:space:]]*tstack@tstack[[:space:]]*$'
  fi
}

# Prints where the tstack marketplace points, or nothing when it is not added.
marketplace_path() {
  has_claude || return 0
  claude plugin marketplace list --json 2>/dev/null | python3 -c '
import json, sys
try:
    items = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for m in items if isinstance(items, list) else []:
    if isinstance(m, dict) and m.get("name") == "tstack":
        print(m.get("path") or m.get("installLocation") or "unknown")
' 2>/dev/null || true
}

STATUSLINE_CMD="python3 \"$STATE_DIR/statusline.py\""

if [ "$UNINSTALL" = 1 ]; then
  if [ "$DO_PLUGIN" = 1 ] && has_claude; then
    say "Plugin"
    if plugin_installed; then run claude plugin uninstall tstack@tstack; else echo "  not installed"; fi
    if [ -n "$(marketplace_path)" ]; then run claude plugin marketplace remove tstack; fi
  fi
  if [ "$DO_SETTINGS" = 1 ]; then
    say "Settings ($SETTINGS)"
    python3 "$PLUGIN_DIR/bin/merge_settings.py" --uninstall --target "$SETTINGS" --state "$SETTINGS_STATE" \
      ${dry_flag[@]+"${dry_flag[@]}"} || echo "  left settings.json as it is: remove the tstack entries by hand"
  fi
  if [ "$DO_CLAUDEMD" = 1 ]; then
    say "Global CLAUDE.md"
    python3 "$PLUGIN_DIR/bin/claude_md.py" remove --target "$CLAUDE_HOME/CLAUDE.md" --state "$CLAUDEMD_STATE" \
      ${dry_flag[@]+"${dry_flag[@]}"} || echo "  left CLAUDE.md as it is"
  fi
  if [ "$DO_STATUSLINE" = 1 ] && [ -f "$STATE_DIR/statusline.py" ]; then
    say "Status line"
    run rm -f "$STATE_DIR/statusline.py"
  fi
  [ "$DRY" = 1 ] || rmdir "$STATE_DIR" 2>/dev/null || true
  say "Done. Restart Claude Code to apply. Backups named *.tstack-backup-* stay next to the files they protect."
  exit 0
fi

# Preflight: stop before changing anything if settings.json cannot be merged.
if [ "$DO_SETTINGS" = 1 ]; then
  python3 "$PLUGIN_DIR/bin/merge_settings.py" --check --target "$SETTINGS" || exit 1
  # Record settings.json as it is now, before the plugin CLI edits it, so that
  # --uninstall can restore it exactly.
  [ "$DRY" = 1 ] || python3 "$PLUGIN_DIR/bin/merge_settings.py" --snapshot --target "$SETTINGS" --state "$SETTINGS_STATE"
fi

if [ "$DO_PLUGIN" = 1 ]; then
  say "Plugin"
  if ! has_claude; then
    echo "  claude CLI not found. Install Claude Code, then re-run, or inside a session run:"
    echo "    /plugin marketplace add $PLUGIN_DIR"
    echo "    /plugin install tstack@tstack"
  else
    mp="$(marketplace_path)"
    if [ -n "$mp" ]; then
      mp="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$mp")"
    fi
    if [ -n "$mp" ] && [ "$mp" != "$PLUGIN_DIR" ]; then
      echo "  the tstack marketplace points at $mp; pointing it here instead"
      run claude plugin marketplace remove tstack
      mp=""
    fi
    if [ -z "$mp" ]; then
      run claude plugin marketplace add "$PLUGIN_DIR"
    else
      run claude plugin marketplace update tstack
    fi
    if plugin_installed; then
      run claude plugin update tstack@tstack
    else
      run claude plugin install tstack@tstack
    fi
    echo "  tstack loads in place from $PLUGIN_DIR: keep the folder there. After editing it,"
    echo "  start a new session or run /reload-plugins."
  fi
fi

if [ "$DO_STATUSLINE" = 1 ]; then
  say "Status line"
  run mkdir -p "$STATE_DIR"
  run cp "$PLUGIN_DIR/bin/statusline.py" "$STATE_DIR/statusline.py"
  echo "  $STATE_DIR/statusline.py"
fi

if [ "$DO_SETTINGS" = 1 ]; then
  say "Settings ($SETTINGS)"
  statusline_arg="$STATUSLINE_CMD"
  template="$PLUGIN_DIR/templates/user/settings.json"
  if [ "$DO_STATUSLINE" = 0 ]; then
    statusline_arg=""
    TMP_TEMPLATE="$(mktemp)"
    template="$TMP_TEMPLATE"
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); d.pop("statusLine",None); json.dump(d,open(sys.argv[2],"w"))' \
      "$PLUGIN_DIR/templates/user/settings.json" "$template"
  fi
  python3 "$PLUGIN_DIR/bin/merge_settings.py" --template "$template" --target "$SETTINGS" \
    --state "$SETTINGS_STATE" --statusline "$statusline_arg" ${dry_flag[@]+"${dry_flag[@]}"}
fi

if [ "$DO_CLAUDEMD" = 1 ]; then
  say "Global CLAUDE.md"
  python3 "$PLUGIN_DIR/bin/claude_md.py" add --target "$CLAUDE_HOME/CLAUDE.md" \
    --template "$PLUGIN_DIR/templates/user/CLAUDE.md" --state "$CLAUDEMD_STATE" ${dry_flag[@]+"${dry_flag[@]}"}
fi

say "Done. Restart Claude Code, then in each repo:"
cat <<'EOF'
  /tstack:setup            once per repo (tracker, AGENTS.md, CODING_STANDARDS.md, hooks)
  /tstack:create-verify    once per app (verify skill + feature map)
  /tstack:work ?           which flow fits right now
  /context                 check the always-on context after the restart
EOF
