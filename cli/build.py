#!/usr/bin/env python3
"""
Spectre Build CLI - Execute Claude in a loop, one parent task per iteration.

The CLI handles the loop; Claude handles task tracking and progress writing.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Tools allowed to run without permission prompts
# Safety relies on: (1) directory scoping (Claude can only cd to children),
# (2) explicit tool allowlist, (3) git for rollback, (4) human oversight via streaming
ALLOWED_TOOLS = [
    "Bash",      # Run tests, lint, git commands
    "Read",      # Read files
    "Write",     # Create new files
    "Edit",      # Modify existing files
    "Glob",      # Find files by pattern
    "Grep",      # Search file contents
    "LS",        # List directories
    "TodoRead",  # Read task list
    "TodoWrite", # Update task list
]

# Tools explicitly denied - these would block the loop or are unsafe for automation
DENIED_TOOLS = [
    "AskUserQuestion",  # Would block waiting for user input
    "WebFetch",         # Network access - could hang or be slow
    "WebSearch",        # Network access
    "Task",             # Spawns subagents - unpredictable timing
    "Skill",            # Invokes skills - could have side effects
    "EnterPlanMode",    # Changes execution mode
    "NotebookEdit",     # Not needed for typical builds
]


@dataclass
class BuildStats:
    """Track statistics across the build."""
    start_time: float = field(default_factory=time.time)
    iterations_completed: int = 0
    iterations_failed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    tool_calls: dict = field(default_factory=dict)

    def add_usage(self, usage: dict) -> None:
        """Add token usage from an assistant message."""
        self.total_input_tokens += usage.get("input_tokens", 0)
        self.total_output_tokens += usage.get("output_tokens", 0)
        self.total_cache_read_tokens += usage.get("cache_read_input_tokens", 0)
        self.total_cache_write_tokens += usage.get("cache_creation_input_tokens", 0)

    def add_tool_call(self, tool_name: str) -> None:
        """Track a tool call."""
        self.tool_calls[tool_name] = self.tool_calls.get(tool_name, 0) + 1

    def elapsed_time(self) -> str:
        """Get formatted elapsed time."""
        elapsed = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def _progress_bar(self, value: float, width: int = 16) -> str:
        """Generate a progress bar string."""
        filled = int(value * width)
        empty = width - filled
        return "█" * filled + "░" * empty

    def _format_tokens(self, count: int) -> str:
        """Format token count for display (e.g., 1,337,066 or 1.3M)."""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count:,}"
        else:
            return str(count)

    def _calculate_rank(self) -> str:
        """Calculate a rank based on build performance."""
        total = self.iterations_completed + self.iterations_failed
        if total == 0:
            return "?"
        success_rate = self.iterations_completed / total
        if success_rate == 1.0 and self.iterations_completed >= 5:
            return "S+"
        elif success_rate == 1.0:
            return "S"
        elif success_rate >= 0.9:
            return "A"
        elif success_rate >= 0.7:
            return "B"
        elif success_rate >= 0.5:
            return "C"
        else:
            return "D"

    def print_summary(self, total_tasks: int | None = None) -> None:
        """Print a summary dashboard in shareable format."""
        # Calculate derived stats
        total_tokens = self.total_input_tokens + self.total_output_tokens
        total_cache = self.total_cache_read_tokens + self.total_cache_write_tokens
        cache_rate = self.total_cache_read_tokens / total_cache if total_cache > 0 else 0
        total_tool_calls = sum(self.tool_calls.values())
        rank = self._calculate_rank()

        # Task progress (use iterations as proxy if total_tasks not provided)
        tasks_done = self.iterations_completed
        tasks_total = total_tasks if total_tasks else tasks_done
        task_pct = tasks_done / tasks_total if tasks_total > 0 else 1.0

        # Format elapsed time for display (H:MM:SS format)
        elapsed = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        # Print the dashboard
        tasks_str = f"{self._progress_bar(task_pct)} {tasks_done}/{tasks_total}"
        cache_str = f"{self._progress_bar(cache_rate, 10)} {cache_rate*100:.0f}%"

        print()
        print("╭──────────────────────────────────────╮")
        print("│  $ spectre-build                     │")
        print("│                                      │")
        print("│  ══ MISSION COMPLETE ══              │")
        print("│                                      │")
        print(f"│  TIME       {time_str:<25}│")
        print(f"│  TASKS      {tasks_str:<25}│")
        print(f"│  COMMITS    {self.iterations_completed:<25}│")
        print(f"│  TOKENS     {self._format_tokens(total_tokens):<25}│")
        print(f"│  CACHE      {cache_str:<25}│")
        print(f"│  TOOLS      {total_tool_calls:<25}│")
        print("│                                      │")
        print("│  ─────────────────────────────────   │")
        print(f"│  RANK: {rank:<5}              exit 0   │")
        print("╰──────────────────────────────────────╯")
        print()

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


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="spectre-build",
        description="Execute Claude in a loop, completing one parent task per iteration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for inputs)
  python cli/build.py

  # Flag-based invocation
  python cli/build.py --tasks docs/tasks.md --context docs/scope.md

  # With multiple context files and custom iteration limit
  python cli/build.py --tasks docs/tasks.md --context docs/scope.md docs/plan.md --max-iterations 15
""",
    )

    parser.add_argument(
        "--tasks",
        type=str,
        help="Path to tasks.md file (required)",
    )

    parser.add_argument(
        "--context",
        type=str,
        nargs="*",
        default=[],
        help="Additional context file paths (optional, can specify multiple)",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of iterations (default: 10)",
    )

    return parser.parse_args()


