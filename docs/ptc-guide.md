# PTC (Programmatic Tool Calling) Guide

## What is PTC?

PTC scripts are Python programs that run in Claude Code's Bash sandbox. They perform data-heavy operations (searching, formatting, validating, aggregating) and return only structured JSON summaries to the model's context window.

**Why**: A grep search returns 500-2000 tokens of raw output. A PTC script returns ~50 tokens of structured JSON. Over a session, this saves 85-98% of context budget.

## How It Works

```
Claude invokes:  Bash(python3 skills/researcher/scripts/search_local.py "auth" "login")
Script runs:     grep, glob, parse in Python sandbox
Script outputs:  {"results": [...], "total": 47, "truncated": true}
Claude receives: Only the JSON (~50 tokens instead of ~2000)
```

## Permissions

Configured in `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(python3 skills/*/scripts/*.py:*)",
      "Bash(python3 scripts/*.py:*)"
    ]
  }
}
```

Commands can further restrict via frontmatter:
```yaml
allowed-tools: ["Bash(python3 skills/executor/scripts/*.py:*)"]
```

## Writing PTC Scripts

### Rules

1. **Python 3 stdlib only** — no pip dependencies
2. **No network access** — local filesystem only
3. **JSON output to stdout** — this is what enters context
4. **Errors to stderr** — `print("error", file=sys.stderr)`
5. **30-second timeout** — scripts must complete quickly
6. **Truncate results** — max 10 matches per search term
7. **Input via CLI args** — `sys.argv[1:]`

### Template

```python
#!/usr/bin/env python3
"""PTC Script: <name>.py
Purpose: <what it does>
Usage: python3 scripts/<name>.py <args>
"""
import json
import sys
import subprocess
from pathlib import Path


def main(args: list[str]) -> dict:
    # Do the work
    result = {}
    # ... processing ...
    return result


if __name__ == "__main__":
    try:
        output = main(sys.argv[1:])
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
```

### Common Patterns

#### 1. Codebase Search

```python
def search_codebase(terms, file_pattern="**/*.py"):
    results = []
    for term in terms:
        proc = subprocess.run(
            ["grep", "-rn", "--include", file_pattern, term, "."],
            capture_output=True, text=True, timeout=30
        )
        if proc.stdout:
            matches = proc.stdout.strip().split("\n")[:10]
            results.append({
                "term": term,
                "matches": matches,
                "total": len(proc.stdout.strip().split("\n"))
            })
    return {"results": results, "truncated": any(r["total"] > 10 for r in results)}
```

#### 2. File Aggregation

```python
def aggregate_files(pattern):
    files = list(Path(".").glob(pattern))
    return {
        "count": len(files),
        "files": [str(f) for f in files[:20]],
        "truncated": len(files) > 20
    }
```

#### 3. Schema Validation

```python
import json
def validate_json(file_path, schema_path):
    with open(file_path) as f:
        data = json.load(f)
    with open(schema_path) as f:
        schema = json.load(f)
    errors = []
    # Basic validation (no jsonschema dependency)
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")
    return {"valid": len(errors) == 0, "errors": errors}
```

#### 4. Progress Tracking

```python
def read_progress(progress_file="claude-progress.txt"):
    path = Path(progress_file)
    if not path.exists():
        return {"entries": [], "count": 0}
    lines = path.read_text().strip().split("\n")
    return {"entries": lines[-10:], "count": len(lines), "truncated": len(lines) > 10}
```

## Anti-Patterns

**Don't**:
- Return raw grep output to Claude (use PTC instead)
- Install pip packages in PTC scripts
- Make network calls from PTC scripts
- Process more than needed (truncate early)
- Use PTC for creative/synthesis work (that's Claude's job)

**Do**:
- Use PTC for all searching, formatting, validation, aggregation
- Return structured JSON with counts and truncation flags
- Keep scripts focused on one task
- Include a `"truncated"` field when results are limited
