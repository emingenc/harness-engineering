---
description: "Track 2 Phase 3: Split annotated design.md into tasks.json"
allowed-tools:
  - Read
  - Write
  - Bash(python3 skills/task-splitter/scripts/*.py:*)
  - Bash(python3 skills/planner/scripts/*.py:*)
  - Bash(python3 scripts/*.py:*)
---

# /split — Track 2 Task Splitting

Follow the task-splitter skill workflow exactly:

1. **Find the design** — look for the most recent file in `workspace/designs/`.

2. **Validate** the design has annotations:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/planner/scripts/validate_plan.py \
     "workspace/designs/<name>-design.md"
   ```
   If `annotation_count` is 0, tell the user to annotate first. STOP.

3. **Split** into tasks:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/task-splitter/scripts/split_tasks.py \
     "workspace/designs/<name>-design.md"
   ```

4. **Validate** tasks:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/task-splitter/scripts/validate_tasks.py
   ```

5. **Present** the summary: task count, dependency chain, annotated tasks, any L-scope warnings.

6. **Log**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Split complete: N tasks from <name>-design.md"
   ```

Tell the user: "Tasks generated. Run `/execute` to start implementing task by task."
