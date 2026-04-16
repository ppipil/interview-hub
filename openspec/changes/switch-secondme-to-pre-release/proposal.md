## Why

The current machine cannot resolve the production SecondMe Avatar Open API host `mindos.mindverse.ai`, which blocks local integration testing at the authentication step. The pre-release host `mindos-prek8s.mindverse.ai` is reachable and can authenticate successfully with the configured avatar credentials.

## What Changes

- Switch the backend's default SecondMe base URL to the pre-release environment for local MVP development
- Update local environment files and backend docs to reflect the pre-release default
- Preserve environment override support so production can be restored later without code changes

## Capabilities

### Modified Capabilities

- `secondme-interview-backend`: Prefer the reachable pre-release SecondMe environment for local MVP integration

## Impact

- `apps/api/.env`
- `apps/api/.env.example`
- `apps/api/app/core/config.py`
- `apps/api/README.md`
