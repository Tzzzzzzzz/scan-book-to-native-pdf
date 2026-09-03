# P-002 Source Pixels Are Semantic Authority

- Type: failure prevention
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-004`

## Pattern

OCR engines and language models often produce plausible but wrong punctuation, identifiers, code operators, and table values.

## Root Cause

Recognition confidence and linguistic plausibility are not evidence of what was printed.

## Action

Treat OCR outputs as hypotheses. Compare disagreements with readable source crops, transcribe only visible content, and record page, item, old/new value, geometry, and evidence for each semantic edit.
