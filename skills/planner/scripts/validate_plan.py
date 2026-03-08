#!/usr/bin/env python3
"""PTC Script: validate_plan.py
Validate a design document for completeness and size.

Usage: python3 skills/planner/scripts/validate_plan.py <design.md_path>
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: validate_plan.py <design.md_path>"}))
        sys.exit(1)

    result = validate(sys.argv[1])
    print(json.dumps(result, indent=2))
