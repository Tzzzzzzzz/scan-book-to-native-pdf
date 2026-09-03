# Evaluation Cases

`cases.json` defines disjoint training, validation, and test scenarios. Training cases summarize observed failure modes. Validation and test cases are held-out variants that must not be copied into runtime instructions as answers.

For each skill revision, run the same inference configuration on every validation case and create a scorecard:

```json
{
  "schema_version": "1.0",
  "skill_revision": "64-character-sha256-from-skill_revision.py",
  "eval_definition_sha256": "sha256-of-evals-cases-json",
  "split": "validation",
  "run_config": {
    "model": "same-model-for-both-revisions",
    "reasoning_effort": "same-effort",
    "evaluator": "same-held-out-rubric"
  },
  "cases": [
    {"id": "val-reference-is-style-only", "score": 1.0, "status": "ok"}
  ]
}
```

Generate each `skill_revision` with `scripts/skill_revision.py` against the exact incumbent or candidate package. Scores must be numeric in `[0, 1]`. Use `status: "infrastructure_error"` for a run failure; the gate will refuse to compare incomplete results. The two scorecards must carry identical, non-empty `run_config` objects and the current evaluation-definition hash. `scripts/gate_candidate.py` accepts a proposal only when the candidate macro mean is strictly greater than the incumbent macro mean over exactly the same complete validation case set.

Iteration 002 adds held-out cases for exhaustive review without an arbitrary page cap, explicit disposition of explainable render/bbox warnings, and documented `mixed_native_and_raster` output when only intentional artwork remains. Its accepted gate compares incumbent revision `E645E793F6942299E10F6EB63739E033001E3AD9DBD6F49783A5950E0D5F6112` with candidate revision `2132DE2DFB4A1158D8E4004B1417F79E5F37CEAE682D1890712B2F068F20CAE3`.
