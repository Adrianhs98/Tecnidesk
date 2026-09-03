# Spec: Theme Customization

## Requirements

### Requirement: Persisted Theme Settings
The system must persist the user's selected theme (light or dark) across browser sessions.

#### Scenario: First-time loading uses OS preference
- **Given** a user opens the application for the first time
- **When** the user's operating system prefers dark mode
- **Then** the application should render in dark mode

#### Scenario: Theme toggle updates state and storage
- **Given** the application is rendered in dark mode
- **When** the user clicks the theme toggle button
- **Then** the application should switch to light mode immediately
- **And** the preference should be saved in localStorage
