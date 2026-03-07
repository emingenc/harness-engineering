---
description: "Run verification suite: structural checks, schema validation, and integrity"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(python3 skills/task-splitter/scripts/validate_tasks.py:*)
  - Bash(python3 skills/planner/scripts/validate_plan.py:*)
  - Bash(wc -l:*)
---

# /verify — Verification Suite

Run structural and integrity checks on the plugin.

## Checks

### 1. CLAUDE.md Line Count
```bash
wc -l CLAUDE.md
```
Must be under 150 lines. If over, identify what can move to docs/.

### 2. Skill Frontmatter Validity
For each skill, verify SKILL.md has valid YAML frontmatter with:
- `name` (kebab-case)
- `description` (non-empty, includes trigger phrases)
- `tools` (non-empty)

Use Glob to find all `skills/*/SKILL.md` and Read each one's first 10 lines.

### 3. tasks.json Schema Compliance
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/task-splitter/scripts/validate_tasks.py
```

### 4. Plugin Manifest
Read `.claude-plugin/plugin.json` and verify:
- `name` field exists
- `version` follows semver
- `description` is non-empty

### 5. Design Document Integrity (if any exist)
For each `workspace/designs/*-design.md`:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planner/scripts/validate_plan.py \
  "workspace/designs/<name>-design.md"
```

### 6. File Integrity
Check that all referenced paths in CLAUDE.md actually exist:
- docs/*.md files
- docs/templates/* files
- scripts/*.py files

## Report

Present results as a checklist:
```
## Verification Results

- [x] CLAUDE.md: 87 lines (under 150)
- [x] Skills: 7/7 have valid frontmatter
- [x] tasks.json: valid (0 tasks)
- [x] plugin.json: valid
- [ ] Design docs: none found (OK if not in Track 2)
- [x] File integrity: all references valid
```
