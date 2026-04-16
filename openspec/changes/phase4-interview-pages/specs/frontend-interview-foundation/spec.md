## MODIFIED Requirements

### Requirement: Frontend SHALL manage interview flow in a global store

The frontend SHALL provide a Zustand store that manages the entry stage, setup selections, interviewer options, the active session, conversation messages, feedback results, and request state for each async operation.

#### Scenario: User moves from home into setup

- **WHEN** the user clicks the primary home call-to-action
- **THEN** the store SHALL move the frontend flow into the setup stage

#### Scenario: Starting an interview activates session state

- **WHEN** the store successfully initializes an interview session
- **THEN** it SHALL persist the session, selected interviewer, and first question and SHALL move the frontend flow into the interview stage

#### Scenario: Restart clears session-specific state

- **WHEN** the user restarts the interview flow
- **THEN** the store SHALL clear session-specific data without requiring UI components to own workflow state or hardcoded data
