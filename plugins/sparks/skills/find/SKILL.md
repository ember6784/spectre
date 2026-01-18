---
name: find
description: Use when user wants to search for existing knowledge, find a specific learning, or discover what knowledge is available.
---

# Find Knowledge

Search and load relevant knowledge from the project's sparks into your context.

## How Sparks Works

This project uses **sparks** to capture durable knowledge across sessions:

- **Registry**: A list of knowledge entries stored inline in the apply skill
- **References**: Markdown files containing the actual knowledge (patterns, gotchas, features, etc.)
- **Triggers**: Keywords that indicate when knowledge is relevant

The registry lives at `{{project_root}}/.claude/skills/apply/SKILL.md` under the `## Registry` section. Each entry points to a reference file in `references/{category}/{slug}.md`.

**Registry format**: `{path}|{category}|{triggers}|{description}`

**Categories**: feature, gotchas, patterns, decisions, procedures, integration, performance, testing, ux, strategy

## Path Convention

`{{project_root}}` refers to the root of the current project (typically the git repository root or cwd). Knowledge is stored in `{{project_root}}/.claude/skills/apply/`.

## Workflow

### 1. Read the Apply Skill

```
{{project_root}}/.claude/skills/apply/SKILL.md
```

Parse the `## Registry` section to get all knowledge entries.

### 2. Search for Matches

Match the user's query against:
- **Triggers**: Keywords that indicate when knowledge is relevant
- **Description**: Short summary of what the knowledge covers
- **Category**: Type of knowledge (feature, gotchas, patterns, etc.)
- **Path**: File path (slug may be descriptive)

### 3. Handle Results

**Single match → Load automatically:**

Read the file immediately:
```
{{project_root}}/.claude/skills/apply/{path}
```

The knowledge is now in your context. Use it to assist with the current task.

**Multiple matches → Ask user which to load:**

```
Found {N} relevant entries:

1. **{category}/{slug}** - {description}
2. **{category}/{slug}** - {description}

Which would you like to load? [1/2/all]
```

Then read the selected file(s).

**No matches:**

```
No entries match "{query}".

Available categories:
- feature ({count} entries)
- gotchas ({count} entries)
...

Would you like to search with different keywords, or create new knowledge via /learn?
```

**No query provided (`/find` alone):**

Show summary of all available knowledge by category with counts.

### 4. Apply the Knowledge

After loading knowledge:

- **If there's an active task in the conversation**: Use the knowledge as context to help complete it. The knowledge tells you WHERE to look, WHAT patterns to follow, and WHAT pitfalls to avoid.

- **If this is the start of a thread (no task yet)**: Ask the user what they'd like to do with this knowledge. Example: "I've loaded the authentication feature knowledge. What would you like to know or do?"

## Examples

**User**: `/find hooks` (mid-task)
**Action**: Search, find 1 match, load it, use to help with current work

**User**: `/find sparks` (start of thread)
**Action**: Search, load match, then ask "I've loaded the sparks plugin knowledge. What would you like to know or do?"

**User**: `/find`
**Action**: Show category summary with counts
