from __future__ import annotations

import argparse
import collections
import re
import statistics
from pathlib import Path

import pikepdf

from _pdf_utils import (
    extract_text_pages,
    page_content_bytes,
    resolve_tool,
    write_json,
)


TEXT_SHOW_RE = re.compile(rb"(?<![A-Za-z])(?:Tj|TJ)(?![A-Za-z])")


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def classify(
    image_page_ratio: float,
    text_page_ratio: float,
    median_characters: float,
    recurring_text_share: float,
) -> str:
    if image_page_ratio >= 0.95 and median_characters == 0:
        return "scan_image_only"
    if (
        image_page_ratio >= 0.95
        and median_characters <= 80
        and recurring_text_share >= 0.5
    ):
        return "scan_with_sparse_native_overlay"
    if image_page_ratio >= 0.95 and median_characters > 80:
        return "scan_with_text_layer_candidate"
    if text_page_ratio >= 0.9 and median_characters >= 80 and image_page_ratio < 0.5:
        return "native_or_mixed"
    if text_page_ratio >= 0.9 and median_characters >= 80:
        return "mixed_native_and_raster"
    return "mixed_or_unknown"


def analyze(pdf_path: Path, pdftotext: str, include_details: bool) -> dict[str, object]:
    extracted_pages = extract_text_pages(pdf_path, pdftotext)
    page_rows: list[dict[str, object]] = []
    recurring: collections.Counter[str] = collections.Counter()

    with pikepdf.Pdf.open(pdf_path) as pdf:
        if len(extracted_pages) < len(pdf.pages):
            extracted_pages.extend([""] * (len(pdf.pages) - len(extracted_pages)))
        for page_number, page in enumerate(pdf.pages, 1):
            images = list(page.get_images(recursive=True).values())
            dimensions = [
                (int(image.get("/Width", 0)), int(image.get("/Height", 0)))
                for image in images
            ]
            largest = max(dimensions, key=lambda item: item[0] * item[1], default=(0, 0))
            text = normalized_text(extracted_pages[page_number - 1])
            characters = len("".join(text.split()))
            if text and len(text) <= 160:
                recurring[text] += 1
            content = page_content_bytes(page)
            page_rows.append(
                {
                    "page": page_number,
                    "images": len(images),
                    "largest_image_pixels": largest,
                    "text_show_operators": len(TEXT_SHOW_RE.findall(content)),
                    "extractable_characters": characters,
                    "short_extracted_text": text if len(text) <= 160 else None,
                }
            )

    pages = len(page_rows)
    image_pages = sum(bool(row["images"]) for row in page_rows)
    text_pages = sum(bool(row["extractable_characters"]) for row in page_rows)
    character_counts = [int(row["extractable_characters"]) for row in page_rows]
    top_recurring = recurring.most_common(10)
    recurring_share = top_recurring[0][1] / pages if top_recurring and pages else 0.0
    image_ratio = image_pages / pages if pages else 0.0
    text_ratio = text_pages / pages if pages else 0.0
    median_chars = statistics.median(character_counts) if character_counts else 0.0

    result: dict[str, object] = {
        "path": str(pdf_path),
        "bytes": pdf_path.stat().st_size,
        "pages": pages,
        "classification": classify(image_ratio, text_ratio, median_chars, recurring_share),
        "image_pages": image_pages,
        "extractable_text_pages": text_pages,
        "image_page_ratio": round(image_ratio, 6),
        "text_page_ratio": round(text_ratio, 6),
        "median_extractable_characters": median_chars,
        "recurring_short_text_share": round(recurring_share, 6),
        "recurring_short_text": [
            {"text": text, "pages": count} for text, count in top_recurring
        ],
    }
    if include_details:
        result["details"] = page_rows
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify a PDF as native, image-only scan, or scan with a sparse overlay."
    )
    parser.add_argument("pdf")
    parser.add_argument("--pdftotext", help="Path to Poppler pdftotext.")
    parser.add_argument("--details", action="store_true", help="Include per-page details.")
    parser.add_argument("--expected-class", help="Fail if the classification differs.")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve(strict=True)
    tool = resolve_tool(args.pdftotext, "pdftotext")
    if not tool:
        raise FileNotFoundError("pdftotext is required for native-content classification")
    result = analyze(pdf_path, tool, args.details)
    write_json(args.output, result)
    print(f"classification={result['classification']}")
    print(
        f"pages={result['pages']} image_pages={result['image_pages']} "
        f"text_pages={result['extractable_text_pages']} "
        f"median_characters={result['median_extractable_characters']}"
    )
    if args.expected_class and result["classification"] != args.expected_class:
        print(f"expected={args.expected_class} actual={result['classification']}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
