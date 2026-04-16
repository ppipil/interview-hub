## Context

The project has already accumulated product docs, OpenSpec changes, design assets, and a working frontend shell. Keeping the frontend app at the repository root would make future backend integration noisy because runtime config, source files, install scripts, and build output would compete with shared repository artifacts.

## Goals / Non-Goals

**Goals:**

- Create a backend-ready repository layout without changing user-facing functionality
- Keep shared docs and OpenSpec at the root
- Move the web app into a dedicated workspace
- Reserve a clean path for backend implementation

**Non-Goals:**

- Implementing the backend itself
- Introducing shared packages before they are needed
- Changing frontend behavior or design in this restructuring step

## Decisions

### Use `apps/web` and `apps/api` as the primary app layout

This gives the repository a conventional fullstack structure and avoids locking the project into a frontend-only root layout. The alternative was a `frontend/` folder with no backend placeholder, but that would still require another restructure once the API work starts.

### Keep docs and OpenSpec at the root

`docs/` and `openspec/` are cross-app coordination assets, so they should stay visible from the repository root rather than moving under one application.

### Use root npm workspace scripts as the entrypoint

Developers can keep running commands from the root while actual runtime packages live in `apps/*`. This preserves convenience without sacrificing structure.

## Risks / Trade-offs

- [Workspace setup adds a small amount of tooling overhead] → Keep only one active app workspace for now and use simple root scripts
- [Existing local installs may need one refresh] → Re-run `npm install` once after moving the frontend app
- [Historical docs may reference root-level frontend files] → Update README and treat this change as the new canonical layout
