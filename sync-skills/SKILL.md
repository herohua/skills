---
name: sync-skills
description: Sync local Claude Code skills from GitHub repositories into ~/.claude/skills. Use this whenever the user asks to update, refresh, fetch, pull, or install skills from anthropics/skills, herohua/skills, or similar skill repositories, especially for commands like /sync-skills.
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
---

# Sync Skills

Update the local skills directory at `~/.claude/skills` from these repositories:

- Official skills: `https://github.com/anthropics/skills`
- Personal skills: `https://github.com/herohua/skills`

This skill is for the user's local environment. Prefer generic home-folder references such as `~/.claude/...` in user-facing text, and avoid exposing the account name or absolute home path.

## Goal

Keep local skills current while avoiding accidental deletion of unrelated directories.

## Safety rules

- Only sync directories that contain a `SKILL.md` file.
- For `anthropics/skills`, only sync directories under the repository's `skills/` subdirectory.
- For `herohua/skills`, only sync top-level directories that contain `SKILL.md`.
- Preserve all non-target directories in `~/.claude/skills`.
- Do not delete directories that are not being replaced from the current source repo.
- Use `gh` for fetching or cloning.
- Do not assume Python is installed. Prefer `gh --jq` and shell for overlap detection and sync steps.
- If `gh` authentication fails, stop and ask the user to run `gh auth login`.
- Same-source refresh is allowed without confirmation: official skills may overwrite their own local copies, and personal skills may overwrite their own local copies.
- Cross-source overwrite is not allowed without confirmation. If a skill name exists in both repos, or the current sync would replace a skill that belongs to the other source, stop and ask the user before proceeding.
- Prefer replacing each targeted skill directory atomically by deleting that one directory and copying in the refreshed version, but only after the overwrite rules above are satisfied.

## Default behavior

When invoked without extra arguments, sync both repositories:

1. Clone `anthropics/skills` to a temporary directory.
2. Clone `herohua/skills` to a temporary directory.
3. Build the set of official skill names and personal skill names using `gh --jq` and shell.
4. If any skill names overlap between the two repos, stop and ask the user whether to allow those specific cross-source overwrites.
5. If approved, copy each official `skills/<name>` folder that contains `SKILL.md` into `~/.claude/skills/<name>`.
6. Then copy each personal top-level `<name>` folder that contains `SKILL.md` into `~/.claude/skills/<name>`.
7. Print a concise summary of synced skill names and any confirmed overlap decisions.

## Optional behavior

If `$ARGUMENTS` mentions one source only, support it:

- `official` or `anthropics`: sync only `anthropics/skills`
- `personal` or `herohua`: sync only `herohua/skills`

If `$ARGUMENTS` is ambiguous, ask the user whether to sync `official`, `personal`, or `both`.

## Recommended commands

Use bash commands like these, adjusted only if needed:

### Sync official skills

```bash
target_dir="$HOME/.claude/skills" && tmpdir=$(mktemp -d) && gh repo clone anthropics/skills "$tmpdir/skills-repo" -- --depth=1 && for d in "$tmpdir/skills-repo/skills"/*; do if [ -d "$d" ] && [ -f "$d/SKILL.md" ]; then name=$(basename "$d"); rm -rf "$target_dir/$name"; cp -R "$d" "$target_dir/$name"; printf 'synced %s\n' "$name"; fi; done
```

### Sync personal skills

```bash
target_dir="$HOME/.claude/skills" && tmpdir=$(mktemp -d) && gh repo clone herohua/skills "$tmpdir/personal-skills" -- --depth=1 && for d in "$tmpdir/personal-skills"/*; do if [ -d "$d" ] && [ -f "$d/SKILL.md" ]; then name=$(basename "$d"); rm -rf "$target_dir/$name"; cp -R "$d" "$target_dir/$name"; printf 'synced %s\n' "$name"; fi; done
```

### Sync both in sequence

Run an overlap check first using `gh --jq` and shell. If there is no cross-source overlap, sync the official repo first, then the personal repo.

## Reporting back

After syncing, report:

- Which repo or repos were synced
- Which skill directories were updated
- That non-target directories were preserved

If nothing was synced because authentication or repository access failed, say so plainly and stop.
