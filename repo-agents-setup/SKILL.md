---
name: repo-agents-setup
description: Generate or update AGENTS.md and CLAUDE.md for a repository. Explores the codebase to understand project structure, conventions, build system, testing, and CI/CD, then produces a comprehensive AGENTS.md organized into Principles & Standards and Processes & Workflow sections. Also creates a CLAUDE.md that points to AGENTS.md. Invoke with /repo-agents-setup [--update]
allowed-tools: Bash, Read, Grep, Glob, Agent, AskUserQuestion, Write, Edit
---

# Repo Agents Setup Skill

Generate or update `AGENTS.md` and `CLAUDE.md` for the current repository. These files guide AI coding agents on project conventions, principles, and workflows.

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- `--update`: Update existing AGENTS.md rather than creating from scratch. When updating, read the existing file first and preserve user customizations.
- If no arguments, generate fresh files.

## Overview

The goal is to produce two files:

1. **AGENTS.md** — comprehensive guide for AI agents working in the repo, organized into:
   - Project Overview
   - Repository Structure
   - Principles & Standards (design principles, coding conventions, testing guidelines)
   - Processes & Workflow (development setup, design-first workflow, pre-PR verification, CI/CD, deployment)

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

## Phase 2: Ask Clarifying Questions

Use `AskUserQuestion` to fill gaps that can't be determined from the codebase:

- **Design principles**: Does the team have specific design principles they follow? (e.g., immutability, composition, specific architectural patterns)
- **Design-first workflow**: Does the team require design specs before coding for significant changes? If so, where should they be stored?
- **PR process**: Any specific requirements before opening a PR? (e.g., must build and test pass locally, specific reviewers)
- **Anything else**: Any conventions or rules not captured in config files?

Do NOT ask about things you can already determine from the codebase (build commands, test frameworks, linter configs, etc.).

## Phase 3: Generate AGENTS.md

Write `AGENTS.md` at the repository root with the following structure. Adapt section content to the actual project -- do not include sections that don't apply.

```markdown
# AGENTS.md

## Project Overview
[What the project does, in 2-3 sentences]

## Repository Structure
[Tree diagram of key directories with inline comments explaining purpose]

---

## Principles & Standards

### Design Principles
[Project's core design principles -- only include if the team has explicit ones]

### Coding Conventions
[Style rules, naming conventions, field naming, from linter configs and docs]

### Testing Guidelines
[Test coverage expectations, TDD practices, test organization, test selection guidance]

---

## Processes & Workflow

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
```

### Writing Guidelines

- Be **concise and specific** -- agents need actionable instructions, not prose
- Use **bold** for key rules that must not be violated
- Include actual **commands** agents can copy-paste (build, test, lint)
- Reference **actual file paths** from the repo (not generic examples)
- Use tables for structured information (naming conventions, environment mappings)
- Match the project's own documentation style (check existing docs for tone, casing, formatting)
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
- Ask if they want to adjust anything before committing

## Updating Existing Files (`--update`)

When `--update` is passed:
1. Read the existing `AGENTS.md`
2. Re-explore the codebase for any changes since it was last written
3. Present a diff summary of what would change
4. Use `AskUserQuestion` to confirm before overwriting
5. Preserve any custom sections the user added that aren't auto-generated
