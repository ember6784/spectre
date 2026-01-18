---
description: 👻 | Complete cleanup flow - clean, inspect, lint, test - primary agent
---

# clean: Dead Code Cleanup

## Description
- **What** — Fast pattern-based dead code detection + ESLint bypass analysis with refactor planning
- **Outcome** — Clean code, lint clean, tests pass, conventional commits, tech debt roadmap

## ARGUMENTS Input

Optional scope: empty = uncommitted, commit SHA = from that commit, "only {sha}" = single commit.

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## Execution Style
**Default**: Fast checklist — no subagents, no approval gates for obvious dead code.
**Escalate**: Dispatch @analyst only when NEEDS_REVIEW count > 3.

## Step 1 - Scope & Fast Scan

**DetermineScope**:
- Empty → `git diff --cached --name-only` + `git diff --name-only` + untracked
- Commit SHA → changes from {sha}^..HEAD + uncommitted
- "only {sha}" → just that commit's changes

**PatternScan** — Check each file for:
- [ ] Orphaned imports — no usage in file
- [ ] Unused functions/variables — declared, never called
- [ ] Commented-out code — blocks >5 lines
- [ ] Debug artifacts — debugger, TODO/FIXME
- [ ] Temp logging — console.log, "DEBUG:", "TEMP:"
- [ ] Dead branches — unreachable, always-false
- [ ] Orphaned exports — not imported anywhere
- [ ] Test artifacts — .only, skipped tests
- [ ] AI slop — excessive comments, unnecessary checks, `any` casts
- [ ] ESLint bypasses — `eslint-disable`, `eslint-disable-next-line`, `@ts-ignore`, `@ts-expect-error`

**Categorize immediately**:
- **SAFE_TO_REMOVE**: No refs, no dynamic usage hints, obviously dead
- **NEEDS_REVIEW**: Possible dynamic refs, reflection, string interpolation

**DetectDuplication**: Flag copy-paste (>5 similar lines, 2+ instances).

## Step 2 - Conditional Validation

**If** NEEDS_REVIEW ≤ 3 → Skip subagents, go to Step 3
**Else** → Dispatch @analyst for NEEDS_REVIEW items only:
```
Validate uncertain findings: {needs_review_list}
For each: check dynamic refs, reflection, indirect calls.
Return: SAFE_TO_REMOVE or KEEP with evidence.
```

## Step 3 - ESLint Compliance Planning

**Purpose**: Systematically eliminate tech debt from eslint-disable comments.

**3a. Collect ESLint Bypasses**:
```bash
grep -rn "eslint-disable\|@ts-ignore\|@ts-expect-error" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"
```

**3b. Group by Module**: Cluster findings by directory or logical module (files that import each other).

**3c. For each group with ≥2 bypasses**, dispatch @analyst in parallel:
```
Analyze ESLint bypasses in: {file_list}

For each bypass:
1. Identify the disabled rule(s)
2. Understand WHY it was disabled (type issue? legacy code? third-party types?)
3. Determine the proper fix (type narrowing, interface update, refactor, etc.)

Output a refactor plan:
- File: path
- Line: number
- Rule: disabled-rule-name
- Reason: why it exists
- Fix: specific refactor steps
- Effort: trivial / moderate / significant
- Risk: low / medium / high
```

**3d. Present Refactor Summary**:
- Group by effort level (trivial fixes first)
- Flag high-risk items for user decision
- Create actionable items for future cleanup sprints

**Note**: This step is diagnostic. Actual refactoring happens in follow-up tasks, not during clean.

## Step 4 - Execute

**Remove SAFE items** — No approval needed for obvious dead code.
**Present NEEDS_REVIEW** — User decides (remove/keep).
**Rollback** if tests fail after removal.

## Step 5 - Verify & Commit

- Run lint, fix violations
- Run tests, fix failures or rollback
- Commit by type (chore/refactor/fix/test), conventional format
- Render Next Steps via `@skill-spectre:spectre`
