I'll execute the audit literally per the requested format. Let me work through each exercise's math, scope, and pedagogy.

`Insight -------------------------------------`
- Adjusted R² verification is one of the most error-prone formulas in econometrics quizzes because two slightly different conventions exist (with or without the (n-1)/(n-k-1) form). Independent recomputation is the only reliable check.
- The OVB sign rule (sign of bias = sign of β₂ × sign of δ₁) is a classic conceptual trap. Exercise 009 inverts it cleverly by giving an *observed* slope and asking what the *true* slope must be - exactly the reasoning students must do in applied work.
- All ten exercises in this batch are CONCEPT type, so they correctly omit `common_mistakes` (per spec, that field is required only for MATH and INTERP).
`-------------------------------------------------`

# Combined Audit: S3

## Summary
- Exercises audited: 10 (EN); FR twins not provided in this packet
- CRITICAL: 0
- WARNING: 1
- SUGGESTION: 3

## Math Findings

### [SUGGESTION] Exercise S3_EN_CONCEPT_010
- **Issue**: Verified computation of adjusted R² for both models.
- **Expected**: $\bar{R}^2_A = 1 - 0.58 \cdot (199/195) = 1 - 0.591897 = 0.40810$; $\bar{R}^2_B = 1 - 0.56 \cdot (199/191) = 1 - 0.583456 = 0.41654$.
- **Found**: 0.408 and 0.417 - matches to three decimals.
- **Evidence**: 199/195 = 1.020513; 199/191 = 1.041885. Difference 0.4165 − 0.4081 ≈ 0.0084, rounding to ~0.009 as stated. PASS Math verified.

### [SUGGESTION] Exercise S3_EN_CONCEPT_010 (format)
- **Issue**: `numerical_answer` field contains a LaTeX string with two values (`"$\bar{R}^2_A \approx 0.408$; $\bar{R}^2_B \approx 0.417$"`) rather than a single scalar.
- **Recommendation**: If the schema's `numerical_answer` is intended for downstream auto-grading, consider serialising as a structured object or splitting into two sub-questions. Not blocking - many graders accept narrative numerical answers for HARD multipart items.

### Other math checks (all PASS)
- **001**: Standard MLR form $y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + u$ - correct.
- **002**: $\beta_1 = \partial E(\text{wage} | \text{educ}, \text{exper}) / \partial \text{educ}$ - correct partial-derivative definition.
- **003**: $\bar{R}^2 = 1 - \frac{\text{SSR}/(n-k-1)}{\text{SST}/(n-1)}$ - correct.
- **004**: OVB formula $E(\tilde\beta_1) - \beta_1 = \beta_2 \delta_1$ - correct; sign analysis (+)·(+) = (+) is correct.
- **005**: $x_2 = x_1/1000$ produces a column of $X$ that is a scalar multiple of another → $X^\top X$ singular → MLR.3 violated. Correct.
- **006**: $E(u | x_1, x_2) = 0$ - correct statement of MLR.4.
- **007**: FWL two-step is correctly described (regress $x_1$ on $x_2$, then regress $y$ on residuals).
- **008**: Gauss–Markov stated correctly; MLR.1–4 → unbiasedness, MLR.5 → efficiency. Correct.
- **009**: Sign of OVB bias = (+)·(+) = positive; reasoning that true effect is plausibly zero or negative is logically valid.

## Pedagogy Findings

### [WARNING] Exercise S3_EN_CONCEPT_003 - Difficulty calibration
- **Issue**: Labelled EASY, but the question requires the student to compare two formulas, identify a degrees-of-freedom penalty, and reason about when the penalty exceeds the SSR drop. That is closer to MED - the "single concept, 1–2 step" EASY criterion is a stretch.
- **Recommendation**: Reclassify to MED, or simplify the prompt to "state the formula for adjusted R²" if EASY is the desired level.

### [SUGGESTION] Exercises 001, 002, 003, 004, 005, 006, 007, 008 - Hint count
- **Issue**: All eight have exactly 2 hints. Spec requires 2–3, so technically compliant, but several are HARD or MED items where a third diagnostic-level hint ("what is the question really asking?") would help struggling students.
- **Recommendation**: For at least 004, 006, 007, 008 (MED), consider adding a third vague/diagnostic hint at the front (e.g. "Re-read the question and identify which assumption / object is being tested."). 009 already has 3 hints and is the model.

### [SUGGESTION] Exercises 009, 010 - `common_mistakes` empty
- **Issue**: These are CONCEPT type, so `common_mistakes` is not required by the spec. But both have natural error patterns worth recording (009: students forget that the OVB sign is a *product* and not a sum; 010: students compare raw $R^2$ even after being told not to).
- **Recommendation**: Optional enrichment - populating `common_mistakes` would help downstream tutoring/feedback even though the schema doesn't require it for CONCEPT.

