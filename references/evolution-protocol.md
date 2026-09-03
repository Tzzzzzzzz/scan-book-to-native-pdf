# WikiSkill Evolution Protocol

This package adapts the three-layer WikiSkill method to an installable Codex skill. The skill root is the active Skills Layer; `raw/` and `wiki/` are sibling layers inside the package so global skill discovery still finds root `SKILL.md`.

## Iteration Loop

1. **Inference rollout:** Execute training tasks with the active `SKILL.md` and its runtime resources. Do not expose `raw/` or `wiki/` to the inference agent.
2. **Wiki maintenance:** Append immutable observable traces under a new `raw/iteration-NNN/`. Compare passes and failures, perform root-cause analysis, patch existing pattern pages or add non-duplicate patterns, update `wiki/index.md`, and append `wiki/logs.md`.
3. **Skill proposal:** Give the proposer `wiki/index.md`, `wiki/skill-impact.md`, concise task outcomes, and on-demand access to relevant patterns/raw traces. Produce one atomic create/patch/no-action proposal targeting this skill. Update `PURPOSE.md` when an accepted change gains a new motivating pattern.
4. **Validation gate:** Evaluate incumbent and candidate independently on exactly the held-out validation cases. Accept only a strict macro-mean improvement. Otherwise restore the incumbent skill. In both cases append the proposal, diff, scores, decision, and rollback status to `wiki/skill-impact.md`; never roll back the Wiki.

## Pattern Rules

- One generalizable pattern per file, normally 10-30 lines.
- Include description, root cause, concrete action, status, confidence, and raw evidence.
- Capture both successful and failed strategies.
- Patch an existing pattern when new evidence refines it; do not create duplicates.
- Write each index entry as problem + root cause + fix so a proposer can decide whether to open the page.

## Evaluation Discipline

Training, validation, and test IDs in `evals/cases.json` are disjoint. Do not tune against test outcomes. A static structure check is not a task-performance score. Scorecards supplied to `scripts/gate_candidate.py` must come from comparable inference runs, use every validation case exactly once, and disclose infrastructure failures rather than converting them into arbitrary task scores.

## Source

Method adapted from Google Research's "WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution" (arXiv:2608.27454, 2026).