def normalize_path(path: str) -> str:
    """
    Normalize a file path by stripping @ prefix if present.

    The @ prefix is a common convention meaning "relative to current directory".
    This function strips it so paths like @docs/file.md work as docs/file.md.

    Args:
        path: File path, possibly with @ prefix

    Returns:
        Path with @ prefix removed (if present)
    """
    if path.startswith("@"):
        return path[1:]
    return path


def prompt_for_tasks_file() -> str:
    """Interactively prompt for tasks file path."""
    while True:
        tasks_path = input("Tasks file path: ").strip()
        if tasks_path:
            return tasks_path
        print("Tasks file path is required.")


def prompt_for_context_files() -> list[str]:
    """Interactively prompt for optional context files."""
    print("Additional context files (comma-separated, or Enter to skip): ", end="")
    response = input().strip()

    if not response:
        return []

    # Split by comma and clean up each path
    paths = [p.strip() for p in response.split(",")]
    return [p for p in paths if p]  # Filter empty strings


def prompt_for_max_iterations() -> int:
    """Interactively prompt for max iterations with default."""
    default = 10
    print(f"Max iterations [{default}]: ", end="")
    response = input().strip()

    if not response:
        return default

    try:
        value = int(response)
        if value > 0:
            return value
        print(f"Must be positive. Using default: {default}")
        return default
    except ValueError:
        print(f"Invalid number. Using default: {default}")
        return default


