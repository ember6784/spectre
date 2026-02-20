---
description: 👻 | Independent LLM Code Review - subagent
---
# code_review: Comprehensive Code Analysis

## Description

- Description — Conduct thorough, comprehensive code analysis covering all aspects of code quality, security, and production readiness. Provides comprehensive analysis in single review session with severity-based findings and actionable recommendations.
- Desired Outcome — Complete code review report with severity-categorized findings (CRITICAL/HIGH/MEDIUM/LOW), comprehensive scores, prioritized action plan, saved to a scoped report file (default `comprehensive_code_review.md`, but use a scoped filename if one already exists).

## ARGUMENTS Input

Optional user input to seed this workflow.

&lt;ARGUMENTS&gt; $ARGUMENTS &lt;/ARGUMENTS&gt;

## Step (1/4) - Define Review Scope

- **Action** — ProcessGuidance: Check for ARGUMENTS and extract guidance.
  - **If** ARGUMENTS exists → acknowledge guidance; extract specific focus areas;
  - Proceed with comprehensive review while honoring context
- **Action** — SpecifyScope: Define exact scope using completed work and modified files to prevent scope creep.
  - **CRITICAL**: Before dispatching review agent, provide what was actually implemented and files touched/modified; gives concrete scope boundaries regardless of work origin

**Review Scope Specification - Choose Appropriate Scenario:**

**Common File Format (All Scenarios):**

```plaintext
**Files Modified/Created:**
- `path/to/file.ext` ({created|modified|deleted} - {purpose/what changed})

**Related Files for Review:**
- `path/to/related.ext` ({imports|dependencies|tests|config})
```

#### **Scenario A: Work from Task List** (when `tasks.md` exists and was followed)

```plaintext
**Work Completed (from Task List):**
- Task 1.1: [exact task description from tasks.md]
- Task 1.2: [exact task description from tasks.md]
- Task 2.1: [exact task description from tasks.md]

[Use common file format above]
```

#### **Scenario B: Work from Plan** (working from `plan.md` without formal tasks)

```plaintext
**Work Completed (from Plan Implementation):**
- Implemented: [specific functionality completed, referencing plan.md sections]
- Delivered: [specific features/capabilities built]
- Completed: [specific plan items addressed]

[Use common file format above]

**Plan Context:**
- Plan Section: [specific sections of plan.md implemented]
- Plan Requirements: [requirements from plan this work addresses]
```

#### **Scenario C: Ad-hoc/Independent Work** (work without formal tasks or detailed plan)

```plaintext
**Work Completed (Independent Implementation):**
- Implemented: [specific functionality completed]
- Purpose: [why this work was done - bug fix, feature addition, etc.]
- Scope: [what was intended to be delivered]

[Use common file format above]

**Requirements Context:**
- Original Requirements: [extract from task_summary.md, PRD, or user request]
- Acceptance Criteria: [how success is defined for this work]
- Constraints: [any technical or scope constraints that applied]
```

- **Action** — ExtractWorkContext: Extract requirements and context from appropriate documentation based on scenario.
  - All scenarios: Extract work requirements → trace to origin docs (PRD/task_summary) → pull technical details → identify file context → document out-of-scope
  - **Scenario A**: Source from `tasks.md`
  - **Scenario B**: Source from `plan.md`/`quick_task_plan.md`
  - **Scenario C**: Source from task_summary.md/PRD/user comms; define acceptance criteria

## Step (2/4) - Dispatch Review Agent

- **Action** — GenerateReviewPrompt: Create comprehensive @spectre:reviewer subagent prompt replacing bracketed placeholders:

────────────────────────────────────

### 🔍 Comprehensive Code Review Agent Prompt

**Review Type:** Comprehensive Analysis (All Aspects)

**Work Completed for Review:**\[Choose appropriate format based on work origin - Scenario A, B, or C from Step 2\]

**Files Modified/Created:**\[Complete list of files touched during implementation\]

- `path/to/file1.py` (created - \[brief purpose\])
- `path/to/file2.py` (modified - \[what was changed\])
- `path/to/file3.py` (deleted - \[reason\])

