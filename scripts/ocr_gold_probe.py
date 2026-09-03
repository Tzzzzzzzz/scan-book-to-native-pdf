from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any


PUNCTUATION = set("{}()[]_$%&+*/=<>!:;.,\\\"'|-~?#@")


def parse_page_spec(value: str) -> list[int]:
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
    return sorted(pages)


def levenshtein(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for index, left_char in enumerate(left, 1):
        current = [index]
        for offset, right_char in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[offset] + 1,
                    previous[offset - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def normalized_text(value: str) -> str:
    return "".join(value.split())


def punctuation_text(value: str) -> str:
    return "".join(char for char in value if char in PUNCTUATION)


def character_error_rate(expected: str, actual: str) -> tuple[int, float]:
    distance = levenshtein(expected, actual)
    return distance, distance / max(1, len(expected))


def extract_gold_pages(gold_pdf: Path, pdftotext: str) -> list[str]:
    result = subprocess.run(
        [pdftotext, "-raw", str(gold_pdf), "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    pages = result.stdout.decode("utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


class OcrRunner:
    def __init__(self, backend: str) -> None:
        self.requested_backend = backend
        self.paddle: Any = None
        self.rapid: Any = None
        self.initialization_errors: list[str] = []
        if backend in {"auto", "paddle"}:
            try:
                os.environ.setdefault("FLAGS_use_mkldnn", "0")
                from paddleocr import PaddleOCR

                self.paddle = PaddleOCR(
                    lang="ch",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False,
                )
            except Exception as exc:  # Backend availability is environment-specific.
                self.initialization_errors.append(f"paddle initialization: {type(exc).__name__}: {exc}")
                if backend == "paddle":
                    raise
        if backend == "rapid" or (backend == "auto" and self.paddle is None):
            self._ensure_rapid()

    def _ensure_rapid(self) -> None:
        if self.rapid is not None:
            return
        from rapidocr_onnxruntime import RapidOCR

        self.rapid = RapidOCR()

    def _run_paddle(self, image_path: Path) -> tuple[list[str], list[float]]:
        results = self.paddle.predict(str(image_path))
        payload = results[0].json
        values = payload.get("res", payload)
        return list(values.get("rec_texts", [])), [float(item) for item in values.get("rec_scores", [])]

    def _run_rapid(self, image_path: Path) -> tuple[list[str], list[float]]:
        self._ensure_rapid()
        result, _elapsed = self.rapid(str(image_path))
        rows = result or []
        return [str(row[1]) for row in rows], [float(row[2]) for row in rows]

    def run(self, image_path: Path) -> tuple[str, list[str], list[float], list[str]]:
        errors = list(self.initialization_errors)
        if self.paddle is not None:
            try:
                texts, scores = self._run_paddle(image_path)
                return "paddle", texts, scores, errors
            except Exception as exc:  # Fallback is an explicit part of the probe.
                errors.append(f"paddle inference: {type(exc).__name__}: {exc}")
                if self.requested_backend == "paddle":
                    raise
        texts, scores = self._run_rapid(image_path)
        return "rapid", texts, scores, errors


def render_page(
    source_pdf: Path,
    page: int,
    pdftoppm: str,
    output_prefix: Path,
    scale_to_x: int,
) -> Path:
    result = subprocess.run(
        [
            pdftoppm,
            "-f",
            str(page),
            "-l",
            str(page),
            "-png",
            "-singlefile",
            "-scale-to-x",
            str(scale_to_x),
            "-scale-to-y",
            "-1",
            str(source_pdf),
            str(output_prefix),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    output_path = output_prefix.with_suffix(".png")
    if not output_path.is_file():
        raise FileNotFoundError(f"render was not created: {output_path}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe OCR against held-out pages of a paired source/gold PDF."
    )
    parser.add_argument("source_pdf")
    parser.add_argument("gold_pdf")
    parser.add_argument("--pages", required=True)
    parser.add_argument("--backend", choices=("auto", "paddle", "rapid"), default="auto")
    parser.add_argument("--pdftoppm", help="Path to Poppler pdftoppm.")
    parser.add_argument("--pdftotext", help="Path to Poppler pdftotext.")
    parser.add_argument("--scale-to-x", type=int, default=1000)
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--max-semantic-cer", type=float)
    parser.add_argument("--max-punctuation-cer", type=float)
    parser.add_argument("--output")
    args = parser.parse_args()

    source_path = Path(args.source_pdf).expanduser().resolve(strict=True)
    gold_path = Path(args.gold_pdf).expanduser().resolve(strict=True)
    pages = parse_page_spec(args.pages)
    pdftoppm = args.pdftoppm or shutil.which("pdftoppm")
    pdftotext = args.pdftotext or shutil.which("pdftotext")
    if not pdftoppm or not pdftotext:
        raise FileNotFoundError("pdftoppm and pdftotext are required")
    gold_pages = extract_gold_pages(gold_path, pdftotext)
    if any(page > len(gold_pages) for page in pages):
        raise ValueError("requested page is outside the gold PDF")

    runner = OcrRunner(args.backend)
    reports: list[dict[str, object]] = []
    total_semantic_distance = 0
    total_semantic_characters = 0
    total_punctuation_distance = 0
    total_punctuation_characters = 0
    with tempfile.TemporaryDirectory(prefix="ocr-gold-probe-") as directory:
        temp_dir = Path(directory)
        for page in pages:
            image_path = render_page(
                source_path,
                page,
                pdftoppm,
                temp_dir / f"page-{page:04d}",
                args.scale_to_x,
            )
            backend, lines, scores, backend_errors = runner.run(image_path)
            actual = "\n".join(lines)
            expected = gold_pages[page - 1]
            expected_semantic = normalized_text(expected)
            actual_semantic = normalized_text(actual)
            semantic_distance, semantic_cer = character_error_rate(
                expected_semantic, actual_semantic
            )
            expected_punctuation = punctuation_text(expected)
            actual_punctuation = punctuation_text(actual)
            punctuation_distance, punctuation_cer = character_error_rate(
                expected_punctuation, actual_punctuation
            )
            total_semantic_distance += semantic_distance
            total_semantic_characters += len(expected_semantic)
            total_punctuation_distance += punctuation_distance
            total_punctuation_characters += len(expected_punctuation)
            row: dict[str, object] = {
                "page": page,
                "backend": backend,
                "lines": len(lines),
                "mean_confidence": round(statistics.mean(scores), 6) if scores else None,
                "semantic_characters": len(expected_semantic),
                "semantic_distance": semantic_distance,
                "semantic_cer": round(semantic_cer, 6),
                "punctuation_characters": len(expected_punctuation),
                "punctuation_distance": punctuation_distance,
                "punctuation_cer": round(punctuation_cer, 6),
                "backend_errors": backend_errors,
            }
            if args.include_text:
                row["expected_text"] = expected
                row["ocr_text"] = actual
            reports.append(row)
            print(
                f"page={page} backend={backend} semantic_cer={semantic_cer:.6f} "
                f"punctuation_cer={punctuation_cer:.6f}"
            )

    aggregate_semantic = total_semantic_distance / max(1, total_semantic_characters)
    aggregate_punctuation = total_punctuation_distance / max(1, total_punctuation_characters)
    result = {
        "schema_version": "1.0",
        "source": source_path.name,
        "gold": gold_path.name,
        "requested_backend": args.backend,
        "pages": pages,
        "aggregate_semantic_cer": round(aggregate_semantic, 6),
        "aggregate_punctuation_cer": round(aggregate_punctuation, 6),
        "details": reports,
    }
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        f"aggregate_semantic_cer={aggregate_semantic:.6f} "
        f"aggregate_punctuation_cer={aggregate_punctuation:.6f}"
    )
    if args.max_semantic_cer is not None and aggregate_semantic > args.max_semantic_cer:
        return 2
    if args.max_punctuation_cer is not None and aggregate_punctuation > args.max_punctuation_cer:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
