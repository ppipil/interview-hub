## 1. Formal Question Bank Persistence

- [x] 1.1 Add persistence models and repository interfaces for formal question-bank records with `interviewer` and `global` scopes
- [x] 1.2 Add question-usage persistence so each session records the formal question ID, round number, and source scope used at runtime
- [x] 1.3 Seed a v1 stage taxonomy plus a small global fallback bank and one interviewer-owned sample bank for local verification

## 2. Database-Driven Interview Runtime

- [x] 2.1 Implement deterministic round-to-stage mapping for the supported interview flow so each round resolves a stage key before selection
- [x] 2.2 Build question-selection logic that prefers unused interviewer-owned questions and falls back to unused global questions for the same role and stage
- [x] 2.3 Replace provider-based bootstrap and follow-up question generation with database-backed selection while preserving current session/message APIs
- [x] 2.4 Attach formal question source metadata to delivered questions and save usage records to prevent repeats within the same session

## 3. Interviewer Question Bank Ingestion

- [x] 3.1 Extend backend interviewer create/update contracts to accept structured interviewer-owned question-bank entries with validation for role, stage, and question text
- [x] 3.2 Update questionnaire/admin flows to submit interviewer metadata together with structured question-bank content for that interviewer
- [x] 3.3 Add separate management wiring for global fallback questions so interviewer edits never overwrite the shared fallback bank

## 4. Verification and Rollout

- [x] 4.1 Add backend tests for formal question persistence, selection order, fallback behavior, and no-repeat guarantees within one session
- [x] 4.2 Validate end-to-end flows where a complete interviewer bank serves all rounds and where an incomplete interviewer bank is supplemented by the global fallback bank
- [x] 4.3 Update PRD/README or operator notes to document the new “database-only question source” runtime and the v1 fallback rule
