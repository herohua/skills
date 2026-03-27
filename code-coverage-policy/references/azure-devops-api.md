# Azure DevOps REST API Reference for Code Coverage Policies

Quick reference for API calls used to manage code coverage branch policies. All calls require authentication.

## Authentication

```bash
# Get token via Azure CLI
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)

# All curl calls use basic auth with empty username
curl -s -u ":$TOKEN" ...
```

The resource GUID `499b84ac-1321-427f-aa17-267ca6975798` is the Azure DevOps resource identifier.

**Pitfall**: On Windows, each `Bash` tool invocation starts a fresh shell. Always re-fetch `TOKEN` at the top of each Bash command.

## Base URL

```
ORG="https://dev.azure.com/{organization}"
```

---

## List Repositories

```bash
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/git/repositories?api-version=7.1"
```

Response: `value[]` array. Key fields per repository:
- `id` — Repository GUID (needed for policy scope)
- `name` — Repository name
- `defaultBranch` — e.g., `refs/heads/main`
- `project.id` — Project GUID

---

## Policy Types

```bash
# List all policy types available in the project
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/policy/types?api-version=7.1"
```

Response: `value[]` array. Key fields:
- `id` — Policy type GUID
- `displayName` — Human-readable name (e.g., "Status", "Build", "Minimum approval count")
- `description` — Detailed description

### Common Policy Type IDs

These are the **typical** IDs but they can vary by organization. Always verify via the API.

| Policy Type | Typical ID |
|---|---|
| Minimum approval count | `fa4e907d-c16b-4a4c-9dfa-4906e5d171dd` |
| Build | `0609b952-1397-4640-95ec-e00a01b2c241` |
| Required reviewers | `fd2167ab-b0be-447a-8ec8-39368250530e` |
| Work item linking | `40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e` |
| Status | `cbdc66da-9728-4af8-aada-9a5a32e4a226` |
| Merge strategy | `fa4e907d-c16b-4a4c-9dfa-4916e5d171ab` |
| Git case enforcement | `7ed39669-655c-494e-b4a0-a08b4da0fcce` |
| Max blob size | `2e26e725-8201-4edd-8bf5-978563c34a80` |
| Comment requirements | `c6a1889d-b943-4856-b76f-9e46bb6b0df2` |

---

## Policy Configurations

### List All Policies

```bash
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/policy/configurations?api-version=7.1"
```

Optional query parameters:
- `policyType={typeId}` — Filter by policy type GUID
- `repositoryId={repoId}` — Filter by repository (see pitfall below)
- `refName=refs/heads/{branch}` — Filter by branch
- `$top={n}` — Max results
- `continuationToken={token}` — Pagination (returned in `x-ms-continuationtoken` response **header**, not in the JSON body)

**Pitfall — `repositoryId` filter returns unrelated policies**: The `repositoryId` query parameter does NOT exclusively return policies scoped to that repo. It also returns policies scoped to *other* repos. You MUST verify each returned policy's `settings.scope[].repositoryId` actually matches your target repo (or is `null` for project-wide policies). Failure to do this will cause you to update the wrong policy.

Response: `value[]` array of `PolicyConfiguration` objects:
```json
{
  "id": 42,
  "isEnabled": true,
  "isBlocking": true,
  "type": { "id": "cbdc66da-...", "displayName": "Status" },
  "settings": {
    "statusName": "codecoverage",
    "statusGenre": "MyPipeline",
    "scope": [
      {
        "repositoryId": "repo-guid",
        "refName": "refs/heads/main",
        "matchKind": "Exact"
      }
    ]
  }
}
```

### Get Single Policy

```bash
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/policy/configurations/{configurationId}?api-version=7.1"
```

### Create Policy

```bash
curl -s -u ":$TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  "$ORG/{project}/_apis/policy/configurations?api-version=7.1" \
  -d @/tmp/policy.json
```

Request body structure:
```json
{
  "isEnabled": true,
  "isBlocking": true,
  "type": {
    "id": "{policyTypeId}"
  },
  "settings": {
    ...type-specific settings...,
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

**Scope notes:**
- `repositoryId: null` applies to ALL repositories in the project
- `matchKind`: `"Exact"` for exact branch match, `"Prefix"` for branch prefix (e.g., `refs/heads/release/`)
- Multiple scope entries can be provided in the array

### Update Policy

```bash
curl -s -u ":$TOKEN" \
  -X PUT \
  -H "Content-Type: application/json" \
  "$ORG/{project}/_apis/policy/configurations/{configurationId}?api-version=7.1" \
  -d @/tmp/policy-update.json
```

**Pitfall**: PUT replaces the entire configuration. Always GET the current config first, modify it, then PUT it back. Do not omit fields.

### Delete Policy

```bash
curl -s -u ":$TOKEN" \
  -X DELETE \
  "$ORG/{project}/_apis/policy/configurations/{configurationId}?api-version=7.1"
