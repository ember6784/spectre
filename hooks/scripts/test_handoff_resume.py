#!/usr/bin/env python3
"""
Tests for handoff-resume.py

Run with: python3 -m pytest test_handoff_resume.py -v
"""

import json
import os
import tempfile
import subprocess
import sys
from pathlib import Path

import pytest


# Path to the script under test
SCRIPT_PATH = Path(__file__).parent / "handoff-resume.py"


class TestHandoffResume:
    """Test the consolidated handoff-resume hook script."""

    def test_no_session_dir_exits_silently(self, tmp_path, monkeypatch):
        """When session_logs directory doesn't exist, exit silently with no output."""
        monkeypatch.chdir(tmp_path)
        # No docs/active_tasks/{branch}/session_logs exists

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_no_handoff_files_exits_silently(self, tmp_path, monkeypatch):
        """When session_logs exists but has no handoff files, exit silently."""
        monkeypatch.chdir(tmp_path)

        # Create empty session_logs directory
        session_dir = tmp_path / "docs" / "active_tasks" / "main" / "session_logs"
        session_dir.mkdir(parents=True)

        # Mock git to return 'main' branch
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_finds_latest_handoff_by_timestamp(self, tmp_path, monkeypatch):
        """Should find the most recently modified handoff file."""
        monkeypatch.chdir(tmp_path)

        # Setup git
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

        # Create session_logs with multiple handoff files
        session_dir = tmp_path / "docs" / "active_tasks" / "main" / "session_logs"
        session_dir.mkdir(parents=True)

        # Create older handoff
        old_handoff = {
            "version": "1.0",
            "timestamp": "2024-01-01-120000",
            "branch_name": "main",
            "task_name": "old-task",
            "progress_update": {
                "summary": "Old summary",
                "accomplished": ["old thing"],
                "next_steps": ["old step"],
                "decisions": [],
                "blockers": [],
                "confidence": "low",
                "risks": []
            },
            "beads": {"tasks": []},
            "context": {"last_commit": "abc123", "wip_state": "clean"}
        }
        old_file = session_dir / "2024-01-01-120000_handoff.json"
        old_file.write_text(json.dumps(old_handoff))

        # Create newer handoff (touch to ensure it's newer)
        import time
        time.sleep(0.1)

        new_handoff = {
            "version": "1.0",
            "timestamp": "2024-01-02-120000",
            "branch_name": "main",
            "task_name": "new-task",
            "progress_update": {
                "summary": "New summary",
                "accomplished": ["new thing"],
                "next_steps": ["new step"],
                "decisions": [],
                "blockers": [],
                "confidence": "high",
                "risks": []
            },
            "beads": {"tasks": []},
            "context": {"last_commit": "def456", "wip_state": "uncommitted"}
        }
        new_file = session_dir / "2024-01-02-120000_handoff.json"
        new_file.write_text(json.dumps(new_handoff))

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Should reference the newer task
        assert "new-task" in output["systemMessage"]
        assert "new-task" in output["hookSpecificOutput"]["additionalContext"]

    def test_outputs_valid_hook_json_structure(self, tmp_path, monkeypatch):
        """Output must match Claude Code hook JSON schema."""
        monkeypatch.chdir(tmp_path)

        # Setup git
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/feature-branch")

        # Create session_logs with handoff
        session_dir = tmp_path / "docs" / "active_tasks" / "feature-branch" / "session_logs"
        session_dir.mkdir(parents=True)

        handoff = {
            "version": "1.0",
            "timestamp": "2024-01-01-120000",
            "branch_name": "feature-branch",
            "task_name": "Test Task",
            "progress_update": {
                "summary": "We did stuff",
                "accomplished": ["thing 1", "thing 2"],
                "next_steps": ["next 1"],
                "decisions": ["decided X"],
                "blockers": [],
                "confidence": "high",
                "risks": ["risk 1"]
            },
            "beads": {
                "workspace_label": "feature-branch",
                "task_count": 0,
                "epic_id": "none",
                "epic_title": "No Epic",
                "tasks": []
            },
            "context": {
                "last_commit": "abc123",
                "wip_state": "clean",
                "key_files": ["file1.py"]
            }
        }
        handoff_file = session_dir / "2024-01-01-120000_handoff.json"
        handoff_file.write_text(json.dumps(handoff))

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Verify required hook structure
        assert "systemMessage" in output
        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert "additionalContext" in output["hookSpecificOutput"]

    def test_system_message_contains_task_and_branch(self, tmp_path, monkeypatch):
        """systemMessage should have task name and branch for user visibility."""
        monkeypatch.chdir(tmp_path)

        # Setup git
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/my-feature")

        session_dir = tmp_path / "docs" / "active_tasks" / "my-feature" / "session_logs"
        session_dir.mkdir(parents=True)

        handoff = {
            "version": "1.0",
            "timestamp": "2024-01-01-120000",
            "branch_name": "my-feature",
            "task_name": "Implement Widget",
            "progress_update": {
                "summary": "Working on widget",
                "accomplished": [],
                "next_steps": [],
                "decisions": [],
                "blockers": [],
                "confidence": "medium",
                "risks": []
            },
            "beads": {"tasks": []},
            "context": {}
        }
        (session_dir / "2024-01-01-120000_handoff.json").write_text(json.dumps(handoff))

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        output = json.loads(result.stdout)

        assert "Implement Widget" in output["systemMessage"]
        assert "my-feature" in output["systemMessage"]

    def test_additional_context_contains_session_context_tag(self, tmp_path, monkeypatch):
        """additionalContext should wrap content in <session-context> tags."""
        monkeypatch.chdir(tmp_path)

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

        session_dir = tmp_path / "docs" / "active_tasks" / "main" / "session_logs"
        session_dir.mkdir(parents=True)

        handoff = {
            "version": "1.0",
            "timestamp": "2024-01-01-120000",
            "branch_name": "main",
            "task_name": "Test",
            "progress_update": {
                "summary": "Summary here",
                "accomplished": ["done"],
                "next_steps": ["todo"],
                "decisions": [],
                "blockers": [],
                "confidence": "high",
                "risks": []
            },
            "beads": {"tasks": []},
            "context": {}
        }
        (session_dir / "2024-01-01-120000_handoff.json").write_text(json.dumps(handoff))

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        output = json.loads(result.stdout)
        ctx = output["hookSpecificOutput"]["additionalContext"]

        assert ctx.startswith("<session-context>")
        assert ctx.endswith("</session-context>")

    def test_includes_progress_update_sections(self, tmp_path, monkeypatch):
        """additionalContext should include all progress update sections."""
        monkeypatch.chdir(tmp_path)

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

        session_dir = tmp_path / "docs" / "active_tasks" / "main" / "session_logs"
        session_dir.mkdir(parents=True)

        handoff = {
            "version": "1.0",
            "timestamp": "2024-01-01-120000",
            "branch_name": "main",
            "task_name": "Test",
            "progress_update": {
                "summary": "We made good progress today",
                "accomplished": ["Finished auth", "Added tests"],
                "next_steps": ["Deploy to staging", "Review PR"],
                "decisions": ["Use JWT tokens"],
                "blockers": ["Waiting on API keys"],
                "confidence": "medium",
                "risks": ["Timeline tight"]
            },
            "beads": {"tasks": []},
            "context": {"last_commit": "abc123", "wip_state": "uncommitted"}
        }
        (session_dir / "2024-01-01-120000_handoff.json").write_text(json.dumps(handoff))

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        output = json.loads(result.stdout)
        ctx = output["hookSpecificOutput"]["additionalContext"]

        # Check all sections present
        assert "We made good progress today" in ctx
        assert "Finished auth" in ctx
        assert "Added tests" in ctx
        assert "Deploy to staging" in ctx
        assert "Use JWT tokens" in ctx
        assert "Waiting on API keys" in ctx
        assert "medium" in ctx.lower() or "Confidence" in ctx
        assert "Timeline tight" in ctx

    def test_handles_malformed_json_gracefully(self, tmp_path, monkeypatch):
        """Should exit silently if handoff JSON is malformed."""
        monkeypatch.chdir(tmp_path)

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

        session_dir = tmp_path / "docs" / "active_tasks" / "main" / "session_logs"
        session_dir.mkdir(parents=True)

        # Write malformed JSON
        (session_dir / "2024-01-01-120000_handoff.json").write_text("{ invalid json }")

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_ignores_archived_sessions(self, tmp_path, monkeypatch):
        """Should not load sessions from archive subdirectory."""
        monkeypatch.chdir(tmp_path)

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")

        session_dir = tmp_path / "docs" / "active_tasks" / "main" / "session_logs"
        archive_dir = session_dir / "archive"
        session_dir.mkdir(parents=True)
        archive_dir.mkdir()

        # Put handoff in archive only
        handoff = {
            "version": "1.0",
            "timestamp": "2024-01-01-120000",
            "branch_name": "main",
            "task_name": "Archived Task",
            "progress_update": {"summary": "Old", "accomplished": [], "next_steps": [], "decisions": [], "blockers": [], "confidence": "low", "risks": []},
            "beads": {"tasks": []},
            "context": {}
        }
        (archive_dir / "2024-01-01-120000_handoff.json").write_text(json.dumps(handoff))

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )

        # Should exit silently - no active sessions
        assert result.returncode == 0
        assert result.stdout.strip() == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
