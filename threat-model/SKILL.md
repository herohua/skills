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

Read the .tm7 file and extract the current state. See [references/tm7-format.md](references/tm7-format.md) for the full format reference.

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

Write a Python script that uses the builder functions from [references/tm7_builders.py](references/tm7_builders.py). Copy the needed functions into the script — they handle all XML generation and escaping.

#### Script pattern:

```python
import argparse

# Copy builder functions from references/tm7_builders.py:
#   xml_escape, make_external_interactor, make_process,
#   make_connector, make_threat,
#   set_out_of_scope, resize_boundary, rename_data_flow

DRAWING_SURFACE_GUID = "..."  # from Phase 2
# ... other existing GUIDs ...
# ... new deterministic GUIDs ...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add new border elements before </Borders>
    new_borders = []
    new_borders.append(make_external_interactor(GUID, z_id, "Name", left, top))
    new_borders.append(make_process(GUID, z_id, "Name", left, top))
    content = content.replace("</Borders>", "".join(new_borders) + "</Borders>")

    # 2. Add new data flows before </Lines>
    new_lines = []
    new_lines.append(make_connector(GUID, z_id, "N. Operation (Auth)",
        source_guid, target_guid,
        source_x, source_y, target_x, target_y, handle_x, handle_y))
    content = content.replace("</Lines>", "".join(new_lines) + "</Lines>")

    # 3. Add new threats before </ThreatInstances>
    new_threats = []
    new_threats.append(make_threat(threat_id, "TH7", DRAWING_SURFACE_GUID,
        source_guid, flow_guid, target_guid,
        "Threat title", "Spoofing", "Short desc",
        "Full description", "Flow name", "Mitigations"))
    content = content.replace("</ThreatInstances>",
        "".join(new_threats) + "</ThreatInstances>")

    # 4. Modify existing elements
    content = set_out_of_scope(content, element_guid, "true")
    content = resize_boundary(content, boundary_guid, left, top, width, height)
    content = rename_data_flow(content, "old name", "new name")

    with open(args.output or args.input, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
```

#### Available builder functions (see [references/tm7_builders.py](references/tm7_builders.py)):

| Function | Purpose |
|----------|---------|
| `xml_escape(text)` | Escape `&`, `<`, `>` for XML values |
| `make_external_interactor(guid, z_id, name, left, top, ...)` | Create External Interactor element |
| `make_process(guid, z_id, name, left, top, ...)` | Create Process element |
| `make_connector(guid, z_id, name, source_guid, target_guid, ...)` | Create data flow connector |
| `make_threat(threat_id, type_id, drawing_surface_guid, ...)` | Create STRIDE threat instance |
| `set_out_of_scope(content, element_guid, value)` | Set Out Of Scope flag on an element |
| `resize_boundary(content, boundary_guid, left, top, width, height)` | Resize a trust boundary |
| `rename_data_flow(content, old_name, new_name)` | Rename a flow + update threat references |

All text arguments accept **plain text** — escaping is handled internally.

#### STRIDE Threat Generation

For each new data flow, generate threats covering relevant categories:

| Category | When to Apply | Typical TypeId |
|----------|--------------|----------------|
| **Spoofing** | Flow uses credentials/tokens | TH7, TH86 |
| **Tampering** | Flow carries modifiable data | TH96, TH108 |
| **Repudiation** | Automated actions without audit trail | TH30 |
| **Information Disclosure** | Flow could leak sensitive data | TH94, TH101 |
| **Denial of Service** | Flow to shared resource (apply selectively) | — |
| **Elevation of Privileges** | Automated entity has elevated permissions | TH110 |

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
- **Pass plain text to builder functions** — they handle XML escaping internally
- **Avoid double-escaping**: never pre-escape `&` as `&amp;` before passing to builders
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

## Reference Files

| File | Purpose |
|------|---------|
| [references/tm7_builders.py](references/tm7_builders.py) | Reusable Python builder functions — copy into your script |
| [references/tm7-format.md](references/tm7-format.md) | .tm7 XML format specification, namespace reference, threat TypeIds |

## Output Artifacts

When done, produce:
1. **Python update script** — using builders from `tm7_builders.py`, with `--input` / `--output` args
2. **Changes summary** (Markdown) — table of all elements, flows, and threats added
3. **Updated .tm7 file** — ready to open in Microsoft Threat Modeling Tool
