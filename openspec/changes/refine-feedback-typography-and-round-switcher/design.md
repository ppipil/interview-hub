## Context

The feedback page now has the right content shape, but the visual scale is still a little heavy for the intended MVP report. The round review also becomes vertically long because every round is expanded at once. A paged review surface better matches the user's preference and keeps focus on one round at a time.

## Goals / Non-Goals

**Goals:**
- Make the feedback page typography slightly smaller and calmer
- Let users switch through rounds horizontally instead of reading a long stacked list
- Preserve the existing report data and three-section composition

**Non-Goals:**
- Change backend feedback payloads
- Reintroduce removed feedback modules
- Add gesture-based swipe support in this iteration

## Decisions

- Reduce the page title and section title sizes by roughly one tier while keeping the same visual hierarchy.
- Implement round review navigation with previous/next arrow buttons and a compact round indicator.
- Keep only one round review card visible at a time to reduce page length and cognitive load.

## Risks / Trade-offs

- [One round visible at a time] Users cannot see all rounds simultaneously. -> Mitigation: provide clear previous/next controls and the current round indicator.
- [Less dramatic report heading] Smaller typography reduces visual punch slightly. -> Mitigation: keep spacing, weight, and accent colors consistent with the stitch-inspired report style.
