---

## description: 👻 | Scope features interactively - primary agent

# scope: Interactive Feature Scoping

Collaborative workflow for structuring unstructured thoughts into clear scope boundaries through contextual brainstorming and targeted clarifications. Focuses on user value and scope boundaries before technical considerations. Output: comprehensive scope document with clear boundaries, user value, and key decisions saved to `{OUT_DIR}/concepts/scope.md`.

## ARGUMENTS

&lt;ARGUMENTS&gt; $ARGUMENTS &lt;/ARGUMENTS&gt;

## Step 1: Immediate Reply & Gather Context

- **Action** — ImmediateReply: Respond before any tools.
  - **If** `FROM_KICKOFF=true` → acknowledge kickoff context, read `KICKOFF_DOC`, extract (Core Problem, User Value, Decisions Made, Remaining Ambiguities, Key Code Refs), **SKIP to Step 3**
  - **Else If** ARGUMENTS empty → probe for context enthusiastically
  - **Else** → proceed to Step 2
  - **CRITICAL**: No tool calls except reading kickoff doc when FROM_KICKOFF=true

## Step 2: Interactive Scope Exploration

**SKIP IF FROM_KICKOFF=true**

- **Action** — ExploreScope: Brief contextual dialogue (2-3 exchanges max).

  **CRITICAL**: Never ask empty questions. Always include contextual suggestions based on user input. **Pattern**: "Based on \[context\], I'm thinking \[specific suggestion\]. Is that right?"

  **Topics** (with contextual hypotheses):

  1. **User Problem & Value**: Formulate hypothesis. "Based on \[X\], the core problem seems to be \[Y\]. Is that right?"
  2. **Success Outcomes**: Present 2-4 concrete criteria. "I'm imagining success as: ✅ (1)..., (2)..., (3)... What would you adjust?"
  3. **Scope Boundaries**: Propose 3-5 OUT items. "I'd suggest OUT of scope: ❌ \[list\]. Do these boundaries feel right?"
  4. **Initial Decisions**: Identify 2-3 key decisions with options/trade-offs.

- **Action** — SummarizeExploration: Confirm understanding before clarifications.

  > **My Understanding**: **Core Problem**: \[specific\] **User Value**: \[why it matters\] **In Scope**: \[3-5 items\] **Out of Scope**: \[3-5 items\] **Decisions Needed**: \[specific ambiguities to clarify\]
  >
  > Does this match? Any corrections before targeted questions?

- **Wait** — User confirms or corrects

## Step 3: Generate Targeted Clarifications

- **Action** — DetermineOutputDir:

  - **If** FROM_KICKOFF → use same dir as kickoff doc
  - **Else** → `OUT_DIR = user_specified || docs/active_tasks/{branch_name}`
  - `mkdir -p "$OUT_DIR"`

- **Action** — GenerateTargetedQuestions: Create 5-8 questions based ONLY on ambiguities from Step 2 (or kickoff's "Remaining Ambiguities").

  **CRITICAL**: Only ask about unresolved ambiguities. Do NOT repeat clarified items.

  **Focus areas** (priority order): Scope boundary edge cases → Trade-off decisions (with pros/cons) → UX specifics → Constraints → Integration points

- **Action** — SaveClarifications: Create `{OUT_DIR}/clarifications/scope_clarifications_{timestamp}.md`:

  - Header: concept name, source (kickoff or exploration), context summary
  - Instructions: Answer in `<response>` blocks
  - Questions 1-8: Each with options (if trade-off) showing pros/cons/impact, then `<response>Preferred: | Notes:</response>`

- **Action** — PromptUser: "Saved clarifications to `{path}`. Answer in `<response>` blocks. Reply 'Read it' when ready."

- **Wait** — User replies

- **Action** — ReadClarifications: Read file, use responses (proceed with assumptions if empty)

## Step 4: Create Scope Document

- **Action** — CreateScopeDoc: Generate `{OUT_DIR}/concepts/scope.md` (use scoped filename if exists).

  **Priority**: User value and boundaries BEFORE technical details.

  **Sections**: The Problem (pain, impact, current state) → Target Users (primary, secondary, needs) → Success Criteria (outcomes, metrics) → User Experience (journeys, principles, trade-offs) → Scope Boundaries (in/out/maybe/future) → Constraints (platform, perf, a11y, scale) → Integration (touches, avoids, dependencies) → Decisions (from clarifications + rationale) → Risks (UX, scope creep, open questions) → Next Steps (`/spectre:plan` or `/spectre:create_tasks`, complexity S/M/L)

## Step 5: Iterative Refinement

- **Action** — PresentDraftBoundaries:

  > **Draft Boundaries**: ✅ **In Scope**: \[3-5 key features\] ❌ **Out of Scope**: \[3-5 exclusions\] ⚠️ **Maybe**: \[2-3 items\] ❓ **Open**: \[unresolved questions\]
  >
  > Adjustments? Move items between categories, add exclusions, tighten MVP, clarify priorities. Reply with changes or 'Looks good'.

- **Action** — RefineScope: Update scope doc based on feedback. Allow 1-2 rounds.

- **Wait** — User confirms boundaries

## Step 6: Light Technical Context (Optional)

**Only if scope identifies specific technical/architecture integration points.**

- **Action** — IdentifyTouchpoints: Identify desired areas of research, and dispatch parallel  @codebase-analyzer subagents to research each area. Surface-level only (component names, NOT implementation). List features this interacts with, constraints worth documenting, areas to avoid.

- **Action** — UpdateScopeDoc: Add findings to Integration & Constraints sections if relevant.

## Step 7: Final Review & Complete

- **Action** — PromptFinalReview:

  > **Scope Complete**: `{OUT_DIR}/concepts/scope.md`
  >
  > Includes: Problem & value, scope boundaries, UX journeys, success criteria, decisions, integration points.
  >
  > Review and reply 'Approved' or provide feedback.

- **Wait** — User approves

- **Action** — ConfirmCompletion: "Scope complete. Docs: `{OUT_DIR}/concepts/scope.md`, `{OUT_DIR}/clarifications/scope_clarifications_{timestamp}.md`"

- **Action** — RenderFooter: Render Next Steps using `@skill-spectre:spectre` skill.