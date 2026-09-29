# Stack hooks

Say this once, before proposing: a mistake the agent repeats becomes a type, a lint rule or a hook before it becomes prose.

Destructive git commands and hook bypasses such as `--no-verify` are already blocked by the tstack plugin's own hook. Do not add a per-repo copy.

## 1. Allow the check commands

Take the commands from the repo, never from memory: manifest scripts, `Makefile` or `justfile` targets, the CI workflow. Write one rule per invocation the repo documents: the exact command, or the command plus ` *` when it takes arguments.

| Stack | Example rules |
|---|---|
| JS/TS (pnpm shown) | `Bash(pnpm typecheck)`, `Bash(pnpm lint *)`, `Bash(pnpm test *)`, `Bash(pnpm format *)` |
| Python (uv shown) | `Bash(uv run pyright *)`, `Bash(uv run ruff check *)`, `Bash(uv run ruff format *)`, `Bash(uv run pytest *)` |
| iOS | `Bash(swiftlint lint *)`, `Bash(make test)` |
| Android | `Bash(./gradlew ktlintCheck *)`, `Bash(./gradlew detekt *)`, `Bash(./gradlew testDebugUnitTest *)` |
| Flutter | `Bash(dart format *)`, `Bash(flutter analyze *)`, `Bash(flutter test *)` |

- Never allow a bare runner prefix such as `Bash(npm run *)`, `Bash(npx *)`, `Bash(python *)` or `Bash(./gradlew *)`: it covers arbitrary code.
- When a check is a long command line (an `xcodebuild` with scheme and destination), wrap it in a make target or script first and allow that.
- Project allow rules apply only in a trusted workspace (the user accepted the trust dialog there once). Headless runs in a fresh clone ignore them.

## 2. Format-on-edit hook

Copy [scripts/format-edited-file.sh](scripts/format-edited-file.sh) unchanged to `.claude/hooks/format-edited-file.sh` and `chmod +x` it. It reads `tool_input.file_path` from the hook's stdin JSON and runs, on that one file, only what this repo already uses:

| File | Runs | Only when |
|---|---|---|
| `.py`, `.pyi` | `ruff check --fix`, then `ruff format` | a ruff config exists (`ruff.toml`, `.ruff.toml`, `[tool.ruff]`); `.venv/bin/ruff` is preferred over `PATH` |
| JS/TS, Vue, Svelte | `eslint --fix` | eslint is installed in `node_modules` |
| JS/TS after eslint, and any type no other row names | `biome check --write`, else `prettier --write --ignore-unknown` | biome is installed with a `biome.json`; prettier is installed with a config or a `"prettier"` entry in `package.json` |
| `.swift` | `swiftformat` | a `.swiftformat` config exists |
| `.kt`, `.kts` | `ktlint -F` | `.editorconfig` or the root Gradle files mention ktlint |
| `.dart` | `dart format` | a `pubspec.yaml` exists |

It exits 0 in every case (no python3, tool, config or file), so it never blocks. Claude Code re-syncs a file a hook reformatted, so the next Edit does not fail on a stale read. Skip the hook when an existing PostToolUse hook already formats edited files.

Prove it bites: write a badly formatted scratch file with the repo's main extension, run the script on it, show the result, delete the file.

```bash
printf '{"tool_input":{"file_path":"%s"}}' "$PWD/<scratch file>" | CLAUDE_PROJECT_DIR="$PWD" bash .claude/hooks/format-edited-file.sh
```

## 3. Pre-commit gate

Recommend it when the repo has no pre-commit hook and no CI job running its checks. Run each check on the current tree before wiring it: a gate that is red on a clean tree blocks every commit, so leave a red check out and tell the user. Keep the gate under about a minute; slower suites go to pre-push or CI.

### JS/TS: husky + lint-staged

1. Detect the package manager from the lockfile: `pnpm-lock.yaml` pnpm, `yarn.lock` yarn, `bun.lock` or `bun.lockb` bun, else npm.
2. Install `husky` and `lint-staged` as devDependencies. Add `prettier` only when the repo has no formatter, and then also write `.prettierrc`:
   ```json
   {"useTabs": false, "tabWidth": 2, "printWidth": 80, "singleQuote": false, "trailingComma": "es5", "semi": true, "arrowParens": "always"}
   ```
3. Run `npx husky init`. It creates `.husky/` and the `"prepare": "husky"` script.
4. Write `.husky/pre-commit` (Husky v9 needs no shebang) with `npm` replaced by the detected package manager, dropping a line whose script does not exist:
   ```
   npx lint-staged
   npm run typecheck
   npm run test
   ```
5. Write `.lintstagedrc` for the formatter the repo uses:

   | Repo uses | `.lintstagedrc` |
   |---|---|
   | prettier | `{"*": "prettier --ignore-unknown --write"}` |
   | prettier and eslint | `{"*.{js,jsx,ts,tsx,mjs,cjs}": ["eslint --fix", "prettier --write"], "*.{json,md,css,scss,yml,yaml}": "prettier --write"}` |
   | biome | `{"*.{js,jsx,ts,tsx,mjs,cjs,json,jsonc}": "biome check --write --no-errors-on-unmatched"}` |

6. Prove it: stage one changed file, run `npx lint-staged`, then `sh .husky/pre-commit`.

### Python: pre-commit framework

Mirror the tools CI already runs: in a black, isort or flake8 repo, use those hooks unless the user asks to switch to ruff. Replace `uv run` with the repo's runner (`poetry run`, or nothing), and use `mypy .` instead of `pyright` when the repo uses mypy. Write `.pre-commit-config.yaml`, run `pre-commit autoupdate` (pins each `rev` to the latest tag) and `pre-commit install`, then prove it with `pre-commit run --files <one changed file>`.

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.11
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: typecheck
        name: typecheck
        entry: uv run pyright
        language: system
        types: [python]
        pass_filenames: false
      - id: tests
        name: tests
        entry: uv run pytest -q
        language: system
        pass_filenames: false
        always_run: true
```

### Mobile: a versioned git hook

Write `.githooks/pre-commit` with the platform's lint and unit test commands, `chmod +x` it, and run `git config core.hooksPath .githooks`. That setting is per clone: tell the user, or add it to the repo's bootstrap script. iOS shown:

```sh
#!/bin/sh
set -e
swiftlint lint --strict
make test
```

| Platform | Lint | Unit tests |
|---|---|---|
| iOS | `swiftlint lint --strict` | the repo's `make test` or `xcodebuild ... test` line |
| Android | `./gradlew ktlintCheck detekt` (tasks the build defines) | `./gradlew testDebugUnitTest` |
| Flutter | `dart format --output=none --set-exit-if-changed . && flutter analyze` | `flutter test` |

Simulator and emulator suites are too slow for pre-commit: put them in `.githooks/pre-push`.

## 4. Module boundaries (opt-in)

Offer; do not recommend by default. On yes:

- TypeScript: call the Skill tool with "tstack:typescript" and follow its BOUNDARIES.md.
- Python: call the Skill tool with "tstack:python" and follow its BOUNDARIES.md.

## Merging `.claude/settings.json`

The file is shared with the team. Create it when absent. Add only missing allow rules, append the hook entry to `hooks.PostToolUse` unless an entry already runs `format-edited-file.sh`, and keep every other key. Validate with `python3 -m json.tool .claude/settings.json`. A new file looks like this:

```json
{
  "permissions": {
    "allow": ["Bash(pnpm typecheck)", "Bash(pnpm lint *)", "Bash(pnpm test *)"]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/format-edited-file.sh\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```
