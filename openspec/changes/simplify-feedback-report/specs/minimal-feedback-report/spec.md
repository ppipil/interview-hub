## ADDED Requirements

### Requirement: Feedback page SHALL render only three primary report sections

The feedback page SHALL present only the overall evaluation section, the improvement suggestions section, and the per-round answer review section as primary content.

#### Scenario: User opens a completed feedback report

- **WHEN** the feedback page renders with available feedback data
- **THEN** the page SHALL show only the three primary report sections in the main content area

### Requirement: Feedback page SHALL provide round-by-round answer review

The system SHALL present a review entry for each completed round by pairing the question asked in that round with the user's answer and a short review note.

#### Scenario: User inspects round feedback

- **WHEN** the feedback page is displayed after an interview session
- **THEN** the page SHALL list each round with its question, answer, and a short review note

### Requirement: Feedback page SHALL follow a simplified report layout

The feedback page SHALL use a cleaner report-style visual structure aligned with the stitch reference rather than a multi-panel dashboard composition.

#### Scenario: User scans the feedback page

- **WHEN** the main feedback content is visible
- **THEN** the page SHALL read as a vertically stacked report with moderate spacing and simplified card surfaces
