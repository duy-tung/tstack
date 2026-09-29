#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit), installed by /tstack:setup.
# Formats and lint-fixes the one file Claude just edited with tools this repo
# already uses. Missing tools, configs or input are skipped. Always exits 0.

root=${CLAUDE_PROJECT_DIR:-$PWD}
root=${root%/}
command -v python3 >/dev/null 2>&1 || exit 0
file=$(python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))
except Exception:
    pass
' 2>/dev/null)
case $file in "$root"/*) ;; *) exit 0 ;; esac
[ -f "$file" ] || exit 0

# up NAME...: print the nearest NAME, searching from the file's folder up to the repo root.
up() {
  local dir=${file%/*} name
  while :; do
    for name in "$@"; do
      if [ -e "$dir/$name" ]; then printf '%s\n' "$dir/$name"; return 0; fi
    done
    if [ "$dir" = "$root" ] || [ -z "$dir" ]; then return 1; fi
    dir=${dir%/*}
  done
}
quiet() { "$@" >/dev/null 2>&1; }

case $file in
  *.py | *.pyi)
    if up ruff.toml .ruff.toml >/dev/null || grep -qs '^\[tool\.ruff' "$root/pyproject.toml" "$(up pyproject.toml)"; then
      ruff=$(up .venv/bin/ruff) || ruff=$(command -v ruff) || exit 0
      quiet "$ruff" check --fix "$file"
      quiet "$ruff" format "$file"
    fi
    ;;
  *.swift)
    if up .swiftformat >/dev/null && command -v swiftformat >/dev/null; then quiet swiftformat "$file"; fi
    ;;
  *.kt | *.kts)
    if command -v ktlint >/dev/null && grep -qs ktlint "$root/.editorconfig" "$root/build.gradle.kts" "$root/build.gradle" "$root/gradle/libs.versions.toml"; then
      quiet ktlint -F "$file"
    fi
    ;;
  *.dart)
    if up pubspec.yaml >/dev/null && command -v dart >/dev/null; then quiet dart format "$file"; fi
    ;;
  *)
    case $file in
      *.js | *.jsx | *.mjs | *.cjs | *.ts | *.tsx | *.mts | *.cts | *.vue | *.svelte)
        if eslint=$(up node_modules/.bin/eslint); then quiet "$eslint" --fix "$file"; fi
        ;;
    esac
    if biome=$(up node_modules/.bin/biome) && up biome.json biome.jsonc >/dev/null; then
      quiet "$biome" check --write "$file"
    elif prettier=$(up node_modules/.bin/prettier) && {
      up .prettierrc .prettierrc.json .prettierrc.json5 .prettierrc.yaml .prettierrc.yml .prettierrc.toml \
        .prettierrc.js .prettierrc.cjs .prettierrc.mjs .prettierrc.ts \
        prettier.config.js prettier.config.cjs prettier.config.mjs prettier.config.ts >/dev/null ||
        grep -qs '"prettier"' "$root/package.json" "$(up package.json)"
    }; then
      quiet "$prettier" --write --ignore-unknown "$file"
    fi
    ;;
esac
exit 0
