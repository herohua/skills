# Azure DevOps REST API Reference for PR Reviews

Quick reference for API calls used during PR review. All calls require authentication via personal access token or `az` CLI token.

## Authentication

```bash
# Get token via Azure CLI
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# All curl calls use basic auth with empty username
curl -s -u ":$TOKEN" ...
```

The resource GUID `499b84ac-1321-427f-aa17-267ca6975798` is the Azure DevOps resource identifier.

## Base URL

```
ORG="https://dev.azure.com/{organization}"
# API base: $ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID
```

## PR Metadata

```bash
# Via az CLI (preferred for initial metadata)
az repos pr show --id {prId} --organization https://dev.azure.com/{org} --detect false
```

**Pitfall**: `--project` is NOT a valid flag for `az repos pr show`. Use `--organization` + `--detect false`.

Key response fields:
| Field | Description |
|-------|-------------|
| `repository.id` | Repo GUID (`$REPO_ID`) |
| `repository.project.id` | Project GUID (`$PROJECT_ID`) |
| `lastMergeSourceCommit.commitId` | Latest source commit |
| `lastMergeTargetCommit.commitId` | Latest target commit |
| `sourceRefName` | Source branch (e.g., `refs/heads/feature/x`) |
| `targetRefName` | Target branch (e.g., `refs/heads/develop`) |

## Iterations

```bash
curl -s -u ":$TOKEN" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/iterations?api-version=7.0"
```

Response: `value[]` array of iterations. Each has:
- `id` — iteration number (1, 2, 3...)
- `sourceRefCommit.commitId` — source commit at that iteration
- `targetRefCommit.commitId` — target commit at that iteration
- `commonRefCommit.commitId` — merge base (common ancestor) commit; use this for the base version in diffs

**Pitfall**: Use `commonRefCommit.commitId` (not `targetRefCommit` from iteration 1) for the merge base. `commonRefCommit` is the authoritative common ancestor and is present on every iteration.

## Iteration Changes

```bash
curl -s -u ":$TOKEN" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/iterations/{iterationId}/changes?api-version=7.0"
```

Response: `changeEntries[]` with:
- `changeType`: `1` = add, `2` = edit, `16` = delete
- `item.path`: file path

## Commit Diff Summary

```bash
curl -s -u ":$TOKEN" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/diffs/commits?baseVersion={baseCommit}&baseVersionType=commit&targetVersion={targetCommit}&targetVersionType=commit&api-version=7.0"
```

Response: `changes[]` with `changeType` and `item.path`, plus `aheadCount` and `behindCount`.

**Pitfall**: `az devops invoke --resource diffs` with api-version 7.0 fails. Use raw `curl` instead.

## File Download

```bash
# By branch name
curl -s -u ":$TOKEN" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/items?path=/{filePath}&versionType=branch&version={branchName}&api-version=7.0" \
  -o "/tmp/pr-review/source/{filePath}"

# By commit SHA
curl -s -u ":$TOKEN" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/items?path=/{filePath}&versionType=commit&version={commitSha}&api-version=7.0" \
  -o "/tmp/pr-review/base/{filePath}"
```

**Pitfall**: On Windows, files at `/tmp/` paths are not accessible via the `Read` tool. Use `cat` via `Bash` instead.

## Clone Repository

When a full repo clone is needed for deeper analysis:
```bash
# Clone via az CLI (uses cached credentials)
az repos clone --repository {repoName} --organization https://dev.azure.com/{org} --project {projectName} -- --depth 1 --single-branch --branch {sourceBranch} "/tmp/pr-review/repo"

# Or clone via git with token auth
git clone --depth 1 --single-branch --branch {sourceBranch} \
  "https://:$TOKEN@dev.azure.com/{org}/{project}/_git/{repo}" \
  "/tmp/pr-review/repo"
```

## PR Threads (Comments)

### Fetch existing threads
```bash
curl -s -u ":$TOKEN" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/threads?api-version=7.0"
```

