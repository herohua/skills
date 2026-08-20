# Configuration Reference

Use these templates as a compatibility baseline. Client schemas change; inspect installed help/schema and preserve existing values before applying them.

## Agent Maestro

Default proxy endpoints:

| API | URL |
|---|---|
| OpenAI Responses/Chat | `http://127.0.0.1:23333/api/openai/v1` |
| Anthropic Messages | `http://127.0.0.1:23333/api/anthropic` |
| Gemini | `http://127.0.0.1:23333/api/gemini` |
| OpenAPI | `http://127.0.0.1:23333/openapi.json` |

Agent Maestro's VS Code commands are preferred for Codex and Claude Code because they discover VS Code models and context limits. Discover models from `GET /api/v1/lm/chatModels`; `/api/anthropic/v1/models` may be empty even while requests work. Roughly 1M models (800K–1.5M input tokens) need Claude's `[1m]` suffix. Authentication is disabled by default. If enabled, use an environment variable such as `AGENT_MAESTRO_API_KEY`; never commit the key.

## Codex

Merge into `~/.codex/config.toml`:

```toml
model = "gpt-5.6-sol"
model_provider = "agent-maestro"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[model_providers.agent-maestro]
name = "Agent Maestro"
base_url = "http://127.0.0.1:23333/api/openai/v1"
wire_api = "responses"

[agents]
default_subagent_model = "gpt-5.6-sol"
default_subagent_reasoning_effort = "high"
max_concurrent_threads_per_session = 6
```

Autopilot changes only:

```toml
approval_policy = "never"
sandbox_mode = "danger-full-access"
```

Role files belong in `~/.codex/agents/`. Example reviewer:

```toml
name = "reviewer"
description = "Read-only reviewer focused on correctness, security, and missing tests."
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Review like an owner. Lead with concrete findings and cite files and symbols.
Do not modify files.
"""
```

## Claude Code

