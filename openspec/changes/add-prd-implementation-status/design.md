## Context

The team is now using the PRD as a working alignment document, not just as an early product brief. Without visible status markers, readers must infer progress from code or prior conversations. That slows weekly planning and increases the risk of misreading intentionally simplified features as unfinished bugs.

## Decisions

- Keep the PRD as the source of product intent instead of turning it into a changelog.
- Add a lightweight status framework directly in the PRD:
  - `已完成`
  - `部分完成`
  - `已调整范围`
  - `待补齐`
- Add status callouts to the scope section, major pages, and Definition of Done.
- Include a concrete update date so the status snapshot is time-scoped.

## Risks / Trade-offs

- Status inside the PRD can become stale if ignored. -> Acceptable because the document is already being used as a live planning reference.
- The document becomes slightly longer. -> Worth it because it reduces repeated alignment conversations.
