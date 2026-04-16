## ADDED Requirements

### Requirement: Deep flow pages SHALL expose a return-to-home action

The interview and feedback pages SHALL provide a visible action that returns the user to the home screen.

#### Scenario: User wants to leave the interview page

- **WHEN** the user is on the live interview screen
- **THEN** the page SHALL provide a visible action to return to the home screen

#### Scenario: User wants to leave the feedback page

- **WHEN** the user is on the feedback screen
- **THEN** the page SHALL provide a visible action to return to the home screen

### Requirement: Return-to-home SHALL reset the MVP flow state

Returning to the home screen SHALL reset interview session and setup state so the user lands on a clean entry view.

#### Scenario: User activates a home return action

- **WHEN** the user chooses to return home from setup, interview, or feedback
- **THEN** the app SHALL clear active flow state and show the home stage
