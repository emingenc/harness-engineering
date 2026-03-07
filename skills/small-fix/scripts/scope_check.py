#!/usr/bin/env python3
"""PTC Script: scope_check.py
Estimates whether a fix is Track 1 (small) or should escalate to Track 2.

Usage: python3 skills/small-fix/scripts/scope_check.py "<description>"
"""
import json
import sys

ESCALATION_KEYWORDS = [
    "feature", "redesign", "refactor all", "migrate", "new system",
    "architecture", "rewrite", "overhaul", "multiple services",
    "database schema", "api design", "new module", "framework",
]

SMALL_FIX_KEYWORDS = [
    "fix", "bug", "typo", "import", "config", "update", "change",
    "rename", "correct", "patch", "adjust", "tweak", "broken",
    "error", "crash", "missing", "wrong", "incorrect",
]


def check_scope(description: str) -> dict:
    desc_lower = description.lower()

    escalation_matches = [kw for kw in ESCALATION_KEYWORDS if kw in desc_lower]
    small_matches = [kw for kw in SMALL_FIX_KEYWORDS if kw in desc_lower]

    if escalation_matches and not small_matches:
        scope = "escalate"
        reason = f"Matches escalation keywords: {', '.join(escalation_matches)}"
    elif len(escalation_matches) > len(small_matches):
        scope = "escalate"
        reason = f"More escalation signals ({len(escalation_matches)}) than fix signals ({len(small_matches)})"
    else:
        scope = "track1"
        reason = "Appears to be a small, surgical fix"

    return {
        "scope": scope,
        "reason": reason,
        "escalation_signals": escalation_matches,
        "fix_signals": small_matches,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: scope_check.py '<description>'"}))
        sys.exit(1)
    description = " ".join(sys.argv[1:])
    result = check_scope(description)
    print(json.dumps(result, indent=2))