def validate_inputs(
    tasks_file: str, context_files: list[str], max_iterations: int
) -> bool:
    """
    Validate all inputs before starting build loop.

    Returns True if valid, exits with error message if not.
    """
    errors = []

    # Check tasks file exists and is readable
    tasks_path = Path(tasks_file)
    if not tasks_path.exists():
        errors.append(f"Tasks file not found: {tasks_file}")
    elif not tasks_path.is_file():
        errors.append(f"Tasks path is not a file: {tasks_file}")
    elif not os.access(tasks_path, os.R_OK):
        errors.append(f"Tasks file is not readable: {tasks_file}")

    # Check context files exist if provided
    for ctx_file in context_files:
        ctx_path = Path(ctx_file)
        if not ctx_path.exists():
            errors.append(f"Context file not found: {ctx_file}")
        elif not ctx_path.is_file():
            errors.append(f"Context path is not a file: {ctx_file}")
        elif not os.access(ctx_path, os.R_OK):
            errors.append(f"Context file is not readable: {ctx_file}")

    # Check max-iterations is positive
    if max_iterations <= 0:
        errors.append(f"Max iterations must be positive: {max_iterations}")

    # Report errors and exit if any
    if errors:
        print("Validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    return True


def format_tool_call(name: str, input_data: dict) -> str:
    """Format a tool call for display."""
    if name == "Read":
        path = input_data.get("file_path", "?")
        # Shorten path for display
        if len(path) > 50:
            path = "..." + path[-47:]
        return f"📄 Read: {path}"
    elif name == "Edit":
        path = input_data.get("file_path", "?")
        if len(path) > 50:
            path = "..." + path[-47:]
        return f"✏️  Edit: {path}"
    elif name == "Write":
        path = input_data.get("file_path", "?")
        if len(path) > 50:
            path = "..." + path[-47:]
        return f"📝 Write: {path}"
    elif name == "Bash":
        cmd = input_data.get("command", "?")
        # Truncate long commands
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."
        return f"💻 Bash: {cmd}"
    elif name == "Glob":
        pattern = input_data.get("pattern", "?")
        return f"🔍 Glob: {pattern}"
    elif name == "Grep":
        pattern = input_data.get("pattern", "?")
        return f"🔎 Grep: {pattern}"
    elif name == "TodoWrite":
        return "📋 TodoWrite"
    else:
        return f"🔧 {name}"


def process_stream_event(event: dict, text_buffer: list[str], stats: BuildStats | None = None) -> None:
    """
    Process a single stream-json event and display formatted output.

    Args:
        event: Parsed JSON event from Claude stream
        text_buffer: List to accumulate assistant text for promise detection
        stats: Optional BuildStats to track token usage and tool calls
    """
    event_type = event.get("type")

    if event_type == "assistant":
        # Assistant message - may contain text and/or tool_use
        message = event.get("message", {})
        content = message.get("content", [])

        # Track token usage if stats provided
        if stats and "usage" in message:
            stats.add_usage(message["usage"])

        for item in content:
            item_type = item.get("type")

            if item_type == "text":
                text = item.get("text", "")
                if text.strip():
                    print(f"💬 {text}")
                    text_buffer.append(text)

            elif item_type == "tool_use":
                tool_name = item.get("name", "?")
                tool_input = item.get("input", {})
                formatted = format_tool_call(tool_name, tool_input)
                print(formatted)
                # Track tool call
                if stats:
                    stats.add_tool_call(tool_name)

    # Skip system events and tool_result events (too noisy)


def run_claude_iteration(
    prompt: str,
    timeout: int | None = None,
    stats: BuildStats | None = None,
) -> tuple[int, str, str]:
    """
    Execute Claude with the given prompt and stream formatted output.

    Uses subprocess.Popen to invoke `claude -p` with stream-json output,
    parsing events to display formatted tool calls and assistant messages
    while buffering text for promise detection.

    Args:
        prompt: The full prompt to send to Claude
        timeout: Optional timeout in seconds for the subprocess
        stats: Optional BuildStats to track token usage and tool calls

    Returns:
        Tuple of (exit_code, full_text_output, error_output)

    Raises:
        FileNotFoundError: If claude CLI is not installed
        subprocess.TimeoutExpired: If timeout is exceeded
    """
    # Build command for safe automated execution with structured output
    # - allowedTools: auto-approve these without prompting
    # - disallowedTools: block these entirely (prevents loop blocking)
    cmd = [
        "claude", "-p",
        "--allowedTools", ",".join(ALLOWED_TOOLS),
        "--disallowedTools", ",".join(DENIED_TOOLS),
        "--output-format", "stream-json",
        "--verbose",
    ]

    # Start subprocess with pipes for all streams
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Pass prompt via stdin and close to signal end of input
    process.stdin.write(prompt)
    process.stdin.close()

    # Buffer for assistant text (needed for promise detection)
    text_buffer: list[str] = []

    # Process stream-json events line by line
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
            process_stream_event(event, text_buffer, stats)
        except json.JSONDecodeError:
            # Not valid JSON, might be raw output - print it
            print(line)
            text_buffer.append(line)

    # Wait for process to complete (with optional timeout)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise

    # Capture stderr for error reporting
    error_output = process.stderr.read()

    # Combine buffered text for promise detection
    full_output = "\n".join(text_buffer)

    return process.returncode, full_output, error_output


def detect_promise(output: str) -> str | None:
    """
    Extract promise tag from Claude's output.

    Searches for [[PROMISE:...]] pattern and returns the promise text
    if found. Promise text is stripped of whitespace.

    Args:
        output: Full output from Claude subprocess

    Returns:
        Promise text ("TASK_COMPLETE" or "BUILD_COMPLETE") if found, None otherwise
    """
    match = re.search(r"\[\[PROMISE:(.*?)\]\]", output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def main() -> None:
    """Main entry point for Spectre Build CLI."""
    args = parse_args()

    # Get tasks file - from args or interactive prompt
    tasks_file = args.tasks
    if not tasks_file:
        tasks_file = prompt_for_tasks_file()

    # Determine if running in flag mode (--tasks provided) or interactive mode
    flag_mode = args.tasks is not None

    # Get context files - from args in flag mode, prompt in interactive mode
    context_files = args.context if flag_mode else prompt_for_context_files()

    # Get max iterations - from args or interactive prompt (only if interactive mode)
    if flag_mode:
        # Flag mode - use args value directly
        max_iterations = args.max_iterations
    else:
        # Interactive mode - prompt for confirmation/override
        max_iterations = prompt_for_max_iterations()

    # Normalize paths (strip @ prefix if present)
    tasks_file = normalize_path(tasks_file)
    context_files = [normalize_path(f) for f in context_files]

    # Validate all inputs before proceeding
    validate_inputs(tasks_file, context_files, max_iterations)

    # Convert to absolute paths for consistency
    tasks_file = str(Path(tasks_file).resolve())
    context_files = [str(Path(f).resolve()) for f in context_files]

    # Display configuration
    print("\n--- Spectre Build Configuration ---")
    print(f"Tasks file: {tasks_file}")
    print(f"Context files: {context_files if context_files else 'None'}")
    print(f"Max iterations: {max_iterations}")
    print("-----------------------------------\n")

    # Initialize stats tracking
    stats = BuildStats()

    # Main build loop
    iteration = 0
    while iteration < max_iterations:
        iteration += 1

        # Print iteration header with promise reference
        print(f"\n{'='*60}")
        print(f"🔄 Iteration {iteration}/{max_iterations}")
        print(f"   Complete task: [[PROMISE:TASK_COMPLETE]]")
        print(f"   All done: [[PROMISE:BUILD_COMPLETE]]")
        print(f"{'='*60}\n")

        # Build fresh prompt each iteration
        prompt = build_prompt(tasks_file, context_files)

        # Invoke Claude subprocess with constructed prompt
        try:
            exit_code, output, stderr = run_claude_iteration(prompt, stats=stats)
        except FileNotFoundError:
            print(f"\n{'='*60}", file=sys.stderr)
            print("❌ ERROR: Claude CLI not found", file=sys.stderr)
            print(f"   Iteration: {iteration}/{max_iterations}", file=sys.stderr)
            print("", file=sys.stderr)
            print("The 'claude' command is not installed or not in PATH.", file=sys.stderr)
            print("Install Claude Code CLI: https://claude.ai/code", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            stats.print_summary()
            sys.exit(127)  # Standard exit code for command not found
        except subprocess.TimeoutExpired:
            print(f"\n{'='*60}", file=sys.stderr)
            print("❌ ERROR: Claude execution timed out", file=sys.stderr)
            print(f"   Iteration: {iteration}/{max_iterations}", file=sys.stderr)
            print("", file=sys.stderr)
            print("The Claude subprocess exceeded the allowed time.", file=sys.stderr)
            print("Consider increasing timeout or breaking down tasks.", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            stats.iterations_failed += 1
            stats.print_summary()
            sys.exit(124)  # Standard exit code for timeout

        # Check for promise FIRST - if agent completed its task, trust that
        promise = detect_promise(output)

        # Handle non-zero exit code, but only fail if there's no valid promise
        if exit_code != 0:
            if promise:
                # Agent completed task despite non-zero exit - warn but continue
                print(f"\n⚠ Claude exited with code {exit_code}, but task completed.")
            else:
                # No promise and non-zero exit - this is a real failure
                print(f"\n{'='*60}", file=sys.stderr)
                print(f"❌ ERROR: Claude exited with code {exit_code}", file=sys.stderr)
                print(f"   Iteration: {iteration}/{max_iterations}", file=sys.stderr)
                if stderr:
                    print("", file=sys.stderr)
                    print("stderr output:", file=sys.stderr)
                    print(stderr, file=sys.stderr)
                print(f"{'='*60}", file=sys.stderr)
                stats.iterations_failed += 1
                stats.print_summary()
                sys.exit(exit_code)

        # Handle promise-based flow control
        if promise == "BUILD_COMPLETE":
            stats.iterations_completed += 1
            print(f"\n{'='*60}")
            print("✅ BUILD COMPLETE - All tasks finished!")
            print(f"{'='*60}")
            stats.print_summary()
            sys.exit(0)
        elif promise == "TASK_COMPLETE":
            stats.iterations_completed += 1
            print(f"\n✓ Task complete. Continuing to next iteration...")
            # Loop continues to next iteration
        else:
            # No promise detected - Claude may need more work
            print(f"\n⚠ No promise detected. Continuing to next iteration...")
            # Loop continues to next iteration

    # Max iterations reached
    print(f"\n{'='*60}")
    print(f"⚠ Max iterations ({max_iterations}) reached. Build incomplete.")
    print("   Review build_progress.md and tasks file to assess state.")
    print(f"{'='*60}")
    stats.print_summary()
    sys.exit(1)


if __name__ == "__main__":
    main()
