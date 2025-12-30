---
description: 👻 | Save state snapshot to session_logs - primary agent
---

# handoff: Fast Session State Snapshot with Beads Integration

## Description
- **What** — Generate a Slack-style progress update, gather context, output structured JSON for session resume
- **Outcome** — `{timestamp}_handoff.json` in session_logs (JSON is source of truth)

## Performance Target
**2 tool calls total**: 1 Bash (gather context + beads) + 1 Write (JSON)

## Variables

### Dynamic Variables
- `user_input`: Task name override — (via ARGUMENTS: $ARGUMENTS)

### Static Variables
- `out_dir`: docs/active_tasks/{branch_name}

## ARGUMENTS Input

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## Step (1/2) - Gather Context + Beads Tasks (Single Bash Call)

### ⚠️ CRITICAL: Beads Lookup is MANDATORY

The beads task lookup is **essential for cross-session continuity**. You MUST:
1. Run filtered `bd list` commands to fetch only **actionable tasks** (open, in_progress, blocked)
2. Closed tasks are excluded to reduce token usage
3. If the result is empty `[]`, this means either:
   - No beads database exists (run `bd doctor` to check)
   - No tasks have been created with this workspace label yet
4. **DO NOT SKIP THIS** - the next session depends on knowing task status

- **Action** — GatherContext: Run ONE bash command to get everything:

```bash
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)
mkdir -p "docs/active_tasks/${branch}/session_logs"

# Fetch only actionable tasks (skip closed to reduce tokens)
open=$(bd list --label "$branch" --status open --json 2>/dev/null || echo '[]')
in_prog=$(bd list --label "$branch" --status in_progress --json 2>/dev/null || echo '[]')
blocked=$(bd list --label "$branch" --status blocked --json 2>/dev/null || echo '[]')
beads_tasks=$(echo "$open $in_prog $blocked" | jq -s 'add // []')
beads_count=$(echo "$beads_tasks" | jq 'length' 2>/dev/null || echo 0)

cat << EOF
{
  "branch": "$branch",
  "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)",
  "wip_count": $(git status --porcelain 2>/dev/null | wc -l | xargs),
  "ts": "$(date +%Y-%m-%d-%H%M%S)",
  "beads_count": $beads_count,
  "beads": $beads_tasks
}
EOF
```

- **Output**: JSON with `branch`, `commit`, `wip_count`, `ts`, `beads_count`, `beads` array
- **Beads scope**: Only actionable tasks (open, in_progress, blocked) — closed tasks excluded to reduce tokens
- **Side effect**: Creates `docs/active_tasks/{branch}/session_logs/` directory

### Verify Beads Output

After running the bash command, **CHECK THE OUTPUT**:
- If `beads_count` > 0 → Tasks found, proceed normally
- If `beads_count` = 0 → **PAUSE and investigate**:
  - Was `bd` command available? (check for errors)
  - Is there a beads database? (`bd doctor` would show)
  - Are tasks labeled with the correct branch name?
  - If genuinely no tasks exist, document this in the JSON

## Step (2/2) - Compose Progress Update & Write JSON

- **Action** — ComposeProgressUpdate: From agent's session memory, compose update using "WE" voice:
  - What we accomplished (2-5 bullets)
  - Key decisions we made (0-3 bullets)
  - Blockers we encountered (0-3 bullets)
  - What's next (2-4 bullets)
  - Confidence (high/medium/low) and risks

  **Example tone**: "We finished the auth refactor and got tests passing. Hit a snag with the OAuth callback - tomorrow we'll tackle session management."

- **Action** — BuildBeadsTree: From `beads` array in Step 1 output:
  - Find epic (task with `type: "epic"` or no parent and has children)
  - Build hierarchy: epic → tasks → subtasks
  - All tasks in output are actionable (closed tasks were filtered out)
  - Include task IDs for resume commands

- **Action** — WriteJSON: Save to `docs/active_tasks/{branch}/session_logs/{ts}_handoff.json`

**JSON Schema:**
```json
{
  "version": "1.0",
  "timestamp": "{ts}",
  "branch_name": "{branch}",
  "task_name": "{ARGUMENTS or branch}",

  "progress_update": {
    "summary": "Collaborative 'we' voice summary paragraph",
    "accomplished": ["item1", "item2"],
    "decisions": ["decision1"],
    "blockers": ["blocker1"],
    "next_steps": ["step1", "step2"],
    "confidence": "high|medium|low",
    "risks": ["risk1"]
  },

  "beads": {
    "workspace_label": "{branch}",
    "task_count": 5,
    "epic_id": "bd-xxxxx|none",
    "epic_title": "Epic title",
    "tasks": [
      {
        "id": "bd-xxxxx",
        "title": "Task title",
        "status": "open|in_progress|blocked",
        "type": "task|epic|bug|feature",
        "parent": "bd-xxxxx|null",
        "children": ["bd-xxxxx.1"],
        "labels": ["worktree", "type"],
        "completed": false
      }
    ]
  },

  "context": {
    "key_files": ["path1", "path2"],
    "wip_state": "uncommitted|clean",
    "last_commit": "abc1234"
  }
}
```

- **Action** — RespondToUser:
  ```
  ✓ Handoff saved: docs/active_tasks/{branch}/session_logs/{ts}_handoff.json
    Beads: {task_count} tasks tracked for workspace "{branch}"

  Start a new session or run /clear. Next session will auto-resume from this context.
  ```

## Success Criteria

**Performance**:
- [ ] **1 Bash call**: Context gathered + beads fetched + directory created
- [ ] **1 Write call**: JSON saved

**Beads Integration (MANDATORY)**:
- [ ] `bd list --status {open,in_progress,blocked}` executed for each status
- [ ] Beads count verified (logged in output)
- [ ] If count = 0, investigated why (no db? wrong label? genuinely empty?)
- [ ] Epic identified from task list (if exists)
- [ ] Hierarchical tree built (epic → tasks → subtasks)
- [ ] Only actionable statuses included (open/in_progress/blocked) — closed excluded
- [ ] `workspace_label` included in JSON for verification

**Progress Update Quality**:
- [ ] Summary written in collaborative "we" voice
- [ ] All sections populated (accomplished, decisions, blockers, next_steps)
- [ ] Confidence level assessed (high/medium/low)
- [ ] Risks identified and documented

**JSON Output**:
- [ ] Output directory created if missing
- [ ] JSON file saved with all required fields
- [ ] Schema matches specification
- [ ] Timestamp format consistent (`YYYY-MM-DD-HHMMSS`)

**Response**:
- [ ] User notified with exact file path
- [ ] Beads task count reported
- [ ] Next steps clear (session will auto-resume)
