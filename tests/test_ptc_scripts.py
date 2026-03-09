"""Tests for all PTC scripts."""
import json
import shutil
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR, PROJECT_ROOT, run_script


# ─── scripts/progress.py ────────────────────────────────────────────────

class TestProgress:
    SCRIPT = "scripts/progress.py"

    def test_summary_on_empty(self, work_dir):
        result = run_script(self.SCRIPT, "summary", cwd=str(work_dir))
        assert result["count"] == 0
        assert result["first"] is None
        assert result["last"] is None

    def test_append_creates_entry(self, work_dir):
        result = run_script(self.SCRIPT, "append", "Test message", cwd=str(work_dir))
        assert "appended" in result
        assert "Test message" in result["appended"]
        # File should exist now
        assert (work_dir / "claude-progress.txt").exists()

    def test_read_after_appends(self, work_dir):
        run_script(self.SCRIPT, "append", "First", cwd=str(work_dir))
        run_script(self.SCRIPT, "append", "Second", cwd=str(work_dir))
        run_script(self.SCRIPT, "append", "Third", cwd=str(work_dir))
        result = run_script(self.SCRIPT, "read", cwd=str(work_dir))
        assert result["count"] == 3
        assert not result["truncated"]

    def test_read_last_truncates(self, work_dir):
        for i in range(5):
            run_script(self.SCRIPT, "append", f"Entry {i}", cwd=str(work_dir))
        result = run_script(self.SCRIPT, "read", "--last", "3", cwd=str(work_dir))
        assert result["count"] == 5
        assert result["truncated"] is True
        assert len(result["entries"]) == 3

    def test_summary_after_appends(self, work_dir):
        run_script(self.SCRIPT, "append", "Alpha", cwd=str(work_dir))
        run_script(self.SCRIPT, "append", "Beta", cwd=str(work_dir))
        result = run_script(self.SCRIPT, "summary", cwd=str(work_dir))
        assert result["count"] == 2
        assert "Alpha" in result["first"]
        assert "Beta" in result["last"]


# ─── scripts/progress.py (structured) ───────────────────────────────────

class TestProgressStructured:
    SCRIPT = "scripts/progress.py"

    def test_append_structured_creates_jsonl(self, work_dir):
        result = run_script(
            self.SCRIPT, "append-structured",
            "--action", "session_start",
            "Session started",
            cwd=str(work_dir),
        )
        assert "appended" in result
        assert result["appended"]["action"] == "session_start"
        assert (work_dir / "claude-progress.jsonl").exists()
        # Also writes to text log
        assert (work_dir / "claude-progress.txt").exists()

    def test_append_structured_with_task_id(self, work_dir):
        result = run_script(
            self.SCRIPT, "append-structured",
            "--action", "task_complete",
            "--task-id", "T001",
            "--phase", "execute",
            "--track", "2",
            "--details", '{"commit_sha": "abc123"}',
            "Completed T001",
            cwd=str(work_dir),
        )
        entry = result["appended"]
        assert entry["action"] == "task_complete"
        assert entry["task_id"] == "T001"
        assert entry["phase"] == "execute"
        assert entry["track"] == 2
        assert entry["details"]["commit_sha"] == "abc123"

    def test_append_structured_invalid_action(self, work_dir):
        result = run_script(
            self.SCRIPT, "append-structured",
            "--action", "invalid_action",
            "test",
            cwd=str(work_dir),
        )
        assert "error" in result

    def test_query_by_task_id(self, work_dir, sample_progress_jsonl):
        result = run_script(self.SCRIPT, "query", "--task-id", "T001", cwd=str(work_dir))
        assert result["count"] == 1
        assert result["entries"][0]["task_id"] == "T001"

    def test_query_by_action(self, work_dir, sample_progress_jsonl):
        result = run_script(self.SCRIPT, "query", "--action", "task_complete", cwd=str(work_dir))
        assert result["count"] == 2

    def test_query_by_since(self, work_dir, sample_progress_jsonl):
        result = run_script(self.SCRIPT, "query", "--since", "2026-03-08T10:06:00Z", cwd=str(work_dir))
        assert result["count"] == 1
        assert result["entries"][0]["task_id"] == "T002"

    def test_query_empty(self, work_dir):
        result = run_script(self.SCRIPT, "query", "--task-id", "T999", cwd=str(work_dir))
        assert result["count"] == 0


