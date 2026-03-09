# Tutorials

Hands-on walkthroughs for common use cases. Each tutorial shows the exact commands and what to expect at each step.

---

## Tutorial 1: Fix a Bug (Track 1)

**Scenario**: Your app's login button doesn't redirect after an OAuth callback. This is a small, surgical fix — perfect for Track 1.

**Time**: ~5 minutes, single session

### Step 1: Start the fix

```
> /fix The login button doesn't redirect after OAuth callback
```

Claude will automatically:
1. Run `scope_check.py` to confirm this is Track 1 (small fix)
2. Grep the codebase for relevant terms (`OAuth`, `redirect`, `callback`, `login`)
3. Show you a JSON summary of where matches were found

### Step 2: Watch Claude work

Claude reads only the files from the search results — not the whole codebase. It identifies the bug, implements the minimal fix, and runs existing tests.

You'll see output like:

```
Scope: track1 (touches 1-2 files)
Found 3 matches across 2 files:
  - src/auth/oauth.ts (2 matches)
  - src/components/LoginButton.tsx (1 match)

Reading relevant files...
Fix: Added missing redirect call in OAuth callback handler.
Tests pass.
```

### Step 3: Done

Claude logs the fix to `claude-progress.txt` and you're finished. No `tasks.json`, no design doc — just a clean fix.

### When to escalate

If Claude's scope check returns `escalate` instead of `track1`, the fix is too large. It will suggest `/plan` instead. Trust the signal — multi-file refactors in Track 1 lead to context rot.

---

## Tutorial 2: Build a Feature from Scratch (Track 2)

**Scenario**: You need to add a full user authentication system with JWT, role-based access, and session management. This spans many files and requires planning.

**Time**: Multiple sessions (one per phase + one per micro-task)

### Phase 1: Research

```
> /research user authentication patterns for this codebase
```

Claude will:
1. Define 3-5 research questions ("How are routes protected?", "Is there existing auth middleware?")
2. Search locally via PTC scripts — returns JSON summaries, not raw grep output
3. Spawn sub-agents in parallel for independent questions (each with fresh context)
4. Write findings to `workspace/research/user-authentication.md`

You'll see a summary of key findings and recommendations.

### Phase 2: Plan

```
> /plan
```

Claude:
1. Loads research from `workspace/research/`
2. Drafts a design document using the standard template
3. Asks you 3-5 clarifying questions before finalizing:
   ```
   Before I finalize the design, a few questions:
   1. JWT or session-based auth? (a) JWT with refresh tokens (b) server sessions
   2. Role hierarchy? (a) flat roles (b) hierarchical with inheritance
   3. Password policy? (a) basic (8+ chars) (b) NIST-compliant
   ```
4. Revises the design based on your answers
5. Writes the final design to `workspace/designs/auth-design.md`
6. **STOPS** — this is deliberate

**Important**: Claude stops here and tells you to annotate the design offline.

### Phase 2.5: Annotate (your turn)

Open `workspace/designs/auth-design.md` and add annotations:

```markdown
## Architecture

The auth system uses JWT with refresh token rotation.

<!-- ANNOTATION: Use httpOnly cookies for refresh tokens, not localStorage -->

### Token Flow
1. User logs in → receives access + refresh token
2. Access token expires → client uses refresh token
<!-- ANNOTATION: Add rate limiting on the refresh endpoint — 10 req/min -->
```

Annotations are how you inject architectural decisions. They become priority context when tasks are generated.

### Phase 3: Split

```
> /split
```

Claude:
1. Validates your annotations exist (if zero, it stops and asks you to annotate)
2. Runs `split_tasks.py` to generate `tasks.json`
3. Shows you the task breakdown:

```
Generated 5 tasks from auth-design.md:
  T001: Create User model and migration (S)
  T002: Implement JWT token service (M)
  T003: Add auth middleware (S)
  T004: Create login/register endpoints (M)
  T005: Add role-based access control (L)

Dependencies: T003 depends on T002. T005 depends on T003.
```

### Phase 4: Execute (repeat per task)

```
> /execute
```

For each task, Claude:
1. Picks the next unblocked task from `tasks.json`
2. Reads only the files listed in that task
3. **Writes failing tests first** (TDD gate — non-negotiable)
4. Shows you the tests (for M/L scope tasks)
5. Implements until tests pass
6. Marks complete with commit SHA

After each `/execute`, Claude suggests clearing context:

```
T001 complete (commit: a1b2c3d).
Context can be safely cleared. Run /execute for the next task.
```

**Clear context between tasks.** This is the whole point — each task gets fresh context, staying in the quality zone.

### Phase 5: Completion

