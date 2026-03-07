#!/usr/bin/env python3
"""PTC Script: enhance.py
Analyze and format prompts for the prompt-enhancer skill.

Usage:
  python3 skills/prompt-enhancer/scripts/enhance.py analyze "<prompt>"
  python3 skills/prompt-enhancer/scripts/enhance.py format --original "<orig>" --enhanced "<new>"
"""
import json
import re
import sys
from pathlib import Path

ROLE_PATTERNS = [
    r"you are\b", r"act as\b", r"your role\b", r"as a\b",
    r"pretend you", r"imagine you",
]
EXAMPLE_PATTERNS = [
    r"example:", r"for example", r"e\.g\.", r"such as:",
    r"here is an example", r"input:.*output:",
]
FORMAT_PATTERNS = [
    r"format:", r"output format", r"respond with",
    r"return as", r"provide in", r"json", r"markdown",
    r"table", r"bullet", r"numbered list",
]


def analyze(prompt_text: str) -> dict:
    text_lower = prompt_text.lower()
    words = prompt_text.split()

    has_role = any(re.search(p, text_lower) for p in ROLE_PATTERNS)
    has_examples = any(re.search(p, text_lower) for p in EXAMPLE_PATTERNS)
    has_output_format = any(re.search(p, text_lower) for p in FORMAT_PATTERNS)

    # Specificity: rough heuristic based on concrete vs vague words
    vague_words = {"good", "better", "nice", "some", "things", "stuff", "etc",
                   "maybe", "probably", "something", "anything", "whatever"}
    vague_count = sum(1 for w in words if w.lower().strip(".,!?") in vague_words)
    specificity = max(1, min(5, 5 - vague_count))

    suggestions = []
    if not has_role:
        suggestions.append("Add role definition (e.g., 'You are a ...')")
    if not has_examples and len(words) > 20:
        suggestions.append("Include 1-2 few-shot examples")
    if not has_output_format:
        suggestions.append("Specify output format")
    if specificity < 3:
        suggestions.append("Replace vague language with concrete instructions")
    if len(words) < 10:
        suggestions.append("Prompt is very short; consider adding more context")

    return {
        "has_role": has_role,
        "has_examples": has_examples,
        "has_output_format": has_output_format,
        "specificity_score": specificity,
        "word_count": len(words),
        "suggestions": suggestions,
    }


def format_comparison(original: str, enhanced: str) -> dict:
    orig_analysis = analyze(original)
    enh_analysis = analyze(enhanced)

    return {
        "original": {
            "text": original,
            "scores": orig_analysis,
        },
        "enhanced": {
            "text": enhanced,
            "scores": enh_analysis,
        },
        "improvements": [
            k for k in ["has_role", "has_examples", "has_output_format"]
            if not orig_analysis[k] and enh_analysis[k]
        ],
        "specificity_delta": enh_analysis["specificity_score"] - orig_analysis["specificity_score"],
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: enhance.py <analyze|format> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "analyze":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: enhance.py analyze '<prompt>'"}))
            sys.exit(1)
        text = sys.argv[2]
        # If it's a file path, read it
        if Path(text).exists():
            text = Path(text).read_text()
        result = analyze(text)

    elif cmd == "format":
        args = sys.argv[2:]
        original = enhanced = ""
        if "--original" in args:
            idx = args.index("--original")
            original = args[idx + 1] if idx + 1 < len(args) else ""
        if "--enhanced" in args:
            idx = args.index("--enhanced")
            enhanced = args[idx + 1] if idx + 1 < len(args) else ""
        result = format_comparison(original, enhanced)

    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
