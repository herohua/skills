# threat-model

Update Microsoft Threat Modeling Tool (`.tm7`) files programmatically using Claude Code. Analyzes existing threat models, generates Python update scripts, and applies STRIDE threat analysis for new or changed system designs.

## Usage

```
/threat-model
```

The skill guides you through an interactive workflow — no arguments needed.

### Example Scenarios

```bash
# Update a threat model with a new design
/threat-model
# Then provide: design flowchart + path to .tm7 file

# Add new components and threats
/threat-model
# Then describe: new external interactors, data flows, trust boundaries
```

## What It Does

### Phase 1: Gather Inputs
Collects the design change (flowchart, Mermaid diagram, architecture doc, or description) and the target `.tm7` file path. Asks clarifying questions about scope, trust boundaries, and authentication methods.

### Phase 2: Analyze Existing .tm7
Reads the threat model file and extracts all current elements — processes, external interactors, data stores, trust boundaries, data flows, threats, and annotations. Records GUIDs and ID sequences for later use.

### Phase 3: Plan Changes
Produces a change plan table covering new elements, data flows, trust boundary modifications, and STRIDE threats. Presents the plan for user approval.

### Phase 4: Generate Update Script
Writes a Python script (no external dependencies) that modifies the `.tm7` file using string-based XML manipulation. Generates STRIDE threats with specific, actionable descriptions and mitigations.

### Phase 5: Run and Verify
Executes the script, verifies changes programmatically (element counts, XML escaping, GUID presence), and reports a summary. Recommends opening in Microsoft Threat Modeling Tool for visual verification.

## Key Features

- **No external dependencies** — Python scripts use only stdlib
- **String-based XML manipulation** — avoids DOM parser issues with WCF DataContract namespaces
- **STRIDE threat generation** — Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privileges
- **Consistent naming** — Arrow labels follow `N. Operation (Auth)` convention
- **Idempotent scripts** — deterministic GUIDs for reproducibility

## File Structure

```
threat-model/
├── SKILL.md                  # Workflow guide and best practices
└── references/
    └── tm7-format.md         # .tm7 XML format reference with templates
```

## Supported Element Types

| Type | DFD Concept | Use Case |
|------|-------------|----------|
| `GE.P` | Process | Internal services, workers, APIs |
| `GE.EI` | External Interactor | Users, third-party services, external systems |
| `GE.DS` | Data Store | Databases, queues, storage accounts |
| `GE.DF` | Data Flow | Connections between elements |
| `GE.TB.B` | Trust Boundary | Azure boundary, network zones |
