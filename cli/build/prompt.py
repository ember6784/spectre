"""
Prompt template and construction for build iterations.

The prompt is identical every iteration - only file paths are substituted.
Claude reads files directly; prompt just points to them.
"""

from pathlib import Path


# Prompt template - identical every iteration, only file paths are substituted
PROMPT_TEMPLATE = """\
# SPECTRE Build Loop

You are being invoked by an outer loop. You will complete **exactly ONE parent task**, then STOP.

---

## Files

- **Tasks**: `{tasks_file_path}`
- **Progress**: `{progress_file_path}`
- **Additional Context**: {additional_context_paths_or_none}

---

## Control Flow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Context Gathering                                  │
│  STEP 2: Task Planning (select ONE task)                    │
│  STEP 3: Task Execution (implement selected task)           │
│  STEP 4: Verification (lint + tests)                        │
│  STEP 5: Progress Update (commit + write progress)          │
│  STEP 6: STOP (output promise, end response)                │
└─────────────────────────────────────────────────────────────┘
```

---

## STEP 1: Context Gathering

Read and understand the current state before doing any work.

1. **Read the progress file** (if it exists)
   - Check **Codebase Patterns** section for patterns from prior iterations
   - Review iteration logs to understand what was accomplished
   - Note any recommended task updates or blockers

2. **Read the additional context files** (if provided)
   - Understand scope, requirements, and constraints

3. **Read the tasks file**
   - Parent tasks marked `[x]` are complete
   - Parent tasks marked `[ ]` are incomplete

---

## STEP 2: Task Planning

Select **exactly ONE** incomplete parent task to work on.

- Usually this is the next sequential task
- Use judgment if dependencies have shifted or a task is blocked
- If a task is obsolete, mark it `[x]` with "Skipped - {{reason}}" and select another
- You will execute ONE task — the loop handles the rest

**Output**: Clearly state which parent task you are working on.

---

## STEP 3: Task Execution

Implement the selected parent task.

- Complete all sub-tasks under the parent task
- Mark sub-tasks as `[x]` in the tasks file as you complete them
- Mark the parent task as `[x]` when all sub-tasks are done

⚠️ **ONE TASK ONLY** — Do NOT start the next parent task. Stop after this one.

---

## STEP 4: Verification

Verify your work before committing.

- Run linting on files you created or modified
- Run tests relevant to files you touched
- Fix any failures before proceeding
- Do NOT skip this step

---

## STEP 5: Progress Update

Record your work, then STOP.

1. **Commit your changes**
   - Stage all files changed for this task
   - Commit message format: `feat({{task_id}}): {{brief description}}`

2. **Write to the progress file at `{progress_file_path}`**

   ⚠️ **Write to this EXACT path**: `{progress_file_path}`

   If the file doesn't exist, create it with this structure:
   ```markdown
   # Build Progress

   ## Codebase Patterns
   <!-- Patterns discovered during build -->

   ---
   ```

   Then append your iteration log:
   ```markdown
   ## Iteration — {{Parent Task Title}}
   **Status**: Complete
   **What Was Done**: [2-3 sentence summary]
   **Files Changed**: [list]
   **Key Decisions**: [bullets or "None"]
   **Blockers/Risks**: [bullets or "None"]
   ```

3. **IMMEDIATELY proceed to STEP 6** — Do NOT start another task.

---

## STEP 6: STOP

⛔ **STOP NOW. DO NOT CONTINUE.**

You have completed ONE parent task. Your iteration is DONE.

Output the promise tag and **end your response immediately**:

- More tasks remain → `[[PROMISE:TASK_COMPLETE]]`
- All tasks complete → `[[PROMISE:BUILD_COMPLETE]]`

**Do NOT:**
- Start the next task
- Plan the next task
- Do any more work

The outer loop will call you again for the next task.

---

## Promise Integrity

- Only output promises that are **genuinely true**
- Do NOT output false promises to escape the loop
- If blocked, document the blocker and continue trying
"""


def build_prompt(tasks_file: str, context_files: list[str]) -> str:
    """
    Build the iteration prompt from the template.

    The prompt is identical every iteration - only file paths are substituted.
    Claude reads files directly; prompt just points to them.

    Args:
        tasks_file: Absolute path to the tasks file
        context_files: List of absolute paths to additional context files

    Returns:
        The constructed prompt string ready to send to Claude
    """
    # Derive progress file path (same directory as tasks file, named build_progress.md)
    tasks_path = Path(tasks_file)
    progress_file = str(tasks_path.parent / "build_progress.md")

    # Format additional context paths or "None"
    if context_files:
        additional_context = ", ".join(f"`{f}`" for f in context_files)
    else:
        additional_context = "None"

    # Substitute variables into template
    prompt = PROMPT_TEMPLATE.format(
        tasks_file_path=tasks_file,
        progress_file_path=progress_file,
        additional_context_paths_or_none=additional_context,
    )

    return prompt
