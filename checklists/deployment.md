# Deployment Checklist

Use this before preview and production deployment.

## Secrets And Environment

- Setup-time runtime choices are recorded: chat provider/model, embedding
  provider/model, deployment target, allowed origin, and budget profile.
- `.env.local` exists only locally and is not committed.
- Netlify environment variables are set for production.
- `JWT_SECRET` is strong and not default.
- `TA_CHAT_PASSWORD` is set when auth is required.
- `ALLOWED_ORIGIN` is not `*` for private courses.
- API keys are scoped and rotated if exposed.

## Privacy And Access

- Public/private access policy is confirmed.
- No private source excerpts, student data, active exams, or answer keys are
  exposed in public pages or bundled static assets.
- Instructor understands what data is sent to LLM and embedding providers.
- Cost/budget caps are configured.

## Functional Checks

- Local build passes after latest content copy.
- Preview deploy works.
- Chat answers cite/use intended course material.
- Quiz mode shows approved exercises only.
- Password flow works if enabled.
- Mobile and desktop widget behavior are acceptable.

## Production Approval

Do not run production deployment unless the instructor explicitly approves it.

Record:

- preview URL;
- preview gate: `courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json`;
- production gate: `courses/<course_id>/phase3-output/production/APPROVAL.json`;
- tested date;
- known residual risks;
- production approval status.
