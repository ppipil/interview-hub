## ADDED Requirements

### Requirement: Frontend SHALL provide the four MVP interview screens

The frontend SHALL provide a home screen, setup screen, live interview screen, and feedback screen. These screens MUST map to the user flow defined in `docs/PRD.md` and MUST render from the React application instead of read-only stitch export assets.

#### Scenario: User enters the challenge from home

- **WHEN** the application loads for the first time
- **THEN** the home screen SHALL be shown with a clear primary action that moves the user into interview setup

#### Scenario: User completes the end-to-end journey

- **WHEN** the user configures a session, answers all rounds, and reaches completion
- **THEN** the frontend SHALL show the feedback screen with a way to start another round

### Requirement: Frontend SHALL separate reusable UI from business-aware feature components

The page implementation SHALL keep reusable presentational primitives under `src/components/ui` and workflow-aware assemblies under `src/components/features`.

#### Scenario: Shared card and button treatments are reused across screens

- **WHEN** different pages need buttons, cards, badges, or messaging surfaces
- **THEN** they SHALL use reusable UI primitives instead of redefining styling in each page component

#### Scenario: Feature components own workflow-specific composition

- **WHEN** a page needs setup selection, transcript rendering, or feedback assembly
- **THEN** the composition SHALL live in `src/components/features` rather than inside the app root
