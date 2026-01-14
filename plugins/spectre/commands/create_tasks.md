---
description: 👻 | Transform requirements into executable tasks - primary agent
---

# create_tasks: Unified Task Breakdown

Transform requirements into detailed, actionable task lists with dependency analysis and execution options. Adapts to context: uses existing research when sufficient, conducts research when needed. Outputs sequential and parallel execution strategies. Scales naturally to scope size.

## ARGUMENTS

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

---

## Step 1: Establish Context

### 1a. Determine Output Location
- `TASK_DIR = user_specified || docs/active_tasks/{branch_name}`
- `mkdir -p "${TASK_DIR}/specs" "${TASK_DIR}/research" "${TASK_DIR}/clarifications"`

### 1b. Scan Artifacts
Inventory `TASK_DIR/`: task_summary.md, prd.md, ux.md, plan.md, task_context.md, research/*.md + thread context, ARGUMENTS.

### 1c. Assess Complexity
**Simple** (no research): Single file, clear pattern, explicit scope | **Complex** (research needed): Multi-component, new patterns, unclear approach

---

## Step 2: Research Decision

### 2a. Need Research?
- **If** simple with clear scope → `NEED_RESEARCH=false`
- **If** complex or unclear → `NEED_RESEARCH=true`

### 2b. Have Research? (if needed)
Check artifacts for: codebase patterns, integration points, technical approach, target files.
- **If** sufficient coverage → `HAVE_RESEARCH=true`
- **If** gaps exist → `HAVE_RESEARCH=false` (note gaps)

### 2c. Action
- `NEED=false` → proceed to Step 3
- `NEED=true` AND `HAVE=true` → read existing, proceed to Step 3
- `NEED=true` AND `HAVE=false` → conduct research (2d)

### 2d. Conduct Research (conditional)
Spawn parallel: @codebase-locator, @codebase-analyzer, @codebase-pattern-finder
Review: CLAUDE.md, README.md, architecture docs
Save to `${TASK_DIR}/task_context.md` under "## Technical Research"

---

## Step 3: Extract Requirements

### 3a. Gather & Synthesize
Read all sources (task_summary, prd, plan, ux, thread, ARGUMENTS). Extract: what to build, users, success criteria, out of scope, constraints. Number: REQ-001, REQ-002. Categorize: Core, UX, Technical.

### 3b. Boundary Check
**Scope Litmus Test**: Would user recognize this as exactly what they asked?
**STRICT**: Deliver ONLY what's explicitly stated. No optimizations, extra features, future-proofing unless requested.

---

## Step 4: Generate Tasks

### 4a. Synthesize Architecture Context
- **Action** — SynthesizeArchitectureContext: Document where work fits, technical approach, key decisions (with file references).

### Task Hierarchy
📦 **Phase** (organizational) → 📋 **Parent** (small-medium deliverable) → ✓ **Sub-task** (atomic, 2-3 criteria) → ✓ **Criteria** (verifiable outcomes)

**Numbering**: Phase 1 → 1.1, 1.2 → 1.1.1, 1.1.2 → ✓

### 4b. Create Parent Tasks
- **Action** — CreateParentTasks: Draft phases and parents (📋) covering complete scope. Each parent = cohesive deliverable.

### 4c. Break Down Sub-tasks
- **Action** — BreakdownSubTasks: For each parent, generate sub-tasks.
  - Format: Action verb + technical specifics + file names. Single focused change.
  - **Include**: Technical terms, patterns, integration points, file names, constraints
  - **Avoid**: Code snippets, function signatures, line-by-line steps
  - Criteria: 2-3 verifiable outcomes per sub-task. Split if 5+ criteria.

### 4d. Validate
- **Action** — VerifyCoverage: Map requirements to tasks. Flag gaps → add. Flag unjustified → remove.
- **Action** — ValidateTasks: Coverage, Exclusion (nothing beyond requests), Structure (hierarchy, atomic, verifiable)

---

## Step 5: Dependency Analysis & Execution

### 5a. Map Dependencies
Review parents (📋): output deps, file conflicts, type ordering (setup → work → tests).

### 5b. Sequential Execution
Step-by-step order: `1. Task 1.1 (no deps) → 2. Task 1.2 (depends on 1.1) → ...`

### 5c. Parallel Waves
Group independent parents: Wave 1 (no deps) → Wave 2 (depends on W1) → ... Include rationale.

---

## Step 6: Document & Output

### 6a. Write tasks.md
`TASKS_FILE = ${TASK_DIR}/specs/tasks.md` (use scoped name if exists)

**Sections**: Header → Objective → Scope (in/out) → Requirements Traced (ID|Desc|Source|Tasks table) → Architecture Context (where fits, approach, decisions with file refs) → Tasks (Phase → Parent [1.1] → Sub-tasks with criteria) → Execution Strategies (sequential + parallel) → Coverage Summary

### 6b. Present Summary
- **Action** — SummarizeStructure: "Task Breakdown Complete. Structure: {X} phases, {Y} parents, {Z} sub-tasks. [List phases with parent titles]. Execution: Sequential ({N} steps) | Parallel ({M} waves). Saved to: {path}"

### 6c. Next Steps Footer
- **Action** — RenderFooter:

```
╔══════════════════════════════════════════════════════════╗
║ NEXT STEPS                                               ║
╠══════════════════════════════════════════════════════════╣
║ 🧭 Phase: Task Planning | 🟢 Complete                    ║
║                                                          ║
║ 🎯 Next — Review tasks, then choose execution approach   ║
║                                                          ║
║ ➡️ Options:                                               ║
║ - /spectre:execute — Begin implementation               ║
║ - /spectre:validate — Verify task coverage              ║
║ - Review tasks.md — Adjust before execution              ║
╚══════════════════════════════════════════════════════════╝
```