# ─── skills/small-fix/scripts/scope_check.py ────────────────────────────

class TestScopeCheck:
    SCRIPT = "skills/small-fix/scripts/scope_check.py"

    def test_small_fix_track1(self):
        result = run_script(self.SCRIPT, "fix broken button")
        assert result["scope"] == "track1"
        assert "fix" in result["fix_signals"] or "broken" in result["fix_signals"]

    def test_escalate_large_task(self):
        result = run_script(self.SCRIPT, "redesign the architecture")
        assert result["scope"] == "escalate"
        assert len(result["escalation_signals"]) > 0

    def test_mixed_signals_more_fix(self):
        result = run_script(self.SCRIPT, "fix a broken feature import")
        assert result["scope"] == "track1"
        assert len(result["fix_signals"]) >= len(result["escalation_signals"])


# ─── skills/small-fix/scripts/grep_context.py ───────────────────────────

class TestGrepContext:
    SCRIPT = "skills/small-fix/scripts/grep_context.py"

    def test_search_finds_matches(self, work_dir):
        # Create a searchable file
        (work_dir / "test.py").write_text("import json\nimport sys\n")
        result = run_script(self.SCRIPT, "import", "--pattern", "*.py", cwd=str(work_dir))
        assert len(result["results"]) == 1
        assert result["results"][0]["total"] > 0
        assert len(result["results"][0]["matches"]) > 0

    def test_search_no_results(self, work_dir):
        (work_dir / "test.py").write_text("hello world\n")
        result = run_script(self.SCRIPT, "xyznonexistent", cwd=str(work_dir))
        assert result["results"][0]["total"] == 0
        assert result["results"][0]["matches"] == []

    def test_truncation_at_10(self, work_dir):
        # Create a file with many matching lines
        lines = "\n".join(f"import mod{i}" for i in range(20))
        (work_dir / "big.py").write_text(lines)
        result = run_script(self.SCRIPT, "import", "--pattern", "*.py", cwd=str(work_dir))
        assert result["results"][0]["total"] == 20
        assert len(result["results"][0]["matches"]) == 10
        assert result["truncated"] is True


# ─── skills/researcher/scripts/search_local.py ──────────────────────────

class TestSearchLocal:
    SCRIPT = "skills/researcher/scripts/search_local.py"

    def test_search_with_files(self, work_dir):
        (work_dir / "hooks.py").write_text("# hooks integration\n")
        (work_dir / "config.py").write_text("# hooks config\n")
        result = run_script(self.SCRIPT, "hooks", cwd=str(work_dir))
        assert len(result["results"]) == 1
        r = result["results"][0]
        assert r["total_matches"] > 0
        assert r["total_files"] > 0
        assert len(r["files"]) > 0

    def test_multiple_terms(self, work_dir):
        (work_dir / "app.py").write_text("hooks\nPTC\n")
        result = run_script(self.SCRIPT, "hooks", "PTC", cwd=str(work_dir))
        assert len(result["results"]) == 2

    def test_pattern_filtering(self, work_dir):
        (work_dir / "code.py").write_text("hooks here\n")
        (work_dir / "readme.md").write_text("hooks there\n")
        result = run_script(self.SCRIPT, "hooks", "--pattern", "*.py", cwd=str(work_dir))
        # Should only find in .py file
        assert result["results"][0]["total_files"] == 1


# ─── skills/researcher/scripts/format_findings.py ───────────────────────

