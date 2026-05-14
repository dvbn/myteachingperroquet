#!/usr/bin/env python3
"""Scaffold a local course workflow bundle from templates."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"


TEXT_TEMPLATES = [
    "USER_GUIDE.template.md",
    "VERIFICATION.template.md",
    "SOURCE_NOTES.template.md",
    "ASSESSMENT_STYLE_AUDIT.template.md",
    "DEPLOYMENT.template.md",
    "PRIVACY.template.md",
    "COST_NOTES.template.md",
]

APPROVAL_GATES = [
    ("APPROVAL.setup.json", "setup"),
    ("phase1-output/APPROVAL.json", "phase1"),
    ("phase2-output/smoke/APPROVAL.json", "phase2-smoke"),
    ("phase2-output/full/APPROVAL.json", "phase2-full"),
    ("phase3-output/ingestion/APPROVAL.json", "phase3-ingestion"),
    ("phase3-output/deployment-preview/APPROVAL.json", "deployment-preview"),
    ("phase3-output/production/APPROVAL.json", "production"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a course workflow bundle")
    parser.add_argument("--course-id", required=True, help="Stable course ID/slug")
    parser.add_argument(
        "--courses-dir",
        default="courses",
        help="Root directory for local course bundles",
    )
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="Existing raw source directory. If omitted, creates <course>/raw.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing template-derived files",
    )
    return parser.parse_args()


def write_text_from_template(template: Path, out_path: Path, course_id: str, overwrite: bool) -> None:
    if out_path.exists() and not overwrite:
        return
    text = template.read_text(encoding="utf-8").replace("<course_id>", course_id)
    out_path.write_text(text, encoding="utf-8")


def write_workflow_config(course_dir: Path, course_id: str, raw_dir: Path, overwrite: bool) -> None:
    out_path = course_dir / "workflow_config.json"
    if out_path.exists() and not overwrite:
        return

    template_path = TEMPLATES / "WORKFLOW_CONFIG.template.json"
    data = json.loads(template_path.read_text(encoding="utf-8"))
    data["course"]["course_id"] = course_id
    data["paths"]["raw_dir"] = str(raw_dir)
    data["paths"]["phase1_output"] = str(course_dir / "phase1-output")
    data["paths"]["phase2_smoke_output"] = str(course_dir / "phase2-output" / "smoke")
    data["paths"]["phase2_full_output"] = str(course_dir / "phase2-output" / "full")
    data["paths"]["phase3_ingestion_output"] = str(course_dir / "phase3-output" / "ingestion")
    data["paths"]["deployment_preview_output"] = str(course_dir / "phase3-output" / "deployment-preview")
    data["paths"]["production_output"] = str(course_dir / "phase3-output" / "production")
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_approval_gates(course_dir: Path, overwrite: bool) -> None:
    template_path = TEMPLATES / "APPROVAL.template.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))

    for relative_path, phase in APPROVAL_GATES:
        out_path = course_dir / relative_path
        if out_path.exists() and not overwrite:
            continue
        out_path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(template)
        data["phase"] = phase
        data["status"] = "pending"
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    courses_dir = Path(args.courses_dir)
    course_dir = courses_dir / args.course_id
    raw_dir = Path(args.raw_dir) if args.raw_dir else course_dir / "raw"

    course_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    (course_dir / "phase1-output").mkdir(exist_ok=True)
    (course_dir / "phase2-output" / "smoke").mkdir(parents=True, exist_ok=True)
    (course_dir / "phase2-output" / "full").mkdir(parents=True, exist_ok=True)
    (course_dir / "phase3-output" / "ingestion").mkdir(parents=True, exist_ok=True)
    (course_dir / "phase3-output" / "deployment-preview").mkdir(parents=True, exist_ok=True)
    (course_dir / "phase3-output" / "production").mkdir(parents=True, exist_ok=True)

    write_workflow_config(course_dir, args.course_id, raw_dir, args.overwrite)
    write_approval_gates(course_dir, args.overwrite)

    for template_name in TEXT_TEMPLATES:
        template_path = TEMPLATES / template_name
        out_name = template_name.replace(".template", "")
        write_text_from_template(template_path, course_dir / out_name, args.course_id, args.overwrite)

    branding_template = TEMPLATES / "BRANDING.template.json"
    branding_out = course_dir / "branding.json"
    if not branding_out.exists() or args.overwrite:
        shutil.copyfile(branding_template, branding_out)

    print(f"Scaffolded course bundle: {course_dir}")
    print(f"Raw source directory: {raw_dir}")
    print("Next: add sources, then ask an agent to run the selected pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
