# Lanes

Standing lanes for this project (Passing Notes id `shake-spear`). Shared rules:
[passing-notes lane rules](https://github.com/aberson/passing-notes/blob/HEAD/docs/lane-rules.md).
This file adds only local rules and never weakens them.

```text
Lanes:           central - coordinate, ship, relay the operator (also coordinates alpha4gate and career-ops)
                 skill-mesh - Medium article on Skill Mesh v3, in projects/dev_dispatches
                 np-finance - general Medium article on np-finance, in projects/dev_dispatches
Coordinator:     central   (records lanes and confirms ownership transfers)
Shipper:         central   (merges and pushes)
Operator relay:  central
Lane rules:      passing-notes docs/lane-rules.md, plus the project rules below
```

## Ownership

| Lane | Owns |
|---|---|
| central | Workshop shared files (`docs/plans/`, `docs/lanes/`, `CLAUDE.md`, `AGENTS.md`, `README.md`, `pyproject.toml`, `uv.lock`); `projects/dev_dispatches` shared story files (`active_state.md`, `continuity.md`, `decisions.md`, `index.md`, `story_bible.md`, `scenes/series_plan_*`, `exports/reading/`); all commits and pushes |
| skill-mesh | `projects/dev_dispatches/research/skill_mesh_v3/`, `scenes/skill_mesh_v3_article_seed.md`, `feedback/skill_mesh_v3_factcheck_*.md` |
| np-finance | `projects/dev_dispatches/research/np_finance/`, `scenes/np_finance_article_seed.md` |

## Project rules

- `central` took over from `main` on 2026-11-16 at the operator's request (handover
  from the closed `main` lane). `main` is closed; send coordinator, relay and shipping
  notes to `central`.
- Lanes send edits to central-owned story files as notes to `central`; they do not edit
  them directly.
