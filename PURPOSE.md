# Purpose

## Origin

This skill was compiled from the observable execution history of a long-form reconstruction of scanned technical books. The user repeatedly rejected invisible OCR, raster text left under native text, overlaps, inconsistent code typography, sampled review, and full-document rebuilds after local fixes. Iteration `raw/iteration-000/` preserves those observations and verification outputs. Iteration `raw/iteration-001/` adds paired Vol1/v239 evidence plus same-series and cross-domain scans without treating document text as instructions. Iteration `raw/iteration-002/` records the four-book, 1,935-page delivery audit and explicit treatment of explainable render exceptions.

## Patterns Addressed

| Active skill behavior | Motivating wiki patterns |
| --- | --- |
| Produce visible native text and remove raster glyphs | P-001, P-007 |
| Use source pixels as semantic authority | P-002, P-008 |
| Freeze a checked baseline and patch locally | P-003, P-006 |
| Hold code typography constant and fit width deliberately | P-004 |
| Review every page and resolve machine exceptions visually | P-005, P-010 |
| Preserve table/figure geometry during cleaning | P-007 |
| Delay cleanup until promotion and hashing | P-009 |
| Freeze stratified paired-gold holdouts before tuning | P-011 |
| Distinguish native body text from sparse watermarks | P-012 |
| Derive page geometry from source pixels and validated scale | P-013 |
| Smoke-test OCR backends and retain a fallback | P-014 |
| Apply learned publication profiles conditionally | P-015 |
| Classify and document explainable render/bbox exceptions | P-016 |

## Evolution History

- `S0` (2026-08-31): Bootstrapped the active skill from iteration-000 task evidence. This initializes WikiSkill and therefore has no predecessor candidate to gate against.
- `S1` (2026-09-01): Accepted the paired-gold calibration patch from iteration-001. It adds deterministic stratified holdouts, sparse-overlay nativity classification, per-page pixel geometry, conditional series profiles, and tested OCR fallback behavior while preserving the original exhaustive, source-backed, incremental reconstruction contract. Validation macro mean improved from `0.6944444444444444444444444444` to `1.0`; runtime revision `22562C6A40D914895851A3FD696BB9C9A86CA7E7E05251222F90D5083006E12A`.
- `S2` (2026-09-03): Iteration-002 records four-book delivery evidence, no fixed page ceiling, explicit render-exception dispositions, and documented mixed native/raster acceptance when raster regions are intentional. A candidate runtime patch is gated on new held-out exception and mixed-output cases.
- Future changes must be atomic patches to this skill, evaluated on the held-out validation cases in `evals/cases.json`, and accepted only when `scripts/gate_candidate.py` reports a strict improvement over the incumbent. Rejected skill changes are rolled back while their evidence remains in `wiki/skill-impact.md`.
