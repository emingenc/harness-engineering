# Architecture: Dual-Track Workflow

## Overview

This plugin implements two distinct tracks for Claude Code work, optimized for different task sizes. Both tracks share the same context management and PTC infrastructure.

## Track 1: Surgical Fixes

**Trigger**: `/fix <description>` or small-fix skill activation
**Context cost**: Low (single session, no design doc)
**Flow**:

```
User describes problem
  -> PTC script greps codebase (JSON summary only)
  -> Claude reads relevant files
  -> Claude implements fix
  -> Run tests
  -> Done
```

**When to use**: Bug fixes, small refactors, config changes, one-file features.
**Scope check**: If the fix touches >3 files or requires >30 minutes, escalate to Track 2.

## Track 2: Spec-Driven Features

**Trigger**: `/research`, `/plan`, `/split`, `/execute`
**Context cost**: Distributed across multiple sessions
**Flow**:

```
/research <topic>
  -> Sub-agents explore in parallel (fresh context each)
  -> Summaries written to workspace/research/

/plan
  -> Claude drafts design.md from research
  -> Bi-directional prompting: Claude asks 3-5 clarifying Qs
  -> Human answers refine design
  -> Claude writes final design.md to workspace/designs/
  -> STOP (human annotates offline)

/split
  -> PTC script reads annotated design.md
  -> Validates annotations exist
  -> Generates tasks.json with dependencies
  -> Returns summary only (~100 tokens)

/execute
  -> PTC script picks next unblocked task (~100 tokens)
  -> Claude writes failing tests first (TDD gate)
  -> Human validates tests
  -> Claude implements until tests pass
  -> PTC script marks complete, records commit SHA
  -> Context can be cleared
```

## Hierarchical Roles

| Role | Entity | Responsibility |
|------|--------|----------------|
| Architect | Human | Final decisions, annotations, test validation |
| Manager | Claude | Orchestration, design, implementation |
| Workers | Sub-agents | Isolated research, parallel exploration |

## Context Budget

Target: **<50% context utilization** at all times.

### 5 Techniques

1. **Sub-agents**: Fresh context per research topic. Return summaries, not raw data.
2. **PTC scripts**: Data processing in Python sandbox. Only JSON summaries enter context.
3. **Compaction**: Mid-session context trimming when utilization grows.
4. **`/handoff`**: Structured handoff doc with exact resumption state.
5. **Hard clear**: After task completion + commit, safe to clear context entirely.

### Token Flow Example

Without PTC:
```
grep output: ~500-2000 tokens per search
10 searches = 5000-20000 tokens consumed
```

With PTC:
```
Python grep -> JSON summary: ~50 tokens per search
10 searches = 500 tokens consumed
Savings: 85-98%
```

## 30k Token Decomposition

During `/plan`, if a design.md exceeds ~30k tokens (estimated via word count / 0.75):
- Generate a **Master Plan** (high-level, stays with human)
- Generate **Sub Plans** (isolated, one per domain concern, <10k tokens each)
- `/split` then operates on Sub Plans independently

## 2-Pass Debugging Rule

If Claude cannot identify a bug within 2 debugging passes:
1. Do NOT attempt a 3rd pass
2. Write current state to `claude-progress.txt`
3. Signal: "2-Pass limit reached. Recommend context clear and fresh approach."
4. On restart, fresh context reads only the progress file

This prevents the "apologize-and-retry" death spiral.

## Chain of Verification (CoVe)

After implementing each micro-task, the executor runs:
1. **Generate answer**: Implementation code
2. **Generate verification questions**: Edge cases, consistency checks
3. **Answer independently**: Check each question against actual code
4. **Revise**: Fix any issues before marking complete

## Auto-Execute Loop (`/auto`)

Replaces manual `/execute` repetition with an automated loop that pauses only for human judgment:

```
LOOP:
  select_next.py → if all_complete → auto_summary.py → STOP
  context_tracker.py check → if 70%+ → PAUSE for /handoff
  Read task files
  TDD: write failing tests
    scope M/L → PAUSE (show tests, wait for human)
    scope S → auto-continue
  Implement (max 2 attempts)
  CoVe self-check
  If 2-pass limit → PAUSE (log state, wait for human)
  mark_complete.py + commit
  LOOP BACK
```

HIL pause points: context budget warning, M/L test review, 2-pass limit, completion.

## Context Budget Tracker

`scripts/context_tracker.py` estimates context utilization per session:

- Reads `claude-progress.jsonl` for session activity
- Estimates tokens by scope (S=5k, M=15k, L=30k) + base overhead
- Returns warning level: ok (<50%), caution (50-70%), warning (70-90%), critical (90%+)
- Called by PreCompact hook and `/auto` loop

## Tasks Schema v2

`tasks.json` now includes `schema_version: "2"` with additional task fields:

- `started_at`, `duration_seconds` — timing data
- `estimated_minutes` — scope-based estimate (S=15, M=60, L=120)
- `attempt_count`, `retry_history` — attempt tracking
- `tests_written`, `tests_passed` — test metrics
- `cove_findings` — Chain of Verification results

Top-level additions: `plan_version`, `plan_history` for re-split tracking.
Backward compatible — v1 files work with `.get()` defaults.

## State Recovery Protocol

Any new session can reconstruct state from:
- `claude-progress.txt` — what was done, what failed (text log)
- `claude-progress.jsonl` — structured progress entries (JSON lines)
- `tasks.json` — task status, dependencies, commit SHAs, timing, metrics
- `git log` — actual code state
- `workspace/designs/` — active design documents

Cross-reference these sources to verify claimed state matches reality.
