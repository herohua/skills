# GitHub API Reference for PR Reviews

Quick reference for GitHub API calls used during PR review. Uses the `gh` CLI which handles authentication automatically.

## Authentication

```bash
# Verify auth status
gh auth status

# Login if needed
gh auth login
```

## PR Metadata

```bash
# Full PR metadata as JSON
gh pr view {prNumber} --repo {owner}/{repo} --json title,body,author,reviewRequests,state,baseRefName,headRefName,commits,files,additions,deletions

# Human-readable summary
gh pr view {prNumber} --repo {owner}/{repo}
```

Key JSON fields:
| Field | Description |
|-------|-------------|
| `title` | PR title |
| `body` | PR description |
| `author.login` | PR author |
| `state` | OPEN, CLOSED, MERGED |
| `baseRefName` | Target branch |
| `headRefName` | Source branch |
| `files[].path` | Changed file paths |
| `commits[].oid` | Commit SHAs |

## Diff (Merge-Base)

GitHub's `gh pr diff` already computes against the merge base correctly:
```bash
# Get the full diff (preferred — handles merge-base automatically)
gh pr diff {prNumber} --repo {owner}/{repo}
```

To get the merge base commit explicitly:
```bash
# Get the PR's base SHA (merge base)
gh api repos/{owner}/{repo}/pulls/{prNumber} --jq '.base.sha'

# Compare two commits
gh api repos/{owner}/{repo}/compare/{base}...{head} --jq '.files[].filename'
```

## Changed Files

```bash
# List changed files with stats
gh pr diff {prNumber} --repo {owner}/{repo} --stat

# Get file list via API
gh api repos/{owner}/{repo}/pulls/{prNumber}/files --jq '.[].filename'

# Get file list with patch content
gh api repos/{owner}/{repo}/pulls/{prNumber}/files
```

Response fields per file:
- `filename` — file path
- `status` — "added", "modified", "removed", "renamed"
- `additions`, `deletions`, `changes` — line counts
- `patch` — unified diff content

## File Download

```bash
# View file at a specific commit
gh api repos/{owner}/{repo}/contents/{filePath}?ref={commitSha} --jq '.content' | base64 -d

# Or use raw content URL
gh api repos/{owner}/{repo}/git/blobs/{sha} --jq '.content' | base64 -d
```

## Clone Repository

When a full repo clone is needed for deeper analysis:
```bash
# Shallow clone of the PR branch (uses gh auth automatically)
gh repo clone {owner}/{repo} /tmp/pr-review/repo -- --depth 1 --single-branch --branch {headRefName}

# Or checkout the PR directly into an existing clone
gh pr checkout {prNumber} --repo {owner}/{repo}
```

## PR Comments & Reviews

### Fetch existing review comments (inline)
```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/comments
```

Response: array of comments with:
- `path` — file the comment is on
- `line` / `original_line` — line number
- `body` — comment text
- `user.login` — who wrote it
- `created_at` — timestamp

### Fetch review summaries
```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/reviews
```

### Fetch issue-level comments (general, non-inline)
```bash
gh api repos/{owner}/{repo}/issues/{prNumber}/comments
```

### Post inline file comment
```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/comments \
  -X POST \
  -f path="{filePath}" \
  -F line={lineNumber} \
  -f side="RIGHT" \
  -f body="Comment body with **markdown**

(Comment by Reviewer and Claude)"
```

Parameters:
- `path` — file path relative to repo root (no leading `/`)
- `line` — line number in the diff (RIGHT side = new file)
- `side` — "RIGHT" for new file, "LEFT" for old file
- `commit_id` — (optional) the head SHA of the PR

### Post multi-line comment
```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/comments \
  -X POST \
  -f path="{filePath}" \
  -F start_line={startLine} \
  -F line={endLine} \
  -f start_side="RIGHT" \
  -f side="RIGHT" \
  -f body="Comment spanning multiple lines

(Comment by Reviewer and Claude)"
```

### Post general PR comment (not tied to a file)
```bash
gh pr comment {prNumber} --repo {owner}/{repo} --body "General comment text

(Comment by Reviewer and Claude)"
```

### Submit a full review with multiple comments
```bash
# Create a pending review, add comments, then submit
gh api repos/{owner}/{repo}/pulls/{prNumber}/reviews \
  -X POST \
  -f event="COMMENT" \
  -f body="Review summary" \
  --input comments.json
```

Where `comments.json` contains:
```json
{
  "comments": [
    { "path": "file.py", "line": 10, "body": "Issue here" },
    { "path": "other.py", "line": 20, "body": "Another issue" }
  ]
}
```

## Known Pitfalls Summary

1. **`gh pr diff` is merge-base aware**: Unlike raw `git diff`, `gh pr diff` already handles the merge base correctly. Prefer it over manual commit comparison.
2. **File path format**: GitHub uses paths without leading `/` (e.g., `src/Foo/Bar.cs`), unlike Azure DevOps which requires a leading `/`.
3. **Rate limits**: GitHub API has rate limits (5000 requests/hour for authenticated users). Batch operations where possible.
4. **Large diffs**: PRs with 300+ files may be truncated in the API response. Use pagination or `gh pr diff` for complete diffs.
5. **Draft PRs**: Draft PRs are reviewable but `gh pr review --approve` will fail on drafts.
