# P-003 Incremental Page Patching Preserves Verified Work

- Type: success pattern
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-006`, `raw/iteration-000/traces/verification-results.md#V-005`

## Pattern

Once most pages are correct, rebuilding the entire book for a local correction creates a larger and less reviewable regression surface.

## Root Cause

Global rendering and evolving OCR/layout data can change fonts, resources, geometry, or content on unrelated pages.

## Action

Freeze a checked baseline. Patch one guarded object or regenerate one page, merge it into that baseline, and compare text, images, content streams, and boxes across all pages before promotion.
