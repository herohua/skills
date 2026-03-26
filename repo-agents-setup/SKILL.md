---
name: repo-agents-setup
description: Generate or update AGENTS.md and CLAUDE.md for a repository. Explores the codebase to understand project structure, conventions, build system, testing, and CI/CD, then produces a comprehensive AGENTS.md organized into Principles & Standards and Processes & Workflow sections. Also creates a CLAUDE.md that points to AGENTS.md. Invoke with /repo-agents-setup [--update]
allowed-tools: Bash, Read, Grep, Glob, Agent, AskUserQuestion, Write, Edit
user-invocable: true
---

# Repo Agents Setup Skill

Generate or update `AGENTS.md` and `CLAUDE.md` for the current repository. These files guide AI coding agents on project conventions, principles, and workflows.

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- `--update`: Update existing AGENTS.md rather than creating from scratch. When updating, read the existing file first and preserve user customizations.
- If no arguments, generate fresh files.

## Pre-Flight Check

Before doing any exploration, check if `AGENTS.md` or `CLAUDE.md` already exist in the repository root. If either file exists and `--update` was NOT passed, use `AskUserQuestion` to ask the user:

> "AGENTS.md (and/or CLAUDE.md) already exists in this repository. Would you like to create a fresh version (overwrites the existing file) or update the existing version (preserves your customizations)?"

Options:
- **Create fresh** — start from scratch, overwrite existing files
- **Update existing** — read the current files, re-explore the codebase, and merge changes while preserving custom sections

If the user chooses "Update existing", follow the same flow as `--update` (see "Updating Existing Files" section below).

## Overview

The goal is to produce two files:

1. **AGENTS.md** — comprehensive guide for AI agents working in the repo, organized into:
   - Project Overview (what it does, service dependencies, key data flows)
   - Repository Structure
   - Principles & Standards (key development patterns, coding conventions, testing guidelines)
   - Processes & Workflow (general rules, development setup, design-first workflow, pre-PR verification, CI/CD, deployment, configuration, testing & debugging)

2. **CLAUDE.md** — a short file that says: `Please follow all guidelines and conventions defined in AGENTS.md.`

## Phase 1: Explore the Repository

Thoroughly explore the codebase to gather information. Use the Agent tool with `subagent_type=Explore` for broad exploration, and direct Glob/Grep/Read for targeted lookups. Gather:

### Project Basics
- What the project does (README, top-level docs)
- Languages and frameworks used
- Runtime/SDK versions (e.g., `global.json`, `.node-version`, `.python-version`, `go.mod`)

### Repository Structure
- Key directories and their purposes
- Solution/workspace files (`.sln`, `package.json`, `Cargo.toml`, `go.mod`, etc.)
- Source vs test vs docs vs infra separation

### Key Development Patterns (Domain-Specific)
**IMPORTANT**: Read the main controllers, services, and entry points to understand core architecture and data flows. Do NOT skip this step -- it captures the domain-specific knowledge that makes the AGENTS.md truly useful.
- Core data flow / processing pipeline (read main controllers and service classes)
- What models, APIs, or external services are called and in what order
- Key architectural patterns (streaming, queuing, chunking, retry, etc.)
- Authentication and authorization approach
- Service dependencies and how they interact
- Configuration management patterns (what config files exist, required sections, secrets handling)
- Debugging and local testing approaches (HTTP files, debug headers, test tools)

### Build System
- How to build the project (MSBuild, npm, cargo, make, etc.)
- Build configuration files and their roles

### Code Style & Conventions
- Linter/formatter configs (`.editorconfig`, `.eslintrc`, `stylecop.json`, `rustfmt.toml`, etc.)
- Existing style guides or coding guidelines in docs
- Naming patterns observed in the codebase (e.g., suffixes like `Service`, `Repository`, `Handler`)
- Field naming conventions (check editorconfig or sample files)

### Testing
- Test frameworks used (xUnit, Jest, pytest, etc.)
- Test directory structure
- Any test configuration files (coverage settings, test runners)
- Whether TDD or test-first is practiced (check docs)
- E2E test requirements and when they must be updated

### CI/CD
- Pipeline definitions (Azure Pipelines, GitHub Actions, etc.)
- What the pipelines do (build, test, deploy, security scanning)
- Code coverage requirements (check coverage config files)
- Branch-to-environment mapping

### Deployment
- How and where the project is deployed
- Infrastructure-as-code files (Bicep, Terraform, CloudFormation, etc.)

### Existing Agent/AI Config
- Check for existing `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`
- If updating (`--update`), read and preserve existing content as baseline

## Phase 1b: Consolidate with Existing AI Config Files

**IMPORTANT**: If existing AI configuration files are found (e.g., `.github/copilot-instructions.md`, `.cursorrules`, `.github/instructions/*.md`), do NOT simply ignore them or create a parallel file:

