---
name: review-pr
description: Review a pull request for bugs, design issues, and process concerns. Supports Azure DevOps and GitHub. Fetches PR metadata, computes merge-base diff, analyzes changes, presents findings interactively, and posts approved comments. Invoke with /review-pr <pr-url> [--post-as <name>]
allowed-tools: Bash, Read, Grep, Glob, Agent, AskUserQuestion, WebFetch, mcp__azure-devops__repo_get_repo_by_name_or_id, mcp__azure-devops__repo_get_pull_request_by_id, mcp__azure-devops__repo_list_pull_request_threads, mcp__azure-devops__repo_list_pull_request_thread_comments, mcp__azure-devops__repo_create_pull_request_thread, mcp__azure-devops__repo_reply_to_comment, mcp__azure-devops__repo_resolve_comment, mcp__azure-devops__search_code
user-invocable: true
---

# Pull Request Review Skill

You are helping a reviewer produce a high-quality PR review. This is an **interactive, collaborative process** — you analyze the changes, present findings for validation, and only post comments the reviewer approves.

## Critical Rules

1. **Always diff against the merge base** — never diff against the current target branch HEAD. Diffing against HEAD produces false positives by flagging pre-existing code as PR changes.
2. **Verify every finding is actually in the diff** — before reporting an issue, confirm the relevant lines were changed in this PR (not pre-existing code).
3. **Never auto-post comments** — always present findings to the reviewer first and let them choose what to post.
4. **Check for duplicate feedback** — fetch existing PR threads before posting to avoid repeating what other reviewers already said.

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- **First positional arg**: PR URL (Azure DevOps or GitHub) — required
- `--post-as <name>`: Attribution name for posted comments (default: prompt the user)

If no URL is provided, use `AskUserQuestion` to request one.

---

## Phase 1: Detect Platform & Fetch PR Metadata

### URL Detection

Parse the PR URL to determine the platform:
- **Azure DevOps**: URL contains `dev.azure.com` or `visualstudio.com`. Extract `{org}`, `{project}`, `{repoName}`, and `{prId}` from the URL pattern: `https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{prId}`
- **GitHub**: URL contains `github.com`. Extract `{owner}`, `{repo}`, and `{prNumber}` from: `https://github.com/{owner}/{repo}/pull/{prNumber}`

### Load Platform Reference

