# Azure DevOps REST API Reference for Code Coverage Policies

Quick reference for API calls used to manage code coverage branch policies. All calls require authentication.

## Authentication

```bash
# Get token via Azure CLI (returns an OAuth access token)
TOKEN=$(az account get-access-token \
  --resource 499b84ac-1321-427f-aa17-267ca6975798 \
  --query accessToken -o tsv)

# All curl calls use Bearer token authorization
curl -s -H "Authorization: Bearer $TOKEN" ...
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
curl -s -H "Authorization: Bearer $TOKEN" \
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
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/{project}/_apis/policy/types?api-version=7.1"
```

Response: `value[]` array. Key fields:
- `id` — Policy type GUID
- `displayName` — Human-readable name (e.g., "Status", "Build")
- `description` — Detailed description

### Common Policy Type IDs

These are **typical** IDs but they can vary by organization. Always verify via the API.

| Policy Type | Typical ID |
|---|---|
| Minimum approval count | `fa4e907d-c16b-4a4c-9dfa-4906e5d171dd` |
| Build | `0609b952-1397-4640-95ec-e00a01b2c241` |
| Required reviewers | `fd2167ab-b0be-447a-8ec8-39368250530e` |
| Work item linking | `40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e` |
| Status | `cbdc66da-9728-4af8-aada-9a5a32e4a226` |
| Merge strategy | `fa4e907d-c16b-4a4c-9dfa-4916e5d171ab` |

---

## Policy Configurations

### List All Policies

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/{project}/_apis/policy/configurations?api-version=7.1"
```

Optional query parameters:
- `policyType={typeId}` — Filter by policy type GUID
- `$top={n}` — Max results
- `continuationToken={token}` — Pagination

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
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/{project}/_apis/policy/configurations/{configurationId}?api-version=7.1"
```

### Create Policy

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST -H "Content-Type: application/json" \
  "$ORG/{project}/_apis/policy/configurations?api-version=7.1" \
  -d @payload.json
```

### Update Policy

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X PUT -H "Content-Type: application/json" \
  "$ORG/{project}/_apis/policy/configurations/{configurationId}?api-version=7.1" \
  -d @payload.json
```

**Pitfall**: PUT replaces the entire configuration. Always GET the current config first, modify it, then PUT it back.

### Delete Policy

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X DELETE \
  "$ORG/{project}/_apis/policy/configurations/{configurationId}?api-version=7.1"
```

---

## Status Check Policy Settings

The Status policy type uses these settings:

```json
{
  "statusName": "codecoverage",
  "statusGenre": "{pipeline-name}",
  "authorId": "",
  "invalidateOnSourceUpdate": true,
  "displayName": "Code Coverage Policy",
  "scope": [...]
}
```

| Setting | Description |
|---|---|
| `statusName` | The status name to match. For code coverage, always `codecoverage`. |
| `statusGenre` | The pipeline name. Together, genre + name form the status context `{genre}/{name}`. |
| `authorId` | Identity that must post the status. Empty string = any identity. |
| `invalidateOnSourceUpdate` | `true` = reset status when source branch is updated. |
| `displayName` | Optional friendly name shown in the branch policy UI. |

**Pitfall**: Do NOT include `policyApplicability` as a string (e.g., `"default"`). The API expects a numeric enum or null. Omit the field entirely.

---

## Build Policy Settings

The Build policy type uses these settings:

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

---

## Build Definitions (Pipelines)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/{project}/_apis/build/definitions?api-version=7.1&repositoryId={repoId}&repositoryType=TfsGit"
```

Response: `value[]` array with:
- `id` — Build definition ID (needed for build policies)
- `name` — Pipeline name (used as `statusGenre` for coverage status)

---

## File Download (for azurepipelines-coverage.yml)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/{project}/_apis/git/repositories/{repoId}/items?path=/azurepipelines-coverage.yml&includeContent=true&api-version=7.1"
```

Returns file content directly if it exists, or 404 if not found.

---

## Branch Validation

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORG/{project}/_apis/git/repositories/{repoId}/refs?filter=heads/{branchName}&api-version=7.1"
```

If `value[]` is empty, the branch does not exist.

---

## Known Pitfalls Summary

1. **Token per Bash call**: On Windows, re-fetch `TOKEN` at the top of every Bash tool invocation.
2. **PUT replaces entire config**: Always GET first, modify, then PUT.
3. **Status policy type ID varies**: Always query `/policy/types` — never hardcode.
4. **Status name convention**: Coverage status is `{pipeline-name}/codecoverage`. The `statusGenre` must match the pipeline name exactly.
5. **JSON payload escaping**: Write JSON to a file and use `curl -d @file.json`. Use heredoc with single-quoted delimiter (`<< 'JSONEOF'`) to avoid bash variable expansion.
6. **No status create CLI command**: Status check policies cannot be created via `az repos policy`. Use the REST API directly.
7. **Scope with null repositoryId**: Setting `repositoryId` to `null` applies to ALL repos. Always specify the repo ID.
8. **`policyApplicability` type error**: Omit the field entirely — API expects numeric enum or null, not a string.
9. **Windows `$TEMP` backslash paths**: Use forward-slash paths in the working directory instead.
10. **`/tmp/` not shared on Windows**: Use absolute paths with forward slashes that both bash and Python can resolve.
11. **`jq` may not be available**: Use `python -c "..."` for JSON processing.
12. **Validate branches first**: Always check branch existence via refs API before creating or enforcing policies.
