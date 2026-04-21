## MODIFIED Requirements

### Requirement: Interview prompt orchestration SHALL defer question strategy to the configured SecondMe avatar

The backend SHALL provide only session-level runtime constraints for interview rounds and SHALL allow the configured SecondMe avatar skill document to decide the interview flow, questioning order, and follow-up strategy.

#### Scenario: Session starts with a configured avatar interview skill

- **WHEN** a new interview session is created
- **THEN** the bootstrap prompt SHALL tell the avatar to prioritize its own SecondMe skill document and interview process
- **AND** it SHALL still constrain the session by role, mode, current round, and total rounds
- **AND** it SHALL request a single question output for the frontend UI

#### Scenario: Avatar generates the next interview question after a user answer

- **WHEN** the backend requests a follow-up question for the next round
- **THEN** the follow-up prompt SHALL tell the avatar to decide the most appropriate next question using its configured questioning strategy
- **AND** it SHALL preserve local hard constraints for mode, round number, and total rounds
- **AND** it SHALL request a single question output for the frontend UI
