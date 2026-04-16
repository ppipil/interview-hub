## Why

The frontend still uses an in-memory mock API layer even though the real FastAPI backend is now available locally and can complete a full SecondMe-backed interview flow. To move the MVP into a real end-to-end state, the web app should call the live backend instead of local mock data.

## What Changes

- Replace the frontend mock API implementation with a real HTTP client that talks to the backend
- Add frontend environment configuration for the backend base URL
- Enable backend CORS for local web development so the Vite app can call the API directly

## Capabilities

### Modified Capabilities

- `secondme-interview-backend`: Allow configured local web origins to call the API during development
- `web-live-backend-integration`: Use the real backend API from the web app instead of the in-memory mock service

## Impact

- `apps/web/src/services/api.ts`
- `apps/web/src/store/useInterviewStore.ts`
- `apps/web/src/vite-env.d.ts`
- `apps/web/.env.example`
- `apps/api/app/core/config.py`
- `apps/api/app/main.py`
- `apps/api/.env`
- `apps/api/.env.example`
- `apps/api/README.md`
