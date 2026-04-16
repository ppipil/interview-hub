## ADDED Requirements

### Requirement: Home screen SHALL render a minimal single-action entry

The home screen SHALL present a minimal entry surface containing one concise line of copy and one primary action button.

#### Scenario: User opens the application

- **WHEN** the application first renders the home stage
- **THEN** the home screen SHALL display one short message and one visible primary button

### Requirement: Home screen SHALL avoid non-essential showcase content

The home screen SHALL not render interviewer galleries, feature cards, or secondary entry actions as part of the primary composition.

#### Scenario: User scans the home screen

- **WHEN** the home stage is visible
- **THEN** the screen SHALL omit extra showcase sections and secondary homepage CTAs
