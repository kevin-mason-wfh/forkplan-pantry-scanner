# Runbook

## Required configuration

Set `PROVIDER` to `claude` or `openai`, set `MODEL` to the chosen provider
model, and configure `SCAN_BUCKET` and `SSM_PREFIX`. SecureString parameters
under the prefix are `db-url`, `anthropic-api-key`, and `openai-api-key`.
Provider keys are only required for the selected provider.
The worker and sweeper roles permit KMS decryption only when the SSM parameter
encryption context matches that prefix.
On x86 development hosts, `make build` requires Docker arm64 emulation; the
deployment workflow provisions QEMU before the container build.

## Operations

- Alarm `ScanDLQMessages` indicates messages exhausted their three receives.
- `WorkerErrors` indicates an invocation-level failure; inspect structured
  logs using `scan_id` and `account_id` and check for DB failures before claim.
- `QueueAge` warns when the oldest queued scan exceeds ten minutes.
- The worker cleans scan objects after all claimed outcomes; the bucket
  lifecycle rule removes any remaining `scan-temp/` objects after one day.
- The scheduled sweeper is every five minutes. Its database cleanup statements
  are an intentionally deferred implementation.

## Deploy and recover

Deploy from the `beta` or `prod` GitHub environment using the workflow's OIDC
role, or use `make deploy STAGE=beta|prod` with an authenticated AWS CLI. Review
the CloudFormation changeset before deployment. Failed messages can be
redriven from the DLQ after correcting the underlying issue; duplicate
deliveries are safe because scans are conditionally claimed.
