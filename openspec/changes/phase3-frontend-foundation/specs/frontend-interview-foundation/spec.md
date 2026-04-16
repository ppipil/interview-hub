## ADDED Requirements

### Requirement: Frontend SHALL expose shared interview domain types

The frontend SHALL define a single source of truth for interview roles, modes, interviewer metadata, session lifecycle, message payloads, and feedback payloads. These types MUST align with the field names, enum literals, and nullability described in `docs/openapi.yaml`.

#### Scenario: Types map to request and response payloads

- **WHEN** frontend modules import interview request or response contracts
- **THEN** the imported types SHALL represent the payload shapes defined in `docs/openapi.yaml`

#### Scenario: Setup state reuses API enum literals

- **WHEN** the setup flow stores role or mode selections
- **THEN** those values SHALL use the same enum literals as the API contract

### Requirement: Frontend SHALL provide typed mock interview services

The frontend SHALL expose asynchronous mock service functions for listing interviewers, creating interview sessions, sending user answers, and fetching feedback. Each function MUST return a Promise and MUST simulate network latency instead of returning synchronously.

#### Scenario: Session creation returns the first assistant message

- **WHEN** the setup flow requests a new interview session
- **THEN** the mock service SHALL return a response envelope containing the created session, selected interviewer, and first assistant question

#### Scenario: Final answer unlocks feedback fetching

- **WHEN** the user submits the final answer in a session
- **THEN** the mock service SHALL mark the session as completed and SHALL indicate that feedback can be fetched

### Requirement: Frontend SHALL manage interview flow in a global store

The frontend SHALL provide a Zustand store that manages setup selections, interviewer options, the active session, conversation messages, feedback results, and request state for each async operation.

#### Scenario: Starting an interview activates session state

- **WHEN** the store successfully initializes an interview session
- **THEN** it SHALL persist the session, selected interviewer, and first question and SHALL move the frontend flow into the interview stage

#### Scenario: Restart clears session-specific state

- **WHEN** the user restarts the interview flow
- **THEN** the store SHALL clear session-specific data without requiring UI components to own workflow state or hardcoded data