class TestFormatFindings:
    SCRIPT = "skills/researcher/scripts/format_findings.py"

    def test_valid_findings_writes_markdown(self, work_dir):
        findings = json.dumps({
            "key_findings": ["Auth uses JWT", "Sessions in Redis"],
            "files_examined": ["src/auth.py", "src/session.py"],
            "search_results": [{"term": "JWT", "total_matches": 5}],
            "open_questions": ["What about OAuth?"],
            "recommendation": "Use JWT with refresh tokens",
        })
        output_path = str(work_dir / "research" / "auth.md")
        result = run_script(
            self.SCRIPT,
            "--topic", "Authentication",
            "--output", output_path,
            "--findings", findings,
            cwd=str(work_dir),
        )
        assert result["written_to"] == output_path
        assert result["sections"] > 0
        assert result["word_count"] > 0
        assert Path(output_path).exists()
        content = Path(output_path).read_text()
        assert "Authentication" in content
        assert "JWT" in content

    def test_minimal_findings(self, work_dir):
        findings = json.dumps({"key_findings": ["One finding"]})
        output_path = str(work_dir / "out.md")
        result = run_script(
            self.SCRIPT,
            "--topic", "Test",
            "--output", output_path,
            "--findings", findings,
            cwd=str(work_dir),
        )
        assert result["written_to"] == output_path
        assert Path(output_path).exists()


# ─── skills/planner/scripts/validate_plan.py ────────────────────────────

class TestValidatePlan:
    SCRIPT = "skills/planner/scripts/validate_plan.py"

    def test_valid_design(self):
        result = run_script(self.SCRIPT, str(FIXTURES_DIR / "sample-design.md"))
        assert result["valid"] is True
        assert result["annotation_count"] == 2
        assert result["task_count"] >= 3
        assert len(result["missing_sections"]) == 0

    def test_missing_sections(self, work_dir):
        design = work_dir / "incomplete.md"
        design.write_text("# Design\n\n## Problem Statement\n\nSome problem.\n")
        result = run_script(self.SCRIPT, str(design))
        assert result["valid"] is False
        assert len(result["missing_sections"]) > 0

    def test_nonexistent_file(self):
        result = run_script(self.SCRIPT, "/nonexistent/design.md")
        assert result["valid"] is False
        assert "error" in result

    def test_diff_mode(self):
        result = run_script(
            self.SCRIPT,
            str(FIXTURES_DIR / "sample-design.md"),
            "--diff",
            str(FIXTURES_DIR / "sample-design-v2.md"),
        )
        assert "design1" in result
        assert "design2" in result
        assert "annotation_count_delta" in result
        assert "task_count_delta" in result

    def test_diff_nonexistent(self):
        result = run_script(
            self.SCRIPT,
            str(FIXTURES_DIR / "sample-design.md"),
            "--diff",
            "/nonexistent/design.md",
        )
        assert "error" in result


# ─── skills/task-splitter/scripts/split_tasks.py ────────────────────────

class TestSplitTasks:
    SCRIPT = "skills/task-splitter/scripts/split_tasks.py"

    def test_annotated_design_generates_tasks(self, work_dir):
        design_path = FIXTURES_DIR / "sample-design.md"
        result = run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        assert "error" not in result
        assert result["tasks_generated"] == 3
        assert result["total_annotations"] == 2
        assert "S" in result["scopes"]
        # tasks.json should be created in work_dir
        assert (work_dir / "tasks.json").exists()

    def test_no_annotations_error(self, work_dir):
        design_path = FIXTURES_DIR / "sample-design-no-annotations.md"
        result = run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        assert "error" in result
        assert "annotation" in result["error"].lower()
        assert "hint" in result

    def test_nonexistent_file(self, work_dir):
        result = run_script(self.SCRIPT, "/nonexistent/design.md", cwd=str(work_dir))
        assert "error" in result

    def test_v2_output_schema_version(self, work_dir):
        """Verify split produces schema_version 2 output."""
        design_path = FIXTURES_DIR / "sample-design.md"
        result = run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        assert result["schema_version"] == "2"
        assert result["plan_version"] == 1
        # Check tasks.json content
        data = json.loads((work_dir / "tasks.json").read_text())
        assert data["schema_version"] == "2"
        assert data["plan_version"] == 1
        assert len(data["plan_history"]) == 1

    def test_v2_estimated_minutes(self, work_dir):
        """Verify tasks have estimated_minutes based on scope."""
        design_path = FIXTURES_DIR / "sample-design.md"
        run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        data = json.loads((work_dir / "tasks.json").read_text())
        for task in data["tasks"]:
            assert "estimated_minutes" in task
            if task["scope"] == "S":
                assert task["estimated_minutes"] == 15
            elif task["scope"] == "M":
                assert task["estimated_minutes"] == 60

    def test_v2_files_populated(self, work_dir):
        """Verify file changes from design are mapped to tasks."""
        design_path = FIXTURES_DIR / "sample-design-v2.md"
        result = run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        assert result["file_changes_found"] > 0
        assert result["files_populated"] > 0
        data = json.loads((work_dir / "tasks.json").read_text())
        files_with_content = [t for t in data["tasks"] if t["files"]]
        assert len(files_with_content) > 0

    def test_resplit_increments_plan_version(self, work_dir):
        """Verify re-split increments plan_version and preserves completed."""
        design_path = FIXTURES_DIR / "sample-design.md"
        # First split
        run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        # Mark T001 as completed
        data = json.loads((work_dir / "tasks.json").read_text())
        data["tasks"][0]["status"] = "completed"
        data["tasks"][0]["commit_sha"] = "abc123"
        (work_dir / "tasks.json").write_text(json.dumps(data))
        # Re-split
        result = run_script(self.SCRIPT, str(design_path), cwd=str(work_dir))
        assert result["plan_version"] == 2
        # Check completed task preserved
        data = json.loads((work_dir / "tasks.json").read_text())
        assert data["plan_version"] == 2
        assert len(data["plan_history"]) == 2
        assert data["tasks"][0]["status"] == "completed"
        assert data["tasks"][0]["commit_sha"] == "abc123"


