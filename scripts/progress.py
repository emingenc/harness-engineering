#!/usr/bin/env python3
"""PTC Script: progress.py
Shared cross-session state via claude-progress.txt (append-only).

Usage:
  python scripts/progress.py read [--last N]
  python scripts/progress.py append "<message>"
  python scripts/progress.py summary
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROGRESS_FILE = Path("claude-progress.txt")


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


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: progress.py <read|append|summary> [args]"}))
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
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
