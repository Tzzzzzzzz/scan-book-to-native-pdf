# P-014 OCR Backends Need Smoke Tests and Fallbacks

- Type: tool reliability
- Status: active
- Confidence: high
- Evidence: `raw/iteration-001/traces/paired-training-results.md#OCR-probes`

## Pattern

An OCR engine can fail at initialization or produce high-confidence errors in identifiers and punctuation.

## Root Cause

Runtime kernels, model compatibility, and page composition vary by environment; confidence measures recognition certainty rather than source truth.

## Action

Smoke-test code-heavy and prose pages, compare semantic and punctuation CER against held-in gold, record initialization fixes, and keep a tested fallback. Use the winner only to generate hypotheses; resolve every published item against source pixels.
