# Evolution Log

## Iteration 000 - 2026-08-31

- Consolidated ten generalizable success and failure patterns from the observable reconstruction history.
- Bootstrapped `SKILL.md` as the active procedural layer and added `PURPOSE.md` traceability.
- Separated immutable raw evidence from persistent Wiki knowledge and runtime instructions.
- Added disjoint train, validation, and test cases plus strict-improvement gating for future atomic proposals.
- Initialization has no predecessor skill, so it is recorded as a bootstrap rather than an accepted improvement claim.
- Verified the package with the Codex skill validator and the WikiSkill structural validator.
- Exercised validation gating with strict-improvement acceptance, equal-score rejection/rollback, and incomplete-case refusal.
- Exercised render-band QA with a zero-warning positive control and a negative control that identified the deliberately blanked page 2.

## Iteration 001 - 2026-09-01

- Added the original Vol1 scan as a paired source for the checked v239 result, plus Vol2/Vol3 same-series and AI Agent cross-domain evidence.
- Classified Vol1/Vol2/Vol3 as image-only scans, AI Agent as a scan with a sparse repeated native watermark, and v239 as native-or-mixed.
- Froze a deterministic nine-category Vol1 split: 452 train, 98 validation, 98 sealed test pages; pages 139 and 642 were forced into training because they had already been inspected.
- Learned the publication profile only from training pages and independently reproduced its dominant scale, fonts, sizes, and tones over all validation pages.
- Compared PaddleOCR and RapidOCR on held-in pages, retained PaddleOCR as primary after disabling MKLDNN, and preserved RapidOCR as fallback. Nonzero validation punctuation errors remain proof that OCR is hypothesis-only.
- Added five non-duplicative Wiki patterns, four runtime scripts, one conditional style asset, paired-training guidance, and explicit native/geometry/CER QA gates.
- Strict validation gate accepted proposal `C0C2E53A2448341AACF8694B96A3DE05A5D89BCDD16B4DC352075844735ABC48`: incumbent `0.6944444444444444444444444444`, candidate `1.0`, delta `0.3055555555555555555555555556`.
- After acceptance and runtime freeze, opened one test page from each available held-out category: 1, 7, 40, 73, 95, 163, and 382. PaddleOCR completed all pages with aggregate semantic CER `0.011874` and punctuation CER `0.123620`.
- The test confirmed that even high-confidence OCR retains material cover, code, and punctuation errors. No test page was moved into training and no runtime rule or profile was tuned after disclosure.

## Iteration 002 - 2026-09-03

- Replayed the later four-book continuation as immutable raw evidence: visible native text, no hidden OCR, source-authoritative wording, exhaustive page/word review, incremental correction, coherent typography, no arbitrary page ceiling, and post-promotion cleanup.
- Independently reopened the four delivery PDFs: 648, 608, 516, and 163 pages; all 1,935 page rows passed the combined ledger. All production fonts were embedded with ToUnicode maps and no invisible-text pages or structural errors were found.
- Recorded source-backed incremental corrections (Vol1 p6, Agent p18, Vol3 p10/p189/p379/p455/p488) and verified untouched-page preservation through guarded replacement chains.
- Consolidated P-016: automated render/bbox warnings are candidates, so every warning must be source-reviewed, classified, evidenced, and dispositioned; explainable scan artifacts do not become silent failures or silent passes.
- Updated the nativity gate to allow documented `mixed_native_and_raster` output when text-bearing pages are native and remaining raster regions are intentional artwork.
- Strict validation gate accepted proposal `292B73C47849F7E60C39E7B08341CE87D0A23A602EDDC458143AC9B9F7DE39F2`: incumbent `0.8958333333333333333333333333`, candidate `1.0`, delta `0.1041666666666666666666666667`. No test pages were disclosed or tuned after the gate.
