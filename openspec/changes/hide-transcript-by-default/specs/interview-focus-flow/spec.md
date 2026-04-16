## ADDED Requirements

### Requirement: Interview screen SHALL prioritize the active answer flow

The interview screen SHALL place the answer composer directly below the current question. Transcript history MUST NOT be expanded by default.

#### Scenario: User lands on the current question

- **WHEN** the live interview screen renders
- **THEN** the question SHALL be followed immediately by the answer input surface

#### Scenario: Transcript stays secondary

- **WHEN** the live interview screen renders
- **THEN** transcript history SHALL remain hidden until the user explicitly chooses to view it

### Requirement: Interview transcript SHALL remain accessible on demand

The system SHALL preserve transcript history and expose it behind a secondary interaction such as a reveal button or collapsible panel.

#### Scenario: User chooses to inspect previous messages

- **WHEN** the user activates the transcript reveal control
- **THEN** the full transcript history SHALL become visible without losing the active answer state
