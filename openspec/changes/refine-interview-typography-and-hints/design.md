## Context

The stitch-aligned interview page already establishes the right layout direction, but it still feels oversized on web because the question headline, textarea copy, and supporting labels are too aggressive. The hint card also remains English, which breaks language consistency, and the bottom command bar introduces controls that are not necessary for this stage of the MVP.

## Goals / Non-Goals

**Goals:**
- Make the live interview screen easier to read by reducing font sizes
- Localize the guided hint content into concise Chinese copy
- Show help in guided mode and keep real mode cleaner
- Remove non-essential bottom command controls

**Non-Goals:**
- Change session flow or submission behavior
- Reintroduce transcript history
- Add real audio, pause, or session-management features

## Decisions

- Reduce the question headline and textarea typography while preserving the stitch-like hierarchy.
- Keep hints only for `guided` mode; `real` mode remains hint-free to feel more direct.
- Translate the visible hint title, hint body, response label, placeholder, and action buttons into Chinese for consistency.
- Remove the floating command bar from the page instead of replacing it with another secondary control surface.

## Risks / Trade-offs

- [Less dramatic visual impact] Smaller type reduces the previous oversized editorial look. -> Mitigation: keep strong weight and spacing so the question still reads as the page focus.
- [Fewer controls on screen] Removing the bottom bar means there is no quick “end session” affordance. -> Mitigation: this is acceptable for the current MVP because the main answer flow is the primary task.
