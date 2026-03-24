# bug-report

A Claude Code skill that queries Azure DevOps for open bugs and generates an interactive HTML dashboard with summary tiles, bar charts, and collapsible categorized tables.

## Setup

1. Copy this skill folder to `~/.claude/skills/bug-report/`
2. Copy `generate_report.py` and `config.example.json` to your project working directory
3. Rename `config.example.json` to `config.json` and fill in your values
4. Invoke with `/bug-report`

## Configuration

Create a `config.json` in your working directory:

| Field | Required | Description |
|---|---|---|
| `ado_org` | Yes | Full ADO org URL (e.g. `https://dev.azure.com/myorg`) |
| `ado_project` | Yes | ADO project name |
| `area_path` | Yes | Area path filter for the WIQL query |
| `product_name` | Yes | Display name used in the report title and footer |
| `title_contains` | Yes | Text filter for bug titles (`CONTAINS` clause) |
| `excluded_states` | Yes | Array of states to exclude (e.g. `["Closed", "Resolved"]`) |
| `extra_tag` | No | ADO tag name — bugs with this tag are also grouped into `extra_tag_category` |
| `extra_tag_category` | No | Category name for bugs matching `extra_tag` |

If `config.json` is not found when the skill runs, it will prompt you for the values interactively.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/) with the `azure-devops` extension
- Python 3.x
- Authenticated to ADO: `az login` and `az devops configure --defaults organization=<org> project=<project>`

## How It Works

1. Queries ADO using `az boards query` with a WIQL built from your config
2. Runs `generate_report.py` to transform the JSON into an HTML dashboard
3. Opens the report in your browser

## Report Features

- Summary tiles: total bugs, categories, P0+P1 count, active count, extra tag count
- Bar charts: bugs by category, state, priority
- Collapsible category sections with sortable bug tables
- Bugs are categorized by `[tag]` prefixes in their titles
- Optional extra tag column (if `extra_tag` is configured)
