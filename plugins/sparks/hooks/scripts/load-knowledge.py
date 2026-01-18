#!/usr/bin/env python3
"""
load-knowledge.py

SessionStart hook that injects compliance instructions and registry
directly into Claude's context.

Reads from project-level registry at .claude/skills/find/references/registry.toon
No plugin dependency - purely reads from project.
"""

import json
import sys
from pathlib import Path


def count_registry_entries(lines: list[str]) -> int:
    """Count registry entries (lines with | that aren't comments)."""
    return sum(
        1 for line in lines
        if line.strip() and '|' in line and not line.startswith('#')
    )


def main():
    """Main entry point for SessionStart hook."""
    project_dir = Path.cwd()

    # Registry is in the project directory (inside sparks-find skill)
    registry_path = project_dir / ".claude" / "skills" / "sparks-find" / "references" / "registry.toon"

    if not registry_path.exists():
        sys.exit(0)

    # Read registry
    registry_content = registry_path.read_text().strip()
    lines = registry_content.split('\n') if registry_content else []

    # Count entries
    entry_count = count_registry_entries(lines)

    if entry_count == 0:
        sys.exit(0)

    # Build context with hardcoded compliance + registry
    context = f"""<sparks-knowledge>
This project has {entry_count} captured knowledge skills.

COMPLIANCE: Before searching codebase or dispatching agents, check if any
registered knowledge matches your current task. Load matching skills first
using: Skill({{skill-name}})

## Registry

{registry_content}

## How to Load

To load a skill: Read `.claude/skills/{{skill-name}}/SKILL.md`

Example: If registry has `feature-auth-flows|feature|auth, JWT|Use when implementing auth`
Then read: `.claude/skills/feature-auth-flows/SKILL.md`
</sparks-knowledge>"""

    # Visible notice
    visible_notice = f"sparks: {entry_count} knowledge skills available"

    output = {
        "systemMessage": visible_notice,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }

    print(json.dumps(output), flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
