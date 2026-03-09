#!/usr/bin/env python3
"""Shared file locking for parallel-safe task execution.

Provides atomic read-modify-write on tasks.json so multiple Claude sessions
(each in their own git worktree) can safely pick and complete tasks concurrently.

Uses fcntl.flock (POSIX) for advisory file locking. The lock file is placed
next to tasks.json as .tasks.lock.

Usage:
    from task_lock import locked_tasks_json

    with locked_tasks_json(tasks_path) as (data, write_back):
        # data is the parsed tasks.json dict
        # call write_back(data) to persist changes
        task = pick_a_task(data)
        write_back(data)
"""
import fcntl
import json
import time
from contextlib import contextmanager
from pathlib import Path

# Default timeout waiting for lock (seconds)
LOCK_TIMEOUT = 30
# Retry interval (seconds)
LOCK_RETRY_INTERVAL = 0.1


class TaskLockError(Exception):
    """Raised when the lock cannot be acquired."""


def _lock_path(tasks_path: Path) -> Path:
    """Return the lock file path for a given tasks.json."""
    return tasks_path.parent / ".tasks.lock"


def _resolve_tasks_path(tasks_path: str = "tasks.json") -> Path:
    """Resolve tasks.json path, following git worktree to main repo if needed.

    In a git worktree, tasks.json lives in the main repo (shared state).
    This function detects worktrees and resolves to the main repo's tasks.json.
    """
    path = Path(tasks_path)

    # If an absolute path was given and exists, use it directly
    if path.is_absolute() and path.exists():
        return path

    # Check if we're in a git worktree
    git_dir = Path(".git")
    if git_dir.is_file():
        # .git is a file in worktrees, containing "gitdir: <path>"
        gitdir_content = git_dir.read_text().strip()
        if gitdir_content.startswith("gitdir: "):
            gitdir_path = Path(gitdir_content.split("gitdir: ", 1)[1])
            # Navigate from .git/worktrees/<name> -> main repo
            # gitdir_path is like /main-repo/.git/worktrees/<name>
            main_git_dir = gitdir_path.parent.parent  # .git/worktrees -> .git
            main_repo = main_git_dir.parent  # .git -> repo root
            main_tasks = main_repo / tasks_path
            if main_tasks.exists():
                return main_tasks

    # Default: use relative path from CWD
    return path


@contextmanager
def locked_tasks_json(tasks_path: str = "tasks.json", timeout: float = LOCK_TIMEOUT):
    """Context manager for atomic read-modify-write on tasks.json.

    Acquires an exclusive lock, reads the file, yields (data, write_back),
    and releases the lock on exit.

    Args:
        tasks_path: Path to tasks.json (auto-resolves worktree paths)
        timeout: Max seconds to wait for lock

    Yields:
        (data, write_back) where data is the parsed dict and write_back
        is a callable that writes the modified data back atomically.

    Raises:
        TaskLockError: If lock cannot be acquired within timeout
        FileNotFoundError: If tasks.json doesn't exist
    """
    resolved = _resolve_tasks_path(tasks_path)
    if not resolved.exists():
        raise FileNotFoundError(f"tasks.json not found at {resolved}")

    lock_file = _lock_path(resolved)
    written = False

    def write_back(data: dict):
        nonlocal written
        resolved.write_text(json.dumps(data, indent=2) + "\n")
        written = True

    # Create lock file if needed
    lock_file.touch(exist_ok=True)

    lock_fd = open(lock_file, "w")
    try:
        # Try to acquire lock with timeout
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break  # Lock acquired
            except (IOError, OSError):
                if time.monotonic() >= deadline:
                    raise TaskLockError(
                        f"Could not acquire lock on {lock_file} within {timeout}s. "
                        f"Another session may be stuck. Remove {lock_file} manually if needed."
                    )
                time.sleep(LOCK_RETRY_INTERVAL)

        # Lock acquired — read fresh data
        data = json.loads(resolved.read_text())
        yield data, write_back

    finally:
        # Release lock
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except (IOError, OSError):
            pass
        lock_fd.close()


def get_tasks_path(cli_path: str = "tasks.json") -> Path:
    """Public helper to resolve tasks.json path (worktree-aware)."""
    return _resolve_tasks_path(cli_path)
