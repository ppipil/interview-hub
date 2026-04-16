## Why

The simplified feedback report is closer to the desired structure, but its typography is still slightly oversized and the round-by-round review becomes long when stacked vertically. A smaller type scale and a left-right round switcher will make the page feel lighter and easier to scan.

## What Changes

- Reduce the feedback page typography hierarchy across the report title and section headings
- Replace the stacked round review list with a single-card left-right switcher
- Keep the existing three-section report structure unchanged

## Capabilities

### New Capabilities

- `feedback-round-switcher`: Defines the smaller feedback typography and left-right round review browsing pattern

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/FeedbackPage.tsx`
- `apps/web/src/components/features/feedback/FeedbackSummary.tsx`
- `apps/web/src/components/features/feedback/ImprovementChecklist.tsx`
- `apps/web/src/components/features/feedback/RoundReviewList.tsx`
