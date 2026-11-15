# Repository conventions

- Runtime: Python 3.12, arm64 AWS Lambda, `src/pantry_scanner` layout, managed
  with uv. Use `make check` before proposing changes and `make build` to validate
  SAM changes.
- Keep the API contract in `docs/CONTRACT.md` and the Pydantic models/enums in
  `src/pantry_scanner/domain` synchronized. Do not change frozen message, key,
  status, result, or error-code names.
- Keep provider calls behind `VisionProvider`; never log image data, raw model
  output, ingredient names, or presigned URLs. Never hardcode provider model
  names.
- Parameterize SQL and scope every account-owned query by `account_id`. The
  external API project owns schema, uploads, and pantry writes.
- Use Decimal for unit conversion, preserve lower-bound flags, condition every
  scan state transition on its expected status, and make S3 cleanup best effort.
- Tests must use fake providers and in-memory repositories. Do not make live
  provider or database calls in tests.
- Record design choices that were not specified in `docs/DECISIONS.md`.
