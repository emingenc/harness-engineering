"""Tests for hooks.json validation."""
import json
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT

HOOKS_PATH = PROJECT_ROOT / "hooks" / "hooks.json"


@pytest.fixture
def hooks_data():
    return json.loads(HOOKS_PATH.read_text())


class TestHooksStructure:

    def test_is_valid_json(self):
        data = json.loads(HOOKS_PATH.read_text())
        assert isinstance(data, dict)

    def test_has_description(self, hooks_data):
        assert "description" in hooks_data

    def test_all_four_hook_types_present(self, hooks_data):
        hooks = hooks_data["hooks"]
        expected = {"Stop", "SessionStart", "UserPromptSubmit", "PreCompact"}
        assert set(hooks.keys()) == expected

    def test_each_hook_has_matcher_and_hooks(self, hooks_data):
        for hook_type, entries in hooks_data["hooks"].items():
            assert isinstance(entries, list), f"{hook_type} should be an array"
            for entry in entries:
                assert "matcher" in entry, f"{hook_type} entry missing 'matcher'"
                assert "hooks" in entry, f"{hook_type} entry missing 'hooks'"
                assert isinstance(entry["hooks"], list)

    def test_each_hook_entry_has_type(self, hooks_data):
        for hook_type, entries in hooks_data["hooks"].items():
            for entry in entries:
                for hook in entry["hooks"]:
                    assert "type" in hook, f"{hook_type} hook missing 'type'"
                    assert hook["type"] in ("command", "prompt"), (
                        f"{hook_type} hook has invalid type: {hook['type']}"
                    )
                    if hook["type"] == "command":
                        assert "command" in hook, f"command hook missing 'command' field"
                    else:
                        assert "prompt" in hook, f"prompt hook missing 'prompt' field"

    def test_timeouts_are_valid(self, hooks_data):
        for hook_type, entries in hooks_data["hooks"].items():
            for entry in entries:
                for hook in entry["hooks"]:
                    if "timeout" in hook:
                        assert isinstance(hook["timeout"], int)
                        assert 0 < hook["timeout"] <= 30, (
                            f"{hook_type} timeout {hook['timeout']} out of range (1-30)"
                        )
