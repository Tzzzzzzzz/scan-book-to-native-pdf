from __future__ import annotations

import argparse
from pathlib import Path

import pikepdf

from _pdf_utils import page_box, page_content_hash


PAGE_BOX_KEYS = ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replace one page's rendering content/resources in a checked PDF baseline."
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--page", type=int, required=True, help="One-based target page in the base PDF.")
    parser.add_argument("--patch-page", type=int, default=1, help="One-based page in the patch PDF.")
    parser.add_argument("--allow-page-box-change", action="store_true")
    args = parser.parse_args()

    base_path = Path(args.base).expanduser().resolve(strict=True)
    patch_path = Path(args.patch).expanduser().resolve(strict=True)
    output_path = Path(args.output).expanduser().resolve()
    if output_path in {base_path, patch_path}:
        raise ValueError("output must not overwrite the base or patch PDF")

    base = pikepdf.Pdf.open(base_path)
    patch = pikepdf.Pdf.open(patch_path)
    if not 1 <= args.page <= len(base.pages):
        raise IndexError(f"target page {args.page} is outside 1..{len(base.pages)}")
    if not 1 <= args.patch_page <= len(patch.pages):
        raise IndexError(f"patch page {args.patch_page} is outside 1..{len(patch.pages)}")

    target_index = args.page - 1
    target = base.pages[target_index]
    source = patch.pages[args.patch_page - 1]
    if not args.allow_page_box_change and page_box(target) != page_box(source):
        raise ValueError(
            f"MediaBox mismatch: target={page_box(target)} patch={page_box(source)}; "
            "pass --allow-page-box-change only when intentional"
        )

    untouched_hashes = {
        index: page_content_hash(page)
        for index, page in enumerate(base.pages)
        if index != target_index
    }
    source_hash = page_content_hash(source)
    # Importing the page first gives direct dictionaries (notably /Resources)
    # the same owner as the base PDF on every supported pikepdf version.
    base.pages.append(source)
    imported = base.pages[-1]
    source_contents = imported.obj.get("/Contents")
    source_resources = imported.obj.get("/Resources")
    if source_contents is None or source_resources is None:
        raise ValueError("patch page must have explicit Contents and Resources")

    target.obj["/Contents"] = source_contents
    target.obj["/Resources"] = source_resources
    if args.allow_page_box_change:
        for key in PAGE_BOX_KEYS:
            value = imported.obj.get(key)
            if value is None:
                target.obj.pop(key, None)
            else:
                target.obj[key] = pikepdf.Array([float(number) for number in value])
        if imported.obj.get("/Rotate") is None:
            target.obj.pop("/Rotate", None)
        else:
            target.obj["/Rotate"] = int(imported.obj.get("/Rotate"))
    del base.pages[-1]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(output_path)
    checked = pikepdf.Pdf.open(output_path)
    if len(checked.pages) != len(base.pages):
        raise RuntimeError("page count changed during page replacement")
    changed_elsewhere = [
        index + 1
        for index, digest in untouched_hashes.items()
        if page_content_hash(checked.pages[index]) != digest
    ]
    if changed_elsewhere:
        raise RuntimeError(f"untouched page content changed: {changed_elsewhere}")
    if page_content_hash(checked.pages[target_index]) != source_hash:
        raise RuntimeError("replacement page content does not match the patch page")

    print(f"output={output_path}")
    print(f"pages={len(checked.pages)} replaced_page={args.page} patch_page={args.patch_page}")
    print("untouched_page_content_changes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
