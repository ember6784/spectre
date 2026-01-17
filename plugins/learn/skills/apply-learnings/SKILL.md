---
name: apply-learnings
description: Use when starting implementation, debugging, or feature work on a project with captured learnings.
---

# Apply Learnings

Project-specific knowledge captured via `/learn`. The registry is injected into your context at session start.

<CRITICAL>
If ANY learning's triggers or description match your current task, you MUST Read the file.

DO NOT search the codebase. DO NOT dispatch agents. The registry tells you EXACTLY where the knowledge is.

This is not optional. If it matches, Read it.
</CRITICAL>

## Registry Format

```
{path}|{category}|{triggers}|{description}
```

## Workflow

1. **Scan registry** (already in your context) - match triggers AND description against current task
2. **For each match**, use the Read tool to load:
   ```
   {{project_root}}/.claude/skills/apply-learnings/{path}
   ```
3. **Apply the knowledge** before proceeding with the task
4. **No matches?** Proceed normally

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "Let me search the codebase first" | The registry tells you where knowledge is. Read it. |
| "I'll dispatch an agent to find this" | No. The path is in the registry. Read the file. |
| "I need more context first" | The learning IS the context. Read it first. |
| "This seems like a simple question" | If it matches a learning, read the learning. |

## Example

User asks: "How does /learn work?"

Registry has: `references/feature/learn-plugin.md|feature|learn plugin, /learn|...`

Action: `Read .claude/skills/apply-learnings/references/feature/learn-plugin.md`

NOT: Search for files. NOT: Dispatch agent. Just Read the path from the registry.
