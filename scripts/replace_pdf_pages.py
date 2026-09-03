from __future__ import annotations

"""Replace a verified set of page drawing streams in one incremental pass."""

import argparse
import json
from pathlib import Path

import pikepdf

from _pdf_utils import page_box, page_content_hash, parse_page_spec


PAGE_BOX_KEYS = ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox")


def _copy_page_streams(base: pikepdf.Pdf, target: pikepdf.Page, source: pikepdf.Page) -> None:
    """Import only visible page streams/resources, retaining base page metadata."""
    base.pages.append(source)
    imported = base.pages[-1]
    source_contents = imported.obj.get("/Contents")
    source_resources = imported.obj.get("/Resources")
    if source_contents is None or source_resources is None:
        del base.pages[-1]
        raise ValueError("patch page must have explicit Contents and Resources")
    target.obj["/Contents"] = source_contents
    target.obj["/Resources"] = source_resources
    del base.pages[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="checked baseline PDF")
    parser.add_argument("--patch", required=True, help="same-size candidate PDF")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--pages",
        required=True,
        help="one-based pages/ranges to replace, e.g. 2,4-8",
    )
    parser.add_argument("--allow-page-box-change", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()

    base_path = Path(args.base).expanduser().resolve(strict=True)
    patch_path = Path(args.patch).expanduser().resolve(strict=True)
    output_path = Path(args.output).expanduser().resolve()
    if output_path in {base_path, patch_path}:
        raise ValueError("output must not overwrite the base or patch PDF")

    selected = sorted(parse_page_spec(args.pages))
    if not selected:
        raise ValueError("--pages selected no pages")

    base = pikepdf.Pdf.open(base_path)
    patch = pikepdf.Pdf.open(patch_path)
    if len(base.pages) != len(patch.pages):
        raise ValueError(
            f"page count mismatch: base={len(base.pages)} patch={len(patch.pages)}"
        )
    invalid = [page for page in selected if page > len(base.pages)]
    if invalid:
        raise IndexError(f"pages outside 1..{len(base.pages)}: {invalid}")

    before = {index: page_content_hash(page) for index, page in enumerate(base.pages)}
    source_hashes = {
        page - 1: page_content_hash(patch.pages[page - 1]) for page in selected
    }
    box_mismatches = []
    for page in selected:
        target = base.pages[page - 1]
        source = patch.pages[page - 1]
        if not args.allow_page_box_change and page_box(target) != page_box(source):
            box_mismatches.append(
                {"page": page, "base": page_box(target), "patch": page_box(source)}
            )
    if box_mismatches:
        raise ValueError(f"page box mismatches: {box_mismatches[:8]}")

    for page in selected:
        _copy_page_streams(base, base.pages[page - 1], patch.pages[page - 1])
        if args.allow_page_box_change:
            # This option is intentionally explicit; ordinary typography
            # patches must leave all page geometry owned by the baseline.
            target = base.pages[page - 1]
            source = patch.pages[page - 1]
            for key in PAGE_BOX_KEYS:
                value = source.obj.get(key)
                if value is None:
                    target.obj.pop(key, None)
                else:
                    target.obj[key] = pikepdf.Array([float(number) for number in value])
            if source.obj.get("/Rotate") is None:
                target.obj.pop("/Rotate", None)
            else:
                target.obj["/Rotate"] = int(source.obj.get("/Rotate"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(output_path)
    checked = pikepdf.Pdf.open(output_path)
    if len(checked.pages) != len(base.pages):
        raise RuntimeError("page count changed during page replacement")
    changed_elsewhere = [
        index + 1
        for index, digest in before.items()
        if index not in source_hashes and page_content_hash(checked.pages[index]) != digest
    ]
    if changed_elsewhere:
        raise RuntimeError(f"untouched page content changed: {changed_elsewhere[:20]}")
    replacement_mismatches = [
        page
        for page, digest in source_hashes.items()
        if page_content_hash(checked.pages[page]) != digest
    ]
    if replacement_mismatches:
        raise RuntimeError(f"replacement pages do not match patch: {replacement_mismatches}")

    result = {
        "base": str(base_path),
        "patch": str(patch_path),
        "output": str(output_path),
        "pages": selected,
        "page_count": len(checked.pages),
        "untouched_page_content_changes": 0,
        "replacement_page_mismatches": 0,
    }
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
