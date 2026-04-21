## ADDED Requirements

### Requirement: Interview sessions SHALL route by interviewer provider

The backend SHALL resolve the selected interviewer configuration before creating a session and SHALL route interview execution through the provider assigned to that interviewer.

#### Scenario: User starts a system interviewer session
- **WHEN** a session is created for an interviewer configured as a system interviewer
- **THEN** the backend SHALL use the system-interviewer provider path
- **AND** it SHALL keep the existing session API contract unchanged for the frontend

#### Scenario: User starts an avatar interviewer session
- **WHEN** a session is created for an interviewer configured as an AI avatar interviewer
- **THEN** the backend SHALL use the avatar-interviewer provider path
- **AND** it SHALL keep the existing session API contract unchanged for the frontend

### Requirement: Avatar interviewers SHALL support SecondMe Visitor Chat access

The avatar interviewer path SHALL support the official SecondMe Visitor Chat model for accessing a target avatar through developer-app authentication and avatar API key-based session initialization.

#### Scenario: Anonymous visitor starts chatting with a configured avatar interviewer
- **WHEN** the product creates an avatar interviewer session for an end user who has not logged into SecondMe
- **THEN** the backend SHALL obtain or reuse a valid app token through the developer application's client-credentials flow
- **AND** it SHALL initialize Visitor Chat using the configured avatar API key and a visitor identifier

#### Scenario: Avatar interviewer sends a follow-up message
- **WHEN** the backend submits a follow-up prompt to a Visitor Chat-backed avatar session
- **THEN** it SHALL send the message through the Visitor Chat send endpoint for the same target avatar
- **AND** it SHALL consume the avatar reply from the returned WebSocket session

### Requirement: Interview providers SHALL own independent prompt strategies

The system SHALL allow system interviewers and avatar interviewers to use different prompt strategies for bootstrap questions, follow-up questions, and feedback generation.

#### Scenario: System interviewer generates a question
- **WHEN** the selected interviewer is backed by the system provider
- **THEN** the backend SHALL use a system-interviewer prompt strategy controlled by the application

#### Scenario: Avatar interviewer generates a question
- **WHEN** the selected interviewer is backed by the avatar provider
- **THEN** the backend SHALL preserve the avatar-first questioning strategy
- **AND** it SHALL continue passing only local hard constraints such as role, mode, and round count
