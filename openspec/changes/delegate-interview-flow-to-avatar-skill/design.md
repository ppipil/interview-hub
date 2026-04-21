## Context

The avatar already has a SecondMe-side skill document that encodes interviewer behavior. Our backend should not compete with that document by forcing a rigid question plan. At the same time, the frontend still expects a single question string per round, and the product still relies on local round limits to know when to stop and fetch feedback.

## Decisions

- Treat the SecondMe avatar skill document as the primary source of truth for question flow, pacing, and follow-up strategy.
- Keep the backend prompt focused on runtime constraints:
  - target interview role
  - session mode
  - current round
  - total rounds
- Preserve the UI contract by still requesting a single question with no extra framing or bullet points.
- Include the local interviewer description only as a fallback hint in case the avatar needs extra grounding.

## Risks / Trade-offs

- A freer avatar prompt may produce more variation between sessions. -> This is intentional and aligns better with the configured skill document.
- If the avatar skill document is vague, question quality may depend more on the fallback description. -> Acceptable for the MVP because the real source of behavior is now the avatar-side configuration.
