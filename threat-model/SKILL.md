---
name: threat-model
description: |
  Update Microsoft Threat Modeling Tool (.tm7) files to reflect design changes. Use when the user wants to update a threat model, add new elements/flows/threats to a .tm7 file, modify DFD diagrams, or apply STRIDE analysis. Triggers include: any mention of 'threat model', '.tm7', 'STRIDE', 'DFD', 'data flow diagram', 'threat modeling tool', or requests to add threats, trust boundaries, data flows, or external interactors to a threat model. Also use when user provides a design flowchart and wants to update the corresponding threat model.
---

# Threat Model Update Skill

Update Microsoft Threat Modeling Tool (TMT) `.tm7` files programmatically — adding DFD elements, data flows, trust boundaries, and STRIDE threats to reflect new or changed system designs.

## When to Use

- User provides a design change (flowchart, architecture diagram, description) and wants the threat model updated
- User wants to add new processes, external interactors, data stores, data flows, or trust boundaries
- User wants new STRIDE threats generated for new or modified data flows
- User wants to restructure trust boundaries or rename elements

## High-Level Workflow

### Phase 1: Gather Inputs

Collect from the user:

1. **Design input**: New/changed system design — flowchart, Mermaid diagram, architecture doc, or verbal description
2. **Target .tm7 file**: Path to the existing threat model file to update
3. **Scope**: Which parts of the design are new vs already modeled

Ask clarifying questions:
- Which elements are in-scope vs out-of-scope for threat analysis?
- Which trust boundaries should elements belong to?
- What authentication methods are used on each data flow? (e.g., MSI, OAuth, access token, GitHub App, user login)
- Should arrow labels follow a specific naming convention?

### Phase 2: Analyze Existing .tm7

Read the .tm7 file and extract the current state. The .tm7 format is WCF DataContract-serialized XML — see [references/tm7-format.md](references/tm7-format.md) for the full format reference.

Extract and present to the user:

1. **All border elements** (stencils): processes, external interactors, data stores — names, GUIDs, positions, out-of-scope flags
2. **All trust boundaries**: names, GUIDs, positions, dimensions — which elements they contain
3. **All data flow connectors**: names, source/target elements, authentication annotations
4. **All existing threats**: count by STRIDE category, current ID range
5. **Annotations/notes**: free-text boxes on the diagram
6. **z:Id sequence**: the last used z:Id value (needed for adding new elements)

Key values to record for later use:
- **Drawing Surface GUID**: needed for all new threat instances
- **Existing element GUIDs**: needed as source/target references for new data flows
- **Last threat ID**: new threats continue from this number
- **Last z:Id**: new elements continue from this number

### Phase 3: Plan Changes

Based on the design input and existing model state, produce a change plan:

| Change Type | Details |
|------------|---------|
| New border elements | Name, type (Process/EI/DataStore), position, in/out of scope |
| New data flows | Name, source, target, auth method |
| Modified elements | What changes (position, scope, name) |
| Trust boundary changes | New boundaries, expanded boundaries, elements to include |
| New threats | Which flows get threats, STRIDE categories to cover |
| Annotation updates | Updated step descriptions |

Present the plan to the user for approval before proceeding.

### Phase 4: Generate Update Script

Write a Python script (no external dependencies) that modifies the .tm7 file using string-based XML manipulation. Do NOT use ElementTree or lxml — the .tm7 namespace complexity makes DOM parsing unreliable.

#### Script Structure

```python
"""
Update the Threat Model (.tm7) file.
Usage: python update_threat_model.py [--input <path>] [--output <path>]
"""
import argparse

ABS_NS = "http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts"

# 1. Define existing GUIDs (from Phase 2 analysis)
# 2. Define new GUIDs (deterministic, hardcoded for reproducibility)
# 3. Define element builder functions
# 4. Main function:
#    a. Read the .tm7 file
#    b. Insert new borders before </Borders>
#    c. Insert new connectors before </Lines>
#    d. Insert new threats before </ThreatInstances>
#    e. Modify trust boundaries / element properties as needed
#    f. Write the updated file
```

#### Building Elements

Use these builder patterns for each element type. See [references/tm7-format.md](references/tm7-format.md) for the full XML structure of each element type.

