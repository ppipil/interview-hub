## ADDED Requirements

### Requirement: Interview runtime SHALL select questions from the database instead of live AI generation
The system SHALL use the formal question bank as the source for bootstrap and follow-up questions in the interview runtime.

#### Scenario: Create first-round question from database
- **WHEN** a new interview session is created
- **THEN** the system SHALL select the first question from the formal question bank instead of requesting a generated question from an upstream model provider

#### Scenario: Create later-round question from database
- **WHEN** a user submits an answer and more rounds remain
- **THEN** the system SHALL select the next question from the formal question bank instead of requesting a generated follow-up from an upstream model provider

### Requirement: Runtime selection SHALL prefer interviewer-owned questions before global fallback
The system SHALL always attempt to select a question from the current interviewer's owned bank before using the global fallback bank.

#### Scenario: Interviewer-owned question is available
- **WHEN** the current stage has at least one unused interviewer-owned question for the active role
- **THEN** the system SHALL deliver an interviewer-owned question and SHALL NOT use a global fallback question for that round

#### Scenario: Interviewer-owned bank is insufficient
- **WHEN** no unused interviewer-owned question matches the current stage and role
- **THEN** the system SHALL select an unused global fallback question for the same stage and role

### Requirement: Runtime question selection SHALL follow a fixed stage-based flow
The system SHALL map rounds to predefined stage keys and use those stage keys to select questions.

#### Scenario: Requested rounds exceed one stage
- **WHEN** a session spans multiple rounds
- **THEN** the system SHALL assign each round to a deterministic stage key based on the configured flow

#### Scenario: Question selection respects stage
- **WHEN** a round is assigned to a stage key
- **THEN** the system SHALL only consider unused questions matching that stage key and role for that round

### Requirement: Runtime selection SHALL avoid repeating questions within one session
The system SHALL not deliver the same formal question twice in one interview session.

#### Scenario: Same bank contains limited questions
- **WHEN** earlier rounds have already used a formal question
- **THEN** the runtime SHALL exclude that question from later selection in the same session

#### Scenario: Fallback search occurs after owned-bank depletion
- **WHEN** the runtime switches from interviewer-owned to global fallback selection
- **THEN** it SHALL still exclude any global questions already used earlier in the same session
