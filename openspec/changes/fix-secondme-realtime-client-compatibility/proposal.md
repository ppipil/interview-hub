## Why

The current backend can authenticate against the pre-release SecondMe Avatar Open API, but it fails when establishing the realtime websocket connection. Investigation shows the pre-release websocket gateway accepts a raw HTTP Upgrade request and also works with the `websocket-client` library, while the current `websockets`-based implementation is consistently reset during connection.

## What Changes

- Replace the current realtime websocket client implementation with a compatible adapter built on `websocket-client`
- Keep the backend's async service surface unchanged while moving websocket IO into a dedicated background thread
- Add configuration for the websocket Origin header used during connection

## Capabilities

### Modified Capabilities

- `secondme-interview-backend`: Uses a websocket client implementation compatible with the current SecondMe pre-release realtime gateway

## Impact

- `apps/api/pyproject.toml`
- `apps/api/app/core/config.py`
- `apps/api/.env.example`
- `apps/api/.env`
- `apps/api/README.md`
- `apps/api/app/services/realtime.py`
