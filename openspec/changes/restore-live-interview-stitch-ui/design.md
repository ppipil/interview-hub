## Context

The stitch live interview reference is a highly focused single-task screen: a light top bar, large question headline, optional guided hint card, oversized response textarea, and a floating command bar. The current implementation instead reads like a multi-panel dashboard, which changes the feel of the product even though the same state and API flow exist underneath.

## Goals / Non-Goals

**Goals:**
- Match the structure and visual rhythm of the stitch live interview screenshot
- Keep the active question as the dominant visual element
- Preserve the current interview flow, submission behavior, and store wiring while changing the presentation

**Non-Goals:**
- Redesign the setup or feedback pages in this change
- Add real audio or pause-session backend features
- Reintroduce transcript history into the primary interview layout

## Decisions

- Replace `AppShell` usage on the interview page with a dedicated full-screen layout so the page can match the stitch header, spacing, and background more closely.
- Keep the interview page split into focused feature components (`InterviewStageHeader`, `QuestionPanel`, `AnswerComposer`, `InterviewCommandBar`) so the code stays readable while the UI becomes more bespoke.
- Move guided support text into a dedicated hint card and stop appending hint copy directly to the question text in the mock API.
- Treat transcript history as non-primary and omit it from this screen for now to align with the approved stitch composition.

## Risks / Trade-offs

- [Reduced access to transcript history] Users cannot inspect previous turns from the main interview screen. -> Mitigation: preserve transcript data in store and reintroduce access later behind a separate control if needed.
- [Mobile-first density on desktop] A tighter stitch-like layout may feel less “dashboard-like” on wide screens. -> Mitigation: use centered responsive containers so the page still scales cleanly on web.
