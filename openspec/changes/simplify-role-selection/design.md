## Context

The current role selector reuses a generic card component that was originally shaped for richer website-style content. That creates extra icons, badges, and descriptions that do not match the mobile stitch asset, where role selection is a simple stacked list with strong selected feedback.

## Goals / Non-Goals

**Goals:**
- Make the role step read like a compact mobile interaction
- Keep only the essential role name in each selectable option
- Preserve visual clarity for the selected state without reintroducing content clutter

**Non-Goals:**
- Redesign the mode or interviewer sections in this change
- Change the underlying interview setup data model beyond removing unused role display fields
- Introduce new routing or state flow

## Decisions

- Replace `ChoiceCard` usage in `RoleSelector` with local button markup so the role step can have a lighter visual structure than other setup modules.
- Keep the section title copy, but shorten the supporting sentence to a single concise line that fits the mobile-first tone.
- Simplify `roleOptions` to `value + label` because badge and long description content are no longer part of the experience.
- Use a vertical stack instead of a responsive grid so the role picker keeps the stitch-like rhythm across breakpoints, including web rendering.

## Risks / Trade-offs

- [Visual inconsistency] The role selector will no longer match the richer mode cards by design. -> Mitigation: keep spacing, radius, and color tokens aligned with the shared design system.
- [Future content expansion] If role-specific helper copy returns later, the current config shape is leaner. -> Mitigation: reintroduce only if the product requirement explicitly needs richer role education.
