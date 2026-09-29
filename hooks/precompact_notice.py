#!/usr/bin/env python3
"""tstack PreCompact hook: when auto-compaction fires, remind the user that
the phase boundary went unclaimed. Manual /compact passes silently."""

import json
import sys


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    if payload.get("trigger") != "auto":
        return 0
    message = (
        "tstack: auto-compaction fired, so a phase boundary went unclaimed. "
        "Next time decide at the boundary: continue, /clear, /tstack:handoff, a subagent, "
        "or /compact with an instruction. Long unattended runs keep their state in .tstack/<slug>/."
    )
    print(json.dumps({"systemMessage": message}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
