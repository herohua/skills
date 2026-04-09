# AGENTS.md

## Project Overview

A collection of reusable AI coding agent skills that provide tools for code review, design review, threat modeling, CI/CD management, bug tracking, and repository setup. Skills are designed for Claude Code but can also be used with Copilot, Codex, or other AI coding agents. They are distributed as self-contained directories and installed by copying or symlinking into the agent's skills directory.

## Repository Structure

```
herohua-skills/
├── README.md                         # Installation & usage guide
├── LICENSE                           # MIT License
├── .gitignore
│
└── <skill-name>/                     # Each top-level directory is a skill
    ├── SKILL.md                      # Required: skill definition & workflow
    ├── README.md                     # Optional: quick-reference summary
    ├── references/                   # Optional: API docs, format specs, troubleshooting
    └── scripts/                      # Optional: supporting scripts (.py, .ps1, .js, ...)
```

Current skills: `bug-report`, `code-coverage-policy`, `repo-agents-setup`, `review-design`, `review-pr`, `self-review`, `sync-skills`, `threat-model`.

---

## Principles & Standards

### Skill Structure

Every skill **must** contain a `SKILL.md` file at the skill directory root with YAML-style frontmatter defining:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier (kebab-case, matches directory name) |
| `description` | Yes | What the skill does and when to trigger it |
| `allowed-tools` | Yes | Which Claude Code tools the skill can invoke |
| `user-invocable` | Yes | Whether the skill can be called as a slash command |

Additional files (Python scripts, reference docs, config templates) are placed alongside `SKILL.md` in the same directory or in a `references/` subdirectory.

### Design Guidance

- **Build upon existing skills, MCPs, or tools** — before creating new functionality, check if an existing skill, MCP server, or Claude Code tool already provides what you need, and compose on top of it

### Coding Conventions

- **Skill directory names**: kebab-case (e.g., `review-pr`, `code-coverage-policy`)
- **Python files**: snake_case (e.g., `generate_report.py`, `tm7_builders.py`)
- **Python**: Standard library only — no external dependencies requiring `pip install`
- **Markdown**: Consistent heading hierarchy (H1 for title, H2/H3 for sections), code blocks with language identifiers
- **Reference docs**: Place API references, format specs, and troubleshooting guides in a `references/` subdirectory

### Documentation

- Each skill **can** include a `README.md` with a quick-reference summary
- `SKILL.md` should contain the full workflow specification: phases, steps, tool usage patterns, and examples
- Reference files should be self-contained and usable by agents without additional context

---

## Processes & Workflow

### Development

**Prerequisites:**
- Python 3.x (standard library only)
- Azure CLI with `azure-devops` extension (for ADO-related skills)
- GitHub CLI (`gh`) (for GitHub-related skills)
- Bash-compatible shell

**Adding a new skill:**
1. Create a new directory with a kebab-case name at the repository root
2. Add a `SKILL.md` with required frontmatter and workflow definition
3. Add supporting files (scripts, references) as needed
4. Update the root `README.md` to list the new skill

**Local development must use Git worktrees.** Multiple agents may work in the same repository concurrently, so always create a worktree before making changes to avoid conflicts:

```bash
git worktree add .claude/worktrees/<branch-name> -b <branch-name>
```

**Testing a skill locally:**
- Symlink the skill directory into `~/.claude/skills/` or a project's `.claude/skills/`
- Invoke via its slash command in Claude Code to verify behavior

### Pre-PR Verification

Before opening or updating a PR:

- **Verify SKILL.md frontmatter** is complete (name, description, allowed-tools, user-invocable)
- **Verify Python scripts** run without errors using only the standard library
- **Verify Markdown** renders correctly (check heading levels, code blocks, tables)
- **Keep AGENTS.md and README.md up to date** — when adding or changing skills, update both files to reflect the changes
- **Scrub personal information** — ensure no personal data (names, emails, API keys, tokens, internal URLs) is included in committed files
- **Do not silently ignore failures** — surface any errors to the developer
- **Do not assume issues are pre-existing** — investigate and report them

### PR Process

- Each PR should contain changes for **one feature or fix only** — do not mix unrelated changes together
- Use branch naming convention `<skill-name>/<feature>` (e.g., `threat-model/add-stride-analysis`)
- PRs require at least one approval before merging
- Target the `main` branch for all changes
- Use descriptive commit messages that explain the change

### Deployment

Skills are deployed by end users via copy or symlink:

```bash
# Personal installation (available in all projects)
ln -s /path/to/herohua-skills/review-pr ~/.claude/skills/review-pr

# Project-specific installation
ln -s /path/to/herohua-skills/review-pr .claude/skills/review-pr
```

No CI/CD pipelines or server-side deployment — skills run locally within Claude Code.
