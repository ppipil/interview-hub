## Context

The setup page currently combines simplified role selection with richer mode cards, interviewer detail cards, and a separate start panel. That creates four visible blocks and too much explanatory text for a screen that is supposed to behave like a focused mobile configuration step.

## Goals / Non-Goals

**Goals:**
- Keep the setup page visually limited to three modules
- Remove helper copy below module headings and within the selectable options
- Preserve the existing setup state flow and start action while making the screen lighter

**Non-Goals:**
- Change backend contracts or interview setup business rules
- Redesign non-setup pages in this change
- Remove loading and error handling for interviewer fetching

## Decisions

- Update `SectionTitle` so setup modules can omit eyebrow text and descriptions while other pages continue using the component.
- Simplify role and mode configuration objects to label-only options because descriptive metadata is no longer rendered.
- Rebuild mode and interviewer pickers as compact selection lists instead of informational cards.
- Remove the separate `StartInterviewPanel` from the setup layout and replace it with a bottom sticky action area, so the page still supports starting and resetting without adding a fourth module.

## Risks / Trade-offs

- [Less guidance for new users] Removing helper copy may reduce onboarding context. -> Mitigation: keep labels explicit and selection states strong so the flow stays self-explanatory.
- [Interviewer differentiation is subtler] Without description text, users see less persona detail upfront. -> Mitigation: preserve avatar imagery and ordering so options still feel distinct.
