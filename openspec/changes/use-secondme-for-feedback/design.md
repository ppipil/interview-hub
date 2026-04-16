## Context

The current MVP already maintains an in-memory transcript and an active SecondMe realtime channel for each running interview session. That gives us enough runtime context to ask the same avatar to produce a structured interview report once the user finishes answering. The main challenge is not network transport anymore, but turning a conversational avatar reply into a stable frontend payload.

## Goals / Non-Goals

**Goals:**
- Keep the existing frontend feedback fetch endpoint
- Generate feedback content through SecondMe instead of local heuristics
- Return structured fields for summary, dimensions, strengths, improvements, suggested answer, and per-round reviews
- Keep the implementation modular and isolated behind dedicated services

**Non-Goals:**
- Add a database
- Add a second model provider just for feedback
- Redesign the frontend feedback page information hierarchy

## Decisions

- Reuse the active SecondMe session context for feedback generation so the avatar can see the interview transcript and stay in the same persona.
- Move feedback generation to the `GET /feedback` path so the final answer submit stays lightweight and the frontend can continue to show a loading state while the report is generated.
- Ask SecondMe for strict JSON output and parse it in a dedicated feedback service.
- Extend the API contract with `roundReviews` so the frontend no longer fabricates round notes locally.
- Keep a narrow fallback path inside the parser to normalize partially compliant JSON, but do not silently replace the result with the old heuristic report.

## Risks / Trade-offs

- [Structured output drift] Conversational avatars may wrap JSON in prose or markdown. -> Mitigation: use a strict prompt, extract JSON blocks defensively, and add one repair attempt before failing.
- [Longer feedback fetch latency] Feedback now depends on a live SecondMe round-trip. -> Mitigation: keep generation on the existing feedback-loading state and cache the parsed result in memory after the first successful generation.
- [Session resource lifetime] Feedback generation depends on an active runtime channel. -> Mitigation: keep runtime state alive until feedback is generated and cached.
