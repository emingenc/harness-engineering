#!/usr/bin/env python3
"""PTC Script: split_tasks.py
Parse an annotated design.md and generate tasks.json.

Usage: python3 skills/task-splitter/scripts/split_tasks.py <design.md_path>
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts/ to path for task_lock import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "scripts"))
from task_lock import TaskLockError, locked_tasks_json

TASKS_FILE = Path("tasks.json")

SCOPE_ESTIMATES = {"S": 15, "M": 60, "L": 120}


def extract_annotations(content: str) -> list[str]:
    return re.findall(r"<!-- ANNOTATION:\s*(.*?)\s*-->", content)


def extract_tasks(content: str) -> list[dict]:
    """Extract micro-tasks from the Micro-Task Breakdown section."""
    tasks = []

    # Find the micro-task breakdown section
    pattern = r"(?:##?\s*Micro-Task Breakdown.*?\n)(.*?)(?=\n##?\s|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if not match:
        return tasks

    section = match.group(1)

    # Parse numbered items: "1. Task description -- scope: S/M/L"
    task_pattern = r"^\s*(\d+)\.\s+(.+?)(?:\s*--\s*scope:\s*(S|M|L))?\s*$"
    for m in re.finditer(task_pattern, section, re.MULTILINE):
        num = int(m.group(1))
        title = m.group(2).strip()
        scope = m.group(3) or "M"  # Default to M if not specified

        task_id = f"T{num:03d}"
        tasks.append({
            "id": task_id,
            "title": title,
            "description": "",
            "scope": scope,
            "status": "pending",
            "depends_on": [],
            "files": [],
            "verification": {
                "command": "echo 'TODO: add verification command'",
                "expected": "TODO: define expected output",
            },
            "annotations": [],
            "estimated_minutes": SCOPE_ESTIMATES.get(scope, 60),
            "attempt_count": 0,
            "retry_history": [],
            "cove_findings": [],
        })

    return tasks


def extract_file_changes(content: str) -> dict[str, str]:
    """Extract file changes table to associate files with tasks."""
    files = {}
    # Match table rows: | file | change type | description |
    pattern = r"\|\s*`?([^|`]+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|"
    for m in re.finditer(pattern, content):
        filepath = m.group(1).strip()
        if filepath and not filepath.startswith("-") and filepath != "File":
            desc = m.group(3).strip()
            files[filepath] = desc
    return files


def extract_verification_strategy(content: str) -> list[dict]:
    """Extract verification items from the Verification Strategy section.

    Supports two formats:
    - Table: | Check | Type | Command |
    - Numbered list: 1. Description
    """
    items = []

    pattern = r"(?:##?\s*Verification Strategy.*?\n)(.*?)(?=\n##?\s|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if not match:
        return items

    section = match.group(1)

    # Try table format: | Check | Type | Command |
    table_pattern = r"\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|"
    for m in re.finditer(table_pattern, section):
        check = m.group(1).strip()
        vtype = m.group(2).strip()
        command = m.group(3).strip()
        if check and check != "Check" and not check.startswith("-"):
            items.append({"check": check, "type": vtype, "command": command})

    # If no table found, try numbered list
    if not items:
        list_pattern = r"^\s*\d+\.\s+(.+)$"
        for m in re.finditer(list_pattern, section, re.MULTILINE):
            items.append({"check": m.group(1).strip(), "type": "auto", "command": ""})

    return items


def generate_verification(task: dict, verification_items: list[dict]) -> dict:
    """Generate a verification command for a task.

    Strategy (in priority order):
    1. Match task against verification strategy items by keyword overlap
    2. If task has test files, generate pytest command
    3. If task has script files, generate a run command
    4. Fallback: grep-based existence check on modified files
    """
    # Try matching against verification strategy items
    best_item = None
    best_score = 0
    title_words = set(task["title"].lower().split())
    for item in verification_items:
        check_words = set(item["check"].lower().split())
        overlap = len(title_words & check_words)
        if overlap > best_score:
            best_score = overlap
            best_item = item

    if best_item and best_item.get("command"):
        return {"command": best_item["command"], "expected": "pass"}

    # Check task files for test files
    test_files = [f for f in task["files"] if "test" in f.lower()]
    if test_files:
        return {
            "command": f"python3 -m pytest {test_files[0]} -v",
            "expected": "passed",
        }

    # Check for script files
    script_files = [f for f in task["files"] if f.endswith(".py")]
    if script_files:
        return {
            "command": f"python3 -m py_compile {script_files[0]}",
            "expected": "exit 0",
        }

    # Check for markdown/config files
    if task["files"]:
        return {
            "command": f"test -f {task['files'][0]}",
            "expected": "exit 0",
        }

    # Fallback
    return {
        "command": "echo 'TODO: add verification command'",
        "expected": "TODO: define expected output",
    }


def associate_files_with_tasks(tasks: list[dict], file_changes: dict[str, str]) -> list[dict]:
    """Map file changes to tasks by keyword matching against task titles."""
    for filepath, description in file_changes.items():
        desc_lower = (description + " " + filepath).lower()
        best_match = None
        best_score = 0
        for task in tasks:
            title_words = set(task["title"].lower().split())
            desc_words = set(desc_lower.split())
            overlap = len(title_words & desc_words)
            if overlap > best_score:
                best_score = overlap
                best_match = task
        if best_match and best_score > 0:
            if filepath not in best_match["files"]:
                best_match["files"].append(filepath)
    return tasks


def build_dependencies(tasks: list[dict]) -> list[dict]:
    """Set up linear dependencies by default.
    Tasks are assumed to depend on the previous task unless otherwise specified.
    """
    for i, task in enumerate(tasks):
        if i > 0:
            task["depends_on"] = [tasks[i - 1]["id"]]
    return tasks


def associate_annotations(tasks: list[dict], annotations: list[str]) -> list[dict]:
    """Associate annotations with tasks based on keyword matching."""
    for annotation in annotations:
        ann_lower = annotation.lower()
        best_match = None
        best_score = 0
        for task in tasks:
            title_words = set(task["title"].lower().split())
            ann_words = set(ann_lower.split())
            overlap = len(title_words & ann_words)
            if overlap > best_score:
                best_score = overlap
                best_match = task
        if best_match and best_score > 0:
            best_match["annotations"].append(annotation)

    return tasks


def split(design_path: str) -> dict:
    path = Path(design_path)
    if not path.exists():
        return {"error": f"File not found: {design_path}"}

    content = path.read_text()

    # Extract annotations
    annotations = extract_annotations(content)
    if not annotations:
        return {
            "error": "No annotations found. Human must annotate the design before splitting.",
            "hint": "Add <!-- ANNOTATION: your comment --> to the design document.",
        }

    # Extract tasks
    tasks = extract_tasks(content)
    if not tasks:
        return {
            "error": "No micro-task breakdown found in design document.",
            "hint": "Add a 'Micro-Task Breakdown' section with numbered items.",
        }

    # Extract file changes and associate with tasks
    file_changes = extract_file_changes(content)
    if file_changes:
        tasks = associate_files_with_tasks(tasks, file_changes)

    # Auto-generate verification commands
    verification_items = extract_verification_strategy(content)
    for task in tasks:
        verification = generate_verification(task, verification_items)
        task["verification"] = verification

    # Build dependencies
    tasks = build_dependencies(tasks)

    # Associate annotations
    tasks = associate_annotations(tasks, annotations)

    timestamp = datetime.now(timezone.utc).isoformat()

    # Handle re-split: preserve completed tasks, increment plan_version
    plan_version = 1
    plan_history = []

    if TASKS_FILE.exists():
        try:
            with locked_tasks_json(str(TASKS_FILE)) as (existing, write_back):
                plan_version = existing.get("plan_version", 1) + 1
                plan_history = existing.get("plan_history", [])

                # Preserve completed task statuses
                completed_map = {}
                for t in existing.get("tasks", []):
                    if t["status"] == "completed":
                        completed_map[t["id"]] = t
                for task in tasks:
                    if task["id"] in completed_map:
                        old = completed_map[task["id"]]
                        task["status"] = "completed"
                        task["completed_at"] = old.get("completed_at")
                        task["commit_sha"] = old.get("commit_sha")
                        task["duration_seconds"] = old.get("duration_seconds")
                        task["attempt_count"] = old.get("attempt_count", 0)
                        task["retry_history"] = old.get("retry_history", [])
                        task["tests_written"] = old.get("tests_written")
                        task["tests_passed"] = old.get("tests_passed")

                # Add current split to plan history
                plan_history.append({
                    "version": plan_version,
                    "timestamp": timestamp,
                    "design_path": design_path,
                    "annotation_count": len(annotations),
                })

                # Build tasks.json
                tasks_data = {
                    "schema_version": "2",
                    "design": design_path,
                    "created": timestamp,
                    "plan_version": plan_version,
                    "plan_history": plan_history,
                    "tasks": tasks,
                }

                # Write tasks.json under lock
                write_back(tasks_data)
        except (json.JSONDecodeError, KeyError, TaskLockError):
            pass
    else:
        # First split — no existing file, no lock needed
        plan_history.append({
            "version": plan_version,
            "timestamp": timestamp,
            "design_path": design_path,
            "annotation_count": len(annotations),
        })

        tasks_data = {
            "schema_version": "2",
            "design": design_path,
            "created": timestamp,
            "plan_version": plan_version,
            "plan_history": plan_history,
            "tasks": tasks,
        }

        TASKS_FILE.write_text(json.dumps(tasks_data, indent=2))

    # Build dependency chain summary
    annotated_count = sum(1 for t in tasks if t["annotations"])
    dep_chains = []
    for task in tasks:
        if task["depends_on"]:
            dep_chains.append(f"{task['depends_on'][0]}->{task['id']}")

    files_populated = sum(1 for t in tasks if t["files"])

    return {
        "tasks_generated": len(tasks),
        "annotated_tasks": annotated_count,
        "total_annotations": len(annotations),
        "dependency_chain": ", ".join(dep_chains) if dep_chains else "no dependencies",
        "scopes": {s: sum(1 for t in tasks if t["scope"] == s) for s in ["S", "M", "L"]},
        "files_populated": files_populated,
        "file_changes_found": len(file_changes),
        "schema_version": "2",
        "plan_version": plan_version,
        "written_to": str(TASKS_FILE),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: split_tasks.py <design.md_path>"}))
        sys.exit(1)

    result = split(sys.argv[1])
    print(json.dumps(result, indent=2))
