## Why

The current home screen still contains a full hero composition and interviewer showcase, which makes the entry feel heavier than the intended MVP. The user wants the homepage reduced to the minimum possible entry: one line of copy and one clear button.

## What Changes

- Simplify the home screen to a single sentence of entry copy and one primary action button
- Remove homepage-only preloading and showcase logic that is no longer visible
- Keep the existing stage transition into setup unchanged

## Capabilities

### New Capabilities

- `minimal-home-entry`: Defines the minimal homepage entry surface for the MVP

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/HomePage.tsx`
- `apps/web/src/components/features/home/HeroEntry.tsx`
- Homepage visual density and entry flow
