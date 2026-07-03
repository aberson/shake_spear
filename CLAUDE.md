# shake_spear — Workshop instructions

## Project overview

A markdown-first creative writing workshop: shared AI prompt skills + templates + a
small stdlib-only CLI (`ss`), with independent story subprojects under `projects/`
that each open standalone in VS Code. The AI acts as coach/scene-partner/editor via
the skill files — it does not write the stories by default and the code never calls
an AI API. Full spec: [`plan.md`](plan.md); normative skill/template bodies:
[`docs/seed.md`](docs/seed.md).

## Working in this repo (AI ground rules)

- **This is a creative writing workshop.** Do not treat prose as code — never "lint",
  reformat, or normalize the writer's prose (`drafts/`, story files). Ordinary
  engineering rules apply only to `src/`, `tests/`, and `pyproject.toml`.
- **Preserve drafts.** Never overwrite or delete creative writing unless explicitly
  asked; prefer creating new revision files over destructive edits.
- **Shared prompt skills live in `skills/`** (source of truth; catalog in
  `skills/README.md`). The slash wrappers under `.claude/skills/` only point there.
- **Story projects live in `projects/`** — each opens standalone with `code .` and
  carries local context: `story_bible.md`, `active_state.md`, `continuity.md`,
  `decisions.md`, `index.md`.
- **When assisting with a story, read those local story files FIRST**, before giving
  any advice.
- **Feedback default:** the `skills/quick_feedback.md` format, unless the user asks
  for deep critique.
- **Drafting default:** ASK whether the user wants a plan, sample prose, or coaching —
  do not just write prose for them.
- **Never imitate living authors.** Use craft traits and genre traits instead.

## Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ (stdlib-only runtime) |
| Packaging | uv (`pyproject.toml`; `pip install -e .` also works) |
| CLI | `ss` (`[project.scripts]` → `shake_spear.cli:main`) |
| Tests | pytest (tmp_path-based, no mocks) |
| Lint/type | ruff + mypy |
| Writing assets | Markdown + hand-rolled frontmatter (no YAML dep) |

## Commands

- `uv sync` — install/refresh the environment
- `uv run ss --help` — CLI entry point
- `uv run ss new-story "Title" --slug s --genre g` — scaffold a story project
- `uv run ss session <project> --type scene --minutes 45` — start a session log
- `uv run ss index <project>` — regenerate a story's derived index.md
- `uv run ss recap <project>` — update the recap marker block in active_state.md
- `uv run pytest` — test suite
- `uv run ruff check .` — lint
- `uv run mypy src` — typecheck

No ports; nothing listens on the network.

## Directory layout

```text
src/shake_spear/     # cli, utils, scaffold, creators, session, indexer
skills/              # 14 tool-agnostic prompt skills (source of truth)
.claude/skills/      # thin slash-invocable wrappers over skills/*.md
templates/           # 14 markdown templates ({{placeholder}} tokens)
projects/_template/  # pristine story skeleton (committed)
projects/example_kids_story/  # committed worked example
projects/<story>/    # real stories — gitignored, each its OWN git repo
tests/               # pytest suite incl. end-to-end smoke gate
docs/seed.md         # original seed spec (normative for skill/template bodies)
```

## Architecture summary

One workshop root, many story folders. The CLI is thin file plumbing: `utils.py` owns
the four invariants (slugify, frontmatter grammar, safe_write collision/backup policy,
story/workshop root detection) and everything else renders templates through it.
Derived files (`index.md`, `exports/manuscript.md`) regenerate freely; every other
file is operator-owned — named-entity generators refuse to overwrite without
`--force` (which still writes a `.bak-` copy first), while dated session logs
auto-suffix `_b`/`_c` instead. `ss recap` only rewrites the
`<!-- ss:recap:start/end -->` block. Git model: this repo is public; real stories are
nested per-story private repos (`ss new-story` runs `git init`), individually
flippable to public.

## Current state

Steps 1–5 of the v1 build are complete: repo scaffold, 14 templates, 14 shared
skills + `skills/README.md`, root guides + 14 slash wrappers. Next: Steps 6–14
(the `ss` CLI — utils/scaffold/creators/session/indexer — README, example story,
smoke gate) + M1 UAT. See `plan.md` §11.

## Environment requirements

- Windows 11 primary (WSL optional, unsupported target for v1); cross-platform paths
  via `pathlib`; all I/O `encoding="utf-8"`, `newline="\n"` (no BOM, no CRLF writes).
- Python 3.11+ and uv (or plain venv+pip).
- git on PATH for `ss new-story`'s story-repo init (degrades gracefully without).
- No API keys, no secrets, no network access.
