# P-011 Paired Gold Training Needs Stratified Holdouts

- Type: evaluation integrity
- Status: active
- Confidence: high
- Evidence: `raw/iteration-001/traces/paired-training-results.md#Paired-split`

## Pattern

A page-aligned source/gold pair can teach reusable reconstruction choices, but page browsing before splitting leaks answers into evaluation.

## Root Cause

Technical books mix covers, prose, dense code, diagrams, and chapter openers; a random or post-hoc sample can omit difficult classes and inflate results.

## Action

Hash the pair, force every previously viewed page into training, then freeze deterministic category-stratified train/validation/test splits. Tune only on training, validate independently, and open test pages once after all choices are frozen.
