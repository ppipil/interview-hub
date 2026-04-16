## ADDED Requirements

### Requirement: Frontend repository SHALL include Netlify SPA deployment configuration

The repository SHALL define Netlify configuration that builds the frontend from the monorepo root and publishes the generated `apps/web/dist` output.

#### Scenario: Netlify imports the repository from GitHub

- **WHEN** Netlify reads the repository configuration
- **THEN** it SHALL run the frontend build successfully from the repository root
- **AND** it SHALL publish the built files from the frontend output directory

### Requirement: Netlify deployment SHALL support SPA route refreshes

The deployment configuration SHALL route unmatched frontend paths to `index.html` so client-side routes do not render the default Netlify 404 page.

#### Scenario: User refreshes a nested frontend route

- **WHEN** the browser requests a path handled by the frontend router
- **THEN** Netlify SHALL serve the SPA entry page instead of a static 404
