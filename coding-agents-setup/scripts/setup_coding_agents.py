#!/usr/bin/env python3
"""Merge verified coding-agent JSON configuration without external packages."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gpt-5.6-sol"
DEFAULT_PORT = 23333
DEFAULT_THINKING = "high"
VALID_THINKING = {"off", "minimal", "low", "medium", "high", "xhigh", "max"}


def deep_merge(existing: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge desired keys while preserving unrelated existing keys."""
    merged = dict(existing)
    for key, value in desired.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Cannot parse {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")
    return value


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = path.with_name(f"{path.name}.bak.{stamp}")
    counter = 1
    while target.exists():
        target = path.with_name(f"{path.name}.bak.{stamp}.{counter}")
        counter += 1
    shutil.copy2(path, target)
    return target


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def write_merged_json(path: Path, desired: dict[str, Any], apply: bool) -> None:
    existing = load_json(path)
    merged = deep_merge(existing, desired)
    changed = merged != existing
    print(f"{'CHANGE' if changed else 'OK':6} {path}")
    if not changed or not apply:
        return
    saved = backup(path)
    atomic_write(path, json.dumps(merged, indent=2, ensure_ascii=False) + "\n")
    if saved:
        print(f"       backup: {saved}")


def claude_model_id(model: str, context_window: int) -> str:
    """Match Agent Maestro's Claude Code 1M-band suffix behavior."""
    if model.endswith("[1m]") or not 800_000 < context_window < 1_500_000:
        return model
    return f"{model}[1m]"


def claude_settings(
    model: str,
    port: int,
    thinking: str,
    api_key_env: str | None,
    context_window: int,
) -> dict[str, Any]:
    token = f"${{{api_key_env}}}" if api_key_env else "Powered by Agent Maestro"
    selected_model = claude_model_id(model, context_window)
    return {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "model": selected_model,
        "effortLevel": thinking,
        "alwaysThinkingEnabled": thinking != "off",
        "env": {
            "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{port}/api/anthropic",
            "ANTHROPIC_AUTH_TOKEN": token,
            "ANTHROPIC_MODEL": selected_model,
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": str(context_window),
            "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "85",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CODE_ATTRIBUTION_HEADER": "0",
        },
    }


def pi_models(
    provider_id: str,
    model: str,
    port: int,
    api_key_env: str | None,
    context_window: int,
    max_tokens: int,
) -> dict[str, Any]:
    api_key = f"${api_key_env}" if api_key_env else provider_id
    return {
        "providers": {
            provider_id: {
                "baseUrl": f"http://127.0.0.1:{port}/api/openai/v1",
                "api": "openai-completions",
                "apiKey": api_key,
                "compat": {
                    "supportsDeveloperRole": True,
                    "supportsReasoningEffort": True,
                    "supportsUsageInStreaming": True,
                    "supportsStrictMode": True,
                },
                "models": [
                    {
                        "id": model,
                        "name": f"{model} via Agent Maestro",
                        "reasoning": True,
                        "input": ["text", "image"],
                        "contextWindow": context_window,
                        "maxTokens": max_tokens,
                        "thinkingLevelMap": {
                            "off": "none",
                            "minimal": None,
                            "low": "low",
                            "medium": "medium",
                            "high": "high",
                            "xhigh": "xhigh",
                            "max": "max",
                        },
                    }
                ],
            }
        }
    }


def merge_pi_models(
    existing: dict[str, Any], desired: dict[str, Any], provider_id: str
) -> dict[str, Any]:
    """Merge proxy models by id instead of replacing the provider list."""
    merged = deep_merge(existing, desired)
    existing_provider = existing.get("providers", {}).get(provider_id, {})
    desired_provider = desired["providers"][provider_id]
    current_models = existing_provider.get("models", [])
    desired_models = desired_provider["models"]
    if isinstance(current_models, list):
        by_id = {
            entry.get("id"): entry
            for entry in current_models
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        }
        for entry in desired_models:
            by_id[entry["id"]] = entry
        merged["providers"][provider_id]["models"] = list(by_id.values())
    return merged


def detect_pi_provider_id(home: Path, port: int) -> str:
    """Preserve an existing Pi provider already routed to Agent Maestro."""
    settings = load_json(home / ".pi/agent/settings.json")
    models = load_json(home / ".pi/agent/models.json")
    providers = models.get("providers", {})
    matches: list[str] = []
    if isinstance(providers, dict):
        for provider_id, config in providers.items():
            if not isinstance(config, dict):
                continue
            base_url = str(config.get("baseUrl", "")).replace("localhost", "127.0.0.1").rstrip("/")
            if base_url == f"http://127.0.0.1:{port}/api/openai/v1":
                matches.append(provider_id)
    current = settings.get("defaultProvider")
    if current in matches:
        return current
    if len(matches) == 1:
        return matches[0]
    return "local-proxy"


def opencode_settings(
    model: str,
    port: int,
    thinking: str,
    api_key_env: str | None,
) -> dict[str, Any]:
    api_key = f"{{env:{api_key_env}}}" if api_key_env else "agent-maestro-local"
    return {
        "$schema": "https://opencode.ai/config.json",
        "model": f"agent-maestro/{model}",
        "small_model": f"agent-maestro/{model}",
        "provider": {
            "agent-maestro": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Agent Maestro",
                "options": {
                    "baseURL": f"http://127.0.0.1:{port}/api/openai/v1",
                    "apiKey": api_key,
                },
                "models": {model: {"name": model}},
            }
        },
        "agent": {
            "build": {
                "mode": "primary",
                "model": f"agent-maestro/{model}",
                "reasoningEffort": thinking,
            },
            "reviewer": {
                "description": "Read-only correctness and security reviewer",
                "mode": "subagent",
                "model": f"agent-maestro/{model}",
                "reasoningEffort": thinking,
                "permission": {"edit": "deny", "bash": "deny"},
            },
            "explore": {
                "description": "Read-only codebase explorer",
                "mode": "subagent",
                "model": f"agent-maestro/{model}",
                "reasoningEffort": "medium",
                "permission": {"edit": "deny", "bash": "deny"},
            },
            "scout": {
                "description": "Read-only documentation researcher",
                "mode": "subagent",
                "model": f"agent-maestro/{model}",
                "reasoningEffort": "medium",
                "permission": {"edit": "deny", "bash": "deny"},
            },
        },
        "mcp": {
            "microsoft-learn": {
                "type": "remote",
                "url": "https://learn.microsoft.com/api/mcp",
                "enabled": True,
            },
            "figma": {
                "type": "remote",
                "url": "https://mcp.figma.com/mcp",
                "enabled": True,
            },
        },
    }


