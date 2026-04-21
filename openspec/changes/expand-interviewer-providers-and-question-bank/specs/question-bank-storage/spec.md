## ADDED Requirements

### Requirement: The system SHALL persist a generic interview question bank

The backend SHALL support storing generic interview questions in a database-backed question bank so reusable questions can be managed independently of live provider generation.

#### Scenario: Team stores a generic question in the question bank
- **WHEN** a generic interview question is created for a supported role or interviewer category
- **THEN** the system SHALL persist the question with enough metadata to filter and reuse it later

#### Scenario: Resume-tailored question is requested
- **WHEN** a question depends on a candidate-specific resume context
- **THEN** the system SHALL treat that question as out of scope for this MVP question bank
- **AND** it SHALL not require resume-tailored storage support in this change

### Requirement: The system SHALL persist interview sessions and messages alongside question-bank work

The first database-backed persistence slice SHALL include interview sessions and conversation messages so generated questions and interview outcomes can be associated with durable records.

#### Scenario: Session is created
- **WHEN** a new interview session starts
- **THEN** the system SHALL persist a session record with interviewer, role, mode, and total-round metadata

#### Scenario: Message is exchanged during an interview
- **WHEN** a user answer or interviewer question is produced during a session
- **THEN** the system SHALL persist the message as part of that interview session's conversation history

### Requirement: Question-bank records SHALL support later reduction of repeated upstream generation

Question-bank records SHALL include enough classification metadata for the product to later decide whether to reuse a stored generic question or call an upstream provider again.

#### Scenario: Question is evaluated for reuse
- **WHEN** the backend looks up generic questions for a role or interviewer path
- **THEN** stored question records SHALL expose metadata that lets the system filter by relevant dimensions such as role, mode, or source type
