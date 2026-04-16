## Context

The live interview page currently renders transcript history side-by-side with the answer composer. That layout makes sense for a desktop dashboard, but it hurts focus in a mobile-first interview flow where the main job is to answer the current prompt quickly.

## Goals / Non-Goals

**Goals:**

- Make the current question and answer box the dominant flow
- Keep transcript history accessible but hidden by default
- Preserve existing session and message state behavior

**Non-Goals:**

- Redesigning the entire interview page
- Removing transcript support

## Decisions

### Use a collapsed transcript section

This keeps the answer flow clean while preserving history for users who need to revisit context. The alternative was removing transcript entirely, which would make later review and debugging harder.

### Keep transcript state local to the interview page

The reveal state is a presentation concern, so it does not belong in the global store.

## Risks / Trade-offs

- [Users may miss previous context] → Keep the reveal control visible and label it clearly
- [Another tap is introduced] → Only apply it to transcript history, not to the answer path itself
