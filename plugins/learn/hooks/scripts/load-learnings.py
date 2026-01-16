#!/usr/bin/env python3
"""
load-learnings.py

SessionStart hook that prompts Claude to use the apply-learnings skill.
Only fires if the project has captured learnings.
"""

import json
import sys
from pathlib import Path


def main():
    """Main entry point for SessionStart hook."""
    project_dir = Path.cwd()

    # Check if project has learnings
    registry_path = (
        project_dir / ".claude" / "skills" / "apply-learnings"
        / "references" / "registry.toon"
    )

    if not registry_path.exists():
        sys.exit(0)

    # Count entries (non-empty, non-comment lines)
    content = registry_path.read_text().strip()
    entries = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]

    if not entries:
        sys.exit(0)

    # Prompt Claude to use the skill
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"<project-learnings>\n"
                f"This project has {len(entries)} captured learnings. "
                f"Use the `apply-learnings` skill before starting implementation work.\n"
                f"</project-learnings>"
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
