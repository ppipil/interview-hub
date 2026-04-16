## ADDED Requirements

### Requirement: Repository SHALL separate runnable applications by workspace

The repository SHALL keep runnable applications in `apps/*` instead of placing the frontend runtime directly in the root directory. The frontend application MUST live in `apps/web`, and the repository MUST reserve `apps/api` for the future backend service.

#### Scenario: Frontend app files are isolated from repo root

- **WHEN** developers inspect the repository layout
- **THEN** the frontend runtime files SHALL be located under `apps/web` rather than the root directory

#### Scenario: Backend has a clear landing zone

- **WHEN** backend implementation starts
- **THEN** developers SHALL have `apps/api` available as the service location without reorganizing the frontend app again

### Requirement: Repository root SHALL act as coordination layer

The repository root SHALL own shared docs, OpenSpec artifacts, workspace scripts, and cross-app coordination. It MUST NOT be the runtime home for only one app.

#### Scenario: Root scripts target the web workspace

- **WHEN** developers run repository-level frontend commands
- **THEN** root scripts SHALL delegate execution to `apps/web`
