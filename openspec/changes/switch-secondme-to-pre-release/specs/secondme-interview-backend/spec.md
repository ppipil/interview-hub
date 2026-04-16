## MODIFIED Requirements

### Requirement: Backend SHALL orchestrate one fixed SecondMe interviewer

The backend SHALL support one configured SecondMe avatar interviewer using environment-provided credentials and share code, and the local MVP development default SHALL target a reachable SecondMe environment.

#### Scenario: Local MVP uses the active reachable environment

- **WHEN** the backend loads its default SecondMe base URL for local development
- **THEN** it SHALL default to the pre-release environment `https://mindos-prek8s.mindverse.ai/gate/in`
- **AND** the base URL SHALL remain overrideable through environment variables
