---
name: paf-init-project
description: 'Define project purpose, intent, scope, and solution direction at project start. Use when: new project kickoff, project discovery, requirements capture, clarifying goals, writing PROJECT.md, identifying PAF module boundaries.'
argument-hint: '[--max-rounds <1-20>] [--skip-memory]'
---

# PAF Project Intent Initialization

Run a structured discovery workflow at the start of a project to define intent, requirements, constraints, and an initial PAF module plan.

Primary outputs:
- Updated `PROJECT.md` with project intent and solution direction
- Optional updates to `MEMORY.md` for reusable implementation rules and constraints

## When to Use
- Starting a new project from this template
- Forking this template and replacing template intent with real project intent
- Before designing or implementing modules
- When requirements are vague and need structured discovery

## Inputs

Ask only if the user did not provide them:
1. Maximum interview rounds (default: `20`, allowed: `1-20`)
2. Whether to write rules/constraints to `MEMORY.md` (`yes`/`no`, default: `yes`)

## Procedure

### Step 1 - Read current context files

1. Read `PROJECT.md` and `MEMORY.md`.
2. Merge and preserve valid existing content by default.
3. Replace existing content only when:
   - the user explicitly asks to replace it, or
   - new user-provided information clearly conflicts with older content and replacing the older content will produce a more accurate overall project definition.
4. If this is still a template-intent project, treat discovery answers as the source of truth.

### Step 2 - Run iterative discovery interview (up to max rounds)

Run an interview loop using concise, high-signal questions.

For each round:
1. Ask one focused question that deepens intent understanding.
2. Ask a follow-up control question: "Continue with another question?" with options:
   - `continue`
   - `finish`
3. Stop early when the user selects `finish`.
4. Stop automatically at max rounds.

Question priorities (in order):
1. Mission and problem statement
2. End users/stakeholders and success criteria
3. Scope boundaries and non-goals
4. Functional capabilities and workflows
5. Non-functional constraints (performance, reliability, safety, compliance, cost)
6. Integration and external interfaces
7. Data model and lifecycle expectations
8. Operational expectations (deployment, observability, support)
9. Risks, assumptions, unknowns
10. Delivery phases and acceptance criteria

### Step 3 - Focus on PAF module decomposition

Convert high-level goals into candidate PAF modules.

For each major capability, define:
- Proposed module name (PascalCase class, snake_case address)
- Responsibility (single clear concern)
- Inbound commands/messages
- Outbound messages/requests
- State owned by module
- Dependencies/integrations via Protocol (never direct module-to-module calls)

Group modules into:
- Core runtime modules
- Integration modules (hardware/APIs/files)
- Support modules (logging, health, orchestration)

### Step 4 - Populate PROJECT.md

Update `PROJECT.md` with a clear, structured summary of discovered intent.

Recommended sections:
1. Project Mission
2. Problem Domain
3. Stakeholders and Users
4. Goals and Success Criteria
5. Scope and Non-Goals
6. Functional Requirements
7. Non-Functional Requirements
8. Architecture Intent (PAF)
9. Candidate Module Breakdown
10. Risks, Assumptions, Open Questions
11. Initial Delivery Plan

Requirements for quality:
- Write concrete statements, not vague placeholders
- Preserve user terminology
- Mark unknowns explicitly as open questions
- Keep content implementation-guiding, not marketing-style
- Merge incrementally by default, but refine sections by replacing older conflicting statements when newer user input is clearer or more authoritative

### Step 5 - Populate MEMORY.md (rules only)

If memory updates are enabled, append concise reusable rules to `MEMORY.md`, such as:
- Fixed constraints that should influence future implementation choices
- Strongly stated preferences (technology, safety, architecture boundaries)
- Lessons likely to be reused across tasks

Do not duplicate full requirements in memory; keep memory brief and reusable.

### Step 6 - Confirm and iterate

1. Present a short summary of what was written to `PROJECT.md`.
2. Present any rules added to `MEMORY.md`.
3. Ask whether to run another refinement pass.

## Completion Criteria

All are true:
- Discovery interview executed with explicit continue/finish control each round
- No more than configured max rounds
- `PROJECT.md` updated with project-specific intent and module breakdown
- `MEMORY.md` contains only concise reusable rules (if enabled)
- High-level goals are mapped to concrete candidate PAF modules

## Failure Handling

If blocked by missing user detail:
1. Record unresolved items under open questions in `PROJECT.md`
2. Avoid inventing critical requirements
3. Ask the user for only the minimum missing decisions needed to proceed

If file update conflicts occur:
1. Re-read files
2. Merge with latest content
3. Preserve user-authored content by default
4. Replace older conflicting content when the newer user input clearly supersedes it and improves the overall message

## Example Prompts

- `/paf-init-project`
- `/paf-init-project --max-rounds 12`
- `Initialize this fork by interviewing me and updating PROJECT.md with a PAF module plan.`
- `Run paf-init-project and keep asking until I say finish.`
