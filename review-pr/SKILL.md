---
name: review-pr
description: Review a pull request for bugs, design issues, and process concerns. Supports Azure DevOps and GitHub. Fetches PR metadata, computes merge-base diff, analyzes changes, presents findings interactively, and posts approved comments. Invoke with /review-pr <pr-url> [--post-as <name>]
allowed-tools: Bash, Read, Grep, Glob, Agent, AskUserQuestion, WebFetch
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

Based on the detected platform, read the corresponding API reference file for detailed call patterns:
- **Azure DevOps**: Read `references/azure-devops-api.md` (relative to this skill's directory)
- **GitHub**: Read `references/github-api.md` (relative to this skill's directory)

Only load the reference for the detected platform — do not load both.

### Fetch Metadata

Use the patterns from the loaded reference to fetch PR metadata. Extract:
- Title, description, status
- Author and reviewers
- Source and target branches
- Repository identifiers (needed for subsequent API calls)
- Source and target commit SHAs

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

## Phase 3: Assess Whether Full Repository Context Is Needed

After seeing the diff and changed files, assess whether reviewing only the changed files is sufficient, or whether the full repository is needed for a thorough review.

### Signals That Suggest Full Repo Access Is Needed

- **Interface/API changes**: Modified files define interfaces, base classes, or public APIs that may have callers elsewhere in the repo
- **Shared utility/helper changes**: The PR modifies shared code (e.g., extension methods, common services, configuration) used by multiple consumers
- **Dependency injection / registration changes**: Changes to DI setup or service registration that affect how components are wired
- **Refactoring with renames**: Renamed methods/classes/namespaces that may require updates across the codebase
- **Test files missing from the diff**: Changed production code but no corresponding test file changes — may need to verify test coverage exists elsewhere
- **Cross-project references**: Changes that span multiple projects/modules within a monorepo

### Signals That Suggest Changed Files Are Sufficient

- **Leaf changes**: New files, test-only changes, or modifications to code with no external callers
- **Self-contained features**: New endpoint/handler added with its own tests
- **Configuration/docs only**: Changes to config files, docs, or build scripts

### Decision Workflow

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

Before analyzing, fetch all existing PR threads/comments to avoid duplicate feedback. Use the patterns from the loaded platform reference.

Summarize existing feedback so you can check against it in Phase 5:
- Which files have comments
- What issues were raised
- Who raised them
- Thread status (active, resolved, etc.)

---

## Phase 5: Analyze Changes

For each changed file, read the **full source version** (not just diff hunks) to understand context. If a full repo clone was obtained in Phase 3, use it to explore callers, related files, and broader architectural context via `Agent` subagents (`subagent_type: Explore`).

### Review Checklist

**Bug categories:**
- Syntax/typo errors (mismatched brackets, wrong string formats)
- Logic errors (wrong conditions, off-by-one, dead code paths)
- Missing null/error handling at system boundaries
- Breaking changes to public/internal APIs
- Resource leaks (unclosed connections, missing dispose)

**Design categories:**
- Code duplication that risks drift (DRY violations)
- Unnecessary complexity (redundant calls, over-engineering)
- Inconsistency with existing codebase patterns
- Poor naming or misleading abstractions

**Process categories:**
- TODO/HACK/NOT YET comments that should be resolved pre-merge
- Test coverage gaps (check pipeline status if available)
- Unrelated changes mixed into the PR
- Configuration or secret exposure

### Verification Discipline

**For every potential finding, you MUST verify all three conditions:**
1. **In the diff**: The issue is in lines actually changed by this PR (merge-base comparison). Check the diff output — if the line exists in both base and source versions, it is NOT a PR change.
2. **Not already flagged**: Compare against existing reviewer comments from Phase 4.
3. **Real issue**: Not a misunderstanding of codebase context. When uncertain, read surrounding code for clarification. If you have the full repo, trace callers and dependencies to confirm.

If any condition fails, **discard the finding**. False positives erode reviewer trust.

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

Use `AskUserQuestion` to ask:
1. Which findings to post as PR comments (by number)
2. Any findings to adjust or drop
3. Attribution text for comments (default: suggest "(Comment by {name} and Claude)")

---

## Phase 7: Post Comments to PR

For each approved finding, post an inline threaded comment using the patterns from the loaded platform reference.

Include the agreed attribution text at the end of each comment body.

### After Posting

Report which comments were posted successfully and provide links where available. If any fail, report the error and offer to retry.

---

## Error Handling

- If authentication fails, guide the user through `az login` (Azure DevOps) or `gh auth login` (GitHub)
- If the PR URL cannot be parsed, ask the user to provide the correct URL format
- If file downloads fail for specific files, skip them and note which files could not be reviewed
- If comment posting fails, show the error and offer alternatives (e.g., copy comment text to clipboard)
- If repo clone fails, fall back to reviewing with changed files only and inform the reviewer
