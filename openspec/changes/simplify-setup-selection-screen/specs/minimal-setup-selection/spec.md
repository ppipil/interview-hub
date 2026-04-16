## ADDED Requirements

### Requirement: Setup screen SHALL expose only three configuration modules

The setup screen SHALL render only the role selector, mode selector, and interviewer selector as visible configuration modules.

#### Scenario: User opens the setup screen

- **WHEN** the setup screen is displayed
- **THEN** the page SHALL present exactly three configuration sections for role, mode, and interviewer selection

### Requirement: Setup selection modules SHALL omit helper copy

The setup selection modules SHALL not render descriptive helper text beneath the section heading or beneath the selectable option labels.

#### Scenario: User scans setup options

- **WHEN** the setup screen renders the role, mode, and interviewer modules
- **THEN** each module SHALL show only its title and the selectable options without secondary descriptive copy

### Requirement: Setup start action SHALL remain available outside the module count

The setup screen SHALL preserve a start action for the configured interview session without presenting it as a separate informational module.

#### Scenario: User completes required selections

- **WHEN** the user has selected a role, mode, and interviewer
- **THEN** the page SHALL expose a start action in a lightweight bottom action area