# ─── skills/task-splitter/scripts/validate_tasks.py ─────────────────────

class TestValidateTasks:
    SCRIPT = "skills/task-splitter/scripts/validate_tasks.py"

    def test_valid_tasks(self, sample_tasks_json):
        result = run_script(self.SCRIPT, str(sample_tasks_json))
        assert result["valid"] is True
        assert result["task_count"] == 3
        assert result["status_counts"]["pending"] == 3

    def test_invalid_id_format(self, work_dir):
        data = {
            "design": "d.md",
            "tasks": [{
                "id": "BADID",
                "title": "Test",
                "scope": "S",
                "status": "pending",
                "files": [],
                "verification": {"command": "echo ok", "expected": "ok"},
            }],
        }
        path = work_dir / "tasks.json"
        path.write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(path))
        assert result["valid"] is False
        assert any("invalid ID" in issue for issue in result["issues"])

    def test_empty_tasks(self, empty_tasks_json):
        result = run_script(self.SCRIPT, str(empty_tasks_json))
        assert result["valid"] is False
        assert any("No tasks" in issue for issue in result["issues"])

    def test_duplicate_ids(self, work_dir):
        data = {
            "design": "d.md",
            "tasks": [
                {"id": "T001", "title": "A", "scope": "S", "status": "pending",
                 "files": [], "verification": {"command": "x", "expected": "y"}},
                {"id": "T001", "title": "B", "scope": "S", "status": "pending",
                 "files": [], "verification": {"command": "x", "expected": "y"}},
            ],
        }
        path = work_dir / "tasks.json"
        path.write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(path))
        assert result["valid"] is False
        assert any("duplicate" in issue.lower() for issue in result["issues"])

    def test_v2_todo_verification_warning(self, work_dir):
        """Warn when verification commands contain TODO placeholders."""
        data = {
            "schema_version": "2",
            "design": "d.md",
            "tasks": [{
                "id": "T001", "title": "Test", "scope": "S", "status": "pending",
                "files": [], "verification": {
                    "command": "echo 'TODO: add verification command'",
                    "expected": "TODO: define expected output",
                },
            }],
        }
        path = work_dir / "tasks.json"
        path.write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(path))
        assert result["valid"] is True  # TODOs are warnings, not errors
        assert len(result["warnings"]) >= 2
        assert any("TODO" in w for w in result["warnings"])

    def test_v2_empty_files_warning(self, work_dir):
        """Warn on empty files arrays."""
        data = {
            "schema_version": "2",
            "design": "d.md",
            "tasks": [{
                "id": "T001", "title": "Test", "scope": "S", "status": "pending",
                "files": [], "verification": {"command": "pytest", "expected": "passed"},
            }],
        }
        path = work_dir / "tasks.json"
        path.write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(path))
        assert any("files array is empty" in w for w in result["warnings"])

    def test_v2_quality_metrics(self, sample_tasks_v2_json):
        """Verify quality metrics in v2 output."""
        result = run_script(self.SCRIPT, str(sample_tasks_v2_json))
        assert result["schema_version"] == "2"
        assert "quality_metrics" in result
        assert result["quality_metrics"]["tasks_with_timing"] >= 1
        assert result["quality_metrics"]["tasks_with_tests"] >= 1


