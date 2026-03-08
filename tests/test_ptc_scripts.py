"""Tests for all 12 PTC scripts."""
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
