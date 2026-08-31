# Portable Agent Defaults

These files are a sanitized snapshot of a working Windows setup and are the canonical personal defaults for this skill.

| Reference file | Target path |
|---|---|
| `home/.claude/settings.json` | `~/.claude/settings.json` |
| `home/.codex/config.toml` | `~/.codex/config.toml` |
| `home/.pi/agent/models.json` | `~/.pi/agent/models.json` |
| `home/.pi/agent/settings.json` | `~/.pi/agent/settings.json` |

Merge the files into existing configuration; do not replace whole files. Resolve `~` from the current user's home directory and never add a user name or absolute home path to these references.

## Apply Safely

- Rediscover model availability, context windows, and output limits through Agent Maestro before applying model entries.
- Preserve unrelated providers, projects, plugins, packages, MCP servers, agents, and client settings.
- Treat `Powered by Agent Maestro` and `local-proxy` as non-secret placeholders that are valid only while Agent Maestro authentication is disabled. If authentication is enabled, use a secure environment or credential-store reference.
- Install or verify referenced plugins and Pi packages before enabling them.
- Apply unrestricted settings only after the skill's `--autopilot` confirmation:
  - Codex `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`
  - Claude Code `permissions.defaultMode = "auto"`
  - Pi `defaultProjectTrust = "always"`

The Pi subagent provider is `local-proxy`, matching the provider ID in `models.json`. This intentionally corrects a stale `agent-maestro` provider preference from the source machine.

## Intentionally Excluded

The source files also contained generated or machine-local state that is invalid on another machine:

- Claude Code's Herdr hook command because it referenced a separate local script by absolute path.
- Codex notification executables, trusted project paths, bundled marketplace paths, generated Node/CUA MCP runtimes, pipe IDs, runtime hashes, hook hashes, and model-availability UI state.
- Pi's `lastChangelogVersion`, which is application state rather than a preference.

Let each client recreate generated runtime entries. Add the Herdr hook separately only after installing its script at a known path.
