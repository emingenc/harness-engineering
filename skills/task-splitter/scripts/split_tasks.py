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

TASKS_FILE = Path("tasks.json")


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
        })

    return tasks


def extract_file_changes(content: str) -> dict[str, list[str]]:
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

    # Build dependencies
    tasks = build_dependencies(tasks)

    # Associate annotations
    tasks = associate_annotations(tasks, annotations)

    # Build tasks.json
    tasks_data = {
        "design": design_path,
        "created": datetime.now(timezone.utc).isoformat(),
        "tasks": tasks,
    }

    # Write tasks.json
    TASKS_FILE.write_text(json.dumps(tasks_data, indent=2))

    # Build dependency chain summary
    annotated_count = sum(1 for t in tasks if t["annotations"])
    dep_chains = []
    for task in tasks:
        if task["depends_on"]:
            dep_chains.append(f"{task['depends_on'][0]}->{task['id']}")

    return {
        "tasks_generated": len(tasks),
        "annotated_tasks": annotated_count,
        "total_annotations": len(annotations),
        "dependency_chain": ", ".join(dep_chains) if dep_chains else "no dependencies",
        "scopes": {s: sum(1 for t in tasks if t["scope"] == s) for s in ["S", "M", "L"]},
        "written_to": str(TASKS_FILE),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: split_tasks.py <design.md_path>"}))
        sys.exit(1)

    result = split(sys.argv[1])
    print(json.dumps(result, indent=2))
