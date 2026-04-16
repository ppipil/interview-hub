## MODIFIED Requirements

### Requirement: Backend SHALL orchestrate one fixed SecondMe interviewer

The backend SHALL support one configured SecondMe avatar interviewer using environment-provided credentials and share code, and SHALL use a realtime client implementation compatible with the active SecondMe websocket gateway.

#### Scenario: Realtime connection succeeds with the compatible client

- **WHEN** the backend receives a websocket URL from SecondMe during session bootstrap
- **THEN** it SHALL establish the realtime connection using a compatible websocket client implementation
- **AND** it SHALL preserve the existing async interview orchestration contract for the rest of the backend

#### Scenario: Realtime connection sends configured Origin header

- **WHEN** the backend opens the realtime websocket connection
- **THEN** it SHALL send the configured websocket Origin header
- **AND** the Origin value SHALL remain overrideable through environment variables
