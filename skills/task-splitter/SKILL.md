---
name: task-splitter
description: >-
  Split an annotated design document into micro-tasks in tasks.json.
  Use when user says "split", "break down", "create tasks", "generate tasks",
  or after a design.md has been annotated and the user runs /split.
  This is the third phase of Track 2.
tools: Read, Bash, Write
---

# Task Splitter (Track 2 — Phase 3)

## Purpose

Convert an annotated design.md into a structured tasks.json with explicit
dependencies. This enables micro-separated execution where each task is
completable in <50% context.

## Prerequisites

Before splitting:
1. A design.md must exist in `workspace/designs/`
2. The design.md must have `<!-- ANNOTATION: ... -->` comments
3. The design.md must have a Micro-Task Breakdown section

If annotations are missing, tell the user to annotate first.

## Process

### Step 1: Validate Design

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/planner/scripts/validate_plan.py \
  "workspace/designs/<name>-design.md"
```

Check that:
- `annotation_count` > 0 (refuse if no annotations)
- All required sections are present
- Micro-task breakdown exists

### Step 2: Split

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/task-splitter/scripts/split_tasks.py \
  "workspace/designs/<name>-design.md"
```

This script:
1. Reads the annotated design.md (in Python, not in chat)
2. Validates annotations exist (refuses if none found)
3. Parses the micro-task breakdown section
4. Cross-references annotations with tasks
5. Generates tasks.json conforming to the JSON Schema
6. Returns a summary: "Generated N tasks, M have annotations, dependency chain: ..."

### Step 3: Validate Tasks

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/task-splitter/scripts/validate_tasks.py
```

Checks tasks.json against the schema at `docs/templates/tasks-schema.json`.

### Step 4: Present Summary

Show the user:
- Number of tasks generated
- Dependency chain visualization
- Tasks with annotations
- Any L-scope tasks that should be broken down further

### Step 5: Log

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Tasks split: N tasks from <name>-design.md"
```

## Examples

### Example 1: Simple Split

**Input**: "/split" (after annotating auth-design.md)
**Process**:
1. Validate: 3 annotations found, all sections present
2. Split: 7 tasks generated
3. Validate: schema compliance OK
4. Summary: "Generated 7 tasks, 3 have annotations, chain: T001->T002->T003, T001->T004->T005->T006->T007"

## Anti-Patterns

- Do NOT split a design with no annotations
- Do NOT manually edit tasks.json (use PTC scripts)
- Do NOT proceed to execution without validating tasks
