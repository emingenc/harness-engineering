#!/usr/bin/env python3
"""PTC Script: context_tracker.py
Estimate current session's context utilization.

Usage:
  python3 scripts/context_tracker.py estimate
  python3 scripts/context_tracker.py check
"""
import json
import sys
from pathlib import Path

PROGRESS_JSONL = Path("claude-progress.jsonl")
CONTEXT_WINDOW = 200_000

# Token estimates per scope
SCOPE_TOKENS = {"S": 5_000, "M": 15_000, "L": 30_000}
BASE_OVERHEAD = 3_000  # system prompt
PER_ENTRY_OVERHEAD = 100  # tokens per progress entry

THRESHOLDS = {
    "ok": 50,
    "caution": 70,
    "warning": 90,
}


def get_session_entries() -> list[dict]:
    """Get entries since the last session_start."""
    if not PROGRESS_JSONL.exists():
        return []

    entries = []
    last_session_start = -1

    lines = PROGRESS_JSONL.read_text().strip().split("\n")
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            entries.append(entry)
            if entry.get("action") == "session_start":
                last_session_start = len(entries) - 1
        except json.JSONDecodeError:
            continue

    if last_session_start >= 0:
        return entries[last_session_start:]
    return entries


def estimate() -> dict:
    entries = get_session_entries()

    # Count tasks processed this session
    tasks_processed = []
    for entry in entries:
        if entry.get("action") in ("task_complete", "task_start", "task_fail"):
            task_id = entry.get("task_id")
            if task_id and task_id not in tasks_processed:
                tasks_processed.append(task_id)

    # Estimate tokens from scope
    # Try to read tasks.json for scope info
    scope_tokens = 0
    tasks_path = Path("tasks.json")
    if tasks_path.exists():
        try:
            data = json.loads(tasks_path.read_text())
            task_map = {t["id"]: t for t in data.get("tasks", [])}
            for tid in tasks_processed:
                task = task_map.get(tid, {})
                scope = task.get("scope", "M")
                scope_tokens += SCOPE_TOKENS.get(scope, 15_000)
        except (json.JSONDecodeError, KeyError):
            scope_tokens = len(tasks_processed) * 15_000
    else:
        scope_tokens = len(tasks_processed) * 15_000

    estimated_tokens = BASE_OVERHEAD + scope_tokens + (len(entries) * PER_ENTRY_OVERHEAD)
    utilization_pct = round((estimated_tokens / CONTEXT_WINDOW) * 100, 1)

    return {
        "estimated_tokens": estimated_tokens,
        "utilization_percent": utilization_pct,
        "tasks_this_session": len(tasks_processed),
        "entries_this_session": len(entries),
        "context_window": CONTEXT_WINDOW,
    }


def check() -> dict:
    est = estimate()
    pct = est["utilization_percent"]

    if pct >= THRESHOLDS["warning"]:
        warning_level = "critical"
        recommendation = "Run /handoff now"
    elif pct >= THRESHOLDS["caution"]:
        warning_level = "warning"
        recommendation = "Consider compacting"
    elif pct >= THRESHOLDS["ok"]:
        warning_level = "caution"
        recommendation = "Monitor context usage"
    else:
        warning_level = "ok"
        recommendation = None

    return {
        "estimated_tokens": est["estimated_tokens"],
        "utilization_percent": est["utilization_percent"],
        "warning_level": warning_level,
        "tasks_this_session": est["tasks_this_session"],
        "recommendation": recommendation,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: context_tracker.py <estimate|check>"}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "estimate":
        result = estimate()
    elif cmd == "check":
        result = check()
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
