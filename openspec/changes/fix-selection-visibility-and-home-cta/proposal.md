## Why

Two UI regressions are hurting the current MVP polish: selected interviewer buttons can lose visible text, and the home CTA feels visually too narrow compared with the other primary actions in the app.

## What Changes

- Fix the interviewer selected state so button text remains clearly visible after selection
- Widen and align the home entry CTA with the app's other primary actions
- Keep the existing navigation and selection behavior unchanged

## Capabilities

### New Capabilities

- `selection-visibility-and-home-cta`: Covers selection-state readability fixes and homepage CTA consistency

### Modified Capabilities

- None

## Impact

- `apps/web/src/components/ui/AvatarCard.tsx`
- `apps/web/src/components/features/home/HeroEntry.tsx`
- Setup selection readability and homepage CTA consistency
