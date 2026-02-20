#!/usr/bin/env python3
"""Tests for load-knowledge.py SessionStart hook."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent / "load-knowledge.py"


def create_apply_skill(plugin_dir: Path) -> Path:
    """Create a minimal apply skill file with the expected Registry Location section."""
    skill_path = plugin_dir / "skills" / "spectre-apply" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(
        "---\nname: spectre-apply\n---\n\n# Apply Knowledge\n\n"
        "## Registry Location\n\nThe registry is at somewhere\n\n"
        "## Workflow\n\nDo things.\n"
    )
    return skill_path


def create_registry(project_dir: Path, entries: str, subdir: str = "spectre-recall") -> Path:
    """Create a registry.toon file with given entries."""
    registry_path = (
        project_dir / ".claude" / "skills" / subdir / "references" / "registry.toon"
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(entries)
    return registry_path


def run_hook(plugin_root: str = "", project_dir: str = "", cwd: str = "") -> subprocess.CompletedProcess:
    """Run load-knowledge.py with given environment."""
    env = os.environ.copy()
    if plugin_root:
        env["CLAUDE_PLUGIN_ROOT"] = plugin_root
    else:
        env.pop("CLAUDE_PLUGIN_ROOT", None)
    if project_dir:
        env["CLAUDE_PROJECT_DIR"] = project_dir
    else:
        env.pop("CLAUDE_PROJECT_DIR", None)

    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        cwd=cwd or None,
        env=env,
    )


class TestLoadKnowledge:
    """Core behavioral tests for load-knowledge hook."""

    def test_exits_silently_when_no_plugin_root(self, tmp_path):
        """When CLAUDE_PLUGIN_ROOT is missing, exits with no output."""
        result = run_hook(plugin_root="", cwd=str(tmp_path))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_exits_silently_when_apply_skill_missing(self, tmp_path):
        """When apply skill doesn't exist at plugin root, exits silently."""
        result = run_hook(plugin_root=str(tmp_path), cwd=str(tmp_path))
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_outputs_ready_message_when_no_registry(self, tmp_path):
        """When apply skill exists but no registry, shows 'ready' message."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        result = run_hook(plugin_root=str(plugin_dir), cwd=str(tmp_path))

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "ready" in output["systemMessage"]
        assert "/spectre:learn" in output["systemMessage"]

    def test_outputs_entry_count_when_registry_has_entries(self, tmp_path):
        """When registry has entries, shows count in system message."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        create_registry(
            project_dir,
            "# SPECTRE Knowledge Registry\n"
            "# Format: skill-name|category|triggers|description\n\n"
            "feature-auth|feature|auth, login|Auth system knowledge\n"
            "gotcha-db|gotchas|database, query|DB gotchas\n",
        )

        result = run_hook(
            plugin_root=str(plugin_dir),
            project_dir=str(project_dir),
            cwd=str(tmp_path),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "2 knowledge skills" in output["systemMessage"]

    def test_uses_claude_project_dir_over_cwd(self, tmp_path):
        """CLAUDE_PROJECT_DIR takes precedence over cwd for registry lookup."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        # Put registry in project_dir, NOT in cwd
        project_dir = tmp_path / "actual_project"
        project_dir.mkdir()
        create_registry(
            project_dir,
            "# Registry\n\nmy-skill|feature|test|Test skill\n",
        )

        # cwd is a different directory with no registry
        cwd_dir = tmp_path / "wrong_dir"
        cwd_dir.mkdir()

        result = run_hook(
            plugin_root=str(plugin_dir),
            project_dir=str(project_dir),
            cwd=str(cwd_dir),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Should find the registry via CLAUDE_PROJECT_DIR, not cwd
        assert "1 knowledge skills" in output["systemMessage"]

    def test_falls_back_to_cwd_when_no_project_dir_env(self, tmp_path):
        """Without CLAUDE_PROJECT_DIR, falls back to cwd for registry lookup."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        # Put registry in cwd
        create_registry(
            tmp_path,
            "# Registry\n\ncwd-skill|feature|cwd|CWD skill\n",
        )

        result = run_hook(
            plugin_root=str(plugin_dir),
            project_dir="",  # Not set
            cwd=str(tmp_path),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "1 knowledge skills" in output["systemMessage"]

    def test_falls_back_to_old_registry_path(self, tmp_path):
        """Supports old spectre-find registry path for migration."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        # Use old path name
        create_registry(
            project_dir,
            "# Registry\n\nold-skill|feature|old|Old path skill\n",
            subdir="spectre-find",
        )

        result = run_hook(
            plugin_root=str(plugin_dir),
            project_dir=str(project_dir),
            cwd=str(tmp_path),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "1 knowledge skills" in output["systemMessage"]

    def test_output_contains_spectre_knowledge_tag(self, tmp_path):
        """Additional context is wrapped in <spectre-knowledge> tags."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        result = run_hook(plugin_root=str(plugin_dir), cwd=str(tmp_path))

        assert result.returncode == 0
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert context.startswith("<spectre-knowledge>")
        assert context.endswith("</spectre-knowledge>")

    def test_registry_content_embedded_in_context(self, tmp_path):
        """When registry exists, its content is embedded in the additional context."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        create_registry(
            tmp_path,
            "# Registry\n\nembedded-skill|feature|embed|Embedded skill\n",
        )

        result = run_hook(
            plugin_root=str(plugin_dir),
            project_dir="",
            cwd=str(tmp_path),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "embedded-skill|feature|embed|Embedded skill" in context


class TestCountRegistryEntries:
    """Unit tests for count_registry_entries."""

    def test_ignores_comments_and_blanks(self, tmp_path):
        """Comments and blank lines are not counted as entries."""
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()
        create_apply_skill(plugin_dir)

        create_registry(
            tmp_path,
            "# Comment line\n# Another comment\n\n"
            "real-skill|feature|test|Real skill\n"
            "\n# Trailing comment\n",
        )

        result = run_hook(
            plugin_root=str(plugin_dir),
            project_dir="",
            cwd=str(tmp_path),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "1 knowledge skills" in output["systemMessage"]
