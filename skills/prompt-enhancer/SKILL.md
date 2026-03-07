---
name: prompt-enhancer
description: >-
  Improve and enhance prompts for LLM interactions. Use when user says
  "improve this prompt", "make this prompt better", "enhance prompt",
  "review my prompt", or shares a prompt and asks for feedback.
tools: Read, Bash
---

# Prompt Enhancer

## Process

### Step 1: Analyze

Run the PTC analysis script:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/prompt-enhancer/scripts/enhance.py analyze "<prompt_text_or_file_path>"
```

Returns JSON with scores and suggestions:
```json
{
  "has_role": false,
  "has_examples": false,
  "has_output_format": true,
  "specificity_score": 3,
  "word_count": 42,
  "suggestions": ["Add role definition", "Include few-shot examples"]
}
```

### Step 2: Enhance

Apply surgical improvements based on analysis:
1. Add role definition if missing
2. Replace vague language with concrete instructions
3. Specify output format if missing
4. Add 1-2 few-shot examples if beneficial
5. Add constraints/negative examples where helpful

Do NOT over-engineer. If a dimension is already good, leave it.

### Step 3: Present

Run formatting script:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/prompt-enhancer/scripts/enhance.py format \
  --original "<original>" --enhanced "<enhanced>"
```

Show to user:
- Enhanced prompt (ready to copy)
- Before/after scores
- Brief rationale for each change

## Examples

### Example 1: Vague Prompt

**Input**: "Summarize this text"
**Output**: Enhanced with role ("You are a concise technical writer"), output format ("Provide a 3-bullet summary"), and constraints ("Focus on actionable insights, not background").

### Example 2: Good Prompt Missing Examples

**Input**: "You are a code reviewer. Review the following Python code for bugs and suggest fixes. Format output as a table with columns: Line, Issue, Fix."
**Output**: Added 1 few-shot example showing expected table format. Other dimensions left unchanged.

## Anti-Patterns

- Do NOT add complexity to already-good prompts
- Do NOT change the user's intent or domain focus
- Do NOT add unnecessary XML tags or formatting to simple prompts
