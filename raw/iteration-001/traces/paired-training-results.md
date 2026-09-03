# Paired Training Results

## Paired split

- Pair: Xiangshan Vol1 scan SHA-256 `FBD6C416C1ABB3763A4175B742E6D14595F2B181E4226FF34AC9DF2E63A1D86E` and v239 SHA-256 `43C41CC388C75D727554E412E2A4B1EF4E970DDE33E999DE82BDE598E0862FF0`.
- Previously inspected pages 139 and 642 were forced into training before the split.
- Deterministic stratified split: 452 training, 98 validation, and 98 test pages.
- Categories: blank/art-only 1, body 114, chapter open 1, chapter open with art 14, cover/front art 3, dense code 192, mixed body/art 17, mixed body/code 302, mixed code/art 4.
- Test pages were not used for the observations below.

## Training profile

- All 452 training pages mapped source image pixels to gold PDF points at exactly `0.54` in both axes.
- Dominant CJK body: SimSun, `9.72 pt`, color `[0.34, 0.34, 0.34]`.
- Dominant Latin body: TimesNewRoman, `9.72 pt`, color `[0.34, 0.34, 0.34]`.
- Dominant code: Consolas, `9.2 pt`, color `[0.32, 0.32, 0.32]`.
- The profile stores aggregate style/geometry only and contains no book transcription.

## OCR probes

- Held-in pages 139 and 642, PaddleOCR: aggregate semantic CER `0.025855`; punctuation CER `0.072617`.
- The same pages, RapidOCR: aggregate semantic CER `0.055091`; punctuation CER `0.116490`.
- PaddleOCR was selected as the primary hypothesis generator and RapidOCR as fallback for this environment.
- The first PaddleOCR attempt failed in oneDNN attribute conversion. Disabling MKLDNN with `FLAGS_use_mkldnn=0` and `enable_mkldnn=False` made inference work.
- Page 139 still contained high-confidence identifier, underscore, delimiter, and spacing errors. OCR confidence therefore cannot authorize publication.

## Held-out validation

- An independently recomputed profile over all 98 validation pages reproduced the training profile: scale `0.54`, SimSun/TimesNewRoman body at `9.72 pt`, Consolas code at `9.2 pt`, and the same dominant tones.
- OCR validation pages were frozen in advance: 4, 18, 33, 49, 58, 91, and 420.
- Aggregate validation semantic CER was `0.016349`; punctuation CER was `0.112288`.
- Per-page semantic/punctuation CER: p4 `0.036036/0.131579`, p18 `0.000733/0.333333`, p33 `0.003476/0`, p49 `0.007629/0.056338`, p58 `0.004513/0.357143`, p91 `0.057279/0.164634`, p420 `0.020103/0.063636`.
- These are diagnostic measurements only. Final acceptance remains zero known source-content errors after page-by-page correction.

## Visual and structural observations

- Vol2 pages 100 and 300 and Vol3 pages 100 and 300 visually share the Xiangshan series' body/code design, but their source PDF page boxes differ materially.
- AI Agent page 20 contains a full-page scan, diagram/QR artwork, and only a repeated native watermark in extraction; this is a cross-domain sparse-overlay case.
- Vol1 source/gold page 139 confirms the checked result removes raster body/code and recomposes cleaner shared typography rather than merely placing text over the scan.
