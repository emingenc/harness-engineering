---
description: "Track 1: Apply a surgical fix to the codebase"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash(python3 skills/small-fix/scripts/*.py:*)
  - Bash(python3 scripts/*.py:*)
---

# /fix — Track 1 Surgical Fix

You have been asked to apply a small, surgical fix: **$1**

## Process

1. **Scope check**: Run the scope check PTC script:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/small-fix/scripts/scope_check.py "$1"
   ```
   If `scope` is `escalate`, tell the user this is too large for Track 1 and suggest `/plan` instead. STOP.

2. **Search context**: Use the grep PTC script to find relevant code:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/small-fix/scripts/grep_context.py <relevant_search_terms>
   ```

3. **Read** only the files indicated by the search results.

4. **Implement** the minimal fix needed. Do not refactor surrounding code.

5. **Verify** by running existing tests if available.

6. **Report** what was changed, which files were modified, and any follow-up items.

7. **Log** the fix to progress:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Track 1 fix: $1"
   ```

## Rules

- Maximum 3 files modified
- No new features beyond the fix
- No unnecessary refactoring
- If stuck after 2 attempts, invoke the 2-Pass Rule (see CLAUDE.md)
