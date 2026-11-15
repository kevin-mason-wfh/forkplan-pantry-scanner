# Architecture

The SQS-triggered worker is the sole scan-processing entry point. It validates
the versioned envelope, claims only scans in `QUEUED`, downloads all recorded
temporary objects, prepares JPEGs, invokes the configured vision adapter, and
persists a validated result. A successful claim always terminates in
`COMPLETED`, `FAILED`, or a quiet conditional stop; only infrastructure errors
before the claim cause SQS retry. The event source uses a one-message batch and
partial batch failures.

`pipeline.py` orchestrates ports for scan repositories, image sources, and
vision providers. Domain models define the persistent payload; matching applies
aliases, account ingredients, and published catalog candidates in that order.
The production Postgres repository and provider adapters intentionally raise
`NotImplementedError` in this initial bootstrap. In-memory implementations and
the fake provider allow local logic and tests without external services.

The SAM stack provides a private, short-lived S3 bucket, encrypted SQS queue and
DLQ, two Python 3.12 arm64 Lambdas, least-privilege policies, alarms, and an
API-access managed policy. The sweeper exposes its handler and repository
boundary; its Postgres operations are deferred. The mobile API and database
migrations remain owned by the separate API project.
