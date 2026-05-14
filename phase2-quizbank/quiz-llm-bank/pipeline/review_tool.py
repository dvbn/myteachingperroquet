#!/usr/bin/env python3
"""Exercise Bank Review Tool (config-driven).

CLI helper for reviewing exercises via Claude Code.
Reads session structure from course_config.json instead of hardcoded paths.

Usage:
  python review_tool.py next [--session S4] [--lang EN] [--type MATH] [--difficulty HARD]
  python review_tool.py show <exercise_id>
  python review_tool.py approve <exercise_id> [--comment "..."]
  python review_tool.py flag <exercise_id> --comment "..."
  python review_tool.py reject <exercise_id> --comment "..."
  python review_tool.py edit <exercise_id> --comment "..." [--new-status pending]
  python review_tool.py progress [--verbose]
  python review_tool.py flagged
  python review_tool.py rejected
  python review_tool.py apply-delete <exercise_id> [--dry-run]
  python review_tool.py reset <exercise_id>
"""

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files, get_languages


def _cfg():
    return load_config()


def _review_log_path():
    return get_output_dir(_cfg()) / "review_log.json"


def load_review_log():
    p = _review_log_path()
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_review_log(log):
    p = _review_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_all_exercises(session=None, lang=None, qtype=None, difficulty=None):
    """Load exercises from JSON files, optionally filtered."""
    cfg = _cfg()
    out_dir = get_output_dir(cfg)
    session_dirs = get_session_dirs(cfg)
    json_files = get_json_files(cfg)
    exercises = []

    # Case-insensitive session lookup: match user input against config keys
    if session:
        session_key = next(
            (k for k in session_dirs if k.upper() == session.upper()), session
        )
        sessions = [session_key]
    else:
        sessions = list(session_dirs.keys())
    all_langs = [l.upper() for l in get_languages(cfg)]
    langs_filter = [lang.upper()] if lang else all_langs

    for sn in sessions:
        sdir = session_dirs.get(sn)
        if not sdir:
            continue
        for jf in json_files:
            # Filter by language if specified
            jf_lang = jf.split("_")[1].split(".")[0].upper()
            if jf_lang not in langs_filter:
                continue
            fp = out_dir / sdir / jf
            if not fp.exists():
                continue
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            for ex in data:
                if qtype and ex.get("question_type", "").upper() != qtype.upper():
                    continue
                if difficulty and ex.get("difficulty", "").upper() != difficulty.upper():
                    continue
                ex["_source_file"] = str(fp)
                exercises.append(ex)
    return exercises


def format_exercise(ex):
    """Format an exercise for terminal display."""
    lines = []
    lines.append(f"## {ex['id']}")
    cfg = _cfg()
    title_parts = [ex.get(f"session_title_{l}", "") for l in get_languages(cfg)]
    lines.append(f"**Session:** {ex['session']} — {' / '.join(t for t in title_parts if t)}")
    lines.append(f"**Type:** {ex['question_type']} | **Difficulty:** {ex['difficulty']} | **Language:** {ex['language'].upper()}")
    lines.append(f"**Topics:** {', '.join(ex.get('topics', []))}")
    if ex.get("prerequisites"):
        lines.append(f"**Prerequisites:** {', '.join(ex['prerequisites'])}")
    lines.append("")
    lines.append("### Question")
    lines.append(ex["question_text"])
    if ex.get("data_table"):
        lines.append("\n**Data:**")
        lines.append(ex["data_table"])
    lines.append("")
    lines.append("### Solution")
    sol = ex.get("solution", {})
    lines.append(sol.get("text", "(no solution)"))
    if sol.get("key_formula"):
        lines.append(f"\n**Key formula:** {sol['key_formula']}")
    if sol.get("numerical_answer"):
        lines.append(f"**Numerical answer:** {sol['numerical_answer']}")
    if sol.get("common_mistakes"):
        lines.append("\n**Common mistakes:**")
        for cm in sol["common_mistakes"]:
            lines.append(f"- {cm}")
    lines.append("")
    lines.append("### Hints")
    for i, h in enumerate(ex.get("hints", []), 1):
        lines.append(f"{i}. {h}")
    if ex.get("related_exercises"):
        lines.append(f"\n**Related:** {', '.join(ex['related_exercises'])}")
    lines.append(f"**Twin:** {ex.get('twin_id', 'N/A')}")
    return "\n".join(lines)


def cmd_next(args):
    log = load_review_log()
    exercises = load_all_exercises(
        session=args.session, lang=args.lang,
        qtype=args.type, difficulty=args.difficulty
    )
    if not args.all:
        exercises = [ex for ex in exercises if ex["id"] not in log]
    if not exercises:
        print("No unreviewed exercises match the filters.")
        print(f"Total reviewed: {len(log)}")
        return
    ex = random.choice(exercises)
    print(format_exercise(ex))
    remaining = len(exercises) - 1
    total = len(load_all_exercises(session=args.session, lang=args.lang, qtype=args.type, difficulty=args.difficulty))
    reviewed = total - len(exercises)
    print(f"\n---\n**Progress:** {reviewed}/{total} reviewed ({remaining} remaining with current filters)")


