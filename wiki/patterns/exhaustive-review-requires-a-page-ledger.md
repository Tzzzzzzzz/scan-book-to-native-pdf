# P-005 Exhaustive Review Requires a Page Ledger

- Type: failure prevention
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-005`

## Pattern

Representative samples and contact sheets miss sparse OCR, code, figure-label, and overlap errors.

## Root Cause

Book-scale error distribution is uneven, and aggregate metrics cannot prove that each page was inspected.

## Action

Render every page at stable readable resolution. Track page state, machine warnings, visual decision, correction version, and recheck status. Close the review only when each page and every exception has an explicit result.
