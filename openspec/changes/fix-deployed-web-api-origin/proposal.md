## Why

The deployed frontend currently falls back to `http://127.0.0.1:8001` when `VITE_API_BASE_URL` is not configured. That works for local development, but it breaks deployed environments and leads to misleading CORS errors when the frontend is hosted on a different origin.

## What Changes

- Stop using the local API base URL as the production fallback
- Improve frontend error messaging when the deployed site has no API base URL configured
- Expand backend CORS defaults so local backend testing from `*.netlify.app` works without manual regex changes

## Capabilities

### Modified Capabilities

- `web-live-backend-integration`: Production frontend builds require an explicit API base URL or same-origin backend routing
- `secondme-interview-backend`: Default CORS rules support localhost development and Netlify-hosted frontend testing

## Impact

- `apps/web/src/services/api.ts`
- `apps/web/.env.example`
- `apps/api/app/core/config.py`
- `apps/api/.env.example`
