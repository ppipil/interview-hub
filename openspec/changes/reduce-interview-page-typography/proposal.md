## Why

The current interview page still feels visually oversized for the mobile-first layout the project is aiming for. The header brand, question title, guided hint, and answer composer all read larger than the stitch reference and make the page feel less like a compact interview flow.

## What Changes

- Reduce the primary typography scale on the interview page
- Keep the information hierarchy intact while making the page feel more mobile-first
- Preserve the current interaction model and page structure

## Capabilities

### Modified Capabilities

- `interview-page-typography`: The interview page uses a moderated type scale across the header, question panel, hint panel, and answer composer

## Impact

- `apps/web/src/components/features/interview/**`
- `apps/web/src/pages/InterviewPage.tsx`
