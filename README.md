# Claude Code Skills

Personal collection of reusable [Claude Code](https://claude.ai/claude-code) skills.

## Skills

| Skill | Description |
|-------|-------------|
| [review-design](./review-design/) | Interactive design document review against a codebase |
| [review-pr](./review-pr/) | Interactive PR code review with merge-base diff, supports Azure DevOps and GitHub |
| [sync-skills](./sync-skills/) | Sync official and personal Claude Code skills with overlap checks and safe overwrite rules |
| [threat-model](./threat-model/) | Update Microsoft Threat Modeling Tool (.tm7) files with STRIDE analysis |

## Installation

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

## Usage

Once installed, invoke skills as slash commands in Claude Code:

```
/review-design C:\path\to\design-doc.htm --pr develop
/review-pr https://dev.azure.com/org/project/_git/repo/pullrequest/12345
/review-pr https://github.com/owner/repo/pull/42 --post-as "Your Name"
/sync-skills
```

## Adding New Skills

Each skill lives in its own directory with a `SKILL.md` file:

```
skill-name/
  SKILL.md        # Required - frontmatter + instructions
  templates/      # Optional - template files
  examples/       # Optional - example outputs
```

See [Claude Code docs](https://docs.anthropic.com/en/docs/claude-code) for skill authoring details.

## License

[MIT](LICENSE)
