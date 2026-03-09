#!/usr/bin/env python3
"""PTC Script: plan_diff.py
Compare two design documents and report differences.

Usage: python3 scripts/plan_diff.py <design1.md> <design2.md>
"""
import json
import re
import sys
from pathlib import Path

SECTION_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
ANNOTATION_PATTERN = re.compile(r"<!-- ANNOTATION:\s*(.*?)\s*-->")
TASK_PATTERN = re.compile(r"^\s*\d+\.\s+.+", re.MULTILINE)


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


def diff_designs(path1: str, path2: str) -> dict:
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

    # Compute diffs
    all_sections = set(sections1.keys()) | set(sections2.keys())
    added_sections = set(sections2.keys()) - set(sections1.keys())
    removed_sections = set(sections1.keys()) - set(sections2.keys())
    changed_sections = []
    for s in all_sections - added_sections - removed_sections:
        if sections1.get(s) != sections2.get(s):
            changed_sections.append(s)

    added_annotations = annotations2 - annotations1
    removed_annotations = annotations1 - annotations2

    return {
        "design1": path1,
        "design2": path2,
        "sections_added": sorted(added_sections),
        "sections_removed": sorted(removed_sections),
        "sections_changed": sorted(changed_sections),
        "annotations_added": sorted(added_annotations),
        "annotations_removed": sorted(removed_annotations),
        "annotation_count_delta": len(annotations2) - len(annotations1),
        "task_count_delta": len(tasks2) - len(tasks1),
        "task_count": {"design1": len(tasks1), "design2": len(tasks2)},
        "word_count": {
            "design1": len(content1.split()),
            "design2": len(content2.split()),
        },
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: plan_diff.py <design1.md> <design2.md>"}))
        sys.exit(1)

    result = diff_designs(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
