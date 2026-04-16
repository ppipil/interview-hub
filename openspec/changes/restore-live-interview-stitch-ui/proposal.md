## Why

The current live interview page does not resemble the approved stitch reference. It uses product-style cards and workflow panels instead of the focused interview surface shown in the original design, so the perceived experience is off even when the underlying flow works.

## What Changes

- Rebuild the live interview screen to match the stitch layout more closely, including the minimal top bar, question-first composition, large response area, and floating command center
- Remove transcript and extra workflow panels from the primary interview layout
- Separate guided hints from the main question text so the question headline stays clean and the hint appears in its own surface

## Capabilities

### New Capabilities

- `stitch-live-interview-layout`: Defines the stitch-aligned live interview presentation and interaction layout

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/InterviewPage.tsx`
- `apps/web/src/components/features/interview/InterviewStageHeader.tsx`
- `apps/web/src/components/features/interview/QuestionPanel.tsx`
- `apps/web/src/components/features/interview/AnswerComposer.tsx`
- `apps/web/src/components/features/interview/InterviewCommandBar.tsx`
- `apps/web/src/services/api.ts`
