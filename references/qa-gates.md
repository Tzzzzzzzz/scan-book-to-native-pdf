# QA Gates

Apply gates in proportion to the user's fidelity requirement. When the user asks for page-by-page or word-by-word comparison, every page must participate in automated checks and every exception must be visually resolved.

## Required Artifacts

- immutable source hash;
- versioned baseline and candidate PDFs;
- source and candidate renders for every page;
- correction ledger with source evidence;
- raw and layout-preserving text extractions;
- machine-readable audit outputs;
- final hash and delivery path.

## Gate 1: PDF Integrity

- PDF opens with two independent parsers/tools.
- Expected page count, order, boxes, rotation, outlines, and metadata are present.
- No encryption, broken object references, JavaScript, or unexpected forms were introduced.
- A render exists for every page and no page is blank unless the source is blank.

Run:

```text
python scripts/pdf_inventory.py candidate.pdf --pdftotext /path/to/pdftotext --output inventory.json
```

## Gate 2: Truly Native Text

- Body text and code are visible native PDF text, selectable and extractable.
- There is no invisible OCR layer used as the primary solution.
- A full-page scan is not left underneath replacement body/code glyphs.
- Residual image text is limited to approved logos, photographs, or explicit artwork text.
- All production fonts are embedded and have ToUnicode maps, except documented intentional exceptions.
- Run `pdf_nativity.py` on inputs and the candidate. A repeated watermark or page number over a full-page image is a sparse native overlay, not native body text. The reconstructed candidate must classify as `native_or_mixed` or a manually documented equivalent.

Run:

```text
python scripts/font_audit.py candidate.pdf --require-embedded --require-tounicode --output fonts.json
```

Also run OCR or connected-component checks over image XObjects to locate raster words that the layout model classified as native text.

## Gate 3: Content Fidelity

- Each semantic correction has source-pixel evidence.
- Raw extracted-text differences from the frozen baseline equal the correction whitelist exactly.
- Code punctuation, nested delimiters, identifiers, whitespace, strings, comments, and case match the source.
- If text was derived from an existing native PDF, page-level non-space character multisets must match the frozen checked baseline and every extraction-only spacing change must be source-reviewed. Replacement glyphs and unsupported super/subscripts are failures, not harmless OCR noise.
- Tables and figures contain the same cells, labels, and relationships as the source.
- No language-model rewrite, normalization, or typo correction exists unless the scan visibly supports it.

Run:

```text
python scripts/compare_pdf_revisions.py baseline.pdf candidate.pdf \
  --pdftotext /path/to/pdftotext \
  --expected-text-pages 80,87,139 \
  --output revision-audit.json
```

An extraction-only whitespace difference still requires investigation. It can indicate either a real content error or a changed boundary between adjacent PDF text runs.

## Gate 4: Incremental Isolation

- Pages outside the intended patch set retain their extracted text.
- Page boxes and image fingerprints change only on explicitly allowed pages.
- Shared font/typography changes are documented and checked across the full book.
- Temporary text state (`Tz`, color, font, transformation matrices) is reset after replacement objects.

`compare_pdf_revisions.py` treats image and page-box changes as failures unless they are allowed explicitly.

## Gate 5: Layout and Typography

- No word lies outside its page box.
- No visible body/code overlap, clipping, doubled glyph, or white cleanup rectangle remains.
- Code uses the selected monospaced face, point size, tone, indentation, and baseline rhythm consistently.
- Long lines remain readable and do not collide with inline comments.
- CJK comments align with code and use a compatible CJK font.
- A shared code point size and documented horizontal scale are used across the book; edge repositioning is recorded when a comment would otherwise collide.
- Headers, footers, page numbers, captions, and tables follow one coherent publication style.
- For a same-series book with an accepted paired profile, compare aggregate page scale, body/code faces, sizes, and tones against that profile. Do not apply a profile from another series merely because it looks plausible.

Run:

```text
python scripts/bbox_audit.py candidate.pdf --pdftotext /path/to/pdftotext \
  --fail-on-bounds --output bbox-audit.json
```

Treat overlap reports as candidates: visually confirm them. Record source-existing tight boundaries separately from new visible overlap.

## Gate 6: Full-Page Render Comparison

Render source and candidate pages to identically sized PNGs. Verify the count before comparing.

```text
pdftoppm -png -scale-to-x 1000 -scale-to-y -1 source.pdf source/src
pdftoppm -png -scale-to-x 1000 -scale-to-y -1 candidate.pdf candidate/cand
python scripts/render_band_audit.py source candidate --output band-audit.json
```

The band audit looks for source ink bands with almost no candidate ink. It does not prove exact glyph correctness. Visually inspect every warning at high zoom; antialiasing and a new font can produce small false positives.

For an exhaustive requirement, create a page review ledger and mark every page reviewed. Contact sheets accelerate navigation but do not replace readable-resolution inspection.

OCR CER and confidence are triage signals only. Any nonzero semantic or punctuation error must be resolved against source pixels before final acceptance; aggregate averages cannot waive an individual error.

## Gate 7: Tables, Figures, and Raster Residue

- Grid lines and connectors are continuous.
- Native labels do not sit over old raster glyphs.
- Figure/table crops do not contain missed body or code strips.
- Every intentional raster label is documented and allowed by the user.
- Image count and fingerprints remain stable outside approved figure patches.

Inspect high-risk pages separately: dense code, mixed CJK/ASCII comments, tables, diagrams, covers, contents pages, first/last pages, very long rows, and pages changed by manual corrections.

## Gate 8: Promotion and Cleanup

1. Copy the verified candidate to the delivery filename.
2. Hash candidate and delivery copy; require equality.
3. Reopen the delivery copy and repeat page-count/font checks.
4. Report tests, exceptions, size, and SHA-256.
5. Keep intermediates until the user explicitly requests deletion.

For cleanup, resolve absolute paths, ensure every destructive target is inside the intended workspace, exclude the final file by exact resolved path, delete in one filesystem environment, and verify that the final hash is unchanged. State whether deleted files are recoverable.
