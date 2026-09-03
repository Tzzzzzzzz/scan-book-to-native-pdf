# P-009 Cleanup Follows Promotion and Hashing

- Type: success pattern
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-009`, `raw/iteration-000/traces/verification-results.md#V-001`

## Pattern

Renders, baselines, ledgers, and audit outputs remain necessary until the delivered PDF is independently verified.

## Root Cause

Early deletion removes rollback material and evidence needed to diagnose delivery-copy or late-stage errors.

## Action

Promote and reopen the final file, record its size and SHA-256, obtain explicit cleanup authorization, resolve exact absolute targets, preserve required artifacts, then inventory and rehash after deletion.
