# Combined Audit: S1

## Summary
- Exercises audited: 10 (EN only - FR twins not provided in this packet)
- CRITICAL: 0
- WARNING: 2
- SUGGESTION: 4

## Math Findings

No exercises in this packet contain a `numerical_answer` (all 10 are CONCEPT type with `numerical_answer: null`). Formula-level checks were performed instead.

### [VERIFIED] S1_EN_CONCEPT_005
- **Claim checked**: "for any line passing through $(\bar x, \bar y)$, the residuals already sum to zero"
- **Verification**: For $\hat y_i = a + b x_i$ with $a + b\bar x = \bar y$: $\sum_i (y_i - \hat y_i) = n\bar y - na - bn\bar x = n(\bar y - a - b\bar x) = 0$. PASS Statement is correct.

### [VERIFIED] S1_EN_CONCEPT_009 - Claim C
- **Claim checked**: rescaling $x \mapsto 100x$ divides $\hat\beta_1$ by 100.
- **Verification**: $\widehat{\operatorname{Cov}}(100x, y) = 100\,\widehat{\operatorname{Cov}}(x,y)$; $\widehat{\operatorname{Var}}(100x) = 100^2\,\widehat{\operatorname{Var}}(x)$; ratio $= \hat\beta_1 / 100$. PASS Solution correct.

### [VERIFIED] S1_EN_CONCEPT_010 (a)
- **Claim checked**: $x_i = 5$ for all $i$ produces $0/0$.
- **Verification**: $\bar x = 5 \Rightarrow x_i - \bar x = 0 \Rightarrow$ numerator $= 0$ and denominator $= 0$. PASS Correct.

### [VERIFIED] S1_EN_CONCEPT_004 - interpretation template
- Solution (a): "When years of education increase by 1 year, hourly wage tends to be higher by \$0.62, on average, all else equal." - matches required template exactly. PASS
- Dollar sign correctly escaped as `\$0.62`. PASS

### [VERIFIED] S1_EN_CONCEPT_006 - assumption matching
- SLR.1 <-> B (linearity in parameters), SLR.2 <-> D (random sampling), SLR.3 <-> A (variation in $x$), SLR.4 <-> C ($E(u\mid x)=0$). PASS Matches Wooldridge.

### [VERIFIED] S1_EN_CONCEPT_008 - R² extremes
- Perfect fit: SSR = 0 → $R^2 = 1$. PASS
- $\hat\beta_1 = 0$: $\hat y_i = \bar y \Rightarrow$ SSE = 0 → $R^2 = 0$. PASS

## Pedagogy Findings

### [WARNING] S1_EN_CONCEPT_001 - borderline scope
- **Issue**: The exercise's central topic is the *data-structure classification* (cross-section / time series / panel). Per the scope rubric, "panel data" and "cross-section data" are listed as introduced in S9. However, the standard pedagogy of an introductory econometrics session is to *name* these data structures before any technical panel methods are covered (which genuinely live in S9: FE, RE, DiD, etc.). The exercise tests classification only, not panel-data analysis.
- **Recommendation**: KEEP as-is, but verify against actual S1 slides that data-type classification is more than a passing mention. If S1 slides only mention these terms in one bullet, this becomes a `thin_coverage` flag with `target_session: S9`. Without slide access I default to keep with reasoning.

### [WARNING] S1_EN_CONCEPT_004 - common_mistakes scope
- **Issue**: This exercise mixes CONCEPT and INTERP content (it asks students to interpret $\hat\beta_0$ and $\hat\beta_1$ from an estimated regression). The interpretation portion qualifies as INTERP, for which `common_mistakes` are required. The current `common_mistakes` array is good (two realistic errors) but the `question_type` field is `CONCEPT`, which would normally exempt the field. Recommend either keeping the field (as currently done - good) or reclassifying `question_type` to INTERP for consistency.
- **Recommendation**: Reclassify `question_type` from CONCEPT to INTERP, OR keep CONCEPT and document that `common_mistakes` is intentionally retained.

