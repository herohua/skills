---
name: code-coverage-policy
description: Check and update branch policies for code coverage on Azure DevOps repositories. Lists existing policies, adds code coverage status check policies, updates policy settings (blocking/enabled/threshold), and configures the azurepipelines-coverage.yml file. Supports bulk operations across multiple repos. Invoke with /code-coverage-policy <action> [options]. Actions: check, add, update, configure-yaml.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, AskUserQuestion, mcp__plugin_microsoft-docs_microsoft-learn__microsoft_docs_search, mcp__plugin_microsoft-docs_microsoft-learn__microsoft_docs_fetch
user-invocable: true
---

# Code Coverage Branch Policy Skill

You help users check and enforce code coverage branch policies on Azure DevOps repositories. This skill covers both:
1. **Branch policies** (status check policies that block PR completion based on code coverage)
2. **Pipeline coverage configuration** (the `azurepipelines-coverage.yml` file that controls diff coverage thresholds)

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- **First positional arg**: Action — one of `check`, `add`, `update`, `configure-yaml`, or omit to interactively choose
- `--org <org>`: Azure DevOps organization name (e.g., `myorg`)
- `--project <project>`: Project name (e.g., `MyProject`)
- `--repo <repo>`: Repository name or ID. Can be a **comma-separated list** for bulk operations (e.g., `--repo Repo1,Repo2,Repo3`)
- `--branch <branch>`: Branch to apply policy to (default: default branch of each repo)
- `--pipeline <name>`: Pipeline name (used for code coverage status naming convention `{pipeline}/codecoverage`)
- `--target <percent>`: Diff coverage target percentage (default: 70)
- `--blocking`: Make the policy required (blocking)
- `--optional`: Make the policy optional (non-blocking)

If required parameters are missing, use `AskUserQuestion` to collect them interactively.

---

## Authentication

All Azure DevOps API calls require authentication. Read `references/azure-devops-api.md` for detailed API patterns.

```bash
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)
```

**Pitfall**: On Windows, tokens do not persist across Bash calls. Re-fetch the token in every Bash invocation.

---

## Performance: Bulk Operations Strategy

Azure DevOps does NOT have a general-purpose batch API for policy operations. To handle multiple repos efficiently:

### Fetch-once, process-locally pattern

1. **Fetch all data in a single Bash call**: Download repos list, all policy configurations, and policy types to local temp files in one Bash invocation (one token fetch, three parallel curls).
2. **Process with Python**: Use a single Python script to cross-reference repos, policies, branches, and produce results.
3. **Write updates to temp files**: Generate all JSON payloads locally.
4. **Execute updates in parallel**: Use `curl` background jobs (`&`) or `xargs -P` to PUT/POST multiple policy updates concurrently in a single Bash call.

### Example: Bulk fetch pattern

```bash
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)
WORKDIR="$(pwd)"  # Use a path accessible to both bash and Python

# Fetch all data in parallel
curl -s -u ":$TOKEN" "$ORG/{project}/_apis/git/repositories?api-version=7.1" -o "$WORKDIR/repos.json" &
curl -s -u ":$TOKEN" "$ORG/{project}/_apis/policy/configurations?api-version=7.1" -o "$WORKDIR/policies.json" &
curl -s -u ":$TOKEN" "$ORG/{project}/_apis/policy/types?api-version=7.1" -o "$WORKDIR/types.json" &
wait
```

Then process all locally in Python — no additional API calls needed for `check`. For `add`/`update`, generate JSON files and batch the curl calls.

### Windows file path pitfalls

- **`$TEMP` with backslashes**: Paths like `C:\Users\...\Temp` break `curl -d @path`. Use forward-slash paths in the working directory instead .
- **Python vs bash paths**: `/tmp/` paths from bash are not accessible in Python on Windows. Use absolute paths with forward slashes that both can resolve.
- **`jq` may not be available**: Use `python -c "..."` for JSON processing instead of `jq`.

---

## Branch Validation

**Critical**: Before adding or enforcing a policy on a branch, always verify the branch exists.

```bash
# Check if a branch exists
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/git/repositories/{repoId}/refs?filter=heads/{branchName}&api-version=7.1"
```

If `value[]` is empty, the branch does not exist. **Skip it** and report to the user. Do NOT create or enforce policies on non-existent branches.

When processing multiple repos, fetch refs per repo only when needed (for `add`/`update` actions). For `check`, branch existence is informational but not blocking.

---

## Action: `check` — Inspect Current Policies

Supports a single repo or a **list of repos**. When given multiple repos, produce a summary table.

### Step 1: Fetch all data (once)

Download repos list and all policy configurations to temp files (see Bulk Operations Strategy above).

### Step 2: Resolve Repository IDs

Match repo names from the argument against the repos list. Report any repos that are not found.

### Step 3: Cross-reference policies

For each repo, filter the policies data for:
- **Build validation policies** scoped to that repo
- **Status check policies** with `statusName == "codecoverage"` scoped to that repo

### Step 4: Present findings

For a **single repo**, show detailed policy info:
```
| # | Type   | Name/Display       | Blocking | Enabled | Branch          |
|---|--------|--------------------|----------|---------|-----------------|
| 1 | Build  | CI Pipeline        | Yes      | Yes     | refs/heads/main |
| 2 | Status | CI/codecoverage    | No       | Yes     | refs/heads/main |
```

For **multiple repos**, show a summary table:
```
| Repo          | Default Branch | Build Policy | Coverage Status | Enforcement          |
|---------------|---------------|-------------|----------------|---------------------|
| MyRepo        | main          | main        | main           | ENFORCED (blocking) |
| OtherRepo     | develop       | develop     | None           | Not configured      |
```

