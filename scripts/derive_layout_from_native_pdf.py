#!/usr/bin/env python3
"""Derive a native-rebuild layout from an already checked text PDF.

This adapter is intentionally conservative: the checked PDF supplies the
wording and image objects, while :mod:`build_pdf` supplies the publication
fonts and role-based typography.  It is useful when the original OCR layout
ledger is no longer available but a checked native baseline is available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pikepdf


IMAGE_MATRIX_RE = re.compile(
    rb"q\s+([-+0-9.eE]+)\s+0\s+0\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+cm\s+/(I\d+)\s+Do\s+Q"
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
OPEN_PUNCT = set("([{<")
CLOSE_PUNCT = set(")]}>.,;:!?，。；：！？、")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def pdftotext_bytes(executable: str, pdf: Path, *options: str) -> bytes:
    command = [executable, *options, "-enc", "UTF-8", str(pdf), "-"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"pdftotext failed ({result.returncode}): {message}")
    return result.stdout


def parse_bbox(data: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(data)
    pages: list[dict[str, Any]] = []
    for page in root.findall(".//{*}page"):
        words: list[dict[str, Any]] = []
        for element in page.findall("./{*}word"):
            text = str(element.text or "")
            if not text.strip():
                continue
            values = {
                "text": text,
                "x0": float(element.attrib["xMin"]),
                "y0": float(element.attrib["yMin"]),
                "x1": float(element.attrib["xMax"]),
                "y1": float(element.attrib["yMax"]),
            }
            values["w"] = values["x1"] - values["x0"]
            values["h"] = values["y1"] - values["y0"]
            values["center"] = (values["y0"] + values["y1"]) * 0.5
            values["vertical"] = values["h"] > values["w"] * 1.5 and values["h"] > 25.0
            words.append(values)
        pages.append(
            {
                "width": float(page.attrib.get("width", 0.0)),
                "height": float(page.attrib.get("height", 0.0)),
                "words": words,
            }
        )
    return pages


def is_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def needs_space(previous: dict[str, Any], current: dict[str, Any], gap: float) -> bool:
    """Recreate source inter-token spaces without spacing CJK phrases apart."""
    left = str(previous["text"])
    right = str(current["text"])
    if not left or not right or gap <= 0.55:
        return False
    left_last = left[-1]
    right_first = right[0]
    if left_last in OPEN_PUNCT or right_first in CLOSE_PUNCT:
        return False
    if is_cjk(left) and is_cjk(right) and gap < 2.0:
        return False
    # Word gaps in the source code are visibly larger than punctuation gaps.
    # A modest threshold also preserves spaces around mixed-script comments.
    return gap >= 1.15 or (not is_cjk(left) and not is_cjk(right) and gap > 0.7)


def join_words(words: list[dict[str, Any]]) -> str:
    if not words:
        return ""
    pieces = [str(words[0]["text"])]
    for previous, current in zip(words, words[1:]):
        gap = float(current["x0"]) - float(previous["x1"])
        if needs_space(previous, current, gap):
            pieces.append(" ")
        pieces.append(str(current["text"]))
    return "".join(pieces)


def cluster_rows(
    words: list[dict[str, Any]], page_width: float, page_height: float
) -> list[list[dict[str, Any]]]:
    """Cluster horizontal words by baseline while keeping rotated words apart."""
    horizontal = [word for word in words if not word["vertical"]]
    vertical = [word for word in words if word["vertical"]]
    # The running page number frequently overlaps the header's vertical
    # extent in the source PDF (its baseline is a few points lower).  Keep it
    # as an independent line so the rebuilt header cannot concatenate it with
    # the chapter title.  Restrict this guard to the upper-right furniture
    # band; numeric code tokens elsewhere must remain with their code row.
    furniture_numbers = [
        word
        for word in horizontal
        if re.fullmatch(r"\d{1,4}", str(word["text"]))
        and float(word["x0"]) >= page_width * 0.84
        and float(word["y0"]) <= page_height * 0.09
    ]
    for word in furniture_numbers:
        word["furniture_number"] = True
    furniture_ids = {id(word) for word in furniture_numbers}
    horizontal = [word for word in horizontal if id(word) not in furniture_ids]
    rows: list[dict[str, Any]] = []
    for word in sorted(horizontal, key=lambda item: (item["center"], item["x0"])):
        chosen: dict[str, Any] | None = None
        best = float("inf")
        for row in rows:
            distance = abs(float(word["center"]) - float(row["center"]))
            overlap = max(
                0.0,
                min(float(word["y1"]), float(row["y1"]))
                - max(float(word["y0"]), float(row["y0"])),
            )
            minimum_height = min(float(word["h"]), float(row["h"]))
            if (overlap >= minimum_height * 0.20 or distance <= 3.4) and distance < best:
                chosen = row
                best = distance
        if chosen is None:
            rows.append(
                {
                    "words": [word],
                    "center": word["center"],
                    "y0": word["y0"],
                    "y1": word["y1"],
                    "h": word["h"],
                }
            )
        else:
            chosen["words"].append(word)
            chosen["center"] = sum(item["center"] for item in chosen["words"]) / len(
                chosen["words"]
            )
            chosen["y0"] = min(chosen["y0"], word["y0"])
            chosen["y1"] = max(chosen["y1"], word["y1"])
            chosen["h"] = chosen["y1"] - chosen["y0"]

    output: list[list[dict[str, Any]]] = []
    for row in sorted(rows, key=lambda item: (item["y0"], min(w["x0"] for w in item["words"]))):
        row_words = sorted(row["words"], key=lambda item: (item["x0"], item["y0"]))
        if not row_words:
            continue
        # A large gap denotes separate columns (for example a header and its
        # page number, or source code and an explanatory side note).  Smaller
        # gaps remain one line so code indentation and comments are retained.
        median_height = sorted(float(item["h"]) for item in row_words)[len(row_words) // 2]
        split_gap = max(28.0, median_height * 3.8)
        current = [row_words[0]]
        for previous, word in zip(row_words, row_words[1:]):
            gap = float(word["x0"]) - float(previous["x1"])
            if gap > split_gap:
                output.append(current)
                current = [word]
            else:
                current.append(word)
        output.append(current)

    # Add isolated page-number rows after the normal horizontal clustering.
    for word in furniture_numbers:
        output.append([word])

    # Each vertical word is already a meaningful rotated line in the source.
    # Append them in visual reading order; the builder rotates them clockwise.
    for word in sorted(vertical, key=lambda item: (item["x0"], item["y0"])):
        output.append([word])
    return sorted(output, key=lambda group: (min(item["y0"] for item in group), min(item["x0"] for item in group)))


def line_record(group: list[dict[str, Any]], page: int, render_width: int, render_height: int) -> dict[str, Any]:
    x0 = min(float(item["x0"]) for item in group)
    y0 = min(float(item["y0"]) for item in group)
    x1 = max(float(item["x1"]) for item in group)
    y1 = max(float(item["y1"]) for item in group)
    if any(item.get("furniture_number") for item in group):
        # Keep the running folio clear of the long header title.  The source
        # text boxes overlap by a few points because the title and folio use
        # different baselines; a small rightward nudge preserves the visual
        # relationship while giving the native objects independent bounds.
        x0 += 8.0
        x1 += 8.0
    scale_x = render_width / 540.0
    scale_y = render_height / (540.0 * render_height / render_width)
    # The source pages use a stable 0.54 point/pixel geometry.  Keep the
    # record in top-origin pixels so it is consumed by the existing renderer.
    text = join_words(sorted(group, key=lambda item: item["x0"]))
    record: dict[str, Any] = {
        "text": text,
        "confidence": 1.0,
        "box": [
            int(round(x0 * scale_x)),
            int(round(y0 * scale_x)),
            int(round(x1 * scale_x)),
            int(round(y1 * scale_x)),
        ],
        "polygon": [
            [int(round(x0 * scale_x)), int(round(y0 * scale_x))],
            [int(round(x1 * scale_x)), int(round(y0 * scale_x))],
            [int(round(x1 * scale_x)), int(round(y1 * scale_x))],
            [int(round(x0 * scale_x)), int(round(y1 * scale_x))],
        ],
        "ocr_source": "checked_native_pdf",
        "ocr_selected_source": "checked_native_pdf",
        "source_verified": True,
        "needs_review": False,
    }
    if group[0]["vertical"]:
        record["text_orientation"] = "clockwise_90"
    return record


def split_groups_over_artwork(
    groups: list[list[dict[str, Any]]], artwork_boxes: list[list[int]]
) -> list[list[dict[str, Any]]]:
    """Keep labels over figures/tables at their source x positions.

    A row extractor normally joins nearby words into one line.  That is right
    for prose and code, but wrong for a table: each cell has a modest gap and
    the joined replacement would pack all symbols at the left edge.  Splitting
    only rows that intersect a retained artwork region preserves the grid and
    keeps the labels selectable.
    """
    if not artwork_boxes:
        return groups
    output: list[list[dict[str, Any]]] = []
    for group in groups:
        gx0 = min(float(item["x0"]) for item in group)
        gy0 = min(float(item["y0"]) for item in group)
        gx1 = max(float(item["x1"]) for item in group)
        gy1 = max(float(item["y1"]) for item in group)
        group_area = max(1.0, (gx1 - gx0) * (gy1 - gy0))
        intersects = False
        for ax0, ay0, ax1, ay1 in artwork_boxes:
            overlap = max(0.0, min(gx1, ax1) - max(gx0, ax0)) * max(
                0.0, min(gy1, ay1) - max(gy0, ay0)
            )
            if overlap / group_area >= 0.08:
                intersects = True
                break
        if intersects and len(group) > 1:
            output.extend([[word] for word in group])
        else:
            output.append(group)
    return output


def page_content(page: Any) -> bytes:
    contents = page.Contents
    if isinstance(contents, pikepdf.Array):
        return b"\n".join(bytes(item.read_bytes()) for item in contents)
    return bytes(contents.read_bytes())


def extract_images(page: Any, page_dir: Path, page_width: float, page_height: float, render_width: int, render_height: int) -> list[dict[str, Any]]:
    resources = page.Resources or {}
    xobjects = resources.get("/XObject", {}) or {}
    data = page_content(page)
    images: list[dict[str, Any]] = []
    for index, (width_raw, height_raw, x_raw, y_raw, name_raw) in enumerate(IMAGE_MATRIX_RE.findall(data), 1):
        name = "/" + name_raw.decode("latin1")
        obj = xobjects.get(name)
        if obj is None or str(obj.get("/Subtype", "")) != "/Image":
            continue
        width = float(width_raw)
        height = float(height_raw)
        x = float(x_raw)
        y = float(y_raw)
        sx = render_width / page_width
        sy = render_height / page_height
        box = [
            int(round(x * sx)),
            int(round((page_height - y - height) * sy)),
            int(round((x + width) * sx)),
            int(round((page_height - y) * sy)),
        ]
        suffix = ".jpg" if str(obj.get("/Filter", "")) == "/DCTDecode" else ".bin"
        path = page_dir / f"art-{index:02d}{suffix}"
        path.write_bytes(bytes(obj.read_raw_bytes()))
        images.append({"box": box, "path": path.name})
    return images


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_pdf")
    parser.add_argument("output_dir")
    parser.add_argument("--pages", help="one-based pages/ranges; default is all pages")
    parser.add_argument("--render-width", type=int, default=1500)
    parser.add_argument("--pdftotext", default="pdftotext")
    args = parser.parse_args()

    source = Path(args.native_pdf).expanduser().resolve(strict=True)
    output = Path(args.output_dir).expanduser().resolve()
    pages_dir = output / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    pdftotext = shutil.which(args.pdftotext) or args.pdftotext

    with pikepdf.Pdf.open(source) as pdf:
        page_count = len(pdf.pages)
        media_boxes = [
            [float(page.MediaBox[2] - page.MediaBox[0]), float(page.MediaBox[3] - page.MediaBox[1])]
            for page in pdf.pages
        ]
        metadata = {str(key): str(value) for key, value in (pdf.docinfo or {}).items()}
        bbox_pages = parse_bbox(pdftotext_bytes(pdftotext, source, "-bbox"))

        selected = list(range(1, page_count + 1))
        if args.pages:
            selected_set: set[int] = set()
            for token in args.pages.split(","):
                match = re.fullmatch(r"(\d+)(?:-(\d+))?", token.strip())
                if not match:
                    raise ValueError(f"invalid page range: {token!r}")
                start = int(match.group(1))
                end = int(match.group(2) or start)
                if start < 1 or end > page_count or end < start:
                    raise ValueError(f"page range outside document: {token!r}")
                selected_set.update(range(start, end + 1))
            selected = sorted(selected_set)

        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "source": str(source),
            "source_file": source.name,
            "source_sha256": sha256_file(source),
            "source_bytes": source.stat().st_size,
            "page_count": page_count,
            "selected_pages": selected,
            "kind": "xiangshan",
            "render_width": args.render_width,
            "ocr_backend": "checked_native_pdf",
            "ocr_language": "ch",
            "recognition_refinement": "checked_native_pdf",
            "cover_pages": [1],
            "media_boxes": media_boxes,
            "metadata": metadata,
        }
        write_json(output / "manifest.json", manifest)

        for page_number in selected:
            page = pdf.pages[page_number - 1]
            source_width = float(media_boxes[page_number - 1][0])
            source_height = float(media_boxes[page_number - 1][1])
            render_height = int(round(args.render_width * source_height / source_width))
            page_dir = pages_dir / f"p{page_number:04d}"
            page_dir.mkdir(parents=True, exist_ok=True)
            for old in page_dir.glob("art-*.*"):
                old.unlink()
            words_page = bbox_pages[page_number - 1]
            artwork = extract_images(
                page,
                page_dir,
                source_width,
                source_height,
                args.render_width,
                render_height,
            )
            artwork_boxes = [
                [
                    float(box[0]) / (args.render_width / words_page["width"]),
                    float(box[1]) / (render_height / words_page["height"]),
                    float(box[2]) / (args.render_width / words_page["width"]),
                    float(box[3]) / (render_height / words_page["height"]),
                ]
                for item in artwork
                for box in [item["box"]]
            ]
            groups = cluster_rows(
                words_page["words"], words_page["width"], words_page["height"]
            )
            groups = split_groups_over_artwork(groups, artwork_boxes)
            lines = [
                line_record(group, page_number, args.render_width, render_height)
                for group in groups
                if join_words(group).strip()
            ]
            for index, line in enumerate(lines, 1):
                line["id"] = f"p{page_number:04d}-l{index:04d}"
                # Preserve page furniture and any real figure labels; scanner
                # branding is absent from the checked baseline.
                line["artifact"] = False
            record = {
                "schema_version": "1.0",
                "source_sha256": manifest["source_sha256"],
                "page": page_number,
                "render_width": args.render_width,
                "render_height": render_height,
                "recognition_refinement": "checked_native_pdf",
                "source_media_box": media_boxes[page_number - 1],
                "full_page_artwork": bool(
                    len(artwork) == 1
                    and artwork[0]["box"] == [0, 0, args.render_width, render_height]
                    and not lines
                ),
                "lines": lines,
                "artwork": artwork,
                "vector_rules": [],
            }
            write_json(page_dir / "page.json", record)
            print(
                f"page={page_number} lines={len(lines)} artwork={len(artwork)} "
                f"progress={selected.index(page_number)+1}/{len(selected)}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
