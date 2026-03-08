"""Tests for plugin structural integrity."""
import json
import py_compile
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT


class TestPluginManifest:

    def test_plugin_json_exists(self):
        assert (PROJECT_ROOT / ".claude-plugin" / "plugin.json").exists()

    def test_plugin_json_has_required_fields(self):
        data = json.loads((PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text())
        assert "name" in data
        assert "version" in data
        assert "description" in data


class TestCommands:
    EXPECTED_COMMANDS = [
        "fix", "research", "plan", "split", "execute",
        "new-skill", "handoff", "status", "verify",
    ]

    def test_all_command_files_exist(self):
        for cmd in self.EXPECTED_COMMANDS:
            path = PROJECT_ROOT / "commands" / f"{cmd}.md"
            assert path.exists(), f"Missing command file: {path}"


class TestSkills:
    EXPECTED_SKILLS = [
        "small-fix", "prompt-enhancer", "skill-factory",
        "researcher", "planner", "task-splitter", "executor",
    ]

    def test_all_skill_md_files_exist(self):
        for skill in self.EXPECTED_SKILLS:
            path = PROJECT_ROOT / "skills" / skill / "SKILL.md"
            assert path.exists(), f"Missing SKILL.md: {path}"

    def test_skill_md_has_yaml_frontmatter(self):
        for skill in self.EXPECTED_SKILLS:
            path = PROJECT_ROOT / "skills" / skill / "SKILL.md"
            content = path.read_text()
            assert content.startswith("---"), f"{skill}/SKILL.md missing YAML frontmatter"
            # Extract frontmatter
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{skill}/SKILL.md has malformed frontmatter"
            fm = yaml.safe_load(parts[1])
            assert "name" in fm, f"{skill}/SKILL.md frontmatter missing 'name'"
            assert "description" in fm, f"{skill}/SKILL.md frontmatter missing 'description'"
            assert "tools" in fm, f"{skill}/SKILL.md frontmatter missing 'tools'"


class TestPTCScripts:
    PTC_SCRIPTS = [
        "scripts/progress.py",
        "skills/small-fix/scripts/scope_check.py",
        "skills/small-fix/scripts/grep_context.py",
        "skills/researcher/scripts/search_local.py",
        "skills/researcher/scripts/format_findings.py",
        "skills/planner/scripts/validate_plan.py",
        "skills/task-splitter/scripts/split_tasks.py",
        "skills/task-splitter/scripts/validate_tasks.py",
        "skills/executor/scripts/select_next.py",
        "skills/executor/scripts/mark_complete.py",
        "skills/prompt-enhancer/scripts/enhance.py",
        "skills/skill-factory/scripts/scaffold_skill.py",
    ]

    def test_all_scripts_are_valid_python(self):
        for script in self.PTC_SCRIPTS:
            path = PROJECT_ROOT / script
            assert path.exists(), f"Missing script: {path}"
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Syntax error in {script}: {e}")


class TestClaudeMd:

    def test_claude_md_exists(self):
        assert (PROJECT_ROOT / "CLAUDE.md").exists()