Merge into `~/.claude/settings.json`. Agent Maestro's one-click command also supplies context-window settings based on model metadata.

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "gpt-5.6-sol[1m]",
  "effortLevel": "high",
  "alwaysThinkingEnabled": true,
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:23333/api/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "Powered by Agent Maestro",
    "ANTHROPIC_MODEL": "gpt-5.6-sol[1m]",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ATTRIBUTION_HEADER": "0"
  },
  "permissions": {
    "defaultMode": "auto"
  }
}
```

If Agent Maestro API-key authentication is enabled, do not use the placeholder token. Supply the actual token through a secure helper/environment mechanism supported by Claude Code. Preserve the one-click command's `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`; locally, Sol reported `921793` and selected `[1m]`, but always rediscover these values.

Subagents belong in `~/.claude/agents/*.md`. Example:

```markdown
---
name: reviewer
description: Review correctness, security, regressions, and tests without editing.
model: gpt-5.6-sol
effort: high
permissionMode: plan
---

Review like an owner. Lead with concrete findings and cite files and symbols.
```

`permissionMode: bypassPermissions` is not a substitute for the user's main-session choice and can be blocked by managed policy.

## Pi

Install MCP support:

```bash
pi install npm:pi-mcp-adapter
```

Merge into `~/.pi/agent/models.json`:

```json
{
  "providers": {
    "agent-maestro": {
      "baseUrl": "http://127.0.0.1:23333/api/openai/v1",
      "api": "openai-completions",
      "apiKey": "agent-maestro-local",
      "compat": {
        "supportsDeveloperRole": true,
        "supportsReasoningEffort": true,
        "supportsUsageInStreaming": true,
        "supportsStrictMode": true
      },
      "models": [
        {
          "id": "gpt-5.6-sol",
          "name": "GPT-5.6 Sol via Agent Maestro",
          "reasoning": true,
          "input": ["text", "image"],
          "contextWindow": 921793,
          "maxTokens": 128000,
          "thinkingLevelMap": {
            "off": "none",
            "minimal": null,
            "low": "low",
            "medium": "medium",
            "high": "high",
            "xhigh": "xhigh",
            "max": "max"
          }
        },
        {
          "id": "gpt-5.6-terra",
          "name": "GPT-5.6 Terra via Agent Maestro",
          "reasoning": true,
          "input": ["text", "image"],
          "contextWindow": 921793,
          "maxTokens": 128000,
          "thinkingLevelMap": {
            "off": "none",
            "minimal": null,
            "low": "low",
            "medium": "medium",
            "high": "high",
            "xhigh": "xhigh",
            "max": "max"
          }
        },
        {
          "id": "gpt-5.6-luna",
          "name": "GPT-5.6 Luna via Agent Maestro",
          "reasoning": true,
          "input": ["text", "image"],
          "contextWindow": 921793,
          "maxTokens": 128000,
          "thinkingLevelMap": {
            "off": "none",
            "minimal": null,
            "low": "low",
            "medium": "medium",
            "high": "high",
            "xhigh": "xhigh",
            "max": "max"
          }
        }
      ]
    }
  }
}
```

Do not trust the illustrative context/output limits when Agent Maestro reports different metadata. Replace them with discovered values. The local proxy is known to work with Pi's `openai-completions` API and explicit compatibility flags; when repairing an existing provider, preserve its working name/API instead of renaming it or changing wire protocols.

Merge into `~/.pi/agent/settings.json`:

```json
{
  "defaultProvider": "agent-maestro",
  "defaultModel": "gpt-5.6-sol",
  "defaultThinkingLevel": "high",
  "defaultProjectTrust": "ask"
}
```

`defaultProjectTrust: "always"` is an opt-in convenience setting, not a tool sandbox or permission mode. Pi's bundled example subagent extension uses `~/.pi/agent/agents/*.md` with `model: provider/model:thinking`.

| Agent | Model selector |
|---|---|
| `worker` | `<proxy-provider>/gpt-5.6-sol:high` |
| `planner` | `<proxy-provider>/gpt-5.6-terra:high` |
| `reviewer` | `<proxy-provider>/gpt-5.6-terra:high` |
| `scout` | `<proxy-provider>/gpt-5.6-luna:low` |

Replace `<proxy-provider>` with the effective Pi provider ID (`agent-maestro` on a fresh setup; preserve an existing working ID such as `local-proxy`). Read the installed extension schema before applying this mapping to a different subagent extension.

## OpenCode

Global path: `~/.config/opencode/opencode.json`. OpenCode's provider/model shape evolves, so validate the installed schema. A custom OpenAI-compatible provider commonly resembles:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "agent-maestro/gpt-5.6-sol",
  "small_model": "agent-maestro/gpt-5.6-luna",
  "provider": {
    "agent-maestro": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Agent Maestro",
      "options": {
        "baseURL": "http://127.0.0.1:23333/api/openai/v1",
        "apiKey": "agent-maestro-local"
      },
      "models": {
        "gpt-5.6-sol": { "name": "GPT-5.6 Sol" },
        "gpt-5.6-terra": { "name": "GPT-5.6 Terra" },
        "gpt-5.6-luna": { "name": "GPT-5.6 Luna" }
      }
    }
  },
  "agent": {
    "build": {
      "mode": "primary",
      "model": "agent-maestro/gpt-5.6-sol",
      "reasoningEffort": "high"
    },
    "reviewer": {
      "description": "Read-only correctness and security reviewer",
      "mode": "subagent",
      "model": "agent-maestro/gpt-5.6-sol",
      "reasoningEffort": "high",
      "permission": { "edit": "deny", "bash": "deny" }
    },
    "explore": {
      "mode": "subagent",
      "model": "agent-maestro/gpt-5.6-terra",
      "reasoningEffort": "medium",
      "permission": { "edit": "deny", "bash": "deny" }
    },
    "scout": {
      "mode": "subagent",
      "model": "agent-maestro/gpt-5.6-luna",
      "reasoningEffort": "medium",
      "permission": { "edit": "deny", "bash": "deny" }
    }
  },
  "mcp": {
    "microsoft-learn": {
      "type": "remote",
      "url": "https://learn.microsoft.com/api/mcp",
      "enabled": true
    },
    "figma": {
      "type": "remote",
      "url": "https://mcp.figma.com/mcp",
      "enabled": true
    }
  }
}
```

OpenCode permits operations without approval by default. Only add an explicit global `"permission": {"*": "allow"}` entry in the separately confirmed autonomy phase.

## GitHub Copilot CLI

Inspect `copilot help providers`. Current Copilot CLI supports Agent Maestro through BYOK environment variables:

```powershell
$env:COPILOT_PROVIDER_BASE_URL = "http://127.0.0.1:23333/api/openai/v1"
$env:COPILOT_PROVIDER_TYPE = "openai"
$env:COPILOT_PROVIDER_WIRE_API = "responses"
$env:COPILOT_MODEL = "gpt-5.6-sol"
$env:COPILOT_PROVIDER_MAX_PROMPT_TOKENS = "921793"
$env:COPILOT_PROVIDER_MAX_OUTPUT_TOKENS = "128000"
copilot --effort high
```

If Agent Maestro authentication is enabled, set `COPILOT_PROVIDER_BEARER_TOKEN` from secure storage. Prefer a private user-level launcher/environment; do not commit these settings. If the installed version lacks `help providers`, keep GitHub routing and report the proxy exception.

MCP configuration path: `~/.copilot/mcp-config.json`.

```json
{
  "mcpServers": {
    "microsoft-learn": {
      "type": "http",
      "url": "https://learn.microsoft.com/api/mcp",
      "tools": ["*"]
    },
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp",
      "tools": ["*"]
    }
  }
}
```

Current Copilot CLI separates autonomy from permissions:

```bash
copilot --autopilot --max-autopilot-continues 5 --allow-all
```

Add `--no-ask-user` only for unattended runs. `--effort` supports `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, and `max`; preserve existing `~/.copilot/settings.json` choices. Do not create a permanent unrestricted alias.

## Shared MCP and Skills

Preferred MCP file: `~/.config/mcp/mcp.json`.

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

Manage skills with the Vercel `skills` CLI rather than manipulating skill directories directly:

```bash
npx skills add robmitt/grill-me-skill --skill grill-me --global --agent claude-code --agent codex --agent github-copilot --agent pi --agent opencode --yes
npx skills list --global --json
npx skills update --global grill-me
```

The CLI maintains a canonical `~/.agents/skills` copy and creates agent-specific symlinks where needed. Codex, GitHub Copilot, and OpenCode may be reported as universal consumers rather than separate links; Claude Code and Pi commonly receive explicit symlinks. Prefer symlinks; use `--copy` only where unavailable. Review source skills before using `--yes`, and pin the `skills` npm version in unattended automation.

## Sources

- Agent Maestro: <https://github.com/Joouis/agent-maestro>
- Codex configuration and subagents: <https://developers.openai.com/codex/config-reference> and <https://developers.openai.com/codex/subagents>
- Claude Code settings and subagents: <https://docs.anthropic.com/en/docs/claude-code/settings> and <https://docs.anthropic.com/en/docs/claude-code/sub-agents>
- Copilot CLI MCP and permissions: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers> and <https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools>
- OpenCode config and agents: <https://opencode.ai/docs/config/> and <https://opencode.ai/docs/agents/>
- Microsoft Learn MCP: <https://learn.microsoft.com/en-us/training/support/mcp-get-started>
- Figma MCP: <https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/>
- Skills CLI: <https://github.com/vercel-labs/skills>
- Grill Me: <https://github.com/robmitt/grill-me-skill>