def ensure_default_choices_confirmed(
    home: Path,
    model: str,
    pi_provider_id: str,
    context_window: int,
    confirmed: bool,
) -> None:
    conflicts: list[str] = []
    checks = [
        (home / ".pi/agent/settings.json", "defaultModel", model),
        (home / ".pi/agent/settings.json", "defaultProvider", pi_provider_id),
        (home / ".config/opencode/opencode.json", "model", f"agent-maestro/{model}"),
        (home / ".claude/settings.json", "model", claude_model_id(model, context_window)),
    ]
    for path, key, desired in checks:
        current = load_json(path).get(key)
        if current not in (None, desired):
            conflicts.append(f"{path}: {key}={current!r} -> {desired!r}")
    if conflicts and not confirmed:
        details = "\n  ".join(conflicts)
        raise RuntimeError(
            "Existing default provider/model choices require confirmation. "
            "Review these changes, then rerun with --confirm-default-change:\n  " + details
        )


def ensure_no_mcp_conflicts(home: Path) -> None:
    expected = {
        "microsoft-learn": "https://learn.microsoft.com/api/mcp",
        "figma": "https://mcp.figma.com/mcp",
    }
    sources = [
        (home / ".config/mcp/mcp.json", "mcpServers"),
        (home / ".copilot/mcp-config.json", "mcpServers"),
        (home / ".config/opencode/opencode.json", "mcp"),
    ]
    for path, key in sources:
        servers = load_json(path).get(key, {})
        if not isinstance(servers, dict):
            continue
        for name, url in expected.items():
            entry = servers.get(name)
            if isinstance(entry, dict):
                entry_url = entry.get("url")
                expected_type = "remote" if key == "mcp" else "http"
                entry_type = entry.get("type")
                same_remote = entry_url == url and entry_type in (None, expected_type)
                if not same_remote:
                    raise RuntimeError(
                        f"Conflicting MCP server {name!r} in {path}; resolve it interactively before applying"
                    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="write changes with backups")
    action.add_argument("--dry-run", action="store_true", help="show planned files (default)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="model already verified through Agent Maestro")
    parser.add_argument("--thinking", default=DEFAULT_THINKING)
    parser.add_argument("--proxy-port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--context-window", type=int, help="verified Agent Maestro model context window")
    parser.add_argument("--max-tokens", type=int, help="verified Agent Maestro model output-token limit")
    parser.add_argument(
        "--confirm-default-change",
        action="store_true",
        help="confirm replacement of default provider/model choices shown during dry-run",
    )
    parser.add_argument(
        "--api-key-env",
        help="name of an existing environment variable containing Agent Maestro's API key",
    )
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not 1 <= args.proxy_port <= 65535:
        parser.error("--proxy-port must be between 1 and 65535")
    if not args.model.strip():
        parser.error("--model cannot be empty")
    if args.thinking not in VALID_THINKING:
        parser.error(f"--thinking must be one of: {', '.join(sorted(VALID_THINKING))}")
    if args.api_key_env and args.api_key_env not in os.environ:
        parser.error(f"--api-key-env names an unset variable: {args.api_key_env}")
    if args.apply and (args.context_window is None or args.max_tokens is None):
        parser.error("--apply requires verified --context-window and --max-tokens values")
    if args.context_window is not None and args.context_window <= 0:
        parser.error("--context-window must be positive")
    if args.max_tokens is not None and args.max_tokens <= 0:
        parser.error("--max-tokens must be positive")

    context_window = args.context_window or 921793
    max_tokens = args.max_tokens or 128000
    home = args.home.expanduser().resolve()
    apply = bool(args.apply)
    print("APPLY mode" if apply else "DRY-RUN mode")

    try:
        pi_provider_id = detect_pi_provider_id(home, args.proxy_port)
        ensure_default_choices_confirmed(
            home,
            args.model,
            pi_provider_id,
            context_window,
            args.confirm_default_change or not apply,
        )
        ensure_no_mcp_conflicts(home)
        targets: list[tuple[Path, dict[str, Any], bool]] = [
            (
                home / ".claude/settings.json",
                claude_settings(
                    args.model,
                    args.proxy_port,
                    args.thinking,
                    args.api_key_env,
                    context_window,
                ),
                False,
            ),
            (
                home / ".pi/agent/settings.json",
                {
                    "defaultProvider": pi_provider_id,
                    "defaultModel": args.model,
                    "defaultThinkingLevel": args.thinking,
                },
                False,
            ),
            (
                home / ".pi/agent/models.json",
                pi_models(
                    pi_provider_id,
                    args.model,
                    args.proxy_port,
                    args.api_key_env,
                    context_window,
                    max_tokens,
                ),
                True,
            ),
            (
                home / ".config/opencode/opencode.json",
                opencode_settings(args.model, args.proxy_port, args.thinking, args.api_key_env),
                False,
            ),
        ]
        for path, desired, merge_models in targets:
            if merge_models:
                existing = load_json(path)
                desired = merge_pi_models(existing, desired, pi_provider_id)
            write_merged_json(path, desired, apply)
    except (OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("MCP registration, Codex TOML, autonomy, role-specific models, subagent files, CLI installs, and npx skills remain explicit workflow steps.")
    print("The model and illustrative context limits must be verified before --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
