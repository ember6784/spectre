---
description: 👻 | Execute tasks via strict TDD methodology - primary agent
---

# tdd: Test-Driven Development Execution

## Description
- **What** — Execute tasks using strict TDD (RED → GREEN → REFACTOR) with critical-path tests only
- **Outcome** — Tasks completed with Happy/Failure tests passing, minimal code shipped

## ARGUMENTS Input

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## Instructions

- **2 tests per Test Opportunity (TO)**: 1 Happy path, 1 Failure path — then stop
- **Scoped execution only**: Never run repo-wide tests; use `--testPathPattern`, `--findRelatedTests`, or per-file lint
- **YAGNI**: No abstractions unless test forces it or ≥2 call sites exist
- **Test Opportunity (TO)**: Smallest behavior unit — new/modified function, route, reducer, bug fix, or acceptance criterion
- **Anti-flake**: Use fake timers, stubs, seeded RNG

## Step 1 - Generate TDD TODO List

- **Action** — ParseTaskList: Extract tasks from ARGUMENTS or thread context
  - **If** no clear tasks → stop and ask for guidance
- **Action** — IdentifyTestOpportunities: Derive TOs from tasks, sub-tasks, acceptance criteria
- **Action** — TransformToTDD: Convert each TO to RED-GREEN-REFACTOR cycle using TodoWrite:
  - `RED: Happy — {happy path test}`
  - `RED: Failure — {failure mode test}`
  - `GREEN: Implement minimal logic`
  - `REFACTOR: Tidy without adding behavior`
  - `COMMIT: {conventional commit}`
- **Action** — VerifyScope: Confirm TODO contains ONLY assigned tasks; remove out-of-scope items

## Step 2 - RED Phase: Write Failing Tests

- **Action** — WriteHappyTest: Write first failing test (happy path)
  - Execute only this test/file, not entire suite
  - **If** passes unexpectedly → fix test to validate actual behavior
  - Mark RED: Happy complete
- **Action** — WriteFailureTest: Write second failing test (primary failure mode)
  - Proves system fails safely
  - Run targeted scope only
  - Mark RED: Failure complete
- **Action** — VerifyAllRed: Confirm tests fail for correct reasons before proceeding

## Step 3 - GREEN Phase: Minimal Implementation

- **Action** — ImplementMinimal: Write least code to pass tests
  - No extra branches, params, or dependencies unless test forces them
  - Follow existing project patterns
- **Action** — RunTests: Execute tests (narrowest scope)
  - **If** fail → debug and fix
  - Mark GREEN complete
- **Action** — VerifyMinimal: Remove any speculative code not forced by tests

## Step 4 - REFACTOR Phase: Clean Code

- **Action** — EvaluateRefactoring: Refactor only if duplication ≥3 OR readability materially improves
- **Action** — RefactorSafely: Improve code while keeping tests green
  - Run tests continuously
  - **If** tests fail → revert or fix
  - Mark REFACTOR complete
- **Action** — HandleLintFailures: If complexity/length rules fail, apply in order until clear:
  1. Add guard clauses, split compound expressions
  2. Extract tiny private helpers (same file)
  3. Hoist literals/config to file constants
  4. Split into orchestrator + helpers
  5. Only if still failing: create same-directory helper module

## Step 5 - Loop or Complete

- **Action** — CheckRemainingTasks:
  - **If** more TOs in TODO → return to Step 2
  - **Else** → proceed to Step 6

## Step 6 - Commit & Report

- **Action** — CommitCode: Commit with conventional format (`feat({task}): description`)
- **Action** — GenerateReport: Create completion summary:
  - **Execution Summary**: Tasks completed, test status (✅ Happy ✅ Failure), files modified with file:line refs
  - **Reusable Artifacts**: Test helpers, mocks, fixtures created
  - **Public API Surface**: New/modified exports with signatures
  - **Established Patterns**: Code/testing patterns to follow
  - **Deferred Work**: Coverage gaps for follow-up
- **Action** — ShareReport: Present summary to user or primary agent
