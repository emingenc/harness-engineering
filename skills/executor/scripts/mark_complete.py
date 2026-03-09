#!/usr/bin/env python3
"""PTC Script: mark_complete.py
Mark a task as completed in tasks.json and log to claude-progress.txt.

Usage: python3 skills/executor/scripts/mark_complete.py <task_id> [--commit-sha <sha>] [--tests-written N] [--tests-passed N] [--cove-findings '<json>']
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TASKS_FILE = Path("tasks.json")
PROGRESS_FILE = Path("claude-progress.txt")
PROGRESS_JSONL = Path("claude-progress.jsonl")


def mark_complete(task_id: str, commit_sha: str = None,
                  tests_written: int = None, tests_passed: int = None,
                  cove_findings: list = None) -> dict:
    if not TASKS_FILE.exists():
        return {"error": "tasks.json not found."}

    data = json.loads(TASKS_FILE.read_text())
    tasks = data.get("tasks", [])

    # Find the task
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if not task:
        return {"error": f"Task {task_id} not found in tasks.json."}

    if task["status"] == "completed":
        return {"warning": f"Task {task_id} is already completed."}

    # Update task
    timestamp = datetime.now(timezone.utc).isoformat()
    task["status"] = "completed"
    task["completed_at"] = timestamp
    if commit_sha:
        task["commit_sha"] = commit_sha

    # Calculate duration from started_at
    duration_seconds = None
    started_at = task.get("started_at")
    if started_at:
        try:
            start_dt = datetime.fromisoformat(started_at)
            end_dt = datetime.fromisoformat(timestamp)
            duration_seconds = (end_dt - start_dt).total_seconds()
            task["duration_seconds"] = duration_seconds
        except (ValueError, TypeError):
            pass

    # Increment attempt count
    task["attempt_count"] = task.get("attempt_count", 0) + 1

    # Record retry history
    retry_history = task.get("retry_history", [])
    retry_history.append({
        "attempt": task["attempt_count"],
        "timestamp": timestamp,
        "outcome": "success",
        "error_summary": None,
    })
    task["retry_history"] = retry_history

    # Test counts
    if tests_written is not None:
        task["tests_written"] = tests_written
    if tests_passed is not None:
        task["tests_passed"] = tests_passed

    # CoVe findings
    if cove_findings:
        task["cove_findings"] = cove_findings

    # Write updated tasks.json
    TASKS_FILE.write_text(json.dumps(data, indent=2))

    # Append to text progress log
    progress_entry = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] "
    progress_entry += f"Completed {task_id}: {task['title']}"
    if commit_sha:
        progress_entry += f" (commit: {commit_sha})"
    with open(PROGRESS_FILE, "a") as f:
        f.write(progress_entry + "\n")

    # Append structured progress entry
    structured_entry = {
        "timestamp": timestamp,
        "action": "task_complete",
        "task_id": task_id,
        "phase": "execute",
        "track": 2,
        "details": {
            "commit_sha": commit_sha,
            "duration_seconds": duration_seconds,
            "attempt_count": task["attempt_count"],
            "tests_written": tests_written,
            "tests_passed": tests_passed,
        },
        "message": f"Completed {task_id}: {task['title']}",
    }
    with open(PROGRESS_JSONL, "a") as f:
        f.write(json.dumps(structured_entry) + "\n")

    # Calculate remaining
    completed = sum(1 for t in tasks if t["status"] == "completed")
    total = len(tasks)

    return {
        "marked_complete": task_id,
        "title": task["title"],
        "commit_sha": commit_sha,
        "duration_seconds": duration_seconds,
        "attempt_count": task["attempt_count"],
        "tests_written": tests_written,
        "tests_passed": tests_passed,
        "progress": f"{completed}/{total} tasks completed",
        "remaining": total - completed,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: mark_complete.py <task_id> [--commit-sha <sha>] [--tests-written N] [--tests-passed N] [--cove-findings '<json>']"}))
        sys.exit(1)

    task_id = args[0]
    commit_sha = None
    tests_written = None
    tests_passed = None
    cove_findings = None

    if "--commit-sha" in args:
        idx = args.index("--commit-sha")
        commit_sha = args[idx + 1] if idx + 1 < len(args) else None
    if "--tests-written" in args:
        idx = args.index("--tests-written")
        tests_written = int(args[idx + 1]) if idx + 1 < len(args) else None
    if "--tests-passed" in args:
        idx = args.index("--tests-passed")
        tests_passed = int(args[idx + 1]) if idx + 1 < len(args) else None
    if "--cove-findings" in args:
        idx = args.index("--cove-findings")
        if idx + 1 < len(args):
            try:
                cove_findings = json.loads(args[idx + 1])
            except json.JSONDecodeError:
                cove_findings = [args[idx + 1]]

    result = mark_complete(task_id, commit_sha, tests_written, tests_passed, cove_findings)
    print(json.dumps(result, indent=2))
