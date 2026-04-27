## ADDED Requirements

### Requirement: Interviewer intake flows SHALL support interviewer-owned question-bank ingestion
The system SHALL allow interviewer creation and maintenance flows to attach formal question-bank content to a specific interviewer.

#### Scenario: Create interviewer with question-bank content
- **WHEN** a questionnaire or admin flow submits interviewer metadata together with structured questions
- **THEN** the system SHALL create interviewer-owned formal question-bank records linked to that interviewer

#### Scenario: Update interviewer-owned question bank
- **WHEN** interviewer question-bank content is edited
- **THEN** the system SHALL update the linked interviewer-owned formal question-bank records without affecting global fallback questions

### Requirement: Ingestion SHALL validate minimal structured question fields
Structured question ingestion SHALL reject incomplete question-bank records that cannot participate in runtime selection.

#### Scenario: Missing required selection metadata
- **WHEN** an ingested question omits required runtime fields such as role, stage key, or question text
- **THEN** the system SHALL reject that question-bank record with a validation error

#### Scenario: Accept structured optional content
- **WHEN** an ingested question includes optional reference-answer or tag data
- **THEN** the system SHALL persist that content for later feedback and management use

### Requirement: Global fallback bank SHALL remain separately manageable
The system SHALL support managing the shared fallback bank independently from interviewer-owned banks.

#### Scenario: Add a global fallback question
- **WHEN** an operator creates a global fallback question
- **THEN** the system SHALL store it without attaching it to a specific interviewer

#### Scenario: Interviewer edits do not affect global fallback
- **WHEN** an interviewer-owned bank is updated or deleted
- **THEN** the system SHALL leave global fallback questions unchanged
