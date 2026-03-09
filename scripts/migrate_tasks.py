#!/usr/bin/env python3
"""PTC Script: migrate_tasks.py
Migrate a v1 tasks.json to v2 format.

Usage: python3 scripts/migrate_tasks.py [tasks.json_path]
"""
import json
import sys
from pathlib import Path

SCOPE_ESTIMATES = {"S": 15, "M": 60, "L": 120}


def migrate(tasks_path: str = "tasks.json") -> dict:
    path = Path(tasks_path)
    if not path.exists():
        return {"error": f"File not found: {tasks_path}"}

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    # Already v2?
    if data.get("schema_version") == "2":
        return {"status": "already_v2", "message": "File is already schema version 2."}

    # Add top-level v2 fields
    data["schema_version"] = "2"
    data["plan_version"] = data.get("plan_version", 1)
    data["plan_history"] = data.get("plan_history", [])

    migrated_count = 0
    tasks = data.get("tasks", [])
    for task in tasks:
        changed = False
        if "attempt_count" not in task:
            task["attempt_count"] = 0
            changed = True
        if "retry_history" not in task:
            task["retry_history"] = []
            changed = True
        if "cove_findings" not in task:
            task["cove_findings"] = []
            changed = True
        if "estimated_minutes" not in task:
            scope = task.get("scope", "M")
            task["estimated_minutes"] = SCOPE_ESTIMATES.get(scope, 60)
            changed = True
        if changed:
            migrated_count += 1

    # Write back
    path.write_text(json.dumps(data, indent=2))

    return {
        "status": "migrated",
        "schema_version": "2",
        "tasks_migrated": migrated_count,
        "total_tasks": len(tasks),
        "written_to": str(path),
    }


if __name__ == "__main__":
    tasks_path = sys.argv[1] if len(sys.argv) > 1 else "tasks.json"
    result = migrate(tasks_path)
    print(json.dumps(result, indent=2))
