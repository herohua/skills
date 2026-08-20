---
name: coding-agents-setup
description: Install, configure, update, audit, or repair coding-agent tools on a developer machine. Use for Codex CLI, GitHub Copilot CLI, Claude Code, Pi, OpenCode, Agent Maestro proxy routing, shared MCP servers, shared agent skills, subagent model mappings, and opt-in autopilot or YOLO modes.
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion, Write, Edit
user-invocable: true
---

# Coding Agents Setup

Set up and maintain a consistent personal coding-agent environment. Support Windows first, then macOS and Linux where the same package managers and paths apply.

Read [references/configuration.md](references/configuration.md) before changing configuration. Use [scripts/setup_coding_agents.py](scripts/setup_coding_agents.py) to generate or apply deterministic configuration.

## Defaults

- CLIs: Codex, GitHub Copilot, Claude Code, Pi, and OpenCode.
- VS Code extensions: Agent Maestro and GitHub Copilot.
- Primary model: `gpt-5.6-sol` with `high` reasoning/thinking.
- Proxy: Agent Maestro at `http://127.0.0.1:23333`.
- Shared MCP servers: Microsoft Learn and Figma.
- Shared skill: `grill-me` from `robmitt/grill-me-skill`, managed with the Vercel `skills` CLI via `npx skills`.
- Optional desktop apps: ChatGPT and GitHub Copilot app.
- Optional autonomy: use each client's supported autopilot/YOLO mode. Treat it as an explicit, high-risk opt-in; never silently enable it.

Model names exposed by the VS Code Language Model API vary by account and extension version. Verify `gpt-5.6-sol` is available before making it the default. If unavailable, ask the user to choose from discovered models; do not silently substitute another model.

## Arguments

Interpret `$ARGUMENTS` as intent plus optional switches:

- `install`, `update`, `repair`, or `audit` (default: `install`).
  - `update` is maintenance-only: update already installed agents, agent packages/extensions, and managed skills. Do not install missing agents, MCP servers, desktop apps, or new skills.
  - `repair` may reinstall missing/broken configured components after confirmation.
- `--agents-only`: update installed agent CLIs/extensions and skip skills.
- `--skills-only`: update installed skills and skip agent CLIs/extensions. Mutually exclusive with `--agents-only`.
- `--dry-run`: generate a plan and configuration without changing the machine.
- `--with-apps`: install the optional ChatGPT and GitHub Copilot desktop apps.
- `--autopilot`: enable supported unrestricted/autopilot modes after the risk confirmation.
- `--no-proxy`: keep each CLI's native provider rather than Agent Maestro. Do not run the proxy configuration helper in this mode.
- `--model <id>` and `--thinking <level>`: override `gpt-5.6-sol` and `high`.
- `--proxy-port <port>`: override `23333`.

Reject unknown switches instead of guessing. Reject install-only switches such as `--with-apps` when the intent is `update`.

## Phase 1: Inventory and Confirm

1. Detect the OS, shell, architecture, package managers, Node.js, npm, Git, GitHub CLI, VS Code CLI, and WinGet/Homebrew.
2. Detect each executable's version, resolved path, and installation owner. Distinguish native/standalone, WinGet/Store, npm, and app-bundled installs; installing the same CLI through a second manager can create PATH shadowing and split update state.
3. Run native health/update checks when supported: `codex doctor`, `claude doctor`, `pi list`, `copilot --version`, and `npx skills list --global --json`. Do not treat every doctor warning as fatal; Agent Maestro lacks an OpenAI `GET /v1/models` route, so Codex reachability checks may report a 404 even when Responses requests work.
4. Read existing files before planning changes. At minimum inspect:
   - `~/.codex/config.toml` and `~/.codex/agents/`
   - `~/.claude/settings.json`, `~/.claude/agents/`, and `~/.claude.json`
   - `~/.copilot/settings.json`, managed `config.json` (JSONC), and `mcp-config.json`
   - `~/.pi/agent/settings.json`, `models.json`, `mcp.json`, `agents/`, and installed extension schemas
   - `~/.config/opencode/opencode.json` and `agents/`
   - `~/.config/mcp/mcp.json` and agent-specific skill directories reported by `npx skills list --global`
