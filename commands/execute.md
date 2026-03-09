---
description: "Track 2 Phase 4: Execute one micro-task from tasks.json with TDD"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - Bash(python3 skills/executor/scripts/*.py:*)
  - Bash(python3 scripts/*.py:*)
---

# /execute — Track 2 Execution

Follow the executor skill workflow exactly:

1. **Check context budget**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_tracker.py check
   ```
   If `warning_level` is `warning` or `critical` → **STOP**: "Context budget at {utilization_percent}%. Recommend running /handoff before continuing."

2. **Select next task**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/select_next.py
   ```
   If no tasks available, tell the user. If all complete, congratulate.

3. **Read task context** — only files listed in the task's `files` array.

4. **TDD Gate**:
   - Write failing tests FIRST
   - Run tests — must FAIL
   - For M/L scope: show tests to user, wait for validation
   - For S scope: proceed automatically
   - Implement until tests pass

5. **Chain of Verification (CoVe)**:
   - Does this handle edge cases?
   - Is this consistent with existing patterns?
   - Does this break existing tests?
   - Security concerns?
   - Fix any issues found.

6. **Mark complete**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/mark_complete.py \
     <task_id> --commit-sha <sha>
   ```

7. **Report** what was done and suggest: "Context can be safely cleared. Run `/execute` for the next task."

## 2-Pass Rule

If tests don't pass after 2 attempts:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "2-Pass limit on <task_id>: <details>"
```
STOP and recommend context clear.
