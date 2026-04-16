## Context

The frontend already depends on a session-based interview API contract, but the repository does not yet contain a real backend. The user wants the first backend version to integrate with one SecondMe avatar, avoid a database for now, and keep the code modular instead of placing business logic in one oversized entrypoint.

## Goals / Non-Goals

**Goals:**
- Build a modular FastAPI backend in `apps/api`
- Support one fixed interviewer backed by SecondMe credentials from environment variables
- Keep runtime state in memory only for sessions, messages, feedback, and websocket connections
- Preserve the existing frontend API contract

**Non-Goals:**
- Add a database
- Support multiple avatar providers
- Fully validate the live SecondMe network flow in this environment
- Add authentication, history pages, or persistence

## Decisions

- Use FastAPI because it fits the current Python-first recommendation and provides a simple typed API layer.
- Split the backend into config, API schemas, repositories, services, and route modules to keep logic decoupled from the entrypoint.
- Use one in-memory repository to manage local sessions, messages, feedback, and websocket runtime objects.
- Wrap SecondMe REST and websocket behavior behind dedicated service classes so the interview orchestration stays readable and testable.
- Keep feedback generation local and heuristic for the first version, while using SecondMe for interview-question generation.

## Risks / Trade-offs

- [No persistence] Service restarts will clear sessions and feedback. -> Mitigation: acceptable for the MVP and isolated behind repository interfaces for later database replacement.
- [SecondMe runtime uncertainty] The documented API flow is clear, but the exact live response shapes were not fully validated in this environment due network issues. -> Mitigation: isolate parsing in the client layer and keep the backend easy to adjust.
- [Single interviewer scope] The first backend only exposes one configured interviewer. -> Mitigation: the catalog service and settings are shaped so more interviewers can be added later without rewriting the API layer.
