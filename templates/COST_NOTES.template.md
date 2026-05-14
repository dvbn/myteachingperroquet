# Cost Notes

Course: `<course_id>`

## One-Time Build Costs

- Phase 2 quiz generation agent/subscription:
- Phase 2 quiz verification agent/subscription:
- Phase 3 vector embeddings API (`OPENAI_API_KEY` by default):

## Runtime Costs

- Setup-time budget profile:
- TA chat/query model API (`MISTRAL_API_KEY` by default, or Anthropic/OpenAI/Groq override):
- Per-query embedding API (`OPENAI_API_KEY`):
- Hosting:

## Budget Controls

- Daily budget:
- Requests per minute:
- Messages per session:
- Auth required:

## Cost-Saving Options

- Run monolingual first.
- Use smoke generation before full generation.
- Reduce exercises per session.
- Use cheaper runtime model after quality testing.
- Keep quiz mode disabled until needed.
- Keep the Phase 2 generation/verifier model choice separate from the deployed
  TA runtime model choice.
