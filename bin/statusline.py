#!/usr/bin/env python3
"""tstack status line for Claude Code.

Shows the context window in use with a smart-zone color, the model, and the
effort level. Claude Code pipes a JSON payload on stdin; this prints one line.

Colors: green below two thirds of the smart-zone edge (100k by default),
yellow up to the edge, red past it. Override the edge with TSTACK_SMART_ZONE
(tokens, default 150000; "200k" and "1m" also work).
"""

import json
import math
import os
import sys

GREEN, YELLOW, RED, DIM, BOLD, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


def human(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def smart_zone_edge(default=150_000):
    raw = os.environ.get("TSTACK_SMART_ZONE", "").strip().lower().replace("_", "").replace(",", "")
    if not raw:
        return default
    scale = {"k": 1_000, "m": 1_000_000}.get(raw[-1], 1)
    try:
        value = float(raw[:-1] if scale > 1 else raw) * scale
    except ValueError:
        return default
    if not math.isfinite(value) or value <= 0:
        return default
    return int(value)


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        print("tstack: no status")
        return 0

    edge = smart_zone_edge()
    window = data.get("context_window") or {}
    used = window.get("total_input_tokens") or 0
    size = window.get("context_window_size") or 0
    pct = window.get("used_percentage")
    if pct is None and size:
        pct = round(used * 100 / size)

    if used < edge * 2 // 3:
        color, zone = GREEN, ""
    elif used < edge:
        color, zone = YELLOW, " near edge"
    else:
        color, zone = RED, " dumb zone: clear, hand off or compact at the next boundary"

    parts = [f"{color}{BOLD}{human(used)}{RESET}{color}{zone}{RESET}"]
    if pct is not None:
        parts[0] += f" {DIM}({pct}%){RESET}"

    model = (data.get("model") or {}).get("display_name")
    if model:
        parts.append(model)
    effort = (data.get("effort") or {}).get("level")
    if effort:
        parts.append(f"effort {effort}")
    cwd = (data.get("workspace") or {}).get("current_dir")
    if cwd:
        parts.append(f"{DIM}{os.path.basename(cwd)}{RESET}")

    print(f" {DIM}·{RESET} ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
