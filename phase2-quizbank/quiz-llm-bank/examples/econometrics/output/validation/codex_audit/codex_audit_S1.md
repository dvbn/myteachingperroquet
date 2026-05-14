# Independent Audit: S1_Introduction_SLR

## Summary
- Source files: exercises_EN.json (S1_Introduction_SLR/exercises_EN.json), exercises_FR.json (S1_Introduction_SLR/exercises_FR.json)
- Exercises audited: 20 total (10 EN, 10 FR)
- Quantitative exercises with `solution.numerical_answer`: 0
- CRITICAL: 2
- WARNING: 6
- SUGGESTION: 0
- No duplicate IDs, no missing twins, no broken `related_exercises`, no glossary violations, and no software/code syntax items to validate.
- All EN/FR twins preserve the same data values after normalizing decimal/thousands notation; `solution.numerical_answer` is `null` throughout.
- All solutions are under 300 words; all exercises have 2 hints under 150 words; no hint leaks the answer.
- Difficulty labels are broadly consistent, and I found no suspicious near-duplicates.
- Thin-coverage review is limited by the absence of slide files in the workspace; I only flagged scope issues that are explicit under the provided session scope rules.

## Math Findings
### [WARNING] Exercise S1_EN_CONCEPT_003
- **Issue**: `solution.text` gives conditional-mean interpretations of `\beta_0` and `\beta_1` without stating the needed assumption `E(u \mid x)=0`.
- **Expected**: Either describe `\beta_0` and `\beta_1` as the intercept and slope of the linear component, or explicitly qualify the expected-value interpretation with `E(u \mid x)=0`.
- **Found**: EN item (S1_Introduction_SLR/exercises_EN.json:64) says `\beta_0` is the expected value of `y` when `x=0` and `\beta_1` is the expected change in `y`.
- **Evidence**: The stated key formula `y=\beta_0+\beta_1x+u` is correct, but algebra gives `E(y\mid x)=\beta_0+\beta_1x+E(u\mid x)`, not `\beta_0+\beta_1x` unconditionally.

### [WARNING] Exercise S1_FR_CONCEPT_003
- **Issue**: `solution.text` gives conditional-mean interpretations of `\beta_0` and `\beta_1` without stating the needed assumption `E(u \mid x)=0`.
- **Expected**: Either describe `\beta_0` and `\beta_1` as the intercept and slope of the linear component, or explicitly qualify the expected-value interpretation with `E(u \mid x)=0`.
- **Found**: FR item (S1_Introduction_SLR/exercises_FR.json:64) says `\beta_0` is the expected value of `y` when `x=0` and `\beta_1` is the expected change in `y`.
- **Evidence**: The stated key formula `y=\beta_0+\beta_1x+u` is correct, but algebra gives `E(y\mid x)=\beta_0+\beta_1x+E(u\mid x)`, not `\beta_0+\beta_1x` unconditionally.

## Pedagogy Findings
### [WARNING] Exercise S1_EN_CONCEPT_004
- **Issue**: Part (b) is under-specified. It asks whether the intercept is economically meaningful “in this dataset,” but the sample range of `educ` is never given.
- **Recommendation**: Add the observed range of `educ`, or rewrite the solution as conditional: “not meaningful if `educ=0` is outside or at the edge of the sample.”
- **Evidence**: EN item (S1_Introduction_SLR/exercises_EN.json:97) provides only `n=1,200` and the fitted line, while the solution asserts that `educ=0` is effectively outside the data range.

### [WARNING] Exercise S1_FR_CONCEPT_004
- **Issue**: Part (b) is under-specified. It asks whether the intercept is economically meaningful “in this dataset,” but the sample range of `educ` is never given.
- **Recommendation**: Add the observed range of `educ`, or rewrite the solution as conditional: “not meaningful if `educ=0` is outside or at the edge of the sample.”
- **Evidence**: FR item (S1_Introduction_SLR/exercises_FR.json:97) provides only `n=1{,}200` and the fitted line, while the solution asserts that `educ=0` is effectively outside the data range.

