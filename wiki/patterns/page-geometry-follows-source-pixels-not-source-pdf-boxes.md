# P-013 Page Geometry Follows Source Pixels, Not Source PDF Boxes

- Type: layout consistency
- Status: active
- Confidence: high
- Evidence: `raw/iteration-001/traces/paired-training-results.md#Training-profile`

## Pattern

Related scans can encode nearly identical printed pages in very different PDF MediaBoxes.

## Root Cause

Scanner/export metadata determines the source PDF box, while the checked publication geometry is tied to the page image canvas and a stable pixel-to-point scale.

## Action

Measure each source page's image dimensions, learn scale only from held-in paired pages, and derive output boxes per page. After any geometry change, recheck order, outlines, links, extraction, artwork placement, and all downstream structure.
