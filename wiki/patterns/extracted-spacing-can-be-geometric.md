# P-008 Extracted Spacing Can Be Geometric

- Type: diagnostic pattern
- Status: active
- Confidence: medium
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-004`

## Pattern

Extracted text may gain or lose spaces even when the encoded strings did not change.

## Root Cause

Replacing a font or changing text advance can move adjacent PDF runs across an extractor's inferred word-boundary threshold.

## Action

Inspect raw strings, run boundaries, transformation matrices, and visible spacing. Restore source physical advance before editing semantic text, and verify both rendered and extracted results.
