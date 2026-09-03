# P-016 Explicit Render-Exception Triage

- Type: acceptance discipline
- Status: active
- Confidence: high
- Evidence: `raw/iteration-002/traces/final-qa-observations.md#Final-QA-Observations`, `raw/iteration-002/traces/exception-triage.json`

## Pattern

Full-page source/candidate comparisons can flag scan artifacts, antialiasing shifts, intentional watermarks, or contrast changes inside preserved artwork.

## Root Cause

Pixel-band and bounding-box heuristics measure ink and geometry, not whether a difference carries book meaning.

## Action

Enumerate every warning, inspect its source and candidate crop at readable zoom, classify it, and record a disposition with page and box evidence. Block acceptance only for true missing, altered, or incoherent content; retain accepted exceptions in the final ledger.
