## Why

The frontend is a Vite single-page application inside a monorepo. When deployed to Netlify without explicit SPA redirect and monorepo build settings, direct visits to nested routes can return Netlify's "Page not found" 404 page.

## What Changes

- Add explicit Netlify build configuration for the monorepo
- Add an SPA fallback redirect so all client-side routes resolve to `index.html`

## Capabilities

### Modified Capabilities

- `web-static-deployment`: The frontend repository includes first-party Netlify deployment configuration for the `apps/web` SPA

## Impact

- `netlify.toml`
- Netlify deployment flow for `apps/web`
