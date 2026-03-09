#!/usr/bin/env python3
"""PTC Script: validate_plan.py
Validate a design document for completeness and size.

Usage:
  python3 skills/planner/scripts/validate_plan.py <design.md_path>
  python3 skills/planner/scripts/validate_plan.py <design.md_path> --diff <design2.md_path>
"""
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "Problem Statement",
    "Proposed Solution",
    "Architecture",
    "Trade-offs",
    "Verification Strategy",
    "Micro-Task Breakdown",
]

# Approximate tokens per word ratio
TOKENS_PER_WORD = 1.33
MAX_TOKENS = 30000

ANNOTATION_PATTERN = re.compile(r"<!-- ANNOTATION:.*?-->")
TASK_PATTERN = re.compile(r"^\d+\.\s+.*(?:scope|S|M|L)", re.MULTILINE)
SECTION_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def extract_sections(content: str) -> dict[str, str]:
    """Extract section headers and their content."""
    sections = {}
    matches = list(SECTION_PATTERN.finditer(content))
    for i, match in enumerate(matches):
        name = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[name] = content[start:end].strip()
    return sections


def validate(design_path: str) -> dict:
    path = Path(design_path)
    if not path.exists():
        return {"valid": False, "error": f"File not found: {design_path}"}

    content = path.read_text()
    lines = content.split("\n")
    words = content.split()
    estimated_tokens = int(len(words) * TOKENS_PER_WORD)

    # Check required sections
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        # Look for section header (## or ###)
        pattern = rf"^#{{1,3}}\s+.*{re.escape(section)}"
        if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            missing_sections.append(section)

    # Check for empty sections (header followed immediately by another header or end)
    empty_sections = []
    for i, line in enumerate(lines):
        if line.startswith("##"):
            # Check if next non-empty line is also a header
            for j in range(i + 1, min(i + 5, len(lines))):
                stripped = lines[j].strip()
                if stripped:
                    if stripped.startswith("#"):
                        section_name = line.lstrip("#").strip()
                        empty_sections.append(section_name)
                    break

    # Check for annotations
    annotations = re.findall(r"<!-- ANNOTATION:.*?-->", content)

    # Check for micro-tasks
    task_pattern = r"^\d+\.\s+.*(?:scope|S|M|L)"
    tasks = re.findall(task_pattern, content, re.MULTILINE)

    # Determine if decomposition needed
    needs_decomposition = estimated_tokens > MAX_TOKENS

    issues = []
    if missing_sections:
        issues.append(f"Missing sections: {', '.join(missing_sections)}")
    if empty_sections:
        issues.append(f"Empty sections: {', '.join(empty_sections)}")
    if not tasks:
        issues.append("No micro-task breakdown found")

    return {
        "valid": len(issues) == 0,
        "design_path": design_path,
        "lines": len(lines),
        "words": len(words),
        "estimated_tokens": estimated_tokens,
        "needs_decomposition": needs_decomposition,
        "missing_sections": missing_sections,
        "empty_sections": empty_sections,
        "annotation_count": len(annotations),
        "task_count": len(tasks),
        "issues": issues,
    }


def diff_designs(path1: str, path2: str) -> dict:
    """Compare two design documents."""
    p1 = Path(path1)
    p2 = Path(path2)

    if not p1.exists():
        return {"error": f"File not found: {path1}"}
    if not p2.exists():
        return {"error": f"File not found: {path2}"}

    content1 = p1.read_text()
    content2 = p2.read_text()

    sections1 = extract_sections(content1)
    sections2 = extract_sections(content2)

    annotations1 = set(ANNOTATION_PATTERN.findall(content1))
    annotations2 = set(ANNOTATION_PATTERN.findall(content2))

    tasks1 = TASK_PATTERN.findall(content1)
    tasks2 = TASK_PATTERN.findall(content2)

    all_sections = set(sections1.keys()) | set(sections2.keys())
    added = set(sections2.keys()) - set(sections1.keys())
    removed = set(sections1.keys()) - set(sections2.keys())
    changed = []
    for s in all_sections - added - removed:
        if sections1.get(s) != sections2.get(s):
            changed.append(s)

    return {
        "design1": path1,
        "design2": path2,
        "sections_added": sorted(added),
        "sections_removed": sorted(removed),
        "sections_changed": sorted(changed),
        "annotation_count_delta": len(annotations2) - len(annotations1),
        "task_count_delta": len(tasks2) - len(tasks1),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: validate_plan.py <design.md_path> [--diff <design2.md>]"}))
        sys.exit(1)

    if "--diff" in sys.argv:
        idx = sys.argv.index("--diff")
        if idx + 1 < len(sys.argv):
            result = diff_designs(sys.argv[1], sys.argv[idx + 1])
        else:
            result = {"error": "--diff requires a second design path"}
    else:
        result = validate(sys.argv[1])

    print(json.dumps(result, indent=2))
