---
name: skill-name
description: >-
  1-3 sentences describing what this skill does. Include trigger phrases
  that help Claude match user intent to this skill. Be slightly "pushy"
  with trigger phrases so Claude activates this skill when relevant.
tools: Read, Glob, Grep, Edit, Write, Bash
---

# Skill Name

## When to Use

- [Scenario 1]
- [Scenario 2]

## Process

### Step 1: Gather Context

Run PTC script for context:
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/skill-name/scripts/gather.py <args>
```
Returns JSON summary. Read only the files indicated by the summary.

### Step 2: [Action]

[Instructions in imperative form]

### Step 3: [Action]

[Instructions in imperative form]

## Examples

### Example 1: [Scenario]

**Input**: [What the user says or provides]
**Output**: [What Claude produces]

### Example 2: [Scenario]

**Input**: [What the user says or provides]
**Output**: [What Claude produces]

## Anti-Patterns

- [What NOT to do and why]

## PTC Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/gather.py` | [purpose] | [args] | [JSON shape] |

## References

For detailed documentation, see `references/` directory.
