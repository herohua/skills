"""Fetch ADO work item comments and detect priority/category discrepancies."""
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import base64

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
with open(config_path) as f:
    config = json.load(f)

ado_org = config["ado_org"]
ado_project = config["ado_project"]
pat_env = config.get("ado_pat_env", "ADO_PAT")

input_path = os.path.join(script_dir, "ado_bugs.json")
output_path = os.path.join(script_dir, "ado_comments_analysis.json")

# Priority suggestion patterns
PRIORITY_PATTERNS = [
    re.compile(r"\bshould\s+be\s+P([0-3])\b", re.IGNORECASE),
    re.compile(r"\braise\s+to\s+P([0-3])\b", re.IGNORECASE),
    re.compile(r"\blower\s+to\s+P([0-3])\b", re.IGNORECASE),
    re.compile(r"\bP([0-3])\s+blocker\b", re.IGNORECASE),
    re.compile(r"\bescalate\s+to\s+P([0-3])\b", re.IGNORECASE),
    re.compile(r"\bmark\s+(?:as\s+)?P([0-3])\b", re.IGNORECASE),
    re.compile(r"\bassign\s+(?:as\s+)?(?:a\s+)?P([0-3])\b", re.IGNORECASE),
]

# Priority keyword patterns (no capture group — inferred priority)
PRIORITY_KEYWORD_PATTERNS = [
    (re.compile(r"\b(?:this\s+is|should\s+be)\s+critical\b", re.IGNORECASE), "P0"),
    (re.compile(r"\b(?:this\s+is|should\s+be)\s+(?:high|urgent)\b", re.IGNORECASE), "P1"),
    (re.compile(r"\b(?:lower\s+priority|deprioritize|not\s+urgent)\b", re.IGNORECASE), "P3"),
    (re.compile(r"\b(?:increase\s+priority|higher\s+priority)\b", re.IGNORECASE), "P1"),
]

# Category suggestion patterns
CATEGORY_PATTERNS = [
    re.compile(r"\bmove\s+to\s+\[?(\w[\w\s]*?)\]?\s*(?:category)?\b", re.IGNORECASE),
    re.compile(r"\bshould\s+be\s+in\s+\[?(\w[\w\s]*?)\]?\s*(?:category)?\b", re.IGNORECASE),
    re.compile(r"\bbelongs\s+in\s+\[?(\w[\w\s]*?)\]?\b", re.IGNORECASE),
    re.compile(r"\brecategorize\s+(?:to|as)\s+\[?(\w[\w\s]*?)\]?\b", re.IGNORECASE),
    re.compile(r"\bwrong\s+category\b", re.IGNORECASE),
]


def get_auth_header():
    """Get authorization header — try PAT env var first, then az CLI."""
    pat = os.environ.get(pat_env, "")
    if pat:
        encoded = base64.b64encode(f":{pat}".encode()).decode()
        return f"Basic {encoded}"
    # Fallback to az CLI
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", "499b84ac-1321-427f-aa17-267ca6975798", "--query", "accessToken", "-o", "tsv"],
            capture_output=True, text=True, check=True, shell=True
        )
        token = result.stdout.strip()
        if token:
            return f"Bearer {token}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def fetch_comments(bug_id, auth_header):
    """Fetch comments for a single work item."""
    org = ado_org.rstrip("/")
    url = f"{org}/{ado_project}/_apis/wit/workItems/{bug_id}/comments?api-version=7.0-preview.3"
    req = urllib.request.Request(url, headers={
        "Authorization": auth_header,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("comments", [])
    except urllib.error.HTTPError as e:
        print(f"  Warning: HTTP {e.code} fetching comments for bug {bug_id}")
        return []
    except Exception as e:
        print(f"  Warning: Error fetching comments for bug {bug_id}: {e}")
        return []


def analyze_comment(text, current_priority, current_categories):
    """Analyze a single comment for discrepancies. Returns list of discrepancies."""
    discrepancies = []

    # Check priority suggestions with explicit P-number
    for pattern in PRIORITY_PATTERNS:
        match = pattern.search(text)
        if match:
            suggested_p = int(match.group(1))
            if suggested_p != current_priority:
                discrepancies.append({
                    "type": "priority",
                    "suggested": f"P{suggested_p}",
                    "current": f"P{current_priority}",
                    "snippet": text[max(0, match.start() - 30):match.end() + 30].strip(),
                })

    # Check priority keyword patterns
    for pattern, suggested_label in PRIORITY_KEYWORD_PATTERNS:
        match = pattern.search(text)
        if match:
            suggested_p = int(suggested_label[1])
            if suggested_p != current_priority:
                discrepancies.append({
                    "type": "priority",
                    "suggested": suggested_label,
                    "current": f"P{current_priority}",
                    "snippet": text[max(0, match.start() - 30):match.end() + 30].strip(),
                })

    # Check category suggestions
    for pattern in CATEGORY_PATTERNS:
        match = pattern.search(text)
        if match:
            suggested_cat = match.group(1).strip() if match.lastindex else "unknown"
            # Only flag if it's not already in the current categories
            if suggested_cat.lower() not in [c.lower() for c in current_categories]:
                discrepancies.append({
                    "type": "category",
                    "suggested": suggested_cat,
                    "current": ", ".join(current_categories) or "Uncategorized",
                    "snippet": text[max(0, match.start() - 30):match.end() + 30].strip(),
                })

    return discrepancies


def main():
    with open(input_path) as f:
        bugs = json.load(f)

    auth_header = get_auth_header()
    if not auth_header:
        print(f"Error: No ADO authentication available. Set ${pat_env} or run 'az login'.")
        sys.exit(1)

    print(f"Fetching comments for {len(bugs)} bugs...")
    results = []

    for i, b in enumerate(bugs):
        bug_id = b.get("id")
        fields = b.get("fields", {})
        title = fields.get("System.Title", "")
        current_priority = fields.get("Microsoft.VSTS.Common.Priority", "N/A")

        # Get current categories from title
        matches = re.findall(r"\[([^\]]+)\]", title)
        title_contains = config.get("title_contains", config["product_name"])
        current_categories = [m for m in matches if m.lower() != title_contains.lower()]

        comments = fetch_comments(bug_id, auth_header)
        all_discrepancies = []
        for comment in comments:
            comment_text = comment.get("text", "")
            # Strip HTML tags from comment text
            clean_text = re.sub(r"<[^>]+>", " ", comment_text)
            comment_by = comment.get("createdBy", {}).get("displayName", "Unknown")
            comment_date = comment.get("createdDate", "")[:10]

            discs = analyze_comment(clean_text, current_priority, current_categories)
            for d in discs:
                d["comment_by"] = comment_by
                d["comment_date"] = comment_date
            all_discrepancies.extend(discs)

        entry = {
            "id": bug_id,
            "title": title,
            "current_priority": current_priority,
            "current_categories": current_categories,
            "discrepancies": all_discrepancies,
        }
        results.append(entry)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(bugs)} bugs...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    disc_count = sum(1 for r in results if r["discrepancies"])
    total_discs = sum(len(r["discrepancies"]) for r in results)
    print(f"\nDone. {disc_count} bugs with discrepancies ({total_discs} total discrepancies).")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
