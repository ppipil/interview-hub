## Why

The backend currently loads `.env` values with a lightweight custom parser. That parser keeps backslashes exactly as written, so a copied regex like `\\.` stays double-escaped instead of becoming `\.`. When `BACKEND_CORS_ORIGIN_REGEX` is provided this way, FastAPI's CORS middleware fails to match valid origins such as `http://localhost:5174`, which makes local and hosted frontend testing fail with misleading CORS errors.

## What Changes

- Normalize dotenv-provided regex values before wiring them into FastAPI CORS settings
- Update local and example backend environment files so the CORS regex is copy-paste safe
- Keep the deployed-frontend CORS coverage aligned with the backend defaults

## Capabilities

### Modified Capabilities

- `secondme-interview-backend`: Dotenv-backed CORS regex values match localhost and Netlify origins correctly

## Impact

- `apps/api/app/core/config.py`
- `apps/api/.env`
- `apps/api/.env.example`
