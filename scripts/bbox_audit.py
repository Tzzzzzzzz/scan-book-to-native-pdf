from __future__ import annotations

import argparse
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from _pdf_utils import resolve_tool, write_json


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_text(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Poppler word bounds and same-line overlaps.")
    parser.add_argument("pdf")
    parser.add_argument("--pdftotext", help="Path to Poppler pdftotext; auto-detected when omitted.")
    parser.add_argument("--tolerance", type=float, default=0.25)
    parser.add_argument("--min-overlap", type=float, default=0.35)
    parser.add_argument("--fail-on-bounds", action="store_true")
    parser.add_argument("--max-overlaps", type=int)
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve(strict=True)
    tool = resolve_tool(args.pdftotext, "pdftotext")
    if not tool:
        raise FileNotFoundError("pdftotext is required; pass --pdftotext")

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as handle:
        bbox_path = Path(handle.name)
    try:
        result = subprocess.run(
            [tool, "-bbox-layout", str(pdf_path), str(bbox_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            message = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"pdftotext failed ({result.returncode}): {message}")
        root = ET.parse(bbox_path).getroot()
    finally:
        bbox_path.unlink(missing_ok=True)

    bounds: list[dict[str, object]] = []
    overlaps: list[dict[str, object]] = []
    word_count = 0
    page_number = 0
    for page in (element for element in root.iter() if local_name(element.tag) == "page"):
        page_number += 1
        width = float(page.attrib["width"])
        height = float(page.attrib["height"])
        for line in (element for element in page.iter() if local_name(element.tag) == "line"):
            words: list[tuple[float, float, float, float, str]] = []
            for word in (element for element in line if local_name(element.tag) == "word"):
                x0 = float(word.attrib["xMin"])
                y0 = float(word.attrib["yMin"])
                x1 = float(word.attrib["xMax"])
                y1 = float(word.attrib["yMax"])
                text = element_text(word)
                word_count += 1
                words.append((x0, y0, x1, y1, text))
                if (
                    x0 < -args.tolerance
                    or y0 < -args.tolerance
                    or x1 > width + args.tolerance
                    or y1 > height + args.tolerance
                ):
                    bounds.append(
                        {"page": page_number, "text": text, "box": [x0, y0, x1, y1], "page_size": [width, height]}
                    )
            words.sort(key=lambda item: (item[0], item[1]))
            for left, right in zip(words, words[1:]):
                overlap = left[2] - right[0]
                if overlap > args.min_overlap:
                    overlaps.append(
                        {
                            "page": page_number,
                            "left": left[4],
                            "right": right[4],
                            "overlap": overlap,
                            "left_box": left[:4],
                            "right_box": right[:4],
                        }
                    )

    report = {
        "path": str(pdf_path),
        "pages": page_number,
        "words": word_count,
        "bounds_violations": bounds,
        "same_line_overlaps": overlaps,
    }
    write_json(args.output, report)
    print(f"pages={page_number} words={word_count}")
    print(f"bounds_violations={len(bounds)}")
    print(f"same_line_overlaps={len(overlaps)}")

    failed = args.fail_on_bounds and bool(bounds)
    if args.max_overlaps is not None and len(overlaps) > args.max_overlaps:
        failed = True
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
