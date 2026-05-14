# Exercise Generation Prompt Template

You are generating exercises for a multilingual university exercise bank.

## CRITICAL: Scope Constraint (read first, applies to every exercise)

This batch is for session **{{session_id}}**. Every exercise must stay
within the scope of this session and its prerequisites.

**Two failure modes to avoid:**

1. **Forward references.** If the slides for {{session_id}} mention a
   concept in passing or as "we'll cover X in a later session", DO NOT
   generate exercises about X. Such concepts belong to their proper
   session, not this one.
2. **Thin coverage.** If a concept appears in only ~1 slide of the
   session's material, DO NOT make it the central topic of an exercise.
   A concept deserves exercises only when the slides cover it
   substantively (a dedicated subsection of multiple slides).

The authoritative allow / deny lists are at the **bottom of this prompt**,
under "Content Boundary". When in doubt, prefer the constraint over the
slide content — if a concept is in the **Forbidden** list, it is forbidden
even if the current session's slides mention it.

## Course Information

- **Course**: {{course_name_en}} / {{course_name_fr}}
- **Institution**: {{institution}}
- **Domain**: {{domain}}

## Current Session

- **Session**: {{session_id}} — {{session_title}}
- **Topics**: {{topics}}
- **Prerequisites**: {{prerequisites}}

## Exercise Requirements

Generate **{{exercise_count}}** exercises in **{{primary_language_name}}** for this session.

### Type Distribution
{{type_distribution}}

Use the configured `question_type` values exactly. If the type is `YES_NO`,
write a yes/no or true/false-style prompt with a brief justification. If it is
`MCQ`, include answer choices in `question_text` and explain why the distractors
are wrong in `solution.text`. If it is `OPEN`, keep it short enough for quiz
mode. If it is `CASE`, use a compact course-relevant scenario, not a long exam
essay.

### Difficulty Distribution (approximate)
{{difficulty_distribution}}

{{#if assessment_style}}
### Assessment Style Evidence
Match the observed assessment and practice style below. Do not replace it
with generic defaults from the course domain.

{{assessment_style}}

{{/if}}
{{#if quiz_mode_constraints}}
### TA Quiz Mode Constraints
These exercises may be served by a short-form chat assistant. Follow the
constraints below when producing quiz-visible items.

{{quiz_mode_constraints}}

{{/if}}
### ID Format
Use the pattern: `{{session_id}}_{{primary_language_upper}}_{TYPE}_{NNN}` where NNN starts at 001 and increments.

## Exercise Schema

Each exercise must have these fields:

```json
{
  "id": "{{session_id}}_{{primary_language_upper}}_{TYPE}_{NNN}",
  "twin_id": "{{session_id}}_{{secondary_language_upper}}_{TYPE}_{NNN}",
  "session": "{{session_id}}",
  {{session_title_fields}}
  "language": "{{primary_language}}",
  "question_type": "{TYPE}",
  "difficulty": "{{difficulty_levels}}",
  "topics": ["..."],
  "prerequisites": ["..."],
  "lecture_ref": "{{session_id}}.X",
  "question_text": "Full question in markdown with LaTeX",
  "data_table": null,  // or a markdown table STRING like "| Col1 | Col2 |\n|---|---|\n| val1 | val2 |" — NEVER an object
  "solution": {
    "text": "Solution text (max {{max_words}} words), key steps + formula",
    "key_formula": "$...$" or null,
    "numerical_answer": "..." or null,
    "common_mistakes": ["..."] // required for {{common_mistakes_types}}; use [] if none
  },
  "hints": [
    "Hint 1: vague/diagnostic (max {{hint_max_words}} words)",
    "Hint 2: more specific, scaffolded",
    "Hint 3: most specific (optional)"
  ],
  "related_exercises": ["other IDs in same language"]
}
```

## Quality Requirements

1. **Correctness**: Every formula and numerical answer must be independently verifiable. Show your work.
{{#if interpretation_template}}
2. **Interpretation template**: For interpretation exercises, use:
   > {{interpretation_template}}
{{/if}}
3. **Hint progression**: Hints must go from vague/diagnostic to specific/scaffolded. Never leak the answer.
4. **Difficulty calibration**:
{{difficulty_calibration}}
5. **Common mistakes**: For {{common_mistakes_types}} exercises, include 1-2 realistic student errors.
6. **Uniqueness**: No two exercises should be the same question with different numbers.
7. **Data realism**: Use plausible real-world scenarios and realistic values.
8. **Topic salience**: Generate exercises only for topics that have at
   least a dedicated subsection (multiple slides) of treatment in this
   session's material. If a concept appears in only 1 slide or as a
   passing mention, do not generate exercises centrally about it. Brief
   mentions may be cited as context but should never be the exercise's
   primary subject.

{{#if software_tool}}
## Software Exercises ({{software_tool}})

For {{software_tool}} exercises:
- Include valid {{software_tool}} code in the question or solution
- Focus on practical application of session concepts
- Include expected output interpretation
{{/if}}

<!-- The authoritative Content Boundary block is appended by prompt_renderer
     after the batch instructions and course materials, so it appears as the
     last thing the model reads before producing output. -->


## Output

Output a valid JSON array of exercise objects. Ensure valid JSON with proper escaping of LaTeX backslashes.
