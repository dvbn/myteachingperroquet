# Twin Generation Prompt Template

You are translating exercises from {{source_language_name}} into {{target_language_name}} for a bilingual university exercise bank.

## Course Information

- **Course**: {{course_name_target}}
- **Institution**: {{institution}}

## Task

Translate the following {{source_language_name}} exercises into {{target_language_name}}. This is NOT a word-for-word translation — it is a **bilingual twin** that must:

1. **Preserve all numerical values** exactly (same data, same answers)
2. **Preserve difficulty** and **topics** labels
3. **Use mandatory {{target_language_name}} terminology** from the glossary below
{{#if interpretation_template_target}}
4. **Adapt the interpretation template** to {{target_language_name}}:
   > {{interpretation_template_target}}
{{/if}}
5. **Maintain the same structure**: same number of sub-parts, same hints count

## Glossary (mandatory terms)

{{glossary_terms}}

## ID Mapping

For each {{source_language_upper}} exercise, create the {{target_language_upper}} twin:
- Change `_{{source_language_upper}}_` to `_{{target_language_upper}}_` in the ID
- Set `language` to `"{{target_language}}"`
- Set `twin_id` to the original {{source_language_upper}} exercise ID
- Update `session_title_{{target_language}}` to the {{target_language_name}} title
- Keep all numerical values, formulas, and data tables identical

## Input Exercises ({{source_language_upper}})

{{exercises_source_json}}

## Output

Output a valid JSON array of {{target_language_name}} exercise objects matching the schema exactly.
