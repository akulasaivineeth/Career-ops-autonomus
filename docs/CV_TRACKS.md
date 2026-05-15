# CV Tracks

Fill in `cv/da.md`, `cv/mle.md`, and `cv/de.md` with your real experience.

## Rules
- **Never fabricate** skills, companies, dates, or numbers.
- The Tailor agent strengthens bullet relevance but never adds claims not already present.
- The Scorer picks the best-matching track per JD; you can override via `profile.yml → tracks.preferred`.

## Authoring tips
- Keep bullets **quantified**: use %, $, users, ms, GB.
- List skills your CV can actually back up under the experience section.
- Add `certifications:` entries only if verifiable.

## How the agent reads them
At Tailor time: agent loads `cv/{track}.md`, rewrites up to 8 bullets to highlight `tailor_keywords` from the Scorer, **preserving every factual claim**, then passes the tailored markdown to `generate-pdf.mjs`.