5. Check `http://127.0.0.1:<port>/openapi.json` and `/api/v1/info`. If unavailable, ask the user to open VS Code, install/enable Agent Maestro, and run **Agent Maestro: Start API Server**.
6. Discover models from `GET /api/v1/lm/chatModels`, not only `/api/anthropic/v1/models` (the latter can legitimately return an empty list). Match by model ID and record `vendor`, `family`, image/tool capabilities, and `maxInputTokens`. Duplicate IDs can be exposed by both `copilot` and `copilotcli`; preserve which entry supplied the limits.
7. Verify the requested model through Agent Maestro/VS Code. Prefer Agent Maestro's one-click Codex and Claude configuration commands when available because they record exact context-window metadata and Claude's required `[1m]` suffix.
8. Show a concise plan: package installs/upgrades, files to merge, backups, authentication steps, optional app installs, and unsupported settings.
9. Ask before overwriting an existing provider/default-model choice.
10. If `--autopilot` was requested, separately warn that unrestricted agents can execute commands, modify/delete files, access credentials, and make network requests. Require an explicit confirmation and recommend a VM/container or disposable worktree.

For an audit, stop after reporting drift unless the user asks to repair it.

## Update-Only Workflow

When intent is `update`:

1. Inventory installation ownership and versions first.
2. Build the target set from components that are already installed. A missing executable, extension, MCP server, app, or skill is `not installed`; do not add it.
3. If neither filter is supplied, update both installed agents and installed skills. Honor `--agents-only` and `--skills-only`.
4. For agents, update through the detected owner:
   - standalone Codex: `codex update`
   - self-managed Copilot CLI: `copilot update stable`
   - native Claude Code: `claude update`
   - Pi: `pi update --all`
   - npm-managed OpenCode: `npm update --global opencode-ai`
   - VS Code extensions: update through VS Code's extension manager; do not reinstall absent extensions
   - other detected managers: use that manager's update operation rather than migrating channels
5. For skills, run `npx skills list --global --json`, review the lock/source inventory, then `npx skills update --global`. This updates only lockfile-managed installed skills and must not run `skills add`, `--all`, discovery, or installation commands.
6. After updates, re-run versions, health checks, `npx skills list --global --json`, Agent Maestro model discovery, and Pi extension-path checks. Client updates can change schemas or bundled extension paths.
7. Do not rewrite model, MCP, autonomy, subagent, or default-provider configuration merely because an update is available. If an update broke compatibility, report drift and switch to `repair` only with confirmation.
8. Report `updated`, `already current`, `failed`, `skipped by filter`, and `not installed` separately.

## Phase 2: Install or Update Tools

Prefer each tool's existing official installation channel. Do not pipe remote scripts into a shell when an official native, npm, WinGet, or Homebrew package is available. Do not migrate installation channels during routine maintenance without confirmation.

| Tool | Preferred fresh install | Update an existing install |
|---|---|---|
| Codex | Official standalone/Codex app on Windows; otherwise official package | `codex update` for standalone; use its detected package manager otherwise |
| Copilot CLI | WinGet on Windows or official package for the platform | `copilot update stable` for its self-managed install |
| Claude Code | Native installer | `claude update` |
| Pi | `npm install --global --ignore-scripts @earendil-works/pi-coding-agent` | `pi update --all` (self plus packages) |
| OpenCode | `npm install --global opencode-ai` when no native package exists | detected package manager |

Require Node.js 22.19 or newer only for npm-based installs and `npx skills`; native Codex, Copilot, and Claude installs do not need to be replaced merely because they are not in global npm. Before installing, compare `command -v`/`where.exe`, package-manager inventory, and tool doctor output to avoid duplicate binaries.

Install VS Code extensions when `code` is available and the user wants VS Code Copilot itself. Agent Maestro can also receive models from other registered VS Code LM providers (for example Copilot CLI), so a missing `GitHub.copilot` extension is not by itself a proxy failure:

```bash
code --install-extension Joouis.agent-maestro
code --install-extension GitHub.copilot
```

For optional Windows apps, resolve the current Microsoft Store IDs before installation and show them to the user. Do not rely on a fixed ChatGPT ID: current Store/MSIX inventory may display the OpenAI Codex app under a `ChatGPT` label or package family. Inspect both `winget list` and MSIX package identity before deciding an app is missing. The GitHub Copilot app has used Store ID `XPDCK2L0R6V76J`, but verify it at runtime.

```powershell
winget search --source msstore ChatGPT
winget search --source msstore "GitHub Copilot"
winget install --exact --source msstore --id <verified-id> --accept-source-agreements --accept-package-agreements
```

If an install fails, surface the exact command and error. Continue only with independent items after telling the user what will be skipped.

## Phase 3: Configure Agent Maestro

Use loopback, not `0.0.0.0`, for clients. Default endpoints:

| Protocol | Base URL |
|---|---|
| OpenAI | `http://127.0.0.1:23333/api/openai/v1` |
| Anthropic | `http://127.0.0.1:23333/api/anthropic` |
| Gemini | `http://127.0.0.1:23333/api/gemini` |

Agent Maestro authentication is disabled by default. If the user enabled an LLM API key in the extension, obtain it interactively and store only environment-variable references or the client's secure credential store. Never write a provided secret into this repository or print it.

When VS Code is interactive, ask the user to run:

1. **Agent Maestro: Configure Codex Settings** and select the requested model.
2. **Agent Maestro: Configure Claude Code Settings** and select the requested model.

Then merge the remaining settings from the generated plan. If one-click commands are unavailable, use the templates in the reference and script.

For Copilot CLI, inspect `copilot help providers`. Current versions can route through Agent Maestro using `COPILOT_PROVIDER_BASE_URL=http://127.0.0.1:<port>/api/openai/v1`, `COPILOT_PROVIDER_TYPE=openai`, `COPILOT_PROVIDER_WIRE_API=responses`, `COPILOT_MODEL=<model>`, and discovered prompt/output limits. Configure these in the user's shell environment or a private launcher, not in repository files. Use the Agent Maestro API key only through `COPILOT_PROVIDER_BEARER_TOKEN` when proxy authentication is enabled.

## Phase 4: Configure Models and Subagents

Use the primary model for the main coding agent and map specialized subagents deliberately:

| Role | Preferred model | Thinking | Access |
|---|---|---|---|
| primary/implementer | `gpt-5.6-sol` | high | workspace write |
| reviewer/security | `gpt-5.6-sol` | high | read-only |
| explorer/code mapper | `gpt-5.6-terra` | medium | read-only |
| docs researcher | `gpt-5.6-luna` | medium | read-only + MCP |
| quick/triage | `gpt-5.6-luna` | low | read-only |

Before writing mappings, verify every model exists through Agent Maestro. If only the primary model exists, map all roles to it rather than creating broken entries. If a role-specific model is missing, ask before falling back.

Configure native subagents where supported:

- Codex: `[agents]` defaults plus `~/.codex/agents/*.toml`.
- Claude Code: `~/.claude/agents/*.md`, using the proxy model ID and role-appropriate `effort`.
- OpenCode: global `agent` entries with `mode`, `model`, `reasoningEffort`, and permissions.
- Copilot CLI: inspect `copilot help providers`. Current versions support Agent Maestro through BYOK environment variables. Custom agents may use `--agent`; if per-agent model selection is unavailable, document that subagents inherit the selected session model.
- Pi: Pi has no built-in generic subagent manifest, but its bundled example subagent extension uses `~/.pi/agent/agents/*.md`. If that extension is detected, read its installed `README.md`/`agents.ts`, install user-level agent definitions, and use model selectors in the form `provider/model:thinking` (for example `agent-maestro/gpt-5.6-terra:high`, or the preserved provider ID on an existing setup). Map `worker`→Sol/high, `planner` and `reviewer`→Terra/high, and `scout`→Luna/low. Ensure the configured extension and prompt paths still exist after Pi updates. Do not invent a mapping for a different extension.

## Phase 5: Install Shared MCP Servers and Skills

Create or merge the tool-agnostic global MCP file at `~/.config/mcp/mcp.json`.

Manage skills with the Vercel `skills` CLI through `npx skills`; do not manually copy, symlink, update, or remove managed skills. Use the CLI's canonical install plus per-agent links so one update reaches every supported client. Pin the npm package version in automation when reproducibility is required.

Default MCP endpoints:

