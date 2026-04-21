## Context

The backend uses a tiny `.env` reader instead of a full dotenv library. That keeps the runtime light, but it also means escape sequences are not decoded. For ordinary strings this is fine, but regex configuration is sensitive to the number of backslashes. The current example values use shell-style escaped dots, which makes the regex too strict once read by the custom loader.

## Decisions

- Add a dedicated regex env reader that collapses doubled backslashes before the pattern reaches FastAPI.
- Keep the normalization targeted to regex configuration instead of changing all env parsing behavior.
- Update the checked-in local `.env` and `.env.example` to show the plain regex form that our loader expects.

## Risks / Trade-offs

- Collapsing doubled backslashes is opinionated, but it is the safer default for regex config loaded from `.env` files in this project.
- Existing environments that already use single-backslash regexes continue to work unchanged.
