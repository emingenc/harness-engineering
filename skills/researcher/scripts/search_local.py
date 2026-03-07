#!/usr/bin/env python3
"""PTC Script: search_local.py
Search codebase for relevant code. Returns structured JSON summary.

Usage: python3 skills/researcher/scripts/search_local.py <term1> [term2] [--pattern "*.py"]
"""
import json
import subprocess
import sys


def search_codebase(terms: list[str], file_pattern: str = "*") -> dict:
    results = []
    for term in terms:
        try:
            proc = subprocess.run(
                ["grep", "-rn", "--include", file_pattern, term, "."],
                capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            results.append({"term": term, "error": "timeout", "matches": [], "total": 0})
            continue

        if proc.stdout:
            all_matches = proc.stdout.strip().split("\n")
            # Extract unique files
            files = list(set(m.split(":")[0] for m in all_matches if ":" in m))
            results.append({
                "term": term,
                "matches": all_matches[:10],
                "files": files[:10],
                "total_matches": len(all_matches),
                "total_files": len(files),
            })
        else:
            results.append({"term": term, "matches": [], "files": [], "total_matches": 0, "total_files": 0})

    return {
        "results": results,
        "truncated": any(r.get("total_matches", 0) > 10 for r in results),
        "summary": f"Searched {len(terms)} terms, found matches in {sum(r.get('total_files', 0) for r in results)} files",
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: search_local.py <term1> [term2] [--pattern '*.py']"}))
        sys.exit(1)

    pattern = "*"
    if "--pattern" in args:
        idx = args.index("--pattern")
        if idx + 1 < len(args):
            pattern = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    result = search_codebase(args, pattern)
    print(json.dumps(result, indent=2))
