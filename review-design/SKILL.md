---
name: review-design
description: Review a design document against the current codebase. Reads design docs, explores the codebase for context, collaborates with the reviewer to align on key points, then generates a structured review. Invoke with /review-design <path-to-document> [--output <output-dir>] [--pr <target-branch>]
allowed-tools: Read, Grep, Glob, Bash, Agent, Write, Edit, AskUserQuestion
---

# Design Document Review Skill

You are helping a reviewer produce a high-quality design review. This is an **interactive, collaborative process** — not a one-shot generation. You work with the reviewer to understand their priorities, align on key feedback, and produce a review that reflects their judgment.

## Existing Skills You Should Leverage

- **docx** skill: Use for reading .docx files (handles unpacking, XML extraction, pandoc conversion). Invoke when the input is a .docx file.
- **pdf** skill: Use for reading .pdf files (handles text extraction, table extraction). Invoke when the input is a .pdf file.

## Input Parsing

Parse arguments from `$ARGUMENTS`:
- **First positional arg**: Path to the design document (required)
- `--output <dir>`: Directory to save the review (default: current working directory)
- `--pr <branch>`: If provided, create a PR targeting this branch after saving the review into the repo's docs directory
- `--title <title>`: Optional custom title for the review file (default: derived from document name)

---

## Phase 1: Read and Understand the Document

Read the design document. Handle different formats:
- **.htm/.html**: Use `Read` tool. Word-exported HTML — extract text content, ignore CSS/styling.
- **.md/.txt**: Use `Read` tool directly.
- **.pdf**: Use the **pdf** skill for extraction.
- **.docx**: Use the **docx** skill for extraction. If the file is OLE2 format (header `D0CF11E0`), inform the user to re-export as .htm or .pdf.

Extract and present a **brief summary** to the reviewer:
- What problem is being solved
- Key architectural decisions proposed
- Main trade-offs identified by the author

---

## Phase 2: Explore the Codebase for Context

Launch **parallel** Agent subagent searches (`subagent_type: Explore`) to gather codebase context relevant to the design. Identify 2-4 exploration themes based on the document content. Common themes:
- Existing implementations of components the design proposes to add/modify
- Current data flow and architecture patterns
- Configuration and infrastructure already in use
- Related features or services mentioned in the design

Do NOT duplicate searches — each agent should cover a distinct area.

### Cost Optimization
- Use `subagent_type: Explore` agents (haiku-based) for codebase search
- Parallelize all independent searches
- Use Grep/Glob to find relevant sections first, only Read when needed

---

## Phase 3: Collaborate with Reviewer on Key Points

**This is the critical phase.** Do NOT write the full review yet. Instead, present your findings to the reviewer and align on the feedback.

### Step 3a: Present Draft Findings

Present to the reviewer a **numbered list of potential feedback items**, each with:
- A one-line title
- Whether it's a **Concern** (design should be reconsidered) or a **Question** (needs clarification from the author)
- Whether it's **Blocking** (must be resolved before implementation) or **Non-blocking** (can be addressed later)
- A 1-2 sentence explanation

Example format:
```
1. [Blocking Concern] Key construction is incomplete
   The cache key omits prompt version and fixType flag, which would cause incorrect cache hits.

2. [Blocking Question] How are multi-line edits handled in per-line cache?
   AI can produce cross-line suggestions. Unclear how these map to per-line cache entries.

3. [Non-blocking Concern] No sizing estimate for storage
   Document doesn't estimate data volume. Should include back-of-envelope calculation.
```

### Step 3b: Ask Reviewer for Input

Use `AskUserQuestion` or direct questions to ask the reviewer:

1. **Which items to keep, drop, or adjust?** — The reviewer may disagree with some findings or want to deprioritize them.
2. **Any additional concerns the reviewer has?** — The reviewer brings domain knowledge, team context, and priorities that codebase exploration alone cannot surface.
3. **Reviewer's priorities for this specific design** — Ask about the context so you can make the right trade-off calls. For example:
   - Does this service prioritize **performance** over **cost**?
   - Is **quick rollout** more important than **perfect architecture**?
   - Are there team/org constraints (e.g., "we can't add new Azure resources right now")?
   - What's the deployment cadence — does upgrade continuity matter?

### Step 3c: Resolve Options Before Writing

If any feedback item presents **multiple options** (e.g., "Redis vs CosmosDB", "grace period vs two-tier fallback"), do NOT just list them in the review. Instead:

1. Present the options to the reviewer with trade-offs
2. Ask for their context and preference
3. Based on their input, **make a recommendation** in the review

The final review should state a clear recommendation per concern, not leave the design author with unresolved choices. The reviewer's job is to guide the author, not hand them a menu.

### Step 3d: Confirm Final Structure

Before writing, confirm with the reviewer:
- The list of items to include
- The blocking vs non-blocking classification
- The concern vs question classification
- Any specific wording or framing preferences

---

## Phase 4: Write the Review

Once aligned with the reviewer, write the review in this format:

```markdown
# Review: {Document Title}

**Author:** {doc author} | **Reviewed by:** {reviewer} | **Date:** {today}

---

## Overall Assessment
{1-2 paragraph summary: design quality, readiness for implementation, top-level recommendation}

---

## Strengths
{Numbered list of 3-5 things the design does well, with brief justification}

---

## Blocking Items

### Concerns (Must Reconsider)
{Numbered sections. Each has:
- Clear title
- Explanation with codebase evidence (file paths, line numbers)
- Clear recommendation (not multiple options)}

### Questions (Must Clarify)
{Numbered sections. Each has:
- Clear title
- Why the current description is insufficient
- What specific information is needed}

---

## Non-blocking Items

### Concerns
{Same format, briefer}

### Questions
{Same format, briefer}

---

## Minor / Editorial
{Bullet list of small corrections, typos, missing details}

---

## Summary

| Area | Type | Severity | Verdict |
|------|------|----------|---------|
| {area} | Concern/Question | Blocking/Non-blocking | {recommendation} |

{Final 1-2 sentence recommendation}
```

### Review Checklist

When reviewing, systematically check for:
1. **Completeness of key/identifier design**: Are all factors that affect output included?
2. **Consistency with existing codebase patterns**: DI, data access, serialization, error handling
3. **Upgrade/migration story**: What happens during deployments? In-flight user impact?
4. **Infrastructure reuse vs new dependencies**: Can existing infra be reused?
5. **Edge cases**: Race conditions, concurrent access, data loss, boundary operations
6. **Correctness of claims**: Does the doc reference code/functions that actually exist?
7. **Operational concerns**: Sizing, cost, monitoring, failure modes

---

## Phase 5: Save and Deliver

### Save the review
Save to the output directory with filename: `Review-{sanitized-document-title}.md`

### Create PR (if --pr flag provided)
If `--pr <branch>` was specified:
1. Copy the review into the repo's docs directory
2. Create a new branch `user/review-{short-name}`
3. Commit: `Add design review for {document title}`
4. Push and create PR targeting the specified branch
5. For Azure DevOps repos: `az repos pr create`; for GitHub: `gh pr create`
6. Report the PR URL

### Report
Summarize to the reviewer:
- Top findings (blocking items)
- Where the review was saved
- PR URL if created
