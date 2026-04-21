## Why

The current interview prompts tell SecondMe exactly how to start and continue the interview. That makes the integration predictable, but it underuses the avatar's own skill document and interview workflow that are already configured on the SecondMe side. We want the avatar to decide what to ask and how to pace the interview based on its configured material, while the backend only supplies session-level constraints such as role, mode, and round count.

## What Changes

- Relax the interview bootstrap prompt so the avatar prioritizes its own SecondMe skill document and interview flow
- Relax follow-up prompts so the avatar decides the most appropriate next question from its configured strategy
- Keep local app constraints limited to role, mode, current round, and total rounds

## Capabilities

### Modified Capabilities

- `secondme-interview-backend`: Interview question prompts defer question strategy and flow design to the configured SecondMe avatar skill

## Impact

- `apps/api/app/services/interview.py`
