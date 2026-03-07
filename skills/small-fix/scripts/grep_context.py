#!/usr/bin/env python3
"""PTC Script: grep_context.py
Search codebase for relevant context. Returns structured JSON summary.
Only the JSON enters the model's context window.

Usage: python3 skills/small-fix/scripts/grep_context.py <term1> [term2] [--pattern "*.py"]
"""
import json
import subprocess
import sys


def search(terms: list[str], file_pattern: str = "*") -> dict:
    results = []
    for term in terms:
        try:
            proc = subprocess.run(
                ["grep", "-rn", "--include", file_pattern, term, "."],
                capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            results.append({"term": term, "error": "timeout", "matches": []})
            continue

        if proc.stdout:
            all_matches = proc.stdout.strip().split("\n")
            results.append({
                "term": term,
                "matches": all_matches[:10],
                "total": len(all_matches),
            })
        else:
            results.append({"term": term, "matches": [], "total": 0})

    return {
        "results": results,
        "truncated": any(r.get("total", 0) > 10 for r in results),
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: grep_context.py <term1> [term2] [--pattern '*.py']"}))
        sys.exit(1)

    pattern = "*"
    if "--pattern" in args:
        idx = args.index("--pattern")
        if idx + 1 < len(args):
            pattern = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    result = search(args, pattern)
    print(json.dumps(result, indent=2))