When all tasks are done:

```
> /execute
All tasks complete! 5/5 tasks finished.
See claude-progress.txt for the full execution log.
```

---

## Tutorial 3: Resume After a Break

**Scenario**: You were midway through a Track 2 feature, took a break, and now you're in a new session.

### Option A: Just run /status

```
> /status
```

```
## Status Overview

| Metric       | Value                |
|--------------|----------------------|
| Tasks done   | 2/5                  |
| Next task    | T003: Add auth middleware |
| Progress log | 8 entries            |
| Last activity| 2025-03-07 16:42     |

### Recent Activity
- T002 complete (commit: def456)
- T001 complete (commit: abc123)
- Split complete: 5 tasks from auth-design.md
```

Then continue:

```
> /execute
```

### Option B: Use a handoff (for longer breaks)

Before ending the previous session:

```
> /handoff
```

This writes a structured document to `workspace/handoff-<timestamp>.md` with:
- Current task status
- Decisions made this session
- What was tried (especially failed attempts)
- Remaining work
- Resumption instructions

Next session, Claude reads the handoff and picks up exactly where you left off.

---

## Tutorial 4: Create a Custom Skill

**Scenario**: Your team frequently writes database migration scripts. You want a skill that scaffolds migrations with the right patterns.

```
> /new-skill db-migration
```

Claude asks 5 questions:

```
1. What should this skill enable Claude to do?
   → Generate database migration files with up/down methods

2. Is this Track 1 or Track 2?
   → Track 1 (each migration is a single file)

3. What triggers it?
   → "create migration", "add migration", "migrate"

4. Expected output format?
   → A migration file in db/migrations/ with timestamp prefix

5. PTC opportunities?
   → Yes: scan existing migrations for naming conventions and column types
```

Claude then:
1. Scaffolds `skills/db-migration/` with `SKILL.md` and `scripts/` directory
2. Drafts the SKILL.md with your trigger phrases and process steps
3. Creates PTC scripts (e.g., `scan_migrations.py` to find existing patterns)
4. Logs the creation

Your new skill is auto-discovered on the next session.

---

## Tutorial 5: Improve a Prompt

**Scenario**: You have a system prompt for a code review bot, but it's not producing consistent results.

Claude's `prompt-enhancer` skill helps analyze and improve LLM prompts.

### Analyze the prompt

```
> Can you analyze this prompt? "Review the code and find bugs."
```

Claude runs `enhance.py analyze`:

```json
{
  "scores": {
    "specificity": 2,
    "role_framing": 1,
    "output_format": 1,
    "examples": 1,
    "constraints": 1
  },
  "overall": 1.2,
  "has_role": false,
  "has_examples": false,
  "suggestions": [
    "Add a role definition (e.g., 'You are a senior code reviewer...')",
    "Specify what types of bugs to look for",
    "Define the output format (e.g., 'Return findings as a markdown checklist')",
    "Add 1-2 examples of good review output",
    "Set constraints ('Focus on security and performance, not style')"
  ]
}
```

### Get the improved version

Claude generates a side-by-side comparison:

```
BEFORE:
  "Review the code and find bugs."

AFTER:
  "You are a senior software engineer conducting a code review.
   Analyze the provided code for:
   1. Security vulnerabilities (injection, auth bypass, data exposure)
   2. Performance issues (N+1 queries, unnecessary allocations)
   3. Logic errors (off-by-one, null handling, race conditions)

   For each finding, provide:
   - Severity: critical / warning / info
   - Location: file and line number
   - Description: what's wrong and why it matters
   - Fix: suggested code change

   Ignore style/formatting issues unless they affect readability."
```

---

## Tutorial 6: Debug a Stuck Session (2-Pass Rule)

**Scenario**: Claude can't find a bug after two attempts. The 2-Pass Rule kicks in.

### What happens automatically

After the second failed attempt, Claude:

1. Writes state to `claude-progress.txt`:
   ```
   2-Pass limit on T003: Auth middleware not catching expired tokens.
   Tried: (1) checking token expiry logic, (2) inspecting middleware order.
   Suspect: issue may be in token refresh race condition.
   ```

2. Tells you:
   ```
   2-Pass limit reached. I've logged my findings to claude-progress.txt.
   Recommend: clear context and approach fresh.
   ```

### What you do

1. Clear the context (start a new session)
2. Claude automatically reads `claude-progress.txt` on startup
3. It approaches the problem fresh, informed by previous attempts but without the accumulated noise

This prevents the "sorry, let me try again" death spiral where Claude apologizes endlessly without making progress.

---

## Tutorial 7: Verify Plugin Integrity

