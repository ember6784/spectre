---
description: 👻 | Unified planning entry point - researches, assesses complexity, routes to workflow - primary agent
---

# plan: Intelligent Planning Router

## Description
- **What** — Research codebase, assess complexity, route to appropriate workflow (direct tasks or plan-first)
- **Outcome** — Detailed task breakdown ready for execution

## ARGUMENTS Input

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## Instructions
- Research before routing; present architectural options for user buy-in
- Route based on hard-stops and clarity, not point-scoring
- Never overwrite existing `tasks.md` or `plan.md` — use scoped names

## Step 1 - Research Codebase

- **Action** — DetermineOutputDir:
  - `OUT_DIR=docs/active_tasks/{branch_name}` (or user-specified)
  - `mkdir -p "${OUT_DIR}"`

- **Action** — CheckExistingResearch: Read `{OUT_DIR}/task_context.md` for "## Technical Research"
  - **If** comprehensive → use existing, skip research
  - **Else** → proceed

- **Action** — AutomatedResearch: Spawn parallel agents
  - `@codebase-locator`, `@codebase-analyzer`, `@codebase-pattern-finder`
  - **Wait** for all; read identified files

- **Action** — SaveResearch: Update `{OUT_DIR}/task_context.md` with Architecture Patterns, Dependencies, Implementation Approaches, Impact Summary

## Step 2 - Present Architectural Options

- **Action** — PresentOptions: 2-4 strategies (simplest to most robust)
  - Each: core approach, trade-offs, when it makes sense
- **Wait** — User selects strategy
- **Action** — UpdateContext: Document selection in task_context.md

## Step 3 - Decide Routing

- **Action** — EvaluateHardStops: Any true = PLAN_FIRST
  | db_schema_destructive | new_service_or_component | auth_or_pii_change |
  | payment_billing_logic | public_api_change | caching_consistency | slo_sla_risk |

- **Action** — MakeDecision:
  - **If** any hard-stop OR ambiguity OR user requests → `PLAN_FIRST`
  - **Else** → `DIRECT_TASKS`

- **Action** — AnnounceRoute: Tell user which path and why

## Step 4 - Route to Workflow

**CRITICAL**: Use Skill tool to invoke slash commands. Do NOT just describe.

- **If** `DIRECT_TASKS`:
  - **Action** — ExecuteSkill: `/spectre:create_tasks {OUT_DIR}/task_context.md`
  - **Wait** — Returns task breakdown

- **ElseIf** `PLAN_FIRST`:
  - **Action** — ExecuteSkill: `/spectre:create_plan {OUT_DIR}/task_context.md`
  - **Wait** — Returns plan
  - **Action** — PromptUser: "Review plan. Reply 'Approved' or provide feedback."
  - **Wait** — User approval
  - **Action** — ExecuteSkill: `/spectre:create_tasks`
  - **Wait** — Returns task breakdown

- **Action** — RenderFooter: Use `@skill-spectre:spectre` skill for Next Steps