### [SUGGESTION] HARD exercises (008, 009, 010) - third hint
- **Issue**: All three HARD exercises have only 2 hints. The spec allows 2–3; for multi-part HARD synthesis questions, a third, more-scaffolded hint would help students who are stuck on a specific sub-part.
- **Recommendation**: Optionally add a Hint 3 for each HARD exercise that scaffolds the most difficult sub-part (e.g., for 008, a hint focused on (c) - the extreme cases; for 009, a hint specifically about unit-free vs. unit-dependent quantities; for 010, a hint for part (b) on precision).

### [SUGGESTION] S1_EN_CONCEPT_005 - capture the "cancel-out" misconception in common_mistakes
- **Issue**: The question is built around a specific student misconception (minimizing $\sum(y_i - \hat y_i)$). The misconception is well-explained in the question stem but is not codified in `common_mistakes`. Adding it would help downstream consumers (e.g., a study tool that surfaces common errors).
- **Recommendation**: Add a `common_mistakes` entry such as: "Believing OLS minimizes the (signed) sum of residuals rather than the sum of *squared* residuals - overlooks that signed residuals cancel."

### [SUGGESTION] S1_EN_CONCEPT_007 - reference to S1.4 (omitted variable concept)
- **Issue**: Part (c) describes the failure of SLR.4 due to correlation between $x$ and unobservables. This is the classic *omitted variable bias* setup. OVB is in the FORBIDDEN list (S2). The exercise wisely refrains from using the term "omitted variable bias" or computing the bias formula - it stays at the conceptual "SLR.4 fails" level, which is in S1 scope. No action needed; flagged here to confirm the boundary was respected.
- **Recommendation**: KEEP. Verify that future edits do not introduce the explicit term "omitted variable bias" or the bias formula $E(\hat\beta_1) = \beta_1 + \beta_2 \cdot \delta_1$.

### [SUGGESTION] S1_EN_CONCEPT_009 - Claim A precision
- **Issue**: Claim A says "If the sample correlation between $x$ and $y$ is zero, then $\hat\beta_1 = 0$." The justification correctly notes this requires $\widehat{\operatorname{Var}}(x) > 0$ (SLR.3). Could be tightened by stating explicitly that under SLR.3 the equivalence holds.
- **Recommendation**: Minor wording polish; not blocking.

## Twin Parity
- Pairs checked: 0 (FR twins not included in audit packet)
- Mismatches: cannot verify
- Note: All 10 EN exercises declare a `twin_id` of the form `S1_FR_CONCEPT_NNN` matching the EN id's numeric suffix. Format is consistent. Content equivalence (numerical answers, difficulty labels, data values) cannot be verified without the FR exercises.

## Forward References / Scope
- No exercise uses any FORBIDDEN term substantively (no Gauss-Markov, BLUE, OVB, p-value, F-statistic, MLR, dummy variable, t-test, robust SE, log-log, etc.).
- CONCEPT_001 uses "cross-section / time series / panel" as classification labels (not as method names) - flagged above as borderline; defaulting to KEEP.
- CONCEPT_004(b) uses the phrase "all else equal" as part of the standard interpretation template - this is not a forward reference to MLR; it is the canonical SLR phrasing required by the audit's own interpretation template.
- CONCEPT_007(c) describes a violation of SLR.4 without naming "omitted variable bias" - clean.

## Glossary Compliance
- All exercises in this packet are EN (primary language for English material). Glossary EN→FR enforcement applies to the FR twins, which are not in this packet. No glossary findings on the EN side.

## Exercises Verified (No Issues)
- S1_EN_CONCEPT_002: OK
- S1_EN_CONCEPT_003: OK
- S1_EN_CONCEPT_006: OK
- S1_EN_CONCEPT_008: OK (with optional 3rd-hint suggestion)
- S1_EN_CONCEPT_010: OK (with optional 3rd-hint suggestion)

