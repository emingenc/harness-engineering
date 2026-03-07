#!/usr/bin/env python3
"""PTC Script: mark_complete.py
Mark a task as completed in tasks.json and log to claude-progress.txt.

Usage: python3 skills/executor/scripts/mark_complete.py <task_id> [--commit-sha <sha>]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TASKS_FILE = Path("tasks.json")
PROGRESS_FILE = Path("claude-progress.txt")


def mark_complete(task_id: str, commit_sha: str = None) -> dict:
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

    # Write updated tasks.json
    TASKS_FILE.write_text(json.dumps(data, indent=2))

    # Append to progress log
    progress_entry = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] "
    progress_entry += f"Completed {task_id}: {task['title']}"
    if commit_sha:
        progress_entry += f" (commit: {commit_sha})"
    with open(PROGRESS_FILE, "a") as f:
        f.write(progress_entry + "\n")

    # Calculate remaining
    completed = sum(1 for t in tasks if t["status"] == "completed")
    total = len(tasks)

    return {
        "marked_complete": task_id,
        "title": task["title"],
        "commit_sha": commit_sha,
        "progress": f"{completed}/{total} tasks completed",
        "remaining": total - completed,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: mark_complete.py <task_id> [--commit-sha <sha>]"}))
        sys.exit(1)

    task_id = args[0]
    commit_sha = None
    if "--commit-sha" in args:
        idx = args.index("--commit-sha")
        commit_sha = args[idx + 1] if idx + 1 < len(args) else None

    result = mark_complete(task_id, commit_sha)
    print(json.dumps(result, indent=2))
