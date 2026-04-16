## Why

Phase 3 needs a stable frontend foundation before any page assembly starts. Without shared types, a session-aware store, and a mock API that mirrors the backend contract, the UI layer would drift away from `docs/openapi.yaml` and start hardcoding data in components.

## What Changes

- Add a shared TypeScript domain model layer derived from `docs/openapi.yaml`
- Add a mock interview service layer with asynchronous functions for interviewers, sessions, messages, and feedback
- Add a Zustand store to manage setup selections, active session state, message history, feedback state, and async request status
- Record this foundation work as an OpenSpec change so later phases can extend it instead of bypassing it

## Capabilities

### New Capabilities

- `frontend-interview-foundation`: Defines the typed domain contracts, mock API behavior, and global interview flow state used by the frontend shell

### Modified Capabilities

- None

## Impact

- `docs/openapi.yaml`
- `src/types/index.ts`
- `src/services/api.ts`
- `src/store/useInterviewStore.ts`
- Future page implementations in `src/components` and route-level page assembly
