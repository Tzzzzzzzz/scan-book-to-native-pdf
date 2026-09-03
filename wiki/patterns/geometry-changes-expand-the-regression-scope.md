# P-006 Geometry Changes Expand the Regression Scope

- Type: failure prevention
- Status: active
- Confidence: high
- Evidence: `raw/iteration-000/traces/user-feedback.md#O-007`

## Pattern

A correction that changes text width, page count, page boxes, fonts, or shared resources can affect content beyond the edited line.

## Root Cause

PDF placement, extraction order, outlines, links, and resource dictionaries depend on shared structure.

## Action

Keep local edits local when possible. If geometry or shared resources change, expand regression checks to every page and verify page order, boxes, outlines, links, extraction, fonts, and render completeness.
