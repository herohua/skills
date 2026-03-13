# TM7 File Format Reference

Reference guide for working with Microsoft Threat Modeling Tool `.tm7` files programmatically.

## File Structure

The `.tm7` file is WCF DataContract-serialized XML with root element `<ThreatModel>`. The file is typically stored as a single line of XML (no pretty-printing).

### Top-Level Elements

| Element | Description |
|---------|-------------|
| `DrawingSurfaceList` | Contains DFD diagrams (Borders + Lines) |
| `MetaInformation` | Model metadata |
| `Notes` | Free-text notes |
| `ThreatInstances` | All identified threats |
| `ThreatGenerationEnabled` | Boolean flag |
| `Validations` | Validation results |
| `KnowledgeBase` | Template definitions (element types, threat types, STRIDE categories) |
| `Profile` | Template profile info |

### XML Namespaces

| Prefix | URI | Purpose |
|--------|-----|---------|
| *(default/root)* | `http://schemas.datacontract.org/2004/07/ThreatModeling.Model` | Root `ThreatModel` |
| `i:` | `http://www.w3.org/2001/XMLSchema-instance` | Type attributes, nil markers |
| `z:` | `http://schemas.microsoft.com/2003/10/Serialization/` | Serialization IDs |
| `a:` | `http://schemas.microsoft.com/2003/10/Serialization/Arrays` | Array/dictionary containers |
| `b:` | `http://schemas.datacontract.org/2004/07/ThreatModeling.KnowledgeBase` | KB types, threats |
| `c:` | `http://www.w3.org/2001/XMLSchema` | Typed values (`c:string`, `c:boolean`) |
| `abs` (inline) | `http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts` | Base element properties |

The abstract namespace is used inline (not as a prefix) in element properties: `xmlns="http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts"`.

### Insertion Points

When adding new elements, insert them before the closing tag of the relevant section:

| Section | Insert Before | Content Type |
|---------|--------------|--------------|
| Borders | `</Borders>` | Stencils (processes, data stores, external interactors, trust boundaries, annotations) |
| Lines | `</Lines>` | Data flows (connectors) |
| ThreatInstances | `</ThreatInstances>` | Threat entries |

## DFD Element Types

All DFD elements are stored as `<a:KeyValueOfguidanyType>` entries with `<a:Key>` (GUID) and `<a:Value>` (typed element).

### GenericTypeId Mapping

| GenericTypeId | DFD Concept | Visual `i:type` |
|---------------|-------------|-----------------|
| `GE.P` | Process | `StencilEllipse` |
| `GE.DS` | Data Store | `StencilParallelLines` |
| `GE.EI` | External Interactor | `StencilRectangle` |
| `GE.DF` | Data Flow | `Connector` |
| `GE.TB.B` | Trust Border Boundary | `BorderBoundary` |
| `GE.TB.L` | Trust Line Boundary | `LineBoundary` |
| `GE.A` | Free Text Annotation | `StencilRectangle` |

### Specialized TypeIds

| TypeId | Description |
|--------|-------------|
| `SE.P.TMCore.WebAPI` | Web API process |
| `SE.P.TMCore.WebApp` | Web Application process |
| `SE.P.TMCore.AzureEventHub` | Azure Event Hub |
| `SE.DF.TMCore.Request` | Request data flow |
| `SE.DF.TMCore.Response` | Response data flow |
| `SE.TB.TMCore.RemoteUserTrustBoundary` | Remote user trust boundary |

## Element XML Templates

### External Interactor (StencilRectangle)

```xml
<a:KeyValueOfguidanyType>
<a:Key>{GUID}</a:Key>
<a:Value z:Id="i{Z_ID}" i:type="StencilRectangle">
<GenericTypeId xmlns="{ABS_NS}">GE.EI</GenericTypeId>
<Guid xmlns="{ABS_NS}">{GUID}</Guid>
<Properties xmlns="{ABS_NS}">
<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>External Interactor</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>
<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Name</b:DisplayName><b:Name/>
<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{NAME}</b:Value></a:anyType>
<a:anyType i:type="b:BooleanDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Out Of Scope</b:DisplayName><b:Name>71f3d9aa-b8ef-4e54-8126-607a1d903103</b:Name>
<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">{OUT_OF_SCOPE}</b:Value></a:anyType>
<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Reason For Out Of Scope</b:DisplayName><b:Name>752473b6-52d4-4776-9a24-202153f7d579</b:Name>
<b:Value i:type="c:string" xmlns:c="{XSD_NS}"/></a:anyType>
</Properties>
<TypeId xmlns="{ABS_NS}">GE.EI</TypeId>
<Height xmlns="{ABS_NS}">{HEIGHT}</Height>
<Left xmlns="{ABS_NS}">{LEFT}</Left>
<StrokeDashArray i:nil="true" xmlns="{ABS_NS}"/>
<StrokeThickness xmlns="{ABS_NS}">1</StrokeThickness>
<Top xmlns="{ABS_NS}">{TOP}</Top>
<Width xmlns="{ABS_NS}">{WIDTH}</Width>
</a:Value></a:KeyValueOfguidanyType>
```

