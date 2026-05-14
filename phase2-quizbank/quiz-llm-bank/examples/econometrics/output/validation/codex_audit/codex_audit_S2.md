# Independent Audit: S2_SLR_Properties

## Summary
- Exercises audited: 20 total (10 EN, 10 FR)
- Exercises with `numerical_answer`: 0
- CRITICAL: 4
- WARNING: 3
- SUGGESTION: 4
- No code/software commands appear in this session.
- Twin parity is otherwise clean: all 10 twin pairs exist; `difficulty`, `lecture_ref`, `question_type`, and `numerical_answer` (all `null`) match; `related_exercises` resolve and stay same-language.
- No forward references detected. Thin-coverage review is limited because no slide deck/source notes were present in the workspace; I used `course_config.json` and `lecture_ref`.

## Math Findings
- All LaTeX formulas checked are mathematically valid.

### [VERIFIED] Exercises S2_EN/FR_CONCEPT_003
- **Issue**: Embedded `R^2` numerics needed verification.
- **Expected**: `0.18^2 = 0.0324` and `sqrt(0.18) = 0.42426...`.
- **Found**: The solutions state `R^2 ≈ 0.0324` when `r=0.18`, and `|r| ≈ 0.424` when `R^2=0.18`.
- **Evidence**: Recomputations match exactly.

### [VERIFIED] Exercises S2_EN/FR_CONCEPT_009
- **Issue**: The study-comparison numerics and population-`R^2` formula needed verification.
- **Expected**: With `β1=2`, `Var(x)=1`, `σ_A^2=1`, `σ_B^2=16`, the population analogue gives `R_A^2 = 4/(4+1)=0.80` and `R_B^2 = 4/(4+16)=0.20`.
- **Found**: The stored solutions report `0.80` and `0.20`.
- **Evidence**: Recomputed values match; the formula is valid under the SLR second-moment setup used in the exercise.

### [WARNING] Exercises S2_EN/FR_CONCEPT_010
- **Issue**: The omitted-variable-bias algebra is correct, but the prompt uses sample-covariance language while the solution concludes about population bias.
- **Expected**: Bias claims should be tied to population covariance, or the prompt should ask about the realized omitted-variable component in the given sample.
- **Found**: The prompt says “In the sample, `Cov(educ, ability) > 0`,” while the solution then invokes the population identity `β1 = γ1 + γ2 Cov/Var`.
- **Evidence**: Bias is an expectation concept, so its sign is pinned down by population covariance, not by one realized sample covariance.

## Pedagogy Findings
### [CRITICAL] Exercises S2_EN_CONCEPT_001 / S2_FR_CONCEPT_001
- **Issue**: Hint 2 leaks the full matching answer. It explicitly maps SLR.1–SLR.4 to the four descriptions, so the core task is solvable from the hint alone.
- **Recommendation**: Rewrite Hint 2 so it stays directional rather than enumerating each assumption-description pair.

### [CRITICAL] Exercises S2_EN_CONCEPT_004 / S2_FR_CONCEPT_004
- **Issue**: Hint 3 effectively gives away part (c) by restating the zero-conditional-mean idea that uniquely identifies SLR.4.
- **Recommendation**: Replace it with a weaker nudge toward “the assumption about the error term,” without paraphrasing `E(u|x)=0`.

### [SUGGESTION] Exercises S2_EN_CONCEPT_005 / S2_FR_CONCEPT_005
- **Issue**: Solution part (c) introduces “best linear predictor” / “meilleur prédicteur linéaire,” which is correct but not a labeled S2 term and is unnecessary for the intended lesson.
- **Recommendation**: Rephrase in plain associational language: the slope still summarizes average earnings differences by education, but not causally.

### [SUGGESTION] Exercises S2_EN_CONCEPT_008 / S2_FR_CONCEPT_008
- **Issue**: The explanation for why the prediction interval is wider than the confidence interval is correct but would be clearer with the variance decomposition written explicitly.
- **Recommendation**: Add `Var(y_0-\hat y_0|x_0)=Var(\hat y_0|x_0)+\sigma^2` or an equivalent line.

