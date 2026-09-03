from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pikepdf


def page_content_bytes(page: pikepdf.Page) -> bytes:
    contents = page.obj.get("/Contents")
    if contents is None:
        return b""
    if isinstance(contents, pikepdf.Array):
        return b"\n".join(stream.read_bytes() for stream in contents)
    return contents.read_bytes()


def page_content_hash(page: pikepdf.Page) -> str:
    return hashlib.sha256(page_content_bytes(page)).hexdigest()


def page_box(page: pikepdf.Page, key: str = "/MediaBox") -> tuple[float, ...]:
    value = page.obj.get(key)
    if value is None and key == "/MediaBox":
        value = page.MediaBox
    if value is None:
        return ()
    return tuple(round(float(number), 4) for number in value)


def image_fingerprints(page: pikepdf.Page) -> list[str]:
    fingerprints: list[str] = []
    for image in page.get_images(recursive=True).values():
        try:
            payload = image.read_raw_bytes()
        except (pikepdf.PdfError, AttributeError):
            payload = image.read_bytes()
        attributes = tuple(
            str(image.get(key, ""))
            for key in ("/Width", "/Height", "/ColorSpace", "/BitsPerComponent", "/Filter")
        )
        digest = hashlib.sha256(repr(attributes).encode("utf-8") + b"\0" + payload).hexdigest()
        fingerprints.append(digest)
    return sorted(fingerprints)


def resolve_tool(explicit: str | None, name: str) -> str | None:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"{name} was not found at {path}")
        return str(path)
    return shutil.which(name)


def extract_text_pages(pdf_path: Path, pdftotext: str, mode: str = "-raw") -> list[str]:
    command = [pdftotext]
    if mode:
        command.append(mode)
    command.extend([str(pdf_path), "-"])
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"pdftotext failed ({result.returncode}): {message}")
    pages = result.stdout.decode("utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def parse_page_spec(value: str | None) -> set[int]:
    if not value:
        return set()
    pages: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", token)
        if not match:
            raise ValueError(f"invalid page specification: {token!r}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start < 1 or end < start:
            raise ValueError(f"invalid page range: {token!r}")
        pages.update(range(start, end + 1))
    return pages


def write_json(path: str | None, payload: object) -> None:
    if path:
        import json

        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
