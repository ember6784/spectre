#!/usr/bin/env python3
"""
Spectre Build CLI - Execute Claude in a loop, one parent task per iteration.

The CLI handles the loop; Claude handles task tracking and progress writing.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


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


def run_claude_iteration(prompt: str) -> tuple[int, str, str]:
    """
    Execute Claude with the given prompt and stream output.

    Uses subprocess.Popen to invoke `claude -p`, passing the prompt via stdin.
    Streams stdout line-by-line for real-time visibility while buffering
    the full output for promise detection.

    Args:
        prompt: The full prompt to send to Claude

    Returns:
        Tuple of (exit_code, full_output, error_output)

    Raises:
        FileNotFoundError: If claude CLI is not installed
    """
    # Build command - use -p flag for print mode (non-interactive)
    cmd = ["claude", "-p"]

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

    # Buffer for full output (needed for promise detection)
    output_lines: list[str] = []

    # Stream stdout line-by-line, printing each immediately
    for line in process.stdout:
        print(line, end="", flush=True)
        output_lines.append(line)

    # Wait for process to complete
    process.wait()

    # Capture stderr for error reporting
    error_output = process.stderr.read()

    # Combine buffered output
    full_output = "".join(output_lines)

    return process.returncode, full_output, error_output


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

    # TODO: Build loop implementation in Task 2.2
    print("Build loop not yet implemented. Configuration validated successfully.")


if __name__ == "__main__":
    main()