**Related Files to Review:**\[Dependencies, tests, config files that may be impacted\]

- `path/to/related1.py` (imports/dependencies)
- `path/to/test_file.py` (test coverage)
- `config/settings.py` (configuration changes)

**Requirements & Context:**\[Specific requirements and acceptance criteria for work completed - extracted from appropriate documentation based on scenario\]

**Project Overview:**\[High‑level feature/bug description, requirements, acceptance criteria\]

**Documentation Context:**`docs/tasks/{task_name}/` (if available)

- Available docs: \[list which exist: task_summary.md, prd.md, plan.md, tasks.md\]
- Missing docs: \[list which expected docs are missing\]

**Guidelines & Preferences:**\[Style guides, architecture rules, naming conventions, test expectations\]

---

#### Step 1: Context Collection & Code Identification

**FIRST: Gather Task Context**

1. **Read Task Documentation**: Locate and read files in `docs/tasks/{task_name}/`:

   - `scope.md` or `ux.md` or `prd.md` or `spec.md` or any other scope artifact
   - `initial_plan.md` or `plan.md` or `quick_task_plan.md` - Implementation approach
   - `tasks.md` or `{task_name}_tasks.md` - Specific work items and progress

2. **Identify Code Scope**: Based on task documentation:

   - **Primary Files**: Files directly mentioned in plans and task lists
   - **Related Files**: Dependencies, imports, related modules
   - **Test Files**: Associated unit tests and integration tests
   - **Configuration**: Any config changes related to feature

3. **Explore Codebase**: Use codebase search tools to:

   - Find implementations mentioned in task documentation
   - Locate related functions, classes, modules
   - Identify recent changes related to task scope

**Code Review Scope Decision**: Focus review on code that:

- ✅ Is directly mentioned in task documentation
- ✅ Implements features described in plan
- ✅ Contains recent changes related to task objectives
- ✅ Has dependencies or impacts from primary implementation

**THEN: Proceed with Comprehensive Review**

---

#### Step 2: Comprehensive Code Review Analysis

**Severity Scale Reference:**

- **CRITICAL**: Prevents execution, security vulnerabilities, auth bypasses, data exposure
- **HIGH**: Affects maintainability, core functionality, user experience, resource leaks
- **MEDIUM**: Quality improvements, test coverage, configuration, performance (non-critical)
- **LOW**: Documentation, polish, cleanup

**Perform comprehensive analysis covering all aspects:**

### 🔧 Foundation & Correctness

**1. Compile/Run Readiness** → CRITICAL if prevents execution

- Syntax errors, unresolved references, missing imports/modules
- Misconfigured build / dependency files

**2. Structural Soundness** → HIGH if affects maintainability

- File & class organization, directory layout, module boundaries

**3. Implementation Completeness** → HIGH if core functionality missing

- Stubbed functions, TODO/FIXME markers, unhandled edge paths
- Absence of required unit tests or placeholders for them

**4. Logic Validation** → CRITICAL if breaks functionality

- Off‑by‑one mistakes, null handling, obvious condition errors
- End‑to‑end scenario walkthroughs against requirements
- State transitions and error flows for all inputs

### 🛡️ Security & Safety

**Input Validation & Injection Prevention** → CRITICAL

- SQL injection: Parameterized queries, input sanitization
- XSS: Output encoding, Content Security Policy, input validation
- Command injection: Avoid system calls with user input
- Path traversal: Validate file paths, use safe path operations

**Authentication & Authorization** → CRITICAL for auth bypasses

- Broken authentication: Session management, password policies
- Privilege escalation: Role-based access control validation
- JWT security: Proper signing, expiration, secure storage
- API authentication: Rate limiting, token validation

**Data Protection** → CRITICAL for data exposure

- Sensitive data exposure: Encryption at rest and in transit
- PII handling: Data minimization, proper anonymization
- Hard-coded secrets: Environment variables, secret management
- Insecure randomness: Cryptographically secure random generation

**API & Network Security** → HIGH

