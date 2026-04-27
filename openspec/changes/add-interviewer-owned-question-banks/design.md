## Context

Interview Hub already has interviewer metadata, question-bank persistence wiring, provider routing, and multi-round session state, but the active runtime still delegates question generation to Doubao or SecondMe. That no longer matches product direction. The new requirement is to make the database the only source of interview questions, while still preserving interviewer differentiation through interviewer-scoped banks and allowing product-safe fallback to a shared global bank.

This is a cross-cutting change because it affects persistence schema, interview runtime selection, questionnaire/admin ingestion, and the meaning of provider-backed interviewers. Providers can still exist for other purposes, such as avatar-backed feedback or later agent augmentation, but they must stop acting as the source of interview questions in the main loop.

## Goals / Non-Goals

**Goals:**
- Make interview question delivery database-driven for both bootstrap and subsequent rounds.
- Support interviewer-specific question banks plus a shared global fallback bank.
- Ensure the runtime can fill all requested rounds even when an interviewer's own bank is incomplete.
- Preserve fixed interview flow semantics through structured stage metadata rather than free-form model generation.
- Allow interviewer creation flows to save structured question-bank content for that interviewer.
- Track which source supplied each question so behavior is auditable and tunable later.

**Non-Goals:**
- Real-time AI question generation.
- RAG, multimodal selection, or agentic runtime planning in this change.
- Complex percentage-based blending between interviewer and global banks.
- Resume-tailored question generation or personalized question authoring.
- Replacing feedback generation in this change.

## Decisions

### 1. Split formal question bank from historical generated-question storage

The current `question_bank` table behaves more like deduplicated historical question storage. This change will introduce a formal bank model for runtime selection rather than overloading the existing semantics.

Why:
- Runtime needs structured metadata such as scope, stage, type, difficulty, enablement, and ordering.
- Historical generated questions and formal curated questions have different lifecycles and trust levels.

Alternative considered:
- Reuse the existing `question_bank` table and add more columns.
- Rejected because it mixes curated runtime content with incidental stored questions and complicates migration logic.

### 2. Use explicit scope types: interviewer-owned and global

Each formal question row will carry a scope concept:
- `interviewer`: question belongs to one interviewer
- `global`: question is reusable fallback content

Why:
- It matches the product model exactly.
- It supports deterministic selection order: interviewer bank first, global fallback second.

Alternative considered:
- One table per interviewer or separate interviewer/global tables.
- Rejected because one normalized table with a scope field is simpler to query and maintain.

### 3. Drive runtime selection from fixed stage keys

Question rows will include stage metadata such as `intro`, `fundamentals`, `project`, `system_design`, `behavioral`, `closing`. Session runtime maps round number to stage key, then selects a question from the interviewer bank for that stage and role. If none are available, it selects from the global bank for the same stage and role.

Why:
- It preserves the product's fixed interview flow without AI orchestration.
- It keeps question coverage predictable across 1-10 rounds.

Alternative considered:
- Pure sequential ordering only.
- Rejected because stage keys preserve intent and allow future flow tuning without rewriting all question rows.

### 4. Introduce question usage tracking per session

The runtime will persist which formal question IDs were used in a session so later rounds cannot repeat the same question and so product can audit source selection.

Why:
- “No repeat within one interview” is now a hard runtime requirement.
- It provides the future basis for coverage analytics and fallback-ratio tuning.

Alternative considered:
- Infer usage from saved assistant messages only.
- Rejected because message text is not a stable key once display formatting evolves.

### 5. Keep provider routing but narrow provider responsibility

Interviewer providers remain in the system because interviewer type/provider still matters for later integrations, but question generation responsibility moves out of providers. In v1 of this change, providers are bypassed for question selection and only remain relevant for feedback or future extensions.

Why:
- It minimizes disruption to existing interviewer catalog concepts.
- It prevents a large, risky rewrite of unrelated feedback/runtime pieces.

Alternative considered:
- Remove providers entirely from interview sessions.
- Rejected because provider metadata still matters for avatar interviewers and later roadmap work.

### 6. Start ingestion with structured text input, not file parsing

Questionnaire/admin flows will support structured question entry for interviewer banks in this change. Bulk upload files can be added later once the formal model is stable.

Why:
- It aligns with the user's “通过问卷上传” direction without forcing a complex parser into the first version.
- It keeps the first data contract small and testable.

Alternative considered:
- Build CSV/PDF upload in the same change.
- Rejected because it adds parsing complexity before the runtime contract is proven.

## Risks / Trade-offs

- [Interviewer banks may be too sparse to cover all stages] -> Global fallback remains mandatory and runtime always records source origin.
- [Stage mapping may feel rigid for some interviewers] -> Store per-question stage metadata and keep later weighting/ratio tuning open.
- [Provider-backed interviewers may feel less “alive” when questions stop being generated] -> Preserve interviewer-specific banks, persona, and feedback behavior so differentiation remains visible.
- [Questionnaire ingestion may be too lightweight for large banks] -> Start with structured manual entry and add bulk import only after the formal schema is validated.
- [Introducing a second question-bank model can confuse maintainers] -> Explicitly document formal curated bank vs historical generated-question storage and avoid dual runtime usage.

## Migration Plan

1. Add new persistence model and tables for formal question-bank records and question usage tracking.
2. Seed a small set of global fallback questions plus at least one interviewer-owned sample bank.
3. Update interview runtime to resolve questions from the formal bank instead of calling providers for bootstrap/follow-up questions.
4. Persist question usage per session and source metadata on delivered messages.
5. Extend questionnaire/admin flows to create interviewer-owned question-bank records.
6. Verify that incomplete interviewer banks still produce full interviews through global fallback.

Rollback strategy:
- Keep the prior provider-based selection code behind a temporary fallback path until database-driven runtime is validated locally.
- If formal bank rollout fails, sessions can temporarily fall back to the existing provider-based question generation while keeping new schema work in place.

## Open Questions

- Should the formal question bank live beside the current `question_bank` table long-term, or should historical generated-question storage later be removed?
- What exact stage taxonomy should v1 standardize on for all roles?
- Should interviewer-owned banks eventually support per-stage priority or weighting before we introduce ratio tuning?
