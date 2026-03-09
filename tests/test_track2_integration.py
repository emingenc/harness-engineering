"""Integration test: Track 2 full cycle (research -> plan -> split -> execute)."""
import json
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR, PROJECT_ROOT, run_script


class TestTrack2FullCycle:
    """Simulates a complete Track 2 spec-driven feature workflow."""

    def test_full_track2_lifecycle(self, work_dir):
        # Create searchable files in the work dir
        (work_dir / "hooks.py").write_text("# hooks integration code\nPTC_ENABLED = True\n")
        (work_dir / "config.py").write_text("# PTC configuration\n")

        # ── Phase 1: Research ──
        result = run_script(
            "skills/researcher/scripts/search_local.py",
            "hooks", "PTC",
            cwd=str(work_dir),
        )
        assert len(result["results"]) == 2
        assert result["results"][0]["total_matches"] > 0

        # Format findings
        findings = json.dumps({
            "key_findings": ["Hooks use PTC scripts", "Config is separate"],
            "files_examined": ["hooks.py", "config.py"],
            "search_results": [{"term": "hooks", "total_matches": 1}],
            "open_questions": ["Should hooks be configurable?"],
            "recommendation": "Keep hooks and PTC separate",
        })
        output_path = str(work_dir / "research" / "findings.md")
        result = run_script(
            "skills/researcher/scripts/format_findings.py",
            "--topic", "Hooks and PTC",
            "--output", output_path,
            "--findings", findings,
            cwd=str(work_dir),
        )
        assert result["written_to"] == output_path
        assert Path(output_path).exists()

        # ── Phase 2: Plan validation ──
        design_path = str(FIXTURES_DIR / "sample-design.md")
        result = run_script(
            "skills/planner/scripts/validate_plan.py",
            design_path,
        )
        assert result["valid"] is True

        # ── Phase 3: Split into tasks ──
        result = run_script(
            "skills/task-splitter/scripts/split_tasks.py",
            design_path,
            cwd=str(work_dir),
        )
        assert result["tasks_generated"] == 3
        assert (work_dir / "tasks.json").exists()
        # Verify v2 schema
        assert result["schema_version"] == "2"

        # Validate generated tasks
        result = run_script(
            "skills/task-splitter/scripts/validate_tasks.py",
            str(work_dir / "tasks.json"),
        )
        assert result["valid"] is True
        assert result["task_count"] == 3

        # ── Phase 4: Execute cycle ──

        # Select first task (now sets in_progress)
        result = run_script(
            "skills/executor/scripts/select_next.py",
            str(work_dir / "tasks.json"),
        )
        assert result["task"]["id"] == "T001"

        # Verify in_progress was set
        data = json.loads((work_dir / "tasks.json").read_text())
        assert data["tasks"][0]["status"] == "in_progress"
        assert data["tasks"][0].get("started_at") is not None

        # Complete T001
        result = run_script(
            "skills/executor/scripts/mark_complete.py",
            "T001", "--commit-sha", "abc123",
            "--tests-written", "3", "--tests-passed", "3",
            cwd=str(work_dir),
        )
        assert result["marked_complete"] == "T001"
        assert result["remaining"] == 2
        assert result["attempt_count"] == 1

        # Select next → T002
        result = run_script(
            "skills/executor/scripts/select_next.py",
            str(work_dir / "tasks.json"),
        )
        assert result["task"]["id"] == "T002"

        # Complete T002
        result = run_script(
            "skills/executor/scripts/mark_complete.py",
            "T002", "--commit-sha", "def456",
            cwd=str(work_dir),
        )
        assert result["marked_complete"] == "T002"
        assert result["remaining"] == 1

        # Complete T003
        result = run_script(
            "skills/executor/scripts/mark_complete.py",
            "T003", "--commit-sha", "ghi789",
            cwd=str(work_dir),
        )
        assert result["marked_complete"] == "T003"
        assert result["remaining"] == 0

        # Select next → all complete
        result = run_script(
            "skills/executor/scripts/select_next.py",
            str(work_dir / "tasks.json"),
        )
        assert result["status"] == "all_complete"

        # ── Verify progress log ──
        progress = (work_dir / "claude-progress.txt").read_text()
        lines = [l for l in progress.strip().split("\n") if l.strip()]
        assert len(lines) == 3
        assert "T001" in lines[0]
        assert "T002" in lines[1]
        assert "T003" in lines[2]
        assert "abc123" in lines[0]

        # ── Verify structured progress log ──
        assert (work_dir / "claude-progress.jsonl").exists()
        jsonl_lines = (work_dir / "claude-progress.jsonl").read_text().strip().split("\n")
        assert len(jsonl_lines) == 3
        for line in jsonl_lines:
            entry = json.loads(line)
            assert entry["action"] == "task_complete"


class TestAutoLoopIntegration:
    """Simulates the auto-execute loop workflow."""

    def test_auto_loop_simulation(self, work_dir):
        """Simulate what /auto does: select → execute → mark → repeat."""
        # Set up tasks using split
        design_path = str(FIXTURES_DIR / "sample-design.md")
        run_script(
            "skills/task-splitter/scripts/split_tasks.py",
            design_path,
            cwd=str(work_dir),
        )

        # Log session start
        run_script(
            "scripts/progress.py",
            "append-structured",
            "--action", "session_start",
            "Auto-execute session started",
            cwd=str(work_dir),
        )

        completed_tasks = []
        for iteration in range(10):  # Safety limit
            # Step 1: Check context
            ctx = run_script("scripts/context_tracker.py", "check", cwd=str(work_dir))
            assert ctx["warning_level"] == "ok"  # Small tasks, should be fine

            # Step 2: Select next task
            result = run_script(
                "skills/executor/scripts/select_next.py",
                str(work_dir / "tasks.json"),
            )

            if result.get("status") == "all_complete":
                break

            assert "task" in result
            task_id = result["task"]["id"]

            # Step 3: Mark complete (simulating implementation)
            run_script(
                "skills/executor/scripts/mark_complete.py",
                task_id,
                "--commit-sha", f"commit_{task_id}",
                "--tests-written", "2",
                "--tests-passed", "2",
                cwd=str(work_dir),
            )
            completed_tasks.append(task_id)

        assert len(completed_tasks) == 3

        # Step 4: Generate summary
        summary = run_script("scripts/auto_summary.py", str(work_dir / "tasks.json"))
        assert summary["status"] == "all_complete"
        assert summary["tasks_completed"] == 3
        assert summary["total_tests_written"] == 6

        # Step 5: Dashboard
        dashboard = run_script("scripts/dashboard.py", "full", str(work_dir / "tasks.json"))
        assert "3/3" in dashboard["overall_progress"]
        assert dashboard["quality_metrics"]["total_tests_written"] == 6
