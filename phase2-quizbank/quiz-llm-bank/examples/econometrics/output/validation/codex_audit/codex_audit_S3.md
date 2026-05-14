# Independent Audit: S3_Multiple_Regression

Audited files: exercises_EN.json (S3_Multiple_Regression/exercises_EN.json) and exercises_FR.json (S3_Multiple_Regression/exercises_FR.json)

## Summary
- Exercises audited: 20 total (10 EN, 10 FR)
- Numerical-answer exercises independently recomputed: 2 records / 1 twin pair (`S3_*_CONCEPT_010`)
- CRITICAL: 2
- WARNING: 2
- SUGGESTION: 0
- No duplicate IDs, no missing twins, no broken `related_exercises`, no software code to validate, and no forward-reference or thin-coverage findings
- All solutions are under 300 words; all hint counts are 2-3 and within length limits

## Math Findings
### [CRITICAL] Exercise S3_EN_CONCEPT_009
- **Issue**: Part (b) asks for a sign conclusion that the stated information does not identify.
- **Expected**: With positive omitted-variable bias, the true class-size effect must be **less positive than the observed SLR slope**, but its sign remains ambiguous unless the bias magnitude is known.
- **Found**: The solution says the true partial effect is plausibly “zero or negative,” and Hint 2 steers the student the same way.
- **Evidence**: If the observed SLR slope were `+0.10` and the upward bias were `+0.03`, then the true effect would still be `+0.07`. If the bias were `+0.15`, the true effect would be `-0.05`. The only valid inference is `beta_true = beta_SLR - bias < beta_SLR`.

### [CRITICAL] Exercise S3_FR_CONCEPT_009
- **Issue**: La partie (b) demande une conclusion de signe que les informations fournies n'identifient pas.
- **Expected**: Avec un biais de variable omise positif, l'effet véritable doit être **plus faible que la pente SLR observée**, mais son signe reste ambigu tant que l'ampleur du biais n'est pas connue.
- **Found**: La solution conclut à un effet « nul ou négatif », et l'indice 2 pousse dans la même direction.
- **Evidence**: Si la pente SLR observée était `+0,10` et le biais `+0,03`, l'effet véritable resterait `+0,07`. Si le biais était `+0,15`, l'effet véritable serait `-0,05`. La seule inférence justifiée est `beta_vrai = beta_SLR - biais < beta_SLR`.

## Pedagogy Findings
- No standalone pedagogy-only failures beyond the underdetermined wording/solution in `S3_EN_CONCEPT_009` and `S3_FR_CONCEPT_009`.
- Question clarity, hint progression, and solution-length constraints otherwise passed.

## Structural Findings
### [WARNING] Exercise S3_FR_CONCEPT_008
- **Issue**: The French twin keeps the English expansion of `BLUE` (“Best Linear Unbiased Estimator”), so the glossary translation for “Unbiased” is not fully respected inside the French exercise.
- **Recommendation**: Keep the acronym `BLUE` if desired, but state the expansion only in French, e.g. “meilleur estimateur linéaire sans biais”.

### [WARNING] Exercise S3_EN_CONCEPT_010
- **Issue**: Twin `numerical_answer` strings are not identical across EN/FR, even though the numeric content matches.
- **Found**: EN stores `0.408` / `0.417`; FR stores `0{,}408` / `0{,}417` with localized punctuation and spacing.
- **Evidence**: From `n=200`, `k_A=4`, `k_B=8`, `R^2_A=0.42`, `R^2_B=0.44`,
  `\bar R^2_A = 1-(1-0.42)*199/195 = 0.40810256`
  and `\bar R^2_B = 1-(1-0.44)*199/191 = 0.41654450`,
  so the math is correct, but the twin-field representation is not identical.
- **Recommendation**: Canonicalize `numerical_answer` across twins or store structured numeric values.

