## ADDED Requirements

### Requirement: Feedback page SHALL use moderated typography

The feedback page SHALL present the report title and section titles at a moderated size that supports comfortable reading without overpowering the page.

#### Scenario: User scans the report

- **WHEN** the feedback page is displayed
- **THEN** the report title and section headings SHALL use a smaller hierarchy than the prior oversized presentation

### Requirement: Round review SHALL use left-right switching

The feedback page SHALL present the round-by-round review as a single active round card with controls to move to the previous or next round.

#### Scenario: User moves between round reviews

- **WHEN** the user activates the previous or next round controls
- **THEN** the feedback page SHALL replace the visible round review content with the selected round's question, answer, and note
