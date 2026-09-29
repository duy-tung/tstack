#!/usr/bin/env python3
"""Add or remove the tstack block in ~/.claude/CLAUDE.md.

The block sits between <!-- tstack:begin --> and <!-- tstack:end -->. Text
outside it is never touched. The first `add` records the file as it was, so
`remove` restores it byte for byte when nothing else changed since.

Usage:
  claude_md.py add --target T --template P --state S [--dry-run]
  claude_md.py remove --target T --state S [--dry-run]
"""

import argparse
import json
import os
import re
import sys

BEGIN, END = "<!-- tstack:begin -->", "<!-- tstack:end -->"
BLOCK = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"(?:\r?\n)?", re.S)
BLOCK_WITH_GAP = re.compile(r"(?:\r?\n)*" + BLOCK.pattern, re.S)


def read(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def load_state(path):
    raw = read(path)
    return json.loads(raw) if raw else {}


def strip_block(text):
    return BLOCK_WITH_GAP.sub("\n", text)


def add(args):
    text = read(args.target)
    current = text or ""
    nl = "\r\n" if "\r\n" in current else "\n"
    with open(args.template, encoding="utf-8") as fh:
        body = fh.read().strip().replace("\n", nl)
    block = f"{BEGIN}{nl}{body}{nl}{END}{nl}"
    if BLOCK.search(current):
        new = BLOCK.sub(lambda m: block, current, count=1)
        action = "updated the tstack block" if new != current else "tstack block already current"
    else:
        new = (current.rstrip() + nl + nl if current.strip() else "") + block
        action = "added the tstack block"
    print(f"  {action} in {args.target}")
    if args.dry_run or new == current:
        return 0
    state = load_state(args.state)
    if "original" not in state:
        state["original"] = text
        write(args.state, json.dumps(state))
    write(args.target, new)
    return 0


def remove(args):
    text = read(args.target)
    state = load_state(args.state)
    if text is None or not BLOCK.search(text):
        print("  no tstack block found")
        if not args.dry_run and os.path.exists(args.state):
            os.remove(args.state)
        return 0
    print(f"  removed the tstack block from {args.target}")
    if args.dry_run:
        return 0
    stripped = strip_block(text)
    has_original = "original" in state
    original = state.get("original")
    if has_original and stripped.rstrip() == (original or "").rstrip():
        if original is None:
            os.remove(args.target)
        else:
            write(args.target, original)
        print("  restored the original file byte for byte")
    else:
        nl = "\r\n" if "\r\n" in text else "\n"
        stripped = stripped.rstrip("\r\n")
        if stripped:
            write(args.target, stripped + nl)
        else:
            os.remove(args.target)
    if os.path.exists(args.state):
        os.remove(args.state)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["add", "remove"])
    ap.add_argument("--target", required=True)
    ap.add_argument("--template")
    ap.add_argument("--state", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return add(args) if args.mode == "add" else remove(args)


if __name__ == "__main__":
    sys.exit(main())