### Process (StencilEllipse)

Same structure as External Interactor but with:
- `i:type="StencilEllipse"`
- `<GenericTypeId>GE.P</GenericTypeId>`
- Header `<b:DisplayName>Generic Process</b:DisplayName>`
- `<TypeId>GE.P</TypeId>` (or specialized like `SE.P.TMCore.WebAPI`)

### Data Flow Connector

```xml
<a:KeyValueOfguidanyType>
<a:Key>{GUID}</a:Key>
<a:Value z:Id="i{Z_ID}" i:type="Connector">
<GenericTypeId xmlns="{ABS_NS}">GE.DF</GenericTypeId>
<Guid xmlns="{ABS_NS}">{GUID}</Guid>
<Properties xmlns="{ABS_NS}">
<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Request</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>
<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Name</b:DisplayName><b:Name/>
<b:Value i:type="c:string" xmlns:c="{XSD_NS}">{NAME}</b:Value></a:anyType>
<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Dataflow Order</b:DisplayName><b:Name>15ccd509-98eb-49ad-b9c2-b4a2926d1780</b:Name>
<b:Value i:type="c:string" xmlns:c="{XSD_NS}">0</b:Value></a:anyType>
<a:anyType i:type="b:BooleanDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Out Of Scope</b:DisplayName><b:Name>71f3d9aa-b8ef-4e54-8126-607a1d903103</b:Name>
<b:Value i:type="c:boolean" xmlns:c="{XSD_NS}">false</b:Value></a:anyType>
<a:anyType i:type="b:StringDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Reason For Out Of Scope</b:DisplayName><b:Name>752473b6-52d4-4776-9a24-202153f7d579</b:Name>
<b:Value i:type="c:string" xmlns:c="{XSD_NS}"/></a:anyType>
<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Configurable Attributes</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>
<a:anyType i:type="b:HeaderDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>As Generic Data Flow</b:DisplayName><b:Name/><b:Value i:nil="true"/></a:anyType>
<a:anyType i:type="b:ListDisplayAttribute" xmlns:b="{KB_NS}">
<b:DisplayName>Show Boundary Threats</b:DisplayName><b:Name>23e2b6f4-fcd8-4e76-a04a-c9ff9aff4f59</b:Name>
<b:Value i:type="a:ArrayOfstring"><a:string>Select</a:string><a:string>Yes</a:string><a:string>No</a:string></b:Value>
<b:SelectedIndex>0</b:SelectedIndex></a:anyType>
</Properties>
<TypeId xmlns="{ABS_NS}">SE.DF.TMCore.Request</TypeId>
<HandleX xmlns="{ABS_NS}">{HANDLE_X}</HandleX>
<HandleY xmlns="{ABS_NS}">{HANDLE_Y}</HandleY>
<PortSource xmlns="{ABS_NS}">{PORT_SOURCE}</PortSource>
<PortTarget xmlns="{ABS_NS}">{PORT_TARGET}</PortTarget>
<SourceGuid xmlns="{ABS_NS}">{SOURCE_GUID}</SourceGuid>
<SourceX xmlns="{ABS_NS}">{SOURCE_X}</SourceX>
<SourceY xmlns="{ABS_NS}">{SOURCE_Y}</SourceY>
<TargetGuid xmlns="{ABS_NS}">{TARGET_GUID}</TargetGuid>
<TargetX xmlns="{ABS_NS}">{TARGET_X}</TargetX>
<TargetY xmlns="{ABS_NS}">{TARGET_Y}</TargetY>
</a:Value></a:KeyValueOfguidanyType>
```

**Port values**: `North`, `South`, `East`, `West`, `NorthWest`, `NorthEast`, `SouthWest`, `SouthEast`

**Coordinate guidance**:
- `SourceX/SourceY`: connection point on the source element
- `TargetX/TargetY`: connection point on the target element
- `HandleX/HandleY`: midpoint label position — vary these to avoid overlapping labels

## Threat Instance Template

