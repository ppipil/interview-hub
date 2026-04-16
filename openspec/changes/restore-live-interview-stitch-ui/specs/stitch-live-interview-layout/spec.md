## ADDED Requirements

### Requirement: Live interview screen SHALL prioritize the stitch-style answer flow

The live interview screen SHALL present a focused layout with a minimal top bar, a dominant current-question section, a large response input surface, and a floating command center.

#### Scenario: User lands in an active interview session

- **WHEN** the live interview screen renders with an active session
- **THEN** the screen SHALL show the interviewer header, current question, response area, and floating command controls as the primary visible structure

### Requirement: Guided hints SHALL appear separately from the question headline

The system SHALL keep the main question text free of guided helper copy. When guided mode is active, hint content MUST appear in a separate hint surface beneath the question.

#### Scenario: Guided mode question is shown

- **WHEN** the live interview screen renders in guided mode
- **THEN** the question headline SHALL remain concise and any hint text SHALL render in a dedicated hint card

### Requirement: Transcript history SHALL not appear in the primary live interview layout

The live interview screen SHALL not render transcript history as part of the main visible layout.

#### Scenario: User is answering the current question

- **WHEN** the live interview screen is displayed
- **THEN** transcript history SHALL remain absent from the primary page composition
