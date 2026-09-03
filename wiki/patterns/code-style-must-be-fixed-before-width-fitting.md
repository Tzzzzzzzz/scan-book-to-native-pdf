# P-004 Code Style Must Be Fixed Before Width Fitting

- Type: failure and corrective strategy
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-003`, `#O-008`

## Pattern

Per-line font fitting makes code vary in size, weight, darkness, and mixed-script alignment.

## Root Cause

Independent OCR boxes are optimized to local width instead of a shared publication style.

## Action

Fix one face, point size, tone, and baseline rhythm per code style. Preserve indentation and comments. Fit long rows using bounded horizontal scaling or deliberate reflow, never silent line-specific point-size reduction.
