## Context

The simplified setup screen and minimal homepage are both close to the intended MVP shape, but they still have small visual issues. The interviewer card selected state mixes base and active background classes, which can leave white text on a light background. The homepage CTA uses the shared button component correctly but becomes too visually narrow because its label is very short.

## Goals / Non-Goals

**Goals:**
- Make interviewer selection states reliably readable
- Make the homepage CTA feel like a proper primary action
- Keep the fixes small and limited to the affected UI surfaces

**Non-Goals:**
- Redesign the setup layout again
- Change the shared button component for the entire app
- Introduce new homepage content

## Decisions

- Move `AvatarCard` background and text colors fully into the selected/unselected branches so active styles cannot conflict with base classes.
- Keep the home button on the shared `Button` primitive, but give the hero CTA a larger minimum width and align its label with the rest of the app's action language.

## Risks / Trade-offs

- [CTA width tuning] A wider home button may feel slightly oversized on very small screens. -> Mitigation: use a moderate minimum width instead of forcing a full-width layout.
- [Local fix scope] This change only addresses the confirmed interviewer visibility regression. -> Mitigation: preserve the same conditional pattern already working in the role and mode selectors.