- SSRF: URL validation, allowlist external requests
- CORS misconfiguration: Proper origin validation
- API rate limiting: Prevent abuse and DoS
- HTTPS enforcement: Secure transport, HSTS headers

### 🎯 Quality & Robustness

**5. Error Handling & User Safety** → HIGH if affects user experience

- Ensure graceful degradation and clear, user‑appropriate messages
- Detect error states that could block users or leak internal details

**6. Test Coverage & Quality** → MEDIUM if adequate coverage exists

- Measure unit/integration test breadth, branch coverage, boundary cases
- Point out missing negative tests and flaky patterns

**7. Performance Considerations** → HIGH if affects UX, MEDIUM otherwise

- O(n²) loops on large data, excessive network/DB calls, synchronous waits
- N+1 queries, blocking I/O on hot paths
- Inefficient algorithms, caching opportunities

**8. Code Quality & Maintainability** → MEDIUM

- Duplication & reusability: Copy‑pasted blocks, redundant utility functions
- Design consistency: Architecture layers, API contracts, dependency inversion
- Naming coherence, comment accuracy, adherence to style guides

### 🚀 Production Readiness

**9. Resource Management** → HIGH if causes leaks, MEDIUM otherwise

- Memory & resource leaks: Unclosed files/streams, lingering timers, event listeners, DB cursors
- Repeated allocations in tight loops, large object retention

**10. Infrastructure & Configuration** → MEDIUM

- Insecure dependencies: Known CVEs, outdated packages
- Security headers: CSP, X-Frame-Options, etc.
- Error handling: No sensitive info in error messages
- Logging security: No credentials in logs, log injection prevention

**11. Documentation & Developer UX** → LOW

- Up‑to‑date README, code comments, public API docs
- Log levels appropriate, no PII in logs, actionable messages

**12. Final Polish** → LOW

- Remove unused functions, constants, feature flags, debug prints
- Ensure commit history or diff is clean and scoped

**Critical Rule for Review Recommendations:**

- **Flag as Issues**: Only problems that prevent delivering **Work Completed** requirements
- **Suggest Improvements**: Only changes that directly support **Work Completed** acceptance criteria
- **DO NOT Flag**: Missing functionality from incomplete work, future plans, or different scopes
- **DO NOT Suggest**: Enhancements beyond minimal viable implementation for completed work

---

### Response Format

**Structure your review report with these sections:**

1. **Work & File Scope Boundary Validation** – Confirmation that review aligns with completed work and modified files

   - Completed work parsed and understood (tasks/plan/independent work with specifics)
   - Modified/created files identified and their purposes understood
   - Work-specific requirements extracted from available documentation
   - In-scope vs out-of-scope work/files for THIS review clearly identified
   - Other work not completed or out of scope explicitly excluded from this review

2. **Context Collection Summary** – Brief overview of task documentation reviewed and code scope identified

3. **Files Reviewed** – List of specific files and code areas examined

4. **Summary Assessment** – Overall readiness, security posture, and risk level

5. **Detailed Findings by Severity**:

   **🚨 CRITICAL Issues** - Must fix before any deployment

   - `[File:Line]` **Security/Functionality**: \[Description and fix\]

   **🔥 HIGH Priority** - Should fix before next stage

   - `[File:Line]` **Logic/Performance**: \[Description and fix\]

   **⚠️ MEDIUM Priority** - Quality improvements

   - `[File:Line]` **Code Quality**: \[Description and fix\]

   **💡 LOW Priority** - Nice-to-have improvements

   - `[File:Line]` **Polish/Documentation**: \[Description and fix\]

6. **Comprehensive Scores (0‑10)**:

   - **Security Posture**: \[Score\] - Vulnerability assessment
   - **Logic Correctness**: \[Score\] - Functionality validation
   - **Code Quality**: \[Score\] - Maintainability and structure
   - **Production Readiness**: \[Score\] - Overall deployment readiness

7. **Prioritized Action Plan** – Ordered list of fixes by severity and impact

Save the report as **Markdown Document** (default `docs/tasks/{task_name}/reviews/comprehensive_code_review.md`; if it already exists, create a scoped variant like `docs/tasks/{task_name}/reviews/{task_name}_comprehensive_code_review_{timestamp}.md` to avoid overwriting). Create `docs/tasks/{task_name}` if it does not exist.

Respond to user with summary of only high priority items and point to file. Do not perform fixes yourself.

### Final Important Note

We are a startup building an early stage product hoping to find Product Market Fit. We must avoid over-engineering like the plague. Stick to YAGNI + SOLID + KISS + DRY principles. All recommendations, while comprehensive, should not over complicate the product or architecture for the stage that we're in.

**CRITICAL**:  DO NOT flag missing features from incomplete work or different scopes. DO NOT suggest improvements beyond what is explicitly requested in completed work. Focus only on ensuring code delivers what was specifically asked for in completed work, not entire project scope.

────────────────────────────────────

- **Action** — DispatchAgent: Deploy @spectre:reviewer subagent code review agent with comprehensive prompt above.

## Step (3/4) - Process Review & Create Action Plan

- **Action** — CollectReview: Monitor and receive comprehensive code review analysis.

  - Wait for review agent completion
  - Receive comprehensive report with severity-based findings
  - Verify report covers all required areas (foundation, security, quality, production readiness)

- **Action** — ProcessFindings: Create actionable next steps.

  - Summarize by severity: Extract CRITICAL, identify HIGH, note MEDIUM, catalog LOW
  - Create action plan: Prioritize by severity and impact; suggest implementation order (CRITICAL → HIGH → MEDIUM → LOW); identify additional resources needed; group related fixes

- **Action** — PresentSummary: Present findings to user with numbered, severity‑based summary.

  > **🔍 Comprehensive Code Review Complete**
    **> **Overall Assessment**: \[Brief headline on code readiness, security posture, risk level\]
    **> **Review Report Location**: `{REVIEW_FILE}`
  >
  > ## Key Findings (Numbered for User Selection)
  >
  > ### 🚨 Critical Issues (Must Fix Immediately)
  >
  > 1. **\[Security/Functionality\]**: \[Brief description with file/line reference\]
  >
  >    - **Impact**: \[Why this is critical\]
  >    - **Recommendation**: \[Specific fix needed\]
  >
  > 2. **\[Security/Functionality\]**: \[Brief description with file/line reference\]
  >
  >    - **Impact**: \[Why this is critical\]
  >    - **Recommendation**: \[Specific fix needed\]
  >
  > ### 🔥 High Priority (Should Fix Next)
  >
  > 3. **\[Logic/Performance\]**: \[Brief description with file/line reference\]
  >
  >    - **Impact**: \[Quality/performance impact\]
  >    - **Effort**: \[Estimated complexity\]
  >
  > 4. **\[Error Handling\]**: \[Brief description with file/line reference\]
  >
  >    - **Impact**: \[User experience impact\]
  >    - **Effort**: \[Estimated complexity\]
  >
  > ### ⚠️ Medium Priority (Quality Improvements)
  >
  > 5. **\[Code Quality\]**: \[Brief description with file/line reference\]
  >
  >    - **Benefit**: \[Maintainability improvement\]
  >    - **Effort**: \[Low/Medium complexity\]
  >
  > 6. **\[Test Coverage\]**: \[Brief description with file/line reference\]
  >
  >    - **Benefit**: \[Quality assurance improvement\]
  >    - **Effort**: \[Low/Medium complexity\]
  >
  > ### 💡 Low Priority (Polish & Documentation)
  >
  > 7. **\[Documentation\]**: \[Brief description\]
  >    - **Benefit**: \[Developer experience improvement\]
  >    - **Effort**: \[Low complexity\]

## Step (4/4) - Handoff

- **Action** — RenderFooter: Render Next Steps using `@skill-spectre:spectre-guide` skill.

## Output Location

```bash
branch_name=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)
OUT_DIR=${target_dir:-docs/tasks/$branch_name}
mkdir -p "$OUT_DIR/reviews"
```