1. **Read all existing AI config files** thoroughly
2. **Extract all content** from them -- every rule, pattern, convention, and code example
3. **Merge everything into AGENTS.md** as the single source of truth
4. **Ask the user** whether to remove the old files (recommended) or keep them as pointers to AGENTS.md
5. If the old files contain **tool-specific features** (e.g., Copilot's `<instructions>` XML with `applyTo` filters), note these to the user since they may need special handling

If existing style guide documents are found (e.g., coding style markdown files):
- **Link to them** from AGENTS.md rather than duplicating content inline
- If they live in a tool-specific location (e.g., `.github/instructions/`), suggest moving them to a neutral location like `docs/coding-principles/`

## Phase 2: Ask Clarifying Questions

Use `AskUserQuestion` to fill gaps that can't be determined from the codebase:

- **Design principles**: Does the team have specific design principles they follow? (e.g., immutability, composition, specific architectural patterns)
- **Design-first workflow**: Does the team require design specs before coding for significant changes? If so, where should they be stored?
- **PR process**: Any specific requirements before opening a PR? (e.g., must build and test pass locally, specific reviewers)
- **Anything else**: Any conventions or rules not captured in config files?

Do NOT ask about things you can already determine from the codebase (build commands, test frameworks, linter configs, etc.).

## Phase 3: Generate AGENTS.md

Write `AGENTS.md` at the repository root with the following structure. Adapt section content to the actual project -- do not include sections that don't apply.

**IMPORTANT**: Carefully separate content by concern:
- **Principles & Standards** = technical patterns, coding style rules, testing conventions (what the code should look like)
- **Processes & Workflow** = human/team rules, process steps, verification checklists (what developers should do)

Do NOT mix process rules (e.g., "always confirm with maintainer before implementing") into coding convention sections. Process rules belong under Processes & Workflow.

```markdown
# AGENTS.md

## Project Overview
[What the project does, in 2-3 sentences. Include integration points (e.g., PR workflows, chat integrations).]

### Service Dependencies
[External services the project depends on -- databases, AI models, storage, monitoring. Include specific model names/versions if applicable.]

## Repository Structure
[Tree diagram of key directories with inline comments explaining purpose]

---

## Principles & Standards

### Key Development Patterns
[Domain-specific architecture: data flows, processing pipelines, streaming patterns, retry strategies, authentication. Include code examples from the actual codebase.]

### Coding Conventions
[Link to existing style docs if they exist rather than duplicating. Only include conventions inline if no separate doc exists. Use tables for naming conventions.]

### Testing Guidelines
[Test coverage expectations, test organization, test selection guidance. Include E2E test update requirements.]

---

## Processes & Workflow

### General Rules
[Team process rules: confirm before implementing, update docs when changing features, etc.]

### Development
[Prerequisites, build commands, how to run tests]

### Design-First Workflow
[If applicable: write spec first, get human review, then code]

### Pre-PR Verification
[What must pass before opening/updating a PR. Emphasize: do not silently ignore failures, surface errors to the developer.]

### CI/CD
[Pipeline structure, coverage requirements, security scanning]

### Deployment
[How and where the project deploys]

### Configuration
[Config file locations, required sections, secrets handling, environment variable patterns]

### Testing & Debugging
[Local API testing tools, debug headers, extension debugging, test environments]
```

### Writing Guidelines

- Be **concise and specific** -- agents need actionable instructions, not prose
- Use **bold** for key rules that must not be violated
- Include actual **commands** agents can copy-paste (build, test, lint)
- Reference **actual file paths** from the repo (not generic examples)
- Use tables for structured information (naming conventions, environment mappings)
- Match the project's own documentation style (check existing docs for tone, casing, formatting)
- **Link to existing docs** rather than duplicating -- if a repo already has a coding style guide, link to it instead of copying its content into AGENTS.md
- Always include the Pre-PR Verification section with these rules:
  - Must run build and tests before opening/updating a PR
  - Do not silently ignore failures -- surface errors to the developer
  - Do not assume test failures are pre-existing -- report them

## Phase 4: Generate CLAUDE.md

Write `CLAUDE.md` at the repository root:

```
Please follow all guidelines and conventions defined in AGENTS.md.
```

Keep it minimal -- all substance goes in AGENTS.md.

## Phase 5: Present to User

After generating both files, present a summary of what was generated:
- List the sections included in AGENTS.md
- Call out any sections you skipped and why
- Note any existing AI config files that were consolidated and recommend removal
- Ask if they want to adjust anything before committing

## Updating Existing Files (`--update`)

When `--update` is passed:
1. Read the existing `AGENTS.md`
2. Re-explore the codebase for any changes since it was last written
3. Present a diff summary of what would change
4. Use `AskUserQuestion` to confirm before overwriting
5. Preserve any custom sections the user added that aren't auto-generated
