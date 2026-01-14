---
description: 👻 | Quickly scope, research, & plan s/m tasks - primary agent
---

# quick_dev: Scope → Research → Plan for Small/Medium Tasks

## Description
- **What** — Lightweight workflow for bug fixes and small features: confirm scope, research via parallel agents, create implementation plan
- **Outcome** — Validated scope, research synthesis, `quick_task_plan.md` with parent/sub-task structure

## ARGUMENTS Input

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## Step 1 - Gather Context

- **Action** — ImmediateReply: Respond before running tools
  - **If** ARGUMENTS has task context → proceed to Step 2
  - **Else** → ask: "What are you trying to build or fix? Share any docs or context."
  - **CRITICAL**: No tool calls here. No technical questions — research answers those.
- **Wait** — Only if ARGUMENTS empty

- **Action** — ReadFiles: Read any files mentioned by user completely (no limit/offset)

## Step 2 - Confirm Scope (Functional Only)

**Scope is about WHAT we're building, not HOW.** Technical approach comes from research.

- **Action** — PresentScope:
  > **📋 Scope Confirmation**
  >
  > **Objective**: {functional outcome}
  >
  > **✅ In Scope**: {what the feature does — behaviors, not implementation}
  >
  > **❌ Out of Scope**: {what we're NOT building}
  >
  > **Constraints**: {user-provided only}
  >
  > Reply with corrections or "Confirmed".

- **Wait** — User confirms or corrects

## Step 3 - Research

- **Action** — SpawnAgents: Launch parallel research agents
  - `@codebase-locator` — find WHERE files/components live
  - `@codebase-analyzer` — understand HOW code works
  - `@codebase-pattern-finder` — find similar implementations
  - `@web-search-researcher` — external docs (only if user asks)
  - **Wait** for ALL agents to complete

- **Action** — Synthesize: Compile findings with file paths, patterns, architectural decisions

## Step 4 - Clarify Ambiguities

- **Action** — AskClarifyingQuestions: Use AskUserQuestion tool for 3-5 questions
  - **Only ask** what research couldn't answer: scope edge cases, UX preferences, trade-off decisions
  - For multi-option questions: include Pros/Cons/Trade-offs
  - **Never ask** technical questions answerable by code

## Step 5 - Create Plan

- **Action** — DetermineOutputDir:
  - `OUT_DIR=docs/active_tasks/{branch_name}` (or user-specified)
  - `mkdir -p "${OUT_DIR}/specs"`

- **Action** — GeneratePlan: Create `{OUT_DIR}/specs/quick_task_plan.md` (use scoped name if exists)

  **Plan Structure**:
  1. Agreed Scope (Objective, In/Out of Scope, Constraints)
  2. Research Summary (key codebase findings)
  3. Approach Summary (strategy, integration points)
  4. Implementation Tasks (see format below)
  5. Success Criteria

  **Task Format**: `## Phase` → `### [1.1] Parent Task` → `- [ ] **1.1.1** Sub-task` → `- [ ] Criterion`

  **Sub-task guidance**:
  - Start with action verb, use technical terms, name files/components
  - Include: patterns, integration points, constraints
  - Exclude: code snippets, line-by-line steps
  - 2-3 acceptance criteria per sub-task

  **Bounds**: ~3 phases, ~8 parent tasks max. If exceeds → suggest `/spectre:create_tasks`

- **Action** — ValidateCoverage: Verify all in-scope items have tasks; no out-of-scope tasks added

## Step 6 - Document & Handoff

- **Action** — PresentSummary:
  > **Task Plan Created**: `{path}`
  > ✅ Scope | ✅ Research | ✅ Plan

- **Action** — RenderFooter: Use `@skill-spectre:spectre` skill for Next Steps