Enforcement states:
- **ENFORCED (blocking)** — status check exists and is blocking
- **Advisory (non-blocking)** — status check exists but is non-blocking
- **Not configured** — no status check policy for code coverage (build policy may exist)
- **Not configured (no build)** — no build or status policies at all

---

## Action: `add` — Add Code Coverage Status Check Policy

### Prerequisites
- A build pipeline must already exist that publishes code coverage results
- The pipeline must have run at least once to post the code coverage status

### Step 1: Validate branch existence

**Before creating any policy**, verify the target branch exists on the repository (see Branch Validation). Skip non-existent branches and report them.

### Step 2: Determine Status Name

Code coverage status follows the naming convention: `{pipeline-name}/codecoverage`

If `--pipeline` is not specified, look up build definitions for the repo and ask the user.

### Step 3: Resolve Policy Type ID

Query the policy types API to get the Status policy type ID for this organization.

### Step 4: Create the Status Check Policy

Write JSON payload to a file in the working directory, then POST:

```json
{
  "isEnabled": true,
  "isBlocking": true,
  "type": {
    "id": "{statusPolicyTypeId}"
  },
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

**Important settings:**
- `statusName`: Always `codecoverage` (this is what the pipeline posts)
- `statusGenre`: The pipeline name (the status context is `{genre}/{name}`)
- `isBlocking`: `true` for required, `false` for optional
- `invalidateOnSourceUpdate`: `true` to reset status when the source branch is updated
- `authorId`: Empty string means any identity can post the status

**Pitfall**: Do NOT include `policyApplicability` as a string (e.g., `"default"`). The API expects a numeric enum or null. Omit the field entirely to get the default behavior (apply on PR creation).

### Step 5: Verify

Re-run the `check` action to confirm the policy was created.

---

## Action: `update` — Update an Existing Policy

### Step 1: Find the Policy

Run the `check` action to list policies. Identify policies to update.

### Step 2: Validate branch existence

If the policy targets a specific branch, verify it exists. If the branch doesn't exist, **skip it** and report it to the user rather than modifying the policy.

### Step 3: Get Current Policy Configuration

```bash
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/policy/configurations/{policyId}?api-version=7.1"
```

### Step 4: Modify and Update

Apply the requested changes. Write the modified JSON to a file in the working directory, then PUT:

```bash
curl -s -u ":$TOKEN" \
  -X PUT \
  -H "Content-Type: application/json" \
  "$ORG/{project}/_apis/policy/configurations/{policyId}?api-version=7.1" \
  -d @"$WORKDIR/cc_update_{policyId}.json"
```

**Pitfall**: The `PUT` request must include the full policy configuration, not just the changed fields. Always read the existing config first and modify it.

### Bulk update pattern

When updating multiple policies (e.g., enforcing across several repos):

```bash
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# Fetch all policies to update, modify in Python, write individual JSON files
# Then run parallel PUTs:
for PID in $POLICY_IDS; do
  curl -s -u ":$TOKEN" -X PUT -H "Content-Type: application/json" \
    "$ORG/{project}/_apis/policy/configurations/$PID?api-version=7.1" \
    -d @"$WORKDIR/cc_update_$PID.json" &
done
wait
# Collect and report results
```

### Step 5: Verify

Fetch the updated policies to confirm changes.

---

## Action: `configure-yaml` — Configure Coverage YAML

This action creates or updates the `azurepipelines-coverage.yml` file at the root of the repository. This file controls:
- Whether diff coverage comments are posted on PRs
- The diff coverage target percentage

### Step 1: Check if File Exists

If the user has a local clone of the repo, check for `azurepipelines-coverage.yml` at the repo root. If not, ask for the local repo path or offer to download it via API.

### Step 2: Create or Update the File

```yaml
coverage:
  status:
    comments: on
    diff:
      target: {target}%
```

Default target is 70%. The user can override with `--target`.

### Step 3: Instruct Next Steps

Tell the user:
1. Commit and push the `azurepipelines-coverage.yml` file to the default branch
2. The pipeline must publish code coverage via `PublishCodeCoverageResults@2` task (V2, not V1)
3. After the next PR build, the code coverage status will be posted

---

## Interactive Mode (no action specified)

If no action is provided, present options:

1. **Check existing policies** — See what code coverage policies are configured
2. **Add a code coverage policy** — Create a new status check policy for code coverage
3. **Update an existing policy** — Change blocking/enabled settings on an existing policy
4. **Configure coverage YAML** — Create/update the `azurepipelines-coverage.yml` file

---

## Error Handling

- **Authentication failure**: Guide user through `az login` and ensure they have `Edit policies` permission on the repository
- **Policy type not found**: The status policy type ID varies by org. Always query the types API first.
- **Policy creation fails with 403**: User lacks `Edit policies` permissions. They need Project Admin or explicit policy edit permissions.
- **Status name mismatch**: If the policy is created but never evaluates, verify the `statusGenre/statusName` matches what the pipeline posts. The naming convention is `{pipeline-name}/codecoverage`.
- **Coverage status stuck**: Common causes include incorrect branch policy name format, using PublishCodeCoverage V1 instead of V2, PRs with 100+ files, or multiple coverage policies configured.
- **Non-existent branch**: Always validate branch existence before creating/enforcing policies. Skip and report non-existent branches.

---

## Troubleshooting Reference

Read `references/troubleshooting.md` for common issues and solutions when code coverage policies don't work as expected.
