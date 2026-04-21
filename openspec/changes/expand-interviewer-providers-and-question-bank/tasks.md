## 1. Provider Foundations

- [x] 1.1 Expand interviewer catalog data to describe interviewer type, provider, prompt strategy, and provider-specific credentials/config keys
- [x] 1.2 Introduce provider adapter interfaces for bootstrap question, follow-up question, and feedback generation without changing the public interview API contract
- [x] 1.3 Add configuration scaffolding for one Doubao-backed system interviewer and one SecondMe-backed avatar interviewer

## 2. SecondMe Visitor Chat Migration

- [x] 2.1 Replace the current legacy avatar-auth flow with a Visitor Chat client abstraction that supports `init`, `send`, and WebSocket reply handling
- [x] 2.2 Implement developer-app authentication for Visitor Chat anonymous mode using `client_id`, `client_secret`, app token caching, and `visitorId`
- [x] 2.3 Update avatar session creation to access the target avatar through its avatar API key instead of the current share-code-driven flow
- [x] 2.4 Verify and document the minimal environment variables and runtime assumptions needed for Visitor Chat in local and deployed environments

## 3. System Interviewer Provider

- [x] 3.1 Add a Doubao client/service for system interviewer question generation
- [x] 3.2 Implement a system-interviewer prompt strategy for bootstrap questions, follow-up questions, and feedback generation
- [x] 3.3 Route session creation and message sending through the correct provider based on the selected interviewer

## 4. Round Selection

- [x] 4.1 Update shared types and backend validation to support `totalRounds` values from 1 through 10
- [x] 4.2 Add a setup-page round selector UI with a default of 3 rounds
- [x] 4.3 Ensure frontend state management and API requests preserve the selected round count end to end

## 5. Question Bank MVP

- [x] 5.1 Define the MVP database schema for interviewer metadata, interview sessions, conversation messages, and generic question-bank records
- [x] 5.2 Add repository interfaces and initial persistence wiring for sessions and messages
- [x] 5.3 Implement generic question-bank create/read support with role- or category-level metadata for later reuse
- [x] 5.4 Keep resume-tailored question storage explicitly out of scope while documenting the extension path

## 6. Verification and Rollout

- [x] 6.1 Add tests or integration checks for provider routing, round validation, and question-bank persistence
- [x] 6.2 Validate one end-to-end system interviewer flow and one end-to-end avatar interviewer flow
- [x] 6.3 Update README or deployment notes with provider-specific configuration, especially SecondMe Visitor Chat app authentication requirements
