#!/usr/bin/env python3
"""PTC Script: validate_tasks.py
Validate tasks.json against the schema and check for issues.

Usage: python3 skills/task-splitter/scripts/validate_tasks.py [tasks.json_path]
"""
import json
import sys
from pathlib import Path

TASKS_FILE = Path("tasks.json")
SCHEMA_FILE = Path("docs/templates/tasks-schema.json")


def validate(tasks_path: str = "tasks.json") -> dict:
    path = Path(tasks_path)
    if not path.exists():
        return {"valid": False, "error": f"File not found: {tasks_path}"}

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"Invalid JSON: {e}"}

    issues = []
    warnings = []

    # Detect schema version
    schema_version = data.get("schema_version", "1")

    # Check top-level required fields
    if "tasks" not in data:
        issues.append("Missing required field: tasks")
        return {"valid": False, "issues": issues, "warnings": warnings}

    if "design" not in data:
        issues.append("Missing required field: design")

    tasks = data["tasks"]
    if not isinstance(tasks, list):
        issues.append("'tasks' must be an array")
        return {"valid": False, "issues": issues, "warnings": warnings}

    if len(tasks) == 0:
        issues.append("No tasks found")

    task_ids = set()
    tasks_with_timing = 0
    tasks_with_tests = 0

    for i, task in enumerate(tasks):
        # Check required fields
        for field in ["id", "title", "scope", "status", "files", "verification"]:
            if field not in task:
                issues.append(f"Task {i}: missing required field '{field}'")

        # Check ID format
        task_id = task.get("id", "")
        if not task_id.startswith("T") or len(task_id) != 4:
            issues.append(f"Task {i}: invalid ID format '{task_id}' (expected T001-T999)")
        if task_id in task_ids:
            issues.append(f"Task {i}: duplicate ID '{task_id}'")
        task_ids.add(task_id)

        # Check scope
        scope = task.get("scope", "")
        if scope not in ("S", "M", "L"):
            issues.append(f"Task {task_id}: invalid scope '{scope}' (expected S/M/L)")

        # Check status
        status = task.get("status", "")
        if status not in ("pending", "in_progress", "completed", "blocked", "skipped"):
            issues.append(f"Task {task_id}: invalid status '{status}'")

        # Check verification
        verification = task.get("verification", {})
        if not isinstance(verification, dict):
            issues.append(f"Task {task_id}: verification must be an object")
        elif "command" not in verification or "expected" not in verification:
            issues.append(f"Task {task_id}: verification must have 'command' and 'expected'")
        else:
            # Warn on placeholder verification commands
            if "TODO" in verification.get("command", ""):
                warnings.append(f"Task {task_id}: verification command contains TODO placeholder")
            if "TODO" in verification.get("expected", ""):
                warnings.append(f"Task {task_id}: verification expected contains TODO placeholder")

        # Warn on empty files arrays
        files = task.get("files", [])
        if isinstance(files, list) and len(files) == 0:
            warnings.append(f"Task {task_id}: files array is empty")

        # Check depends_on references
        for dep in task.get("depends_on", []):
            if dep not in task_ids and dep not in [t.get("id") for t in tasks]:
                issues.append(f"Task {task_id}: depends on unknown task '{dep}'")

        # Track quality metrics
        if task.get("duration_seconds") is not None or task.get("started_at"):
            tasks_with_timing += 1
        if task.get("tests_written") is not None:
            tasks_with_tests += 1

    # Check for circular dependencies
    def has_cycle(task_id, visited=None, stack=None):
        if visited is None:
            visited = set()
        if stack is None:
            stack = set()
        visited.add(task_id)
        stack.add(task_id)
        task = next((t for t in tasks if t.get("id") == task_id), None)
        if task:
            for dep in task.get("depends_on", []):
                if dep not in visited:
                    if has_cycle(dep, visited, stack):
                        return True
                elif dep in stack:
                    return True
        stack.discard(task_id)
        return False

    for task in tasks:
        if has_cycle(task.get("id", "")):
            issues.append(f"Circular dependency detected involving task {task.get('id')}")
            break

    # Summary stats
    status_counts = {}
    for task in tasks:
        s = task.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    result = {
        "valid": len(issues) == 0,
        "schema_version": schema_version,
        "task_count": len(tasks),
        "status_counts": status_counts,
        "issues": issues,
        "warnings": warnings,
    }

    # Add quality metrics for v2
    if schema_version == "2":
        result["quality_metrics"] = {
            "tasks_with_timing": tasks_with_timing,
            "tasks_with_tests": tasks_with_tests,
        }

    return result


if __name__ == "__main__":
    tasks_path = sys.argv[1] if len(sys.argv) > 1 else "tasks.json"
    result = validate(tasks_path)
    print(json.dumps(result, indent=2))