# ─── skills/executor/scripts/select_next.py ─────────────────────────────

class TestSelectNext:
    SCRIPT = "skills/executor/scripts/select_next.py"

    def test_picks_first_pending(self, sample_tasks_json):
        result = run_script(self.SCRIPT, str(sample_tasks_json))
        assert "task" in result
        assert result["task"]["id"] == "T001"
        assert result["progress"]["total"] == 3

    def test_all_complete(self, work_dir):
        data = {
            "design": "d.md",
            "tasks": [
                {"id": "T001", "title": "Done", "scope": "S", "status": "completed",
                 "files": [], "verification": {"command": "x", "expected": "y"}},
            ],
        }
        (work_dir / "tasks.json").write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(work_dir / "tasks.json"))
        assert result["status"] == "all_complete"

    def test_no_file_error(self, work_dir):
        result = run_script(self.SCRIPT, str(work_dir / "tasks.json"))
        assert "error" in result

    def test_blocked_dependencies(self, work_dir):
        data = {
            "design": "d.md",
            "tasks": [
                {"id": "T001", "title": "A", "scope": "S", "status": "in_progress",
                 "depends_on": [], "files": [], "verification": {"command": "x", "expected": "y"}},
                {"id": "T002", "title": "B", "scope": "S", "status": "pending",
                 "depends_on": ["T001"], "files": [], "verification": {"command": "x", "expected": "y"}},
            ],
        }
        (work_dir / "tasks.json").write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(work_dir / "tasks.json"))
        assert result["status"] == "blocked"
        assert "T002" in result["blocked_tasks"]

    def test_sets_started_at_and_in_progress(self, sample_tasks_json):
        """Verify select_next sets started_at and status to in_progress."""
        result = run_script(self.SCRIPT, str(sample_tasks_json))
        assert result["task"]["id"] == "T001"
        # Read back tasks.json to verify
        data = json.loads(sample_tasks_json.read_text())
        task = data["tasks"][0]
        assert task["status"] == "in_progress"
        assert "started_at" in task
        assert task["started_at"] is not None

    def test_estimated_minutes_in_output(self, work_dir):
        """Verify estimated_minutes is included in output."""
        data = {
            "design": "d.md",
            "tasks": [{
                "id": "T001", "title": "A", "scope": "S", "status": "pending",
                "depends_on": [], "files": [], "verification": {"command": "x", "expected": "y"},
                "estimated_minutes": 15,
            }],
        }
        (work_dir / "tasks.json").write_text(json.dumps(data))
        result = run_script(self.SCRIPT, str(work_dir / "tasks.json"))
        assert result["task"]["estimated_minutes"] == 15


# ─── skills/executor/scripts/mark_complete.py ───────────────────────────

