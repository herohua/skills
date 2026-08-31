# AI Coding Agent Skills

Personal collection of reusable skills for AI coding agents — designed for [Claude Code](https://claude.ai/claude-code) and compatible with Copilot, Codex, and other agents.

## Skills

| Skill | Description |
|-------|-------------|
| [bug-report](./bug-report/) | Refresh an ADO bug report dashboard with summary tiles, charts, and categorized bug tables |
| [code-coverage-policy](./code-coverage-policy/) | Check and update Azure DevOps branch policies for code coverage |
| [coding-agents-setup](./coding-agents-setup/) | Install and maintain coding-agent CLIs, portable default profiles, Agent Maestro proxy models, subagents, MCP servers, skills, and optional autopilot modes |
| [repo-agents-setup](./repo-agents-setup/) | Generate or update AGENTS.md and CLAUDE.md for a repository |
| [review-design](./review-design/) | Interactive design document review against a codebase |
| [review-pr](./review-pr/) | Interactive PR code review with merge-base diff, supports Azure DevOps and GitHub |
| [self-review](./self-review/) | Automated self-review loop: spawns a read-only reviewer, triages findings, fixes issues, iterates until clean |
| [sync-skills](./sync-skills/) | Sync official and personal Claude Code skills with overlap checks and safe overwrite rules |
| [threat-model](./threat-model/) | Update Microsoft Threat Modeling Tool (.tm7) files with STRIDE analysis |

## Installation

### Claude Code

Copy the skill directories you want into your Claude Code skills folder:

```bash
# Personal (all projects)
cp -r review-design/ ~/.claude/skills/review-design/
cp -r sync-skills/ ~/.claude/skills/sync-skills/

# Project-specific
cp -r review-design/ .claude/skills/review-design/
cp -r sync-skills/ .claude/skills/sync-skills/
```

Or clone the whole repo and symlink:

```bash
git clone https://github.com/herohua/skills.git ~/claude-skills
ln -s ~/claude-skills/review-design ~/.claude/skills/review-design
```

### Other Agents

Each skill's `SKILL.md` contains the full workflow specification. Point your agent at the relevant `SKILL.md` file — the instructions are agent-agnostic.

## Usage

Once installed, invoke skills as slash commands in Claude Code:

```
/bug-report refresh
/code-coverage-policy check --repo my-repo
/coding-agents-setup install --dry-run
/coding-agents-setup install --with-apps --autopilot
/coding-agents-setup update
/coding-agents-setup update --skills-only
/repo-agents-setup
/review-design C:\path\to\design-doc.htm --pr develop
/review-pr https://dev.azure.com/org/project/_git/repo/pullrequest/12345
/review-pr https://github.com/owner/repo/pull/42 --post-as "Your Name"
/self-review
/self-review D:\path\to\repo --max-rounds 5
/sync-skills
/threat-model C:\path\to\model.tm7
```

For other agents, follow the invocation pattern described in each skill's `SKILL.md`.

## Adding New Skills

Each skill lives in its own directory with a `SKILL.md` file:

```
skill-name/
  SKILL.md        # Required - frontmatter + instructions
  references/     # Optional - API docs, format specs
  scripts/        # Optional - supporting scripts
```

See [Claude Code docs](https://docs.anthropic.com/en/docs/claude-code) for skill authoring details.

## License

[MIT](LICENSE)
