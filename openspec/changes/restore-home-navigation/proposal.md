## Why

After simplifying the interview and feedback screens, the app lost a reliable path back to the home screen from deeper stages. Users can now enter the flow but may get stuck without a visible return path.

## What Changes

- Restore a visible home navigation action on the custom interview and feedback headers
- Make the setup screen's home action fully reset the flow instead of only switching stage
- Keep the simplified page layouts intact while restoring basic navigation safety

## Capabilities

### New Capabilities

- `global-home-return`: Defines a reliable return-to-home action across the MVP flow

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/SetupPage.tsx`
- `apps/web/src/pages/InterviewPage.tsx`
- `apps/web/src/pages/FeedbackPage.tsx`
- `apps/web/src/components/features/interview/InterviewStageHeader.tsx`