## Structural Findings
### [WARNING] Exercise S1_EN_CONCEPT_009
- **Issue**: The stem is structurally a true/false item, but `question_type` and the ID type component are `CONCEPT`.
- **Recommendation**: Reclassify it as `TF` and align the IDs accordingly, or rewrite the stem as an open-ended concept question without truth-value labels.
- **Evidence**: EN item (S1_Introduction_SLR/exercises_EN.json:267) explicitly asks whether Claims A-D are “true” or “false”.

### [WARNING] Exercise S1_FR_CONCEPT_009
- **Issue**: The stem is structurally a true/false item, but `question_type` and the ID type component are `CONCEPT`.
- **Recommendation**: Reclassify it as `TF` and align the IDs accordingly, or rewrite the stem as an open-ended concept question without truth-value labels.
- **Evidence**: FR item (S1_Introduction_SLR/exercises_FR.json:267) explicitly asks whether affirmations A-D are “vraie/fausse”.

## Scope Findings
### [CRITICAL] Exercise S1_EN_CONCEPT_001
- **Issue**: Forward reference. The central task is classifying datasets as cross-section, time series, or panel, but all three are listed as later-session concepts in the supplied scope rules.
- **Expected**: An S1 exercise should center on allowed S1 topics, or this item should be moved to the session where data-structure types are introduced.
- **Found**: EN item (S1_Introduction_SLR/exercises_EN.json:3) is entirely about dataset-type classification.
- **Evidence**: Under the provided scope matrix, `cross-section data`, `time series`, and `panel data` are introduced in `S9`, so this is a session-placement error, not just a wording issue.

### [CRITICAL] Exercise S1_FR_CONCEPT_001
- **Issue**: Forward reference. The central task is classifying datasets as cross-section, time series, or panel, but all three are listed as later-session concepts in the supplied scope rules.
- **Expected**: An S1 exercise should center on allowed S1 topics, or this item should be moved to the session where data-structure types are introduced.
- **Found**: FR item (S1_Introduction_SLR/exercises_FR.json:3) is entirely about dataset-type classification.
- **Evidence**: Under the provided scope matrix, `cross-section data`, `time series`, and `panel data` are introduced in `S9`, so this is a session-placement error, not just a wording issue.

## Exercises Verified (No Issues)
- `S1_EN_CONCEPT_002` / `S1_FR_CONCEPT_002`: OK. Correlation-vs-causation reasoning is sound and in scope.
- `S1_EN_CONCEPT_005` / `S1_FR_CONCEPT_005`: OK. The OLS objective and the cancellation critique are mathematically valid.
- `S1_EN_CONCEPT_006` / `S1_FR_CONCEPT_006`: OK. SLR.1-SLR.4 matching is correct.
- `S1_EN_CONCEPT_007` / `S1_FR_CONCEPT_007`: OK. The SLR.4 violation logic is correct and the hints do not leak answers.
- `S1_EN_CONCEPT_008` / `S1_FR_CONCEPT_008`: OK. The SST/SSE/SSR decomposition, `R^2` identities, and extreme-case conclusions (`R^2=1`, `R^2=0`) are correct.
- `S1_EN_CONCEPT_010` / `S1_FR_CONCEPT_010`: OK. The `x_i=5` case correctly yields an undefined slope (`0/0`), and the low-variation explanation is sound.

