# Preflight Report

Course:

Date:

## Moreexercices Input

- [ ] `course_config.json` exists.
- [ ] Required config keys are present.
- [ ] `session.inbox_files` resolve to unified topic corpus files, or default
  `Slides` fallback resolves to unified topic corpus files.
- [ ] `session.example_files` resolve, or default `ExamExamples` fallback resolves.

Result:

## TA Input

- [ ] `data/course_config.json` validates against TA schema.
- [ ] `sources/SOURCES.md` exists.
- [ ] Lecture Markdown exists and chunks non-empty in dry-run.
- [ ] Lecture Markdown is unified by topic and not split by raw source/instructor.
- [ ] No authoring-only file appears under `sources/lectures`.
- [ ] No lecture filename triggers preflight false positives.

Result:

## Deferred Downstream Changes

- [ ] `DOWNSTREAM_CHANGE_REQUESTS.md` exists.
- [ ] Blocking requests are clearly marked.

Result:
