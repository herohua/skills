# Code Review Checklist

This reference file defines the standard review criteria and verification discipline shared across review skills (`/review-pr`, `/self-review`, etc.).

## How to Use

For each changed file, read the **full source version** (not just diff hunks) to understand context. If you have access to the full repository, explore callers, related files, and broader architectural context.

Apply the checklist below to every changed file. Then verify each potential finding using the verification discipline at the bottom before reporting it.

---

## Review Categories

### Bugs
- Syntax/typo errors (mismatched brackets, wrong string formats)
- Logic errors (wrong conditions, off-by-one, dead code paths)
- Missing null/error handling at system boundaries
- Breaking changes to public/internal APIs
- Resource leaks (unclosed connections, missing dispose)
- Computed properties with hidden allocations (e.g., collection expressions `[.. a, .. b]` in property getters that allocate on every access)

### Design
- Code duplication that risks drift (DRY violations)
- Unnecessary complexity (redundant calls, over-engineering)
- Inconsistency with existing codebase patterns
- Poor naming or misleading abstractions

### Process
- TODO/HACK/NOT YET comments that should be resolved pre-merge
- Test coverage gaps (check pipeline status if available)
- Unrelated changes mixed into the PR
- Configuration or secret exposure
- Doc comments (`<param>`, `<returns>`, `<summary>`) out of sync with changed method signatures
- User-facing strings (banner messages, error messages, UI labels): check for clarity, grammar, consistency with existing messaging patterns

### Security
- Hardcoded credentials, API keys, or tokens (check for strings that look like secrets)
- SQL injection: string concatenation in database queries instead of parameterized queries
- XSS: unescaped user input rendered in HTML/templates
- Path traversal: user-controlled input used in file paths without sanitization
- Insecure deserialization: deserializing untrusted data without validation
- Missing authentication/authorization checks on new endpoints
- Sensitive data exposure: PII or secrets logged, returned in error messages, or stored unencrypted

---

## Severity Levels

| Level | Meaning |
|-------|---------|
| **Bug** | Functional correctness issue |
| **Security** | Security vulnerability or risk |
| **Design** | Architectural or maintainability concern |
| **Process** | TODO items, test gaps, unrelated changes |
| **Nit** | Style, naming, minor improvement |

---

## Verification Discipline

**For every potential finding, you MUST verify all three conditions:**

1. **In the diff**: The issue is in lines actually changed in this branch (merge-base comparison). Check the diff output — if the line exists in both base and source versions, it is NOT a change introduced by this branch.
2. **Not already flagged**: Compare against any existing reviewer comments or won't-fix list to avoid duplicates.
3. **Real issue**: Not a misunderstanding of codebase context. When uncertain, read surrounding code for clarification. If you have the full repo, trace callers and dependencies to confirm.

If any condition fails, **discard the finding**. False positives erode reviewer trust.

---

## Output Format

Present findings as a **numbered table**:

```
| #  | Severity | File:Line | Description | Existing? |
|----|----------|-----------|-------------|-----------|
| 1  | Bug      | Foo.cs:44 | Null ref... | No        |
| 2  | Design   | Bar.cs:12 | DRY viol... | No        |
| 3  | Nit      | Baz.cs:88 | Naming...   | Similar   |
```

For each finding, include:
- What the issue is
- Why it matters
- Suggested fix (if obvious)

---

## Binary File Detection

Before generating diffs, detect and skip binary files using these checks (in order):

1. **File extension**: Skip known binary types: `.png`, `.jpg`, `.jpeg`, `.gif`, `.ico`, `.bmp`, `.webp`, `.svg`, `.woff`, `.woff2`, `.ttf`, `.eot`, `.otf`, `.dll`, `.exe`, `.zip`, `.tar`, `.gz`, `.pdf`, `.snk`, `.p12`, `.pfx`.
2. **HTTP Content-Type**: When downloading files via API, binary files return `application/octet-stream` instead of a text type.
3. **Null byte check**: If the downloaded content contains null bytes (`\x00`) in the first 8 KB, treat it as binary.

Note binary files in the review summary as "binary file changed — not diffed".

---

## Line Number Verification

**Do NOT estimate line numbers from diff hunk headers** (e.g., `@@ -181,4 +198,31 @@`). Hunk headers show approximate ranges and are misleading — they don't account for surrounding context lines, doc comments, or blank lines between the hunk boundary and your target code.

Before posting an inline comment, always verify the exact line number by running `cat -n` or `grep -n` on the downloaded source file. For example:
```bash
grep -n 'IsOriginalContentChanged' /tmp/pr-review/source/File.cs
```

Getting this wrong causes comments to appear on the wrong line (e.g., on a doc comment instead of the method signature).