```json
{
  "mcpServers": {
    "microsoft-learn": {
      "type": "http",
      "url": "https://learn.microsoft.com/api/mcp"
    },
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

Pi needs `pi-mcp-adapter` to consume shared MCP config:

```bash
pi install npm:pi-mcp-adapter
```

For `install` or confirmed `repair`, review `grill-me` before installing, then use `npx skills` globally for all five CLIs. Never run this add command during `update`:

```bash
npx skills add robmitt/grill-me-skill --skill grill-me --global --agent claude-code --agent codex --agent github-copilot --agent pi --agent opencode --yes
npx skills list --global
```

If the CLI does not recognize `github-copilot`, inspect `npx skills add --help` for the current agent identifier instead of guessing.

For a targeted maintenance request, use `npx skills update --global grill-me`; for normal update-only maintenance, use `npx skills update --global` to update every already installed, lockfile-managed skill. Use `npx skills remove --global grill-me` only for explicit removal. Use `--json` for machine-readable audits. Never use `skills add` during update, never use `add --all` for an unreviewed repository, and never execute code from an unreviewed skill.

Also register the MCP servers through native commands/config where shared config is not automatically consumed. Before running an add command, list existing servers and skip an identical entry; update or remove a conflicting same-name entry only with confirmation:

```bash
codex mcp add microsoft-learn --url https://learn.microsoft.com/api/mcp
codex mcp add figma --url https://mcp.figma.com/mcp
claude mcp add --scope user --transport http microsoft-learn https://learn.microsoft.com/api/mcp
claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp
copilot mcp add --transport http microsoft-learn https://learn.microsoft.com/api/mcp
copilot mcp add --transport http figma https://mcp.figma.com/mcp
```

For OpenCode, merge both as remote MCP entries. Figma requires browser OAuth on first use. Microsoft Learn does not require authentication. Prefer the official Claude plugins when requested: `microsoftdocs/mcp` for Microsoft Learn and `figma@claude-plugins-official` for Figma.

## Phase 6: Optional Autonomy

Only perform this phase after the separate confirmation.

- Codex: set `approval_policy = "never"` and `sandbox_mode = "danger-full-access"` only when the installed version supports them.
- Claude Code: set user-level `permissions.defaultMode` to `auto` when the user wants guarded autopilot. Use `bypassPermissions` only if explicitly requested, not merely from `--autopilot`; require a second confirmation for bypass and do not disable managed safety policy.
- Copilot CLI: prefer its current native flags: `copilot --autopilot` for continued autonomous work, optionally bounded with `--max-autopilot-continues`; `--allow-all`/`--yolo` controls permissions, and `--no-ask-user` prevents questions. Do not create a permanent unrestricted alias.
- OpenCode: it already allows operations by default; set explicit `permission` values to `allow` only to make the intent auditable.
- Pi: built-in file and shell tools have no approval layer. Set `defaultProjectTrust: "always"` only when requested; this controls loading project configuration and is not a sandbox bypass.

Do not claim full autonomy where a client, organization policy, OAuth prompt, OS permission, or MCP tool still requires interaction.

## Phase 7: Apply Safely

1. Run the helper with `--dry-run` first.
2. Back up every changed file beside the original using a UTC timestamp.
3. Merge owned keys; preserve unknown keys and unrelated providers, agents, MCP servers, skills, and permissions.
4. Write atomically through a temporary file and rename.
5. Do not modify repository-scoped configuration unless explicitly requested.
6. Keep secrets out of logs, diffs, shell history, and generated reports.

Example:

```bash
python coding-agents-setup/scripts/setup_coding_agents.py --dry-run
python coding-agents-setup/scripts/setup_coding_agents.py --apply --context-window <verified-value> --max-tokens <verified-value>
```

Pass `--model`, `--thinking`, and `--proxy-port` through when overridden. `--apply` requires the context and output limits discovered for the selected model. If dry-run shows an existing default provider/model replacement and the user confirms it, add `--confirm-default-change`. If Agent Maestro authentication is enabled, set the secret in the current environment and pass only its name with `--api-key-env`; never place its value on the command line.

The helper intentionally does not write autonomy, MCP registration, or role-specific fallback models. Apply those interactively after model discovery and confirmations.

## Phase 8: Verify and Report

Verify:

- All five CLI version commands succeed.
- Agent Maestro responds on loopback and the selected model is available.
- Each client reports the requested default model and high thinking/reasoning. For Claude, a roughly 1M model should use `gpt-5.6-sol[1m]`; for Pi, confirm `thinkingLevelMap` and the actual `provider/model:thinking` subagent selectors.
- A harmless POST prompt succeeds through the proxy for each configurable CLI. Do not fail solely because `codex doctor` probes an unsupported Agent Maestro route and reports 404.
- Microsoft Learn MCP can search docs.
- Figma is configured; report `authentication pending` until OAuth completes.
- `npx skills list --global --json` and `~/.agents/.skill-lock.json` show `grill-me`. The CLI may report Codex, GitHub Copilot, and OpenCode as `universal` consumers of the canonical `~/.agents/skills` copy while listing explicit symlinks only for Claude Code and Pi; verify discovery in each client rather than requiring five displayed links.
- Native subagents resolve to existing models and honor read-only/write permissions.
- Autonomy settings match the exact confirmed level.

Report a table with `component`, `version`, `model/provider`, `MCP`, `skills`, `autonomy`, and `status`. Include changed and backup paths. Clearly identify manual follow-up actions and unsupported capabilities.
