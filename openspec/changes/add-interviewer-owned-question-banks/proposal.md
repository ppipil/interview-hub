## Why

The current interview flow still treats the database question bank as supporting storage while the runtime continues to rely on provider-generated questions. Product direction has now changed: interview questions must come from a controlled database source, and each interviewer needs their own reusable bank so the experience reflects that interviewer's style without depending on live AI generation.

## What Changes

- Introduce interviewer-owned question banks so every interviewer can have a dedicated pool of formal interview questions and reference answers.
- Add a global fallback question bank that can supplement interviewer-specific banks when the interviewer's own bank does not contain enough questions for the requested flow.
- Change interview runtime selection so bootstrap questions and follow-up questions are chosen from the database using a fixed stage-based flow instead of upstream AI generation.
- Add question-source tracking so every delivered question records whether it came from the interviewer-owned bank or the global fallback bank.
- Extend interviewer intake flows so questionnaire/admin creation can also ingest structured question-bank records for that interviewer.
- Keep fallback ratio tuning and advanced weighting out of scope for this first change; v1 selection order is interviewer bank first, then global fallback when needed.

## Capabilities

### New Capabilities
- `interviewer-question-banks`: Store and manage interviewer-scoped interview questions alongside a reusable global fallback bank.
- `database-driven-interview-runtime`: Run interviews from a fixed database-backed question selection flow without live AI question generation.
- `interviewer-question-bank-ingestion`: Allow interviewer creation and maintenance flows to attach structured question-bank content to a specific interviewer.

### Modified Capabilities

## Impact

- Backend persistence models and repository layer in `apps/api/app/models/` and `apps/api/app/repositories/`
- Interview orchestration and provider-routing behavior in `apps/api/app/services/`
- Startup seeding and database initialization for formal question-bank records
- Admin/questionnaire flows in `apps/web/src/` that currently create interviewer metadata without structured question-bank ingestion
- API contracts and tests for session creation, question selection, and interviewer content management
