# forkplan-pantry-scanner

The pantry scanner is a Python 3.12 worker for Forkplan's asynchronous pantry
photo scans. It consumes SQS messages, analyses the referenced temporary S3
images through a configurable vision provider, matches detections against the
account and shared ingredient catalogs, and writes the result to the existing
`pantry_scans` row. It has no HTTP API and does not create schema or write to a
pantry.

## Setup

Install [uv](https://docs.astral.sh/uv/), AWS SAM CLI, and Python 3.12, then run:

```sh
make install
make check
```

The Claude and OpenAI provider SDKs are optional local extras and are both
included in the Lambda build. The provider (`claude` or `openai`) and model are
configuration values; model names are never embedded in source code.

## Architecture

`handlers/worker.py` validates SQS envelopes and invokes `pipeline.py` once per
record. The pipeline conditionally claims a queued scan, downloads and safely
re-encodes each image, calls the `VisionProvider` abstraction, validates and
post-processes detections, matches ingredients, converts units, persists the
result, and best-effort deletes temporary objects. Messages malformed before a
claim are dropped; infrastructure failures before a claim are returned as
partial batch failures. After a successful claim, processing failures are
persisted and swallowed so redelivery is harmless.

Domain types in `src/pantry_scanner/domain` define the frozen API/database
contract. Matching and unit conversion are provider-independent. The
`MemoryRepository` and `FakeProvider` support tests and local development;
Postgres repositories and the Claude/OpenAI adapters intentionally remain
stubs. The scheduled sweeper has an interface and handler, while its database
queries remain for a later phase.

## Local worker

Sample SQS and schedule events are in `events/`. Run the SQS event through the
worker locally with an in-memory repository, an in-memory JPEG, and the fake
provider (no AWS credentials, SSM values, database, or live provider needed):

```sh
uv run python scripts/try_scan.py events/sqs_scan.json
```

The demonstration creates a queued in-memory scan based on the sample message
and prints only its final status and item count. Unit tests likewise use
in-memory repositories and no live provider calls. Production Postgres and
provider adapters remain stubs.

## Deploy

Set the repository variable `AWS_DEPLOY_ROLE_ARN` to an OIDC-trusted deployment
role, configure GitHub environments named `beta` and `prod`, and add the
required SSM SecureString values under `/forkplan/pantry-scanner/<stage>/`.
Trigger **Deploy** from GitHub Actions and choose the stage. Alternatively:

```sh
make build
make deploy STAGE=beta
```

The SAM stack creates the worker, scheduled sweeper, encrypted queue and DLQ,
private temporary-image bucket, alarms, and a stage-specific `ApiAccessPolicy`
for attachment to the mobile API's Lambda role. Deployment requires the appropriate AWS
credentials and SAM configuration.

See [architecture](docs/ARCHITECTURE.md), [contract](docs/CONTRACT.md),
[decisions](docs/DECISIONS.md), and the [runbook](docs/RUNBOOK.md).
