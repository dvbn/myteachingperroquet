# Pipeline: Netlify Deployment

Use this after TA ingestion has passed locally and the instructor wants a
preview or production deployment.

## Inputs

```text
phase3-ta-llm-system/
```

## Steps

1. Confirm TA ingestion approval at
   `courses/<course_id>/phase3-output/ingestion/APPROVAL.json`.
2. Confirm access policy: password required or public.
3. Confirm environment variables and budget settings.
4. Run local build commands again if data changed.
5. Deploy preview.
6. Ask the instructor to test the preview.
7. Stop for preview approval at
   `courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json`.
8. Deploy production only after approval at
   `courses/<course_id>/phase3-output/production/APPROVAL.json`.

## Required Environment Variables

At minimum:

- `OPENAI_API_KEY` for embeddings and query embeddings.
- Runtime LLM provider key such as `MISTRAL_API_KEY`, `ANTHROPIC_API_KEY`, or `LLM_API_KEY`.
- `JWT_SECRET`.
- `COURSE_ID`.
- `TA_CHAT_PASSWORD` when auth is required.
- `ALLOWED_ORIGIN` for production.

See `phase3-ta-llm-system/README.md` for the current full list.

## Commands

```bash
cd phase3-ta-llm-system
npm run preflight
npm run chunk
npm run transform
npm run rebuild
npm run vectors
netlify deploy
netlify deploy --prod
```

Do not run `netlify deploy --prod` without explicit production approval at
`courses/<course_id>/phase3-output/production/APPROVAL.json`.