class TestMarkComplete:
    SCRIPT = "skills/executor/scripts/mark_complete.py"

    def test_marks_task_complete(self, sample_tasks_json, work_dir):
        result = run_script(self.SCRIPT, "T001", cwd=str(work_dir))
        assert result["marked_complete"] == "T001"
        assert result["remaining"] == 2
        # Verify tasks.json updated
        data = json.loads(sample_tasks_json.read_text())
        assert data["tasks"][0]["status"] == "completed"
        # Verify progress log
        assert (work_dir / "claude-progress.txt").exists()

    def test_already_completed_warning(self, sample_tasks_json, work_dir):
        run_script(self.SCRIPT, "T001", cwd=str(work_dir))
        result = run_script(self.SCRIPT, "T001", cwd=str(work_dir))
        assert "warning" in result

    def test_unknown_id_error(self, sample_tasks_json, work_dir):
        result = run_script(self.SCRIPT, "T999", cwd=str(work_dir))
        assert "error" in result

    def test_commit_sha_recorded(self, sample_tasks_json, work_dir):
        result = run_script(self.SCRIPT, "T001", "--commit-sha", "abc123", cwd=str(work_dir))
        assert result["commit_sha"] == "abc123"
        data = json.loads(sample_tasks_json.read_text())
        assert data["tasks"][0]["commit_sha"] == "abc123"

    def test_duration_calculated(self, work_dir):
        """Verify duration_seconds is calculated from started_at."""
        data = {
            "design": "d.md",
            "tasks": [{
                "id": "T001", "title": "Test", "scope": "S", "status": "in_progress",
                "depends_on": [], "files": [],
                "verification": {"command": "x", "expected": "y"},
                "started_at": "2026-03-08T10:00:00+00:00",
            }],
        }
        (work_dir / "tasks.json").write_text(json.dumps(data))
        result = run_script(self.SCRIPT, "T001", cwd=str(work_dir))
        assert result["duration_seconds"] is not None
        assert result["duration_seconds"] > 0

    def test_attempt_count_incremented(self, sample_tasks_json, work_dir):
        """Verify attempt_count is incremented."""
        result = run_script(self.SCRIPT, "T001", cwd=str(work_dir))
        assert result["attempt_count"] == 1
        data = json.loads(sample_tasks_json.read_text())
        assert data["tasks"][0]["attempt_count"] == 1
        assert len(data["tasks"][0]["retry_history"]) == 1
        assert data["tasks"][0]["retry_history"][0]["outcome"] == "success"

    def test_tests_and_cove_recorded(self, sample_tasks_json, work_dir):
        """Verify test counts and cove findings are recorded."""
        result = run_script(
            self.SCRIPT, "T001",
            "--tests-written", "5",
            "--tests-passed", "4",
            "--cove-findings", '["Edge case: null input not handled"]',
            cwd=str(work_dir),
        )
        assert result["tests_written"] == 5
        assert result["tests_passed"] == 4
        data = json.loads(sample_tasks_json.read_text())
        assert data["tasks"][0]["tests_written"] == 5
        assert data["tasks"][0]["tests_passed"] == 4
        assert len(data["tasks"][0]["cove_findings"]) == 1

    def test_structured_progress_entry(self, sample_tasks_json, work_dir):
        """Verify structured JSONL entry is written."""
        run_script(self.SCRIPT, "T001", "--commit-sha", "xyz789", cwd=str(work_dir))
        assert (work_dir / "claude-progress.jsonl").exists()
        lines = (work_dir / "claude-progress.jsonl").read_text().strip().split("\n")
        entry = json.loads(lines[-1])
        assert entry["action"] == "task_complete"
        assert entry["task_id"] == "T001"
        assert entry["details"]["commit_sha"] == "xyz789"


# ─── scripts/context_tracker.py ─────────────────────────────────────────

