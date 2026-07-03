# shake_spear — Workshop instructions

## Project overview

A markdown-first creative writing workshop: shared AI prompt skills + templates + a
small stdlib-only CLI (`ss`), with independent story subprojects under `projects/`
that each open standalone in VS Code. The AI acts as coach/scene-partner/editor via
the skill files — it does not write the stories by default and the code never calls
an AI API. Full spec: [`plan.md`](plan.md); normative skill/template bodies:
[`docs/seed.md`](docs/seed.md).

**This is a prose-first repo.** Do not treat prose as code. Never overwrite or delete
creative writing (`drafts/`, story files) — prefer new revision files. When helping
with a story, read its local `story_bible.md`, `active_state.md`, `continuity.md`,
`decisions.md`, `index.md` first. Never imitate living authors; use craft traits.

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

Plan written (`plan.md`, 2026-07-02), no code yet. Next: `/repo-init` →
`/plan-expedite --plan plan.md` → `/build-phase` (14 automated steps + M1 UAT).

## Environment requirements

- Windows 11 primary (WSL optional, unsupported target for v1); cross-platform paths
  via `pathlib`; all I/O `encoding="utf-8"`, `newline="\n"` (no BOM, no CRLF writes).
- Python 3.11+ and uv (or plain venv+pip).
- git on PATH for `ss new-story`'s story-repo init (degrades gracefully without).
- No API keys, no secrets, no network access.
