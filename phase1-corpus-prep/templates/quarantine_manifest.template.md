# Quarantine Manifest

| Source | Reason | Risk | Possible Recovery | Decision |
|---|---|---|---|---|
| `resources/...` | transcript / duplicate / noisy OCR / correction / spreadsheet | high | targeted excerpt only | quarantine |

## Rules

- Quarantined material is not emitted to downstream consumers by default.
- Any recovery must preserve provenance and state the admitted excerpt.
- Spreadsheets stay quarantined unless the user explicitly approves a specific
  file as a course dataset.
