import json
import os
import re
from collections import defaultdict
from datetime import datetime

# Load config from config.json in the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
with open(config_path) as f:
    config = json.load(f)

product_name = config["product_name"]
ado_org = config["ado_org"]
ado_project = config["ado_project"]
area_path = config["area_path"]
extra_tag = config.get("extra_tag", "")
extra_tag_category = config.get("extra_tag_category", "")
title_contains = config.get("title_contains", product_name)

# Category keyword heuristic for auto-suggesting categories on uncategorized bugs
DEFAULT_CATEGORY_KEYWORDS = {
    "API": ["api", "endpoint", "rest", "request", "response", "http", "status code", "400", "401", "403", "404", "500"],
    "Backend": ["server", "backend", "service", "middleware", "controller", "handler"],
    "Infrastructure": ["infra", "deploy", "pipeline", "ci/cd", "build", "release", "config", "environment"],
    "Stability": ["crash", "hang", "freeze", "timeout", "retry", "intermittent", "flaky", "unstable", "stuck"],
    "Performance": ["slow", "latency", "performance", "memory", "cpu", "throughput", "bottleneck", "lag"],
    "UX": ["ui", "ux", "display", "layout", "button", "dialog", "modal", "tooltip", "responsive"],
    "Accessibility": ["a11y", "accessibility", "screen reader", "narrator", "keyboard", "focus", "aria", "wcag"],
    "Data": ["data", "database", "sql", "query", "migration", "schema", "corruption", "loss"],
    "Security": ["security", "auth", "permission", "token", "credential", "vulnerability", "xss", "csrf"],
    "Documentation": ["doc", "documentation", "readme", "help text", "tooltip text", "error message"],
}
# Allow config.json to override/extend keyword categories
CATEGORY_KEYWORDS = {**DEFAULT_CATEGORY_KEYWORDS, **config.get("category_keywords", {})}


def suggest_category(title, tags):
    """Score a bug's title+tags against keyword categories. Returns (category, True) or (None, False)."""
    text = f"{title} {tags}".lower()
    best_cat, best_score = None, 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_cat, best_score = cat, score
    if best_score >= 1:
        return best_cat, True
    return None, False

# All paths are relative to the script's directory
output_dir = script_dir

# Derive org short name (last segment of org URL) for display
org_short = ado_org.rstrip("/").rsplit("/", 1)[-1]

# Work item URL base
wi_url_base = f"{ado_org}/{ado_project}/_workitems/edit"

# Input / output paths
input_path = os.path.join(output_dir, "ado_bugs.json")
output_path = os.path.join(output_dir, "bug_report.html")

with open(input_path) as f:
    bugs = json.load(f)

# Load comment discrepancy analysis (optional — report works without it)
comments_path = os.path.join(output_dir, "ado_comments_analysis.json")
discrepancy_map = {}  # bug_id -> list of discrepancies
discrepancy_bug_count = 0
try:
    with open(comments_path) as f:
        comments_analysis = json.load(f)
    for entry in comments_analysis:
        if entry.get("discrepancies"):
            discrepancy_map[entry["id"]] = entry["discrepancies"]
    discrepancy_bug_count = len(discrepancy_map)
except (FileNotFoundError, json.JSONDecodeError):
    pass

# Categorize bugs
categorized = defaultdict(list)
for b in bugs:
    fields = b.get("fields", {})
    title = fields.get("System.Title", "")
    matches = re.findall(r"\[([^\]]+)\]", title)
    cats = [m for m in matches if m.lower() != title_contains.lower()]

    bug_info = {
        "id": b.get("id"),
        "title": title,
        "state": fields.get("System.State", "N/A"),
        "priority": fields.get("Microsoft.VSTS.Common.Priority", "N/A"),
        "severity": fields.get("Microsoft.VSTS.Common.Severity", "N/A"),
        "assigned_to": (
            fields.get("System.AssignedTo", {}).get("displayName", "Unassigned")
            if isinstance(fields.get("System.AssignedTo"), dict)
            else "Unassigned"
        ),
        "created_date": fields.get("System.CreatedDate", ""),
        "tags": fields.get("System.Tags", ""),
        "url": f"{wi_url_base}/{b.get('id')}",
        "suggested": False,
    }

    if cats:
        for c in cats:
            categorized[c].append(bug_info)
    else:
        # Try keyword-based category suggestion
        suggested_cat, is_suggested = suggest_category(title, bug_info["tags"])
        if is_suggested:
            bug_info["suggested"] = True
            categorized[suggested_cat].append(bug_info)
        else:
            categorized["Uncategorized"].append(bug_info)

    # Also add to extra tag category if tagged but not already there
    if extra_tag:
        tags = fields.get("System.Tags", "")
        if extra_tag.lower() in tags.lower() and extra_tag_category not in cats:
            categorized[extra_tag_category].append(bug_info)

