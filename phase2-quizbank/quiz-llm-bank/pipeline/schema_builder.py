#!/usr/bin/env python3
"""Generate a JSON Schema for exercises from course_config.json."""

import json
import sys
from pathlib import Path

# Allow running from pipeline/ or project root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, get_output_dir, get_languages


def build_schema(cfg: dict) -> dict:
    """Build a JSON Schema (draft 2020-12) from config."""
    sessions = [s["id"] for s in cfg["sessions"]]
    ex_types = cfg["exercise_types"]
    difficulties = list(cfg["difficulty_distribution"].keys())
    languages = get_languages(cfg)

    # Build required fields — session_title_{lang} for each configured language
    required = [
        "id", "twin_id", "session",
    ]
    for lang in languages:
        required.append(f"session_title_{lang}")
    required += [
        "language", "question_type", "difficulty", "topics", "prerequisites",
        "lecture_ref", "question_text", "solution", "hints", "related_exercises",
    ]

    # Determine which solution fields are required
    # Default includes key_formula to stay compatible with downstream
    # exercise-bank consumers that index quantitative formulas.
    sol_required = cfg.get("solution_constraints", {}).get(
        "required_solution_fields", ["text", "key_formula"]
    )

    # Build course name for title — use first available course_name_* or course_id
    course_name = cfg.get(f"course_name_{languages[0]}", cfg["course_id"])

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{course_name} Exercise",
        "description": f"Schema for exercise bank: {cfg['course_id']}",
        "type": "object",
        "required": required,
        "properties": {
            "id": {
                "type": "string",
                "pattern": cfg["id_regex"],
                "description": "Unique exercise ID",
            },
            "twin_id": {
                "type": "string",
                "pattern": cfg["id_regex"],
                "description": "ID of the translation twin exercise",
            },
            "session": {
                "type": "string",
                "enum": sessions,
            },
            "language": {
                "type": "string",
                "enum": languages,
            },
            "question_type": {
                "type": "string",
                "enum": ex_types,
            },
            "difficulty": {
                "type": "string",
                "enum": difficulties,
            },
            "topics": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "prerequisites": {
                "type": "array",
                "items": {"type": "string"},
            },
            "lecture_ref": {"type": "string"},
            "question_text": {"type": "string"},
            "data_table": {"type": ["string", "null"]},
            "solution": {
                "type": "object",
                "required": sol_required,
                "properties": {
                    "text": {"type": "string"},
                    "key_formula": {"type": ["string", "null"]},
                    "numerical_answer": {"type": ["string", "null"]},
                    "common_mistakes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            "hints": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": cfg["solution_constraints"].get("hints_min", 2),
                "maxItems": cfg["solution_constraints"].get("hints_max", 3),
            },
            "related_exercises": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }

    # Add session_title_{lang} property for each configured language
    for lang in languages:
        schema["properties"][f"session_title_{lang}"] = {"type": "string"}

    # Add software_code field if a software_tool is configured.
    # The field name is always "software_code" regardless of the tool;
    # cfg["software_tool"] tells the generator which tool to use *inside* the field.
    if cfg.get("software_tool"):
        schema["properties"]["software_code"] = {"type": ["string", "null"]}

    return schema


def main():
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    out_dir = get_output_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)
    schema = build_schema(cfg)
    schema_path = out_dir / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Schema written to {schema_path}")


if __name__ == "__main__":
    main()
