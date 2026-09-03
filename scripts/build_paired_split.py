from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

import pdfplumber


SUBSET_RE = re.compile(r"^/?[A-Z]{6}\+")


def parse_page_spec(value: str | None) -> set[int]:
    if not value:
        return set()
    pages: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", token)
        if not match:
            raise ValueError(f"invalid page specification: {token!r}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1 or end < start:
            raise ValueError(f"invalid page range: {token!r}")
        pages.update(range(start, end + 1))
    return pages


def write_json(path: str, payload: object) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalized_font(value: str) -> str:
    return SUBSET_RE.sub("", value or "")


def page_category(
    page_number: int,
    characters: int,
    monospace: int,
    images: int,
    max_size: float,
) -> str:
    if not characters:
        return "blank_or_art_only"
    if page_number <= 4:
        return "cover_or_front_art"
    if max_size >= 18 and images:
        return "chapter_open_with_art"
    if max_size >= 18:
        return "chapter_open"
    if images and monospace >= 100:
        return "mixed_code_and_art"
    if images:
        return "mixed_body_and_art"
    if monospace >= 100 and monospace / characters >= 0.6:
        return "dense_code"
    if monospace >= 50:
        return "mixed_body_and_code"
    return "body"


def split_category(
    rows: list[dict[str, object]],
    forced_train: set[int],
    seed: str,
) -> None:
    forced = [row for row in rows if int(row["page"]) in forced_train]
    remaining = [row for row in rows if int(row["page"]) not in forced_train]
    remaining.sort(
        key=lambda row: hashlib.sha256(
            f"{seed}:{row['category']}:{row['page']}".encode("utf-8")
        ).hexdigest()
    )
    total = len(rows)
    if total >= 6:
        target_validation = max(1, round(total * 0.15))
        target_test = max(1, round(total * 0.15))
    elif total >= 3:
        target_validation = 1
        target_test = 1
    else:
        target_validation = 0
        target_test = 0
    target_train = total - target_validation - target_test
    train_slots = max(0, target_train - len(forced))
    for row in forced:
        row["split"] = "train"
    for index, row in enumerate(remaining):
        if index < train_slots:
            row["split"] = "train"
        elif index < train_slots + target_validation:
            row["split"] = "validation"
        else:
            row["split"] = "test"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic stratified train/validation/test splits for a source/gold PDF pair."
    )
    parser.add_argument("source_pdf")
    parser.add_argument("gold_pdf")
    parser.add_argument("--force-train", help="One-based pages already inspected during development.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_path = Path(args.source_pdf).expanduser().resolve(strict=True)
    gold_path = Path(args.gold_pdf).expanduser().resolve(strict=True)
    source_sha = file_hash(source_path)
    gold_sha = file_hash(gold_path)
    forced_train = parse_page_spec(args.force_train)
    rows: list[dict[str, object]] = []

    with pdfplumber.open(source_path) as source, pdfplumber.open(gold_path) as gold:
        if len(source.pages) != len(gold.pages):
            raise ValueError(
                f"paired PDFs have different page counts: {len(source.pages)} != {len(gold.pages)}"
            )
        for page_number, page in enumerate(gold.pages, 1):
            chars = page.chars
            character_count = len(chars)
            monospace = sum(
                "consolas" in normalized_font(str(char.get("fontname", ""))).lower()
                or "mono" in normalized_font(str(char.get("fontname", ""))).lower()
                for char in chars
            )
            images = len(page.images)
            max_size = max((float(char.get("size", 0.0)) for char in chars), default=0.0)
            category = page_category(
                page_number, character_count, monospace, images, max_size
            )
            rows.append(
                {
                    "page": page_number,
                    "category": category,
                    "characters": character_count,
                    "monospace_characters": monospace,
                    "images": images,
                    "max_text_size": round(max_size, 2),
                    "gold_page_box": [round(float(page.width), 3), round(float(page.height), 3)],
                }
            )

    for page in forced_train:
        if page < 1 or page > len(rows):
            raise ValueError(f"forced training page is outside the pair: {page}")

    grouped: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for row in rows:
        grouped[str(row["category"])].append(row)
    seed = hashlib.sha256(f"{source_sha}:{gold_sha}".encode("ascii")).hexdigest()
    for category_rows in grouped.values():
        split_category(category_rows, forced_train, seed)

    split_counts = collections.Counter(str(row["split"]) for row in rows)
    category_counts = collections.Counter(str(row["category"]) for row in rows)
    category_split_counts: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    for row in rows:
        category_split_counts[str(row["category"])][str(row["split"])] += 1

    result = {
        "schema_version": "1.0",
        "source": {
            "file": source_path.name,
            "sha256": source_sha,
            "pages": len(rows),
        },
        "gold": {
            "file": gold_path.name,
            "sha256": gold_sha,
            "pages": len(rows),
        },
        "seed": seed,
        "forced_training_pages": sorted(forced_train),
        "split_counts": dict(sorted(split_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "category_split_counts": {
            category: dict(sorted(counts.items()))
            for category, counts in sorted(category_split_counts.items())
        },
        "pages": rows,
    }
    write_json(args.output, result)
    print(f"pages={len(rows)} split_counts={dict(sorted(split_counts.items()))}")
    print(f"categories={dict(sorted(category_counts.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
