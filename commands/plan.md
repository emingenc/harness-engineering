---
description: "Track 2 Phase 2: Generate a design document with bi-directional prompting"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash(python3 skills/planner/scripts/*.py:*)
  - Bash(python3 scripts/*.py:*)
---

# /plan — Track 2 Design Phase

Follow the planner skill workflow exactly:

1. **Load research** from `workspace/research/`. If no research exists, tell the user to run `/research <topic>` first.

2. **Draft design** using the template at `docs/templates/design-template.md`. Write to `workspace/designs/<name>-design.md`.

3. **Bi-directional prompting** — ask 3-5 clarifying questions (multiple choice preferred) BEFORE finalizing. Wait for answers.

4. **Revise** design based on answers.

5. **Validate**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/planner/scripts/validate_plan.py \
     "workspace/designs/<name>-design.md"
   ```

6. If `needs_decomposition` is true, split into Master Plan + Sub Plans.

7. **STOP** and tell the user:
   ```
   Design written to: workspace/designs/<name>-design.md

   NEXT STEPS:
   1. Open the design document
   2. Add annotations: <!-- ANNOTATION: your comment -->
   3. Run /split when done annotating
   ```

8. **Log**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/progress.py append "Design created: <name>-design.md"
   ```

**DO NOT proceed to implementation. STOP after writing the design.**
