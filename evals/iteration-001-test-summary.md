# Iteration 001 One-Time Test Summary

The paired method and runtime instructions were frozen before opening the test split. No runtime file or profile was tuned after the following pages were disclosed.

## Paired Vol1 Test

- Pages: 1, 7, 40, 73, 95, 163, and 382.
- Covered categories: cover/front art, body, mixed body/code, chapter open with art, dense code, mixed code/art, and mixed body/art.
- Backend: PaddleOCR on every page; no initialization or inference fallback was needed.
- Aggregate semantic CER: `0.011874`.
- Aggregate punctuation CER: `0.123620`.
- Page 1 semantic CER was `0.364706`; page 7 punctuation CER was `0.500000`; dense-code page 95 was `0.013339/0.152866` semantic/punctuation CER.
- Full machine-readable results are in `iteration-001-test-ocr-report.json`.

These measurements do not claim publication fidelity. They confirm that the frozen workflow reports rather than hides OCR errors and that raw OCR still requires source-backed correction to zero known errors.

## Generalization Cases

- Xiangshan Vol2 and Vol3 remain image-only scans and supply same-series layout/style evidence without a gold transcription. Their differing source MediaBoxes require per-page source-pixel geometry.
- The AI Agent book remains a scan with a sparse repeated native watermark and supplies a cross-domain classifier/layout case. Its Xiangshan style profile must not be applied without independent evidence.

No new reconstructed Vol2, Vol3, or AI Agent PDF was produced in this skill-evolution iteration; the test target was the reusable method and its acceptance behavior.
