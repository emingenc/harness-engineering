"""Shared fixtures for harness-engineering plugin tests."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Project root (one level up from tests/)
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_script(script_path: str, *args: str, cwd: str = None) -> dict:
    """Run a PTC script and parse its JSON output.

    Args:
        script_path: Path to the Python script (relative to PROJECT_ROOT or absolute).
        *args: Command-line arguments to pass.
        cwd: Working directory for the subprocess.

    Returns:
        Parsed JSON dict from stdout.
    """
    full_path = PROJECT_ROOT / script_path if not Path(script_path).is_absolute() else Path(script_path)
    cmd = [sys.executable, str(full_path)] + list(args)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError(
            f"Script {script_path} did not return valid JSON.\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}\nreturncode: {proc.returncode}"
        )


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    """Change to a temporary working directory, restore after test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def sample_tasks_json(work_dir):
    """Create a valid tasks.json with 3 tasks in the work_dir."""
    data = {
        "design": "design.md",
        "created": "2026-03-08T00:00:00+00:00",
        "tasks": [
            {
                "id": "T001",
                "title": "Create auth module",
                "description": "JWT token issuer",
                "scope": "S",
                "status": "pending",
                "depends_on": [],
                "files": ["src/auth/token.py"],
                "verification": {"command": "pytest tests/test_auth.py", "expected": "passed"},
                "annotations": ["Consider JWT with short-lived tokens"],
            },
            {
                "id": "T002",
                "title": "Add refresh token rotation",
                "description": "Session store with Redis",
                "scope": "M",
                "status": "pending",
                "depends_on": ["T001"],
                "files": ["src/auth/session.py"],
                "verification": {"command": "pytest tests/test_session.py", "expected": "passed"},
                "annotations": [],
            },
            {
                "id": "T003",
                "title": "Implement RBAC engine",
                "description": "Role-based access control",
                "scope": "M",
                "status": "pending",
                "depends_on": ["T002"],
                "files": ["src/auth/rbac.py"],
                "verification": {"command": "pytest tests/test_rbac.py", "expected": "passed"},
                "annotations": [],
            },
        ],
    }
    tasks_path = work_dir / "tasks.json"
    tasks_path.write_text(json.dumps(data, indent=2))
    return tasks_path


@pytest.fixture
def empty_tasks_json(work_dir):
    """Create a tasks.json with empty tasks array."""
    data = {"design": "design.md", "created": "2026-03-08T00:00:00+00:00", "tasks": []}
    tasks_path = work_dir / "tasks.json"
    tasks_path.write_text(json.dumps(data, indent=2))
    return tasks_path


@pytest.fixture
def sample_progress(work_dir):
    """Create a claude-progress.txt with sample entries."""
    progress_path = work_dir / "claude-progress.txt"
    progress_path.write_text(
        "[2026-03-08T10:00:00Z] Started session\n"
        "[2026-03-08T10:05:00Z] Completed T001: Create auth module\n"
        "[2026-03-08T10:10:00Z] Completed T002: Add refresh token\n"
    )
    return progress_path
