# Harness Engineering Plugin

Dual-track workflow for Claude Code. Enforces TDD, context budgets, PTC scripts, and micro-task decomposition.

## Tracks

- **Track 1** (small fixes): `/fix` command. Surgical, single-context, PTC-assisted.
- **Track 2** (features): `/research` -> `/plan` -> `/split` -> `/execute`. Spec-driven, TDD-gated.

## Architecture

See `docs/architecture.md` for the full two-track system.

## Commands

| Command | Track | Purpose |
|---------|-------|---------|
| `/fix <desc>` | 1 | Surgical fix with PTC-assisted search |
| `/new-skill <name>` | 1 | Scaffold a new skill |
| `/research <topic>` | 2 | Parallel research via sub-agents |
| `/plan` | 2 | Generate design.md, STOP for annotation |
| `/split` | 2 | Split annotated design.md into tasks.json |
| `/execute` | 2 | Execute one micro-task from tasks.json |
| `/handoff` | - | Write handoff doc for context transfer |
| `/status` | - | Show progress overview |
| `/verify` | - | Run verification suite |

## Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| small-fix | `skills/small-fix/` | Track 1 surgical fixes |
| prompt-enhancer | `skills/prompt-enhancer/` | Improve LLM prompts |
| skill-factory | `skills/skill-factory/` | Create new skills |
| researcher | `skills/researcher/` | Track 2 research phase |
| planner | `skills/planner/` | Track 2 design generation |
| task-splitter | `skills/task-splitter/` | Track 2 micro-separation |
| executor | `skills/executor/` | Track 2 one-task execution |

## PTC Scripts

Python scripts run in Bash sandbox. Only JSON summaries enter context.
See `docs/ptc-guide.md` for patterns.

**Permission config** in `.claude/settings.json`:
- `skills/*/scripts/*.py` — per-skill PTC scripts
- `scripts/*.py` — shared PTC scripts

## Context Management Rules

1. **Budget**: Stay under 50% context utilization
2. **Sub-agents**: Use for parallel research (fresh context each)
3. **PTC scripts**: Process data in Python, return JSON summaries only
4. **Compaction**: Use `/handoff` before context limit
5. **Hard clear**: After task completion + commit, context can be cleared

## Debugging: 2-Pass Rule

If a bug isn't found in 2 attempts:
1. Write state to `claude-progress.txt`
2. Signal: "2-Pass limit reached. Recommend context clear."
3. Never loop endlessly

## TDD Gate (Track 2)

1. Pick next task from tasks.json
2. Write **failing tests first**
3. Human validates tests
4. Implement until tests pass
5. Mark complete with commit SHA

## State Files

- `claude-progress.txt` — Append-only cross-session log
- `tasks.json` — Active micro-task list (see `docs/templates/tasks-schema.json`)
- `workspace/designs/` — Design documents (gitignored)
- `workspace/research/` — Research summaries (gitignored)

## Conventions

See `docs/conventions.md` for commit style, naming, and code patterns.

## Templates

- `docs/templates/design-template.md` — Track 2 design doc
- `docs/templates/skill-template.md` — Skill SKILL.md boilerplate
- `docs/templates/tasks-schema.json` — tasks.json JSON Schema
