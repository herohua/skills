# Azure DevOps MCP Tools Reference for PR Reviews

Quick reference for ADO operations using the `azure-devops` MCP server. Authentication is handled transparently by the MCP server — no token management needed.

For curl-based operations (iterations, file downloads, diffs), see `azure-devops-api.md`.

## Bootstrapping: URL → Repository ID

The MCP tools require a `repositoryId` (GUID). Parse the PR URL to extract `{project}` and `{repoName}`, then look up the ID:

1. Parse URL: `https://dev.azure.com/{org}/{project}/_git/{repoName}/pullrequest/{prId}`
2. Call `repo_get_repo_by_name_or_id(project={project}, repositoryNameOrId={repoName})`
3. Extract `id` from the response — this is `$REPO_ID` for all subsequent calls.

Also extract `project.id` from the response — this is `$PROJECT_ID`, needed for curl-based operations.

## PR Metadata

```
repo_get_pull_request_by_id(repositoryId=$REPO_ID, pullRequestId={prId})
```

Key response fields:
| Field | Description |
|-------|-------------|
| `repository.id` | Repo GUID (`$REPO_ID`) |
| `repository.project.id` | Project GUID (`$PROJECT_ID`) |
| `lastMergeSourceCommit.commitId` | Latest source commit |
| `lastMergeTargetCommit.commitId` | Latest target commit |
| `sourceRefName` | Source branch (e.g., `refs/heads/feature/x`) |
| `targetRefName` | Target branch (e.g., `refs/heads/develop`) |
| `status` | PR status: `active`, `completed`, or `abandoned` |

## Fetch PR Threads (Existing Comments)

```
repo_list_pull_request_threads(repositoryId=$REPO_ID, pullRequestId={prId})
```

Optional parameters:
- `skip` / `top` — pagination (default top=100)
- `baseIteration` / `iteration` — filter threads by iteration range

Response includes threads with:
- `id` — thread ID
- `status` — "active", "resolved", etc.
- `threadContext.filePath` — file the thread is on (null for general comments)
- `comments[]` — array of comments in the thread

### Fetch Individual Thread Comments

```
repo_list_pull_request_thread_comments(repositoryId=$REPO_ID, pullRequestId={prId}, threadId={threadId})
```

Use when you need detailed comment content for a specific thread.

## Post Comments

### General Comment (no file context)

```
repo_create_pull_request_thread(
  repositoryId=$REPO_ID,
  pullRequestId={prId},
  content="Comment body with **markdown**\n\n(Comment by Reviewer and Claude)"
)
```

### Inline File Comment

```
repo_create_pull_request_thread(
  repositoryId=$REPO_ID,
  pullRequestId={prId},
  content="Comment body",
  filePath="/src/path/to/File.cs",
  rightFileStartLine=44,
  rightFileStartOffset=1,
  rightFileEndLine=44,
  rightFileEndOffset=83
)
```

### IMPORTANT: Set Thread Status After Posting

The MCP `repo_create_pull_request_thread` tool does **not** support a `status` parameter. Threads created via MCP have no status, which Azure DevOps renders as **"Unknown"** in the UI. This looks unprofessional and confusing to reviewers.

**After every `repo_create_pull_request_thread` call**, immediately PATCH the thread to set `"status": 1` (Active):

```bash
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)
curl -s -u ":$TOKEN" -X PATCH -H "Content-Type: application/json" \
  "$ORG/$PROJECT_ID/_apis/git/repositories/$REPO_ID/pullrequests/{prId}/threads/{threadId}?api-version=7.0" \
  -d '{"status": 1}'
```

Extract `{threadId}` from the `id` field in the MCP response. This is a lightweight call and should be done for every posted thread.

**Alternative**: Use the curl-based posting method from `azure-devops-api.md` instead of MCP, which includes `"status": 1` in the JSON body directly.

**`iterationContext` limitation**: The MCP tool does not support `pullRequestThreadContext.iterationContext` (`firstComparingIteration` / `secondComparingIteration`). Comments anchor to the latest iteration by default. This is safe when the freshness check (Phase 7) confirms no new iterations since analysis. If iteration pinning is required, fall back to curl — see `azure-devops-api.md`.

**Line number verification**: Always verify exact line numbers against the downloaded source file before posting. See `review-checklist.md` § "Line Number Verification".

## Reply to Thread

```
repo_reply_to_comment(
  repositoryId=$REPO_ID,
  pullRequestId={prId},
  threadId={threadId},
  content="Reply body"
)
```

## Resolve Thread

```
repo_resolve_comment(
  repositoryId=$REPO_ID,
  pullRequestId={prId},
  threadId={threadId}
)
```

Sets thread status to **resolved** (status=4). The author can re-activate the thread.

**Note**: This does NOT close/hide the thread (status=2). To hide an accidental comment, use the curl PATCH method in `azure-devops-api.md`.

## Search Code (Remote Repo Search)

```
search_code(
  searchText="IFooService.Bar",
  project=["{project}"],
  repository=["{repoName}"]
)
```

Use in Phase 3 to check for callers of changed interfaces or methods without cloning the entire repository. If the search answers the question (e.g., "are there other callers of this interface?"), a full clone can be skipped.

## Known Pitfalls

1. **`repo_get_pull_request_by_id` requires `repositoryId`**: Must call `repo_get_repo_by_name_or_id` first to get the GUID. Cannot go directly from PR URL to PR metadata.
2. **No `iterationContext` on inline comments**: MCP tool lacks `firstComparingIteration` / `secondComparingIteration` params. Comments anchor to latest iteration. Fall back to curl when pinning to a specific iteration.
3. **Resolve vs close**: `repo_resolve_comment` resolves threads (status=4), not closes them (status=2). Use curl for hiding accidental comments.
4. **`filePath` requires leading `/`**: Always prefix file paths with `/` (e.g., `/src/Foo/Bar.cs`).
5. **`project` parameter**: Some MCP tools accept an optional `project` parameter. When provided, use the project name (not the GUID).
6. **Threads created without status show as "Unknown"**: `repo_create_pull_request_thread` does not set a thread status. Azure DevOps renders these as "Unknown" in the UI. Always PATCH the thread to `"status": 1` (Active) immediately after creation — see "Set Thread Status After Posting" above.
