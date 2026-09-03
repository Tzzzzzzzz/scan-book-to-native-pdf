# P-010 Audit Tools Produce Candidates, Not Proof

- Type: diagnostic pattern
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/verification-results.md#V-002`, `#V-003`, `#V-004`, `#V-006`

## Pattern

Inventory, font, bounds, overlap, and render-band checks find important failure candidates but cannot establish semantic or visual identity by themselves.

## Root Cause

Extractors infer structure, antialiasing creates pixel noise, and correctness depends on source meaning that summary metrics do not encode.

## Action

Use automated audits over the full book, retain machine-readable exceptions, and resolve every warning with readable source/candidate inspection. A clean report is necessary evidence, never the sole acceptance criterion.
