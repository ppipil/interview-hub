## Context

The current backend only supports a single fixed SecondMe avatar interviewer and still uses a legacy integration flow built around `SECONDME_API_KEY`, share code lookup, in-memory runtime state, and a process-held realtime channel. The setup page also hides round selection even though the state model already carries `totalRounds`, and there is no database layer for storing interview questions, sessions, or messages.

The next phase needs three coordinated changes: route interview sessions by interviewer provider, expose a user-facing round selector, and introduce a minimal persistent question-bank foundation. This is a cross-cutting change because it touches backend orchestration, frontend setup UX, integration credentials, and future deployment assumptions.

## Goals / Non-Goals

**Goals:**
- Support both Doubao-backed system interviewers and SecondMe Visitor Chat-backed avatar interviewers behind one interview session API.
- Make provider choice an interviewer-catalog concern instead of hard-coding a single upstream client into the interview service.
- Explicitly support SecondMe Visitor Chat developer-app authentication for anonymous end users via app token, visitor identifier, and target avatar API key.
- Allow setup to select 1-10 rounds with one shared validation contract across web and API.
- Define and implement an MVP persistence model for generic question bank records, interview sessions, and conversation messages.

**Non-Goals:**
- Resume-tailored question generation or storage.
- Full historical replay and interrupted-session recovery.
- Replacing all dynamic generation with question-bank lookup in this change.
- Frontend login or user account work.

## Decisions

### 1. Introduce provider routing at the interviewer level

The interviewer catalog will become the source of truth for both interviewer type and provider metadata. Session creation will resolve an interviewer first, then dispatch to a provider-specific runtime path.

Why:
- It keeps the public API centered on `interviewerId`.
- It lets system and avatar interviewers share a product surface while using different upstream implementations.

Alternative considered:
- Routing only by `interviewer.type`.
- Rejected because multiple providers may exist within the same type later, and prompt/runtime differences belong to catalog metadata.

### 2. Use provider-specific orchestration interfaces

The backend will split interview execution into provider-facing adapters such as `SystemInterviewProvider` and `AvatarInterviewProvider`, each responsible for bootstrap question generation, follow-up generation, and feedback generation.

Why:
- Current `InterviewService` is tightly coupled to one SecondMe client and one realtime runtime model.
- Doubao and SecondMe Visitor Chat have materially different session and streaming semantics.

Alternative considered:
- Keeping one large service with branching `if provider == ...`.
- Rejected because it would make prompt logic, runtime state, and failure handling increasingly hard to reason about.

### 3. Migrate avatar interviewers to Visitor Chat semantics

Avatar interviewers will use the Visitor Chat model documented by SecondMe: developer-app authentication, `client_credentials` app token for anonymous visitors, `visitor-chat/init`, WebSocket reply streaming, and `visitor-chat/send`.

Why:
- It matches the current product need where interview users do not need to log into SecondMe directly.
- It makes “access target avatar by avatar API key” an explicit supported path.

Alternative considered:
- Staying on the current legacy endpoint chain.
- Rejected because the official product direction and developer model now center on Visitor Chat, and the team needs the app-token understanding captured in scope.

### 4. Keep prompt strategy separate by provider and interviewer type

Prompt builders will be split so system interviewers can use a Doubao-oriented strategy while avatar interviewers continue deferring question strategy to the avatar’s own skill document plus local hard constraints.

Why:
- The PRD requires both interviewer classes.
- System interviewers need locally controlled behavior, while avatar interviewers intentionally rely more on avatar-owned skills.

Alternative considered:
- One generic prompt template with small substitutions.
- Rejected because it weakens the behavioral distinction that the product is trying to validate.

### 5. Expand rounds to 1-10 through a shared validation contract

The frontend setup selector and backend session validation will both clamp and validate against the same 1-10 rule, while product defaults remain conservative at 3 rounds.

Why:
- It supports testing and future upgrades without changing the user-facing flow contract later.
- It removes the current mismatch where total rounds exist in state but are not user-configurable.

Alternative considered:
- Keep backend at 1-3 and add a frontend-only selector.
- Rejected because it creates false affordances and hard-to-debug validation mismatches.

### 6. Start persistence with a narrow MVP schema

The first database-backed persistence slice will cover:
- interviewer definitions or provider metadata needed by catalog loading
- interview sessions
- conversation messages
- generic question bank entries

Why:
- This is enough to support reusable generic questions and future analytics without overcommitting to resume-aware question generation.

Alternative considered:
- Storing only question-bank rows first.
- Rejected because session and message persistence are natural companions once database infrastructure is introduced.

## Risks / Trade-offs

- [Visitor Chat credential model is new to the team] -> Capture app-token and anonymous visitor flow as explicit tasks and configuration requirements before implementation starts.
- [Two providers can drift in behavior and response shape] -> Normalize outputs at the provider adapter boundary and keep frontend contracts unchanged.
- [1-10 rounds may increase generation cost and latency] -> Keep default rounds at 3 and treat larger counts as an advanced/testing path.
- [Question bank may be too limited to replace live generation] -> Keep it as augmentation and fallback rather than the only question source.
- [Database introduction broadens change scope] -> Limit this change to MVP tables and repository interfaces, not full analytics or resume ingestion.

## Migration Plan

1. Add provider-aware interviewer catalog metadata and feature-flagged configuration for system and avatar interviewers.
2. Introduce provider adapter interfaces without removing the current public interview API contract.
3. Implement Doubao system interviewer path.
4. Implement SecondMe Visitor Chat path, including app token handling for anonymous visitors.
5. Add database schema and repository layer for sessions, messages, and generic question bank.
6. Enable setup round selection UI and update backend validation to 1-10.
7. Roll out with one system interviewer and one avatar interviewer first, then expand catalog entries.

Rollback strategy:
- Keep the old single-avatar path available behind configuration until Visitor Chat is verified.
- If database-backed question bank causes issues, continue generating dynamically while retaining session/message persistence work.

## Open Questions

- Will feedback for system interviewers also be generated by Doubao, or should there be a shared feedback provider later?
- Where should interviewer catalog metadata live long-term: config file, database table, or admin-managed content source?
- Should generic question bank selection happen before provider generation, after provider generation, or as a fallback-only strategy?