# Sort categories: alphabetical, but "Uncategorized" last
sorted_cats = sorted(
    [c for c in categorized.keys() if c != "Uncategorized"]
)
if "Uncategorized" in categorized:
    sorted_cats.append("Uncategorized")

# Count states across all bugs
state_counts = defaultdict(int)
priority_counts = defaultdict(int)
for b in bugs:
    fields = b.get("fields", {})
    state_counts[fields.get("System.State", "N/A")] += 1
    priority_counts[fields.get("Microsoft.VSTS.Common.Priority", "N/A")] += 1

# Count bugs with the extra tag
extra_tag_ids = set()
if extra_tag:
    for b in bugs:
        fields = b.get("fields", {})
        tags = fields.get("System.Tags", "")
        if extra_tag.lower() in tags.lower():
            extra_tag_ids.add(b["id"])
extra_tag_count = len(extra_tag_ids)

# State colors
state_colors = {
    "New": "#0078d4",
    "Active": "#f59e0b",
    "Triaged": "#8b5cf6",
    "Review": "#10b981",
    "Resolved": "#6b7280",
    "Closed": "#374151",
}

# Priority labels
priority_labels = {0: "P0 - Critical", 1: "P1 - High", 2: "P2 - Medium", 3: "P3 - Low"}

# Category colors
cat_colors = [
    "#0078d4", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#3498db", "#e91e63", "#607d8b"
]

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# Escape area_path backslashes for HTML display
area_path_display = area_path.replace("\\", "&#92;")

# Build extra tag column header tooltip
extra_tag_tooltip = f"Tagged: {extra_tag} ({extra_tag_category})" if extra_tag else ""

