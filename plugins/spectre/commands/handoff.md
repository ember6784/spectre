---
description: 👻 | Save state snapshot to session_logs - primary agent
---

# handoff: Fast Session State Snapshot

Generate progress update, gather context, output structured JSON for session resume. Output: `{timestamp}_handoff.json` in session_logs.

**Performance Target**: 2 tool calls (1 Bash + 1 Write)

## ARGUMENTS

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## Step 1: Gather Context (Single Bash Call)

- **Action** — GatherContext: Run ONE bash command:

```bash
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)
mkdir -p "docs/active_tasks/${branch}/session_logs"

beads_available=false
beads_tasks='[]'
beads_count=0

if command -v bd &>/dev/null && bd doctor &>/dev/null; then
  beads_available=true
  open=$(bd list --label "$branch" --status open --json 2>/dev/null || echo '[]')
  in_prog=$(bd list --label "$branch" --status in_progress --json 2>/dev/null || echo '[]')
  blocked=$(bd list --label "$branch" --status blocked --json 2>/dev/null || echo '[]')
  beads_tasks=$(echo "$open $in_prog $blocked" | jq -s 'add // []')
  beads_count=$(echo "$beads_tasks" | jq 'length' 2>/dev/null || echo 0)
fi

cat << EOF
{
  "branch": "$branch",
  "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)",
  "wip_count": $(git status --porcelain 2>/dev/null | wc -l | xargs),
  "ts": "$(date +%Y-%m-%d-%H%M%S)",
  "beads_available": $beads_available,
  "beads_count": $beads_count,
  "beads": $beads_tasks
}
EOF
```

**Output**: JSON with branch, commit, wip_count, ts, beads_available, beads_count, beads[]

**Task sources**: TodoWrite (captured by hook automatically), Beads (fetched if `bd` available)

## Step 2: Compose & Write JSON

- **Action** — ComposeProgressUpdate: From session memory, compose using "WE" voice:

  | Field | Required | Description |
  |-------|----------|-------------|
  | summary | ✓ | Slack-style paragraph a human would read |
  | goal | ✓ | What we're building + success criteria |
  | accomplished | ✓ | What we completed (2-5 bullets) |
  | now | ✓ | **What you were actively working on when session ended** (critical!) |
  | next_steps | ✓ | Upcoming work (2-4 bullets) |
  | confidence | ✓ | high / medium / low |
  | constraints | | Known constraints or assumptions |
  | decisions | | Key decisions made (0-3 bullets) |
  | blockers | | Things blocking progress |
  | open_questions | | Questions needing answers |
  | risks | | Identified risks |

  **Tone**: "We finished the auth refactor and got tests passing. Hit a snag with OAuth callback - next we'll tackle session management."

- **Action** — BuildWorkingSet: Capture active context:
  - `key_files`: Files actively edited
  - `active_ids`: Beads task IDs in progress
  - `recent_commands`: Recent terminal commands (test, build, etc.)

- **Action** — BuildBeadsTree (if available): From beads array, build hierarchy (epic → tasks → subtasks). Include task IDs for resume.

- **Action** — WriteJSON: Save to `docs/active_tasks/{branch}/session_logs/{ts}_handoff.json`

**JSON Schema**:
```json
{
  "version": "1.1",
  "timestamp": "{ts}",
  "branch_name": "{branch}",
  "task_name": "{ARGUMENTS or branch}",
  "progress_update": {
    "summary": "string",
    "goal": "string",
    "accomplished": ["string"],
    "now": "string (critical for resume)",
    "next_steps": ["string"],
    "confidence": "high|medium|low",
    "constraints": ["string"],
    "decisions": ["string"],
    "blockers": ["string"],
    "open_questions": ["string"],
    "risks": ["string"]
  },
  "working_set": {
    "key_files": ["path"],
    "active_ids": ["bd-xxxxx"],
    "recent_commands": ["command"]
  },
  "beads": {
    "available": "boolean",
    "workspace_label": "{branch}",
    "task_count": "number",
    "epic_id": "bd-xxxxx|null",
    "epic_title": "string|null",
    "tasks": [{"id", "title", "status", "type", "parent", "children", "labels"}]
  },
  "context": {
    "wip_state": "uncommitted|clean",
    "last_commit": "abc1234"
  }
}
```

If beads unavailable: `available: false`, `tasks: []`

- **Action** — RespondToUser: "✓ Handoff saved: {path}. [If beads: {count} tasks for '{branch}']. Next session auto-resumes from this context."
