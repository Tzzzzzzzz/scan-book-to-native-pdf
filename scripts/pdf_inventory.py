from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import pikepdf

from _pdf_utils import extract_text_pages, page_box, page_content_bytes, resolve_tool, write_json


TEXT_SHOW_RE = re.compile(rb"(?<![A-Za-z])(?:Tj|TJ)(?![A-Za-z])")


def resource_fonts(page: pikepdf.Page) -> list[str]:
    resources = page.obj.get("/Resources")
    if resources is None:
        try:
            resources = page.Resources
        except AttributeError:
            return []
    fonts = resources.get("/Font", {})
    return sorted(str(name) for name in fonts.keys())


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory a scanned or native PDF.")
    parser.add_argument("pdf")
    parser.add_argument("--pdftotext", help="Path to Poppler pdftotext; auto-detected when omitted.")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve(strict=True)
    pdf = pikepdf.Pdf.open(pdf_path)
    pages: list[dict[str, object]] = []
    size_counts: Counter[tuple[float, ...]] = Counter()

    for number, page in enumerate(pdf.pages, 1):
        content = page_content_bytes(page)
        box = page_box(page)
        size_counts[box] += 1
        images = page.get_images(recursive=True)
        pages.append(
            {
                "page": number,
                "media_box": box,
                "rotation": int(page.obj.get("/Rotate", 0)),
                "image_count": len(images),
                "text_show_operators": len(TEXT_SHOW_RE.findall(content)),
                "content_bytes": len(content),
                "font_resources": resource_fonts(page),
            }
        )

    tool = resolve_tool(args.pdftotext, "pdftotext")
    if tool:
        extracted = extract_text_pages(pdf_path, tool)
        for index, page in enumerate(pages):
            text = extracted[index] if index < len(extracted) else ""
            page["extractable_characters"] = len("".join(text.split()))

    summary = {
        "path": str(pdf_path),
        "file_size": pdf_path.stat().st_size,
        "pages": len(pdf.pages),
        "encrypted": bool(pdf.is_encrypted),
        "page_sizes": [
            {"media_box": box, "pages": count}
            for box, count in sorted(size_counts.items(), key=lambda item: item[0])
        ],
        "pages_with_images": [page["page"] for page in pages if page["image_count"]],
        "pages_with_text_operators": [
            page["page"] for page in pages if page["text_show_operators"]
        ],
        "image_only_candidates": [
            page["page"]
            for page in pages
            if page["image_count"] and not page["text_show_operators"]
        ],
        "extractable_text_pages": (
            [page["page"] for page in pages if page.get("extractable_characters", 0)]
            if tool
            else None
        ),
        "details": pages,
    }
    write_json(args.output, summary)

    print(f"path={pdf_path}")
    print(f"pages={summary['pages']} bytes={summary['file_size']}")
    print(
        f"pages_with_images={len(summary['pages_with_images'])} "
        f"pages_with_text_operators={len(summary['pages_with_text_operators'])}"
    )
    print(f"image_only_candidates={len(summary['image_only_candidates'])}")
    if tool:
        print(f"extractable_text_pages={len(summary['extractable_text_pages'])}")
    else:
        print("extractable_text_pages=not_checked (pdftotext unavailable)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
