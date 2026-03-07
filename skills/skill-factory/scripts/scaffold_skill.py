#!/usr/bin/env python3
"""PTC Script: scaffold_skill.py
Create the directory structure for a new skill.

Usage: python3 skills/skill-factory/scripts/scaffold_skill.py --name <skill-name> --track <1|2>
"""
import json
import sys
from pathlib import Path

SKILL_TEMPLATE = '''---
name: {name}
description: >-
  [TODO: 1-3 sentences describing what this skill does. Include trigger phrases.]
tools: Read, Glob, Grep, Edit, Write, Bash
---

# {title}

## When to Use

- [TODO: Scenario 1]
- [TODO: Scenario 2]

## Process

### Step 1: Gather Context

[TODO: Describe how to gather context, preferably via PTC script]

### Step 2: Execute

[TODO: Main action steps in imperative form]

### Step 3: Verify

[TODO: How to verify the result]

## Examples

### Example 1: [Scenario]

**Input**: [What the user says]
**Output**: [What Claude produces]

## Anti-Patterns

- [TODO: What NOT to do]
'''


def scaffold(name: str, track: int) -> dict:
    base = Path("skills") / name
    if base.exists():
        return {"error": f"Skill directory already exists: {base}"}

    # Create directories
    dirs = [base / "scripts"]
    if track == 2:
        dirs.append(base / "references")

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create SKILL.md from template
    title = name.replace("-", " ").title()
    skill_content = SKILL_TEMPLATE.format(name=name, title=title)
    skill_path = base / "SKILL.md"
    skill_path.write_text(skill_content)

    created = [str(skill_path)] + [str(d) + "/" for d in dirs]

    return {
        "created": created,
        "skill_path": str(skill_path),
        "track": track,
        "next_steps": [
            f"Edit {skill_path} to fill in the TODO sections",
            "Add PTC scripts to scripts/ directory",
            f"Optionally create commands/{name}.md for a slash command",
        ],
    }


def main():
    args = sys.argv[1:]
    name = None
    track = 1

    if "--name" in args:
        idx = args.index("--name")
        name = args[idx + 1] if idx + 1 < len(args) else None
    if "--track" in args:
        idx = args.index("--track")
        track = int(args[idx + 1]) if idx + 1 < len(args) else 1

    if not name:
        print(json.dumps({"error": "Usage: scaffold_skill.py --name <skill-name> [--track <1|2>]"}))
        sys.exit(1)

    result = scaffold(name, track)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
