## Context

The interview page is already structurally close to the intended MVP, but its text sizing is still closer to a desktop hero layout than a mobile interview screen. The user wants the page to feel denser and calmer without changing the actual content order.

## Decisions

- Reduce the title scale in the header and question panel first, because they dominate the page most.
- Slightly reduce the answer textarea copy, button labels, and hint text to keep the visual rhythm consistent.
- Keep spacing mostly intact so the page still feels breathable after the typography change.

## Risks / Trade-offs

- If the question title becomes too small, long prompts may lose emphasis. -> Mitigation: lower the size modestly while preserving strong weight and line-height.
- If only one component is changed, the page can feel visually inconsistent. -> Mitigation: adjust the full interview reading path together.
