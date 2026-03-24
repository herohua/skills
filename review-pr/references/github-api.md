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
- `previous_filename` — original path before rename/copy (only present when `status` is `"renamed"` or `"copied"`)

### Pagination for Large PRs

The `/pulls/{prNumber}/files` endpoint returns at most 30 files by default (max 100 with `per_page`). For PRs with more than 100 changed files, follow the `Link` response header for pagination:

```bash
# First page
gh api repos/{owner}/{repo}/pulls/{prNumber}/files?per_page=100 > /tmp/pr-review/files-page1.json

# Follow pagination via Link header (rel="next")
gh api repos/{owner}/{repo}/pulls/{prNumber}/files?per_page=100&page=2
```

Alternatively, `gh pr diff` returns the complete diff regardless of file count and does not paginate.

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

### Cross-Fork PRs

When a PR originates from a fork, the head branch lives in a different repository. Check `head.repo.full_name` in the PR metadata:

```bash
# Check if PR is from a fork
gh api repos/{owner}/{repo}/pulls/{prNumber} \
  --jq 'if .head.repo.full_name != .base.repo.full_name then "fork: " + .head.repo.full_name else "same repo" end'
```

For fork PRs, clone or fetch from the fork's repository to download source files. The `gh pr checkout` command handles this automatically.

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
- `commit_id` — the head SHA of the PR. Technically optional, but **strongly recommended**: without it, GitHub uses the PR's latest head commit, which can shift between when you read the diff and when you post the comment, causing the comment to land on the wrong line. Always pass the SHA you diffed against.

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

### Batch Comments via Pending Review

Instead of posting comments one at a time (which creates noisy email notifications), batch them into a single pending review and submit once:

```bash
# Step 1: Create a pending review
REVIEW_ID=$(gh api repos/{owner}/{repo}/pulls/{prNumber}/reviews \
  -X POST -f event="PENDING" --jq '.id')

# Step 2: Add comments to the pending review
gh api repos/{owner}/{repo}/pulls/{prNumber}/reviews/$REVIEW_ID/comments \
  -X POST -f path="src/file.py" -F line=10 -f body="Issue here"

# Step 3: Submit the review (makes all comments visible at once)
gh api repos/{owner}/{repo}/pulls/{prNumber}/reviews/$REVIEW_ID/events \
  -X POST -f event="COMMENT" -f body="Review summary"
```

This sends a single notification to the PR author with all comments grouped together.

### Delete a Comment

To remove a mistakenly posted review comment:

```bash
# Delete a pull request review comment by ID
gh api repos/{owner}/{repo}/pulls/comments/{commentId} -X DELETE

# Delete a general issue comment by ID
gh api repos/{owner}/{repo}/issues/comments/{commentId} -X DELETE
```

## Known Pitfalls Summary

1. **`gh pr diff` is merge-base aware**: Unlike raw `git diff`, `gh pr diff` already handles the merge base correctly. Prefer it over manual commit comparison.
2. **File path format**: GitHub uses paths without leading `/` (e.g., `src/Foo/Bar.cs`), unlike Azure DevOps which requires a leading `/`.
3. **Rate limits**: GitHub API has rate limits (5000 requests/hour for authenticated users). Mitigate with:
   - Batch comments into a single pending review instead of posting individually.
   - Check remaining quota via `gh api rate_limit --jq '.resources.core'` before starting a large review.
   - Cache file downloads and diff results so repeated reviews of the same PR don't re-fetch unchanged data.
   - If you receive HTTP 403 with `X-RateLimit-Remaining: 0`, wait until `X-RateLimit-Reset` (Unix epoch seconds).
4. **Large diffs**: The `/pulls/{prNumber}/files` endpoint returns at most 3000 files and truncates individual file patches over ~100 KB. When the response includes `"truncated": true` or a file's `patch` field is missing, fall back to `gh pr diff` which streams the complete diff. For very large PRs (1000+ files), consider reviewing in batches by directory or using the pagination approach described above.
5. **Draft PRs**: Draft PRs are reviewable but `gh pr review --approve` will fail on drafts.
