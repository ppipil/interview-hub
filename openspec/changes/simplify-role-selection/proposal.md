## Why

The setup screen still presents role selection as a desktop-style card grid with extra copy density. For a mobile-first interview flow, the role step should feel immediate, lightweight, and closer to the stitch reference.

## What Changes

- Simplify the role section copy into a shorter single-line description
- Replace the role card grid with a stacked mobile-style option list
- Reduce each role option to the role name only, while preserving a clear selected state

## Capabilities

### New Capabilities

- `mobile-role-selection`: Defines the simplified mobile-first role selection pattern on the setup screen

### Modified Capabilities

- None

## Impact

- `apps/web/src/components/features/setup/RoleSelector.tsx`
- `apps/web/src/config/interviewOptions.ts`
- Setup screen mobile-first interaction and copy density
