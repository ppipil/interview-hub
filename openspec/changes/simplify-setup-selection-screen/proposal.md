## Why

The setup screen still feels too much like a desktop website, with extra helper text, grouped explanations, and a separate summary module. For the intended mobile-first flow, users should only see the three required choices and a clear start action.

## What Changes

- Reduce the setup screen to three selection modules: role, mode, and interviewer
- Remove helper descriptions and secondary small text beneath setup section titles and options
- Replace the dedicated summary/start module with a simpler bottom start action

## Capabilities

### New Capabilities

- `minimal-setup-selection`: Defines the minimal mobile-first setup flow with only three selection modules and a bottom action area

### Modified Capabilities

- None

## Impact

- `apps/web/src/pages/SetupPage.tsx`
- `apps/web/src/components/features/setup/RoleSelector.tsx`
- `apps/web/src/components/features/setup/ModeSelector.tsx`
- `apps/web/src/components/features/setup/InterviewerPicker.tsx`
- `apps/web/src/components/ui/SectionTitle.tsx`
- `apps/web/src/config/interviewOptions.ts`
