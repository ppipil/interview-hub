## Context

The frontend app is now deployed separately from the backend. In development, a localhost fallback is convenient, but in production it causes the browser to request `127.0.0.1` from the user's own machine. When the backend is running locally on the same machine, the request may reach the service but still fail on CORS. When the backend is not local, the request is simply wrong.

## Decisions

- Keep `http://127.0.0.1:8001` as the development-only fallback.
- Remove the localhost fallback from production builds so deployed environments either use `VITE_API_BASE_URL` or same-origin paths.
- Return a clearer frontend error when production builds are missing API configuration.
- Expand default backend CORS regex to include `https://*.netlify.app` so local backend testing with a Netlify-hosted frontend is smoother.

## Risks / Trade-offs

- Allowing `*.netlify.app` in the default regex is broader than a single fixed deploy URL. -> Acceptable for the MVP, and exact origins can still be pinned with `BACKEND_CORS_ORIGINS`.
- Production builds without `VITE_API_BASE_URL` will now fail more honestly instead of silently trying localhost. -> This is intentional and easier to debug.
