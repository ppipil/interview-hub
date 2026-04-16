## Context

The stitch feedback reference already suggests a cleaner report rhythm than the current implementation. Our existing feedback page includes multiple sidecar modules that feel more like a feature showcase than a focused复盘页. The desired page should read like a concise report with only the sections that directly help the user improve.

## Goals / Non-Goals

**Goals:**
- Reduce the feedback page to three core sections
- Keep the layout visually aligned with the stitch feedback screenshot
- Provide a useful round-by-round review without requiring backend API changes

**Non-Goals:**
- Change the backend feedback schema
- Add retry or navigation panels back into the main feedback report
- Introduce deeper analytics or scoring dashboards

## Decisions

- Build the round-by-round review from existing session messages in the frontend store, pairing each round's assistant question with the user's answer.
- Keep the page on a custom report-style layout instead of `AppShell` so the UI can align more closely with the stitch screenshot.
- Reuse the existing `feedback.summary` and `feedback.improvements` data for the first two sections, and derive a lightweight coaching note per round from the user's answer length and content.

## Risks / Trade-offs

- [Heuristic round review] Per-round comments are generated from frontend heuristics instead of dedicated backend analysis. -> Mitigation: keep the comments concise and clearly framed as lightweight复盘观察.
- [Removed quick actions] The page no longer shows retry/home panels in the main body. -> Mitigation: this matches the current product direction of keeping the report itself simple.
