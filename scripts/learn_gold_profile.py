from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import statistics
from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader


SUBSET_RE = re.compile(r"^/?[A-Z]{6}\+")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalized_font(value: str) -> str:
    return SUBSET_RE.sub("", value or "")


def is_cjk(text: str) -> bool:
    return any(
        "\u3400" <= char <= "\u4dbf"
        or "\u4e00" <= char <= "\u9fff"
        or "\uf900" <= char <= "\ufaff"
        for char in text
    )


def color_key(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return json.dumps([round(float(item), 4) for item in value])
    if isinstance(value, (int, float)):
        return json.dumps(round(float(value), 4))
    return repr(value)


def largest_image_dimensions(page: Any) -> tuple[int, int]:
    resources = page.get("/Resources") or {}
    xobjects = resources.get("/XObject") or {}
    dimensions: list[tuple[int, int]] = []
    for reference in xobjects.values():
        obj = reference.get_object()
        if obj.get("/Subtype") == "/Image":
            dimensions.append((int(obj.get("/Width", 0)), int(obj.get("/Height", 0))))
    return max(dimensions, key=lambda item: item[0] * item[1], default=(0, 0))


def top_values(counter: collections.Counter[Any], count: int = 12) -> list[dict[str, object]]:
    return [{"value": value, "characters": total} for value, total in counter.most_common(count)]


def dominant(counter: collections.Counter[Any]) -> Any:
    return counter.most_common(1)[0][0] if counter else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Learn an aggregate publication profile from held-in pages of a source/gold PDF pair."
    )
    parser.add_argument("source_pdf")
    parser.add_argument("gold_pdf")
    parser.add_argument("split_manifest")
    parser.add_argument("--split", default="train")
    parser.add_argument("--profile-name", default="paired-gold-publication-profile")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_path = Path(args.source_pdf).expanduser().resolve(strict=True)
    gold_path = Path(args.gold_pdf).expanduser().resolve(strict=True)
    manifest_path = Path(args.split_manifest).expanduser().resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_sha = file_hash(source_path)
    gold_sha = file_hash(gold_path)
    if source_sha != manifest["source"]["sha256"]:
        raise ValueError("source hash does not match the split manifest")
    if gold_sha != manifest["gold"]["sha256"]:
        raise ValueError("gold hash does not match the split manifest")
    selected = {
        int(row["page"]) for row in manifest["pages"] if row["split"] == args.split
    }
    if not selected:
        raise ValueError(f"split contains no pages: {args.split}")

    role_fonts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    role_sizes: dict[str, collections.Counter[float]] = collections.defaultdict(collections.Counter)
    role_colors: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    page_boxes: collections.Counter[tuple[float, float]] = collections.Counter()
    scale_x: list[float] = []
    scale_y: list[float] = []
    left_margins: list[float] = []
    right_margins: list[float] = []
    top_margins: list[float] = []
    bottom_margins: list[float] = []
    retained_image_pages = 0

    source_reader = PdfReader(str(source_path))
    with pdfplumber.open(gold_path) as gold:
        if len(source_reader.pages) != len(gold.pages):
            raise ValueError("source and gold page counts differ")
        for page_number in sorted(selected):
            page = gold.pages[page_number - 1]
            chars = page.chars
            page_boxes[(round(float(page.width), 3), round(float(page.height), 3))] += 1
            retained_image_pages += bool(page.images)
            if chars:
                left = min(float(char["x0"]) for char in chars)
                right = float(page.width) - max(float(char["x1"]) for char in chars)
                top = min(float(char["top"]) for char in chars)
                bottom = float(page.height) - max(float(char["bottom"]) for char in chars)
                left_margins.append(left)
                right_margins.append(right)
                top_margins.append(top)
                bottom_margins.append(bottom)

            image_width, image_height = largest_image_dimensions(source_reader.pages[page_number - 1])
            if image_width and image_height:
                scale_x.append(float(page.width) / image_width)
                scale_y.append(float(page.height) / image_height)

            for char in chars:
                font = normalized_font(str(char.get("fontname", "")))
                text = str(char.get("text", ""))
                if "consolas" in font.lower() or "mono" in font.lower():
                    role = "code"
                elif is_cjk(text):
                    role = "cjk_body"
                else:
                    role = "latin_body"
                role_fonts[role][font] += 1
                role_sizes[role][round(float(char.get("size", 0.0)), 2)] += 1
                role_colors[role][color_key(char.get("non_stroking_color"))] += 1

    roles: dict[str, object] = {}
    for role in sorted(role_fonts):
        roles[role] = {
            "dominant_font": dominant(role_fonts[role]),
            "dominant_size_pt": dominant(role_sizes[role]),
            "dominant_color": dominant(role_colors[role]),
            "font_distribution": top_values(role_fonts[role]),
            "size_distribution": top_values(role_sizes[role]),
            "color_distribution": top_values(role_colors[role]),
        }

    result = {
        "schema_version": "1.0",
        "profile_name": args.profile_name,
        "conditional_profile": True,
        "content_authority": "source_scan",
        "style_authority": "paired_gold_training_pages",
        "source": {
            "file": source_path.name,
            "sha256": source_sha,
            "pages": len(source_reader.pages),
        },
        "gold": {
            "file": gold_path.name,
            "sha256": gold_sha,
            "pages": len(source_reader.pages),
        },
        "split_manifest_sha256": file_hash(manifest_path),
        "derivation_split": args.split,
        "selected_pages": len(selected),
        "page_geometry": {
            "page_boxes": [
                {"width": box[0], "height": box[1], "pages": count}
                for box, count in page_boxes.most_common()
            ],
            "source_pixel_to_pdf_point_scale": {
                "median_x": round(statistics.median(scale_x), 6),
                "median_y": round(statistics.median(scale_y), 6),
                "min_x": round(min(scale_x), 6),
                "max_x": round(max(scale_x), 6),
                "min_y": round(min(scale_y), 6),
                "max_y": round(max(scale_y), 6),
            },
            "median_text_margins_pt": {
                "left": round(statistics.median(left_margins), 3),
                "right": round(statistics.median(right_margins), 3),
                "top": round(statistics.median(top_margins), 3),
                "bottom": round(statistics.median(bottom_margins), 3),
            },
        },
        "roles": roles,
        "retained_image_pages_in_split": retained_image_pages,
        "rules": [
            "Apply this profile only to the same publication series or after independent style matching.",
            "Never use the gold wording to override source pixels.",
            "Keep code point size fixed; use bounded width fitting or reflow.",
        ],
    }
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"profile={args.profile_name} split={args.split} pages={len(selected)} "
        f"scale={result['page_geometry']['source_pixel_to_pdf_point_scale']}"
    )
    for role, values in roles.items():
        print(
            f"{role}: font={values['dominant_font']} "
            f"size={values['dominant_size_pt']} color={values['dominant_color']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
