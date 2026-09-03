#!/usr/bin/env python3
"""Validate this installable skill's WikiSkill layers and provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_SKILL_HEADINGS = (
    "## When to Apply",
    "## When Not to Apply",
    "## Instructions",
)
REQUIRED_PURPOSE_HEADINGS = (
    "## Origin",
    "## Patterns Addressed",
    "## Evolution History",
)
REQUIRED_PATTERN_FIELDS = ("Type", "Status", "Confidence", "Evidence")
REQUIRED_ROOT_FILES = (
    "SKILL.md",
    "PURPOSE.md",
    "wikiskill.json",
    "wiki/index.md",
    "wiki/logs.md",
    "wiki/skill-impact.md",
    "evals/cases.json",
    "scripts/gate_candidate.py",
    "scripts/skill_revision.py",
)


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read valid JSON {path}: {exc}")
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_skill_frontmatter(text: str, errors: list[str]) -> dict[str, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        errors.append("SKILL.md has no YAML frontmatter")
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def validate_root(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_ROOT_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if errors:
        return errors

    package = load_json(root / "wikiskill.json", errors)
    if isinstance(package, dict):
        if package.get("method") != "WikiSkill":
            errors.append("wikiskill.json method must be WikiSkill")
        mapping = package.get("package_mapping", {})
        expected_mapping = {
            "raw_layer": "raw",
            "wiki_layer": "wiki",
            "skills_layer": ".",
            "active_skill": "scan-book-to-native-pdf",
        }
        if mapping != expected_mapping:
            errors.append("wikiskill.json package_mapping is not the supported installable-skill mapping")
        inference_paths = package.get("access_policy", {}).get("inference", [])
        if any(str(item).startswith(("raw", "wiki")) for item in inference_paths):
            errors.append("inference access policy must exclude raw/ and wiki/")
        gating = package.get("gating", {})
        if gating.get("acceptance_rule") != "candidate_macro_mean > incumbent_macro_mean":
            errors.append("gating must require strict candidate improvement")
        if gating.get("rollback_skill_on_rejection") is not True:
            errors.append("gating must roll back rejected skill changes")
        if gating.get("retain_wiki_on_rejection") is not True:
            errors.append("gating must retain wiki state after rejection")

    skill_path = root / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    frontmatter = parse_skill_frontmatter(skill_text, errors)
    if frontmatter.get("name") != "scan-book-to-native-pdf":
        errors.append("SKILL.md name does not match the installed skill")
    if not frontmatter.get("description"):
        errors.append("SKILL.md description is empty")
    for heading in REQUIRED_SKILL_HEADINGS:
        if heading not in skill_text:
            errors.append(f"SKILL.md missing heading: {heading}")
    if skill_path.stat().st_size > 7000:
        errors.append("SKILL.md exceeds the 7000-byte runtime budget")
    if re.search(r"(?:read|load|consult).*?(?:raw/|wiki/)", skill_text, re.IGNORECASE | re.DOTALL):
        errors.append("runtime skill must not instruct the inference agent to read raw/ or wiki/")

    purpose_text = (root / "PURPOSE.md").read_text(encoding="utf-8")
    for heading in REQUIRED_PURPOSE_HEADINGS:
        if heading not in purpose_text:
            errors.append(f"PURPOSE.md missing heading: {heading}")

    pattern_dir = root / "wiki" / "patterns"
    patterns = sorted(pattern_dir.glob("*.md")) if pattern_dir.is_dir() else []
    if not patterns:
        errors.append("wiki/patterns contains no pattern pages")
    index_text = (root / "wiki" / "index.md").read_text(encoding="utf-8")
    pattern_ids: set[str] = set()
    for pattern_path in patterns:
        text = pattern_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not 10 <= len(lines) <= 30:
            errors.append(f"pattern should contain 10-30 lines: {pattern_path.name} ({len(lines)})")
        id_match = re.match(r"# (P-\d{3})\b", text)
        if not id_match:
            errors.append(f"pattern lacks a stable P-NNN heading: {pattern_path.name}")
        else:
            pattern_id = id_match.group(1)
            if pattern_id in pattern_ids:
                errors.append(f"duplicate pattern id: {pattern_id}")
            pattern_ids.add(pattern_id)
        for field in REQUIRED_PATTERN_FIELDS:
            if not re.search(rf"^- {field}:\s*\S", text, re.MULTILINE):
                errors.append(f"pattern missing {field}: {pattern_path.name}")
        evidence_paths = re.findall(r"`(raw/[^`#]+)(?:#[^`]*)?`", text)
        if not evidence_paths:
            errors.append(f"pattern has no raw evidence path: {pattern_path.name}")
        for relative in evidence_paths:
            if not (root / relative).is_file():
                errors.append(f"pattern evidence does not exist: {pattern_path.name} -> {relative}")
        index_target = f"wiki/patterns/{pattern_path.name}"
        if index_target not in index_text:
            errors.append(f"pattern missing from wiki/index.md: {pattern_path.name}")

    purpose_ids = set(re.findall(r"\bP-\d{3}\b", purpose_text))
    missing_purpose = sorted(pattern_ids - purpose_ids)
    if missing_purpose:
        errors.append(f"PURPOSE.md does not map pattern ids: {', '.join(missing_purpose)}")

    iteration_dirs = sorted((root / "raw").glob("iteration-[0-9][0-9][0-9]"))
    if not iteration_dirs:
        errors.append("raw layer contains no iteration directories")
    for iteration_dir in iteration_dirs:
        manifest_path = iteration_dir / "manifest.json"
        if not manifest_path.is_file():
            errors.append(f"raw iteration lacks manifest: {iteration_dir.name}")
            continue
        manifest = load_json(manifest_path, errors)
        if not isinstance(manifest, dict):
            continue
        if manifest.get("immutable") is not True:
            errors.append(f"raw iteration is not marked immutable: {iteration_dir.name}")
        if manifest.get("trace_policy") != "observable_actions_and_outputs_only":
            errors.append(f"unsupported raw trace policy: {iteration_dir.name}")
        expected_iteration = int(iteration_dir.name.rsplit("-", 1)[1])
        if manifest.get("iteration") != expected_iteration:
            errors.append(f"raw iteration number does not match its directory: {iteration_dir.name}")
        declared_files: set[Path] = set()
        for entry in manifest.get("files", []):
            relative = entry.get("path", "")
            expected_hash = str(entry.get("sha256", "")).upper()
            trace_path = (root / relative).resolve()
            try:
                trace_path.relative_to(iteration_dir.resolve())
            except ValueError:
                errors.append(f"manifest path escapes its raw iteration: {relative}")
                continue
            declared_files.add(trace_path)
            if not trace_path.is_file():
                errors.append(f"manifest trace missing: {relative}")
            elif sha256_file(trace_path) != expected_hash:
                errors.append(f"immutable raw trace hash mismatch: {relative}")
        actual_files = {
            path.resolve()
            for path in iteration_dir.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        }
        if actual_files != declared_files:
            undeclared = sorted(str(path.relative_to(root)) for path in actual_files - declared_files)
            absent = sorted(str(path.relative_to(root)) for path in declared_files - actual_files)
            errors.append(
                f"raw manifest inventory mismatch in {iteration_dir.name}; "
                f"undeclared={undeclared}, absent={absent}"
            )

    cases_doc = load_json(root / "evals" / "cases.json", errors)
    if isinstance(cases_doc, dict):
        cases = cases_doc.get("cases", [])
        seen_ids: set[str] = set()
        splits: set[str] = set()
        for case in cases:
            case_id = case.get("id", "")
            split = case.get("split", "")
            if not case_id or case_id in seen_ids:
                errors.append(f"evaluation case id is empty or duplicated: {case_id!r}")
            seen_ids.add(case_id)
            splits.add(split)
            if not case.get("required_behaviors") or not case.get("forbidden_behaviors"):
                errors.append(f"evaluation case lacks behavioral rubric: {case_id}")
        if splits != {"train", "validation", "test"}:
            errors.append(f"evaluation splits must be train/validation/test, got: {sorted(splits)}")

    cache_dirs = [path for path in root.rglob("__pycache__") if path.is_dir()]
    if cache_dirs:
        errors.append("generated __pycache__ directories must not remain in the installed skill")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="skill root (default: parent of scripts/)",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate_root(root)
    report = {"root": str(root), "valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif errors:
        print("WikiSkill validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"WikiSkill validation passed: {root}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
