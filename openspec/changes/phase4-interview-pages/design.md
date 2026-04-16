## Context

The frontend foundation from Phase 3 is already in place: typed contracts, mock APIs, and a Zustand workflow store. The remaining work is to assemble a real React experience on top of it while preserving the design language from `docs/design.md` and only borrowing structure from the read-only `stitch_exports/` assets.

## Goals / Non-Goals

**Goals:**

- Ship a functioning Vite + React frontend shell
- Render all four core screens with a cohesive visual language
- Keep page logic thin by composing `ui` and `features` layers
- Use store and service actions instead of embedding fake data in the UI

**Non-Goals:**

- Adding a real backend transport layer
- Introducing route libraries that are not required for the MVP
- Reproducing every non-MVP stitch asset such as dashboards, history, or utility navigation

## Decisions

### Use stage-driven rendering instead of adding a router dependency

The defined stack did not include a router, and the store already owns workflow state. The app root will render the current screen from store stage, which keeps the MVP dependency surface smaller while still supporting the full flow.

### Preserve the design system, not the stitch implementation

The stitch exports contain useful layout rhythms and visual hierarchy, but they also include non-MVP navigation and demo-only sections. The implemented pages will follow `docs/design.md` tokens and reuse only the parts of stitch that strengthen the challenge flow.

### Keep business copy and option metadata out of UI primitives

Role and mode metadata will live in configuration modules, while actual interviewer data will come from the mock API/store layer. This keeps primitives generic and avoids embedding mock data directly in page-level JSX.

## Risks / Trade-offs

- [Stage-based rendering can make deep linking harder later] -> Treat routing as a future enhancement once real URLs become a product requirement
- [UI surface area grows quickly] -> Keep presentational patterns centralized in `src/components/ui`
- [No installed dependencies means build validation may be blocked] -> Add the full project config now and perform dependency installation/build validation when the environment allows it
