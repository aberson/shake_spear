# shake_spear

A markdown-first creative writing workshop for VS Code. Shared AI prompt
skills, reusable templates, and a small stdlib-only CLI (`ss`) that scaffolds
and manages independent story projects — so you can sit down, open a story
folder, and be writing within minutes.

## What this is

shake_spear is a writing *practice* system, not a content mill. Everything you
write lives in plain markdown files on disk; the AI — guided by the prompt
files in [`skills/`](skills/README.md) — acts as a coach, scene partner, and
continuity assistant, and does not write your stories by default. The git
model matches: this workshop repo (tools, skills, templates) is public, while
each real story under `projects/` is its own private nested git repo that you
can flip public individually whenever you choose.

No web app, no database, no AI API calls. The product is the files.

## Install and run it locally

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
uv run ss --help
```

Or with a plain virtual environment and pip:

```bash
python -m venv .venv
# activate it:
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   macOS / Linux:         source .venv/bin/activate
pip install -e .
ss --help
```

The rest of this README writes bare `ss …` commands — on the uv path, prefix
them with `uv run` (e.g. `uv run ss new-story …`).

## Create a new story

```bash
ss new-story "Kids Space Bakery" --slug kids_space_bakery --genre kids --mode playful
```

- The title is the only required argument; `--slug` defaults to the slugified
  title (lowercase `a-z0-9_`).
- `--genre` and `--mode` are recorded in the story bible's frontmatter and
  steer the genre skills (e.g. kids vs. mystery).
- **Each new story becomes its own private git repo by default** — `ss
  new-story` runs `git init` plus an initial commit inside the new folder,
  and the workshop repo ignores it. Pass `--no-git` to skip; if git is not on
  your PATH the step is skipped with a notice.
- `--force` regenerates an existing project's generated files (timestamped
  `.bak-` backups are kept — your writing is never silently destroyed).

You get a complete story folder: `story_bible.md`, `active_state.md`,
`continuity.md`, `decisions.md`, a derived `index.md`, subfolders for scenes /
characters / world / drafts / sessions, and local AI guide files. Every
scaffolded story's own README maps the folders in detail.

## Explore the worked example

[`projects/example_kids_story/`](projects/example_kids_story/) is a complete
small story built with the real CLI: a filled story bible, two characters, two
world elements, two scene cards, a short draft, a session log, a generated
index, and a recap. Browse it to see what a living story project looks like
before you make your own.

## Start a writing session

```bash
ss session kids_space_bakery --type scene --minutes 45
ss daily kids_space_bakery
```

- `ss session` creates a dated log under `sessions/` with the frontmatter
  filled, a warm-start summary pulled from `active_state.md`, and links to the
  skills relevant to the session type.
- Defaults: `--type scene`, `--minutes 45`. Known types: `scene`, `revision`,
  `character`, `worldbuilding`, `dialogue`, `kids`, `mystery`, `freewrite`
  (free-form values are accepted and slugified into the filename).
- `ss daily` is sugar for a 15-minute freewrite session.
- The project argument is optional whenever your terminal is already inside a
  story folder — every command detects the story by walking up from the
  current directory. A second same-day session gets a `_b` suffix instead of
  refusing.

## Add a scene, character, or world element

```bash
ss scene kids_space_bakery "The bakery runs out of moon sugar"
ss character kids_space_bakery "Nova the baker"
ss world kids_space_bakery "Moon sugar"
```

Each command creates one markdown file from the matching template
(`scenes/…`, `characters/…`, `world/…`) with the title or name filled into the
frontmatter. If the file already exists the command refuses (exit code 2)
unless you pass `--force`, which keeps a timestamped `.bak-` backup first.

Story files carry `tags: []` frontmatter — the one-paragraph tag conventions
live in [`templates/story_project_README.md`](templates/story_project_README.md)
(and in every scaffolded story's README).

## Regenerate a story's index

```bash
ss index kids_space_bakery
```

`index.md` is a **derived** file: `ss index` rebuilds it from the story's
markdown files (story files, characters, world elements, scenes, drafts,
sessions, feedback, revisions, plus a top-10 recently-modified list). Never
edit it by hand — regenerate it whenever it drifts.

## Open a story directly with `code .`

```bash
cd projects/kids_space_bakery
code .
```

Every story works as a standalone VS Code workspace. The local `CLAUDE.md`
and `AGENTS.md` files inside the story help AI tools find the shared workshop
skills: they list the story's read-first files (`story_bible.md`,
`active_state.md`, `continuity.md`) and point at the shared skills two levels
up, and the story ships with its own `.claude/skills/` slash wrappers so
commands like `/immersive-session` and `/quick-feedback` work with the story
folder as the workspace root.

## Use the shared skills

The 14 shared skills in [`skills/`](skills/README.md) are plain markdown
instruction sets any AI assistant can follow. Three ways to invoke them:

1. **Claude Code at the workshop root** — each skill has a slash wrapper:
   `/quick-feedback`, `/immersive-session`, `/scene-planner`, …
2. **Any other assistant** — point it at the file (`Read
   skills/quick_feedback.md and apply it to the scene below.`) or paste the
   file's contents into the chat.
3. **Inside a story folder** — the story-local wrappers give you the same
   slash commands, or reference the shared files by relative path
   (`../../skills/…`).

The full catalog, the skeleton every skill shares, and per-context details
live in [`skills/README.md`](skills/README.md). Between sessions, `ss recap`
(refresh the "start here next time" block in `active_state.md`), `ss status`
(print it, writing nothing), and `ss export` (gather `drafts/` into
`exports/manuscript.md`) are the supporting loop.

## Your first writing exercise

Recommended first session once your first story exists — copy this into the
session and follow it:

```markdown
# First Writing Session: Tiny Scene

Open a new story project and start a 30–45 minute session.

Goal: write one small scene, not a chapter.

Prompt:

A character wants something simple, but another character misunderstands why it matters.

During the session:

1. Create a character profile.
2. Create a scene card.
3. Define the emotional turn.
4. Write 300–700 words.
5. Run quick feedback.
6. Update continuity.
7. Write the next tiny action.
```

## Development

- Tests: `uv run pytest` · lint: `uv run ruff check .` · types: `uv run mypy src`
- The full specification and build plan live in [`plan.md`](plan.md); the
  original seed spec is [`docs/seed.md`](docs/seed.md).
- In VS Code, `Terminal → Run Task…` exposes the common commands (new-story,
  session, index, recap, status, list-projects, export, pytest) via
  [`.vscode/tasks.json`](.vscode/tasks.json).
