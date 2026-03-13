"""
Reusable builder functions for .tm7 threat model file manipulation.

Copy this file into your update script and call the functions as needed.
All functions produce XML strings compatible with Microsoft Threat Modeling Tool.

Usage:
    from tm7_builders import *

    # or copy the functions you need directly into your script
"""

# =============================================================================
# CONSTANTS
# =============================================================================

ABS_NS = "http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts"
KB_NS = "http://schemas.datacontract.org/2004/07/ThreatModeling.KnowledgeBase"
XSD_NS = "http://www.w3.org/2001/XMLSchema"


def xml_escape(text):
    """Escape text for safe inclusion in XML values."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# =============================================================================
# ELEMENT BUILDERS — produce XML strings to insert before </Borders> or </Lines>
# =============================================================================

def make_external_interactor(guid, z_id, name, left, top,
                             width=104, height=100, out_of_scope="false"):
    """Create an External Interactor (StencilRectangle, GE.EI)."""
    return (
        f'<a:KeyValueOfguidanyType>'
        f'<a:Key>{guid}</a:Key>'
        f'<a:Value z:Id="i{z_id}" i:type="StencilRectangle">'
        f'<GenericTypeId xmlns="{ABS_NS}">GE.EI</GenericTypeId>'
        f'<Guid xmlns="{ABS_NS}">{guid}</Guid>'
        f'<Properties xmlns="{ABS_NS}">'
        f'<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>External Interactor</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Name</b:DisplayName><b:Name/>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{xml_escape(name)}</b:Value></a:anyType>'
        f'<a:anyType i:type="b:BooleanDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Out Of Scope</b:DisplayName>'
        f'<b:Name>71f3d9aa-b8ef-4e54-8126-607a1d903103</b:Name>'
        f'<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">{out_of_scope}</b:Value></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Reason For Out Of Scope</b:DisplayName>'
        f'<b:Name>752473b6-52d4-4776-9a24-202153f7d579</b:Name>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}"/></a:anyType>'
        f'</Properties>'
        f'<TypeId xmlns="{ABS_NS}">GE.EI</TypeId>'
        f'<Height xmlns="{ABS_NS}">{height}</Height>'
        f'<Left xmlns="{ABS_NS}">{left}</Left>'
        f'<StrokeDashArray i:nil="true" xmlns="{ABS_NS}"/>'
        f'<StrokeThickness xmlns="{ABS_NS}">1</StrokeThickness>'
        f'<Top xmlns="{ABS_NS}">{top}</Top>'
        f'<Width xmlns="{ABS_NS}">{width}</Width>'
        f'</a:Value></a:KeyValueOfguidanyType>'
    )


def make_process(guid, z_id, name, left, top,
                 width=104, height=100, out_of_scope="false"):
    """Create a Process (StencilEllipse, GE.P)."""
    return (
        f'<a:KeyValueOfguidanyType>'
        f'<a:Key>{guid}</a:Key>'
        f'<a:Value z:Id="i{z_id}" i:type="StencilEllipse">'
        f'<GenericTypeId xmlns="{ABS_NS}">GE.P</GenericTypeId>'
        f'<Guid xmlns="{ABS_NS}">{guid}</Guid>'
        f'<Properties xmlns="{ABS_NS}">'
        f'<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Generic Process</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Name</b:DisplayName><b:Name/>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{xml_escape(name)}</b:Value></a:anyType>'
        f'<a:anyType i:type="b:BooleanDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Out Of Scope</b:DisplayName>'
        f'<b:Name>71f3d9aa-b8ef-4e54-8126-607a1d903103</b:Name>'
        f'<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">{out_of_scope}</b:Value></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Reason For Out Of Scope</b:DisplayName>'
        f'<b:Name>752473b6-52d4-4776-9a24-202153f7d579</b:Name>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}"/></a:anyType>'
        f'</Properties>'
        f'<TypeId xmlns="{ABS_NS}">GE.P</TypeId>'
        f'<Height xmlns="{ABS_NS}">{height}</Height>'
        f'<Left xmlns="{ABS_NS}">{left}</Left>'
        f'<StrokeDashArray i:nil="true" xmlns="{ABS_NS}"/>'
        f'<StrokeThickness xmlns="{ABS_NS}">1</StrokeThickness>'
        f'<Top xmlns="{ABS_NS}">{top}</Top>'
        f'<Width xmlns="{ABS_NS}">{width}</Width>'
        f'</a:Value></a:KeyValueOfguidanyType>'
    )


def make_connector(guid, z_id, name, source_guid, target_guid,
                   source_x, source_y, target_x, target_y,
                   handle_x, handle_y,
                   port_source="East", port_target="West"):
    """Create a data flow connector (Connector, GE.DF).

    Args:
        guid:        New GUID for this connector.
        z_id:        Next z:Id sequence number.
        name:        Display name, e.g. "5. Create Issue (GitHub App)".
                     Plain text — will be XML-escaped automatically.
        source_guid: GUID of the source stencil.
        target_guid: GUID of the target stencil.
        source_x/y:  Connection point on source element.
        target_x/y:  Connection point on target element.
        handle_x/y:  Midpoint label position — vary to avoid overlap.
        port_source:  Port on source (North/South/East/West/NW/NE/SW/SE).
        port_target:  Port on target.
    """
    escaped_name = xml_escape(name)
    return (
        f'<a:KeyValueOfguidanyType>'
        f'<a:Key>{guid}</a:Key>'
        f'<a:Value z:Id="i{z_id}" i:type="Connector">'
        f'<GenericTypeId xmlns="{ABS_NS}">GE.DF</GenericTypeId>'
        f'<Guid xmlns="{ABS_NS}">{guid}</Guid>'
        f'<Properties xmlns="{ABS_NS}">'
        f'<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Request</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Name</b:DisplayName><b:Name/>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{escaped_name}</b:Value></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Dataflow Order</b:DisplayName>'
        f'<b:Name>15ccd509-98eb-49ad-b9c2-b4a2926d1780</b:Name>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}">0</b:Value></a:anyType>'
        f'<a:anyType i:type="b:BooleanDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Out Of Scope</b:DisplayName>'
        f'<b:Name>71f3d9aa-b8ef-4e54-8126-607a1d903103</b:Name>'
        f'<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">false</b:Value></a:anyType>'
        f'<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Reason For Out Of Scope</b:DisplayName>'
        f'<b:Name>752473b6-52d4-4776-9a24-202153f7d579</b:Name>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}"/></a:anyType>'
        f'<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Configurable Attributes</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>'
        f'<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>As Generic Data Flow</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>'
        f'<a:anyType i:type="b:ListDisplayAttribute" xmlns:b="{KB_NS}">'
        f'<b:DisplayName>Show Boundary Threats</b:DisplayName>'
        f'<b:Name>23e2b6f4-fcd8-4e76-a04a-c9ff9aff4f59</b:Name>'
        f'<b:Value i:type="a:ArrayOfstring">'
        f'<a:string>Select</a:string><a:string>Yes</a:string><a:string>No</a:string></b:Value>'
        f'<b:SelectedIndex>0</b:SelectedIndex></a:anyType>'
        f'</Properties>'
        f'<TypeId xmlns="{ABS_NS}">SE.DF.TMCore.Request</TypeId>'
        f'<HandleX xmlns="{ABS_NS}">{handle_x}</HandleX>'
        f'<HandleY xmlns="{ABS_NS}">{handle_y}</HandleY>'
        f'<PortSource xmlns="{ABS_NS}">{port_source}</PortSource>'
        f'<PortTarget xmlns="{ABS_NS}">{port_target}</PortTarget>'
        f'<SourceGuid xmlns="{ABS_NS}">{source_guid}</SourceGuid>'
        f'<SourceX xmlns="{ABS_NS}">{source_x}</SourceX>'
        f'<SourceY xmlns="{ABS_NS}">{source_y}</SourceY>'
        f'<TargetGuid xmlns="{ABS_NS}">{target_guid}</TargetGuid>'
        f'<TargetX xmlns="{ABS_NS}">{target_x}</TargetX>'
        f'<TargetY xmlns="{ABS_NS}">{target_y}</TargetY>'
        f'</a:Value></a:KeyValueOfguidanyType>'
    )


def make_threat(threat_id, type_id, drawing_surface_guid,
                source_guid, flow_guid, target_guid,
                title, category, short_desc, description,
                interaction_name, possible_mitigations,
                priority="High", sdl_phase="Implementation"):
    """Create a threat instance to insert before </ThreatInstances>.

    Args:
        threat_id:             Unique numeric ID (continue from last existing).
        type_id:               Threat type from KnowledgeBase (e.g. "TH7", "TH96").
        drawing_surface_guid:  GUID of the containing diagram.
        source_guid:           GUID of the source stencil.
        flow_guid:             GUID of the data flow connector.
        target_guid:           GUID of the target stencil.
        title:                 Threat title — plain text, auto-escaped.
        category:              STRIDE category name (e.g. "Spoofing").
        short_desc:            Brief STRIDE description.
        description:           Full threat description — plain text, auto-escaped.
        interaction_name:      Data flow display name — must match the connector's Name.
                               Plain text, auto-escaped.
        possible_mitigations:  Suggested mitigations — plain text, auto-escaped.
        priority:              "High", "Medium", or "Low".
        sdl_phase:             "Implementation", "Design", etc.
    """
    key = f"{type_id}{source_guid}{flow_guid}{target_guid}"
    interaction_key = f"{source_guid}:{flow_guid}:{target_guid}"
    return (
        f'<a:KeyValueOfstringThreatpc_P0_PhOB>'
        f'<a:Key>{key}</a:Key>'
        f'<a:Value xmlns:b="{KB_NS}">'
        f'<b:ChangedBy i:nil="true"/>'
        f'<b:DrawingSurfaceGuid>{drawing_surface_guid}</b:DrawingSurfaceGuid>'
        f'<b:FlowGuid>{flow_guid}</b:FlowGuid>'
        f'<b:Id>{threat_id}</b:Id>'
        f'<b:InteractionKey>{interaction_key}</b:InteractionKey>'
        f'<b:InteractionString i:nil="true"/>'
        f'<b:ModifiedAt>0001-01-01T00:00:00</b:ModifiedAt>'
        f'<b:Priority>{priority}</b:Priority>'
        f'<b:Properties>'
        f'<a:KeyValueOfstringstring><a:Key>Title</a:Key>'
        f'<a:Value>{xml_escape(title)}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>UserThreatCategory</a:Key>'
        f'<a:Value>{category}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>UserThreatShortDescription</a:Key>'
        f'<a:Value>{short_desc}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>UserThreatDescription</a:Key>'
        f'<a:Value>{xml_escape(description)}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>InteractionString</a:Key>'
        f'<a:Value>{xml_escape(interaction_name)}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>PossibleMitigations</a:Key>'
        f'<a:Value>{xml_escape(possible_mitigations)}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>Priority</a:Key>'
        f'<a:Value>{priority}</a:Value></a:KeyValueOfstringstring>'
        f'<a:KeyValueOfstringstring><a:Key>SDLPhase</a:Key>'
        f'<a:Value>{sdl_phase}</a:Value></a:KeyValueOfstringstring>'
        f'</b:Properties>'
        f'<b:SourceGuid>{source_guid}</b:SourceGuid>'
        f'<b:State>AutoGenerated</b:State>'
        f'<b:StateInformation i:nil="true"/>'
        f'<b:TargetGuid>{target_guid}</b:TargetGuid>'
        f'<b:Title i:nil="true"/>'
        f'<b:TypeId>{type_id}</b:TypeId>'
        f'<b:Upgraded>false</b:Upgraded>'
        f'<b:UserThreatCategory i:nil="true"/>'
        f'<b:UserThreatDescription i:nil="true"/>'
        f'<b:UserThreatShortDescription i:nil="true"/>'
        f'<b:Wide>false</b:Wide>'
        f'</a:Value></a:KeyValueOfstringThreatpc_P0_PhOB>'
    )


# =============================================================================
# MODIFICATION HELPERS — modify properties of existing elements in-place
# =============================================================================

def set_element_boolean(content, element_guid, property_name_guid, new_value):
    """Set a boolean property on an element identified by its GUID.

    Args:
        content:            Full .tm7 file content string.
        element_guid:       GUID of the target element.
        property_name_guid: GUID of the property (e.g. Out Of Scope GUID).
        new_value:          "true" or "false".

    Returns:
        Modified content string.

    Example — set PR Auto Merger out of scope:
        content = set_element_boolean(content,
            "c3d4e5f6-...", "71f3d9aa-...", "true")
    """
    marker = f'<a:Key>{element_guid}</a:Key>'
    idx = content.find(marker)
    if idx == -1:
        print(f"  WARNING: Element {element_guid} not found")
        return content

    region = content[idx:idx + 2000]
    for old_val, new_val in [("false", new_value), ("true", new_value)]:
        if old_val == new_value:
            continue
        old = (f'<b:Name>{property_name_guid}</b:Name>'
               f'<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">{old_val}</b:Value>')
        new = (f'<b:Name>{property_name_guid}</b:Name>'
               f'<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">{new_val}</b:Value>')
        pos = region.find(old)
        if pos != -1:
            abs_pos = idx + pos
            content = content[:abs_pos] + new + content[abs_pos + len(old):]
            print(f"  Set {property_name_guid} = {new_value} on {element_guid[:8]}...")
            break
    return content


OUT_OF_SCOPE_GUID = "71f3d9aa-b8ef-4e54-8126-607a1d903103"


def set_out_of_scope(content, element_guid, value="true"):
    """Shortcut to set Out Of Scope on an element."""
    return set_element_boolean(content, element_guid, OUT_OF_SCOPE_GUID, value)


def resize_boundary(content, boundary_guid, left, top, width, height):
    """Resize a trust boundary element.

    Args:
        content:        Full .tm7 file content string.
        boundary_guid:  GUID of the trust boundary element.
        left/top:       New position.
        width/height:   New dimensions.

    Tip: to compute dimensions that encompass elements, use 50px padding:
        left   = min(element_lefts) - 50
        top    = min(element_tops) - 50
        right  = max(element_left + element_width) + 50
        bottom = max(element_top + element_height) + 50
        width  = right - left
        height = bottom - top
    """
    marker = f'<a:Key>{boundary_guid}</a:Key>'
    idx = content.find(marker)
    if idx == -1:
        print(f"  WARNING: Boundary {boundary_guid} not found")
        return content

    import re
    region_start = idx
    region = content[region_start:region_start + 3000]

    props = [
        (f'Left xmlns="{ABS_NS}"', left),
        (f'Top xmlns="{ABS_NS}"', top),
        (f'Width xmlns="{ABS_NS}"', width),
        (f'Height xmlns="{ABS_NS}"', height),
    ]
    for tag, new_val in props:
        pattern = f'<{tag}>\\d+</'
        match = re.search(pattern, region)
        if match:
            old_text = match.group()
            new_text = f'<{tag}>{new_val}</'
            abs_pos = region_start + match.start()
            content = content[:abs_pos] + new_text + content[abs_pos + len(old_text):]
            region = content[region_start:region_start + 3000]

    print(f"  Resized boundary {boundary_guid[:8]}...: L={left}, T={top}, W={width}, H={height}")
    return content


def rename_data_flow(content, old_name, new_name):
    """Rename a data flow arrow and update threat InteractionStrings.

    Args:
        content:   Full .tm7 file content string.
        old_name:  Current display name (plain text, e.g. "5. Create Issue (Access Token)").
        new_name:  New display name (plain text, e.g. "5. Create Issue (GitHub App)").
    """
    old_escaped = xml_escape(old_name)
    new_escaped = xml_escape(new_name)

    old_pattern = (
        f'<b:DisplayName>Name</b:DisplayName><b:Name/>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{old_escaped}</b:Value>'
    )
    new_pattern = (
        f'<b:DisplayName>Name</b:DisplayName><b:Name/>'
        f'<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{new_escaped}</b:Value>'
    )

    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern, 1)
        print(f"  Renamed: '{old_name}' -> '{new_name}'")
    else:
        print(f"  WARNING: Data flow '{old_name}' not found")

    # Also update InteractionString in threats
    old_interaction = f'<a:Key>InteractionString</a:Key><a:Value>{old_escaped}</a:Value>'
    new_interaction = f'<a:Key>InteractionString</a:Key><a:Value>{new_escaped}</a:Value>'
    count = content.count(old_interaction)
    if count > 0:
        content = content.replace(old_interaction, new_interaction)
        print(f"    Updated {count} threat InteractionString references")

    return content


# =============================================================================
# SCRIPT BOILERPLATE — use this as main() template
# =============================================================================

SCRIPT_TEMPLATE = '''
import argparse

def main():
    parser = argparse.ArgumentParser(description="Update threat model (.tm7).")
    parser.add_argument("--input", required=True, help="Path to the source .tm7 file")
    parser.add_argument("--output", default=None, help="Output path (default: overwrites input)")
    args = parser.parse_args()
    output_path = args.output or args.input

    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()

    # --- 1. Add new border elements ---
    new_borders = []
    # new_borders.append(make_external_interactor(...))
    # new_borders.append(make_process(...))
    content = content.replace("</Borders>", "".join(new_borders) + "</Borders>")

    # --- 2. Add new data flows ---
    new_lines = []
    # new_lines.append(make_connector(...))
    content = content.replace("</Lines>", "".join(new_lines) + "</Lines>")

    # --- 3. Add new threats ---
    new_threats = []
    # new_threats.append(make_threat(...))
    content = content.replace("</ThreatInstances>", "".join(new_threats) + "</ThreatInstances>")

    # --- 4. Modify existing elements (optional) ---
    # content = set_out_of_scope(content, "element-guid", "true")
    # content = resize_boundary(content, "boundary-guid", left, top, width, height)
    # content = rename_data_flow(content, "old name", "new name")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Done!")

if __name__ == "__main__":
    main()
'''
