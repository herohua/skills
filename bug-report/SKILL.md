---
name: bug-report
description: Refresh an ADO bug report dashboard. Queries Azure DevOps for open bugs, regenerates an HTML dashboard with summary tiles, charts, and categorized bug tables, then opens it in the browser. Invoke with /bug-report [refresh]
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion
---

# ADO Bug Report Skill

Generate and refresh an HTML bug report dashboard from Azure DevOps work items. Configuration is driven by `config.json` co-located with the script in the working directory.

## Configuration

Look for `config.json` in the current working directory. It contains:

```json
{
  "ado_org": "https://dev.azure.com/<org>",
  "ado_project": "<project>",
  "area_path": "<area\\path>",
  "product_name": "<display name>",
  "title_contains": "<title filter>",
  "excluded_states": ["Closed", "Resolved"],
  "editorial_tag": "editorial-triage",
  "editorial_category": "Editorial"
}
```

If `config.json` is not found, use `AskUserQuestion` to gather:
- ADO org URL (e.g. `https://dev.azure.com/myorg`)
- ADO project name
- Area path
- Product/display name
- Title filter text (for `CONTAINS` clause)

Then create `config.json` from the answers before proceeding.

## Project Layout

All files live in the working directory (same directory as `config.json`):

- `config.json` — Configuration: ADO org, project, area path, product name, editorial tag
- `generate_report.py` — Main script: reads config.json + ado_bugs.json → generates HTML report
- `ado_bugs.json` — Raw ADO query output (refreshed each run)
- `bug_report.html` — Generated HTML report

## Refresh Steps

Read `config.json` first to get the values, then run these three steps sequentially:

### Step 1: Query ADO

Build the WIQL dynamically from config values. The template is:

```
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Priority], [Microsoft.VSTS.Common.Severity], [System.AssignedTo], [System.CreatedDate], [System.Tags]
FROM workitems
WHERE [System.WorkItemType] = 'Bug'
  AND [System.Title] CONTAINS '<title_contains>'
  AND [System.State] <> '<excluded_state_1>'
  AND [System.State] <> '<excluded_state_2>'
  AND [System.AreaPath] UNDER '<area_path>'
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

Run with:
```bash
az boards query --wiql "<WIQL>" --org <ado_org> --project <ado_project> --output json > ado_bugs.json
```

### Step 2: Generate HTML

```bash
python generate_report.py
```

### Step 3: Open report

```bash
start "" bug_report.html
```

## Report Features

- **Summary tiles**: Total bugs, Categories, P0+P1 count, Active count, Pending review count (if editorial_tag configured)
- **Bar charts**: Bugs by Category, State, Priority
- **Collapsible category sections** with bug tables (ID link, title, state, priority, editorial icon, assignee, created date)
- **Expand All / Collapse All** controls

## Categorization Logic

1. Categories are extracted from `[xxx]` prefixes in bug titles (excluding `[<title_contains>]`)
2. If `editorial_tag` is configured, bugs with that tag are also added to the editorial category
3. Bugs without any `[xxx]` prefix go to **Uncategorized**
4. Within each category, bugs are sorted by created date descending (newest first)

## After Refresh

Report the total bug count and category count to the user.

## Modifying the Report

If the user asks to change the report format, edit `generate_report.py` directly. The script reads `config.json` and `ado_bugs.json`, then produces `bug_report.html`. After editing, re-run steps 2 and 3.
