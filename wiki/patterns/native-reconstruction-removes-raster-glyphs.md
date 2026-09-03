# P-001 Native Reconstruction Removes Raster Glyphs

- Type: failure and corrective strategy
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-002`, `#O-003`

## Pattern

A PDF can expose selectable text while still showing scanned glyphs, or can draw native text directly over those glyphs.

## Root Cause

Invisible OCR changes only searchability. Visible overlays retain raster edges and create dark, doubled, or misaligned text.

## Action

Classify page regions, remove raster glyphs with tight masks and local inpainting, preserve genuine artwork, then draw visible native text. Inspect high-zoom source/candidate crops for residual halos and overlaps.