## Scope & Coverage

All ten exercises remain inside S3 (or its declared S1/S2 prerequisites). I checked every exercise against the forbidden-term list:

| Exercise | Topic | Forbidden term match? |
|---|---|---|
| 001 | MLR standard form | None |
| 002 | Partial effect | None |
| 003 | Adjusted R² | None (S3-allowed) |
| 004 | OVB sign | None (S2 prereq) |
| 005 | Perfect collinearity / MLR.3 | None |
| 006 | MLR.4 | None |
| 007 | Frisch–Waugh–Lovell / partition regression | None (S3-allowed) |
| 008 | Gauss–Markov / BLUE | None |
| 009 | OVB applied (class size) | None |
| 010 | Adjusted R² with $n=200$ | None |

No `forward_reference` or `thin_coverage` flags - adjusted R², partition regression, Gauss–Markov, MLR.1–5, OVB and perfect collinearity are all explicitly in S3 scope per the allowed list, and each is a substantive subsection.

## Twin Parity
- Pairs checked: 0 (FR twins not included in this audit packet)
- Mismatches: not assessable - recommend a follow-up audit pass once FR exercises are visible.

## Exercises Verified (No Issues)
- S3_EN_CONCEPT_001: OK
- S3_EN_CONCEPT_002: OK
- S3_EN_CONCEPT_004: OK
- S3_EN_CONCEPT_005: OK
- S3_EN_CONCEPT_006: OK
- S3_EN_CONCEPT_007: OK
- S3_EN_CONCEPT_008: OK
- S3_EN_CONCEPT_009: OK (math + scope verified, 3 hints, well-calibrated HARD)

```findings_json
[
  {
    "finding_id": "audit_001",
    "severity": "major",
    "category": "pedagogy",
    "exercise_id": "S3_EN_CONCEPT_003",
    "session_id": "S3",
    "description": "Difficulty labelled EASY but the prompt asks the student to compare two formulas (R^2 and adjusted R^2), identify a degrees-of-freedom penalty, and reason about when the penalty exceeds the SSR reduction. This is two concepts combined plus algebraic reasoning, which fits the MED rubric (2-3 concepts) better than EASY (1-2 steps, single concept).",
    "evidence": "difficulty='EASY'; solution requires writing both formulas, identifying that increasing k by 1 raises the penalty term SSR/(n-k-1), and explaining when the penalty outweighs the gain in fit.",
    "recommended_fix": "Either relabel difficulty to 'MED', or simplify the prompt to 'State the formula for adjusted R^2 and identify the penalty term' to match an EASY level.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_002",
    "severity": "minor",
    "category": "format",
    "exercise_id": "S3_EN_CONCEPT_010",
    "session_id": "S3",
    "description": "numerical_answer field contains a LaTeX-formatted string with two values rather than a single scalar. Downstream auto-grading or tooling that expects a numeric scalar may not parse it correctly.",
    "evidence": "numerical_answer = \"$\\bar{R}^2_A \\approx 0.408$; $\\bar{R}^2_B \\approx 0.417$\"",
    "recommended_fix": "Either store as a structured object {model_A: 0.408, model_B: 0.417}, split into two sub-exercises, or set numerical_answer=null and keep the values inline in solution.text.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_003",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S3_EN_CONCEPT_004",
    "session_id": "S3",
    "description": "MED-difficulty exercise has only 2 hints. Spec allows 2-3; a third diagnostic hint at the front would help students who do not immediately recognise the OVB framing. Other MED items (006, 007, 008) share the same minor gap - only 009 (HARD) carries the recommended 3 hints.",
    "evidence": "hints array length = 2 across exercises 001, 002, 003, 004, 005, 006, 007, 008.",
    "recommended_fix": "Optional: add a vague/diagnostic first hint to MED exercises, e.g. 'Identify which MLR assumption / formula is being tested before computing.'",
    "recommended_action": "keep",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_004",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S3_EN_CONCEPT_009",
    "session_id": "S3",
    "description": "common_mistakes is empty. Not required by spec for CONCEPT type, but this HARD exercise has well-known student errors worth recording (e.g. confusing sign of OVB with sign of correlation alone; forgetting that bias is a product not a sum; concluding that the SLR slope being positive proves a positive partial effect).",
    "evidence": "common_mistakes = [] on a HARD multi-part exercise applying OVB sign analysis.",
    "recommended_fix": "Optional enrichment: populate common_mistakes with 2-3 realistic error patterns to support tutoring downstream.",
    "recommended_action": "keep",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  }
]
```

Audit complete: 0 critical, 1 warning (difficulty mislabel on 003), 3 suggestions (format on 010, hint count on MED items, optional `common_mistakes` enrichment). All math verified independently; no forward-reference or thin-coverage violations detected. Twin parity could not be assessed because FR exercises were not included in the packet - recommend a follow-up cross-language pass.
