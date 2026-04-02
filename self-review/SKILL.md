---
name: self-review
description: Automated self-review loop for code changes. Accepts a PR URL, a local git repo path, or defaults to the current directory. Spawns a fresh review agent (with no prior context) to find bugs, design issues, and code quality problems, then triages findings, fixes valid issues, and iterates until the review is clean. Use this skill when the user wants to self-review their PR or branch, do an automated code review cycle, have Claude review and fix its own code, or iterate on code quality before requesting human review. Invoke with /self-review [pr-url-or-repo-path] [--max-rounds <N>]
allowed-tools: Bash, Read, Grep, Glob, Agent, AskUserQuestion
user-invocable: true
---

# Self-Review Skill

You are the **coordinator** of an automated self-review loop. You orchestrate two specialized agents, triage findings, interact with the user, and manage the iteration lifecycle.

## Agent Architecture

| Agent | Type | Role | Can modify files? |
|-------|------|------|-------------------|
| **Coordinator** (you) | main | Orchestrate loop, triage findings, interact with user, gate exits, commit | No (only via fix agent) |
| **Review agent** | `Explore` | Analyze diff, report findings | No (read-only) |
| **Fix agent** | `general-purpose` | Apply code fixes, run tests | Yes |

The key insight is that the review agent has **zero context** about prior decisions — it reviews the diff cold, just like a human reviewer seeing the code for the first time. This surfaces issues that the author (you, with full context) might overlook due to familiarity bias.

**All reviews happen locally.** Whether the input is a PR URL or a local branch, the review always runs against a local git diff. If the input is a PR URL, the PR changes are checked out locally first.

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- **First positional arg** (optional): A PR URL, or a local folder path to a git repository. If omitted, use the current working directory.
- `--max-rounds <N>`: Maximum review-fix iterations (default: 10). The loop may exit earlier if the review is clean.

### Detecting input type

1. If the arg starts with `http://` or `https://` — treat it as a **PR URL**.
2. If the arg is a filesystem path (absolute or relative) that exists as a directory — treat it as a **local git repo path**. `cd` into it.
3. If no arg is provided — use the **current working directory**.

## Phase 1: Set Up Local Working Copy

The goal of this phase is to ensure we have a local git repo with the changes to review checked out as the current branch.

### Path A: PR URL provided

1. **Parse the PR URL** to extract repository and PR identifiers:
   - **GitHub**: `https://github.com/{owner}/{repo}/pull/{number}` — extract owner, repo, number
   - **Azure DevOps**: `https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}` — extract org, project, repo, id

2. **Check if a local clone already exists.** Look at the current working directory (or any parent): does `git remote -v` match the PR's repository? If yes, use it. If not, use `AskUserQuestion` to ask:
   - "Provide path to existing local clone"
   - "Clone the repository" — shallow clone (`--depth 1`) the source branch into a temp directory

3. **Check out the PR's source branch.** Fetch and check out the branch so the local diff matches the PR:
   - **GitHub**: `gh pr checkout <number>` (if `gh` is available) or fetch the source branch manually
   - **Azure DevOps**: `git fetch origin <source-branch> && git checkout <source-branch>`

4. **Identify the target branch** from the PR metadata (the branch the PR merges into). This becomes the base branch for diffing.

### Path B: Local path or CWD

1. Verify it is a git repository: `git -C <path> rev-parse --is-inside-work-tree`. If not, inform the user and stop.

2. **Detect the base branch** by checking which of these remote branches exist (use `git rev-parse --verify`), in order of priority:
   - `origin/main`
   - `origin/master`
   - `origin/develop`
   - `origin/working`
   - `origin/release`

3. If multiple candidates exist, or if the detected base seems wrong, use `AskUserQuestion` to confirm: "I detected `origin/main` as the base branch. Is this correct?"

### Common: Compute merge base and validate

1. Get the current branch name: `git branch --show-current`
2. Compute the merge base: `git merge-base <base-branch> HEAD`
3. Verify the diff is non-empty: `git diff <merge-base>...HEAD --stat`. If empty, inform the user there are no changes to review and stop.

### Log the detected configuration

```
Repository: <path>
Branch: <current-branch>
Base branch: origin/main
Merge base: abc1234
Changed files: N
```

---

## Phase 2: Review-Fix Loop

Maintain two lists across iterations:
- **Won't-fix list**: Findings triaged as acceptable (by-design, pre-existing, out-of-scope, or too minor). Passed to subsequent review rounds so the reviewer doesn't re-raise them.
- **Fixed list**: Findings that were addressed. Confirms fixes worked if they don't reappear.

**Log all decisions.** Every triage verdict must include the reasoning. This log is shown to the user at each round and in the final summary.

### For each round (up to max-rounds):

#### Step 1: Spawn the review agent

Launch a **read-only** review agent using `Agent` with `subagent_type: Explore`. The Explore agent can only read files, search code, and run read-only shell commands — it cannot edit files, write files, or post comments. This enforces a clean separation: the review agent observes and reports; the main agent decides and acts.

Prompt for the review agent:

```
You are a fresh code reviewer with no prior context about this code.
Your role is READ-ONLY: analyze the code and report findings. Do NOT
modify any files or post comments anywhere.

Review the diff of branch <current-branch> against <merge-base> in the
git repository at <repo-path>.

Run: git diff <merge-base>...HEAD

First, read the review checklist at:
  <this-skill-directory>/references/review-checklist.md
Apply its categories, severity levels, and verification discipline to
every changed file.

Focus ONLY on files changed in this branch. Read the full source of each
changed file (not just diff hunks) to understand context.

The following issues have already been reviewed and accepted as won't-fix:
<won't-fix list — numbered, with file/line and brief reason>

Return any NEW findings not covered above. If you find no new issues,
say "No new issues found."

For each finding, provide:
- File path and line number
- Severity: bug, design, style, nit, process, security
- Description of the issue
- Suggested fix if applicable
```

