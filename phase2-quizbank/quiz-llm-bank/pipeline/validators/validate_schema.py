#!/usr/bin/env python3
"""Phase 2 validator: JSON schema conformance.

Validates every exercise JSON file against the generated schema.json.
Exit code 0 = PASS (0 CRITICALs), 1 = FAIL.

Flags:
  --findings-output <path>  Write structured findings JSON alongside markdown.
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files
from findings_io import FindingCollector


def _parse_args():
    findings_output = None
    config_path = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--findings-output" and i + 1 < len(args):
            findings_output = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            config_path = args[i]
            i += 1
        else:
            i += 1
    return config_path, findings_output


def main():
    config_path, findings_output = _parse_args()
    cfg = load_config(config_path)
    out_dir = get_output_dir(cfg)
    schema_path = out_dir / "schema.json"
    collector = FindingCollector(source="validator_schema")

    if not schema_path.exists():
        print(f"CRITICAL: schema.json not found at {schema_path}")
        collector.add("critical", "schema", "_global",
                       f"schema.json not found at {schema_path}",
                       blocking=True)
        if findings_output:
            collector.write(findings_output)
        sys.exit(1)

    try:
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"CRITICAL: cannot load schema.json: {e}")
        collector.add("critical", "schema", "_global",
                       f"Cannot load schema.json: {e}",
                       evidence=f"path={schema_path}, error={e}",
                       blocking=True)
        if findings_output:
            collector.write(findings_output)
        sys.exit(1)

    json_files = get_json_files(cfg)
    session_dirs = get_session_dirs(cfg)
    criticals = 0
    warnings = 0
    total = 0

    print("# Schema Validation Report\n")

    for sid, sdir in session_dirs.items():
        for jf in json_files:
            fp = out_dir / sdir / jf
            if not fp.exists():
                continue

            with open(fp, encoding="utf-8") as f:
                try:
                    exercises = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"### CRITICAL {fp.name}: Invalid JSON — {e}")
                    collector.add("critical", "schema", f"_session:{sid}",
                                   f"Invalid JSON in {fp.name}: {e}",
                                   evidence=str(e), session_id=sid)
                    criticals += 1
                    continue

            if not isinstance(exercises, list):
                print(f"### CRITICAL {fp.name}: Root element is not an array")
                collector.add("critical", "schema", f"_session:{sid}",
                               f"Root element is not an array in {fp.name}",
                               evidence=f"file={fp.name}, type={type(exercises).__name__}",
                               session_id=sid)
                criticals += 1
                continue

            for ex in exercises:
                total += 1
                eid = ex.get("id", f"unknown_{total}")
                try:
                    jsonschema.validate(ex, schema)
                except jsonschema.ValidationError as e:
                    field = ".".join(str(p) for p in e.absolute_path) or "(root)"
                    print(f"### CRITICAL Exercise {eid} ({fp.name})")
                    print(f"- **Field**: {field}")
                    print(f"- **Issue**: {e.message}\n")
                    collector.add("critical", "schema", eid,
                                   f"Schema violation at field '{field}': {e.message}",
                                   evidence=f"field={field}, value={e.instance!r}"[:500],
                                   recommended_fix=f"Fix field '{field}' to conform to schema",
                                   session_id=sid)
                    criticals += 1

    print(f"\n## Summary")
    print(f"- Exercises validated: {total}")
    print(f"- CRITICALs: {criticals}")
    print(f"- WARNINGs: {warnings}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
