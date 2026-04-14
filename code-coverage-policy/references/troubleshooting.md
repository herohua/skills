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
         target: 60%
   ```

3. **Pipeline hasn't run yet**: The status is only posted after a pipeline run that publishes coverage.

4. **Wrong coverage format**: For `.html` files, coverage status checks aren't supported. Use Cobertura or JaCoCo XML formats.

## Coverage Policy Gets Stuck

**Symptom**: The status check shows as "Pending" indefinitely.

**Causes & Solutions**:

1. **Incorrect branch policy name format**: The `statusGenre` in the policy must exactly match the pipeline name. Verify with:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" \
     "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoId}/pullrequests/{prId}/statuses?api-version=7.1"
   ```

2. **Using PublishCodeCoverage V1**: Upgrade to V2.

3. **Too many files in PR**: If the PR has more than 100 files, the coverage policy may get stuck.

4. **Multiple coverage policies**: If you have multiple coverage policies for the same scope, one gets stuck. Keep only one.

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

## Status Type ID Mismatch

**Symptom**: Policy creation fails or policy doesn't match any status.

**Solution**: Always query the policy types API to get the correct Status type ID:
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://dev.azure.com/{org}/{project}/_apis/policy/types?api-version=7.1"
```
Look for `displayName == "Status"` and use its `id`.

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
      # Diff coverage target percentage (default: 60%)
      target: 60%
```

The file must be named exactly `azurepipelines-coverage.yml` and placed at the repository root.
