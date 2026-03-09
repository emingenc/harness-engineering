#!/usr/bin/env python3
"""PTC Script: dashboard.py
Generate dashboard data for task visualization.

Usage:
  python3 scripts/dashboard.py full [tasks.json_path]
  python3 scripts/dashboard.py graph [tasks.json_path]
  python3 scripts/dashboard.py velocity [tasks.json_path]
"""
import json
import sys
from pathlib import Path

TASKS_FILE = Path("tasks.json")
PROGRESS_JSONL = Path("claude-progress.jsonl")


def load_tasks(tasks_path: str) -> dict:
    path = Path(tasks_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def build_graph(tasks: list[dict]) -> str:
    """Build a Mermaid dependency graph."""
    lines = ["graph TD"]
    for task in tasks:
        tid = task["id"]
        title = task.get("title", "")[:30]
        status = task.get("status", "pending")

        # Style based on status
        if status == "completed":
            lines.append(f"    {tid}[\"✓ {tid}: {title}\"]:::done")
        elif status == "in_progress":
            lines.append(f"    {tid}[\"{tid}: {title}\"]:::active")
        else:
            lines.append(f"    {tid}[\"{tid}: {title}\"]")

        for dep in task.get("depends_on", []):
            lines.append(f"    {dep} --> {tid}")

    lines.append("    classDef done fill:#2d5016,stroke:#4ade80")
    lines.append("    classDef active fill:#1e3a5f,stroke:#60a5fa")
    return "\n".join(lines)


def build_progress_bars(tasks: list[dict]) -> list[dict]:
    """Build ASCII progress bars for each task."""
    bars = []
    for task in tasks:
        status = task.get("status", "pending")
        if status == "completed":
            bar = "[##########] 100%"
            pct = 100
        elif status == "in_progress":
            bar = "[#####.....] 50%"
            pct = 50
        else:
            bar = "[..........] 0%"
            pct = 0

        bars.append({
            "id": task["id"],
            "title": task.get("title", "")[:40],
            "status": status,
            "scope": task.get("scope", "?"),
            "bar": bar,
            "percent": pct,
        })
    return bars


def compute_velocity(tasks: list[dict]) -> dict:
    """Compute velocity metrics."""
    completed = [t for t in tasks if t.get("status") == "completed"]
    durations = [t["duration_seconds"] for t in completed if t.get("duration_seconds")]

    avg_duration_min = 0
    if durations:
        avg_duration_min = round(sum(durations) / len(durations) / 60, 1)

    # Estimate remaining
    remaining = [t for t in tasks if t.get("status") in ("pending", "in_progress")]
    scope_estimates = {"S": 15, "M": 60, "L": 120}
    estimated_remaining = sum(
        scope_estimates.get(t.get("scope", "M"), 60)
        for t in remaining
    )

    # If we have actual data, use avg duration per scope
    if durations:
        scope_actuals = {}
        for t in completed:
            dur = t.get("duration_seconds")
            scope = t.get("scope", "M")
            if dur:
                if scope not in scope_actuals:
                    scope_actuals[scope] = []
                scope_actuals[scope].append(dur / 60)

        estimated_remaining = 0
        for t in remaining:
            scope = t.get("scope", "M")
            if scope in scope_actuals:
                estimated_remaining += sum(scope_actuals[scope]) / len(scope_actuals[scope])
            else:
                estimated_remaining += scope_estimates.get(scope, 60)

    return {
        "avg_duration_minutes": avg_duration_min,
        "estimated_remaining_minutes": round(estimated_remaining, 1),
        "completed_count": len(completed),
        "remaining_count": len(remaining),
    }


def quality_metrics(tasks: list[dict]) -> dict:
    """Compute quality metrics."""
    completed = [t for t in tasks if t.get("status") == "completed"]
    total_tests = sum(t.get("tests_written", 0) or 0 for t in completed)
    total_cove = sum(len(t.get("cove_findings", [])) for t in completed)
    two_pass = sum(
        1 for t in completed
        for r in t.get("retry_history", [])
        if r.get("outcome") == "2pass_limit"
    )

    return {
        "total_tests_written": total_tests,
        "cove_findings_count": total_cove,
        "two_pass_triggers": two_pass,
    }


def full(tasks_path: str) -> dict:
    data = load_tasks(tasks_path)
    if not data:
        return {"error": f"Could not load {tasks_path}"}

    tasks = data.get("tasks", [])
    completed_count = sum(1 for t in tasks if t.get("status") == "completed")

    return {
        "dependency_graph_mermaid": build_graph(tasks),
        "progress_bars": build_progress_bars(tasks),
        "quality_metrics": quality_metrics(tasks),
        "velocity": compute_velocity(tasks),
        "overall_progress": f"{completed_count}/{len(tasks)} tasks ({round(completed_count/len(tasks)*100) if tasks else 0}%)",
        "schema_version": data.get("schema_version", "1"),
        "plan_version": data.get("plan_version", 1),
    }


def graph(tasks_path: str) -> dict:
    data = load_tasks(tasks_path)
    if not data:
        return {"error": f"Could not load {tasks_path}"}
    return {"dependency_graph_mermaid": build_graph(data.get("tasks", []))}


def velocity(tasks_path: str) -> dict:
    data = load_tasks(tasks_path)
    if not data:
        return {"error": f"Could not load {tasks_path}"}
    return {"velocity": compute_velocity(data.get("tasks", []))}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: dashboard.py <full|graph|velocity> [tasks.json_path]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    tasks_path = sys.argv[2] if len(sys.argv) > 2 else "tasks.json"

    if cmd == "full":
        result = full(tasks_path)
    elif cmd == "graph":
        result = graph(tasks_path)
    elif cmd == "velocity":
        result = velocity(tasks_path)
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
