#!/usr/bin/env python3
"""PTC Script: select_next.py
Find the next unblocked task from tasks.json.
Sets started_at and status to in_progress when selecting.
Returns only that single task's metadata (~100 tokens).

Usage: python3 skills/executor/scripts/select_next.py [tasks.json_path]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TASKS_FILE = Path("tasks.json")


def select_next(tasks_path: str = "tasks.json") -> dict:
    path = Path(tasks_path)
    if not path.exists():
        return {"error": "tasks.json not found. Run /split first."}

    data = json.loads(path.read_text())
    tasks = data.get("tasks", [])

    if not tasks:
        return {"error": "No tasks in tasks.json. Run /split first."}

    # Find completed task IDs
    completed = {t["id"] for t in tasks if t["status"] == "completed"}

    # Find next unblocked pending task
    for task in tasks:
        if task["status"] != "pending":
            continue

        # Check if all dependencies are completed
        deps = task.get("depends_on", [])
        if all(d in completed for d in deps):
            # Set started_at and status to in_progress
            timestamp = datetime.now(timezone.utc).isoformat()
            task["status"] = "in_progress"
            task["started_at"] = timestamp

            # Write back to tasks.json
            path.write_text(json.dumps(data, indent=2))

            return {
                "task": {
                    "id": task["id"],
                    "title": task["title"],
                    "description": task.get("description", ""),
                    "scope": task["scope"],
                    "files": task["files"],
                    "verification": task["verification"],
                    "annotations": task.get("annotations", []),
                    "depends_on": deps,
                    "estimated_minutes": task.get("estimated_minutes"),
                },
                "progress": {
                    "completed": len(completed),
                    "total": len(tasks),
                    "remaining": len(tasks) - len(completed),
                },
            }

    # Check if all done
    if len(completed) == len(tasks):
        return {"status": "all_complete", "message": "All tasks are completed!"}

    # Some tasks exist but are blocked
    blocked = [t["id"] for t in tasks if t["status"] == "pending"]
    in_progress = [t["id"] for t in tasks if t["status"] == "in_progress"]

    return {
        "status": "blocked",
        "message": "No unblocked tasks available.",
        "blocked_tasks": blocked,
        "in_progress_tasks": in_progress,
        "completed": len(completed),
        "total": len(tasks),
    }


if __name__ == "__main__":
    tasks_path = sys.argv[1] if len(sys.argv) > 1 else "tasks.json"
    result = select_next(tasks_path)
    print(json.dumps(result, indent=2))
