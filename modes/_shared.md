# _shared — Global scoring rules, tools, and ATS-track router

## Scoring dimensions (10, weights sum to 1.0)

| Dimension | Weight | A (5) | F (1) |
|-----------|--------|-------|-------|
| role_fit | 0.20 | Exact title + scope | Tangentially related |
| comp | 0.15 | ≥ target range | Below floor |
| remote_policy | 0.12 | Matches preference | Hard opposite |
| level_fit | 0.12 | Exact seniority | Under/over by ≥2 levels |
| tech_stack_match | 0.12 | ≥80% CV overlap | ≤20% overlap |
| growth | 0.10 | Clear ML/data focus | No signal |
| company_quality | 0.08 | Strong brand/stage fit | Declining or unknown |
| learning_value | 0.06 | Novel scope | Repetition |
| leadership_signal | 0.03 | Explicit lead/mentor | IC-only |
| geographic_fit | 0.02 | Home metro or remote | Relocation req. |

## Kill signals (auto-reject regardless of score)

- `sponsorship_required: true` AND `profile.yml: sponsorship_available: false`
- `comp_range_max` < `profile.yml: comp.min_floor`
- Location outside `profile.yml: allowed_locations` and no remote
- Explicit excluded keyword from `profile.yml: deal_breakers[]`

## ATS track router

After scoring, the Scorer selects DA / MLE / DE. The Tailor reads `cv/{track}.md`.

## Python orchestrator

From Phase 1, `/apply` dispatches to the Python bridge. This file documents the evaluation
logic the Scorer agent implements; the Claude Code `apply` mode is now a bridge dispatcher.
See `modes/apply.md` and `bridge/server.py`.