#### Step 2: Triage findings (coordinator)

The coordinator (you) triages each finding. This is your job — not the review agent's or the fix agent's — because triage requires conversation context, knowledge of prior design decisions, and user interaction.

For each finding, classify it into one of:

| Verdict | Criteria | Action |
|---------|----------|--------|
| **Fix** | Valid bug, design issue, or meaningful improvement | Apply the fix |
| **Won't fix** | By-design, pre-existing, out-of-scope, or too minor | Add to won't-fix list with reason |
| **Already fixed** | Reviewer flagged something already addressed | Ignore |
| **Invalid** | Reviewer misunderstood the code | Add to won't-fix list with explanation |
| **Uncertain** | Not sure whether this is valid or worth fixing | Ask the user |

**When uncertain, ask the user.** Use `AskUserQuestion` to present the finding and let the user decide:
- "Fix it" — apply the fix
- "Won't fix" — add to won't-fix list
- "Skip for now" — don't fix, don't add to won't-fix (may come back next round)

Present the triage to the user as a summary table:

```
## Round N Review Summary

| # | Severity | File:Line | Description | Verdict | Reason |
|---|----------|-----------|-------------|---------|--------|
| 1 | bug | Foo.cs:42 | Null ref... | Fix | Valid — missing null check |
| 2 | design | Bar.cs:15 | Missing... | Won't fix | Pre-existing behavior |
| 3 | nit | Baz.cs:99 | Naming... | Won't fix | Too minor for this PR |
| 4 | design | Qux.cs:7 | Perf concern | Uncertain | Asked user |
```

#### Step 3: Spawn the fix agent

If there are findings marked **Fix**, launch a **general-purpose** Agent to apply them. The fix agent has full read-write access. Give it the specific list of fixes to apply — nothing more.

Prompt for the fix agent:

```
You are a code fix agent. Apply the following fixes to the git repository
at <repo-path>. For each fix, read the relevant file to understand context,
then apply the change.

Fixes to apply:
<numbered list of findings marked Fix, each with file, line, description,
and suggested fix>

After applying all fixes, run the test suite:
<test-command, e.g. dotnet test, npm test, pytest, etc.>

If tests fail, investigate and fix the failures.

Report back:
- Which fixes were applied successfully
- Any test failures and how they were resolved
- Any fixes you could not apply (with reason)

Do NOT make changes beyond the listed fixes. Do NOT refactor or improve
surrounding code.
```

Log the fix agent's results: what was changed, which file/line, and why.

#### Step 4: Check exit conditions

Exit the loop if ANY of these conditions are met:
- The review agent returned "No new issues found"
- All findings in this round were triaged as won't-fix, invalid, or nit-level
- Maximum rounds reached (default: 10)
- No fixes were applied in this round (all findings were triaged as acceptable)

If exiting, proceed to Phase 3. Otherwise, loop back to Step 1.

---

## Phase 3: Verify and Commit

After the loop completes:

1. **Run the test suite one final time** to confirm all changes work together. If tests fail, fix the failures before proceeding.
2. Check if any files were modified: `git status`
3. If changes exist:
   - Show the user a summary of all fixes applied across all rounds, with file paths and descriptions
   - Use `AskUserQuestion` to ask what to do:
     - **"Commit and push"**: Stage changed files, commit with a descriptive message, and push
     - **"Commit only"**: Stage and commit without pushing
     - **"Leave uncommitted"**: Leave changes in the working tree for manual review
3. If no changes were made, inform the user that the review found no actionable issues.

### Commit message format

```
Address self-review findings

- <brief description of fix 1>
- <brief description of fix 2>
...

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Phase 4: Final Summary

Present a complete decision log and summary:

```
## Self-Review Complete

**Rounds**: N
**Total findings across all rounds**: X
**Fixed**: Y
**Won't fix**: Z
**User decisions**: W

### Fixes Applied
1. [File:Line] Description of fix — Reason
2. ...

### Won't Fix (with reasons)
1. [File:Line] Description — Reason (by-design / pre-existing / out-of-scope / ...)
2. ...

### User Decisions
1. [File:Line] Description — User chose: fix/won't fix/skip

**Review status**: Clean / Minor items remaining
```

List any remaining won't-fix items so the user can decide if any need attention from a human reviewer.

---

## Decision-Making Guidelines

- **Be conservative with fixes.** Only mark something as "Fix" if you are confident it is a genuine improvement. When in doubt, mark it "Uncertain" and ask the user.
- **Don't over-fix.** The goal is to catch real issues, not to gold-plate the code. Nits and style preferences should generally be won't-fixed unless the user has expressed a preference.
- **Respect prior decisions.** If this conversation involved making deliberate design choices (e.g., using string interpolation instead of a serializer), those are by-design won't-fixes.
- **Log everything.** Every finding and every verdict should be traceable. The user should be able to look at the final summary and understand exactly what was found, what was done about it, and why.

## Tips for Effective Self-Review

- The review agent intentionally has no context about design decisions — this is a feature, not a bug. It catches things that look wrong to fresh eyes.
- Won't-fix items often reveal places where a code comment would help future readers understand the rationale.
- If the same finding keeps coming back across rounds despite being won't-fixed, consider whether the code could be restructured to make the intent clearer.
- The skill works best when tests exist — it can verify fixes don't break anything.
