#!/usr/bin/env python3
"""PTC Script: select_next.py
Find the next unblocked task from tasks.json.
Sets started_at and status to in_progress when selecting.
Returns only that single task's metadata (~100 tokens).

Parallel-safe: uses file locking so multiple sessions can pick tasks concurrently.

Usage: python3 skills/executor/scripts/select_next.py [tasks.json_path]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts/ to path for task_lock import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "scripts"))
from task_lock import TaskLockError, locked_tasks_json


def select_next(tasks_path: str = "tasks.json") -> dict:
    try:
        with locked_tasks_json(tasks_path) as (data, write_back):
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

                    # Write back under lock
                    write_back(data)

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

    except FileNotFoundError:
        return {"error": "tasks.json not found. Run /split first."}
    except TaskLockError as e:
        return {"error": f"Lock contention: {e}"}


if __name__ == "__main__":
    tasks_path = sys.argv[1] if len(sys.argv) > 1 else "tasks.json"
    result = select_next(tasks_path)
    print(json.dumps(result, indent=2))
