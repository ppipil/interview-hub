## Context

The home page currently behaves like a product marketing surface with multiple cards and interviewer previews. That creates extra explanation before the user even enters the MVP flow. The desired behavior is a minimal launch pad that gets the user into setup immediately.

## Goals / Non-Goals

**Goals:**
- Reduce the home page to a single concise message and one primary button
- Remove unused homepage fetching and showcase composition
- Preserve the existing transition from home to setup

**Non-Goals:**
- Redesign the setup, interview, or feedback pages
- Change store behavior after the user enters setup
- Add any new homepage interactions beyond the primary CTA

## Decisions

- Keep `AppShell` so the page still sits within the current app frame, but use a single centered entry block inside it.
- Simplify `HeroEntry` into a compact presentational component that renders only one sentence and one button.
- Stop fetching interviewers on the home screen because the simplified layout no longer uses that data.

## Risks / Trade-offs

- [Less context before entry] New users get less explanation on the first screen. -> Mitigation: make the one-line copy explicit and keep the CTA obvious.
- [Unused legacy component file] Some old home-display code may remain temporarily if not referenced. -> Mitigation: remove homepage composition references so the live UI stays minimal even if helper files remain in the repo.
