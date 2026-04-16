## Why

The current feedback page still contains too many modules for the current MVP. The user only wants three sections now: an overall evaluation, improvement suggestions, and a round-by-round answer review, presented in a simpler report-style layout closer to the stitch reference.

## What Changes

- Simplify the feedback page to three content sections: comprehensive evaluation, improvement suggestions, and per-round answer review
- Remove extra feedback modules such as dimension score cards, suggested answer panels, and retry hero panels from the main page
- Rebuild the feedback page layout to better match the stitch feedback screenshot

## Capabilities

### New Capabilities

- `minimal-feedback-report`: Defines the simplified report-style feedback page for the MVP

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/FeedbackPage.tsx`
- `apps/web/src/components/features/feedback/FeedbackSummary.tsx`
- `apps/web/src/components/features/feedback/ImprovementChecklist.tsx`
- `apps/web/src/components/features/feedback/RoundReviewList.tsx`
- Feedback page composition and visual density
