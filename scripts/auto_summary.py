#!/usr/bin/env python3
"""PTC Script: auto_summary.py
Generate a completion summary after all tasks are done.

Usage: python3 scripts/auto_summary.py [tasks.json_path]
"""
import json
import sys
from pathlib import Path

TASKS_FILE = Path("tasks.json")
PROGRESS_JSONL = Path("claude-progress.jsonl")


def summarize(tasks_path: str = "tasks.json") -> dict:
    path = Path(tasks_path)
    if not path.exists():
        return {"error": "tasks.json not found."}

    data = json.loads(path.read_text())
    tasks = data.get("tasks", [])

    # Task stats
    completed = [t for t in tasks if t.get("status") == "completed"]
    total = len(tasks)

    # Duration stats
    durations = [t["duration_seconds"] for t in completed if t.get("duration_seconds")]
    total_duration = sum(durations) if durations else 0
    avg_duration = (total_duration / len(durations)) if durations else 0

    # Duration by scope
    duration_by_scope = {}
    for t in completed:
        scope = t.get("scope", "M")
        dur = t.get("duration_seconds")
        if dur is not None:
            if scope not in duration_by_scope:
                duration_by_scope[scope] = []
            duration_by_scope[scope].append(dur)

    avg_by_scope = {}
    for scope, durs in duration_by_scope.items():
        avg_by_scope[scope] = round(sum(durs) / len(durs) / 60, 1) if durs else 0

    # Test stats
    total_tests_written = sum(t.get("tests_written", 0) or 0 for t in completed)
    total_tests_passed = sum(t.get("tests_passed", 0) or 0 for t in completed)

    # CoVe findings
    all_cove = []
    for t in completed:
        all_cove.extend(t.get("cove_findings", []))

    # 2-pass triggers from progress log
    two_pass_count = 0
    if PROGRESS_JSONL.exists():
        for line in PROGRESS_JSONL.read_text().strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("action") == "2pass_limit":
                    two_pass_count += 1
            except json.JSONDecodeError:
                continue

    # Attempt stats
    total_attempts = sum(t.get("attempt_count", 0) for t in completed)

    return {
        "status": "all_complete",
        "tasks_completed": len(completed),
        "total_tasks": total,
        "total_duration_seconds": total_duration,
        "total_duration_minutes": round(total_duration / 60, 1) if total_duration else 0,
        "avg_duration_minutes": round(avg_duration / 60, 1) if avg_duration else 0,
        "avg_duration_by_scope": avg_by_scope,
        "total_attempts": total_attempts,
        "two_pass_triggers": two_pass_count,
        "total_tests_written": total_tests_written,
        "total_tests_passed": total_tests_passed,
        "cove_findings_count": len(all_cove),
        "cove_findings": all_cove[:10],  # Truncate to 10
        "scopes": {s: sum(1 for t in tasks if t.get("scope") == s) for s in ["S", "M", "L"]},
    }


if __name__ == "__main__":
    tasks_path = sys.argv[1] if len(sys.argv) > 1 else "tasks.json"
    result = summarize(tasks_path)
    print(json.dumps(result, indent=2))
