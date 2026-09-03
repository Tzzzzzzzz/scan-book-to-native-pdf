# P-015 Series Style Profiles Are Conditional

- Type: generalization control
- Status: active
- Confidence: high
- Evidence: `raw/iteration-001/traces/corpus-inventory.json`

## Pattern

Aggregate typography learned from a checked volume can improve related volumes without becoming a universal template.

## Root Cause

Volumes in one publication series share design intent, while unrelated books differ in page geometry, fonts, artwork, watermarks, and content density.

## Action

Store only aggregate geometry and typography, require independent same-series or style-match evidence before applying the profile, and derive a new profile for cross-domain books. In every case, source pixels retain semantic authority.