**External Interactor** — `StencilRectangle` with `GenericTypeId = GE.EI`
**Process** — `StencilEllipse` with `GenericTypeId = GE.P`
**Data Store** — `StencilParallelLines` with `GenericTypeId = GE.DS`
**Data Flow** — `Connector` with `GenericTypeId = GE.DF`, `TypeId = SE.DF.TMCore.Request`
**Trust Boundary** — `BorderBoundary` with `GenericTypeId = GE.TB.B`

#### Building Threats

For each new data flow, generate threats covering relevant STRIDE categories:

| Category | When to Apply |
|----------|--------------|
| **Spoofing** | Flow uses credentials/tokens — risk of token theft or identity impersonation |
| **Tampering** | Flow carries data that could be modified — risk of content injection |
| **Repudiation** | Automated actions without audit trail — risk of unverifiable actions |
| **Information Disclosure** | Flow carries or produces content that could leak sensitive data |
| **Denial of Service** | Flow to a shared resource that could be overwhelmed (apply selectively) |
| **Elevation of Privileges** | Flow grants access or automated entity has elevated permissions |

Each threat needs:
- A unique sequential `b:Id` (continue from last existing ID)
- A `TypeId` from the KnowledgeBase (e.g., TH7 for spoofing, TH96 for tampering)
- Source, flow, and target GUIDs
- A descriptive title, STRIDE category, description, and possible mitigations
- The `InteractionString` matching the data flow's display name

#### Key Threat TypeIds

| TypeId | Typical Use |
|--------|------------|
| TH7 | Credential/token theft (Spoofing) |
| TH30 | Insufficient audit trail (Repudiation) |
| TH86 | Source spoofing to gain access (Spoofing) |
| TH94 | Sensitive info through error messages (Info Disclosure) |
| TH96 | Injection / tampering with data (Tampering) |
| TH101 | Sensitive info in encrypted content (Info Disclosure) |
| TH108 | Malicious inputs into API (Tampering) |
| TH110 | Unauthorized access / privilege escalation (EoP) |

### Phase 5: Run and Verify

1. **Run the script** against the .tm7 file
2. **Verify changes** programmatically:
   - Count border elements, data flows, and threats before/after
   - Check for double-escaped XML entities (`&amp;amp;`)
   - Verify new GUIDs are present
   - Verify Out Of Scope flags are set correctly
   - Verify trust boundary dimensions encompass intended elements
3. **Report results** to the user with a summary table

Tell the user to open the .tm7 in Microsoft Threat Modeling Tool to visually verify:
- Element positions and layout
- Arrow label readability (no overlaps)
- Trust boundary coverage
- Threat list completeness

## Best Practices

### XML Manipulation
- **Always use string-based manipulation** (find/replace) — never DOM parsers for .tm7 files
- **XML-escape all user-facing text** before inserting: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`
- **Avoid double-escaping**: if a value is already escaped in the Python source, do not escape it again in the builder function
- **Use deterministic GUIDs** for reproducibility — hardcode them as constants

### Naming Conventions
- **Arrow labels**: Use format `N. Operation (Auth)` — e.g., `5. Create Issue (GitHub App)`
- **Auth methods**: MSI, GitHub App, GitHub Login, OAuth, Access Token, API Key, etc.
- **Element names**: Use clear, descriptive names matching the design diagram

### Positioning
- **Spread arrow handle positions** to avoid label overlap — vary HandleX/HandleY coordinates
- **Expand trust boundaries** with 50px padding around contained elements
- **Keep elements within their trust boundaries** — verify positions against boundary coordinates

### Threat Quality
- Write **specific, actionable threat descriptions** — not generic boilerplate
- Include **concrete mitigations** relevant to the specific technology and auth method
- Set appropriate **priority**: High for credential theft, code injection, privilege escalation; Medium for audit/logging gaps
- Update **InteractionString** in threats when renaming data flows

### Annotation
- Maintain a **step-by-step annotation box** describing the entire workflow
- Update it whenever new flows are added
- Expand the annotation box dimensions to fit additional text

## Output Artifacts

When done, produce:
1. **Python update script** — idempotent where possible, with `--input` / `--output` args
2. **Changes summary** (Markdown) — table of all elements, flows, and threats added
3. **Updated .tm7 file** — ready to open in Microsoft Threat Modeling Tool
