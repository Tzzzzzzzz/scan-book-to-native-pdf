# Skill Impact

## Bootstrap S0 - 2026-08-31

- Target: `scan-book-to-native-pdf`
- Source iteration: `raw/iteration-000/`
- Action: create the initial WikiSkill active skill and provenance map
- Active runtime revision: `5B706786C9E19B2855FE89453C0DCACB027124518EAC7276315057331AFA008D`
- Validation decision: bootstrap, not comparable to an incumbent
- Result: active
- Rationale: WikiSkill requires an initial skill state before strict validation gating can evaluate later atomic proposals.

Future entries must include proposal identity, target skill, exact patch or full content, incumbent score, candidate score, validation case IDs, acceptance/rejection, and rollback status. Rejected entries remain here so later proposers do not repeat them.

## Proposal 001 - 2026-08-31T16:16:49.366288+00:00

- Target: `scan-book-to-native-pdf`
- Action: `patch`
- Proposal SHA-256: `C0C2E53A2448341AACF8694B96A3DE05A5D89BCDD16B4DC352075844735ABC48`
- Incumbent revision: `5B706786C9E19B2855FE89453C0DCACB027124518EAC7276315057331AFA008D`
- Candidate revision: `22562C6A40D914895851A3FD696BB9C9A86CA7E7E05251222F90D5083006E12A`
- Evaluation definition SHA-256: `4C68C65406C9C52AF090633B837777570041BC286FE691CE5ECD98E39CC1DF9F`
- Validation cases: `val-cleanup-after-delivery`, `val-four-corpus-nativity`, `val-local-fix-changes-page-box`, `val-long-code-line-consistency`, `val-mixed-diagram-label-cleaning`, `val-ocr-punctuation-is-not-publishable`, `val-paired-profile-heldout`, `val-per-page-pixel-geometry`, `val-reference-is-style-only`
- Incumbent macro mean: `0.6944444444444444444444444444`
- Candidate macro mean: `1.0`
- Decision: **accepted**
- Rollback: not required

### Full Proposal

    {
      "action": "patch",
      "name": "scan-book-to-native-pdf",
      "edits": [
        {
          "op": "insert_after",
          "target": "Read references/workflow.md before the first reconstruction.",
          "content": "Route paired source/gold training through a frozen category-stratified split; learn aggregate style and geometry from training pages only; validate independently; reserve test pages until all choices are frozen. Keep source pixels as semantic authority and prohibit gold wording leakage."
        },
        {
          "op": "append",
          "content": "Add repeat-aware PDF nativity classification, a paired split builder, aggregate gold-profile learner, OCR backend probe/fallback, the conditional Xiangshan v239 profile, and QA gates for sparse overlays, per-page pixel geometry, and non-publishable raw OCR. Preserve every incumbent reconstruction, incremental correction, exhaustive review, and cleanup behavior."
        }
      ]
    }

## Proposal 002 - 2026-09-03T01:55:13.908094+00:00

- Target: `scan-book-to-native-pdf`
- Action: `patch`
- Proposal SHA-256: `292B73C47849F7E60C39E7B08341CE87D0A23A602EDDC458143AC9B9F7DE39F2`
- Incumbent revision: `E645E793F6942299E10F6EB63739E033001E3AD9DBD6F49783A5950E0D5F6112`
- Candidate revision: `2132DE2DFB4A1158D8E4004B1417F79E5F37CEAE682D1890712B2F068F20CAE3`
- Evaluation definition SHA-256: `856400598AE68D7C4C3DCB15212F0A57424B7A8835BFF4F6A980509E06EA1648`
- Validation cases: `val-cleanup-after-delivery`, `val-exhaustive-review-no-page-ceiling`, `val-four-corpus-nativity`, `val-local-fix-changes-page-box`, `val-long-code-line-consistency`, `val-mixed-diagram-label-cleaning`, `val-mixed-native-raster-output`, `val-ocr-punctuation-is-not-publishable`, `val-paired-profile-heldout`, `val-per-page-pixel-geometry`, `val-reference-is-style-only`, `val-render-exception-disposition`
- Incumbent macro mean: `0.8958333333333333333333333333`
- Candidate macro mean: `1.0`
- Decision: **accepted**
- Rollback: not required

### Full Proposal

    {
      "action": "patch",
      "name": "scan-book-to-native-pdf",
      "edits": [
        {
          "op": "replace",
          "target": "Record page-count policy, figure-label policy, review depth, and cleanup policy.",
          "content": "Record page-count policy, figure-label policy, review depth, and cleanup policy; never impose an arbitrary page-count ceiling when exhaustive fidelity is requested."
        },
        {
          "op": "replace",
          "target": "require `native_or_mixed`, never image-only or sparse-overlay classifications.",
          "content": "require native text on every text-bearing page. Accept `native_or_mixed` or a documented `mixed_native_and_raster` result when only intentional artwork remains; reject image-only body output or sparse-overlay-only text."
        },
        {
          "op": "replace",
          "target": "Resolve every warning at readable zoom.",
          "content": "Resolve every warning at readable zoom and record its page, box, class, evidence, and disposition."
        }
      ]
    }
