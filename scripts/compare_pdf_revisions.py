from __future__ import annotations

import argparse
from pathlib import Path

import pikepdf

from _pdf_utils import (
    extract_text_pages,
    image_fingerprints,
    page_box,
    page_content_hash,
    parse_page_spec,
    resolve_tool,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare a checked PDF baseline with a candidate.")
    parser.add_argument("base")
    parser.add_argument("candidate")
    parser.add_argument("--pdftotext", help="Path to Poppler pdftotext; auto-detected when omitted.")
    parser.add_argument("--expected-text-pages", help="Exact one-based page set, e.g. 80,87,139-141.")
    parser.add_argument("--allow-image-pages", help="Pages allowed to change image fingerprints.")
    parser.add_argument("--allow-box-pages", help="Pages allowed to change MediaBox/CropBox/rotation.")
    parser.add_argument("--allow-page-count-change", action="store_true")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    base_path = Path(args.base).expanduser().resolve(strict=True)
    candidate_path = Path(args.candidate).expanduser().resolve(strict=True)
    base = pikepdf.Pdf.open(base_path)
    candidate = pikepdf.Pdf.open(candidate_path)
    compared_pages = min(len(base.pages), len(candidate.pages))

    content_changed: list[int] = []
    image_changed: list[int] = []
    box_changed: list[int] = []
    for index in range(compared_pages):
        base_page = base.pages[index]
        candidate_page = candidate.pages[index]
        page_number = index + 1
        if page_content_hash(base_page) != page_content_hash(candidate_page):
            content_changed.append(page_number)
        if image_fingerprints(base_page) != image_fingerprints(candidate_page):
            image_changed.append(page_number)
        base_geometry = (
            page_box(base_page, "/MediaBox"),
            page_box(base_page, "/CropBox"),
            int(base_page.obj.get("/Rotate", 0)),
        )
        candidate_geometry = (
            page_box(candidate_page, "/MediaBox"),
            page_box(candidate_page, "/CropBox"),
            int(candidate_page.obj.get("/Rotate", 0)),
        )
        if base_geometry != candidate_geometry:
            box_changed.append(page_number)

    tool = resolve_tool(args.pdftotext, "pdftotext")
    text_changed: list[int] | None = None
    if tool:
        base_text = extract_text_pages(base_path, tool)
        candidate_text = extract_text_pages(candidate_path, tool)
        text_changed = [
            index + 1
            for index, (left, right) in enumerate(zip(base_text, candidate_text))
            if left != right
        ]
        if len(base_text) != len(candidate_text):
            text_changed.extend(
                range(min(len(base_text), len(candidate_text)) + 1, max(len(base_text), len(candidate_text)) + 1)
            )

    expected_text = (
        parse_page_spec(args.expected_text_pages)
        if args.expected_text_pages is not None
        else None
    )
    allowed_images = parse_page_spec(args.allow_image_pages)
    allowed_boxes = parse_page_spec(args.allow_box_pages)
    violations: list[str] = []

    if len(base.pages) != len(candidate.pages) and not args.allow_page_count_change:
        violations.append(f"page count changed: {len(base.pages)} -> {len(candidate.pages)}")
    unexpected_images = sorted(set(image_changed) - allowed_images)
    unexpected_boxes = sorted(set(box_changed) - allowed_boxes)
    if unexpected_images:
        violations.append(f"unexpected image changes: {unexpected_images}")
    if unexpected_boxes:
        violations.append(f"unexpected page geometry changes: {unexpected_boxes}")
    if expected_text is not None:
        if text_changed is None:
            violations.append("expected text pages were supplied but pdftotext is unavailable")
        elif set(text_changed) != expected_text:
            violations.append(
                f"text change set mismatch: expected {sorted(expected_text)}, actual {text_changed}"
            )

    report = {
        "base": str(base_path),
        "candidate": str(candidate_path),
        "base_pages": len(base.pages),
        "candidate_pages": len(candidate.pages),
        "content_changed_pages": content_changed,
        "text_changed_pages": text_changed,
        "image_changed_pages": image_changed,
        "box_changed_pages": box_changed,
        "violations": violations,
    }
    write_json(args.output, report)

    print(f"pages={len(base.pages)}/{len(candidate.pages)}")
    print(f"content_changed={len(content_changed)} {content_changed}")
    print(f"text_changed={None if text_changed is None else len(text_changed)} {text_changed}")
    print(f"image_changed={len(image_changed)} {image_changed}")
    print(f"box_changed={len(box_changed)} {box_changed}")
    print(f"violations={len(violations)}")
    for violation in violations:
        print(f"ERROR: {violation}")
    return 2 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
