---
description: "Track 2 Phase 1: Research a topic using parallel sub-agents and PTC scripts"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Agent
  - Write
  - Bash(python3 skills/researcher/scripts/*.py:*)
  - Bash(python3 scripts/*.py:*)
---

# /research — Track 2 Research Phase

You have been asked to research: **$1**

Follow the researcher skill workflow exactly:

1. **Define** 3-5 specific research questions about "$1"

2. **Local search** first via PTC:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/researcher/scripts/search_local.py <relevant_terms>
   ```

3. **Read** only the most relevant files from the search results

4. **Sub-agents** for deeper questions (spawn in parallel if independent):
   Use Agent tool with `subagent_type: "Explore"` for each independent question

5. **External docs** via context7 MCP only if local search is insufficient

6. **Synthesize** findings:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/researcher/scripts/format_findings.py \
     --topic "$1" --output "workspace/research/$1.md" --findings '<json>'
   ```

7. **Present** key findings and recommend next steps

8. **Log**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Research complete: $1"
   ```
