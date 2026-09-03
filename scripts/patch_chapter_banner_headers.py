#!/usr/bin/env python3
"""Patch single-digit Xiangshan chapter banners without touching page content.

The checked native baseline occasionally exposes the three glyphs in a
chapter banner ("第", digit, "章") as separate words.  The digit can then be
misclassified as rotated text by the layout adapter.  This small, guarded
transform joins only a top-of-page trio whose boxes are on the same baseline.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(value: object) -> str:
    return "".join(str(value).split())


def box(line: dict[str, Any]) -> tuple[float, float, float, float]:
    return tuple(float(value) for value in line["box"])


def same_band(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> bool:
    _x0, y0, _x1, y1 = first
    _a0, z0, _a1, z1 = second
    return min(y1, z1) - max(y0, z0) >= -18.0


def patch_record(record: dict[str, Any]) -> bool:
    page_height = float(record.get("render_height", 0))
    lines = list(record.get("lines", []))
    for digit_index, digit_line in enumerate(lines):
        digit = compact(digit_line.get("text", ""))
        if digit not in set("123456789"):
            continue
        if digit_line.get("text_orientation") != "clockwise_90":
            continue
        digit_box = box(digit_line)
        if page_height and digit_box[1] > page_height * 0.28:
            continue
        before: tuple[int, dict[str, Any]] | None = None
        after: tuple[int, dict[str, Any]] | None = None
        for index, candidate in enumerate(lines):
            if index == digit_index:
                continue
            text = compact(candidate.get("text", ""))
            candidate_box = box(candidate)
            if not same_band(digit_box, candidate_box):
                continue
            if text == "\u7b2c" and candidate_box[2] <= digit_box[0] + 10:
                if before is None or candidate_box[2] > box(before[1])[2]:
                    before = (index, candidate)
            elif text == "\u7ae0" and candidate_box[0] >= digit_box[2] - 10:
                if after is None or candidate_box[0] < box(after[1])[0]:
                    after = (index, candidate)
        if before is None or after is None:
            continue
        first_index, first_line = before
        last_index, last_line = after
        merged = dict(first_line)
        merged["id"] = first_line.get("id", digit_line.get("id"))
        # Keep the source banner's deliberate character spacing selectable.
        merged["text"] = f"\u7b2c {digit} \u7ae0"
        merged["box"] = [
            min(box(first_line)[0], digit_box[0], box(last_line)[0]),
            min(box(first_line)[1], digit_box[1], box(last_line)[1]),
            max(box(first_line)[2], digit_box[2], box(last_line)[2]),
            max(box(first_line)[3], digit_box[3], box(last_line)[3]),
        ]
        merged["text_orientation"] = None
        merged["style_role"] = "heading"
        remove = {digit_index, first_index, last_index}
        insert_at = min(remove)
        record["lines"] = [
            (merged if index == insert_at else line)
            for index, line in enumerate(lines)
            if index not in remove or index == insert_at
        ]
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_layout")
    parser.add_argument("output_layout")
    args = parser.parse_args()
    source = Path(args.source_layout).expanduser().resolve(strict=True)
    output = Path(args.output_layout).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    shutil.copytree(source, output)
    changed: list[int] = []
    for path in sorted((output / "pages").glob("p*/page.json")):
        record = load(path)
        if patch_record(record):
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(int(record["page"]))
    print(json.dumps({"pages_changed": changed, "count": len(changed)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