Response: `value[]` with:
- `id` — thread ID
- `status` — "active", "resolved", etc.
- `threadContext.filePath` — file the thread is on (null for general comments)
- `comments[]` — array of comments in the thread
  - `commentType` — `1` = normal, skip `"system"` type
  - `content` — comment body (supports markdown)
  - `author.displayName` — who wrote it

### Post inline file comment
```bash
curl -s -u ":$TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/threads?api-version=7.0" \
  -d '{
    "comments": [
      {
        "parentCommentId": 0,
        "content": "Comment body with **markdown**\n\n(Comment by Reviewer and Claude)",
        "commentType": 1
      }
    ],
    "status": 1,
    "threadContext": {
      "filePath": "/src/path/to/File.cs",
      "rightFileStart": { "line": 44, "offset": 1 },
      "rightFileEnd": { "line": 44, "offset": 83 }
    },
    "pullRequestThreadContext": {
      "iterationContext": {
        "firstComparingIteration": 1,
        "secondComparingIteration": 2
      }
    }
  }'
```

### Post general PR comment (no file context)
```bash
curl -s -u ":$TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/threads?api-version=7.0" \
  -d '{
    "comments": [
      {
        "parentCommentId": 0,
        "content": "General comment text\n\n(Comment by Reviewer and Claude)",
        "commentType": 1
      }
    ],
    "status": 1
  }'
```

## Field Reference

| Field | Value | Meaning |
|-------|-------|---------|
| `commentType` | `1` | Normal comment |
| `status` | `1` | Active thread |
| `parentCommentId` | `0` | Top-level comment (not a reply) |
| `changeType` (iterations) | `1` | File added |
| `changeType` (iterations) | `2` | File edited |
| `changeType` (iterations) | `16` | File deleted |

## Known Pitfalls Summary

1. **WebFetch fails**: Azure DevOps URLs redirect to sign-in (302 to `vssps.visualstudio.com/_signin`). Use `az` CLI or `curl` with token.
2. **`--project` flag invalid**: `az repos pr show` does not accept `--project`. Use `--organization` + `--detect false`.
3. **`az devops invoke` unreliable**: The `--resource diffs` + `--api-version 7.0` combo fails. Use raw `curl`.
4. **Windows `/tmp/` paths**: Files at `/tmp/` are not readable by the `Read` tool on Windows. Use `Bash` + `cat`.
5. **Merge-base vs HEAD**: Always use the merge base (common ancestor) for diffs, not the current target branch HEAD. Diffing against HEAD flags pre-existing code as PR changes.
6. **`filePath` prefix**: Thread context `filePath` must start with `/` (e.g., `/src/Foo/Bar.cs`).
7. **Token does not persist across Bash calls**: On Windows, each `Bash` tool invocation starts a fresh shell. Always re-fetch `TOKEN` at the top of each Bash command: `TOKEN=$(az account get-access-token --resource 499b84ac-... --query accessToken -o tsv)`.
8. **Inline JSON `-d` breaks with markdown content**: Comment bodies containing backticks, code blocks, or escaped characters cause bash escaping failures when passed inline via `-d '{...}'`. Always write JSON payloads to temp files and use `curl -d @/tmp/pr-review/commentN.json`. Use heredoc with single-quoted delimiter (`<< 'JSONEOF'`) to avoid bash variable expansion.
9. **Closing accidental threads**: To hide a mistakenly posted thread, PATCH the thread URL with `{"status": "closed"}`:
   ```bash
   curl -s -u ":$TOKEN" -X PATCH -H "Content-Type: application/json" \
     "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/threads/{threadId}?api-version=7.0" \
     -d '{"status": "closed"}'
   ```
10. **`secondComparingIteration` must match latest iteration**: When posting inline comments, set `secondComparingIteration` in the `pullRequestThreadContext.iterationContext` to the latest iteration number. Using a stale iteration number causes comments to appear on the wrong code or fail silently.
