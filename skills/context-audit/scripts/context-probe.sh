#!/usr/bin/env bash
# Measure a fresh session's always-on context with `claude -p "/context"`.
# Run from the repo root so project instruction files and settings load.
#   context-probe.sh save <name>             snapshot the current setup (before, after)
#   context-probe.sh try '<settings json>'   price a settings change against "before"
#   context-probe.sh diff <from> <to>        compare two snapshots
# Snapshots live in ${TMPDIR:-/tmp}/tstack-context-audit/<name>.md.
set -euo pipefail
dir="${TMPDIR:-/tmp}/tstack-context-audit"
mkdir -p "$dir"

compare() {
  python3 - "$@" <<'PY'
import re, sys

def num(s):
    s = s.strip().replace(",", "")
    mult = {"k": 1_000, "M": 1_000_000}.get(s[-1:], 1)
    return round(float(s.rstrip("kM")) * mult)

def fmt(n):
    return f"{n / 1000:.1f}k" if abs(n) >= 1000 else str(n)

def load(path):
    text = open(path).read()
    total = re.search(r"\*\*Tokens:\*\*\s*([\d.,]+[kM]?)", text)
    table = re.search(r"### Estimated usage by category\n(.*?)(?:\n###|\Z)", text, re.S)
    if not total or not table:
        sys.exit(f"Could not parse {path}; read it directly.")
    rows = {"Total": num(total.group(1))}
    for line in table.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Category", "Free space", "Autocompact buffer"):
            continue
        if re.fullmatch(r"[\d.,]+[kM]?", cells[1]):
            rows[cells[0]] = num(cells[1])
    return rows

if len(sys.argv) == 2:
    print("| Category | Tokens |\n|---|---|")
    for name, n in load(sys.argv[1]).items():
        print(f"| {name} | {fmt(n)} |")
    sys.exit()

before, after, changed_only = load(sys.argv[1]), load(sys.argv[2]), sys.argv[3] == "1"
print("| Category | Before | After | Change |\n|---|---|---|---|")
for name in list(before) + [k for k in after if k not in before]:
    a, b = before.get(name, 0), after.get(name, 0)
    if changed_only and a == b and name != "Total":
        continue
    print(f"| {name} | {fmt(a)} | {fmt(b)} | {'+' if b > a else ''}{fmt(b - a)} |")
PY
}

case "${1:-}" in
  save)
    [ -n "${2:-}" ] || { echo "usage: $0 save <name>" >&2; exit 2; }
    claude -p "/context" > "$dir/$2.md"
    compare "$dir/$2.md"
    echo "Full breakdown (MCP tools, memory files, skills): $dir/$2.md"
    ;;
  try)
    [ -n "${2:-}" ] && [ -f "$dir/before.md" ] || { echo "usage: $0 try '<settings json>' (after: $0 save before)" >&2; exit 2; }
    claude -p "/context" --settings "$2" > "$dir/try.md"
    compare "$dir/before.md" "$dir/try.md" 1
    ;;
  diff)
    [ -f "$dir/${2:-}.md" ] && [ -f "$dir/${3:-}.md" ] || { echo "usage: $0 diff <from> <to>" >&2; exit 2; }
    compare "$dir/$2.md" "$dir/$3.md" 0
    ;;
  *)
    sed -n '2,7p' "$0" >&2
    exit 2
    ;;
esac
