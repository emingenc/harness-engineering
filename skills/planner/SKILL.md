---
name: planner
description: >-
  Generate design documents for Track 2 features. Use when user says
  "plan this", "design this feature", "create a plan", "write a design doc",
  or after research is complete and the user wants to move to planning.
  This is the second phase of Track 2.
tools: Read, Glob, Grep, Edit, Write, Bash
---

# Planner (Track 2 — Phase 2)

## Purpose

Generate a design.md from research findings. Uses bi-directional prompting
(Claude asks clarifying Qs) and stops for human annotation before proceeding.

## Process

### Step 1: Load Research

Read the relevant research file:
```
workspace/research/<topic>.md
```

If no research exists, tell the user to run `/research <topic>` first.

### Step 2: Draft Initial Design

Use the template at `docs/templates/design-template.md`.
Write to `workspace/designs/<name>-design.md`.

Fill in:
- Problem Statement (from research)
- Proposed Solution (synthesize from findings)
- Architecture (components, data flow, file changes)
- Trade-offs (at least 2 options considered)
- Dependencies
- Verification Strategy
- Preliminary Micro-Task Breakdown

### Step 3: Bi-Directional Prompting (DO NOT SKIP)

Before finalizing, ask 3-5 targeted clarifying questions:

Format as multiple choice when possible:
```
Before I finalize this design, I have a few questions:

1. For the auth middleware, should we:
   a) Extend the existing middleware
   b) Create a new middleware chain
   c) Other (please specify)

2. Should error responses follow:
   a) The existing JSON error format
   b) RFC 7807 Problem Details
   c) Other (please specify)

3. ...
```

Wait for the user's answers.

### Step 4: Revise and Finalize

Incorporate answers into the design. Write the final version.

### Step 5: Validate

Run validation:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planner/scripts/validate_plan.py \
  "workspace/designs/<name>-design.md"
```

This checks:
- Document completeness (all sections filled)
- Size (triggers 30k decomposition if too large)
- Micro-task breakdown exists

### Step 6: STOP

Tell the user:
```
Design document written to: workspace/designs/<name>-design.md

NEXT STEPS:
1. Open the design document
2. Add annotations using: <!-- ANNOTATION: your comment -->
3. When done, run /split to generate tasks
```

**DO NOT proceed to implementation.** The human must annotate first.

### Step 7: Log

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Design created: <name>-design.md (awaiting annotation)"
```

## 30k Token Decomposition

If `validate_plan.py` reports the design exceeds 30k tokens:

1. Generate a **Master Plan** — high-level overview, stays with human
2. Generate **Sub Plans** — one per domain concern, each <10k tokens
3. Write Sub Plans to `workspace/designs/<name>-sub-<n>.md`
4. Each Sub Plan can be independently `/split` and `/execute`d

## Examples

### Example 1: Simple Feature

**Input**: "/plan" (after researching auth flow)
**Process**:
1. Read workspace/research/authentication-flow.md
2. Draft design with 5 micro-tasks
3. Ask 3 clarifying Qs about middleware approach
4. Revise based on answers
5. Validate (under 30k, all sections present)
6. STOP for annotation

### Example 2: Large Feature (Decomposition)

**Input**: "/plan" (after researching full API redesign)
**Process**:
1. Read workspace/research/api-redesign.md
2. Draft design — validate_plan.py reports 45k tokens
3. Decompose into Master Plan + 3 Sub Plans
4. Ask clarifying Qs about each sub-domain
5. Write all plans
6. STOP for annotation

## Anti-Patterns

- Do NOT skip bi-directional prompting
- Do NOT proceed to implementation after planning
- Do NOT write a design without research
- Do NOT create a design.md with empty sections
