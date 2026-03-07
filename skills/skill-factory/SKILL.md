---
name: skill-factory
description: >-
  Create new Claude Code skills from scratch. Use when the user says
  "new skill", "create a skill", "make a skill for X", "turn this into a skill",
  "automate this pattern", or "scaffold a skill".
tools: Read, Glob, Grep, Bash, Edit, Write
---

# Skill Factory

## Workflow

### Phase 1: Capture Intent (DO NOT SKIP)

Ask the user:
1. What should this skill enable Claude to do?
2. Is this Track 1 (small/surgical) or Track 2 (multi-step)?
3. What triggers it? (user phrases, contexts)
4. What is the expected output format?
5. Are there PTC opportunities? (grepping, formatting, validation that should run in script sandbox rather than chat context)

### Phase 2: Scaffold

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-factory/scripts/scaffold_skill.py \
  --name "<skill-name>" --track <1|2>
```

Creates:
- `skills/<name>/SKILL.md` (from template)
- `skills/<name>/references/` (if Track 2)
- `skills/<name>/scripts/` (always)

### Phase 3: Draft SKILL.md

Read the template at `docs/templates/skill-template.md` for structure.

**Frontmatter rules:**
- `name`: kebab-case
- `description`: 1-3 sentences, include trigger phrases (slightly "pushy")
- `tools`: Only list tools actually needed

**Body rules:**
- Under 500 lines; overflow goes to `references/`
- Imperative form ("Read the file", not "You should read the file")
- Explain WHY, not just WHAT
- Include 2-3 concrete examples with Input/Output
- Identify PTC script opportunities (repetitive, deterministic, data-heavy work)

### Phase 4: Create PTC Scripts (if identified)

For each PTC opportunity:
1. Write script following `docs/ptc-guide.md` patterns
2. JSON output only
3. Python 3 stdlib only
4. Test with sample input

### Phase 5: Create Slash Command (if appropriate)

If the skill should have a `/command` trigger:
1. Create `commands/<name>.md` with frontmatter
2. Reference the skill in the command body
3. Set appropriate `allowed-tools`

### Phase 6: Test

Test with 2-3 realistic prompts to verify:
- Skill triggers correctly from description
- PTC scripts produce valid JSON
- Process flow makes sense

## Examples

### Example 1: Creating a Linting Skill

**Input**: "Create a skill that runs linting on changed files"
**Process**:
- Scaffold `skills/lint-check/`
- SKILL.md: trigger on "lint", "check style", "code quality"
- PTC script: `scripts/find_changed.py` uses git diff to find changed files, returns JSON list
- SKILL.md instructs Claude to run linter on those files only

### Example 2: Creating a Migration Skill

**Input**: "Create a skill for database migrations"
**Process**:
- Scaffold `skills/db-migrate/` with references/
- SKILL.md: trigger on "migration", "db change", "schema update"
- references/migration-patterns.md: common migration patterns
- PTC script: `scripts/check_schema.py` validates migration file format

## Anti-Patterns

- Do NOT create skills for one-time tasks (use a command instead)
- Do NOT stuff >500 lines into SKILL.md (use references/)
- Do NOT add tools to frontmatter that the skill doesn't actually use
- Do NOT create a skill without trigger phrases in the description
