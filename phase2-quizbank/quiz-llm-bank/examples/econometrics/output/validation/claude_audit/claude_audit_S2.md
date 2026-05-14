# Combined Audit: S2

## Summary
- Exercises audited: 10 EN (FR twins not supplied; twin parity not verifiable in this batch)
- CRITICAL: 0
- WARNING: 2
- SUGGESTION: 4

## Math Findings

No exercises in this batch carry `numerical_answer`. Where embedded numerical illustrations appear inside solutions (e.g., the $R^2$ comparisons), they were independently recomputed and verified.

### [VERIFIED] Exercise S2_EN_CONCEPT_003 - embedded numerics
- Claim: "$|r_{xy}| \approx 0.424$ would be needed for $R^2 = 0.18$".
- Recomputed: $\sqrt{0.18} = 0.42426\ldots$ PASS
- Claim: "correlation of 0.18 → $R^2 \approx 0.0324$".
- Recomputed: $0.18^2 = 0.0324$ PASS

### [VERIFIED] Exercise S2_EN_CONCEPT_009 - population $R^2$ decomposition
- Formula given: $R^2 = \beta_1^2\operatorname{Var}(x) / (\beta_1^2\operatorname{Var}(x) + \sigma^2)$.
- Study A: $\beta_1=2$, Var(x)=1, $\sigma^2=1$ => $4/(4+1) = 0.80$ PASS
- Study B: $\beta_1=2$, Var(x)=1, $\sigma^2=16$ => $4/(4+16) = 0.20$ PASS
- Formula itself is the correct population analogue when $E(u\mid x)=0$ and $u\perp x$ at second moments.

### [VERIFIED] Exercise S2_EN_CONCEPT_010 - OVB sign formula
- Population identity: $\beta_1 = \gamma_1 + \gamma_2\,\dfrac{\operatorname{Cov}(\text{educ},\text{ability})}{\operatorname{Var}(\text{educ})}$.
- Standard OVB formula, derivation traces correctly: with $u = \gamma_2\,\text{ability} + v$ and $E(v\mid \cdot)=0$, projecting $u$ on $\text{educ}$ yields exactly the stated bias term. With both $\gamma_2>0$ and $\operatorname{Cov}>0$, the bias is positive (upward), as stated. PASS

### [VERIFIED] Exercise S2_EN_CONCEPT_002 - OLS mechanical identity
- Claim (c): with an intercept, $\sum_i \hat{u}_i = 0$ from the FOC. Correct: differentiating SSR w.r.t. $\hat{\beta}_0$ gives $-2\sum_i (y_i - \hat{\beta}_0 - \hat{\beta}_1 x_i) = 0$ => $\sum_i \hat{u}_i = 0$. PASS

### [VERIFIED] Exercise S2_EN_CONCEPT_006(a)
- "$R^2=0 \Leftrightarrow \hat{\beta}_1 = 0$ in a model with intercept and $\operatorname{Var}_n(x)>0$": correct. SSE=0 => $\hat{y}_i = \bar{y}$ for all $i$ => slope is zero (then $\hat{\beta}_0=\bar{y}$). PASS

All other formulas (OLS slope FOCs, BLUE statement, prediction-error decomposition $y_0 - \hat{y}_0 = (\beta_0-\hat{\beta}_0) + (\beta_1-\hat{\beta}_1)x_0 + u_0$, residual definition) are valid.

## Pedagogy Findings

### [WARNING] Exercise S2_EN_CONCEPT_004 - Hint 3 leaks part (c)
- **Issue**: Hint 3 reads "Among SLR.1–SLR.4, which assumption controls the *mean of the error term* given $x$?" Part (c) asks exactly that ("which assumption is the **key** one for unbiasedness?"). The hint essentially names the answer (SLR.4 = zero conditional mean) by paraphrasing its definition.
- **Recommendation**: Soften Hint 3 to point at the *concept* without naming the assumption's content, e.g. "Of the four SLR assumptions, only one constrains the error term's behavior - that is the relevant one for unbiasedness." This preserves the diagnostic ladder without trivializing part (c).

### [WARNING] Exercise S2_EN_CONCEPT_001 - Hint 3 partially leaks the (d) match
- **Issue**: Hint 3 says "The assumption that delivers unbiasedness of $\hat{\beta}_1$ is the zero conditional mean assumption." Combined with item (d)'s text $E(u\mid x)=0$, this collapses the (d)→SLR.4 mapping for any student who reads hint 3.
- **Recommendation**: Replace with a non-leaking nudge such as "Each statement maps one-to-one - once you have committed to three, the fourth is forced."

