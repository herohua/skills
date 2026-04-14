---
name: code-coverage-policy
description: |
  Check and enforce code coverage branch policies on Azure DevOps repositories.
  Use when the user requests to:
  (1) Check existing code coverage policies on one or more repos
  (2) Add a code coverage status check policy to a branch
  (3) Update policy settings (blocking, enabled, threshold) on existing policies
  (4) Configure the azurepipelines-coverage.yml file for PR diff coverage
  (5) Bulk-enforce coverage policies across many repos at once
  Triggers include: any mention of 'code coverage policy', 'branch policy', 'coverage status check',
  'azurepipelines-coverage.yml', 'diff coverage target', or requests to enforce, add, or audit
  code coverage policies in Azure DevOps.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, AskUserQuestion, mcp__plugin_microsoft-docs_microsoft-learn__microsoft_docs_search, mcp__plugin_microsoft-docs_microsoft-learn__microsoft_docs_fetch
user-invocable: true
---

# Code Coverage Branch Policy Skill

Manage code coverage branch policies on Azure DevOps repositories — check existing policies, add new status check policies, update settings, and configure PR diff coverage thresholds. Supports single-repo and bulk operations.

## Prerequisites

**Permissions required**: The `add` and `update` actions require the **Edit policies** permission at the repository or branch level. Most engineers do not have this by default.

Groups that have **Edit policies** by default:
- **Project Administrators**

Groups that do **not** have it by default but can be granted it:
- **Build Administrators**, **Contributors**, or any custom security group

To check your permissions: go to **Project Settings > Repositories > {repo} > Security**, find your user or group, and look for **Edit policies = Allow**.

The `check` action (read-only) works with standard **Read** permissions (Contributors, Build Admins, etc.). If you get a 403 error on mutation operations, ask a Project Administrator to grant **Edit policies** on the target repository.

See [references/troubleshooting.md](references/troubleshooting.md) for more details on permission issues.

## When to Use

- User wants to see what code coverage policies exist on a repo or set of repos
- User wants to add a code coverage status check policy to block PRs without sufficient coverage
- User wants to update settings on an existing code coverage policy (e.g., enabled/disabled)
- User wants to create or update the `azurepipelines-coverage.yml` file for PR diff coverage
- User wants to enforce coverage policies across many repos in bulk

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- **First positional arg**: Action — one of `check`, `add`, `update`, `configure-yaml`, or omit to interactively choose
- `--org <org>`: Azure DevOps organization name
- `--project <project>`: Project name
- `--repo <repo>`: Repository name or ID. Accepts **comma-separated list** for bulk operations (e.g., `--repo Repo1,Repo2,Repo3`)
- `--branch <branch>`: Branch to apply policy to. If omitted, the tool automatically resolves the default branch for each repo via the API (`defaultBranch` field from the repositories endpoint) — no need to specify `main`, `live`, etc.
- `--pipeline <name>`: Pipeline name (used for status naming convention `{pipeline}/codecoverage`)
- `--target <percent>`: Diff coverage target percentage (default: 60)
- `--blocking`: Make the policy required (blocking)
- `--optional`: Make the policy optional (non-blocking)

If required parameters are missing, use `AskUserQuestion` to collect them interactively.

---

## High-Level Workflow

### Phase 1: Authentication

All Azure DevOps API calls require an OAuth access token. See [references/azure-devops-api.md](references/azure-devops-api.md) for full API patterns.

```bash
TOKEN=$(az account get-access-token \
  --resource 499b84ac-1321-427f-aa17-267ca6975798 \
  --query accessToken -o tsv)
```

**Pitfall**: On Windows, tokens do not persist across Bash tool invocations. Re-fetch the token at the top of every Bash call.

### Phase 2: Execute Action

Route to the appropriate action based on user input. If no action is specified, present an interactive menu:

1. **Check existing policies** — See what code coverage policies are configured
2. **Add a code coverage policy** — Create a new status check policy
3. **Update an existing policy** — Change blocking/enabled settings
4. **Configure coverage YAML** — Create/update the `azurepipelines-coverage.yml` file

### Phase 3: Verify

After any mutation (`add`, `update`, `configure-yaml`), re-run `check` to confirm the change took effect and report results to the user.

---

## Performance: Bulk Operations Strategy

Azure DevOps does NOT have a general-purpose batch API for policy operations. Use a **fetch-once, process-locally** pattern:

