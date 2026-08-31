# Coding Agents Setup

Installs, audits, updates, and repairs a consistent coding-agent environment for Codex, GitHub Copilot CLI, Claude Code, Pi, and OpenCode.

## Defaults

- Routes supported clients through the Agent Maestro VS Code proxy.
- Uses `gpt-5.6-sol` with high thinking by default.
- Bundles sanitized Claude Code, Codex, and Pi configuration snapshots under `references/defaults/home/` for new-machine setup.
- Installs the default Pi package set: MCP adapter, web access, and subagents.
- Maps review, exploration, documentation, and triage subagents to suitable GPT-5.6 variants after verifying availability.
- Configures Microsoft Learn MCP and Figma MCP, and manages the `grill-me` skill across agents with `npx skills`.
- Optionally installs ChatGPT and the GitHub Copilot desktop app.
- Optionally enables supported autopilot/YOLO modes after explicit risk confirmation.

## Usage

```text
/coding-agents-setup install --dry-run
/coding-agents-setup install
/coding-agents-setup install --with-apps
/coding-agents-setup install --autopilot
/coding-agents-setup update
/coding-agents-setup update --agents-only
/coding-agents-setup update --skills-only
/coding-agents-setup audit
/coding-agents-setup repair
```

`update` is maintenance-only: it updates existing agent installations and lockfile-managed skills without installing missing agents or adding skills. The included standard-library Python helper safely merges JSON configuration and creates timestamped backups. Codex TOML, native MCP commands, `npx skills`, and subagent manifests remain explicit workflow steps so existing configuration is not overwritten blindly.

The bundled profile omits user-specific paths and generated runtime state. It is a merge reference rather than a set of files to copy wholesale; unrestricted settings remain gated by `--autopilot`.
