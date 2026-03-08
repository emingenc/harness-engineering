"""Integration test: Track 1 (/fix) full workflow simulation."""
import json
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT, run_script


class TestTrack1Flow:
    """Simulates a complete Track 1 surgical fix workflow."""

    def test_full_track1_flow(self, work_dir):
        # Create a codebase to search
        (work_dir / "app.py").write_text(
            "import json\nimport sys\n\ndef main():\n    pass\n"
        )

        # Step 1: Scope check confirms Track 1
        result = run_script(
            "skills/small-fix/scripts/scope_check.py",
            "fix broken test import",
        )
        assert result["scope"] == "track1"

        # Step 2: Grep for context
        result = run_script(
            "skills/small-fix/scripts/grep_context.py",
            "import", "--pattern", "*.py",
            cwd=str(work_dir),
        )
        assert len(result["results"]) == 1
        assert result["results"][0]["total"] > 0

        # Step 3: Log completion to progress
        result = run_script(
            "scripts/progress.py",
            "append", "Track 1 fix completed: fixed broken import",
            cwd=str(work_dir),
        )
        assert "appended" in result

        # Step 4: Verify no tasks.json contamination (Track 1 doesn't use it)
        assert not (work_dir / "tasks.json").exists()
