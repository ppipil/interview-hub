## ADDED Requirements

### Requirement: Web frontend SHALL call the configured backend API

The web frontend SHALL fetch interviewers, create sessions, send interview messages, and fetch feedback through the configured backend API instead of using in-memory mock data.

#### Scenario: Frontend loads interviewers from backend

- **WHEN** the setup flow requests interviewer data
- **THEN** the frontend SHALL call the backend interviewer endpoint
- **AND** it SHALL surface backend error messages through the existing store error handling

#### Scenario: Frontend uses configurable backend base URL

- **WHEN** the frontend constructs API requests
- **THEN** it SHALL use the configured `VITE_API_BASE_URL` value when provided
- **AND** it SHALL keep a sensible local default for MVP development

## MODIFIED Requirements

### Requirement: Backend SHALL expose the existing interview MVP API contract

The backend SHALL continue exposing the existing interview endpoints and SHALL allow configured local web origins to call them during development.

#### Scenario: Local Vite frontend calls backend

- **WHEN** a browser-based frontend running on a configured local development origin sends requests to the backend
- **THEN** the backend SHALL include the required CORS headers so the requests can complete successfully
- **AND** the allowed origins SHALL remain configurable through environment variables
