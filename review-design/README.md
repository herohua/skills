# review-design

Interactive design document review skill for Claude Code. Reads a design doc, explores the codebase for context, collaborates with the reviewer to align on key feedback, then generates a structured review.

## Usage

```
/review-design <path-to-document> [--output <dir>] [--pr <branch>] [--title <title>]
```

### Examples

```bash
# Basic review — saves to current directory
/review-design ~/Downloads/cache-design.htm

# Review with custom output directory
/review-design ~/Downloads/cache-design.htm --output ~/reviews

# Review and create a PR targeting develop
/review-design ~/Downloads/cache-design.htm --pr develop
```

## What It Does

### Phase 1: Read the Document
Reads the design doc (supports .htm, .md, .txt, .pdf, .docx) and extracts key points. Leverages the `docx` and `pdf` skills for binary formats.

### Phase 2: Explore the Codebase
Launches parallel codebase searches to gather context relevant to the design — existing implementations, patterns, infrastructure, and related features.

### Phase 3: Collaborate with Reviewer
**Interactive phase.** Presents draft findings and asks the reviewer to:
- Keep, drop, or adjust items
- Provide additional concerns from domain knowledge
- Share priorities (performance vs cost, quick rollout vs perfect architecture, etc.)
- Choose between options so the review makes clear recommendations

### Phase 4: Write the Review
Generates a structured review with:
- **Blocking vs Non-blocking** severity classification
- **Concerns** (design should be reconsidered) vs **Questions** (needs clarification)
- Clear recommendations per item (no unresolved option menus)
- Summary table

### Phase 5: Save and Deliver
Saves the review as markdown. Optionally creates a PR (supports both GitHub and Azure DevOps).

## Supported Document Formats

| Format | Method |
|--------|--------|
| `.htm` / `.html` | Direct read, strips Word markup |
| `.md` / `.txt` | Direct read |
| `.pdf` | Via `pdf` skill |
| `.docx` | Via `docx` skill |
| `.doc` (legacy) | User prompted to re-export |
