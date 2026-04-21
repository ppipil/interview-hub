## ADDED Requirements

### Requirement: Frontend production builds SHALL not default to localhost API origins

The frontend SHALL only use the localhost API base URL as a development fallback and SHALL not hardcode it into production builds.

#### Scenario: Production build is deployed without `VITE_API_BASE_URL`

- **WHEN** the frontend runs in a deployed environment without an explicit API base URL
- **THEN** it SHALL avoid using `127.0.0.1` as the default production API origin
- **AND** it SHALL surface an error that the deployed API address is not configured

### Requirement: Backend default CORS policy SHALL support Netlify-hosted frontend testing

The backend SHALL allow localhost development origins and `*.netlify.app` origins through its default CORS regex so a locally running API can be tested from a Netlify-hosted frontend.

#### Scenario: Netlify-hosted frontend calls a local backend

- **WHEN** the frontend origin matches a `netlify.app` deploy URL
- **AND** the backend is running locally with default CORS settings
- **THEN** the backend SHALL include an `Access-Control-Allow-Origin` header for that request