def cmd_show(args):
    exercises = load_all_exercises()
    for ex in exercises:
        if ex["id"] == args.exercise_id:
            print(format_exercise(ex))
            log = load_review_log()
            if args.exercise_id in log:
                entry = log[args.exercise_id]
                print(f"\n**Review status:** {entry['status']}")
                if entry.get("comment"):
                    print(f"**Comment:** {entry['comment']}")
                print(f"**Reviewed:** {entry['timestamp']}")
            return
    print(f"Exercise '{args.exercise_id}' not found.")
    sys.exit(1)


def cmd_log_decision(args, status):
    log = load_review_log()
    entry = {
        "status": status,
        "comment": args.comment or "",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    if args.exercise_id in log:
        prev = log[args.exercise_id]
        entry["previous_status"] = prev["status"]
        entry["previous_comment"] = prev.get("comment", "")
    log[args.exercise_id] = entry
    save_review_log(log)

    # Also log the twin
    exercises = load_all_exercises()
    twin_id = None
    for ex in exercises:
        if ex["id"] == args.exercise_id:
            twin_id = ex.get("twin_id")
            break
    if twin_id and twin_id not in log:
        twin_entry = {
            "status": status,
            "comment": f"[auto-synced from {args.exercise_id}] {args.comment or ''}".strip(),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        log[twin_id] = twin_entry
        save_review_log(log)
        print(f"Logged: {args.exercise_id} -> {status}")
        print(f"Synced: {twin_id} -> {status}")
    else:
        print(f"Logged: {args.exercise_id} -> {status}")
    if args.comment:
        print(f"Comment: {args.comment}")


def cmd_progress(args):
    log = load_review_log()
    all_exercises = load_all_exercises()
    counts = {"approved": 0, "flagged": 0, "rejected": 0}
    for entry in log.values():
        s = entry["status"]
        counts[s] = counts.get(s, 0) + 1

    total = len(all_exercises)
    reviewed = len(log)
    print("## Review Progress\n")
    print(f"**Total exercises:** {total}")
    print(f"**Reviewed:** {reviewed}/{total} ({100 * reviewed / total:.0f}%)" if total else "**Reviewed:** 0")
    print(f"  - Approved: {counts['approved']}")
    print(f"  - Flagged: {counts['flagged']}")
    print(f"  - Rejected: {counts['rejected']}")
    print(f"**Remaining:** {total - reviewed}")

    if args.verbose:
        cfg = _cfg()
        session_dirs = get_session_dirs(cfg)
        print("\n### By Session\n")
        print(f"{'Session':<8} {'Total':>6} {'Reviewed':>9} {'Approved':>9} {'Flagged':>8} {'Rejected':>9}")
        print("-" * 55)
        for sn in session_dirs:
            s_exercises = load_all_exercises(session=sn)
            s_total = len(s_exercises)
            s_approved = sum(1 for ex in s_exercises if log.get(ex["id"], {}).get("status") == "approved")
            s_flagged = sum(1 for ex in s_exercises if log.get(ex["id"], {}).get("status") == "flagged")
            s_rejected = sum(1 for ex in s_exercises if log.get(ex["id"], {}).get("status") == "rejected")
            s_reviewed = s_approved + s_flagged + s_rejected
            print(f"{sn:<8} {s_total:>6} {s_reviewed:>9} {s_approved:>9} {s_flagged:>8} {s_rejected:>9}")


def cmd_flagged(args):
    log = load_review_log()
    flagged = {eid: e for eid, e in log.items() if e["status"] == "flagged"}
    if not flagged:
        print("No flagged exercises.")
        return
    print(f"## Flagged Exercises ({len(flagged)})\n")
    for eid, entry in sorted(flagged.items()):
        print(f"- **{eid}**: {entry.get('comment', '(no comment)')}")


def cmd_rejected(args):
    log = load_review_log()
    rejected = {eid: e for eid, e in log.items() if e["status"] == "rejected"}
    if not rejected:
        print("No rejected exercises.")
        return
    print(f"## Rejected Exercises ({len(rejected)})\n")
    for eid, entry in sorted(rejected.items()):
        print(f"- **{eid}**: {entry.get('comment', '(no comment)')}")


def cmd_apply_delete(args):
    cfg = _cfg()
    out_dir = get_output_dir(cfg)
    session_dirs = get_session_dirs(cfg)
    log = load_review_log()
    eid = args.exercise_id

    if eid not in log or log[eid]["status"] != "rejected":
        print(f"Error: {eid} is not in 'rejected' status. Cannot delete.")
        sys.exit(1)

    exercises = load_all_exercises()
    target = None
    twin_id = None
    for ex in exercises:
        if ex["id"] == eid:
            target = ex
            twin_id = ex.get("twin_id")
            break
    if not target:
        print(f"Error: {eid} not found in exercise files.")
        sys.exit(1)

    ids_to_delete = [eid]
    if twin_id:
        ids_to_delete.append(twin_id)

    if args.dry_run:
        print(f"[DRY RUN] Would delete: {', '.join(ids_to_delete)}")
        return

    for sn, sdir in session_dirs.items():
        for jf in get_json_files(cfg):
            fp = out_dir / sdir / jf
            if not fp.exists():
                continue
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            original_len = len(data)
            data = [ex for ex in data if ex["id"] not in ids_to_delete]
            if len(data) < original_len:
                for ex in data:
                    if ex.get("related_exercises"):
                        ex["related_exercises"] = [
                            r for r in ex["related_exercises"] if r not in ids_to_delete
                        ]
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                removed = original_len - len(data)
                print(f"Removed {removed} exercise(s) from {fp.name}")

    for did in ids_to_delete:
        if did in log:
            log[did]["status"] = "deleted"
            log[did]["deleted_at"] = datetime.now().isoformat(timespec="seconds")
    save_review_log(log)
    print(f"Deleted: {', '.join(ids_to_delete)}")


def cmd_reset(args):
    log = load_review_log()
    eid = args.exercise_id
    if eid in log:
        del log[eid]
        save_review_log(log)
        print(f"Reset: {eid} is now unreviewed.")
    else:
        print(f"{eid} was not in the review log.")


def cmd_edit(args):
    log = load_review_log()
    eid = args.exercise_id
    if eid not in log:
        print(f"{eid} has not been reviewed yet.")
        sys.exit(1)
    if args.comment:
        log[eid]["comment"] = args.comment
    if args.new_status:
        log[eid]["previous_status"] = log[eid]["status"]
        log[eid]["status"] = args.new_status
    log[eid]["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_review_log(log)
    print(f"Updated: {eid} -> status={log[eid]['status']}, comment={log[eid].get('comment', '')}")


def main():
    parser = argparse.ArgumentParser(description="Exercise Bank Review Tool")
    sub = parser.add_subparsers(dest="command")

    p_next = sub.add_parser("next", help="Pick a random unreviewed exercise")
    p_next.add_argument("--session", help="Filter by session (e.g. S4)")
    p_next.add_argument("--lang", help="Filter by language code")
    p_next.add_argument("--type", help="Filter by question type")
    p_next.add_argument("--difficulty", help="Filter by difficulty level")
    p_next.add_argument("--all", action="store_true", help="Include already-reviewed exercises")

    p_show = sub.add_parser("show", help="Show a specific exercise")
    p_show.add_argument("exercise_id")

    p_approve = sub.add_parser("approve", help="Approve an exercise")
    p_approve.add_argument("exercise_id")
    p_approve.add_argument("--comment", default="")

    p_flag = sub.add_parser("flag", help="Flag an exercise for modification")
    p_flag.add_argument("exercise_id")
    p_flag.add_argument("--comment", required=True)

    p_reject = sub.add_parser("reject", help="Reject an exercise")
    p_reject.add_argument("exercise_id")
    p_reject.add_argument("--comment", required=True)

    p_edit = sub.add_parser("edit", help="Update a review decision")
    p_edit.add_argument("exercise_id")
    p_edit.add_argument("--comment")
    p_edit.add_argument("--new-status", choices=["approved", "flagged", "rejected"])

    p_progress = sub.add_parser("progress", help="Show review progress")
    p_progress.add_argument("--verbose", "-v", action="store_true")

    sub.add_parser("flagged", help="List flagged exercises")
    sub.add_parser("rejected", help="List rejected exercises")

    p_del = sub.add_parser("apply-delete", help="Delete a rejected exercise from JSON files")
    p_del.add_argument("exercise_id")
    p_del.add_argument("--dry-run", action="store_true")

    p_reset = sub.add_parser("reset", help="Remove a review decision")
    p_reset.add_argument("exercise_id")

    args = parser.parse_args()

    commands = {
        "next": cmd_next,
        "show": cmd_show,
        "approve": lambda a: cmd_log_decision(a, "approved"),
        "flag": lambda a: cmd_log_decision(a, "flagged"),
        "reject": lambda a: cmd_log_decision(a, "rejected"),
        "edit": cmd_edit,
        "progress": cmd_progress,
        "flagged": cmd_flagged,
        "rejected": cmd_rejected,
        "apply-delete": cmd_apply_delete,
        "reset": cmd_reset,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
