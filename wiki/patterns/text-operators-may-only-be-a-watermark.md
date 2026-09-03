# P-012 Text Operators May Only Be a Watermark

- Type: classification failure prevention
- Status: active
- Confidence: high
- Evidence: `raw/iteration-001/traces/corpus-inventory.json`

## Pattern

Extractable text or PDF text-show operators do not prove that the book's body is native.

## Root Cause

A scanned page can carry a small repeated watermark, page number, or label while all meaningful body content remains inside a full-page image.

## Action

Measure image coverage, per-page character counts, and recurring short strings. Classify a full-image document with sparse repeated text as a scanned book with a native overlay, and reconstruct its body rather than treating the watermark as successful OCR.
