#!/usr/bin/env python3
"""Merge tstack's recommended user settings into ~/.claude/settings.json.

Rules:
- A key the user already set keeps the user's value (reported as "kept yours").
- Lists are merged as a union, preserving order.
- statusLine is replaced only when absent or when it already points at tstack.
- Something tstack added once and the user later removed is never re-added.
- A timestamped backup is written before any change.
- What tstack added (leaves, list items, and the containers it had to create)
  is recorded in <state>, so --uninstall removes exactly that.
- --snapshot records the file as it was before tstack touched anything
  (including the plugin CLI). When nothing else changed since, --uninstall
  restores that original byte for byte.

Usage:
  merge_settings.py --check --target S
  merge_settings.py --snapshot --target S --state F
  merge_settings.py --template T --target S --state F --statusline CMD [--dry-run]
  merge_settings.py --uninstall --target S --state F [--dry-run]
"""

import argparse
import copy
import json
import os
import shutil
import sys
import time

MARK = "tstack"
MISSING = object()


class BadJSON(Exception):
    pass


def read_raw(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def parse(raw, path="settings"):
    if raw is None or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BadJSON(f"{path} is not valid JSON (line {exc.lineno}, column {exc.colno}: {exc.msg})") from None
    if not isinstance(data, dict):
        raise BadJSON(f"{path} does not hold a JSON object")
    return data


def load_state(path):
    raw = read_raw(path)
    state = parse(raw, path) if raw else {}
    state.setdefault("added", [])
    return state


def is_ours(status_line):
    return isinstance(status_line, dict) and MARK in str(status_line.get("command", ""))


def merge(target, template, path, added, kept, previous, skipped):
    for key, value in template.items():
        here = f"{path}.{key}" if path else key
        if key == "statusLine" and not path:
            record = {"path": here, "value": value}
            if key not in target:
                if any(r.get("path") == here for r in previous):
                    skipped.append(here)  # the user removed it
                    continue
                target[key] = copy.deepcopy(value)
                added.append(record)
            elif is_ours(target[key]):
                if target[key] != value:
                    target[key] = copy.deepcopy(value)
                    added.append(record)
            else:
                kept.append(here)
            continue
        if isinstance(value, (dict, list)):
            empty = {} if isinstance(value, dict) else []
            if key not in target:
                container = {"path": here, "container": True}
                if container in previous:
                    skipped.append(here)  # the user removed the whole container
                    continue
                target[key] = empty
                added.append(container)
            if type(target[key]) is not type(empty):
                kept.append(here)
                continue
            if isinstance(value, dict):
                merge(target[key], value, here, added, kept, previous, skipped)
            else:
                for item in value:
                    record = {"path": here, "item": item}
                    if item in target[key]:
                        continue
                    if record in previous:
                        skipped.append(f"{here} item {item}")  # the user removed it
                        continue
                    target[key].append(copy.deepcopy(item))
                    added.append(record)
            continue
        record = {"path": here, "value": value}
        if key not in target:
            if any(r.get("path") == here and "value" in r for r in previous):
                skipped.append(here)  # the user removed it
                continue
            target[key] = copy.deepcopy(value)
            added.append(record)
        elif target[key] != value:
            kept.append(here)


def node_at(target, path):
    node = target
    for part in path.split(".")[:-1]:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) else None


def remove(target, record):
    if record.get("container"):
        return False
    parent = node_at(target, record["path"])
    leaf = record["path"].split(".")[-1]
    if parent is None or leaf not in parent:
        return False
    if "item" in record:
        if isinstance(parent[leaf], list) and record["item"] in parent[leaf]:
            parent[leaf].remove(record["item"])
            return True
        return False
    if parent[leaf] == record["value"]:
        del parent[leaf]
        return True
    return False


def prune_created(target, records):
    containers = [r["path"] for r in records if r.get("container")]
    for path in sorted(containers, key=lambda p: p.count("."), reverse=True):
        parent = node_at(target, path)
        leaf = path.split(".")[-1]
        if parent is not None and leaf in parent and parent[leaf] in ({}, []):
            del parent[leaf]


def drop_residue(data, original):
    """Top-level empty containers the original did not have. The plugin CLI
    leaves `enabledPlugins: {}` and `extraKnownMarketplaces: {}` behind."""
    return {k: v for k, v in data.items() if not (v in ({}, []) and k not in original)}


def backup(path):
    if os.path.exists(path):
        dest = f"{path}.tstack-backup-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(path, dest)
        print(f"  backup: {dest}")


def write(path, data, keep_backup=True):
    if keep_backup:
        backup(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        if isinstance(data, str):
            fh.write(data)
        else:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")


def fill(node, placeholder, value):
    if isinstance(node, dict):
        return {k: fill(v, placeholder, value) for k, v in node.items()}
    if isinstance(node, list):
        return [fill(v, placeholder, value) for v in node]
    return value if node == placeholder else node


def uninstall(args):
    if not os.path.exists(args.state):
        print("  nothing to remove (no tstack record)")
        return 0
    state = load_state(args.state)
    raw = read_raw(args.target)
    target = parse(raw, args.target)
    records = state["added"]
    removed = [r for r in records if remove(target, r)]
    prune_created(target, records)
    for r in removed:
        print(f"  removed {r['path']}" + (f" item {r['item']}" if "item" in r else ""))
    if not removed:
        print("  nothing to remove")
    if args.dry_run:
        return 0
    original = state.get("original", MISSING)
    if original is None and drop_residue(target, {}) == {}:
        if raw is not None:
            backup(args.target)
            os.remove(args.target)
        print("  restored: no settings file, as before tstack")
    elif isinstance(original, str) and drop_residue(target, parse(original)) == parse(original):
        if raw != original:
            write(args.target, original)
        print("  restored the original file byte for byte")
    elif removed:
        write(args.target, target)
    os.remove(args.state)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template")
    ap.add_argument("--target", required=True)
    ap.add_argument("--state")
    ap.add_argument("--statusline", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    try:
        if args.check:
            parse(read_raw(args.target), args.target)
            return 0
        if args.uninstall:
            return uninstall(args)
        state = load_state(args.state)
        raw = read_raw(args.target)
        target = parse(raw, args.target)
        if args.snapshot:
            if args.dry_run:
                return 0
            if raw is None and state["added"]:
                # The user deleted settings.json since the last install: start over.
                state = {"added": [], "original": None}
                write(args.state, state, keep_backup=False)
            elif "original" not in state:
                state["original"] = raw
                write(args.state, state, keep_backup=False)
            return 0

        with open(args.template, encoding="utf-8") as fh:
            template = fill(json.load(fh), "__STATUSLINE__", args.statusline)
        added, kept, skipped = [], [], []
        merge(target, template, "", added, kept, state["added"], skipped)
        for a in added:
            if a.get("container"):
                continue
            print(f"  set {a['path']}" + (f" += {a['item']}" if "item" in a else f" = {json.dumps(a['value'], ensure_ascii=False)}"))
        for k in kept:
            print(f"  kept yours: {k}")
        for k in skipped:
            print(f"  skipped, you removed it after an earlier install: {k}")
        if skipped:
            print(f"  (to get those back, delete {args.state} and re-run)")
        if not added:
            print("  settings already up to date")
            return 0
        if args.dry_run:
            return 0
        write(args.target, target)
        state.setdefault("original", raw)
        state["added"] = state["added"] + [a for a in added if a not in state["added"]]
        write(args.state, state, keep_backup=False)
        return 0
    except BadJSON as exc:
        print(f"  {exc}. Claude Code cannot read it either: fix the file, then re-run.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
