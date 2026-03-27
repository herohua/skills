# Code Coverage Policy Troubleshooting

Common issues and solutions when working with code coverage branch policies in Azure DevOps.

## Coverage Status Never Appears on PRs

**Symptom**: You've added a status check policy for code coverage, but the PR never shows the coverage status.

**Causes & Solutions**:

1. **Pipeline doesn't publish code coverage**: Ensure the pipeline uses `PublishCodeCoverageResults@2` (V2, not V1). V1 does not support diff coverage or status checks.

2. **No `azurepipelines-coverage.yml`**: The code coverage status check requires this file at the repo root. Create it with at minimum:
   ```yaml
   coverage:
     status:
       comments: on
       diff:
         target: 70%
   ```

3. **Pipeline hasn't run yet**: The status is only posted after a pipeline run that publishes coverage.

4. **Wrong coverage format**: For `.html` files, coverage status checks aren't supported. Use Cobertura or JaCoCo XML formats.

## Coverage Policy Gets Stuck

**Symptom**: The status check shows as "Pending" indefinitely.

**Causes & Solutions**:

1. **Genre mismatch between policy and pipeline**: The `statusGenre` in the policy must exactly match the genre that the pipeline posts. Each pipeline has its own naming convention — it is NOT always `{repo-name}-pullrequest`. Common variations include:
   - `myrepo-pullrequest` (most common)
   - `myrepo-pr` (some repos use shorter suffix)
   - `myrepo-pullrequest-gatebuild` (some repos append extra qualifier)
   - `myrepo.pullrequest` (dot instead of dash separator)

   **Never guess the genre.** Always look it up from actual PR statuses:
   ```bash
   # Find the actual genre from recent PR statuses
   curl -s -u ":$TOKEN" \
     "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoId}/pullrequests/{prId}/statuses?api-version=7.1" \
     | python -c "
   import json, sys
   for s in json.load(sys.stdin).get('value', []):
       ctx = s.get('context', {})
       if ctx.get('name','').lower() == 'codecoverage':
           print(f'genre={ctx.get(\"genre\")}')"
   ```
   If building automation, query up to 5 recent PRs to find the codecoverage genre. If no genre is found, skip the repo rather than guessing.

2. **Using PublishCodeCoverage V1**: Upgrade to V2.

3. **Too many files in PR**: If the PR has more than 100 files, the coverage policy may get stuck.

4. **Multiple coverage policies**: If you configure multiple coverage policies for the same scope, one gets stuck. Keep only one.

## 0% Diff Coverage Despite Adding Tests

**Symptom**: Coverage status shows 0% even after adding tests.

**Causes & Solutions**:

1. **Tests not running**: Verify the newly added tests are included in the build. Check the test results tab.

2. **Non-executable changes only**: Lines removed, whitespace changes, or comment additions are non-executable and won't have coverage data.

## Diff Coverage Comments Not Appearing

**Symptom**: Coverage status works but no PR comments are posted.

**Causes & Solutions**:

1. **Comments not enabled**: Set `comments: on` in `azurepipelines-coverage.yml`.

2. **Using V1 task**: Diff coverage comments require `PublishCodeCoverageResults@2`.

3. **No executable changes**: Config-only changes don't generate diff coverage comments.

## Policy Creation Fails (403 Forbidden)

**Symptom**: REST API returns 403 when creating or updating a policy.

**Solution**: The user needs one of:
- **Project Administrators** group membership
- Repository-level **Edit policies** permission

To check permissions:
```bash
# List security namespaces (for reference)
curl -s -u ":$TOKEN" \
  "https://dev.azure.com/{org}/_apis/securitynamespaces?api-version=7.1"
```

## Status Type ID Mismatch

**Symptom**: Policy creation fails or policy doesn't match any status.

**Solution**: Always query the policy types API to get the correct Status type ID for your org:
```bash
curl -s -u ":$TOKEN" \
  "https://dev.azure.com/{org}/{project}/_apis/policy/types?api-version=7.1" | \
  jq '.value[] | select(.displayName == "Status") | .id'
```

## Bash `!` Escaping Corrupts `filenamePatterns`

**Symptom**: After creating or updating a policy via bash script, the `filenamePatterns` in Azure DevOps show `\!*.md` instead of `!*.md`, causing the exclusion patterns to not work.

**Cause**: Bash (especially on Windows) treats `!` as a history expansion character. Even inside single quotes, `!` can get escaped to `\!` in certain contexts (inline `python -c`, heredocs, variable assignments).

**Solution**: Never pass `!` through bash. Use a separate Python helper script that hardcodes the patterns:

```python
# policy_helper.py
FILENAME_PATTERNS = ["/*", "!*.md", "!*.yml", "!*.yaml", "!/docs/*"]

def update(get_file, put_file):
    p = json.load(open(get_file))
    p['isEnabled'] = True
    p['isBlocking'] = True
    s = p.setdefault('settings', {})
    s['filenamePatterns'] = FILENAME_PATTERNS
    # ... other settings ...
    json.dump(p, open(put_file, 'w'))
```

Then call from bash: `python policy_helper.py update "$GET_FILE" "$PUT_FILE"`

**If already corrupted**: Re-fetch the policy, run it through the helper script, and PUT it back. Verify the stored patterns are correct by GETting the policy again.

## PUT Update Fails or Silently Ignores Changes

**Symptom**: PUT request returns 200 but the policy isn't updated, or returns 400/500.

**Cause**: The request body contains read-only fields that ADO rejects or ignores.

**Solution**: Remove these read-only fields before PUT:
```python
READONLY_FIELDS = ['createdBy', 'createdDate', '_links', 'revision', 'url', 'id']
for k in READONLY_FIELDS:
    policy.pop(k, None)
```

Note: `id` must also be removed — it's in the URL path already and including it in the body can cause conflicts.

## Coverage Report Shows Inaccurate Numbers

**Symptom**: Numbers in the Code Coverage tab don't match expectations.

**Causes**:
- The data comes from the coverage file directly. If using custom tasks, check if DLLs or files are missing from the coverage report.
- When both .NET Core and .NET Framework are used, you may see duplicate DLLs (by design — same module from different paths).

## Multiple Pipelines and Coverage Merging

Code coverage does NOT merge across multiple pipelines. If multiple pipelines trigger on a PR, only per-pipeline coverage is reported. To get unified coverage, consolidate into a single pipeline.

## azurepipelines-coverage.yml Reference

Full configuration options:

```yaml
coverage:
  status:
    # Post coverage details as PR comments (off by default)
    comments: on | off

    diff:
      # Diff coverage target percentage (default: 70%)
      target: 60%
```

The file must be named exactly `azurepipelines-coverage.yml` and placed at the repository root.