```findings_json
[
  {
    "finding_id": "codex_audit_001",
    "severity": "critical",
    "category": "forward_reference",
    "exercise_id": "S1_EN_CONCEPT_001",
    "session_id": "S1",
    "description": "The exercise's central topic is dataset-type classification using cross-section data, time series, and panel data, which are listed as later-session concepts rather than S1 concepts.",
    "evidence": "The prompt asks students to classify three datasets as cross-section, time series, or panel. Under the supplied scope rules, `cross-section data`, `time series`, and `panel data` are introduced in S9, so the whole task is out of scope for S1.",
    "recommended_fix": "Move this exercise to S9, or replace it with an S1-centered question on OLS, simple linear regression, covariance/correlation, R-squared, or SLR.1-SLR.4.",
    "recommended_action": "reclassify",
    "target_session": "S9",
    "out_of_scope_concept": "cross-section data / time series / panel data",
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_002",
    "severity": "critical",
    "category": "forward_reference",
    "exercise_id": "S1_FR_CONCEPT_001",
    "session_id": "S1",
    "description": "The exercise's central topic is dataset-type classification using cross-section data, time series, and panel data, which are listed as later-session concepts rather than S1 concepts.",
    "evidence": "The prompt asks students to classify three datasets as cross-section, time series, or panel. Under the supplied scope rules, `cross-section data`, `time series`, and `panel data` are introduced in S9, so the whole task is out of scope for S1.",
    "recommended_fix": "Move this exercise to S9, or replace it with an S1-centered question on OLS, simple linear regression, covariance/correlation, R-squared, or SLR.1-SLR.4.",
    "recommended_action": "reclassify",
    "target_session": "S9",
    "out_of_scope_concept": "cross-section data / time series / panel data",
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_003",
    "severity": "major",
    "category": "correctness",
    "exercise_id": "S1_EN_CONCEPT_003",
    "session_id": "S1",
    "description": "The solution interprets β0 and β1 as conditional-mean quantities without stating the needed assumption E(u|x)=0.",
    "evidence": "The prompt gives only `y = β0 + β1 x + u`, but the solution says β0 is the expected value of y when x=0 and β1 is the expected change in y from a one-unit increase in x. In general, `E(y|x)=β0+β1x+E(u|x)`.",
    "recommended_fix": "Describe β0 as the intercept and β1 as the slope of the linear component, or explicitly qualify the expected-value interpretation with `under E(u|x)=0`.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_004",
    "severity": "major",
    "category": "correctness",
    "exercise_id": "S1_FR_CONCEPT_003",
    "session_id": "S1",
    "description": "The solution interprets β0 and β1 as conditional-mean quantities without stating the needed assumption E(u|x)=0.",
    "evidence": "The prompt gives only `y = β0 + β1 x + u`, but the solution says β0 is the expected value of y when x=0 and β1 is the expected change in y from a one-unit increase in x. In general, `E(y|x)=β0+β1x+E(u|x)`.",
    "recommended_fix": "Describe β0 as the intercept and β1 as the slope of the linear component, or explicitly qualify the expected-value interpretation with `under E(u|x)=0`.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_005",
    "severity": "major",
    "category": "pedagogy",
    "exercise_id": "S1_EN_CONCEPT_004",
    "session_id": "S1",
    "description": "Part (b) is under-specified because it asks whether the intercept is economically meaningful in this dataset without providing the range of education in the sample.",
    "evidence": "The prompt gives only the fitted line and sample size `1,200`. The solution and hint then assert that `educ = 0` is outside or effectively outside the sample range, but the exercise never states that range.",
    "recommended_fix": "Add the observed range of `educ`, or rewrite the solution as conditional: `not meaningful if educ=0 is outside or at the edge of the sample`.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_006",
    "severity": "major",
    "category": "pedagogy",
    "exercise_id": "S1_FR_CONCEPT_004",
    "session_id": "S1",
    "description": "Part (b) is under-specified because it asks whether the intercept is economically meaningful in this dataset without providing the range of education in the sample.",
    "evidence": "The prompt gives only the fitted line and sample size `1{,}200`. The solution and hint then assert that `educ = 0` is outside or effectively outside the sample range, but the exercise never states that range.",
    "recommended_fix": "Add the observed range of `educ`, or rewrite the solution as conditional: `not meaningful if educ=0 is outside or at the edge of the sample`.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_007",
    "severity": "major",
    "category": "format",
    "exercise_id": "S1_EN_CONCEPT_009",
    "session_id": "S1",
    "description": "The item is structurally a true/false exercise, but `question_type` and the ID type component are labeled `CONCEPT`.",
    "evidence": "The stem explicitly asks students to state whether Claims A-D are `true` or `false` and justify each answer.",
    "recommended_fix": "Change the exercise to type `TF` and rename the IDs accordingly, or rewrite the stem as an open-ended concept question without truth-value labels.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_008",
    "severity": "major",
    "category": "format",
    "exercise_id": "S1_FR_CONCEPT_009",
    "session_id": "S1",
    "description": "The item is structurally a true/false exercise, but `question_type` and the ID type component are labeled `CONCEPT`.",
    "evidence": "The stem explicitly asks students to state whether claims A-D are `vraie` or `fausse` and justify each answer.",
    "recommended_fix": "Change the exercise to type `TF` and rename the IDs accordingly, or rewrite the stem as an open-ended concept question without truth-value labels.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  }
]
```