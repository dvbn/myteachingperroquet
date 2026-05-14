# Claude Prompt: Inventory Audit

You are Claude Opus 4.7 acting as an independent corpus auditor.

Do not edit files.

Inspect the raw course resources and proposed source inventory.

Return concise Markdown with:

- missing or duplicated source groups;
- likely canonical sources;
- likely authoring-only sources;
- likely quarantine sources and reasons;
- risks that require human review;
- no more than 10 concrete recommendations.

Never propose bulk ingestion of risky folders. Prefer targeted admission with
visible provenance tags.

