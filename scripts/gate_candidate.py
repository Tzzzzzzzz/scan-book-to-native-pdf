#!/usr/bin/env python3
"""Gate one atomic WikiSkill proposal on complete held-out validation scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import textwrap
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class GateError(ValueError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read valid JSON {path}: {exc}") from exc


def expected_validation_ids(cases_path: Path) -> tuple[set[str], str]:
    raw = cases_path.read_bytes()
    document = load_json(cases_path)
    cases = document.get("cases", []) if isinstance(document, dict) else []
    ids = {case.get("id", "") for case in cases if case.get("split") == "validation"}
    if not ids or "" in ids:
        raise GateError("evaluation definition has no complete validation split")
    return ids, hashlib.sha256(raw).hexdigest().upper()


def validate_proposal(path: Path) -> tuple[dict[str, Any], str, str]:
    raw = path.read_text(encoding="utf-8")
    try:
        proposal = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GateError(f"proposal must be JSON: {exc}") from exc
    action = proposal.get("action")
    name = proposal.get("name")
    if action not in {"create", "patch"}:
        raise GateError("proposal action must be create or patch")
    if not isinstance(name, str) or not name:
        raise GateError("proposal must target exactly one named skill")
    if action == "create":
        if not proposal.get("skill_md") or not proposal.get("purpose_md"):
            raise GateError("create proposal requires full skill_md and purpose_md")
    else:
        edits = proposal.get("edits")
        if not isinstance(edits, list) or not edits:
            raise GateError("patch proposal requires one or more edits")
        for edit in edits:
            if edit.get("op") not in {"append", "replace", "insert_after"}:
                raise GateError("patch edit op must be append, replace, or insert_after")
            if not edit.get("content"):
                raise GateError("every patch edit requires content")
            if edit.get("op") != "append" and not edit.get("target"):
                raise GateError("replace and insert_after edits require a short exact target")
            if len(str(edit.get("target", ""))) > 500:
                raise GateError("patch targets must be short, specific spans (maximum 500 characters)")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
    return proposal, raw, digest


def scorecard(
    path: Path, expected_ids: set[str], expected_eval_hash: str
) -> tuple[dict[str, Any], Decimal]:
    document = load_json(path)
    if not isinstance(document, dict) or document.get("split") != "validation":
        raise GateError(f"scorecard must declare split=validation: {path}")
    revision = str(document.get("skill_revision", ""))
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", revision):
        raise GateError(f"scorecard skill_revision must be a 64-character SHA-256: {path}")
    if str(document.get("eval_definition_sha256", "")).upper() != expected_eval_hash:
        raise GateError(f"scorecard is not bound to the current evaluation definition: {path}")
    run_config = document.get("run_config")
    if not isinstance(run_config, dict) or not run_config:
        raise GateError(f"scorecard lacks a non-empty run_config: {path}")
    case_rows = document.get("cases")
    if not isinstance(case_rows, list):
        raise GateError(f"scorecard cases must be a list: {path}")
    seen: set[str] = set()
    scores: list[Decimal] = []
    for row in case_rows:
        case_id = row.get("id", "")
        if not case_id or case_id in seen:
            raise GateError(f"empty or duplicate scorecard case id: {case_id!r}")
        seen.add(case_id)
        if row.get("status") != "ok":
            raise GateError(f"validation case is incomplete: {case_id} ({row.get('status')})")
        try:
            score = Decimal(str(row.get("score")))
        except (InvalidOperation, TypeError) as exc:
            raise GateError(f"invalid score for {case_id}") from exc
        if score < 0 or score > 1:
            raise GateError(f"score outside [0, 1] for {case_id}: {score}")
        scores.append(score)
    if seen != expected_ids:
        missing = sorted(expected_ids - seen)
        extra = sorted(seen - expected_ids)
        raise GateError(f"scorecard validation ids mismatch; missing={missing}, extra={extra}")
    mean = sum(scores, Decimal(0)) / Decimal(len(scores))
    return document, mean


def append_impact(
    path: Path,
    iteration: str,
    proposal: dict[str, Any],
    proposal_raw: str,
    proposal_hash: str,
    incumbent: dict[str, Any],
    candidate: dict[str, Any],
    incumbent_mean: Decimal,
    candidate_mean: Decimal,
    accepted: bool,
    case_ids: list[str],
    eval_hash: str,
) -> None:
    decision = "accepted" if accepted else "rejected"
    rollback = "not required" if accepted else "restore incumbent skill; retain wiki"
    timestamp = datetime.now(timezone.utc).isoformat()
    block = (
        f"\n## Proposal {iteration} - {timestamp}\n\n"
        f"- Target: `{proposal['name']}`\n"
        f"- Action: `{proposal['action']}`\n"
        f"- Proposal SHA-256: `{proposal_hash}`\n"
        f"- Incumbent revision: `{incumbent['skill_revision']}`\n"
        f"- Candidate revision: `{candidate['skill_revision']}`\n"
        f"- Evaluation definition SHA-256: `{eval_hash}`\n"
        f"- Validation cases: {', '.join(f'`{item}`' for item in case_ids)}\n"
        f"- Incumbent macro mean: `{incumbent_mean}`\n"
        f"- Candidate macro mean: `{candidate_mean}`\n"
        f"- Decision: **{decision}**\n"
        f"- Rollback: {rollback}\n\n"
        "### Full Proposal\n\n"
        f"{textwrap.indent(proposal_raw.rstrip(), '    ')}\n"
    )
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(block)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    skill_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--cases", type=Path, default=skill_root / "evals" / "cases.json")
    parser.add_argument("--incumbent", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--target", default="scan-book-to-native-pdf")
    parser.add_argument("--iteration", required=True, help="iteration identifier, for example 001")
    parser.add_argument("--impact-log", type=Path, help="append the full outcome to this skill-impact.md")
    parser.add_argument("--decision-output", type=Path, help="write a machine-readable decision JSON")
    args = parser.parse_args()

    try:
        expected_ids, eval_hash = expected_validation_ids(args.cases)
        proposal, proposal_raw, proposal_hash = validate_proposal(args.proposal)
        if proposal["name"] != args.target:
            raise GateError(f"proposal targets {proposal['name']!r}, expected {args.target!r}")
        incumbent, incumbent_mean = scorecard(args.incumbent, expected_ids, eval_hash)
        candidate, candidate_mean = scorecard(args.candidate, expected_ids, eval_hash)
        if incumbent["run_config"] != candidate["run_config"]:
            raise GateError("incumbent and candidate run_config objects differ")
        if incumbent["skill_revision"] == candidate["skill_revision"]:
            raise GateError("candidate revision must differ from incumbent revision")
        accepted = candidate_mean > incumbent_mean
        case_ids = sorted(expected_ids)
        result = {
            "valid_comparison": True,
            "iteration": args.iteration,
            "target": proposal["name"],
            "proposal_sha256": proposal_hash,
            "eval_definition_sha256": eval_hash,
            "validation_case_ids": case_ids,
            "incumbent_revision": incumbent["skill_revision"],
            "candidate_revision": candidate["skill_revision"],
            "incumbent_macro_mean": str(incumbent_mean),
            "candidate_macro_mean": str(candidate_mean),
            "delta": str(candidate_mean - incumbent_mean),
            "decision": "accept" if accepted else "reject",
            "rollback_skill": not accepted,
            "retain_wiki": True,
        }
        if args.impact_log:
            append_impact(
                args.impact_log,
                args.iteration,
                proposal,
                proposal_raw,
                proposal_hash,
                incumbent,
                candidate,
                incumbent_mean,
                candidate_mean,
                accepted,
                case_ids,
                eval_hash,
            )
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.decision_output:
            args.decision_output.write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0 if accepted else 2
    except (GateError, OSError) as exc:
        error = {"valid_comparison": False, "error": str(exc)}
        output = json.dumps(error, ensure_ascii=False, indent=2)
        if args.decision_output:
            args.decision_output.write_text(output + "\n", encoding="utf-8")
        print(output, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
