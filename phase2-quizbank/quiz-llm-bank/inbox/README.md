# inbox/ — drop your course materials here

This is where you put the slides and other materials the AI assistant
will read when generating exercises. The pipeline only **reads** this
folder — it never writes to it, so your originals are safe.

## What goes where

```
inbox/
  Slides/
    S1/   ← put session 1's slide files here
    S2/
    S3/
    ...
  Exercises/   ← (optional) any past exercises you want to use as style examples
  Syllabus/    ← (optional) the course syllabus or outline
```

The session folder names (`S1`, `S2`, etc.) match the session IDs in
your course config. When you talk through Step 2 of the main README,
the assistant will help you pick those.

## What format the slides should be in

Markdown (`.md`) files are the simplest and most reliable.

If your slides are in **PDF** or **PowerPoint**, just tell the assistant
— it can convert them for you. ("Here are my PDF slides for sessions 1
through 5; please convert them.")

A few quality tips that help the AI generate better exercises:

- One topic per file is fine; multiple files per session is also fine.
  The assistant will read all of them together.
- Keep section headings (`##`, `###`) intact — the AI uses them to
  understand the structure of each session.
- Mathematical notation in standard LaTeX (`$ ... $`) preserves best.

## How big is too big?

Each session's combined slide content is capped at roughly 50,000 words.
That's plenty for most courses. If you have an unusually large session
(say, 100+ slides combined), the assistant will warn you and offer to
either split it or trim down to the most useful slides.

## What if my slides mention a concept that's taught later?

That's a common situation: an early session briefly says "we'll cover X
in week 8". The repo handles this safely — the AI generator is told to
ignore those forward references, so you won't get an exercise about X
in week 1. You don't need to scrub your slides.
