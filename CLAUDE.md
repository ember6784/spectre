# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPECTRE is a Claude Code plugin that implements an agentic workflow: **S**cope → **P**lan → **E**xecute → **C**lean → **T**est → **R**ebase → **E**valuate. It's a meta-prompt orchestration system where prompts invoke subagents that execute specialized prompts.

## Repository Structure

```
commands/           # 23 markdown command prompts (scope.md, plan.md, execute.md, etc.)
agents/             # 7 specialized subagent definitions (@coder, @analyzer, @locator, etc.)
hooks/              # Python hooks for session memory
  hooks.json        # Hook registration
  scripts/          # handoff-resume.py, capture-todos.py
references/         # Shared reference docs injected into prompts
.claude-plugin/     # Plugin registration (plugin.json, marketplace.json)
docs/               # Generated artifacts (scope docs, plans, handoff state)
```

## Commands

Run tests:
```bash
pytest hooks/scripts/test_handoff_resume.py
```

No build or lint commands - this is a prompt/configuration-only plugin.

## Architecture

### Meta-Prompt Orchestration
Commands are markdown prompts that:
1. Read user arguments
2. Spawn parallel subagents (`@spectre:coder`, `@spectre:analyzer`, etc.)
3. Subagents execute their specialized prompts
4. Main prompt synthesizes findings and produces artifacts

### Wave-Based Execution
`execute.md` groups tasks into dependency-aware waves that run in parallel, with reflection and adaptation between waves.

### Session Memory (Hooks)
Two Python hooks maintain context across sessions:
- **SessionStart** (`handoff-resume.py`): Restores previous session context from `docs/` handoff files
- **UserPromptSubmit** (`capture-todos.py`): Captures todos when `/spectre:handoff` is triggered

Both use `os.fork()` for non-blocking background processing.

### Generated Artifacts
Commands create files in `docs/active_tasks/{branch}/`:
- `{task}_scope.md` - Scope boundaries
- `{task}_plan.md` - Implementation plan
- `tasks.md` - Task breakdown
- `{timestamp}_handoff.json` - Session state
- `{timestamp}_todos.json` - Captured todos

## Key Patterns

### Hook Non-Blocking Pattern
```python
pid = os.fork()
if pid == 0:
    do_work()  # Child does I/O
    os._exit(0)
else:
    sys.exit(0)  # Parent returns immediately
```

### Command Flow
Every command ends with contextual "Next Steps" suggestions. Follow them—they're grounded in actual codebase state.

### Subagent Invocation
Commands spawn agents like `@spectre:codebase-analyzer` for parallel research. Agents return file:line references, not generic advice.

## Working in This Repo

- **Adding commands**: Create markdown in `commands/` following existing patterns (ARGUMENTS parsing, EXECUTION FLOW, Next Steps output)
- **Adding agents**: Create markdown in `agents/` with role, mission, and methodology sections
- **Modifying hooks**: Update Python scripts in `hooks/scripts/`, run tests, ensure non-blocking behavior
- **Testing hooks**: `pytest hooks/scripts/test_handoff_resume.py -v`

## Important Notes

- Commands always use `/spectre:` prefix (e.g., `/spectre:scope`)
- Session state lives in `docs/` and `.claude/spectre/` (both gitignored)
- Hooks use Python 3 standard library only (no external dependencies)
- `os.fork()` is Unix-only—Windows compatibility not yet implemented