## Exercises Verified (No Issues)
- `S3_EN_CONCEPT_001` / `S3_FR_CONCEPT_001`: OK
- `S3_EN_CONCEPT_002` / `S3_FR_CONCEPT_002`: OK
- `S3_EN_CONCEPT_003` / `S3_FR_CONCEPT_003`: OK
- `S3_EN_CONCEPT_004` / `S3_FR_CONCEPT_004`: OK
- `S3_EN_CONCEPT_005` / `S3_FR_CONCEPT_005`: OK
- `S3_EN_CONCEPT_006` / `S3_FR_CONCEPT_006`: OK
- `S3_EN_CONCEPT_007` / `S3_FR_CONCEPT_007`: OK
- `S3_EN_CONCEPT_008`: OK
- `S3_FR_CONCEPT_010`: math/formula/reasoning OK; see twin-format warning above

```findings_json
[
  {
    "finding_id": "codex_audit_001",
    "severity": "critical",
    "category": "correctness",
    "exercise_id": "S3_EN_CONCEPT_009",
    "session_id": "S3",
    "description": "Part (b) is underidentified: a small positive SLR slope plus positive omitted-variable bias does not determine the sign of the true class-size effect.",
    "evidence": "Positive OVB implies beta_true = beta_SLR - bias < beta_SLR, but the sign depends on the bias magnitude. Example: +0.10 - 0.03 = +0.07, while +0.10 - 0.15 = -0.05. The current solution and Hint 2 incorrectly push toward zero/negative.",
    "recommended_fix": "Rewrite part (b), the solution, and Hint 2 to say that the true effect is less positive than the SLR estimate and that its sign remains ambiguous unless the magnitude of the upward bias is known.",
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
    "category": "correctness",
    "exercise_id": "S3_FR_CONCEPT_009",
    "session_id": "S3",
    "description": "La partie (b) est sous-identifiée : une petite pente SLR positive et un biais de variable omise positif ne déterminent pas le signe de l'effet véritable de la taille de classe.",
    "evidence": "Un BVO positif implique beta_vrai = beta_SLR - biais < beta_SLR, mais le signe dépend de l'ampleur du biais. Exemple : +0,10 - 0,03 = +0,07, tandis que +0,10 - 0,15 = -0,05. La solution actuelle et l'indice 2 orientent à tort vers nul/négatif.",
    "recommended_fix": "Réécrire la partie (b), la solution et l'indice 2 pour dire que l'effet véritable est moins positif que l'estimation SLR et que son signe reste ambigu tant que l'ampleur du biais à la hausse n'est pas connue.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": true,
    "source": "audit_codex"
  },
  {
    "finding_id": "codex_audit_003",
    "severity": "major",
    "category": "glossary",
    "exercise_id": "S3_FR_CONCEPT_008",
    "session_id": "S3",
    "description": "The French solution expands BLUE with English words, so the glossary translation for 'Unbiased' is not fully respected inside the French twin-language exercise.",
    "evidence": "solution.text contains the English expansion 'Best Linear Unbiased Estimator' before giving the French gloss 'meilleur estimateur linéaire sans biais'.",
    "recommended_fix": "Keep the acronym BLUE if desired, but express the expansion only in French, e.g. 'meilleur estimateur lineaire sans biais', without the embedded English term 'Unbiased'.",
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
    "category": "twin",
    "exercise_id": "S3_EN_CONCEPT_010",
    "session_id": "S3",
    "description": "The EN/FR twins do not store identical numerical_answer strings, even though the underlying values match.",
    "evidence": "EN numerical_answer is '$\\\\bar{R}^2_A \\\\approx 0.408$; $\\\\bar{R}^2_B \\\\approx 0.417$' while FR stores '$\\\\bar{R}^2_A \\\\approx 0{,}408$ ; $\\\\bar{R}^2_B \\\\approx 0{,}417$'. Recomputed from n=200, kA=4, kB=8, R2A=0.42, R2B=0.44: 0.40810256 and 0.41654450.",
    "recommended_fix": "Canonicalize numerical_answer across twins or store structured numeric fields so parity checks do not depend on locale-specific punctuation.",
    "recommended_action": "rewrite",
    "target_session": null,
    "out_of_scope_concept": null,
    "slide_evidence": null,
    "blocking": false,
    "source": "audit_codex"
  }
]
```