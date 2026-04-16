## ADDED Requirements

### Requirement: Live interview screen SHALL use moderated typography

The live interview screen SHALL present the question area and answer area with readable typography that does not overwhelm the layout on web-sized screens.

#### Scenario: User reads the current question

- **WHEN** the live interview screen renders
- **THEN** the question headline and answer input text SHALL use moderated sizes suitable for continuous reading

### Requirement: Guided hints SHALL be localized and mode-aware

The system SHALL present hint content in Chinese and SHALL only show hint guidance when the interview is running in guided mode.

#### Scenario: Guided mode is active

- **WHEN** the current session mode is `guided`
- **THEN** the live interview screen SHALL render a Chinese hint card beneath the question

#### Scenario: Real mode is active

- **WHEN** the current session mode is `real`
- **THEN** the live interview screen SHALL not render the hint card

### Requirement: Live interview screen SHALL omit temporary bottom command controls

The live interview screen SHALL not render the temporary bottom control bar containing pause, audio, or end-session actions.

#### Scenario: User is answering a question

- **WHEN** the live interview screen is visible
- **THEN** the bottom command bar SHALL be absent from the layout
