# Final QA Observations

The four final delivery PDFs were independently reopened after incremental page replacement and copied to their delivery names.

| Corpus | Pages | Classification | Native text pages | Image-bearing pages | PDF errors |
| --- | ---: | --- | ---: | ---: | ---: |
| Xiangshan Vol1 | 648 | native_or_mixed | 647 | 39 | 0 |
| Xiangshan Vol2 | 608 | native_or_mixed | 606 | 48 | 0 |
| Xiangshan Vol3 | 516 | native_or_mixed | 515 | 39 | 0 |
| AI Agent | 163 | mixed_native_and_raster | 162 | 99 | 0 |

All delivery fonts were embedded and had ToUnicode maps; invisible-text pages and blank pages were zero. The combined page ledger covered 1,935 source/final page pairs and reported every page pass.

Incremental corrections restored source-visible rules on Vol1 page 6 and AI Agent page 18. Vol3 separators were restored on pages 10, 189, 379, 455, and 488 through a guarded five-page replacement chain; untouched-page content hashes remained unchanged at every step.

The final render-band audit produced a small set of explainable differences: scan-edge speckles, repeated scan watermarks/QR marks, contrast variation inside source-verified raster figures, and one normalized baseline shift. Each was recorded with a page/box and disposition; none represented missing book content.

Evidence reports: `qa/final/four-pdf-regression-final.json`, `qa/final/four-book-delivery-manifest-final.json`, and `qa/final/four-book-revision-acceptance-final.json`.
