from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
from PIL import Image

from _pdf_utils import write_json


PAGE_RE = re.compile(r"(\d+)(?=\.[^.]+$)")


def index_images(directory: Path) -> dict[int, Path]:
    indexed: dict[int, Path] = {}
    for path in directory.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            continue
        match = PAGE_RE.search(path.name)
        if not match:
            continue
        page = int(match.group(1))
        if page in indexed:
            raise ValueError(f"duplicate page number {page} in {directory}")
        indexed[page] = path
    return indexed


def groups(rows: np.ndarray, max_gap: int) -> list[tuple[int, int]]:
    if not len(rows):
        return []
    result: list[tuple[int, int]] = []
    start = previous = int(rows[0])
    for raw in rows[1:]:
        current = int(raw)
        if current - previous > max_gap + 1:
            result.append((start, previous + 1))
            start = current
        previous = current
    result.append((start, previous + 1))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Find possible missing ink bands in full-page render sets.")
    parser.add_argument("source_dir")
    parser.add_argument("candidate_dir")
    parser.add_argument("--threshold", type=int, default=225)
    parser.add_argument("--min-source-row-ink", type=int, default=8)
    parser.add_argument("--min-band-ink", type=int, default=40)
    parser.add_argument("--candidate-ratio", type=float, default=0.05)
    parser.add_argument("--y-tolerance", type=int, default=4)
    parser.add_argument("--x-tolerance", type=int, default=4)
    parser.add_argument("--max-row-gap", type=int, default=1)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve(strict=True)
    candidate_dir = Path(args.candidate_dir).expanduser().resolve(strict=True)
    source = index_images(source_dir)
    candidate = index_images(candidate_dir)
    missing_files = sorted(set(source) - set(candidate))
    extra_files = sorted(set(candidate) - set(source))
    findings: list[dict[str, object]] = []
    dimension_mismatches: list[dict[str, object]] = []

    for page in sorted(set(source) & set(candidate)):
        source_gray = np.asarray(Image.open(source[page]).convert("L"))
        candidate_gray = np.asarray(Image.open(candidate[page]).convert("L"))
        if source_gray.shape != candidate_gray.shape:
            dimension_mismatches.append(
                {"page": page, "source": source_gray.shape, "candidate": candidate_gray.shape}
            )
            continue
        source_ink = source_gray < args.threshold
        candidate_ink = candidate_gray < args.threshold
        row_counts = source_ink.sum(axis=1)
        active_rows = np.flatnonzero(row_counts >= args.min_source_row_ink)
        for y0, y1 in groups(active_rows, args.max_row_gap):
            ys, xs = np.nonzero(source_ink[y0:y1])
            if not len(xs):
                continue
            x0 = int(xs.min())
            x1 = int(xs.max()) + 1
            source_count = int(source_ink[y0:y1, x0:x1].sum())
            if source_count < args.min_band_ink:
                continue
            cy0 = max(0, y0 - args.y_tolerance)
            cy1 = min(candidate_ink.shape[0], y1 + args.y_tolerance)
            cx0 = max(0, x0 - args.x_tolerance)
            cx1 = min(candidate_ink.shape[1], x1 + args.x_tolerance)
            candidate_count = int(candidate_ink[cy0:cy1, cx0:cx1].sum())
            ratio = candidate_count / max(source_count, 1)
            if ratio < args.candidate_ratio:
                findings.append(
                    {
                        "page": page,
                        "source_file": source[page].name,
                        "candidate_file": candidate[page].name,
                        "box": [x0, y0, x1, y1],
                        "source_ink": source_count,
                        "candidate_ink": candidate_count,
                        "ratio": ratio,
                    }
                )

    report = {
        "source_dir": str(source_dir),
        "candidate_dir": str(candidate_dir),
        "source_pages": len(source),
        "candidate_pages": len(candidate),
        "missing_candidate_pages": missing_files,
        "extra_candidate_pages": extra_files,
        "dimension_mismatches": dimension_mismatches,
        "possible_missing_bands": findings,
    }
    write_json(args.output, report)
    print(f"pages={len(source)}/{len(candidate)}")
    print(f"missing_candidate_pages={missing_files}")
    print(f"extra_candidate_pages={extra_files}")
    print(f"dimension_mismatches={len(dimension_mismatches)}")
    print(f"possible_missing_bands={len(findings)}")
    failed = bool(missing_files or extra_files or dimension_mismatches or findings)
    return 0 if args.report_only or not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
