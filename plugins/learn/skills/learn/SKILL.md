---
name: learn
description: Use when user invokes /learn or wants to save patterns, decisions, gotchas, procedures, or feature knowledge from a conversation.
---

# Learning Agent

You capture durable project knowledge into Skills that Claude Code loads on-demand.

## Path Convention

`{{project_root}}` refers to the root of the current project (typically the git repository root or cwd). Learnings are written to `{{project_root}}/.claude/skills/apply-learnings/`.

## Storage Structure

```
{{project_root}}/.claude/skills/apply-learnings/
├── SKILL.md              # Router skill (bootstrapped on first learning)
└── references/
    ├── registry.toon     # Index of all learnings
    ├── patterns/
    │   └── {slug}.md
    ├── gotchas/
    │   └── {slug}.md
    ├── feature/
    │   └── {slug}.md
    └── ...
```

## Registry

Before proposing a learning, check for existing learnings:

```
{{project_root}}/.claude/skills/apply-learnings/references/registry.toon
```

Format: `{category}/{slug}|{category}|{triggers}|{description}` (one learning per line)

## Workflow

### 1. Parse Input

**With arguments**: Use the explicit content as the knowledge to capture.
**Without arguments**: Analyze recent conversation (last 10-20 messages) to identify what's worth preserving.

### 2. Apply Capture Criteria

Must meet **at least 2 of 4**:

| Criterion  | Question                         |
| ---------- | -------------------------------- |
| Frequency  | Will this come up again?         |
| Pain       | Did it cost real debugging time? |
| Surprise   | Was it non-obvious?              |
| Durability | Still true in 6 months?          |

**Capture**: Patterns, decisions with rationale, debugging insights, conventions, tribal knowledge.
**Skip**: One-off solutions, generic knowledge, temporary workarounds, simple preferences (-> CLAUDE.md).

### 3. Categorize

| Category        | What                                                    | Path                    |
| --------------- | ------------------------------------------------------- | ----------------------- |
| patterns        | Repeatable solutions                                    | `patterns/{slug}.md`    |
| decisions       | Architectural choices + why                             | `decisions/{slug}.md`   |
| gotchas         | Hard-won debugging knowledge                            | `gotchas/{slug}.md`     |
| procedures      | Multi-step processes                                    | `procedures/{slug}.md`  |
| domain          | Project-specific concepts                               | `domain/{slug}.md`      |
| feature         | Feature implementations: design, flows, key files, tasks | `feature/{slug}.md`    |
| strategy        | Roadmap decisions, prioritization rationale, feature bets | `strategy/{slug}.md`  |
| ux              | Design patterns, user research insights, interactions   | `ux/{slug}.md`          |
| integration     | Third-party APIs, vendor quirks, external systems       | `integration/{slug}.md` |
| performance     | Optimization learnings, benchmarks, scaling decisions   | `performance/{slug}.md` |
| testing         | Test strategies, coverage decisions, QA patterns        | `testing/{slug}.md`     |

**Feature category structure**: Feature learnings are higher-level "dossiers" that help the LLM understand how a feature works end-to-end. Use this structure:

```markdown
### {Feature Name}

**Trigger**: {feature name}, {related keywords}
**Confidence**: {level}
**Created**: {YYYY-MM-DD}
**Updated**: {YYYY-MM-DD}
**Version**: 1

**Overview**: {1-2 sentences on what this feature does for users}

**User Flows**:
- {Primary flow}
- {Secondary flows}

**Technical Design**:
- {Architecture summary}
- {Key patterns used}

**Key Files**:
- `path/to/main.ts` - {purpose}
- `path/to/component.tsx` - {purpose}

**Common Tasks**:
- {Task}: {how to approach it}
```

Use `feature` when capturing *how something works* holistically. Use other categories for specific insights (a gotcha within a feature, a pattern used by a feature, etc.).

**Category doesn't fit?** Propose a new one. If the learning clearly doesn't belong in existing categories, suggest a new category with rationale:

```
This doesn't fit existing categories well. I'd propose a new category:

**{new-category}**: {what it captures}

This would cover: {examples of what else might go here}

Create this category? [Y/n]
```

