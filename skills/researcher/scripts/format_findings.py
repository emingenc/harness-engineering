#!/usr/bin/env python3
"""PTC Script: format_findings.py
Format research findings into a markdown summary file.

Usage: echo '<json_findings>' | python3 skills/researcher/scripts/format_findings.py \
  --topic "<topic>" --output "workspace/research/<topic>.md"

Or: python3 skills/researcher/scripts/format_findings.py \
  --topic "<topic>" --output "workspace/research/<topic>.md" --findings '<json>'
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def format_research(topic: str, findings: dict, output_path: str) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    sections = []
    sections.append(f"# Research: {topic}")
    sections.append(f"\n**Date**: {timestamp}")
    sections.append(f"**Status**: Complete\n")

    # Key findings
    if "key_findings" in findings:
        sections.append("## Key Findings\n")
        for i, finding in enumerate(findings["key_findings"], 1):
            sections.append(f"{i}. {finding}")

    # Files examined
    if "files_examined" in findings:
        sections.append("\n## Files Examined\n")
        for f in findings["files_examined"]:
            sections.append(f"- `{f}`")

    # Search results summary
    if "search_results" in findings:
        sections.append("\n## Search Results Summary\n")
        for result in findings["search_results"]:
            term = result.get("term", "unknown")
            total = result.get("total_matches", 0)
            sections.append(f"- **{term}**: {total} matches")

    # Open questions
    if "open_questions" in findings:
        sections.append("\n## Open Questions\n")
        for q in findings["open_questions"]:
            sections.append(f"- {q}")

    # Recommendation
    if "recommendation" in findings:
        sections.append(f"\n## Recommendation\n\n{findings['recommendation']}")

    content = "\n".join(sections) + "\n"

    # Write to file
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content)

    return {
        "written_to": output_path,
        "sections": len(sections),
        "word_count": len(content.split()),
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    topic = "untitled"
    output = "workspace/research/findings.md"
    findings_json = None

    if "--topic" in args:
        idx = args.index("--topic")
        topic = args[idx + 1] if idx + 1 < len(args) else topic
    if "--output" in args:
        idx = args.index("--output")
        output = args[idx + 1] if idx + 1 < len(args) else output
    if "--findings" in args:
        idx = args.index("--findings")
        findings_json = args[idx + 1] if idx + 1 < len(args) else None

    if findings_json:
        findings = json.loads(findings_json)
    else:
        # Read from stdin
        findings = json.load(sys.stdin)

    result = format_research(topic, findings, output)
    print(json.dumps(result, indent=2))
