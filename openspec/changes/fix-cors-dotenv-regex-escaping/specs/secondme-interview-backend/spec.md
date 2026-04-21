## MODIFIED Requirements

### Requirement: Backend CORS configuration SHALL accept dotenv-provided regex values

The backend SHALL interpret `BACKEND_CORS_ORIGIN_REGEX` from `.env` files in a way that preserves the intended regex semantics for localhost development and hosted frontend testing.

#### Scenario: Backend loads a copied regex from `.env`

- **WHEN** `BACKEND_CORS_ORIGIN_REGEX` contains escaped dots such as `\.` or `\\.`
- **AND** the backend starts with that `.env` file
- **THEN** the effective regex used by FastAPI SHALL match valid localhost origins like `http://localhost:5174`
- **AND** it SHALL continue to match configured hosted frontend origins such as `https://example.netlify.app`
