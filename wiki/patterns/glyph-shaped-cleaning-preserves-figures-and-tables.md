# P-007 Glyph-Shaped Cleaning Preserves Figures and Tables

- Type: failure and corrective strategy
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-003`, `#O-004`

## Pattern

Removing source text with whole OCR rectangles can erase grid rules, arrows, connectors, and nearby artwork.

## Root Cause

OCR boxes describe text extent, not the exact raster glyph mask, and mixed regions share pixels with structural lines.

## Action

Use tight glyph masks and local inpainting. Detect and preserve long rules separately, reconstruct damaged vector geometry, and redraw labels only after the surrounding figure or table is intact.
