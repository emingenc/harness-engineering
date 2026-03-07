---
description: "Write a structured handoff document for context transfer between sessions"
allowed-tools:
  - Read
  - Glob
  - Write
  - Bash(python3 scripts/*.py:*)
  - Bash(python3 skills/executor/scripts/select_next.py:*)
---

# /handoff — Context Transfer

Generate a structured handoff document for session transfer.

## Process

1. **Gather state**:
   - Read `claude-progress.txt` (last 10 entries)
   - Read `tasks.json` status summary
   - Check git status for uncommitted changes
   - Note current working task (if any)

2. **Write handoff** to `workspace/handoff-<timestamp>.md`:

```markdown
# Handoff: <timestamp>

## Current State
- Active task: <task_id> or "none"
- Tasks completed: X/Y
- Uncommitted changes: yes/no

## Decisions Made This Session
- [List key decisions]

## What Was Tried
- [List attempts, especially if 2-Pass Rule triggered]

## Remaining Work
- [Next task from tasks.json]
- [Open questions]

## Files Modified
- [List of changed files]

## Resumption Instructions
1. Read this handoff document
2. Read claude-progress.txt (last 5 entries)
3. Run select_next.py to find next task
4. Continue from where we left off
```

3. **Log**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Handoff written: workspace/handoff-<timestamp>.md"
   ```

4. Tell the user: "Handoff written. Safe to clear context. Next session: read the handoff document first."
