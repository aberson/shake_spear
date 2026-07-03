# shake_spear

A markdown-first creative writing workshop: shared AI prompt skills, reusable
templates, and a small stdlib-only Python CLI (`ss`) for scaffolding and managing
independent story subprojects. The AI acts as writing coach, scene partner, and
continuity assistant — guided by prompt files in `skills/` — and does not write the
stories by default. No web app, no database, no AI API calls: the entire product
surface is markdown files on disk.

> **Status: pre-build.** The full specification lives in [`plan.md`](plan.md)
> (14 automated build steps + 1 manual UAT). This README will be replaced by the
> friendly user guide in build Step 14.

## Stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11+, stdlib-only runtime | Simple, durable, zero deps |
| Packaging | uv (`pip install -e .` also works) | Fast, standard pyproject |
| CLI | `ss` console script | Scaffold stories, sessions, scenes, indexes, recaps |
| Tests | pytest | Filesystem-real tests, no mocks |
| Writing assets | Markdown + lightweight frontmatter | The product IS the files |

## Design in one breath

One public workshop repo (tools, skills, templates); each real story under
`projects/` is its own private nested git repo, individually flippable to public.
Creative safety is enforced in code: generators never overwrite without `--force`
(which still writes a backup), recaps only touch a marker block, and nothing ever
auto-modifies `drafts/`.

## Quickstart (post-build)

```powershell
uv sync
uv run ss new-story "Kids Space Bakery" --slug kids_space_bakery --genre kids
uv run ss session kids_space_bakery --type scene --minutes 45
```

See [`plan.md`](plan.md) §10 for the full command tour and [`docs/seed.md`](docs/seed.md)
for the original seed specification.
