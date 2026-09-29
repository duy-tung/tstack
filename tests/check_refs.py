#!/usr/bin/env python3
"""Check that the plugin's cross-references resolve.

- Every `tstack:<name>` names a skill or an agent.
- Every `/tstack:<name>` names a skill.
- `Call the Skill tool with "tstack:<name>"` only targets model-invoked skills
  (a skill with disable-model-invocation cannot be called that way).
- Relative markdown links and ${CLAUDE_SKILL_DIR}/... paths exist.
Fenced code blocks are skipped: they hold examples, not references.

Run: python3 tests/check_refs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def without_fences(text):
    return re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)


def main():
    skills = {}
    for folder in sorted((ROOT / "skills").iterdir()):
        skill_md = folder / "SKILL.md"
        if skill_md.exists():
            front = skill_md.read_text(encoding="utf-8").split("---", 2)[1]
            skills[folder.name] = "user" if "disable-model-invocation: true" in front else "model"
    agents = {p.stem for p in (ROOT / "agents").glob("*.md")}
    problems = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        text = without_fences(path.read_text(encoding="utf-8"))
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
        for name in re.findall(r"tstack:([a-z0-9-]+)", text):
            if name not in skills and name not in agents:
                problems.append(f"{rel}: unknown tstack:{name}")
        for name in re.findall(r"/tstack:([a-z0-9-]+)", text):
            if name not in skills:
                problems.append(f"{rel}: /tstack:{name} is not a skill")
        for name in re.findall(r'(?:Call the Skill tool with|then) "tstack:([a-z0-9-]+)"', text):
            if skills.get(name) != "model":
                problems.append(f"{rel}: Skill-tool call to tstack:{name}, which only the user can invoke")
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
            if re.match(r"^[a-z]+://", target) or target.startswith("mailto:"):
                continue
            if not (path.parent / target).resolve().exists():
                problems.append(f"{rel}: broken link {target}")
        if rel.parts[0] == "skills":
            skill_dir = ROOT / "skills" / rel.parts[1]
            for sub in re.findall(r"\$\{CLAUDE_SKILL_DIR\}(/[A-Za-z0-9_./<>*-]*)", text):
                sub = sub.rstrip(".,;:")
                if "<" in sub or "*" in sub:
                    continue  # a pattern such as scripts/<file>, not a path
                if not Path(str(skill_dir) + sub).resolve().exists():
                    problems.append(f"{rel}: missing ${{CLAUDE_SKILL_DIR}}{sub}")
    user = sum(1 for kind in skills.values() if kind == "user")
    print(f"{len(skills)} skills ({user} user-invoked, {len(skills) - user} model-invoked), {len(agents)} agents")
    for problem in sorted(set(problems)):
        print("FAIL", problem)
    print("all references resolve" if not problems else f"{len(set(problems))} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
