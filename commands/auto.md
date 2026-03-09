---
name: auto
description: Auto-execute Track 2 tasks with HIL-only pauses
tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Agent
---

# /auto — Auto-Execute Loop

Execute Track 2 micro-tasks in a loop, pausing only when human judgment is needed.

## Parallel Execution (Worktrees)

This command is **parallel-safe**. Multiple Claude sessions can run `/auto` simultaneously:

```bash
# Terminal 1                    # Terminal 2                    # Terminal 3
claude --worktree worker-1      claude --worktree worker-2      claude --worktree worker-3
> /auto                         > /auto                         > /auto
```

**How it works:**
- `tasks.json` lives in the **main repo** (shared state)
- `select_next.py` uses **file locking** (`.tasks.lock`) to atomically claim tasks
- Each session gets its own task — no two sessions pick the same one
- Each worktree has its own branch for implementation commits
- If all available tasks are blocked or in-progress by other sessions, this session pauses

**Important:** After completing a task in a worktree, commit changes to the worktree branch. The human merges worktree branches back to main when ready.

## Procedure

Loop through the following steps until all tasks are complete or a pause is triggered:

### Step 1: Select Next Task

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/select_next.py tasks.json
```

If `all_complete` → run the summary and STOP:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_summary.py tasks.json
```
Format the summary as a report and present it.

If `blocked` → **PAUSE**:
- Say: "All remaining tasks are blocked or in-progress by other sessions. Blocked: {blocked_tasks}. In progress: {in_progress_tasks}."
- Log the state:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append-structured --action task_fail --phase execute --track 2 --details '{"blocked_tasks": [...], "in_progress_tasks": [...]}' "Auto-loop paused: waiting for other sessions"
```
- STOP and wait for human.

### Step 2: Check Context Budget

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_tracker.py check
```

If `warning_level` is `warning` or `critical` → **PAUSE**:
- Say: "Context budget at {utilization_percent}%. Recommend running /handoff before continuing."
- STOP and wait for human.

### Step 3: Read Task Files

Read the files listed in the task. Understand the current state.

### Step 4: TDD Gate

Write **failing tests first** for this task.

- If scope is **M** or **L** → **PAUSE**: Show the tests to the human, wait for approval before implementing.
- If scope is **S** → auto-continue to implementation.

### Step 5: Implement

Implement until tests pass. Maximum 2 attempts (2-Pass Rule).

### Step 6: CoVe Self-Check

After implementation, run Chain of Verification:
1. Generate verification questions (edge cases, consistency)
2. Answer each question against actual code
3. Fix any issues found
4. Record findings

### Step 7: Handle 2-Pass Limit

If the bug/issue wasn't resolved in 2 attempts → **PAUSE**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append-structured --action 2pass_limit --task-id {task_id} --phase execute --track 2 "2-Pass limit reached"
```
- Say: "2-Pass limit reached on {task_id}. State logged. Recommend context clear."
- STOP and wait for human.

### Step 8: Mark Complete

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/mark_complete.py {task_id} --commit-sha {sha} --tests-written {N} --tests-passed {N} --cove-findings '{json}'
```

Commit the changes, then loop back to Step 1.

## Pause Points Summary

The loop only pauses for:
1. **Context budget warning** (70%+) → human decides to compact or continue
2. **Blocked/in-progress tasks** → waiting for other sessions to finish their tasks
3. **M/L scope test review** → human validates test design
4. **2-Pass limit** → human decides next approach
5. **All tasks complete** → show summary report
