---
name: apply-learnings
description: Use when starting implementation, debugging, or feature work on a project with captured learnings.
---

# Apply Learnings

Project-specific knowledge captured via `/learn`. Check before starting work.

## Registry Location

```
{{project_root}}/.claude/skills/apply-learnings/references/registry.toon
```

Format: `{category}/{slug}|{category}|{triggers}|{description}`

## Workflow

1. **Read registry** - scan for trigger matches against current task
2. **Load matches** - read `{{project_root}}/.claude/skills/apply-learnings/references/{category}/{slug}.md`
3. **Apply knowledge**:
   - **patterns**: Follow established approach
   - **gotchas**: Avoid known pitfalls
   - **decisions**: Respect architectural choices
   - **feature**: Understand design, flows, key files
   - **procedures**: Follow multi-step processes
4. **Proceed** - if no matches, continue normally
