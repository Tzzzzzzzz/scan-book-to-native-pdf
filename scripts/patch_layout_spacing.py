#!/usr/bin/env python3
"""Restore source-visible identifier spacing in the derived Vol. 1 layout."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    layout = Path(__import__("sys").argv[1]).expanduser().resolve(strict=True)
    path = layout / "pages" / "p0008" / "page.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    replacements = {
        "TileLink\u3002": "TileLink \u3002",
        "TL-C\u3002": "TL-C \u3002",
    }
    changed = 0
    for line in record.get("lines", []):
        text = str(line.get("text", ""))
        for before, after in replacements.items():
            if before in text:
                text = text.replace(before, after)
                changed += 1
        line["text"] = text
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"page": 8, "replacements": changed}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