**Scenario**: You've modified skills or added scripts and want to verify everything is still wired correctly.

```
> /verify
```

Claude runs a suite of structural checks:

```
## Verification Results

- [x] CLAUDE.md: 87 lines (under 150)
- [x] Skills: 7/7 have valid frontmatter
- [x] tasks.json: valid (3 tasks, 2 complete)
- [x] plugin.json: valid (v0.1.0)
- [x] Design docs: 1 found, valid
- [x] File integrity: all references valid
- [ ] ISSUE: skills/db-migration/SKILL.md missing 'tools' in frontmatter
```

Fix any issues flagged, then run `/verify` again.

---

## Tutorial 8: Multi-Session Feature with Context Handoff

**Scenario**: You're building a large feature that will take 3-4 sessions to complete. Here's how to manage context across sessions.

### Session 1: Research + Plan

```
> /research payment processing integration
> /plan
```

Claude produces the design doc. Before ending the session:

```
> /handoff
```

### Session 2: Annotate + Split + Execute first tasks

Read the handoff, annotate the design, then:

```
> /split
> /execute    ← completes T001
> /execute    ← completes T002
> /handoff    ← save state before ending
```

### Session 3: Continue execution

```
> /status     ← see where you are
> /execute    ← T003
> /execute    ← T004
> /execute    ← T005 — all complete!
```

**Key principle**: Each session starts clean. State is reconstructed from `tasks.json`, `claude-progress.txt`, and `git log`. No session depends on remembering what happened in a previous one.

---

## Common Patterns

### Pattern: Quick fix in the middle of a feature

You're mid-Track-2 and notice a typo. Don't interrupt the workflow:

```
> /fix typo in the error message on line 42 of auth.ts
```

Track 1 runs independently. Your Track 2 state (`tasks.json`, progress) is untouched.

### Pattern: Checking progress without disrupting flow

```
> /status
```

This is read-only. It won't modify any state files or change your current task.

---

## Tutorial 9: Auto-Execute Loop

**Scenario**: You've already split tasks and want Claude to execute them all with minimal interruption.

### Step 1: Start the loop

```
> /auto
```

Claude enters an automated loop:
1. Picks the next unblocked task
2. Checks context budget (pauses if >70%)
3. Writes failing tests
   - **S-scope tasks**: auto-continues to implementation
   - **M/L-scope tasks**: pauses to show you the tests for review
4. Implements until tests pass (max 2 attempts)
5. Runs CoVe self-check
6. Marks complete and commits
7. Loops back to step 1

### What you'll see

For S-scope tasks, Claude works silently and reports completion:
```
T001 complete (S, 8 min, commit: a1b2c3d). Continuing...
```

For M/L-scope tasks, Claude pauses:
```
T002 (M): Here are the failing tests I've written:
  - test_refresh_token_rotation
  - test_expired_refresh_rejected
  - test_concurrent_refresh_race

Approve these tests? (yes to continue, or provide feedback)
```

### When the loop pauses

- **Context budget at 72%**: "Recommend running /handoff before continuing."
- **2-Pass limit**: "2-Pass limit on T003. State logged. Recommend context clear."
- **All complete**: Shows a summary report with duration, test counts, and CoVe findings.

---

## Tutorial 10: Dashboard

**Scenario**: You want a visual overview of progress, dependencies, and quality metrics.

```
> /dashboard
```

Claude displays:

```
## Dependency Graph

graph TD
  T001["✓ T001: Create auth module"]:::done
  T002["T002: Add refresh tokens"]:::active
  T003["T003: Implement RBAC"]
  T001 --> T002
  T002 --> T003

## Progress

T001 [##########] 100% ✓ Create auth module (S)
T002 [#####.....] 50%   Add refresh tokens (M)
T003 [..........] 0%    Implement RBAC (M)

Overall: 1/3 tasks (33%)

## Velocity

| Metric           | Value    |
|------------------|----------|
| Avg duration     | 12.5 min |
| Est. remaining   | 85.0 min |

## Quality

| Metric           | Value |
|------------------|-------|
| Tests written    | 4     |
| CoVe findings    | 1     |
| 2-Pass triggers  | 0     |
```

---

### Pattern: When you disagree with the plan

After `/plan`, if the design doc doesn't match your vision:
1. Don't run `/split` yet
2. Edit the design doc directly
3. Add annotations explaining your changes
4. Run `/plan` again if you want Claude to revise, or just `/split` if your edits are complete

### Pattern: Skipping research for well-known domains

If you already know the codebase well:

```
> /plan
```

Claude will note that no research exists and ask if you want to proceed anyway. You can say yes and provide context directly during the bi-directional prompting phase.
