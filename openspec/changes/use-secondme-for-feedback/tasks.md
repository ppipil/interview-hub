## 1. Contract

- [x] 1.1 Extend the feedback schema in `docs/openapi.yaml`, backend models, and frontend types to include avatar-generated round reviews

## 2. Backend

- [x] 2.1 Replace the local heuristic feedback generator with a modular SecondMe feedback prompt and parser service
- [x] 2.2 Update interview orchestration to request feedback from SecondMe on the feedback endpoint and cache the parsed result in memory

## 3. Frontend

- [x] 3.1 Update the feedback page to consume backend-provided round reviews instead of deriving review notes locally

## 4. Verification

- [x] 4.1 Validate the OpenSpec change
- [x] 4.2 Run backend syntax verification and frontend build verification
- [x] 4.3 Smoke-test the live feedback flow against the local backend
