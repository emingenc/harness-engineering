---
name: executor
description: >-
  Execute one micro-task from tasks.json using TDD. Use when user says
  "execute", "run next task", "implement next", "continue execution",
  or runs /execute. This is the fourth phase of Track 2.
  Enforces TDD gate: failing tests FIRST, then implementation.
tools: Read, Glob, Grep, Edit, Write, Bash
---

# Executor (Track 2 — Phase 4)

## Purpose

Execute exactly ONE micro-task from tasks.json. Enforces TDD (failing tests first)
and Chain of Verification (CoVe) before marking complete.

## Process

### Step 1: Select Next Task

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/select_next.py
```

Returns the next unblocked task (~100 tokens). If no tasks available, tell the user.

### Step 2: Read Task Context

Read ONLY the files listed in the task's `files` array. Do not read unrelated files.
If the task has annotations, read those carefully — they contain human reviewer decisions.

### Step 3: TDD Gate (DO NOT SKIP)

**Write failing tests FIRST:**

1. Based on the task's verification spec, write test(s) that define expected behavior
2. Run the tests — they MUST fail (if they pass, the feature already exists)
3. Show the user the failing tests
4. Wait for user validation (for M/L scope tasks)
   - For S scope tasks, proceed automatically

**Only after tests are validated:**

4. Write implementation code until tests pass
5. Run tests again — they MUST pass now

### Step 4: Chain of Verification (CoVe)

After implementation, run this 4-step self-check:

1. **Generate answer**: The implementation code (already written)
2. **Verification questions** — ask yourself:
   - Does this handle the edge cases mentioned in the task?
   - Is this consistent with the existing codebase patterns?
   - Does this break any existing tests?
   - Are there security concerns (injection, XSS, etc.)?
3. **Answer independently**: Check each question against the actual code
4. **Revise**: Fix any issues found

### Step 5: Mark Complete

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/executor/scripts/mark_complete.py \
  <task_id> [--commit-sha <sha>]
```

This updates tasks.json and appends to claude-progress.txt.

### Step 6: Report

Tell the user:
- What was implemented
- Tests written and their status
- CoVe findings (if any issues were found and fixed)
- "Context can be safely cleared. Run `/execute` for the next task."

## 2-Pass Debugging Rule

If tests don't pass after 2 implementation attempts:
1. Do NOT try a 3rd time
2. Log state:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append \
     "2-Pass limit reached on <task_id>: <what was tried>"
   ```
3. Tell the user: "2-Pass limit reached. Recommend context clear and fresh approach."
4. STOP

## Examples

### Example 1: Simple Task (S scope)

**Task**: T001 — Add auth middleware to /api/users endpoint
**Process**:
1. select_next.py returns T001
2. Read the endpoint file
3. Write test: `test_users_endpoint_requires_auth()`
4. Run test -> FAILS (no auth yet) -- auto-proceed (S scope)
5. Add middleware import and decorator
6. Run test -> PASSES
7. CoVe: edge cases OK, consistent with other endpoints
8. mark_complete.py T001 --commit-sha abc123

### Example 2: Complex Task (M scope) with 2-Pass

**Task**: T003 — Implement token refresh logic
**Process**:
1. select_next.py returns T003
2. Read token management files
3. Write test: `test_token_refresh_extends_session()`
4. Run test -> FAILS -- show user, wait for validation
5. User validates test
6. First attempt: implement refresh -- tests still fail
7. Second attempt: fix edge case -- tests PASS
8. CoVe: security check on token handling
9. mark_complete.py T003

## Anti-Patterns

- Do NOT implement without writing tests first
- Do NOT execute multiple tasks in one session
- Do NOT skip CoVe
- Do NOT attempt a 3rd debugging pass (2-Pass Rule)
- Do NOT read files not listed in the task's files array