## Structural Findings
### [WARNING] French exercises S2_FR_CONCEPT_004 / S2_FR_CONCEPT_009 / S2_FR_CONCEPT_010
- **Issue**: Glossary normalization drifts from the required `biais de variables omises` to `biais de variable omise`.
- **Recommendation**: Standardize all three to the glossary form for bilingual consistency.

## Exercises Verified (No Issues)
- S2_EN/FR_CONCEPT_002: OK (error vs residual distinction, residual-sum-to-zero property, and formula all correct)
- S2_EN/FR_CONCEPT_003: OK (embedded numerics recomputed and correct)
- S2_EN/FR_CONCEPT_006: OK (`R^2` TRUE/FALSE logic and decomposition correct)
- S2_EN/FR_CONCEPT_007: OK (BLUE decomposition and homoskedasticity statement correct)

```findings_json
[
  {
    "finding_id": "codex_audit_001",
    "severity": "critical",
    "category": "pedagogy",
    "exercise_id": "S2_EN_CONCEPT_001",
    "session_id": "S2",
    "description": "Hint 2 leaks the answer by explicitly mapping SLR.1-SLR.4 to the four descriptions used in the prompt.",
    "evidence": "Hint 2 says: 'SLR.1 is about the equation. SLR.2 is about how observations were selected. SLR.3 is about whether x varies. SLR.4 is about E(u | x).' The question asks the student to match exactly those four descriptions.",
    "recommended_fix": "Rewrite Hint 2 so it stays directional and does not enumerate all four mappings.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_002",
    "severity": "critical",
    "category": "pedagogy",
    "exercise_id": "S2_FR_CONCEPT_001",
    "session_id": "S2",
    "description": "L'indice 2 divulgue la réponse en associant explicitement SLR.1-SLR.4 aux quatre descriptions de l'énoncé.",
    "evidence": "L'indice 2 dit : 'SLR.1 concerne l'équation... SLR.4 concerne E(u | x).' La tâche demandée est précisément de faire cette correspondance.",
    "recommended_fix": "Réécrire l'indice 2 pour qu'il reste directionnel sans énumérer les quatre correspondances.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_003",
    "severity": "critical",
    "category": "pedagogy",
    "exercise_id": "S2_EN_CONCEPT_004",
    "session_id": "S2",
    "description": "Hint 3 effectively gives away part (c) by paraphrasing the unique assumption the student is supposed to identify.",
    "evidence": "Part (c) asks which SLR assumption is key for unbiasedness. Hint 3 asks: 'Which assumption controls the mean of the error term given x?' That directly points to SLR.4.",
    "recommended_fix": "Replace Hint 3 with a weaker prompt toward 'the assumption about the error term' without paraphrasing zero conditional mean.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_004",
    "severity": "critical",
    "category": "pedagogy",
    "exercise_id": "S2_FR_CONCEPT_004",
    "session_id": "S2",
    "description": "L'indice 3 divulgue pratiquement la réponse à la partie (c) en reformulant l'hypothèse qu'il faut identifier.",
    "evidence": "La partie (c) demande quelle hypothèse SLR est clé pour l'absence de biais. L'indice 3 demande quelle hypothèse contrôle la moyenne du terme d'erreur sachant x, ce qui pointe directement vers SLR.4.",
    "recommended_fix": "Remplacer l'indice 3 par un rappel plus faible vers 'l'hypothèse portant sur le terme d'erreur' sans reformuler E(u | x)=0.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_005",
    "severity": "major",
    "category": "correctness",
    "exercise_id": "S2_EN_CONCEPT_010",
    "session_id": "S2",
    "description": "The prompt uses sample-covariance language, but the solution concludes about population bias. That mixes realized-sample wording with an expectation concept.",
    "evidence": "Prompt: 'In the sample, Cov(educ, ability) > 0.' Solution: 'The OLS slope satisfies (in the population) beta_1 = gamma_1 + gamma_2 Cov/Var > gamma_1.'",
    "recommended_fix": "Change the prompt to population language, e.g. 'Suppose Cov(educ, ability) > 0 in the population,' or rephrase part (b) to ask about the realized omitted-variable component in this sample.",
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
    "category": "correctness",
    "exercise_id": "S2_FR_CONCEPT_010",
    "session_id": "S2",
    "description": "L'énoncé parle de covariance dans l'échantillon, alors que la solution conclut sur un biais de population. Cela mélange un langage d'échantillon réalisé avec un concept d'espérance.",
    "evidence": "Énoncé : 'Dans l'échantillon, Cov(scolarité, capacité) > 0.' Solution : 'La pente MCO satisfait (en population) beta_1 = gamma_1 + gamma_2 Cov/Var > gamma_1.'",
    "recommended_fix": "Remplacer par un énoncé de population, par exemple 'Supposez que Cov(scolarité, capacité) > 0 dans la population', ou reformuler la partie (b) pour parler du terme omis dans cet échantillon.",
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
    "category": "glossary",
    "exercise_id": "S2_FR_CONCEPT_010",
    "session_id": "S2",
    "description": "French glossary normalization drifts from the required 'biais de variables omises' to 'biais de variable omise'. The same drift also appears in S2_FR_CONCEPT_004 and S2_FR_CONCEPT_009.",
    "evidence": "S2_FR_CONCEPT_010 question and solution use 'biais de variable omise'; S2_FR_CONCEPT_004 and S2_FR_CONCEPT_009 also use the singular form, while the provided glossary specifies 'biais de variables omises'.",
    "recommended_fix": "Standardize all affected French exercises to 'biais de variables omises' for glossary consistency.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_008",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S2_EN_CONCEPT_005",
    "session_id": "S2",
    "description": "Solution part (c) introduces 'best linear predictor' terminology that is correct but unnecessary for this S2 concept exercise.",
    "evidence": "Solution (c) says the slope is 'a consistent estimator of the best linear predictor slope'.",
    "recommended_fix": "Replace the jargon with plain descriptive wording about average earnings differences by education, while keeping the non-causal caveat.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_009",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S2_FR_CONCEPT_005",
    "session_id": "S2",
    "description": "La solution de la partie (c) introduit le terme 'meilleur prédicteur linéaire', correct mais inutilement technique pour cet exercice conceptuel de S2.",
    "evidence": "La solution (c) dit que la pente est 'un estimateur convergent de la pente du meilleur prédicteur linéaire'.",
    "recommended_fix": "Remplacer ce jargon par une formulation descriptive simple sur les écarts moyens de revenus selon la scolarité, tout en gardant la distinction non causale.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_010",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S2_EN_CONCEPT_008",
    "session_id": "S2",
    "description": "The solution correctly explains why the prediction interval is wider than the confidence interval, but it omits the clean variance decomposition that makes the point most transparent.",
    "evidence": "Part (b) is prose-only; it never writes Var(y_0 - yhat_0 | x_0) = Var(yhat_0 | x_0) + sigma^2.",
    "recommended_fix": "Add one formula line showing the additive +sigma^2 term in the individual-outcome prediction error variance.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_011",
    "severity": "minor",
    "category": "pedagogy",
    "exercise_id": "S2_FR_CONCEPT_008",
    "session_id": "S2",
    "description": "La solution explique correctement pourquoi l'intervalle de prédiction est plus large que l'intervalle de confiance, mais elle n'écrit pas la décomposition de variance qui rend ce point le plus transparent.",
    "evidence": "La partie (b) reste en prose; elle n'écrit jamais Var(y_0 - yhat_0 | x_0) = Var(yhat_0 | x_0) + sigma^2.",
    "recommended_fix": "Ajouter une ligne de formule montrant explicitement le terme supplémentaire +sigma^2 dans la variance de l'erreur de prédiction individuelle.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  }
]
```