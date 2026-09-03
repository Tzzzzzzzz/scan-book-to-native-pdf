from __future__ import annotations

import argparse
from pathlib import Path

import pikepdf

from _pdf_utils import write_json


def font_descriptor(font: pikepdf.Object) -> pikepdf.Object | None:
    descriptor = font.get("/FontDescriptor")
    if descriptor is not None:
        return descriptor
    descendants = font.get("/DescendantFonts")
    if descendants:
        return descendants[0].get("/FontDescriptor")
    return None


def font_key(font: pikepdf.Object) -> str:
    try:
        return f"{font.objgen[0]}:{font.objgen[1]}"
    except (AttributeError, TypeError):
        return repr(font)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit embedded fonts and ToUnicode maps.")
    parser.add_argument("pdf")
    parser.add_argument("--require-embedded", action="store_true")
    parser.add_argument("--require-tounicode", action="store_true")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve(strict=True)
    pdf = pikepdf.Pdf.open(pdf_path)
    records: dict[str, dict[str, object]] = {}

    for page_number, page in enumerate(pdf.pages, 1):
        resources = page.obj.get("/Resources")
        if resources is None:
            try:
                resources = page.Resources
            except AttributeError:
                continue
        for resource_name, font in resources.get("/Font", {}).items():
            key = font_key(font)
            descriptor = font_descriptor(font)
            subtype = str(font.get("/Subtype", ""))
            embedded = subtype == "/Type3" or bool(
                descriptor
                and any(descriptor.get(name) is not None for name in ("/FontFile", "/FontFile2", "/FontFile3"))
            )
            record = records.setdefault(
                key,
                {
                    "object": key,
                    "base_font": str(font.get("/BaseFont", "")),
                    "subtype": subtype,
                    "embedded": embedded,
                    "to_unicode": font.get("/ToUnicode") is not None,
                    "resources": set(),
                    "pages": set(),
                },
            )
            record["resources"].add(str(resource_name))
            record["pages"].add(page_number)

    fonts: list[dict[str, object]] = []
    for record in records.values():
        record["resources"] = sorted(record["resources"])
        record["pages"] = sorted(record["pages"])
        fonts.append(record)
    fonts.sort(key=lambda item: (str(item["base_font"]), str(item["object"])))

    missing_embedded = [font["object"] for font in fonts if not font["embedded"]]
    missing_unicode = [font["object"] for font in fonts if not font["to_unicode"]]
    report = {
        "path": str(pdf_path),
        "font_count": len(fonts),
        "missing_embedded": missing_embedded,
        "missing_tounicode": missing_unicode,
        "fonts": fonts,
    }
    write_json(args.output, report)

    print(f"fonts={len(fonts)}")
    print(f"missing_embedded={len(missing_embedded)} {missing_embedded}")
    print(f"missing_tounicode={len(missing_unicode)} {missing_unicode}")
    failed = (args.require_embedded and bool(missing_embedded)) or (
        args.require_tounicode and bool(missing_unicode)
    )
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