# Build HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{product_name} - Bug Report</title>
<style>
  :root {{
    --bg: #f8f9fa;
    --card-bg: #ffffff;
    --border: #e0e0e0;
    --text: #1a1a1a;
    --text-secondary: #555;
    --header-bg: linear-gradient(135deg, #0078d4, #005a9e);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  .header {{
    background: var(--header-bg);
    color: white;
    padding: 32px 40px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }}
  .header h1 {{ font-size: 28px; font-weight: 600; margin-bottom: 4px; }}
  .header .subtitle {{ opacity: 0.85; font-size: 14px; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 40px; }}

  /* Summary cards */
  .summary-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }}
  .summary-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
  }}
  .summary-card .number {{ font-size: 36px; font-weight: 700; color: #0078d4; }}
  .summary-card .label {{ font-size: 13px; color: var(--text-secondary); margin-top: 4px; }}

  /* Charts row */
  .charts-row {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-bottom: 28px;
  }}
  .chart-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
  }}
  .chart-card h3 {{ font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; font-weight: 600; }}
  .bar-row {{
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    font-size: 13px;
  }}
  .bar-label {{ width: 120px; flex-shrink: 0; color: var(--text-secondary); }}
  .bar-track {{ flex: 1; height: 22px; background: #eee; border-radius: 4px; overflow: hidden; position: relative; }}
  .bar-fill {{ height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 8px; color: white; font-size: 12px; font-weight: 600; min-width: 28px; }}
  .bar-count {{ margin-left: 8px; font-weight: 600; color: var(--text); }}

  /* Category sections */
  .category-section {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 20px;
    overflow: hidden;
  }}
  .category-header {{
    padding: 16px 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    user-select: none;
    border-bottom: 1px solid var(--border);
  }}
  .category-header:hover {{ background: #f5f5f5; }}
  .category-header .left {{ display: flex; align-items: center; gap: 12px; }}
  .category-badge {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 12px;
    color: white;
    font-size: 13px;
    font-weight: 600;
  }}
  .category-count {{
    font-size: 14px;
    color: var(--text-secondary);
  }}
  .chevron {{
    transition: transform 0.2s;
    font-size: 18px;
    color: #999;
  }}
  .category-section.collapsed .chevron {{ transform: rotate(-90deg); }}
  .category-section.collapsed .bug-table {{ display: none; }}

  /* Bug table */
  .bug-table {{ width: 100%; border-collapse: collapse; }}
  .bug-table th {{
    text-align: left;
    padding: 10px 16px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: #fafafa;
    border-bottom: 1px solid var(--border);
  }}
  .bug-table td {{
    padding: 10px 16px;
    font-size: 13px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top;
  }}
  .bug-table tr:last-child td {{ border-bottom: none; }}
  .bug-table tr:hover td {{ background: #f9f9fb; }}
  .bug-table tr.priority-row-0 td {{ background: #fef2f2; }}
  .bug-table tr.priority-row-0:hover td {{ background: #fee2e2; }}
  .bug-table tr.priority-row-1 td {{ background: #fffbeb; }}
  .bug-table tr.priority-row-1:hover td {{ background: #fef3c7; }}
  body.filter-p01 .bug-table tr:not(.priority-row-0):not(.priority-row-1) {{ display: none; }}
  body.filter-p01 .category-section.empty-after-filter {{ display: none; }}
  .controls button.active {{ background: #0078d4; color: white; border-color: #0078d4; }}
  .bug-id {{
    font-family: 'Cascadia Code', monospace;
    font-weight: 600;
  }}
  .bug-id a {{ color: #0078d4; text-decoration: none; }}
  .bug-id a:hover {{ text-decoration: underline; }}
  .bug-title {{ max-width: 500px; }}

  /* State badges */
  .state-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 600;
    color: white;
  }}
  .priority-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
  }}
  .priority-0 {{ background: #dc2626; color: white; }}
  .priority-1 {{ background: #f59e0b; color: white; }}
  .priority-2 {{ background: #6b7280; color: white; }}
  .extra-tag-icon {{
    display: inline-block;
    width: 22px;
    height: 22px;
    line-height: 22px;
    text-align: center;
    border-radius: 50%;
    background: #9b59b6;
    color: white;
    font-size: 13px;
    font-weight: 700;
    cursor: default;
  }}
  .suggested-label {{
    font-size: 11px;
    font-style: italic;
    color: #e67e22;
    margin-left: 6px;
  }}
  .discrepancy-icon {{
    display: inline-block;
    width: 22px;
    height: 22px;
    line-height: 22px;
    text-align: center;
    border-radius: 4px;
    background: #f59e0b;
    color: white;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    position: relative;
  }}
  .discrepancy-tooltip {{
    display: none;
    position: absolute;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%);
    background: #1a1a1a;
    color: #fff;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 400;
    white-space: nowrap;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    text-align: left;
    max-width: 400px;
    white-space: normal;
  }}
  .discrepancy-icon:hover .discrepancy-tooltip {{ display: block; }}

  .footer {{
    text-align: center;
    padding: 24px;
    color: #999;
    font-size: 12px;
  }}

  /* Collapse all / expand all */
  .controls {{
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    justify-content: flex-end;
  }}
  .controls button {{
    padding: 6px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: white;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-secondary);
  }}
  .controls button:hover {{ background: #f0f0f0; }}
</style>
</head>
<body>

<div class="header">
  <h1>{product_name} &mdash; Remaining Bugs</h1>
  <div class="subtitle">
    ADO Project: {org_short} / {ado_project} &nbsp;&bull;&nbsp;
    Area Path: {area_path_display} &nbsp;&bull;&nbsp;
    Generated: {now}
  </div>
</div>

<div class="container">

<!-- Summary cards -->
<div class="summary-row">
  <div class="summary-card">
    <div class="number">{len(bugs)}</div>
    <div class="label">Total Remaining Bugs</div>
  </div>
  <div class="summary-card">
    <div class="number">{len(categorized)}</div>
    <div class="label">Categories</div>
  </div>
  <div class="summary-card">
    <div class="number" style="color: #dc2626">{priority_counts.get(0, 0) + priority_counts.get(1, 0)}</div>
    <div class="label">P0 + P1 (Critical/High)</div>
  </div>
  <div class="summary-card">
    <div class="number" style="color: #f59e0b">{state_counts.get('Active', 0)}</div>
    <div class="label">Active</div>
  </div>
  <div class="summary-card">
    <div class="number" style="color: #9b59b6">{extra_tag_count}</div>
    <div class="label">Tagged: {extra_tag_category}</div>
  </div>
  <div class="summary-card">
    <div class="number" style="color: #f59e0b">{discrepancy_bug_count}</div>
    <div class="label">Comment Discrepancies</div>
  </div>
</div>

<!-- Charts -->
<div class="charts-row">
  <!-- By Category -->
  <div class="chart-card">
    <h3>Bugs by Category</h3>
"""

max_cat_count = max(len(v) for v in categorized.values()) if categorized else 1
for i, cat in enumerate(sorted_cats):
    count = len(categorized[cat])
    pct = (count / max_cat_count) * 100
    color = cat_colors[i % len(cat_colors)]
    html += f"""    <div class="bar-row">
      <div class="bar-label">{cat}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}">{count}</div></div>
    </div>
"""

html += """  </div>
  <!-- By State -->
  <div class="chart-card">
    <h3>Bugs by State</h3>
"""

max_state_count = max(state_counts.values()) if state_counts else 1
for state in ["New", "Active", "Triaged", "Review"]:
    count = state_counts.get(state, 0)
    if count == 0:
        continue
    pct = (count / max_state_count) * 100
    color = state_colors.get(state, "#888")
    html += f"""    <div class="bar-row">
      <div class="bar-label">{state}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}">{count}</div></div>
    </div>
"""

html += """  </div>
  <!-- By Priority -->
  <div class="chart-card">
    <h3>Bugs by Priority</h3>
"""

max_pri_count = max(priority_counts.values()) if priority_counts else 1
for pri in [0, 1, 2, 3]:
    count = priority_counts.get(pri, 0)
    if count == 0:
        continue
    pct = (count / max_pri_count) * 100
    label = priority_labels.get(pri, f"P{pri}")
    colors_pri = {0: "#dc2626", 1: "#f59e0b", 2: "#6b7280", 3: "#94a3b8"}
    html += f"""    <div class="bar-row">
      <div class="bar-label">{label}</div>
      <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{colors_pri.get(pri, '#888')}">{count}</div></div>
    </div>
"""

html += """  </div>
</div>

<!-- Controls -->
<div class="controls">
  <button id="filterP01Btn" onclick="togglePriorityFilter()">Show only P0/P1</button>
  <button onclick="document.querySelectorAll('.category-section').forEach(s=>s.classList.remove('collapsed'))">Expand All</button>
  <button onclick="document.querySelectorAll('.category-section').forEach(s=>s.classList.add('collapsed'))">Collapse All</button>
</div>
<script>
function togglePriorityFilter() {
  var on = document.body.classList.toggle('filter-p01');
  var btn = document.getElementById('filterP01Btn');
  btn.classList.toggle('active', on);
  btn.textContent = on ? 'Show all priorities' : 'Show only P0/P1';
  document.querySelectorAll('.category-section').forEach(function(sec){
    var visibleRows = sec.querySelectorAll('tbody tr.priority-row-0, tbody tr.priority-row-1');
    sec.classList.toggle('empty-after-filter', on && visibleRows.length === 0);
  });
}
</script>

"""

# Category sections
for i, cat in enumerate(sorted_cats):
    bug_list = categorized[cat]
    color = cat_colors[i % len(cat_colors)]
    # Sort bugs by created date descending (newest first)
    bug_list.sort(key=lambda b: b["created_date"], reverse=True)

    # Build extra tag column header — only show if extra_tag is configured
    extra_tag_th = f'<th style="width:40px" title="{extra_tag_tooltip}">Tag</th>' if extra_tag else ""

    html += f"""<div class="category-section">
  <div class="category-header" onclick="this.parentElement.classList.toggle('collapsed')">
    <div class="left">
      <span class="category-badge" style="background:{color}">{cat}</span>
      <span class="category-count">{len(bug_list)} bug{"s" if len(bug_list) != 1 else ""}{' (includes suggested)' if any(b.get('suggested') for b in bug_list) else ''}</span>
    </div>
    <span class="chevron">&#9660;</span>
  </div>
  <table class="bug-table">
    <thead>
      <tr>
        <th style="width:80px">ID</th>
        <th>Title</th>
        <th style="width:80px">State</th>
        <th style="width:60px">Priority</th>
        {extra_tag_th}
        {'<th style="width:30px" title="Comment discrepancies detected">&#9888;</th>' if discrepancy_map else ''}
        <th style="width:140px">Assigned To</th>
        <th style="width:100px">Created</th>
      </tr>
    </thead>
    <tbody>
"""
    for bug in bug_list:
        state_color = state_colors.get(bug["state"], "#888")
        pri_class = f"priority-{bug['priority']}" if bug["priority"] in [0, 1, 2] else "priority-2"
        created = bug["created_date"][:10] if bug["created_date"] else "N/A"
        # Clean title: remove product name tag and first category tag for display
        display_title = bug["title"]
        display_title = re.sub(rf"\[{re.escape(title_contains)}\]\s*", "", display_title)
        display_title = re.sub(r"\[[^\]]+\]\s*", "", display_title, count=1)

        extra_tag_td = ""
        if extra_tag:
            icon = f'<span class="extra-tag-icon" title="{extra_tag}">{extra_tag_category[0]}</span>' if bug["id"] in extra_tag_ids else ""
            extra_tag_td = f'<td style="text-align:center">{icon}</td>'

        # Discrepancy warning icon
        discrepancy_td = ""
        if discrepancy_map:
            disc_list = discrepancy_map.get(bug["id"], [])
            if disc_list:
                tooltip_lines = "<br>".join(
                    f"{d['type'].title()}: {d.get('comment_by', '?')} suggested {d.get('suggested', '?')} (current: {d.get('current', '?')})"
                    for d in disc_list
                )
                discrepancy_td = f'<td style="text-align:center"><span class="discrepancy-icon" title="Discrepancies found">&#9888;<span class="discrepancy-tooltip">{tooltip_lines}</span></span></td>'
            else:
                discrepancy_td = '<td></td>'

        # Suggested category label
        suggested_label = '<span class="suggested-label">(suggested)</span>' if bug.get("suggested") else ""

        html += f"""      <tr class="priority-row-{bug['priority'] if bug['priority'] in [0,1,2,3] else 'na'}">
        <td class="bug-id"><a href="{bug['url']}" target="_blank">{bug['id']}</a></td>
        <td class="bug-title">{display_title}{suggested_label}</td>
        <td><span class="state-badge" style="background:{state_color}">{bug['state']}</span></td>
        <td><span class="priority-badge {pri_class}">P{bug['priority']}</span></td>
        {extra_tag_td}
        {discrepancy_td}
        <td>{bug['assigned_to']}</td>
        <td>{created}</td>
      </tr>
"""

    html += """    </tbody>
  </table>
</div>

"""

html += f"""</div>

<div class="footer">
  {product_name} Bug Report &bull; {org_short}/{ado_project} &bull; Area Path: {area_path_display} &bull; {now}
</div>

</body>
</html>"""

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Report generated: {output_path}")
print(f"Total bugs: {len(bugs)}")
print(f"Categories: {len(sorted_cats)}")
suggested_ids = set()
for cat_bugs in categorized.values():
    for cb in cat_bugs:
        if cb.get("suggested"):
            suggested_ids.add(cb["id"])
print(f"Suggested categorizations: {len(suggested_ids)}")
if discrepancy_bug_count:
    print(f"Bugs with comment discrepancies: {discrepancy_bug_count}")