```

---

## Status Check Policy Settings

The Status policy type (`cbdc66da-9728-4af8-aada-9a5a32e4a226`) uses these settings:

```json
{
  "statusName": "codecoverage",
  "statusGenre": "{pipeline-name}",
  "authorId": "",
  "invalidateOnSourceUpdate": true,
  "displayName": "Code Coverage Policy",
  "filenamePatterns": [
    "/*",
    "!*.md",
    "!*.yml",
    "!*.yaml",
    "!/docs/*"
  ],
  "scope": [...]
}
```

| Setting | Description |
|---|---|
| `statusName` | The status name to match. For code coverage, this is always `codecoverage`. |
| `statusGenre` | The status genre to match. This is the pipeline name. Together, genre + name form the status context `{genre}/{name}`. |
| `authorId` | Identity that must post the status. Empty string = any identity. |
| `invalidateOnSourceUpdate` | `true` = reset status when source branch is updated. |
| `displayName` | Optional friendly name shown in the branch policy UI. |
| `filenamePatterns` | Optional path filter array. When set, the policy only applies to PRs that touch files matching the patterns. Patterns are applied left-to-right; `!` prefix excludes. |

**Pitfall**: Do NOT include `policyApplicability` as a string (e.g., `"default"`). The API expects a numeric enum or null. Omit the field entirely to get the default behavior (apply on PR creation).

### Path Filters (`filenamePatterns`)

The `filenamePatterns` field is an optional array in `settings` that controls which files trigger the policy. When set, the policy only applies if the PR touches files matching the patterns. This works on **all policy types** (Status, Build, Required Reviewers, etc.).

**Syntax:**
- Patterns are applied left-to-right
- `/*` — include all files
- `!*.md` — exclude files matching the pattern (must come after an include)
- `!/docs/*` — exclude an entire folder
- Paths starting with `/` are relative to repo root
- `*` matches any characters within a path segment
- Multiple patterns in the array, each as a separate string

**Example — exclude documentation-only PRs from code coverage:**
```json
"filenamePatterns": [
  "/*",
  "!*.md",
  "!*.yml",
  "!*.yaml",
  "!/docs/*"
]
```

**Example — only apply to specific source folders:**
```json
"filenamePatterns": [
  "/src/*",
  "/tests/*"
]
```

**Pitfall**: An empty array `[]` means no path filter (policy applies to all files). To exclude files, you must first include with `/*` then exclude with `!` patterns. A filter like `["!*.md"]` alone specifies no files since nothing is included first.

---

## Build Policy Settings

The Build policy type (`0609b952-1397-4640-95ec-e00a01b2c241`) uses these settings:

```json
{
  "buildDefinitionId": 5,
  "queueOnSourceUpdateOnly": true,
  "manualQueueOnly": false,
  "displayName": "Build Validation",
  "validDuration": 720,
  "scope": [...]
}
```

| Setting | Description |
|---|---|
| `buildDefinitionId` | The build definition (pipeline) ID to trigger. |
| `queueOnSourceUpdateOnly` | `true` = only queue builds when source branch changes. |
| `manualQueueOnly` | `true` = don't auto-queue, must be manually triggered. |
| `validDuration` | Minutes before the build result expires. `0` = immediately on target branch update. |
| `displayName` | Friendly name for the build policy. |

---

## Build Definitions (Pipelines)

```bash
# List build definitions for a repository
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/build/definitions?api-version=7.1&repositoryId={repoId}&repositoryType=TfsGit"
```

Response: `value[]` array with:
- `id` — Build definition ID (needed for build policies)
- `name` — Pipeline name (used as `statusGenre` for coverage status)

---

## Azure CLI Alternative Commands

The `az repos policy` CLI commands can also manage policies:

```bash
# List all policies
az repos policy list --org https://dev.azure.com/{org} --project {project} \
  --repository-id {repoId} --branch main

# Show policy details
az repos policy show --id {policyId} --org https://dev.azure.com/{org} --project {project}

# Create build validation policy
az repos policy build create \
  --blocking true --enabled true \
  --branch main --build-definition-id {defId} \
  --display-name "CI Build" \
  --manual-queue-only false --queue-on-source-update-only false \
  --repository-id {repoId} --valid-duration 0 \
  --org https://dev.azure.com/{org} --project {project}

# Update policy via configuration file
az repos policy update --config policy.json --id {policyId} \
  --org https://dev.azure.com/{org} --project {project}

# Create policy from configuration file (supports multiple scopes)
az repos policy create --config policy.json \
  --org https://dev.azure.com/{org} --project {project}
```

**Pitfall**: There is no `az repos policy status create` command. Status check policies must be created via the REST API or the web UI.

---

## File Download (for azurepipelines-coverage.yml)

```bash
# Download a file from the repository
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/git/repositories/{repoId}/items?path=/azurepipelines-coverage.yml&api-version=7.1"
```

Returns the file content directly if it exists, or 404 if not found.

---

## Branch Validation

Before adding or enforcing a policy on a branch, always verify the branch exists:

```bash
curl -s -u ":$TOKEN" \
  "$ORG/{project}/_apis/git/repositories/{repoId}/refs?filter=heads/{branchName}&api-version=7.1"
```

Response: `value[]` array. If the array is empty, the branch does not exist. **Skip it** and report to the user. Do NOT create or enforce policies on non-existent branches.

Example response for an existing branch:
```json
{
  "value": [
    {
      "name": "refs/heads/main",
      "objectId": "abc123..."
    }
  ],
  "count": 1
}
```

Example response for a non-existent branch:
```json
{
  "value": [],
  "count": 0
}
```

---

## Known Pitfalls Summary

1. **Token per Bash call**: On Windows, re-fetch `TOKEN` at the top of every Bash tool invocation.
2. **PUT replaces entire config**: When updating a policy, always GET first, modify, then PUT. Don't send partial configs.
3. **Status policy type ID varies**: Always query `/policy/types` first. Don't hardcode the Status type GUID.
4. **Status name convention**: Code coverage status is posted as `{pipeline-name}/codecoverage`. The `statusGenre` must match the pipeline name exactly. **Never guess the genre** — each pipeline uses its own convention (e.g., `-pullrequest`, `-pr`, `.pullrequest`, `-pullrequest-gatebuild`). Always look up the actual genre from recent PR statuses (see pitfall #19).
5. **WebFetch fails on Azure DevOps**: URLs redirect to sign-in. Use `az` CLI or `curl` with token.
6. **JSON payload escaping**: Always write JSON to a temp file and use `curl -d @file.json`. Use heredoc with single-quoted delimiter (`<< 'JSONEOF'`) to avoid bash variable expansion.
7. **No status create CLI command**: Status check policies cannot be created via `az repos policy`. Use the REST API directly.
8. **Scope with null repositoryId**: Setting `repositoryId` to `null` applies the policy to ALL repositories in the project. Always specify the repo ID for targeted policies.
9. **`policyApplicability` type error**: Do NOT include `policyApplicability` as a string (e.g., `"default"`). The API expects a numeric enum or null. Omit the field entirely to get the default behavior.
10. **Windows `$TEMP` backslash paths**: Paths like `C:\Users\...\Temp` break `curl -d @path`. Use forward-slash paths in the working directory instead (e.g., `/path/to/workdir/file.json`).
11. **`/tmp/` not shared between bash and Python on Windows**: Bash `/tmp/` resolves differently than Python on Windows. Use absolute paths with forward slashes that both can resolve (e.g., `/path/to/workdir/`).
12. **`jq` may not be available on Windows**: Use `python -c "..."` for JSON processing instead of `jq`.
13. **Validate branches before setting policies**: Always check that a branch exists via the refs API before creating or enforcing policies on it. Skip non-existent branches and report them to the user.
14. **`repositoryId` filter returns unrelated policies**: The policy configurations API's `repositoryId` query parameter returns policies scoped to OTHER repos too. Always verify `settings.scope[].repositoryId` matches your target repo before updating.
15. **Continuation token is in response header**: When paginating policy configurations, the continuation token is in the `x-ms-continuationtoken` HTTP response header, NOT in the JSON body. If using `urllib`, read it from `resp.getheaders()`.
16. **Bash `!` escaping in `python -c`**: The `!` character in strings like `!*.md` gets escaped to `\!` by bash even inside single quotes on some shells. This corrupts `filenamePatterns`. Use a separate Python helper script file instead of inline `python -c` for any logic involving `!` characters.
17. **PUT read-only fields**: When updating a policy via PUT, remove ALL read-only fields: `createdBy`, `createdDate`, `_links`, `revision`, `url`, AND `id`. The `id` field is also read-only and causes errors if included.
18. **Update should normalize all settings**: When updating an existing policy (e.g., changing `isBlocking`), also normalize other settings to the desired state: set `invalidateOnSourceUpdate=true`, `displayName`, and `filenamePatterns`. Many legacy policies have `invalidateOnSourceUpdate=false` and no `filenamePatterns`, which is suboptimal.
19. **Genre mismatch causes stuck policies**: When creating a new policy, never hardcode or guess the `statusGenre` (e.g., `{repo}-pullrequest`). Each pipeline has its own naming convention — common variations include `-pullrequest`, `-pr`, `.pullrequest`, `-pullrequest-gatebuild`. Always look up the actual genre from recent PR statuses by querying `GET /pullrequests/{prId}/statuses` and filtering for `context.name == "codecoverage"`. If no codecoverage genre is found in recent PRs, skip the repo rather than guessing.
