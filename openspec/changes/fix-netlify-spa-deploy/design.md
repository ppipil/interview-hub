## Context

The repository root is a workspace, while the deployable frontend lives in `apps/web`. Netlify can deploy monorepos, but it needs to know which build command to run, where the publish directory lives, and how to handle SPA routes that do not map to physical HTML files.

## Decisions

- Add a root-level `netlify.toml` so a GitHub import can work without extra manual path setup.
- Run the existing workspace root build command so Netlify uses the same build path as local development.
- Publish `apps/web/dist` from the root-level build.
- Add a catch-all redirect to `/index.html` with status `200` so SPA client-side routes do not 404 on refresh.

## Risks / Trade-offs

- The root-level `netlify.toml` is specific to deploying the frontend app, not the backend. -> Acceptable because only `apps/web` is suitable for Netlify deployment in the current architecture.
