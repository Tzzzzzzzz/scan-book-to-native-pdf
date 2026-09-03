# OCR and Layout Data Model

Use a structured, versioned model so content corrections and geometry changes can be reviewed independently.

## Suggested Page Record

```json
{
  "page": 138,
  "source_width": 1000,
  "source_height": 1478,
  "items": [
    {
      "id": "p0139-i0021",
      "text": "def doFuncTerm: TermName = {",
      "box": [[67, 693], [330, 693], [330, 713], [67, 713]],
      "confidence": 0.97,
      "role": "code",
      "line_id": "p0139-l0021",
      "ocr_source": "engine-name",
      "evidence": null
    }
  ]
}
```

Use zero-based page indices inside machine data only when every consumer agrees. Display one-based page numbers to users and in filenames. Store the convention in the dataset metadata.

## Coordinates

OCR boxes normally use top-left pixel coordinates. PDF user space normally uses bottom-left points.

For source dimensions `Wpx x Hpx` and PDF page `Wpt x Hpt`:

```text
sx = Wpt / Wpx
sy = Hpt / Hpx
x_pdf = x_px * sx
y_pdf = Hpt - y_px * sy
```

For a top-left OCR rectangle `(x0, y0, x1, y1)`, its PDF bottom-left placement is approximately:

```text
x = x0 * sx
y = Hpt - y1 * sy
width = (x1 - x0) * sx
height = (y1 - y0) * sy
```

Do not assume `sx == sy` without checking. Estimate the text baseline from glyph/line evidence rather than using the rectangle bottom blindly.

## Stable Identity and Corrections

Do not key corrections only by array index; OCR merges and insertions shift indices. Prefer a stable item ID plus page, approximate box, and old-text guard.

A correction record should contain:

```json
{
  "page": 139,
  "item_id": "p0139-i0043",
  "old_text": "binop(sourceInfo, UInt(this.width max that.width) + 1), AddOp, that)",
  "new_text": "binop(sourceInfo, UInt((this.width max that.width) + 1), AddOp, that)",
  "reason": "nested parenthesis confirmed at high zoom",
  "source_crop": "evidence/source-p0139-bottom.png",
  "verified": true
}
```

Apply a correction only when the old-text guard and approximate geometry both match. Fail loudly on zero or multiple matches.

## Roles and Rendering Policy

Useful roles include:

- `body`, `heading`, `header`, `footer`, `page-number`;
- `code`, `code-comment`, `inline-code`;
- `caption`, `table-label`, `figure-label`;
- `artwork-text` for text intentionally retained inside an image.

The role determines font choice, cleaning strategy, grouping, and QA. `artwork-text` must be an explicit, user-compatible decision, not a fallback for OCR difficulty.

## Reading Order and Mixed Runs

Store line IDs and reading order separately from spatial order. A code line may contain several native objects: monospaced ASCII, a CJK comment marker, and CJK comment text. Group by baseline first; x distance alone can split a legitimate line.

Retain source run boundaries when extraction behavior depends on them. After font changes, compare both visible spacing and raw extracted text.
