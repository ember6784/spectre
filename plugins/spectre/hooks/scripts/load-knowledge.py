#!/usr/bin/env python3
"""
load-knowledge.py

SessionStart hook that injects the apply skill content with embedded registry
directly into Claude's context.

Reads:
- Apply skill from plugin: skills/spectre-apply/SKILL.md
- Registry from project: .claude/skills/spectre-recall/references/registry.toon

Combines them by replacing the Registry Location section with actual registry content.
"""

import json
import os
import re
import sys
from pathlib import Path


def count_registry_entries(lines: list[str]) -> int:
    """Count registry entries (lines with | that aren't comments)."""
    return sum(
        1 for line in lines
        if line.strip() and '|' in line and not line.startswith('#')
    )


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    if content.startswith('---'):
        # Find the closing ---
        end = content.find('---', 3)
        if end != -1:
            return content[end + 3:].strip()
    return content


def main():
    """Main entry point for SessionStart hook."""
    project_dir = Path.cwd()
    plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', ''))

    apply_skill_path = plugin_root / "skills" / "spectre-apply" / "SKILL.md"

    if not apply_skill_path.exists():
        sys.exit(0)

    # Paths - check new name first, fall back to old names for migration
    registry_path = project_dir / ".claude" / "skills" / "spectre-recall" / "references" / "registry.toon"
    old_registry_path = project_dir / ".claude" / "skills" / "spectre-find" / "references" / "registry.toon"

    # Support old "spectre-find" path for projects that haven't migrated
    if not registry_path.exists() and old_registry_path.exists():
        registry_path = old_registry_path

    # Read registry if it exists
    registry_content = ""
    entry_count = 0
    if registry_path.exists():
        registry_content = registry_path.read_text().strip()
        lines = registry_content.split('\n') if registry_content else []
        entry_count = count_registry_entries(lines)

    # Read apply skill and strip frontmatter
    apply_content = apply_skill_path.read_text()
    apply_content = strip_frontmatter(apply_content)

    # Replace the Registry Location section with embedded registry or empty notice
    if entry_count > 0:
        registry_section = f"""## Registry

**Format**: `skill-name|category|triggers|description`

```
{registry_content}
```

Each entry corresponds to a skill that can be loaded via `Skill({{skill-name}})`

**Categories:** feature, gotchas, patterns, decisions, procedures, integration, performance, testing, ux, strategy"""
    else:
        registry_section = """## Registry

No knowledge has been captured for this project yet. The behavioral rules in this document still apply.

To capture knowledge from this session, use `/spectre:learn` after completing significant work.

**Categories:** feature, gotchas, patterns, decisions, procedures, integration, performance, testing, ux, strategy"""

    # Replace the Registry Location section
    apply_content = re.sub(
        r'## Registry Location.*?(?=## Workflow)',
        registry_section + '\n\n',
        apply_content,
        flags=re.DOTALL
    )

    # Build final context
    context = f"<spectre-knowledge>\n{apply_content}\n</spectre-knowledge>"

    # Visible notice
    if entry_count > 0:
        visible_notice = f"👻 spectre: {entry_count} knowledge skills available"
    else:
        visible_notice = "👻 spectre: ready — capture knowledge with /spectre:learn"

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