```findings_json
[
  {
    "finding_id": "audit_001",
    "severity": "major",
    "category": "thin_coverage",
    "exercise_id": "S1_EN_CONCEPT_001",
    "session_id": "S1",
    "description": "Central topic is data-structure classification (cross-section / time series / panel). Terms 'panel data' and 'cross-section data' are listed as introduced in S9. Standard pedagogy puts data-type naming in the intro session, but this should be confirmed against actual S1 slide coverage.",
    "evidence": "question_text asks students to classify three datasets as cross-section / time series / panel; topics list contains 'panel_data' and 'cross_section'; lecture_ref S1.1.",
    "recommended_fix": "Verify against S1 slides that data-type classification is substantively covered (more than 1 slide). If thin, reclassify to S9; otherwise keep with reasoning documented.",
    "recommended_action": "keep",
    "target_session": "S9",
    "out_of_scope_concept": "panel data",
    "slide_evidence": "S1.1 (lecture_ref claimed; not independently verified)",
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_002",
    "severity": "major",
    "category": "format",
    "exercise_id": "S1_EN_CONCEPT_004",
    "session_id": "S1",
    "description": "Exercise mixes CONCEPT and INTERP content - part (a) is interpretation of an estimated slope using the standard template, part (b) is intercept interpretation. question_type is CONCEPT but content is INTERP. common_mistakes are present (good) but type/content mismatch should be reconciled.",
    "evidence": "question_type: 'CONCEPT'; question_text: 'Interpret the estimated slope ... using the standard interpretation template'; solution.common_mistakes contains two INTERP-typical errors.",
    "recommended_fix": "Change question_type from 'CONCEPT' to 'INTERP' (preferred), or document why CONCEPT is retained while keeping common_mistakes.",
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
    "exercise_id": "S1_EN_CONCEPT_008",
    "session_id": "S1",
    "description": "HARD multi-part exercise has only 2 hints. Spec allows 2-3; a third scaffolded hint targeting part (c) (extreme R² cases) would help stuck students.",
    "evidence": "hints array has 2 elements; difficulty: 'HARD'; question has parts (a), (b), (c).",
    "recommended_fix": "Add a third hint focused on the extreme cases in part (c): 'When does SSR equal 0? When does SSE equal 0? Translate each into R².'",
    "recommended_action": "rewrite",
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
    "exercise_id": "S1_EN_CONCEPT_009",
    "session_id": "S1",
    "description": "HARD 4-claim true/false exercise has only 2 hints. A third hint specifically distinguishing unit-free vs. unit-dependent quantities would aid claims C and D.",
    "evidence": "hints array has 2 elements; difficulty: 'HARD'; four independent claims (A-D).",
    "recommended_fix": "Add a third hint: 'For C and D, write down the units of beta-hat (units of y per unit of x) versus the units of correlation (none). Which one must change with rescaling, and which cannot?'",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_005",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S1_EN_CONCEPT_010",
    "session_id": "S1",
    "description": "HARD 3-part exercise on SLR.3 has only 2 hints. Part (b) (precision under near-zero variation) is the hardest sub-part and would benefit from its own scaffold.",
    "evidence": "hints array has 2 elements; difficulty: 'HARD'; three parts including precision argument.",
    "recommended_fix": "Add a third hint for part (b): 'Treat the slope as Cov/Var. If Var(x) is tiny but nonzero, what does that do to the magnitude of beta-hat for any small fluctuation in y?'",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_006",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S1_EN_CONCEPT_005",
    "session_id": "S1",
    "description": "Exercise is built around a specific student misconception (minimizing signed sum of residuals) but does not codify it in common_mistakes. Capturing it would make the misconception programmatically discoverable downstream.",
    "evidence": "question_text quotes a wrong student claim about the OLS criterion; solution explains why; common_mistakes is an empty array.",
    "recommended_fix": "Add to common_mistakes: 'Believing OLS minimizes the signed sum of residuals (sum of y_i - y-hat_i) rather than the sum of squared residuals - overlooks that signed residuals cancel and that any line through the sample means already has zero signed residuals.'",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  }
]
```