1. **Fetch all data in a single Bash call**: Download repos list, all policy configurations, and policy types to local files in one Bash invocation (one token fetch, three parallel curls).
2. **Process with Python**: Use a single Python script to cross-reference repos, policies, and branches.
3. **Write updates to local files**: Generate all JSON payloads locally.
4. **Execute updates in parallel**: Use `curl` background jobs (`&`) to PUT/POST multiple policy updates concurrently in a single Bash call.

### Example: Bulk fetch pattern

```bash
TOKEN=$(az account get-access-token \
  --resource 499b84ac-1321-427f-aa17-267ca6975798 \
  --query accessToken -o tsv)
WORKDIR="$(pwd)"

# Fetch all data in parallel
curl -s -H "Authorization: Bearer $TOKEN" "$ORG/$PROJECT/_apis/git/repositories?api-version=7.1" \
  -o "$WORKDIR/repos.json" &
curl -s -H "Authorization: Bearer $TOKEN" "$ORG/$PROJECT/_apis/policy/configurations?api-version=7.1" \
  -o "$WORKDIR/policies.json" &
curl -s -H "Authorization: Bearer $TOKEN" "$ORG/$PROJECT/_apis/policy/types?api-version=7.1" \
  -o "$WORKDIR/types.json" &
wait
```

Then process locally in Python — no additional API calls needed for `check`. For `add`/`update`, generate JSON files and batch the curl calls.

### Windows file path pitfalls

- **`$TEMP` with backslashes**: Paths like `C:\Users\...\Temp` break `curl -d @path`. Use forward-slash paths in the working directory instead.
- **Python vs bash paths**: `/tmp/` paths from bash are not accessible in Python on Windows. Use absolute paths with forward slashes that both can resolve.
- **`jq` may not be available**: Use `python -c "..."` for JSON processing instead of `jq`.

---

## Branch Validation

**Critical**: Before adding or enforcing a policy on a branch, always verify the branch exists.

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/$PROJECT/_apis/git/repositories/$REPO_ID/refs?filter=heads/$BRANCH&api-version=7.1"
```

If `value[]` is empty, the branch does not exist. **Skip it** and report to the user. Do NOT create or enforce policies on non-existent branches.

---

## Action: `check` — Inspect Current Policies

Supports a single repo or a **list of repos**. When given multiple repos, produce a summary table.

### Steps

1. **Fetch all data** (once) — Download repos list and all policy configurations (see Bulk Operations Strategy).
2. **Resolve repository IDs** — Match repo names against the repos list. Report any repos not found.
3. **Cross-reference policies** — For each repo, filter for:
   - Build validation policies scoped to that repo
   - Status check policies with `statusName == "codecoverage"` scoped to that repo
4. **Present findings**

For a **single repo**, show a detailed table:

```
| # | Type   | Name/Display       | Blocking | Enabled | Branch          |
|---|--------|--------------------|----------|---------|-----------------|
| 1 | Build  | CI Pipeline        | Yes      | Yes     | refs/heads/main |
| 2 | Status | CI/codecoverage    | No       | Yes     | refs/heads/main |
```

For **multiple repos**, show a summary table:

```
| Repo       | Default Branch | Build Policy | Coverage Status | Enforcement          |
|------------|---------------|-------------|----------------|---------------------|
| MyRepo     | main          | main        | main           | ENFORCED (blocking) |
| OtherRepo  | develop       | develop     | None           | Not configured      |
```

Enforcement states:
- **ENFORCED (blocking)** — status check exists and is blocking
- **Advisory (non-blocking)** — status check exists but is non-blocking
- **Not configured** — no status check policy for code coverage
- **Not configured (no build)** — no build or status policies at all

---

## Action: `add` — Add Code Coverage Status Check Policy

### Prerequisites

- A build pipeline must already exist that publishes code coverage results
- The pipeline must use `PublishCodeCoverageResults@2` (V2, not V1)

### Steps

1. **Validate branch existence** — Verify the target branch exists (see Branch Validation). Skip non-existent branches.
2. **Determine status name** — Code coverage status follows the convention: `{pipeline-name}/codecoverage`. If `--pipeline` is not specified, look up build definitions and ask the user.
3. **Resolve policy type ID** — Query the policy types API to get the Status policy type ID.
4. **Create the status check policy** — Write JSON payload to a file, then POST:

```json
{
  "isEnabled": true,
  "isBlocking": true,
  "type": { "id": "{statusPolicyTypeId}" },
  "settings": {
    "statusName": "codecoverage",
    "statusGenre": "{pipeline-name}",
    "authorId": "",
    "invalidateOnSourceUpdate": true,
    "displayName": "Code Coverage Policy",
    "scope": [
      {
        "repositoryId": "{repoId}",
        "refName": "refs/heads/{branch}",
        "matchKind": "Exact"
      }
    ]
  }
}
```

**Key settings:**
- `statusName`: Always `codecoverage` (matches what the pipeline posts)
- `statusGenre`: The pipeline name (status context is `{genre}/{name}`)
- `isBlocking`: `true` for required, `false` for optional
- `authorId`: Empty string = any identity can post the status

5. **Verify** — Re-run `check` to confirm the policy was created.

**Pitfall**: Do NOT include `policyApplicability` as a string (e.g., `"default"`). The API expects a numeric enum or null. Omit the field entirely.

---

## Action: `update` — Update an Existing Policy

### Steps

1. **Find the policy** — Run `check` to list policies and identify the one to update.
2. **Validate branch existence** — If the policy targets a specific branch, verify it exists.
3. **Get current configuration** — GET the full policy configuration.
4. **Modify and PUT** — Apply requested changes, write modified JSON to a file, then PUT.

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X PUT -H "Content-Type: application/json" \
  "$ORG/$PROJECT/_apis/policy/configurations/$POLICY_ID?api-version=7.1" \
  -d @"$WORKDIR/cc_update_$POLICY_ID.json"
```

