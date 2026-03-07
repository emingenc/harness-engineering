---
name: small-fix
description: >-
  Apply surgical fixes to codebases. Use when the user says "fix this bug",
  "quick fix", "small change", "patch this", "update this config",
  or describes a problem that can be solved by modifying 1-3 files.
  Do NOT use for features requiring design docs or multi-step planning.
tools: Read, Glob, Grep, Edit, Write, Bash
---

# Small Fix (Track 1)

## When to Use

- Bug fixes affecting 1-3 files
- Config changes
- Small refactors
- One-file features
- Typo fixes, import corrections

## When NOT to Use

- Feature requires >3 files changed -> escalate to Track 2
- Unclear scope -> ask clarifying questions first
- Requires research phase -> use `/research` instead

## Process

### Step 1: Scope Check

Run scope check to validate this is truly a small fix:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/small-fix/scripts/scope_check.py "<description>"
```

If scope is `escalate`, tell the user: "This looks larger than a Track 1 fix. Consider using `/plan` for a Track 2 approach."

### Step 2: Search for Context

Use PTC script to find relevant code:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/small-fix/scripts/grep_context.py <search_terms>
```

Read only the files indicated by the JSON summary. Do NOT read unrelated files.

### Step 3: Implement Fix

1. Read the specific files identified in Step 2
2. Understand the existing code before modifying
3. Make the minimal change needed
4. Do not refactor surrounding code
5. Do not add features beyond what was requested

### Step 4: Verify

Run relevant tests if they exist. If no tests exist for the changed code, note this to the user but do not create tests unless asked.

### Step 5: Report

Summarize:
- What was changed and why
- Files modified
- Any risks or follow-up items

## Examples

### Example 1: Import Fix

**Input**: "Fix the missing import error in auth.py"
**Process**: grep_context.py "import" "auth.py" -> Read auth.py -> Add missing import -> Run tests
**Output**: "Added `from utils import validate_token` to `auth.py:3`. The function was referenced at line 47 but never imported."

### Example 2: Config Update

**Input**: "Change the timeout from 30s to 60s"
**Process**: grep_context.py "timeout" "30" -> Read config file -> Edit value -> Verify
**Output**: "Updated `config/settings.yaml:12` timeout from 30 to 60."

## Anti-Patterns

- Do NOT read the entire codebase to understand a simple fix
- Do NOT refactor code adjacent to the fix
- Do NOT add error handling "while you're in there"
- Do NOT create new files unless the fix specifically requires it
