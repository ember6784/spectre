---
description: 👻 | Scope features interactively - primary agent
---

# scope_riff: Interactive feature and task scoping

### Description
- Description — Collaborative workflow for helping users structure unstructured thoughts into clear scope boundaries through contextual brainstorming and targeted clarification questions. Focuses on user value, scope boundaries (what's in/out), and UX before technical considerations.
- Desired Outcome — Comprehensive scope document (default `scope.md`, but use a scoped filename if one already exists) with clear boundaries, user value proposition, key decisions, and minimal ambiguity, ready for `/new_task` or `/quick_task`.

### INPUTS

ARGUMENTS -> $ARGUMENTS

### Step (1/7) - Immediate Reply & Gather Context

- **Action** — ImmediateReply: Respond immediately before running any commands or tools.
  - **If** `ARGUMENTS` contains `FROM_KICKOFF=true`:
    - Acknowledge the kickoff context: "Continuing from kickoff research. I have the context from our exploration — let's lock down the scope."
    - Read the kickoff document referenced in ARGUMENTS (`KICKOFF_DOC` path)
    - Extract: Core Problem, User Value, Decisions Made, Remaining Ambiguities, Key Code References
    - **SKIP Step 2 entirely** — proceed directly to **Step 3** (Targeted Clarifications)
  - **Else If** `ARGUMENTS` was empty → let the user know you are ready to help them scope their idea, and probe enthusiastically for more information or context to get them started.
  - **Else** Proceed immediately to **Step 2**
  - **CRITICAL**: Do NOT run any tool calls in this step (except reading kickoff doc when FROM_KICKOFF=true)
- **Wait** — User provides input or confirms (skip if FROM_KICKOFF=true)

### Step (2/7) - Interactive Scope Exploration

**SKIP THIS STEP IF FROM_KICKOFF=true** — Kickoff already performed exploration.

**Goal**: Help user articulate and structure unstructured thoughts through contextual conversation

- **Action** — ExploreScope: Engage in brief contextual dialogue (2-3 exchanges maximum)

  **CRITICAL - Contextual Suggestions Required**:
  - **NEVER** ask empty questions like "What does success look like?" or "What's out of scope?"
  - **ALWAYS** include contextual suggestions based on user's input
  - **Format**: "Based on [context from user], I'm thinking [specific suggestion]. Is that right?"
  - **Goal**: Make it easy for user to confirm, correct, or build upon suggestions

  **Topics to explore with contextual suggestions**:

  1. **User Problem & Value** (with contextual hypothesis):
     - Read initial concept/arguments to understand context
     - Formulate specific hypothesis about the user problem
     - Example: "Based on 'users forgetting usage over time,' it sounds like the core problem is lack of visibility into historical usage patterns, making it hard to track consumption or plan ahead. Is that the pain point you're addressing?"

  2. **Success Outcomes** (with specific suggestions):
     - Present 2-4 concrete success criteria based on context
     - Example: "I'm imagining success as: (1) Users can view usage history for the last 90 days minimum, (2) They can export raw data (CSV?) for their own analysis, (3) Access is fast and doesn't require complex setup. What would you adjust?"

  3. **Scope Boundaries** (with suggested exclusions):
     - Propose 3-5 specific OUT of scope items based on context
     - Example: "Given the focus on raw data access, I'd suggest OUT of scope: ❌ Visual dashboards or charts, ❌ Usage analytics or insights/recommendations, ❌ Sharing or team features, ❌ Historical comparisons or trends. Do these boundaries feel right?"

  4. **Initial Decisions** (with option analysis):
     - Identify 2-3 key decisions that need user input
     - Present options with brief trade-offs
     - Example: "I notice we need to decide on the history timeframe - I'm thinking either 30 days (simpler, faster) vs. 12 months (more useful but slower). Which direction feels right?"

  **Exchange Pattern**:
  ```
  Agent: [Contextual question with specific suggestions based on user input]
  User: [Confirms, corrects, or builds upon suggestions]
  Agent: [Follow-up with more contextual suggestions in next area]
  User: [Further refinement]
  Agent: [Summarize understanding and identify ambiguities - see next action]
  ```

- **Action** — SummarizeExploration: Confirm understanding before moving to targeted clarifications:

  Present clear summary to user:
  > "Here's my understanding after our discussion:
  >
  > **Core User Problem**: [Specific problem being solved, based on conversation]
  >
  > **User Value**: [Why this matters, what outcomes we're targeting]
  >
  > **Firm Scope Boundaries**:
  > ✅ **In Scope**:
  > - [3-5 specific items confirmed in conversation]
  >
  > ❌ **Out of Scope**:
  > - [3-5 specific exclusions confirmed in conversation]
  >
  > **Decisions Still Needed** (I'll generate targeted clarification questions for these):
  > - [Specific ambiguity 1 - e.g., "History timeframe: 30 days vs 12 months vs all time"]
  > - [Specific ambiguity 2 - e.g., "Export formats: CSV only vs CSV+JSON"]
  > - [Specific ambiguity 3 - e.g., "Data granularity: daily summaries vs detailed logs"]
  >
  > Does this match your thinking? Any corrections before I generate targeted clarification questions?"

- **Wait** — User confirms or corrects understanding

### Step (3/7) - Generate Targeted Clarifications Document

**Goal**: Remove specific ambiguities identified in Step 2 (or kickoff, if FROM_KICKOFF=true) through structured questions

- **Action** — DetermineOutputDir: Decide where to save artifacts for this workflow.
  - `branch_name=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)`
  - **If** FROM_KICKOFF=true → use same `OUT_DIR` as kickoff document (extract from `KICKOFF_DOC` path)
  - **Else If** user specifies `target_dir/path` → `OUT_DIR={that value}`
  - **Else** → `OUT_DIR=docs/active_tasks/{branch_name}`
  - `mkdir -p "OUT_DIR"`

- **Action** — GenerateTargetedQuestions: Create 5-8 TARGETED questions based ONLY on ambiguities identified in Step 2 (or kickoff's "Remaining Ambiguities" if FROM_KICKOFF=true).

  **CRITICAL - Only Ask About Ambiguities**:
  - **DO NOT** repeat questions about things already clarified in exploration (Step 2 or kickoff)
  - **ONLY** ask about specific decisions, edge cases, or ambiguous areas identified in the summary
  - **If FROM_KICKOFF=true**: Use the "Remaining Ambiguities" and "Decision Points" from kickoff document as the source of questions
  - **Focus Areas** (in priority order):
    1. **Scope Boundary Edge Cases**: Ambiguous items that could be in or out
    2. **Specific Trade-off Decisions**: Where user needs to choose between options (with pros/cons analysis)
    3. **UX Specifics**: User flow details, interaction patterns, accessibility requirements
    4. **High-Level Constraints**: Performance expectations, platform requirements, scale needs
    5. **Integration Points**: What existing features this touches (NOT implementation details)

  **Avoid**:
  - Questions about things confirmed in Step 2
  - Technical implementation details or architecture decisions
  - Generic questions if scope is already clear in that area

  **Example** - If Step 2 revealed "export feature" as in-scope but format unclear:
  - ✅ Ask: "Export formats - which are in scope?" [with options CSV only vs CSV+JSON with pros/cons]
  - ❌ Don't ask: "Should we include export?" (already answered in Step 2)

- **Action** — SaveClarifications: Create `{OUT_DIR}/clarifications/scope_clarifications_{timestamp}.md` with template:
  ```markdown
  # Scope Clarifications for {concept_name}
  *Created by: scope_riff.md on {timestamp}*
  *Source: {FROM_KICKOFF ? "Kickoff research" : "Scope exploration"}*

  **Context from Exploration**:
  - Core Problem: [summary from Step 2 OR kickoff document]
  - Firm Boundaries: [what's already clear from Step 2 OR kickoff]
  - Kickoff Document: [{KICKOFF_DOC path if FROM_KICKOFF=true, else omit}]

  **Instructions**: Answer inside each `<response></response>` block. If a question involves choosing between approaches, list the Options inline under that question, then select Preferred option inside the response. If not applicable, reply 'skip'.

  ## Targeted Questions (Ambiguities Only)

  1) {targeted question 1 - addressing specific ambiguity from Step 2}
  Options (if applicable):
  - Option A — {short name}
    - Pros: {2–4 bullets}
    - Cons: {2–4 bullets}
    - Trade-offs: {what you gain vs. lose}
    - Impact: {UX | scope | complexity | delivery}
  - Option B — {short name}
    - Pros: {2–4 bullets}
    - Cons: {2–4 bullets}
    - Trade-offs: {what you gain vs. lose}
    - Impact: {UX | scope | complexity | delivery}
  <response>
  Preferred option: {Option A|Option B|Other|skip}
  Notes: {Any additional guidance}
  </response>

  2) {targeted question 2}
  [same structure for questions 2-8]
  ```

- **Action** — PromptUser: "I saved targeted clarification questions here: `{path}`. These address the specific ambiguities we identified. Please add answers inside `<response>` blocks. If you prefer me to proceed with assumptions, leave blocks empty. Reply 'Read it' when ready."
- **Wait** — User replies "Read it"
- **Action** — ReadClarifications: Re-open clarifications file from disk (no limits) and use responses. If empty, proceed with documented assumptions

### Step (4/7) - Create Scope Document

**CRITICAL**: Wait for updated clarifications before proceeding.

- **Action** — CreateOutputDir: Create concepts directory.
  - `mkdir -p "OUT_DIR/concepts"`

- **Action** — CreateScopeDoc: Generate comprehensive scope document; default path `{OUT_DIR}/concepts/scope.md` but if that exists, create a scoped filename (e.g., `{OUT_DIR}/concepts/{task_name}_scope.md` or `scope_{timestamp}.md`) to avoid overwriting. Use the chosen path for all references.
  - **Priority**: User value and scope boundaries BEFORE technical details
  - Use sections below and populate from conversation and clarification responses
  - Template:
    ```markdown
    # {Feature/Task Name} - Scope Definition

    ## The Problem
    **User Pain Point**: [What specific user problem or opportunity are we addressing?]

    **Why It Matters**: [What's the impact of NOT solving this? Who is affected?]

    **Current State**: [What do users do today? What's broken or missing?]

    ## Target Users
    **Primary Users**: [Who will use this primarily?]

    **Secondary Users**: [Who else benefits or is affected?]

    **User Needs**: [What are their key needs and constraints?]

    ## Success Criteria
    **User Outcomes** (what does "done" look like from user perspective):
    - [Specific outcome 1 - e.g., "Users can view their full usage history in under 2 seconds"]
    - [Specific outcome 2]
    - [Specific outcome 3]

    **Success Metrics** (how we'll know this is valuable):
    - [Metric 1 - e.g., "80% of users access history at least monthly"]
    - [Metric 2]

    ## User Experience

    ### Key User Journeys
    **Primary Flow**:
    1. [Entry point - e.g., "User clicks 'Usage History' in account menu"]
    2. [Key interactions]
    3. [Exit point/outcome]

    **Alternative Flows** (if applicable):
    - [Alternative path 1]
    - [Edge case flow]

    ### UX Principles & Trade-offs
    **Guiding Principles**:
    - [Principle 1 - e.g., "Prioritize speed over comprehensiveness"]
    - [Principle 2 - e.g., "Raw data access, not curated insights"]

    **Acceptable Trade-offs**:
    - ✅ [What we're willing to compromise - e.g., "Simple table view vs rich visualizations"]
    - ❌ [What we won't compromise - e.g., "Must support keyboard navigation"]

    ## Scope Boundaries

    ### In Scope (Minimum Valuable Version)
    **Core Features**:
    - [Feature 1 - specific and measurable]
    - [Feature 2]
    - [Feature 3]

    **User Scenarios Covered**:
    - [Scenario 1]
    - [Scenario 2]

    **Must-Have Capabilities**:
    - [Capability 1]
    - [Capability 2]

    ### Out of Scope (Now)
    **Explicitly Excluded**:
    - ❌ [Feature/capability we're NOT building - e.g., "Analytics or trend visualization"]
    - ❌ [Another exclusion - e.g., "Automated usage alerts"]
    - ❌ [Another exclusion - e.g., "Team/shared access"]

    **Future Enhancements** (consider later):
    - 🔮 [Potential future addition 1]
    - 🔮 [Potential future addition 2]

    **Related But Separate Work**:
    - [Other initiative this doesn't include]

    ### Maybe/Deferred
    - ⚠️ [Item that could be included if scope allows]
    - ⚠️ [Dependency that might expand scope]

    ## High-Level Constraints
    **Platform/Environment**:
    - [Platform requirements - e.g., "Web only, mobile responsive"]
    - [Browser/device constraints]

    **Performance Expectations**:
    - [Performance requirement - e.g., "Load history in <2s for 90 days of data"]

    **Accessibility**:
    - [Accessibility level - e.g., "WCAG 2.1 AA compliance required"]

    **Scale/Volume**:
    - [Scale expectations - e.g., "Support up to 10,000 usage events per user"]

    ## Integration & Dependencies

    ### Existing Features This Touches
    - [Feature/system 1 - e.g., "Account settings page (adds new menu item)"]
    - [Feature/system 2 - e.g., "Usage tracking API (reads data)"]

    ### What This Should NOT Affect
    - ❌ [System/feature to avoid - e.g., "Billing calculations"]
    - ❌ [Another area to avoid]

    ### External Dependencies
    - [Dependency 1 - e.g., "Requires usage data collection to be active"]
    - [Dependency 2]

    ## Key Decisions Made
    **Decisions from Clarifications**:
    - [Decision 1 from Step 3 - with rationale]
    - [Decision 2 from Step 3 - with rationale]
    - [Decision 3 from Step 3 - with rationale]

    **Trade-offs Accepted**:
    - [Trade-off 1 - what we chose and why]
    - [Trade-off 2]

    ## Risks & Open Questions

    ### User Experience Risks
    - ⚠️ [UX risk 1 - e.g., "Users may not find the feature in account menu"]
    - ⚠️ [UX risk 2]

    ### Scope Risks
    - ⚠️ [Scope creep risk 1 - e.g., "Requests for filtering may expand scope"]
    - ⚠️ [Scope creep risk 2]

    ### Open Questions
    - ❓ [Unresolved question 1 that might affect scope]
    - ❓ [Unresolved question 2]

    ## Next Steps
    - [ ] Review scope with stakeholders (if applicable)
    - [ ] Create an Implementation Plan: `/spectre:plan` or jump straight to tasks `/spectre:create_tasks`
    - [ ] Complexity estimate: **[Small/Medium/Large]**

    ## Source
    - Scope exploration from Step 2
    - Targeted clarifications in `clarifications/scope_clarifications_{timestamp}.md`
    ```

### Step (5/7) - Iterative Scope Refinement

**Goal**: Refine scope boundaries collaboratively before finalizing

- **Action** — PresentDraftBoundaries: Share draft scope boundaries in chat for quick refinement:
  > I've drafted the scope boundaries based on our discussion and clarifications:
  >
  > **✅ In Scope (Minimum Valuable Version)**:
  > - [3-5 key features/capabilities from scope document]
  >
  > **❌ Out of Scope**:
  > - [3-5 key exclusions from scope document]
  >
  > **⚠️ Maybe/Deferred**:
  > - [2-3 items that could expand scope]
  >
  > **❓ Open Questions** (if any):
  > - [Any unresolved questions that might affect scope]
  >
  > What would you like to adjust? Common refinements:
  > - Move items between in-scope/out-of-scope/maybe
  > - Add explicit exclusions to prevent scope creep
  > - Tighten the minimum valuable version
  > - Clarify priorities or user journey focus
  >
  > Reply with specific changes or 'Looks good' to proceed to final review.

- **Action** — RefineScope: Make adjustments based on user feedback
  - Update scope document with any changes
  - Update task_context.md with refinement notes
  - Allow 1-2 rounds of refinement if needed

- **Wait** — User confirms scope boundaries are correct

### Step (6/7) - Light Technical Context (Optional)

**Goal**: Add minimal technical context ONLY if scope involves integration with existing systems

- **Condition**: Only proceed if scope document identifies specific integration points

- **Action** — IdentifyTouchpoints: Surface-level identification (NO deep implementation research):
  - List existing features/components this might interact with (just names/purposes)
  - Note high-level technical constraints worth documenting
  - Identify areas that should NOT be touched
  - **Effort limit**: Surface-level only
  - **Depth**: Surface-level only - file/component names, NOT implementation details

- **Action** — UpdateScopeDoc: Add brief technical context to scope document if findings are relevant:
  - Update "Integration & Dependencies" section with component names
  - Add any critical technical constraints to "High-Level Constraints"
  - Note any "do not touch" areas in "What This Should NOT Affect"

- **Action** — UpdateContext: Append minimal technical findings to `task_context.md`:
  ```markdown
  ## Light Technical Context (Optional)
  *Added by: scope_riff.md on {timestamp}*

  ### Integration Touchpoints
  - {Component/file name} - {brief purpose}
  - {Component/file name} - {brief purpose}

  ### Technical Constraints
  - {Constraint if any}

  ### Areas to Avoid
  - {System/component to not modify}
  ```

### Step (7/7) - Final Review & Complete

- **Action** — PromptFinalReview: Direct user to review complete scope document:
  > **📄 Scope Definition Complete**
  >
  > I've created a comprehensive scope document here:
  > **`{OUT_DIR}/concepts/scope.md`**
  >
  > The document includes:
  > - ✅ User problem and value proposition
  > - ✅ Clear scope boundaries (in/out/maybe)
  > - ✅ User experience and key journeys
  > - ✅ Success criteria and metrics
  > - ✅ Key decisions from our clarifications
  > - ✅ Integration points and constraints (if applicable)
  >
  > Please review the document directly and confirm:
  > - Does it accurately capture what we're trying to achieve?
  > - Are the boundaries clear enough to prevent scope creep?
  > - Are there any missing considerations?
  >
  > Reply 'Approved' to finalize, or provide specific feedback for revisions.

- **Wait** — User reviews and approves final scope document

- **Action** — ConfirmCompletion: Present completion summary:
  > **🎯 Scope Definition Complete - Ready for Next Phase**
  >
  > **Process Completed:**
  > - ✅ **Interactive Exploration**: Helped structure unstructured thoughts into clear scope boundaries
  > - ✅ **Targeted Clarifications**: Resolved specific ambiguities through structured questions
  > - ✅ **Iterative Refinement**: Collaboratively refined scope boundaries
  > - ✅ **Scope Document**: Comprehensive scope definition prioritizing user value and boundaries
  > - ✅ **Technical Context**: Minimal integration touchpoints identified (if applicable)
  >
  > **Documents Created/Updated:**
  > - ✅ **Scope Definition**: `{OUT_DIR}/concepts/scope.md`
  > - ✅ **Clarifications**: `{OUT_DIR}/clarifications/scope_clarifications_{timestamp}.md`
  > - ✅ **Task Context**: `{OUT_DIR}/task_context.md`
  >
  > The Scope Definition is now complete with clear boundaries and minimal ambiguity, ready for the next phase.

- **Action** — RenderFooter: Render Next Steps footer using `@spectre:spectre` skill (contains format template and SPECTRE command options)

### Next Steps

See `@spectre:spectre` skill for footer format and command options.