```xml
<a:KeyValueOfstringThreatpc_P0_PhOB>
<a:Key>{TYPE_ID}{SOURCE_GUID}{FLOW_GUID}{TARGET_GUID}</a:Key>
<a:Value xmlns:b="{KB_NS}">
<b:ChangedBy i:nil="true"/>
<b:DrawingSurfaceGuid>{DRAWING_SURFACE_GUID}</b:DrawingSurfaceGuid>
<b:FlowGuid>{FLOW_GUID}</b:FlowGuid>
<b:Id>{THREAT_ID}</b:Id>
<b:InteractionKey>{SOURCE_GUID}:{FLOW_GUID}:{TARGET_GUID}</b:InteractionKey>
<b:InteractionString i:nil="true"/>
<b:ModifiedAt>0001-01-01T00:00:00</b:ModifiedAt>
<b:Priority>{PRIORITY}</b:Priority>
<b:Properties>
<a:KeyValueOfstringstring><a:Key>Title</a:Key><a:Value>{TITLE}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>UserThreatCategory</a:Key><a:Value>{CATEGORY}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>UserThreatShortDescription</a:Key><a:Value>{SHORT_DESC}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>UserThreatDescription</a:Key><a:Value>{DESCRIPTION}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>InteractionString</a:Key><a:Value>{FLOW_NAME}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>PossibleMitigations</a:Key><a:Value>{MITIGATIONS}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>Priority</a:Key><a:Value>{PRIORITY}</a:Value></a:KeyValueOfstringstring>
<a:KeyValueOfstringstring><a:Key>SDLPhase</a:Key><a:Value>{SDL_PHASE}</a:Value></a:KeyValueOfstringstring>
</b:Properties>
<b:SourceGuid>{SOURCE_GUID}</b:SourceGuid>
<b:State>AutoGenerated</b:State>
<b:StateInformation i:nil="true"/>
<b:TargetGuid>{TARGET_GUID}</b:TargetGuid>
<b:Title i:nil="true"/>
<b:TypeId>{TYPE_ID}</b:TypeId>
<b:Upgraded>false</b:Upgraded>
<b:UserThreatCategory i:nil="true"/>
<b:UserThreatDescription i:nil="true"/>
<b:UserThreatShortDescription i:nil="true"/>
<b:Wide>false</b:Wide>
</a:Value></a:KeyValueOfstringThreatpc_P0_PhOB>
```

### Threat Key Formula

`Key = {TypeId}{SourceGuid}{FlowGuid}{TargetGuid}` (concatenated, no separators)

### InteractionKey Formula

`InteractionKey = {SourceGuid}:{FlowGuid}:{TargetGuid}` (colon-separated)

## Well-Known Property GUIDs

| GUID | Property |
|------|----------|
| `71f3d9aa-b8ef-4e54-8126-607a1d903103` | Out Of Scope (boolean) |
| `752473b6-52d4-4776-9a24-202153f7d579` | Reason For Out Of Scope (string) |
| `15ccd509-98eb-49ad-b9c2-b4a2926d1780` | Dataflow Order (string) |
| `23e2b6f4-fcd8-4e76-a04a-c9ff9aff4f59` | Show Boundary Threats (list) |

## Namespace Constants for Python Scripts

```python
ABS_NS = "http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts"
KB_NS = "http://schemas.datacontract.org/2004/07/ThreatModeling.KnowledgeBase"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
```

## z:Id Sequencing

Every `<a:Value>` element gets a sequential `z:Id` attribute (`i1`, `i2`, ...). When adding new elements, continue from the last used value. The KnowledgeBase element is typically the last in the sequence.

To find the last z:Id, search for the highest `z:Id="iN"` in the file.

## Common Threat TypeIds

| TypeId | Typical Use | STRIDE |
|--------|------------|--------|
| `TH7` | Credential/token theft | Spoofing |
| `TH16` | Sniffing traffic | Information Disclosure |
| `TH30` | Insufficient audit trail | Repudiation |
| `TH32` | Spoof via insecure TLS | Spoofing |
| `TH58` | Reuse auth tokens | Spoofing |
| `TH59` | Exploit token permissions | Elevation of Privileges |
| `TH61` | Eavesdrop communication | Tampering |
| `TH62` | Gain elevated privileges | Elevation of Privileges |
| `TH81` | Phishing / fake website | Spoofing |
| `TH83` | Sensitive data in config | Information Disclosure |
| `TH86` | Spoofing source identity | Spoofing |
| `TH94` | Sensitive info in errors | Information Disclosure |
| `TH96` | Injection / input tampering | Tampering |
| `TH97` | SQL injection via API | Tampering |
| `TH101` | Reverse encrypted content | Information Disclosure |
| `TH102` | Sensitive data in logs | Information Disclosure |
| `TH108` | Malicious API inputs | Tampering |
| `TH109` | Deny malicious act | Repudiation |
| `TH110` | Poor access control / EoP | Elevation of Privileges |

## STRIDE Categories

| Id | Category | Short Description |
|----|----------|-------------------|
| `S` | Spoofing | Impersonating another entity |
| `T` | Tampering | Altering data or code |
| `R` | Repudiation | Denying an action was performed |
| `I` | Information Disclosure | Exposing data to unauthorized parties |
| `D` | Denial of Service | Overwhelming a resource |
| `E` | Elevation of Privileges | Gaining unauthorized access |
