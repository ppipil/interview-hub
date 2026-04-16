## Why

The current interview screen exposes the full transcript immediately, which competes with the main task of answering the current question. For a focused mobile-first interview flow, the answer composer should be the primary next action and transcript history should stay secondary.

## What Changes

- Move the answer composer directly below the current question
- Hide the transcript by default and reveal it only when the user asks to inspect it
- Keep transcript history available for recovery and context without making it the dominant surface

## Capabilities

### New Capabilities

- `interview-focus-flow`: Defines the answer-first interview interaction pattern for the live interview screen

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/InterviewPage.tsx`
- `apps/web/src/components/features/interview/TranscriptPanel.tsx`
- Live interview UX and mobile-first interaction flow
