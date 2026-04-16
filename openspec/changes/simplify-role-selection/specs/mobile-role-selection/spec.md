## ADDED Requirements

### Requirement: Setup screen SHALL present role selection as a simplified mobile-first list

The setup screen SHALL render the role section as a stacked list of selectable options rather than a dense information card grid.

#### Scenario: User browses available roles

- **WHEN** the setup screen displays the role selection step
- **THEN** each role option SHALL appear as a compact list button in a vertical stack

### Requirement: Role options SHALL display only the role name

The system SHALL show only the role label inside each selectable role option. Supplemental badges, icons, and descriptive body copy MUST NOT appear in the role option itself.

#### Scenario: User scans the role options

- **WHEN** the role selection list is rendered
- **THEN** each option SHALL contain the role name as its primary and only visible content, aside from optional selected-state affordances

### Requirement: Role section copy SHALL stay concise

The setup screen SHALL keep the role section support copy to a single short line so the step reads quickly on mobile-sized layouts.

#### Scenario: User reads the role section header

- **WHEN** the role section header is rendered
- **THEN** the supporting description SHALL appear as one concise sentence beneath the title