class TestContextTracker:
    SCRIPT = "scripts/context_tracker.py"

    def test_estimate_empty(self, work_dir):
        result = run_script(self.SCRIPT, "estimate", cwd=str(work_dir))
        assert result["estimated_tokens"] >= 3000  # base overhead
        assert result["tasks_this_session"] == 0

    def test_check_ok_level(self, work_dir):
        result = run_script(self.SCRIPT, "check", cwd=str(work_dir))
        assert result["warning_level"] == "ok"
        assert result["recommendation"] is None

    def test_estimate_with_progress(self, work_dir, sample_progress_jsonl):
        result = run_script(self.SCRIPT, "estimate", cwd=str(work_dir))
        assert result["tasks_this_session"] == 2
        assert result["estimated_tokens"] > 3000

    def test_check_warning_levels(self, work_dir):
        """Verify warning thresholds work correctly."""
        # Create a JSONL with many task completions to push utilization up
        jsonl_path = work_dir / "claude-progress.jsonl"
        entries = [{"timestamp": "2026-03-08T10:00:00Z", "action": "session_start", "message": "Start"}]
        # Add enough L-scope task completions to push over 50%
        tasks_data = {"design": "d.md", "tasks": []}
        for i in range(5):
            tid = f"T{i+1:03d}"
            entries.append({
                "timestamp": f"2026-03-08T1{i}:00:00Z",
                "action": "task_complete",
                "task_id": tid,
                "message": f"Completed {tid}",
            })
            tasks_data["tasks"].append({
                "id": tid, "title": f"Task {i}", "scope": "L",
                "status": "completed", "files": [],
                "verification": {"command": "x", "expected": "y"},
            })

        with open(jsonl_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
        (work_dir / "tasks.json").write_text(json.dumps(tasks_data))

        result = run_script(self.SCRIPT, "check", cwd=str(work_dir))
        # 5 L-scope tasks = 150k tokens + overhead → should be warning or critical
        assert result["warning_level"] in ("warning", "critical")
        assert result["recommendation"] is not None


# ─── scripts/dashboard.py ───────────────────────────────────────────────

class TestDashboard:
    SCRIPT = "scripts/dashboard.py"

    def test_full_dashboard(self, sample_tasks_v2_json):
        result = run_script(self.SCRIPT, "full", str(sample_tasks_v2_json))
        assert "dependency_graph_mermaid" in result
        assert "progress_bars" in result
        assert "quality_metrics" in result
        assert "velocity" in result
        assert "overall_progress" in result
        assert "graph TD" in result["dependency_graph_mermaid"]

    def test_graph_only(self, sample_tasks_v2_json):
        result = run_script(self.SCRIPT, "graph", str(sample_tasks_v2_json))
        assert "dependency_graph_mermaid" in result
        assert "T001" in result["dependency_graph_mermaid"]

    def test_velocity(self, sample_tasks_v2_json):
        result = run_script(self.SCRIPT, "velocity", str(sample_tasks_v2_json))
        assert "velocity" in result
        assert result["velocity"]["completed_count"] == 1
        assert result["velocity"]["remaining_count"] == 2

    def test_progress_bars(self, sample_tasks_v2_json):
        result = run_script(self.SCRIPT, "full", str(sample_tasks_v2_json))
        bars = result["progress_bars"]
        assert len(bars) == 3
        completed_bar = next(b for b in bars if b["id"] == "T001")
        assert completed_bar["percent"] == 100
        pending_bar = next(b for b in bars if b["id"] == "T003")
        assert pending_bar["percent"] == 0

    def test_no_file_error(self, work_dir):
        result = run_script(self.SCRIPT, "full", str(work_dir / "nonexistent.json"))
        assert "error" in result


# ─── scripts/auto_summary.py ────────────────────────────────────────────

class TestAutoSummary:
    SCRIPT = "scripts/auto_summary.py"

    def test_summary_with_completed_tasks(self, sample_tasks_v2_json, work_dir):
        # Mark all tasks complete in the fixture
        data = json.loads(sample_tasks_v2_json.read_text())
        for task in data["tasks"]:
            task["status"] = "completed"
            task["duration_seconds"] = 600
            task["attempt_count"] = 1
            task["tests_written"] = 3
            task["tests_passed"] = 3
        sample_tasks_v2_json.write_text(json.dumps(data))

        result = run_script(self.SCRIPT, str(sample_tasks_v2_json))
        assert result["status"] == "all_complete"
        assert result["tasks_completed"] == 3
        assert result["total_duration_seconds"] > 0
        assert result["total_tests_written"] == 9

    def test_summary_no_file(self, work_dir):
        result = run_script(self.SCRIPT, str(work_dir / "tasks.json"))
        assert "error" in result


# ─── scripts/migrate_tasks.py ───────────────────────────────────────────

class TestMigrateTasks:
    SCRIPT = "scripts/migrate_tasks.py"

    def test_migrate_v1_to_v2(self, sample_tasks_json):
        """Migrate a v1 tasks.json to v2."""
        result = run_script(self.SCRIPT, str(sample_tasks_json))
        assert result["status"] == "migrated"
        assert result["schema_version"] == "2"
        assert result["tasks_migrated"] == 3
        # Verify file content
        data = json.loads(sample_tasks_json.read_text())
        assert data["schema_version"] == "2"
        for task in data["tasks"]:
            assert "attempt_count" in task
            assert "retry_history" in task
            assert "cove_findings" in task
            assert "estimated_minutes" in task

    def test_migrate_already_v2(self, sample_tasks_v2_json):
        """Already v2 should be a no-op."""
        result = run_script(self.SCRIPT, str(sample_tasks_v2_json))
        assert result["status"] == "already_v2"

    def test_migrate_no_file(self, work_dir):
        result = run_script(self.SCRIPT, str(work_dir / "tasks.json"))
        assert "error" in result


# ─── scripts/plan_diff.py ───────────────────────────────────────────────

class TestPlanDiff:
    SCRIPT = "scripts/plan_diff.py"

    def test_diff_two_designs(self):
        result = run_script(
            self.SCRIPT,
            str(FIXTURES_DIR / "sample-design.md"),
            str(FIXTURES_DIR / "sample-design-v2.md"),
        )
        assert "sections_changed" in result
        assert "annotation_count_delta" in result
        assert result["annotation_count_delta"] == 1  # v2 has 3, v1 has 2
        assert "task_count_delta" in result

    def test_diff_same_file(self):
        result = run_script(
            self.SCRIPT,
            str(FIXTURES_DIR / "sample-design.md"),
            str(FIXTURES_DIR / "sample-design.md"),
        )
        assert result["annotation_count_delta"] == 0
        assert result["task_count_delta"] == 0
        assert len(result["sections_changed"]) == 0

    def test_diff_nonexistent(self):
        result = run_script(
            self.SCRIPT,
            str(FIXTURES_DIR / "sample-design.md"),
            "/nonexistent/design.md",
        )
        assert "error" in result


# ─── skills/prompt-enhancer/scripts/enhance.py ──────────────────────────

class TestEnhance:
    SCRIPT = "skills/prompt-enhancer/scripts/enhance.py"

    def test_analyze_weak_prompt(self):
        result = run_script(self.SCRIPT, "analyze", "Write code")
        assert result["has_role"] is False
        assert result["has_examples"] is False
        assert len(result["suggestions"]) > 0

    def test_analyze_strong_prompt(self):
        result = run_script(
            self.SCRIPT, "analyze",
            "You are a senior engineer. Write a function that validates email addresses. "
            "Return as JSON with keys: valid, reason."
        )
        assert result["has_role"] is True
        assert result["has_output_format"] is True

    def test_format_comparison(self):
        result = run_script(
            self.SCRIPT, "format",
            "--original", "Write code",
            "--enhanced", "You are a senior engineer. Write a Python function. Return as JSON.",
        )
        assert "original" in result
        assert "enhanced" in result
        assert "improvements" in result
        assert result["specificity_delta"] >= 0


# ─── skills/skill-factory/scripts/scaffold_skill.py ─────────────────────

class TestScaffoldSkill:
    SCRIPT = "skills/skill-factory/scripts/scaffold_skill.py"

    def test_track1_scaffold(self, work_dir):
        # The script creates under skills/ relative to cwd
        result = run_script(self.SCRIPT, "--name", "test-skill", "--track", "1", cwd=str(work_dir))
        assert "error" not in result
        assert (work_dir / "skills" / "test-skill" / "SKILL.md").exists()
        assert (work_dir / "skills" / "test-skill" / "scripts").is_dir()
        assert not (work_dir / "skills" / "test-skill" / "references").exists()

    def test_track2_scaffold(self, work_dir):
        result = run_script(self.SCRIPT, "--name", "research-skill", "--track", "2", cwd=str(work_dir))
        assert "error" not in result
        assert result["track"] == 2
        assert (work_dir / "skills" / "research-skill" / "references").is_dir()

    def test_existing_dir_error(self, work_dir):
        (work_dir / "skills" / "existing").mkdir(parents=True)
        result = run_script(self.SCRIPT, "--name", "existing", "--track", "1", cwd=str(work_dir))
        assert "error" in result
