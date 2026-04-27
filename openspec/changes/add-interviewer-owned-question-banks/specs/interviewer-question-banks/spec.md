## ADDED Requirements

### Requirement: Formal question banks SHALL support interviewer-owned and global scopes
The system SHALL store curated interview questions in a formal question-bank model that distinguishes between interviewer-owned questions and global fallback questions.

#### Scenario: Store an interviewer-owned question
- **WHEN** an interviewer-specific question is created
- **THEN** the system SHALL persist it with an interviewer scope and the owning `interviewer_id`

#### Scenario: Store a global fallback question
- **WHEN** a reusable fallback question is created
- **THEN** the system SHALL persist it with a global scope and no interviewer ownership requirement

### Requirement: Formal question-bank records SHALL include runtime selection metadata
Each formal question-bank record SHALL include enough structured metadata for deterministic runtime selection.

#### Scenario: Save structured metadata
- **WHEN** a formal question-bank record is created
- **THEN** the system SHALL store at least role, stage key, question text, enablement state, and ordering metadata

#### Scenario: Save optional evaluation content
- **WHEN** a formal question-bank record includes learning content
- **THEN** the system SHALL store optional reference-answer and tag metadata with the question

### Requirement: The system SHALL track formal question usage by session
The system SHALL persist which formal question records were used in each interview session.

#### Scenario: Record question usage
- **WHEN** a question is delivered during an interview
- **THEN** the system SHALL persist the session ID, formal question ID, round number, and source scope for that delivery

#### Scenario: Preserve source origin
- **WHEN** a question comes from the global fallback bank
- **THEN** the usage record SHALL identify that the delivered question source was global fallback rather than interviewer-owned
