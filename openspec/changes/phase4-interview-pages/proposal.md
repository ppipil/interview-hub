## Why

The project now has typed contracts, a global store, and a mock service layer, but it still lacks the actual user-facing experience. Phase 4 needs to assemble the MVP into a functional frontend shell so users can move from the landing page into setup, complete a mock interview, and review feedback without relying on placeholder stitch exports.

## What Changes

- Add a Vite + React + Tailwind frontend app shell for the MVP
- Implement the four core user-facing screens: home, setup, interview, and feedback
- Assemble the UI with the planned `ui` and `features` component split
- Extend frontend flow state to support the home entry screen and page-to-page transitions

## Capabilities

### New Capabilities

- `frontend-interview-pages`: Defines the MVP page experience, navigation flow, and page assembly requirements for the frontend shell

### Modified Capabilities

- `frontend-interview-foundation`: Extend the global store flow to support the home entry stage in addition to setup, interview, and feedback

## Impact

- Frontend project config files for Vite, Tailwind, TypeScript, and entrypoints
- `src/App.tsx`, `src/main.tsx`, and shared styling
- `src/components/ui/**/*`
- `src/components/features/**/*`
- `src/pages/**/*`
- `src/store/useInterviewStore.ts`
- `src/types/index.ts`
