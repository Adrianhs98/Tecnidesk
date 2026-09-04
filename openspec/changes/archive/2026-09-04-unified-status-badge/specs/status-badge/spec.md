# Spec: StatusBadge Component

## Capability: status-badge
Render consistent, accessible ticket status badges with theme-aware colors, borders, and icons defined in `DESIGN.md`.

### Requirement: Known Ticket Statuses
The component MUST render the label, custom background color, text color, border tint, and icon corresponding to the status in `STATUS_CONFIG`.

#### Scenario: Render "Recibido" status
- **Given** a status value `"EN_ESPERA_INGRESO"`
- **When** the `<StatusBadge status="EN_ESPERA_INGRESO" />` is rendered
- **Then** the badge displays the label text `"Recibido"`
- **And** it applies text color `#0369a1`, background `#f0f9ff`, and border `#bae6fd`
- **And** it includes the `"REC"` icon indicator

#### Scenario: Render "Esperando repuesto" status
- **Given** a status value `"ESPERANDO_REPUESTO"`
- **When** the `<StatusBadge status="ESPERANDO_REPUESTO" />` is rendered
- **Then** the badge displays the label text `"Esperando repuesto"`
- **And** it applies violet text color `#6d28d9`, background `#f5f3ff`, and border `#ddd6fe`

#### Scenario: Render "Listo para retirar" status
- **Given** a status value `"LISTO_PARA_RETIRAR"`
- **When** the `<StatusBadge status="LISTO_PARA_RETIRAR" />` is rendered
- **Then** the badge displays the label text `"Listo"`
- **And** it applies emerald text color `#047857`, background `#ecfdf5`, and border `#a7f3d0`

### Requirement: Fallback for Unknown or Custom Statuses
The component MUST handle invalid, custom, or missing status keys gracefully without breaking the layout.

#### Scenario: Unrecognized status key
- **Given** an unrecognized status `"ESTADO_DESCONOCIDO"`
- **When** `<StatusBadge status="ESTADO_DESCONOCIDO" />` is rendered
- **Then** the badge displays the fallback label `"ESTADO_DESCONOCIDO"`
- **And** it applies neutral styling without throwing an exception

### Requirement: Icon Visibility Control
The component MUST allow consumers to omit or hide the status icon.

#### Scenario: Badge with icons disabled
- **Given** status `"EN_REVISION"` and prop `showIcon={false}`
- **When** `<StatusBadge status="EN_REVISION" showIcon={false} />` is rendered
- **Then** the badge displays the label text `"En revision"`
- **And** no leading icon element is rendered
