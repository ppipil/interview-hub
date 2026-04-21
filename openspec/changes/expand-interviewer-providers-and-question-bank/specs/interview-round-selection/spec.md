## ADDED Requirements

### Requirement: Setup flow SHALL allow selecting 1 to 10 interview rounds

The setup flow SHALL expose a round-count selector that allows users to choose between 1 and 10 rounds before starting a session.

#### Scenario: User selects a supported round count
- **WHEN** the user chooses a round count from 1 to 10 in setup
- **THEN** the selected value SHALL be stored in the setup state
- **AND** it SHALL be sent in the create-session request

#### Scenario: Setup initializes with the product default
- **WHEN** the setup screen loads with no previous selection
- **THEN** the default round count SHALL remain 3

### Requirement: Web and API SHALL enforce the same round-count validation

The frontend and backend SHALL share the same accepted round range of 1 through 10 so users cannot select a value that the backend later rejects.

#### Scenario: Frontend prevents unsupported round counts
- **WHEN** a value outside 1 through 10 is entered or selected in the setup flow
- **THEN** the frontend SHALL normalize or reject the value before session creation

#### Scenario: Backend receives an unsupported round count
- **WHEN** the create-session API receives a round count outside 1 through 10
- **THEN** the backend SHALL reject or normalize the value using the same 1 through 10 contract
- **AND** it SHALL not silently fall back to the previous 1 through 3 limit
