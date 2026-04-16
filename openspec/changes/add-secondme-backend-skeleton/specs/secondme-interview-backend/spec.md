## ADDED Requirements

### Requirement: Backend SHALL expose the existing interview MVP API contract

The backend SHALL expose endpoints for listing interviewers, creating interview sessions, sending user messages, and fetching feedback, aligned with the frontend contract already defined in the repository.

#### Scenario: Frontend requests interviewers

- **WHEN** the frontend calls the interviewer listing endpoint
- **THEN** the backend SHALL return the configured fixed interviewer in the expected response envelope

#### Scenario: Frontend creates a new session

- **WHEN** the frontend calls the session creation endpoint
- **THEN** the backend SHALL initialize an in-memory interview session and return the first question with session metadata

### Requirement: Backend SHALL orchestrate one fixed SecondMe interviewer

The backend SHALL support one configured SecondMe avatar interviewer using environment-provided credentials and share code.

#### Scenario: Session uses configured interviewer

- **WHEN** the frontend requests a session with the configured interviewer id
- **THEN** the backend SHALL use the corresponding SecondMe configuration to bootstrap the interview flow

### Requirement: Backend SHALL keep MVP state in memory

The backend SHALL store interview sessions, message history, runtime websocket metadata, and generated feedback in memory only for this version.

#### Scenario: Session progresses through rounds

- **WHEN** a user sends answers during an active interview
- **THEN** the backend SHALL update the in-memory session and message state without requiring a database
