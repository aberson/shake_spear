"""``ss new-story`` + ``ss list-projects`` (plan §3.1, §3.5, §4, Appendix C).

``new_story`` scaffolds ``projects/<slug>/``: it copies the skeleton from
``projects/_template/`` (subfolders + story ``.gitignore`` ONLY — plan §3.1),
renders every story FILE fresh from ``templates/``, generates story-local
Claude Code wrappers under ``.claude/skills/``, then initializes the story's
own git repo (plan §3.5). ``list_projects`` reads ``story_bible.md``
frontmatter for each project and writes nothing.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from shake_spear.utils import (
    Frontmatter,
    RefuseError,
    UsageError,
    parse_frontmatter,
    reject_list_shaped,
    render_frontmatter,
    render_template,
    require_workshop_root,
    safe_write,
    slugify,
    validate_slug,
)

#: template filename -> rendered filename inside the story (plan §3.1 / §11 Step 6).
_STORY_FILES: dict[str, str] = {
    "story_project_README.md": "README.md",
    "local_AGENTS.md": "AGENTS.md",
    "local_CLAUDE.md": "CLAUDE.md",
    "story_bible.md": "story_bible.md",
    "active_state.md": "active_state.md",
    "continuity_log.md": "continuity.md",
    "decision_log.md": "decisions.md",
}

#: Stub for the derived index; `ss index` (Step 9) regenerates it freely (plan §3.4).
_INDEX_STUB = "_(Derived file: `ss index` regenerates this; safe to overwrite.)_\n"


def _wrapper_body(skill_filename: str) -> str:
    """Story-local wrapper body per plan Appendix C (standalone-clone degradation incl.)."""
    return (
        "This folder is one story inside the shake_spear workshop. Read\n"
        f"`../../skills/{skill_filename}` (relative to this story's root) and follow\n"
        "it. First read `active_state.md`, `story_bible.md`, and `continuity.md` here.\n"
        "If the shared skills path does not exist (standalone clone), say so and coach\n"
        "from the local story files alone.\n"
    )


def _notice(message: str) -> None:
    """Diagnostic notice on stderr with the shared ``ss: notice:`` prefix."""
    print(f"ss: notice: {message}", file=sys.stderr)


def _resolve_slug(title: str, slug: str | None) -> str:
    """``--slug`` verbatim if valid, else slugified title (plan §3.2).

    Both paths funnel through :func:`shake_spear.utils.validate_slug` — the
    single validator (charset, underscore placement, reserved device names,
    ``_template``).
    """
    if slug is None:
        return slugify(title)
    return validate_slug(slug)


def _copy_skeleton(
    template_dir: Path, story_dir: Path, force: bool, backups: list[Path]
) -> list[Path]:
    """Copy the ``projects/_template/`` skeleton (subfolders, ``.gitkeep``s, ``.gitignore``)."""
    created: list[Path] = []
    story_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(template_dir.rglob("*")):
        target = story_dir / source.relative_to(template_dir)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif source.name == ".gitkeep":
            # Empty markers: create when absent; never worth a backup under --force.
            if not target.exists():
                created.append(safe_write(target, "", "refuse"))
        else:
            content = source.read_text(encoding="utf-8")
            created.append(safe_write(target, content, "refuse", force=force, backups=backups))
    return created


def _render_story_files(
    templates_dir: Path,
    story_dir: Path,
    context: dict[str, str],
    force: bool,
    backups: list[Path],
) -> list[Path]:
    """Render every story file fresh from ``templates/`` (plan §3.1: no _template drift)."""
    created: list[Path] = []
    for template_name, story_name in _STORY_FILES.items():
        template_path = templates_dir / template_name
        if not template_path.is_file():
            raise UsageError(f"missing template: {template_path}")
        content = render_template(template_path, context)
        created.append(
            safe_write(story_dir / story_name, content, "refuse", force=force, backups=backups)
        )
    return created


def _generate_wrappers(root: Path, story_dir: Path, force: bool, backups: list[Path]) -> list[Path]:
    """Generate story-local ``.claude/skills/<kebab>/SKILL.md`` wrappers (plan §5.2, App. C).

    One wrapper per ``skills/*.md`` (README excluded). The description is read
    from the workshop-root wrapper's frontmatter — the single source of truth;
    missing root wrappers surface loudly rather than silently drifting.
    """
    created: list[Path] = []
    skills_dir = root / "skills"
    skill_files = sorted(p for p in skills_dir.glob("*.md") if p.name != "README.md")
    if not skill_files:
        raise UsageError(f"no shared skills found under {skills_dir}")
    for skill_file in skill_files:
        kebab = skill_file.stem.replace("_", "-")
        root_wrapper = root / ".claude" / "skills" / kebab / "SKILL.md"
        if not root_wrapper.is_file():
            raise UsageError(f"missing workshop-root wrapper for {skill_file.name}: {root_wrapper}")
        description = parse_frontmatter(root_wrapper.read_text(encoding="utf-8")).get("description")
        if not isinstance(description, str) or not description:
            raise UsageError(f"root wrapper has no description: {root_wrapper}")
        frontmatter: Frontmatter = {
            "name": kebab,
            "description": description,
            "user-invocable": "true",
        }
        content = render_frontmatter(frontmatter) + "\n" + _wrapper_body(skill_file.name)
        target = story_dir / ".claude" / "skills" / kebab / "SKILL.md"
        created.append(safe_write(target, content, "refuse", force=force, backups=backups))
    return created


def _git_init_commit(story_dir: Path, slug: str) -> None:
    """``git init`` + one scaffold commit inside the story (plan §3.5); graceful without git."""
    git = shutil.which("git")
    if git is None:
        _notice("git not found on PATH; story repo not initialized (plan §3.5)")
        return
    for command in (
        [git, "init"],
        [git, "add", "-A"],
        [git, "commit", "-m", f"story scaffold: {slug}"],
    ):
        result = subprocess.run(command, cwd=story_dir, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            _notice(f"git {' '.join(command[1:])} failed in {story_dir}: {detail}")
            return


def new_story(
    title: str,
    *,
    slug: str | None = None,
    genre: str = "",
    mode: str = "",
    force: bool = False,
    no_git: bool = False,
    start: Path | None = None,
) -> tuple[Path, list[Path], list[Path]]:
    """Scaffold a story project; return ``(story_root, created_paths, backup_paths)``.

    Refuse semantics are dir-level: an existing ``projects/<slug>/`` exits 2
    unless ``--force``, in which case individual files are rewritten through
    :func:`safe_write` force semantics (timestamped ``.bak-`` backups, all
    collected in ``backup_paths`` so the CLI can print them — plan §4).
    """
    reject_list_shaped(title, "title")
    root = require_workshop_root(start)
    story_slug = _resolve_slug(title, slug)
    template_dir = root / "projects" / "_template"
    templates_dir = root / "templates"
    if not template_dir.is_dir():
        raise UsageError(f"missing story skeleton: {template_dir}")
    if not templates_dir.is_dir():
        raise UsageError(f"missing templates directory: {templates_dir}")
    story_dir = root / "projects" / story_slug
    if story_dir.exists() and not force:
        raise RefuseError(
            f"{story_dir} already exists (use --force to overwrite its generated files)"
        )

    context = {"title": title, "slug": story_slug, "genre": genre, "mode": mode}
    created: list[Path] = []
    backups: list[Path] = []
    created += _copy_skeleton(template_dir, story_dir, force, backups)
    created += _render_story_files(templates_dir, story_dir, context, force, backups)
    created.append(
        safe_write(story_dir / "index.md", _INDEX_STUB, "refuse", force=force, backups=backups)
    )
    created += _generate_wrappers(root, story_dir, force, backups)
    if not no_git:
        _git_init_commit(story_dir, story_slug)
    return story_dir, created, backups


def _field(data: Frontmatter, key: str) -> str:
    """A frontmatter value as a display string: lists joined ``", "``, absent → ``""``."""
    value = data.get(key, "")
    if isinstance(value, list):
        return ", ".join(value)
    return value


def list_projects(root: Path) -> list[tuple[str, str, str, str]]:
    """Rows of ``(slug, title, genre, status)`` for ``projects/*`` minus ``_template``.

    Missing ``story_bible.md`` or fields degrade to blanks (plan §4). Read-only.
    """
    projects_dir = root / "projects"
    rows: list[tuple[str, str, str, str]] = []
    if not projects_dir.is_dir():
        return rows
    for entry in sorted(projects_dir.iterdir()):
        if not entry.is_dir() or entry.name == "_template" or entry.name.startswith("."):
            continue
        data: Frontmatter = {}
        bible = entry / "story_bible.md"
        if bible.is_file():
            data = parse_frontmatter(bible.read_text(encoding="utf-8"))
        rows.append(
            (entry.name, _field(data, "title"), _field(data, "genre"), _field(data, "status"))
        )
    return rows


def cmd_new_story(args: argparse.Namespace) -> int:
    """``ss new-story`` — prints created paths (and ``.bak-`` backups), then the story root."""
    story_dir, created, backups = new_story(
        args.title,
        slug=args.slug,
        genre=args.genre,
        mode=args.mode,
        force=args.force,
        no_git=args.no_git,
    )
    for path in created:
        print(path)
    for backup in backups:
        print(backup)
    print(story_dir)
    return 0


def cmd_list_projects(args: argparse.Namespace) -> int:
    """``ss list-projects`` — table of slug/title/genre/status; writes nothing."""
    root = require_workshop_root()
    rows = list_projects(root)
    if not rows:
        print("(no story projects yet)")
        return 0
    header = ("slug", "title", "genre", "status")
    widths = [max(len(header[i]), *(len(row[i]) for row in rows)) for i in range(len(header))]
    for cells in (header, *rows):
        line = "  ".join(cell.ljust(width) for cell, width in zip(cells, widths, strict=True))
        print(line.rstrip())
    return 0
