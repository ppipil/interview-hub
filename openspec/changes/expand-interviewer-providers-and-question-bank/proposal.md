## Why

The product now needs to move beyond a single fixed SecondMe avatar interviewer and align more closely with the PRD by supporting both system interviewers and AI avatar interviewers. At the same time, the setup flow still lacks round selection, and the backend has no structured question bank foundation for reducing repeated generation cost.

## What Changes

- Add a multi-interviewer provider architecture that supports:
  - system interviewers backed by Doubao
  - AI avatar interviewers backed by SecondMe Visitor Chat
- Introduce provider-specific prompt strategies so system and avatar interviewers can use different question and feedback orchestration logic.
- Add Visitor Chat developer-app authentication work for avatar interviewers, including app-level token flow, anonymous visitor support, and target avatar access via avatar API key.
- Expand round selection from the current hidden 1-3 range to an explicit 1-10 selection with unified frontend and backend validation.
- Define an MVP database schema for interview sessions, conversation messages, and a reusable general-purpose question bank.
- Support initial ingestion and retrieval for generic interview questions while explicitly leaving resume-tailored question generation out of scope for this change.

## Capabilities

### New Capabilities
- `interviewer-provider-routing`: Route interview sessions by interviewer type and provider, including Doubao-backed system interviewers and SecondMe Visitor Chat-backed avatar interviewers.
- `interview-round-selection`: Allow users to choose the interview round count in setup and enforce a shared 1-10 validation contract across web and API.
- `question-bank-storage`: Persist generic interview questions and related interview records so the product can start reducing repeated upstream generation.

### Modified Capabilities

## Impact

- Backend service orchestration in `apps/api/app/services/`
- Interviewer catalog and session initialization APIs
- SecondMe integration logic, including migration planning from legacy endpoints to Visitor Chat
- New Doubao provider client and provider-routing abstractions
- Setup page and frontend state validation in `apps/web/src/`
- New database and repository layer for sessions, messages, and question bank records