**Pitfall**: PUT replaces the entire configuration. Always GET the current config first, modify it, then PUT it back.

### Bulk update pattern

```bash
TOKEN=$(az account get-access-token \
  --resource 499b84ac-1321-427f-aa17-267ca6975798 \
  --query accessToken -o tsv)

for PID in $POLICY_IDS; do
  curl -s -H "Authorization: Bearer $TOKEN" -X PUT -H "Content-Type: application/json" \
    "$ORG/$PROJECT/_apis/policy/configurations/$PID?api-version=7.1" \
    -d @"$WORKDIR/cc_update_$PID.json" &
done
wait
```

5. **Verify** — Fetch the updated policies to confirm changes.

---

## Action: `configure-yaml` — Configure Coverage YAML

Creates or updates `azurepipelines-coverage.yml` at the repository root.

### Steps

1. **Check if file exists** — Look for `azurepipelines-coverage.yml` at the repo root. Ask for the local repo path if needed.
2. **Create or update the file**:

```yaml
coverage:
  status:
    comments: on
    diff:
      target: 60%
```

Override with `--target` to set a different threshold.

3. **Instruct next steps** — Tell the user:
   - Commit and push `azurepipelines-coverage.yml` to the default branch
   - The pipeline must publish coverage via `PublishCodeCoverageResults@2` (V2)
   - After the next PR build, the code coverage status will appear

---

## Error Handling

| Problem | Cause | Solution |
|---------|-------|----------|
| 403 Forbidden | Missing permissions | User needs **Project Administrators** or repo-level **Edit policies** permission |
| Policy type not found | Type ID varies by org | Always query the types API first — never hardcode |
| Policy never evaluates | Status name mismatch | Verify `statusGenre/statusName` matches what the pipeline posts (`{pipeline-name}/codecoverage`) |
| Coverage status stuck | V1 task, >100 files, or multiple policies | Upgrade to V2, reduce PR size, or remove duplicate policies |
| Branch not found | Branch deleted or typo | Validate via refs API before creating policies |

For a full troubleshooting guide, see [references/troubleshooting.md](references/troubleshooting.md).

---

## Best Practices

1. **Always validate branches** before creating or enforcing policies. Skip non-existent branches and report them.
2. **Fetch once, process locally** for bulk operations — minimizes API calls and token refreshes.
3. **Write JSON payloads to files** and use `curl -d @file.json` — avoids shell escaping issues.
4. **Use Python for JSON processing** instead of `jq` — more reliable cross-platform.
5. **Re-fetch tokens per Bash call** on Windows — tokens don't persist across shell invocations.
6. **Use forward-slash paths** even on Windows — avoids breakage with `curl`, Python, and temp file operations.
7. **Never include `policyApplicability`** as a string — the API expects a numeric enum or null.
8. **PUT replaces entirely** — always GET the existing config, modify it, then PUT the full object.
9. **Verify after mutations** — always re-run `check` after `add` or `update` to confirm success.

## Reference Files

| File | Purpose |
|------|---------|
| [references/azure-devops-api.md](references/azure-devops-api.md) | REST API reference: endpoints, authentication, payload formats, known pitfalls |
| [references/troubleshooting.md](references/troubleshooting.md) | Common issues and solutions for code coverage policies |
