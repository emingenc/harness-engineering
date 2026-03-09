#!/usr/bin/env python3
"""PTC Script: progress.py
Shared cross-session state via claude-progress.txt (append-only).
Dual-writes structured entries to claude-progress.jsonl.

Usage:
  python scripts/progress.py read [--last N]
  python scripts/progress.py append "<message>"
  python scripts/progress.py summary
  python scripts/progress.py append-structured --action <type> [--task-id <id>] [--phase <phase>] [--track <1|2>] [--details '<json>'] "<message>"
  python scripts/progress.py query --task-id <id>
  python scripts/progress.py query --action <type>
  python scripts/progress.py query --since <timestamp>
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROGRESS_FILE = Path("claude-progress.txt")
PROGRESS_JSONL = Path("claude-progress.jsonl")

VALID_ACTIONS = {
    "session_start", "task_start", "task_complete", "task_fail",
    "2pass_limit", "handoff", "fix_applied", "plan_created",
    "tasks_split", "cove_finding",
}


def read_progress(last_n: int = 10) -> dict:
    if not PROGRESS_FILE.exists():
        return {"entries": [], "count": 0, "truncated": False}
    lines = [l for l in PROGRESS_FILE.read_text().strip().split("\n") if l.strip()]
    total = len(lines)
    entries = lines[-last_n:] if last_n > 0 else lines
    return {
        "entries": entries,
        "count": total,
        "truncated": total > len(entries),
    }


def append_progress(message: str) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] {message}"
    with open(PROGRESS_FILE, "a") as f:
        f.write(entry + "\n")
    return {"appended": entry}


def summary() -> dict:
    if not PROGRESS_FILE.exists():
        return {"count": 0, "first": None, "last": None}
    lines = [l for l in PROGRESS_FILE.read_text().strip().split("\n") if l.strip()]
    if not lines:
        return {"count": 0, "first": None, "last": None}
    return {
        "count": len(lines),
        "first": lines[0],
        "last": lines[-1],
    }


def append_structured(action: str, message: str, task_id: str = None,
                      phase: str = None, track: int = None,
                      details: dict = None) -> dict:
    if action not in VALID_ACTIONS:
        return {"error": f"Invalid action: {action}. Valid: {', '.join(sorted(VALID_ACTIONS))}"}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build structured entry
    entry = {
        "timestamp": timestamp,
        "action": action,
        "message": message,
    }
    if task_id:
        entry["task_id"] = task_id
    if phase:
        entry["phase"] = phase
    if track is not None:
        entry["track"] = track
    if details:
        entry["details"] = details

    # Write to JSONL
    with open(PROGRESS_JSONL, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Also write to text log for backward compat
    text_parts = [f"[{timestamp}]"]
    if action:
        text_parts.append(f"[{action}]")
    if task_id:
        text_parts.append(f"[{task_id}]")
    text_parts.append(message)
    text_entry = " ".join(text_parts)
    with open(PROGRESS_FILE, "a") as f:
        f.write(text_entry + "\n")

    return {"appended": entry}


def query(task_id: str = None, action: str = None, since: str = None) -> dict:
    if not PROGRESS_JSONL.exists():
        return {"entries": [], "count": 0}

    entries = []
    for line in PROGRESS_JSONL.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if task_id and entry.get("task_id") != task_id:
            continue
        if action and entry.get("action") != action:
            continue
        if since and entry.get("timestamp", "") < since:
            continue

        entries.append(entry)

    return {"entries": entries, "count": len(entries)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: progress.py <read|append|summary|append-structured|query> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "read":
        last_n = 10
        if "--last" in sys.argv:
            idx = sys.argv.index("--last")
            if idx + 1 < len(sys.argv):
                last_n = int(sys.argv[idx + 1])
        result = read_progress(last_n)
    elif cmd == "append":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: progress.py append '<message>'"}))
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        result = append_progress(message)
    elif cmd == "summary":
        result = summary()
    elif cmd == "append-structured":
        # Parse flags
        args = sys.argv[2:]
        action = None
        task_id = None
        phase = None
        track = None
        details = None
        message_parts = []

        i = 0
        while i < len(args):
            if args[i] == "--action" and i + 1 < len(args):
                action = args[i + 1]
                i += 2
            elif args[i] == "--task-id" and i + 1 < len(args):
                task_id = args[i + 1]
                i += 2
            elif args[i] == "--phase" and i + 1 < len(args):
                phase = args[i + 1]
                i += 2
            elif args[i] == "--track" and i + 1 < len(args):
                track = int(args[i + 1])
                i += 2
            elif args[i] == "--details" and i + 1 < len(args):
                try:
                    details = json.loads(args[i + 1])
                except json.JSONDecodeError:
                    details = {"raw": args[i + 1]}
                i += 2
            else:
                message_parts.append(args[i])
                i += 1

        if not action:
            print(json.dumps({"error": "append-structured requires --action <type>"}))
            sys.exit(1)

        message = " ".join(message_parts) if message_parts else ""
        result = append_structured(action, message, task_id, phase, track, details)
    elif cmd == "query":
        args = sys.argv[2:]
        task_id = None
        action = None
        since = None

        i = 0
        while i < len(args):
            if args[i] == "--task-id" and i + 1 < len(args):
                task_id = args[i + 1]
                i += 2
            elif args[i] == "--action" and i + 1 < len(args):
                action = args[i + 1]
                i += 2
            elif args[i] == "--since" and i + 1 < len(args):
                since = args[i + 1]
                i += 2
            else:
                i += 1

        result = query(task_id, action, since)
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