### [SUGGESTION] Exercise S2_EN_CONCEPT_005 - "best linear predictor" terminology
- **Issue**: Solution part (c) frames the surviving interpretation as "$\hat{\beta}_1$ is still a consistent estimator of the best linear predictor slope." The BLP framework is correct but is not a labeled S2 concept; an EASY-to-MED student may not parse it.
- **Recommendation**: Rephrase as "$\hat{\beta}_1$ is still a valid summary of the *average* difference in earnings between workers who differ by one year of education in this population - a descriptive (not causal) statement." Removes jargon while preserving the message.

### [SUGGESTION] Exercise S2_EN_CONCEPT_002 - solution clarity on (c) vs (d)
- **Issue**: The "Key takeaway" line is the most useful sentence and is buried at the end. Students often miss it.
- **Recommendation**: Promote the (c)-mechanical / (d)-assumption distinction to a labeled "Key contrast" line up top.

### [SUGGESTION] Exercise S2_EN_CONCEPT_007 - make "L = linear in $y$" the headline
- **Issue**: The most-confused part of BLUE is the L. The solution gets it right, but the gloss "$\hat{\beta}_1 = \sum_i w_i\, y_i$ for weights $w_i$ that depend only on the $x_i$'s" is the load-bearing fact and could be put first under L with explicit emphasis.
- **Recommendation**: Lead the L block with that closed form; the contrast against "linear in $x$" then lands.

### [SUGGESTION] Exercise S2_EN_CONCEPT_008 - surface the variance decomposition
- **Issue**: Solution prose names the two sources but does not write the variance decomposition $\operatorname{Var}(y_0 - \hat{y}_0 \mid x_0) = \operatorname{Var}(\hat{y}_0 \mid x_0) + \sigma^2$ explicitly, which is the cleanest way to see *why* the prediction interval is wider.
- **Recommendation**: Add one line in (b) showing the additive $+\sigma^2$ term.

### Solution length, hint count, format
- All 10 solutions are well under 300 words.
- Each exercise has exactly 3 hints, all clearly under 150 words.
- All `\$` escapes are correct (only relevant in S2_EN_CONCEPT_005, which uses `\$4,200` and `\$4{,}200`). PASS
- All exercises are CONCEPT type; the spec requires `common_mistakes` only for MATH/INTERP, so its absence on 9/10 is compliant. Exercise 010 includes two well-targeted entries.

### Difficulty calibration
- 001, 002, 003 (EASY): single-concept identification/matching/MCQ - calibration appropriate. PASS
- 004, 005, 006, 007 (MED): require articulating two-three concepts and applying them - calibration appropriate. PASS
- 008, 009, 010 (HARD): multi-part synthesis (decomposition, derivation, sign analysis) - calibration appropriate. PASS

### Uniqueness within session
- 001 and 004 both touch SLR.1–SLR.4 but at very different depths (matching vs. interpreting unbiasedness). Not a near-duplicate.
- 003, 006, 009 all involve $R^2$ but address distinct facets (interpretation, true/false on the decomposition, comparison across studies). Not duplicates.
- 005 and 010 both treat the education–wage example with omitted ability, but 005 is descriptive/conceptual and 010 is a derivation with sign analysis. Acceptable as a paired arc; consider cross-referencing 005 <-> 010 in `related_exercises` (010 already lists 005; 005 lists 010 - PASS symmetric).

## Twin Parity
- Pairs checked: 0 of 10 (FR twins were not supplied in this audit batch).
- All EN exercises declare a `twin_id` of the form `S2_FR_CONCEPT_NNN` matching their own `NNN`. Twin-side checks (numerical_answer identity, difficulty match, identical data, glossary compliance MCO/erreur type/etc.) are deferred to a twin-pair audit.

## Scope & Coverage (Part C)
All 10 exercises stay within S2 + S1 prerequisites:
- SLR.1–SLR.4, SLR.5, BLUE, Gauss-Markov, $R^2$, SST/SSE/SSR, omitted variable bias, prediction with confidence interval - all explicitly listed as S2.
- Exercise 005 uses confounding/OVB framing (S2 omitted variable bias). PASS
- Exercise 008 uses "prediction interval" - not separately listed, but a direct extension of the session-titled "Prediction" sub-topic with `lecture_ref: S2.6`. Treated as in-scope.
- No forward references detected to MLR, t-tests, robust SE, log-log, fixed effects, IV, etc.
- No thin-coverage flags: every exercise's central topic (assumptions, residuals/errors, $R^2$, unbiasedness, BLUE, prediction error, OVB) is a core S2 subsection per the allowed list.

