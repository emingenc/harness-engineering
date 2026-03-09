---
description: Display task progress dashboard with dependency graph and metrics
allowed-tools:
  - Bash
  - Bash(python3 scripts/dashboard.py:*)
  - Read
---

# /dashboard — Task Progress Dashboard

Display a visual overview of task progress, dependencies, and quality metrics.

## Procedure

### Step 1: Generate Dashboard Data

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/dashboard.py full tasks.json
```

### Step 2: Format and Present

Using the JSON output, format a report with these sections:

#### Dependency Graph

Render the `dependency_graph_mermaid` field as a Mermaid diagram:

```mermaid
{dependency_graph_mermaid}
```

#### Progress

Show each task's progress bar from `progress_bars`:

```
T001 [##########] 100% ✓ Create auth module (S)
T002 [#####.....] 50%   Add refresh tokens (M)
T003 [..........] 0%    Implement RBAC (M)

Overall: {overall_progress}
```

#### Velocity

From the `velocity` field:

| Metric | Value |
|--------|-------|
| Avg duration | {avg_duration_minutes} min |
| Est. remaining | {estimated_remaining_minutes} min |
| Completed | {completed_count} |
| Remaining | {remaining_count} |

#### Quality

From `quality_metrics`:

| Metric | Value |
|--------|-------|
| Tests written | {total_tests_written} |
| CoVe findings | {cove_findings_count} |
| 2-Pass triggers | {two_pass_triggers} |
