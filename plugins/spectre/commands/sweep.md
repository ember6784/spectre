---
description: 👻 | Light pass cleanup post feature dev - clean, lint, test - primary agent
---

## Pre-Commit Cleanup

You are preparing recently committed or uncommitted changes for check-in. Perform a systematic cleanup.

**Execution Style**: This is a fast, formulaic checklist. No subagents, no user approval gates. Just execute each step and move on.

### 1. Diff Sanity Check

- Review full diff for unintentional changes (whitespace-only edits, merge artifacts)
- Verify no accidentally staged files outside the intended scope
- Confirm no secrets, API keys, credentials, or sensitive data in diff

### 2. Logging Audit

- Remove temporary/debug logging (console.log, print, debug flags, etc.)
- Preserve intentional logs: errors, critical warnings, key state transitions
- Verify log levels are appropriate for production context

### 3. Code Hygiene

- Remove commented-out code (it's in git history if needed)
- Resolve or document any TODO/FIXME/HACK introduced in this session
- Remove hardcoded test values that should be config/env

### 4. Dead Code Scan (Pattern Checklist)

Scan changed files for these patterns — remove if found, no deep investigation:

- [ ] **Orphaned imports** — imports with no usage in the file
- [ ] **Unused functions/variables** — declared but never called/referenced
- [ ] **Commented-out code blocks** — large blocks (>5 lines)
- [ ] **Debug artifacts** — debugger statements, leftover TODO/FIXME from this work
- [ ] **Temporary logging** — console.log without context, "DEBUG:", "TEMP:", checkpoint logs
- [ ] **Dead branches** — unreachable code, always-false conditions
- [ ] **Orphaned exports** — exports not imported anywhere
- [ ] **Test artifacts** — `.only`, skipped tests, leftover test data
- [ ] **AI slop** — excessive comments, unnecessary defensive checks, `any` casts

For duplication: flag obvious copy-paste (>5 similar lines, 2+ instances) but don't deep-dive.

### 5. Lint

- Run linter and fix any violations
- Verify .gitignore coverage (no temp files, build artifacts, IDE configs)

### 6. Test Coverage (Risk-Aware)

**CRITICAL**: This step is about CREATING NEW TESTS for changed code, not just running existing tests.

**Quick risk triage** — prioritize test effort by file type:

| Tier | Files | Coverage |
|------|-------|----------|
| **P0 Critical** | auth, payment, security, crypto, session, token, PII | Thorough: all behaviors + error paths |
| **P1 Core** | API handlers, feature components, services, state | Key paths: happy path + critical errors |
| **P2 Supporting** | Utils, helpers, hooks, formatters | Light: public function smoke test |
| **P3 Skip** | Types (.d.ts), configs, styles, index barrels, simple wrappers | No tests needed |

**Execute** (in order):
1. **Identify new/changed behaviors** — What NEW functionality was added or modified? List specific behaviors.
2. **Check for existing coverage** — Do tests already exist for these behaviors? If not, they need tests.
3. **Write NEW tests** for uncovered behaviors:
   - P0 files: write tests for all behaviors + error paths
   - P1 files: write tests for happy path + 1-2 error cases
   - P2 files: write tests for public surface only
   - P3 files: explicitly skip — no tests
4. **Update existing tests** if behavior intentionally changed
5. **Run full test suite** and confirm all pass

**Anti-pattern**: Do NOT just run existing tests and call it done. If you changed code, you likely need new tests.

### 7. Commit Strategy

Group changes into logical commits by:
- Feature/behavior additions (feat)
- Refactors/cleanup — no behavior change (refactor)
- Bug fixes (fix)
- Test additions/updates (test)
- Config/dependency changes (chore)
- Documentation (docs)

### 8. Conventional Commits

- Write commits following: `type(scope): description`
- Types: feat, fix, refactor, test, chore, docs, style, perf
- Each commit message should answer: What does this change and why?