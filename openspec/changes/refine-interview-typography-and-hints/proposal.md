## Why

The current live interview page is visually closer to the stitch layout, but the typography is still too large for comfortable use and some copy remains in English. The temporary bottom command bar also adds unnecessary noise for the current MVP.

## What Changes

- Reduce headline and response-area typography on the live interview screen
- Replace guided hint copy with Chinese text and only show hints in guided mode
- Remove the temporary bottom command bar from the live interview layout

## Capabilities

### New Capabilities

- `localized-interview-focus-ui`: Defines the lighter typography, localized hint copy, and simplified interview controls

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/InterviewPage.tsx`
- `apps/web/src/components/features/interview/QuestionPanel.tsx`
- `apps/web/src/components/features/interview/AnswerComposer.tsx`
- `apps/web/src/components/features/interview/InterviewStageHeader.tsx`
- `apps/web/src/components/features/interview/InterviewCommandBar.tsx`
