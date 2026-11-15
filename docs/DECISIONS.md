# Decisions

- Use the US customary conversion factors specified in the brief, represented
  as decimal constants to avoid binary floating-point drift.
- Normalize a trailing English `s` for simple singularisation; avoid broader
  stemming so ingredient terms are not unexpectedly rewritten.
- Use one SQS message per Lambda invocation batch item; the event source batch
  size is one so partial failures remain explicit.
- Use `uv` dependency groups for development tools and optional provider extras.
- Keep Postgres repository methods, external-provider adapters, and sweeper SQL
  unimplemented as explicitly deferred in the brief. Their interfaces and
  non-network test fakes are present.
- Use `status = PUBLISHED` as the catalog visibility filter and a ten-minute
  process-local cache boundary. Account ingredients and aliases are fetched
  for each scan.
- `SsmPrefix` defaults to `/forkplan/pantry-scanner/beta`; deployment overrides
  it per stage in SAM configuration.
