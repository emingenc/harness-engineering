# Conventions

## Naming

- **Files**: kebab-case (`search-local.py`, `design-template.md`)
- **Directories**: kebab-case (`skill-factory/`, `task-splitter/`)
- **Python**: snake_case functions/variables, PascalCase classes
- **Skills**: kebab-case name in frontmatter (`name: small-fix`)
- **Commands**: kebab-case filename = slash command name (`fix.md` -> `/fix`)

## Commits

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Examples:
```
feat(executor): add TDD gate for micro-task execution
fix(planner): prevent design.md exceeding 30k token threshold
docs(ptc-guide): add batch search example
test(small-fix): add scope check boundary tests
chore(settings): update PTC permission patterns
```

## PTC Scripts

- Location: `skills/<name>/scripts/` or `scripts/` (shared)
- Language: Python 3 (stdlib only, no pip dependencies)
- Output: JSON to stdout, errors to stderr
- Input: CLI args or stdin
- No network access
- Timeout: 30 seconds max
- Truncate results to prevent context bloat (max 10 matches per term)

## Skill Structure

```
skills/<name>/
  SKILL.md          # Required. Frontmatter + instructions.
  references/       # Optional. Overflow docs loaded on demand.
  scripts/          # Optional. PTC scripts for this skill.
```

SKILL.md rules:
- Under 500 lines (overflow goes to `references/`)
- Imperative form ("Read the file", not "You should read the file")
- Include 2-3 concrete examples with Input/Output
- Frontmatter: `name`, `description` (with trigger phrases), `tools`

## Command Structure

```yaml
---
description: "What this command does"
allowed-tools: ["Read", "Bash(python ...)"]
---
```

- One command per file in `commands/`
- Use `allowed-tools` to restrict tool access per command
- Reference PTC scripts via `${CLAUDE_PLUGIN_ROOT}/skills/...`

## Code Style

- Keep it simple. No over-engineering.
- No dependencies beyond Python stdlib for PTC scripts.
- Comments only where logic isn't self-evident.
- No feature flags or backwards-compatibility shims.

## Design Documents

- Location: `workspace/designs/<name>-design.md`
- Use template from `docs/templates/design-template.md`
- Status progression: DRAFT -> ANNOTATED -> APPROVED -> IN_PROGRESS -> COMPLETE
- Annotations use HTML comments: `<!-- ANNOTATION: ... -->`