New categories should be general enough to hold multiple learnings, not one-offs.

**Writing Effective Metadata**

**Name field** (slug):
- Letters, numbers, hyphens only (no parentheses or special chars)
- Action-oriented gerunds aid discovery: `creating-skills` not `skill-creation`
- Name by what you DO: `condition-based-waiting` not `async-helpers`

**Description field** (frontmatter):
- Start with "Use when..." — focus on triggering conditions
- Describe WHEN to use, NOT what the skill does (Claude may shortcut to description and skip content)
- Third person, max 500 characters
- Example: `Use when tests have race conditions or pass/fail inconsistently`

**Trigger keywords** (per learning):
- Error messages: `"ENOTEMPTY"`, `"Hook timed out"`
- Symptoms: `flaky`, `hanging`, `race condition`, `zombie`
- Synonyms: `timeout/hang/freeze`, `cleanup/teardown/afterEach`
- Tools: command names, library names, file types

### 4. Match, Update, or Create

Read registry to find candidates, then **read the actual learning file** to compare content.

**Registry scan** - look for:
- Same category
- Overlapping trigger keywords
- Related topic

**If candidate found**, read `references/{category}/{slug}.md` and check:

1. **UPDATE** - New knowledge contradicts, extends, or supersedes an existing learning
   - Same topic but new/better information
   - Original learning was incomplete or wrong
   - Circumstances changed (dependency updated, API changed, etc.)

2. **APPEND** - New learning belongs in same skill but is distinct
   - Related topic, different specific insight
   - Same category, different trigger keywords

3. **CREATE** - No semantic match in registry
   - New topic area
   - Different category

**Decision priority**: UPDATE > APPEND > CREATE (prefer consolidation over proliferation)

### 5. Propose

Stop and wait for user response. Format depends on action type:

**For UPDATE** (revising existing learning):
```
I'd update `{category}/{slug}.md`:

**Current**: {1-2 sentence summary of existing}
**Proposed**: {1-2 sentence summary of revision}
**Reason**: {contradicts|extends|supersedes} - {why}

{Updated content preview}

Update this? [Y/n/edit]
```

**For APPEND** (new learning to existing file):
```
I'd add to `{category}/{slug}.md`:

**{Title}**

{1-3 sentence summary}

{Code example if relevant}

Trigger: {keywords}
Confidence: {low|medium|high}

Save this? [Y/n/edit]
```

**For CREATE** (new learning file):
```
I'd create `{category}/{slug}.md`:

**{Title}**

{1-3 sentence summary}

{Code example if relevant}

Trigger: {keywords}
Confidence: {low|medium|high}

Create this? [Y/n/edit]
```

**Confidence**:
- low = observed once
- medium = repeated or taught
- high = battle-tested

### 6. Handle Response

- `y`/`yes` -> write as proposed
- `n`/`no` -> cancel
- `edit` or custom text -> modify first
- Different skill name -> use that instead

### 7. Write Learning

**Location**: `{{project_root}}/.claude/skills/apply-learnings/references/{category}/{slug}.md`

**CREATE** - New learning file:

```markdown
# {Title}

**Trigger**: {keywords}
**Confidence**: {level}
**Created**: {YYYY-MM-DD}
**Updated**: {YYYY-MM-DD}
**Version**: 1

{Explanation}

{Code if relevant}
```

**UPDATE** - Revise existing learning file:

1. Preserve `**Created**` date
2. Set `**Updated**` to today
3. Increment `**Version**` by 1
4. Update confidence if warranted (e.g., low → medium after verification)

**APPEND** - For files with multiple learnings, add new section:

```markdown
---

## {New Learning Title}

**Trigger**: {keywords}
**Confidence**: {level}
**Created**: {YYYY-MM-DD}
**Updated**: {YYYY-MM-DD}
**Version**: 1

{Explanation}
```

### 8. Update Registry

Add/update entry in `{{project_root}}/.claude/skills/apply-learnings/references/registry.toon`:

```
{category}/{slug}|{category}|{trigger,keywords}|{short description}
```

### 9. Confirm

```
Saved .claude/skills/apply-learnings/references/{category}/{slug}.md
```
