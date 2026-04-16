## Context

The app now uses a mix of `AppShell` pages and custom full-screen pages. The `AppShell` setup page still had a home button, but the interview and feedback pages switched to bespoke headers and no longer exposed any obvious return path. This creates a broken-feeling navigation loop.

## Goals / Non-Goals

**Goals:**
- Ensure the user can always get back to the home screen from active flow pages
- Keep the fix visually light so it does not add clutter back into the simplified layouts
- Reset state appropriately when the user intentionally returns home

**Non-Goals:**
- Introduce a full navigation system or route framework
- Change the MVP stage flow itself
- Add browser-history semantics

## Decisions

- Add a small ghost-style "回到首页" action into the custom interview and feedback headers.
- Use `resetAll()` instead of only `setStage("home")` when returning home so the app state matches user expectation of going back to the entry point.
- Update the setup page's existing home button to use the same `resetAll()` behavior for consistency.

## Risks / Trade-offs

- [State reset surprise] Returning home will clear the current session/setup selections. -> Mitigation: this matches the plain-language expectation of "回到首页" more closely than preserving in-progress state.
- [Slightly busier headers] Adding a home action increases header density a bit. -> Mitigation: keep the button small and secondary.