## Exercises Verified (No Issues Beyond Notes Above)
- S2_EN_CONCEPT_001: OK (Hint 3 leak - see warning)
- S2_EN_CONCEPT_002: OK (clarity suggestion)
- S2_EN_CONCEPT_003: OK
- S2_EN_CONCEPT_004: OK (Hint 3 leak - see warning)
- S2_EN_CONCEPT_005: OK (terminology suggestion)
- S2_EN_CONCEPT_006: OK
- S2_EN_CONCEPT_007: OK (presentation suggestion)
- S2_EN_CONCEPT_008: OK (presentation suggestion)
- S2_EN_CONCEPT_009: OK
- S2_EN_CONCEPT_010: OK

```findings_json
[
  {
    "finding_id": "audit_001",
    "severity": "major",
    "category": "pedagogy",
    "exercise_id": "S2_EN_CONCEPT_004",
    "session_id": "S2",
    "description": "Hint 3 leaks the answer to part (c). Part (c) asks which SLR assumption is key for unbiasedness; Hint 3 paraphrases SLR.4's definition ('which assumption controls the mean of the error term given x'), effectively naming the answer.",
    "evidence": "Hint 3: 'Among SLR.1–SLR.4, which assumption controls the *mean of the error term* given $x$?' Part (c): 'Among SLR.1–SLR.4, which assumption is the key one for unbiasedness?'",
    "recommended_fix": "Replace Hint 3 with a non-leaking nudge, e.g. 'Of the four SLR assumptions, only one is a restriction on the error term - that is the one to look at.'",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  },
  {
    "finding_id": "audit_002",
    "severity": "major",
    "category": "pedagogy",
    "exercise_id": "S2_EN_CONCEPT_001",
    "session_id": "S2",
    "description": "Hint 3 partially leaks the (d) match. By stating that the assumption delivering unbiasedness is the zero conditional mean assumption, and given that statement (d) is literally $E(u \\mid x)=0$, the (d)→SLR.4 mapping becomes trivial.",
    "evidence": "Hint 3: 'The assumption that delivers unbiasedness of $\\hat{\\beta}_1$ is the zero conditional mean assumption.' Combined with item (d)'s text $E(u \\mid x) = 0$, this names one of the four mappings.",
    "recommended_fix": "Soften Hint 3, e.g. 'Each statement maps one-to-one to a single assumption - once three are placed, the fourth is forced. Re-check that you have used each of SLR.1–SLR.4 exactly once.'",
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
    "exercise_id": "S2_EN_CONCEPT_005",
    "session_id": "S2",
    "description": "Solution part (c) introduces 'best linear predictor' terminology that is correct but not a labeled S2 concept; risks confusing students at this stage.",
    "evidence": "Solution (c): 'β̂_1 is still a consistent estimator of the best linear predictor slope, i.e., a measure of how much earnings differ on average between people who differ by one year of education.'",
    "recommended_fix": "Drop the BLP label and keep the descriptive paraphrase: 'β̂_1 still summarizes the average earnings gap between workers who differ by one year of education in this population - a descriptive, not causal, statement.'",
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
    "exercise_id": "S2_EN_CONCEPT_002",
    "session_id": "S2",
    "description": "The most pedagogically valuable contrast (mechanical residual identity vs. error-side assumption) is buried in a 'Key takeaway' line at the end. Many students stop reading after the per-item answers.",
    "evidence": "Solution ends with: 'Key takeaway: residuals are sample-based estimates of errors. Properties (c) and (d) look superficially similar but are very different - (c) is mechanical, (d) is an assumption.'",
    "recommended_fix": "Promote that takeaway to a leading 'Key contrast' line above the per-item answers.",
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
    "exercise_id": "S2_EN_CONCEPT_007",
    "session_id": "S2",
    "description": "The L block could lead with the linear-in-y closed form, which is the load-bearing fact and the most common student misconception (confusing 'linear in y' with 'linear in x').",
    "evidence": "Current L block: 'The estimator is linear in y (not necessarily in x): β̂_1 = Σ_i w_i y_i for weights w_i that depend only on the x_i's.' The closed form belongs at the front.",
    "recommended_fix": "Rewrite L to lead with 'β̂_1 = Σ_i w_i y_i where the weights w_i depend only on the x_i's', then derive the implication that BLUE only compares OLS to other linear-in-y estimators.",
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
    "exercise_id": "S2_EN_CONCEPT_008",
    "session_id": "S2",
    "description": "The variance decomposition that explains why the prediction interval is wider than the CI for E(y|x_0) is described in prose but not written as a formula. The +σ² additive term is the clearest justification.",
    "evidence": "Solution part (b) gives an intuitive description but no formula such as Var(y_0 - ŷ_0 | x_0) = Var(ŷ_0 | x_0) + σ².",
    "recommended_fix": "Add one display line in (b): Var(y_0 − ŷ_0 | x_0) = Var(ŷ_0 | x_0) + σ², so the prediction interval picks up the extra σ² term that the CI for the conditional mean does not.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_claude_combined"
  }
]
```
