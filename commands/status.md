---
description: "Show progress overview: tasks, sessions, and state"
allowed-tools:
  - Read
  - Bash(python3 scripts/*.py:*)
  - Bash(python3 skills/executor/scripts/select_next.py:*)
  - Bash(python3 skills/task-splitter/scripts/validate_tasks.py:*)
---

# /status — Progress Overview

Gather and display current workflow state.

## Process

1. **Progress log**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py summary
   ```

2. **Task status** (if tasks.json exists):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/task-splitter/scripts/validate_tasks.py
   ```

3. **Next task** (if tasks exist):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/select_next.py
   ```

4. **Recent progress**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py read --last 5
   ```

5. **Present** a summary table:

```
## Status Overview

| Metric | Value |
|--------|-------|
| Tasks completed | X/Y |
| Next task | TXXX: title |
| Progress entries | N |
| Last activity | timestamp |

### Recent Activity
- [last 5 progress entries]
```
