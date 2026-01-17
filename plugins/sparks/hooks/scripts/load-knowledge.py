#!/usr/bin/env python3
"""
load-knowledge.py

SessionStart hook that injects the apply-knowledge skill and registry
directly into Claude's context.
"""

import json
import os
import sys
from pathlib import Path


def main():
    """Main entry point for SessionStart hook."""
    project_dir = Path.cwd()

    # Check if project has knowledge
    registry_path = (
        project_dir / ".claude" / "skills" / "apply-knowledge"
        / "references" / "knowledge-registry.toon"
    )

    if not registry_path.exists():
        sys.exit(0)

    # Read registry
    registry_content = registry_path.read_text().strip()
    entries = [l for l in registry_content.split('\n') if l.strip() and not l.startswith('#')]

    if not entries:
        sys.exit(0)

    # Read apply-knowledge skill from plugin
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    skill_path = Path(plugin_root) / "skills" / "apply-knowledge" / "SKILL.md"

    if skill_path.exists():
        skill_content = skill_path.read_text().strip()
    else:
        skill_content = "Apply-knowledge skill not found."

    # Build context with skill + registry injected
    context = f"""<project-knowledge>
This project has {len(entries)} captured knowledge entries.

## Apply-Knowledge Skill

{skill_content}

## Knowledge Registry

{registry_content}

Check triggers against current task and load relevant knowledge from references/.
</project-knowledge>"""

    # Visible notice for debugging (can remove later)
    visible_notice = f"sparks: {len(entries)} knowledge entries available"

    output = {
        "systemMessage": visible_notice,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
