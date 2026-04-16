## Why

The project now has a frontend MVP shell but no backend service that can actually talk to a real SecondMe avatar. We need a minimal backend that can run one fixed interviewer through SecondMe, keep session state in memory, and expose the existing frontend contract without introducing a database yet.

## What Changes

- Add a Python + FastAPI backend skeleton under `apps/api`
- Implement one fixed SecondMe-backed interviewer using environment-based configuration
- Keep interview sessions, message history, runtime websocket state, and feedback in memory for the MVP
- Expose the current frontend-facing interview APIs from the backend

## Capabilities

### New Capabilities

- `secondme-interview-backend`: Defines the no-database FastAPI backend that orchestrates SecondMe avatar interviews for the MVP

### Modified Capabilities

- None

## Impact

- `apps/api/**`
- `docs/openapi.yaml`
- Backend runtime architecture, local development flow, and frontend/backend integration path