Based on the detected platform, read the corresponding API reference file(s) for detailed call patterns:
- **Azure DevOps**: Read `references/azure-devops-mcp.md` (MCP-based operations) and `references/azure-devops-api.md` (curl-based operations for iterations, diffs, file downloads). Both are needed — MCP handles metadata and thread operations, curl handles diff computation. **If the `azure-devops` MCP server is not available** (e.g., MCP tools fail or are not configured), fall back to `azure-devops-api.md` for all operations — it is fully self-contained.
- **GitHub**: Read `references/github-api.md` (relative to this skill's directory)

Only load the reference(s) for the detected platform — do not load both platforms.

### Fetch Metadata

Use the patterns from the loaded reference to fetch PR metadata.

**Azure DevOps (MCP)**: Call `repo_get_repo_by_name_or_id(project={project}, repositoryNameOrId={repoName})` to get the repo GUID, then call `repo_get_pull_request_by_id(repositoryId={repoGuid}, pullRequestId={prId})` for PR metadata. If the MCP tools are unavailable, fall back to `az repos pr show` (see `azure-devops-api.md`).

**GitHub**: Use `gh pr view` as documented in `github-api.md`.

Extract:
- Title, description, status
- Author and reviewers
- Source and target branches
- Repository identifiers (needed for subsequent API calls)
- Source and target commit SHAs

### PR State Validation

After fetching metadata, check the PR status before proceeding:
- **GitHub**: If `state` is `MERGED` or `CLOSED`, inform the reviewer and ask if they still want to review (the diff is still available, but posting comments may be less useful).
- **Azure DevOps**: If `status` is `completed` or `abandoned`, same guidance.

For active/open PRs, proceed normally.

### Present Summary

Display to the reviewer:
- PR title and description
- Author and reviewers
- Source → Target branch
- Number of changed files

---

## Phase 2: Get Correct Diff (Merge-Base)

**This is the most critical phase.** The diff MUST be computed against the merge base (common ancestor), not the target branch HEAD.

Follow the platform-specific patterns from the loaded reference file to:

1. **Find the merge base** (common ancestor commit)
2. **Get the list of changed files** with change types
3. **Download both versions** of each changed file (base and source)
4. **Generate unified diffs** between them

Store the diffs and the full source versions of changed files — both are needed for analysis in Phase 4.

---

### Large PR Strategy

For PRs with 300+ changed files:
1. **Warn the reviewer** that reviewing this many files thoroughly will take significant time.
2. **Prioritize by risk**: Focus on non-test production code first, then tests, then config/docs.
3. **Batch file downloads**: Use pagination (see platform reference) rather than fetching all files in a single API call.
4. **Consider scope splitting**: Ask the reviewer if they want to focus on specific directories or file types.

### Binary File Detection

Before generating diffs, detect and skip binary files. See `references/review-checklist.md` § "Binary File Detection" for the full detection criteria and known binary extensions.

### File Rename and Move Semantics

Platforms report renames differently:
- **GitHub**: The file entry has `status: "renamed"` and a `previous_filename` field with the old path.
- **Azure DevOps**: The `changeType` is `32` (rename) or `34` (rename + edit). The old path is in `sourceServerItem`.

When reviewing renames:
- If rename-only (no content change), note it but skip detailed review.
- If rename + edit, diff the old-path base version against the new-path source version.

### Diff Line to File Line Mapping

When posting inline comments, the `line` parameter refers to different things per platform:
- **GitHub**: The `line` is the **line number in the file** (not the diff hunk position). Use `side: "RIGHT"` for new file lines, `side: "LEFT"` for old file lines.
- **Azure DevOps**: The `rightFileStart.line` / `rightFileEnd.line` in `threadContext` are **1-based line numbers in the file**.

**Do NOT estimate line numbers from diff hunk headers** (e.g., `@@ -181,4 +198,31 @@`). Hunk headers show approximate ranges and are misleading — they don't account for surrounding context lines, doc comments, or blank lines between the hunk boundary and your target code. Instead, always verify the exact line number by running `cat -n` or `grep -n` on the downloaded source file before posting. For example, to comment on `internal bool IsOriginalContentChanged(...)`, run `grep -n 'IsOriginalContentChanged' /tmp/pr-review/source/File.cs` rather than guessing from the diff. Getting this wrong causes comments to appear on the wrong line (e.g., on a doc comment instead of the method signature).

---

## Phase 3: Assess Whether Full Repository Context Is Needed

After seeing the diff and changed files, assess whether reviewing only the changed files is sufficient, or whether the full repository is needed for a thorough review.

### Signals That Suggest Full Repo Access Is Needed

- **Interface/API changes**: Modified files define interfaces, base classes, or public APIs that may have callers elsewhere in the repo
- **Shared utility/helper changes**: The PR modifies shared code (e.g., extension methods, common services, configuration) used by multiple consumers
- **Dependency injection / registration changes**: Changes to DI setup or service registration that affect how components are wired
- **Refactoring with renames**: Renamed methods/classes/namespaces that may require updates across the codebase
- **Test files missing from the diff**: Changed production code but no corresponding test file changes — may need to verify test coverage exists elsewhere
- **Cross-project references**: Changes that span multiple projects/modules within a monorepo

### Try Remote Code Search First (Azure DevOps)

Before deciding to clone, try `search_code` (MCP tool) to search the remote repository for callers or references to changed interfaces/methods. This can answer questions like "are there other callers of this interface?" without a full clone.

```
search_code(searchText="IFooService.Bar", project=["{project}"], repository=["{repoName}"])
```

If the search answers the question, skip the clone entirely. If results are inconclusive or the reviewer needs deeper exploration, proceed to the clone decision below.

### Signals That Suggest Changed Files Are Sufficient

- **Leaf changes**: New files, test-only changes, or modifications to code with no external callers
- **Self-contained features**: New endpoint/handler added with its own tests
- **Configuration/docs only**: Changes to config files, docs, or build scripts

### Auto-Skip Patterns

The following change patterns are reliably self-contained. When **all** changed files match these patterns, state your reasoning in one line and proceed to Phase 4 without prompting:

- **New model/DTO classes**: Files that only define a data class with properties and no behavior. These have no callers until wired in by other changed files already in the diff.
- **Additive method changes**: A method gains a new parameter with a default value, or a new overload is added — callers are unaffected.
- **Test-only changes**: New or modified test files with no production code changes.
- **Config/docs only**: Changes to `.md`, `.json`, `.yml`, `.csproj` config, or build scripts.
- **Wiring + tests included**: The PR includes both the new code and its integration point (e.g., DI registration + service + tests), making the change set self-contained.

### Decision Workflow

If the assessment is **clear-cut** (changes match auto-skip patterns, or are leaf nodes with no external callers), state your reasoning briefly and proceed without prompting. Only use `AskUserQuestion` when the decision is genuinely ambiguous.

When prompting is needed:
1. Present your assessment to the reviewer with reasoning:
   - List which signals you detected
   - Recommend whether a full clone is needed
   - Note what specific questions a full clone would help answer (e.g., "need to check callers of `IFooService.Bar()`")

2. Use `AskUserQuestion` to let the reviewer decide:
   - **"Review with changed files only"** — proceed with what you have
   - **"Clone the repo for full context"** — clone the source branch and use it during analysis
   - **"I'll provide the repo path"** — reviewer points you to an existing local clone

3. If cloning, use the patterns from the loaded platform reference. Use shallow clone (`--depth 1`) on the source branch to minimize download time.

---

## Phase 4: Fetch Existing Comments

Before analyzing, fetch all existing PR threads/comments to avoid duplicate feedback.

**Azure DevOps (MCP)**: Use `repo_list_pull_request_threads(repositoryId, pullRequestId)` to fetch threads. Use `repo_list_pull_request_thread_comments(repositoryId, pullRequestId, threadId)` for detailed comment content on specific threads. If MCP tools are unavailable, fall back to curl (see `azure-devops-api.md`).

**GitHub**: Use `gh api` as documented in `github-api.md`.

Summarize existing feedback so you can check against it in Phase 5:
- Which files have comments
- What issues were raised
- Who raised them
- Thread status (active, resolved, etc.)

### Stale Comment Detection

PRs with multiple iterations often accumulate comments — from human reviewers, AI review bots, or CI tools — that were posted on earlier iterations and may reference code that has since changed or been removed. For each existing comment:
1. Check when the comment was posted relative to the PR iterations — if it was posted on an earlier iteration, it may be stale.
2. If the comment references specific code (via `threadContext` file/line), verify whether that code still exists unchanged in the latest source version.
3. Flag stale comments in your summary so the reviewer knows which existing feedback may no longer be relevant, and so you don't duplicate findings that were already raised but are now outdated.

### Fetch Thread Context for Human Reviewer Comments

For active threads from human reviewers, fetch the `threadContext` (file path and line range) so you know **where** the comment is anchored, not just **what** it says. This allows you to:
- Accurately detect whether your findings overlap with existing inline comments on the same lines.
- Avoid posting a new comment on a line that already has an active discussion thread.
- Provide the reviewer with a richer summary of existing feedback (e.g., "2 active threads on `Foo.cs`, lines 44 and 88").

---

## Phase 5: Analyze Changes

For each changed file, read the **full source version** (not just diff hunks) to understand context. If a full repo clone was obtained in Phase 3, use it to explore callers, related files, and broader architectural context via `Agent` subagents (`subagent_type: Explore`).

### Review Checklist & Verification

Read `references/review-checklist.md` (relative to this skill's directory) for the full review checklist, severity levels, verification discipline, and output format. Apply it to every changed file.

Key points:
- Check for bugs, design issues, process issues, and security vulnerabilities
- **Verify every finding** passes all three conditions: in the diff, not already flagged, and a real issue
- Discard findings that fail any condition — false positives erode reviewer trust

---

## Phase 6: Present Findings to Reviewer

Present a **numbered table** of findings:

```
| #  | Severity | File:Line | Description | Existing? |
|----|----------|-----------|-------------|-----------|
| 1  | Bug      | Foo.cs:44 | Null ref... | No        |
| 2  | Design   | Bar.cs:12 | DRY viol... | No        |
| 3  | Nit      | Baz.cs:88 | Naming...   | Similar   |
```

Severity levels:
- **Bug**: Functional correctness issue
- **Design**: Architectural or maintainability concern
- **Nit**: Style, naming, minor improvement
- **Process**: TODO items, test gaps, unrelated changes

For each finding, include a brief explanation of:
- What the issue is
- Why it matters
- Suggested fix (if obvious)

### Ask Reviewer for Input

Use a **single** `AskUserQuestion` call with multiple questions to minimize round-trips:
- **Question 1**: Which findings to post as PR comments — offer grouped options (e.g., "All findings", "Bugs only", "Bugs + Design", "None")
- **Question 2**: Attribution text for comments — offer options like "(Comment by {reviewer name} and Claude)" or "(Comment by Claude)"

Do NOT ask these as separate sequential questions.

---

## Phase 7: Post Comments to PR

For each approved finding, post a comment using the platform-appropriate method.

**Azure DevOps (MCP)**: Use `repo_create_pull_request_thread` for both inline and general comments. For inline comments, provide `filePath`, `rightFileStartLine`, `rightFileStartOffset`, `rightFileEndLine`, `rightFileEndOffset`. Omit file/line params for general comments. See `azure-devops-mcp.md` for details.

**Azure DevOps (curl fallback)**: Use curl when `iterationContext` pinning is needed (see `azure-devops-api.md` for the full JSON payload with `pullRequestThreadContext.iterationContext`).

**GitHub**: Use `gh api` as documented in `github-api.md`.

Include the agreed attribution text at the end of each comment body.

### Comment Posting Best Practices

- **Prefer MCP tools for Azure DevOps**: `repo_create_pull_request_thread` eliminates JSON escaping, token management, and temp file issues. Only fall back to curl when `iterationContext` is needed.
- **For curl fallback**: Always write the JSON payload to a temp file and use `curl -d @/tmp/pr-review/commentN.json` instead of inline `-d '...'`. Use heredoc with `'JSONEOF'` (single-quoted delimiter) to prevent bash variable expansion.
- Post comments **in parallel** when they target different files to save time.
- For Azure DevOps curl, set `secondComparingIteration` to the **latest iteration number** so line numbers resolve correctly.
- **Rate limiting**: When posting many comments, add a brief delay (1-2 s) between requests. For GitHub, prefer batching all comments into a single pending review (see reference). For Azure DevOps, monitor for HTTP 429 responses and respect the `Retry-After` header.

### Freshness Check Before Posting

**Before posting any comments**, re-fetch the PR iterations to check if a new iteration has been pushed since the analysis was performed. Compare the latest `sourceRefCommit.commitId` against the commit SHA used during analysis.

- If they match, proceed with posting.
- If they differ, **stop** — warn the reviewer that the PR has been updated since the analysis, offer to re-analyze with the new version, and do NOT post stale comments.

This prevents the embarrassing situation of posting review comments that reference code the author has already changed.

### After Posting

Report which comments were posted successfully and provide links where available. If any fail, report the error and offer to retry.

### Cleaning Up Mistakes

If you accidentally post a test comment or wrong content:
- **Azure DevOps (MCP)**: Use `repo_resolve_comment(repositoryId, pullRequestId, threadId)` to resolve the thread. To fully hide it, use curl to PATCH the thread with `"status": "closed"` (see `azure-devops-api.md`).
- **GitHub**: Use `gh api` to delete the comment.

---

## Error Handling

- If authentication fails, guide the user through `az login` (Azure DevOps) or `gh auth login` (GitHub)
- If the PR URL cannot be parsed, ask the user to provide the correct URL format
- If file downloads fail for specific files, skip them and note which files could not be reviewed
- If comment posting fails, show the error and offer alternatives (e.g., copy comment text to clipboard)
- If repo clone fails, fall back to reviewing with changed files only and inform the reviewer

---

## Re-Review After PR Update

This phase is triggered when the reviewer asks to recheck an updated PR, **or** when Claude detects that the PR has been updated (e.g., the freshness check in Phase 7 reveals a new iteration):

1. **Re-fetch PR metadata** to get the new source commit SHA. For Azure DevOps, use `repo_get_pull_request_by_id` (MCP).
2. **Re-fetch iterations** to find the latest iteration number and confirm the merge base hasn't changed.
3. **Optimize the re-diff**:
   - If the merge base is unchanged, reuse the existing base file downloads.
   - Only re-download the source versions of changed files using the new source commit.
   - Compare the old source versions against the new source versions (iteration-over-iteration diff) to quickly identify **what changed between iterations** — present this delta to the reviewer first.
4. **Re-fetch existing comments** — new review threads may have been added since the last review. For Azure DevOps, use `repo_list_pull_request_threads` (MCP).
5. **Re-analyze** with the updated diffs. Previously-posted findings that are still valid do not need to be re-posted. Focus on:
   - Whether previous findings have been addressed
   - Any new issues introduced in the update
   - Any existing reviewer comments that are now resolved or still open
6. **Close addressed threads** — for any previously-posted findings that have been addressed in the new iteration, ask the reviewer which threads to close. Use `AskUserQuestion` with a multi-select list of addressed threads (showing thread ID, finding summary, and how it was addressed). Only close threads the reviewer explicitly approves. Use the platform-specific method to close them:
   - **Azure DevOps (MCP)**: Use `repo_resolve_comment(repositoryId, pullRequestId, threadId)` to resolve. Use `repo_reply_to_comment` to add a note acknowledging the fix before resolving.
   - **Azure DevOps (curl)**: PATCH the thread with `{"status": "closed"}` for full hide
   - **GitHub**: Post a reply acknowledging the fix, or delete if preferred
7. **Present updated findings** following the same Phase 6 workflow.
