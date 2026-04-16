## Why

The repository currently runs as a frontend app from the root directory, which makes later backend integration awkward. To support a Python or Node.js API without mixing runtime files, the project needs a workspace-style layout with clear separation between frontend, backend, docs, and shared specs.

## What Changes

- Move the React frontend application into `apps/web`
- Convert the root package into a workspace manager instead of the frontend runtime package
- Reserve `apps/api` as the backend service entry point
- Update repository docs so future frontend and backend work follow the same structure

## Capabilities

### New Capabilities

- `workspace-layout`: Defines the repository structure required to support both frontend and backend applications

### Modified Capabilities

- None

## Impact

- Root `package.json` and workspace scripts
- `apps/web/**/*`
- `apps/api/**/*`
- Root `README.md`
- OpenSpec artifacts and future onboarding flow
