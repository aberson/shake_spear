"""``ss index`` + ``ss export`` (plan §4, §6, §11 Steps 9 + 11).

Regenerates ``<story>/index.md`` — a DERIVED artifact (plan §3.4 exception
list): overwritten freely through :func:`shake_spear.utils.write_text`, no
``--force``, no ``.bak-`` backup.

Scan contract (plan §4 index row):

- every ``*.md`` under the story root recursively, EXCLUDING anything inside
  a dot-directory (``.claude/``, ``.git/`` — any path part starting with
  ``.``), the root ``index.md`` itself, and the ``exports/`` tree.
  ``exports/manuscript.md`` is itself derived output (Step 11) — listing a
  derived file in a derived index is noise, so ``exports/`` is excluded by
  design (seed §11's section list has no Exports section either).
- files map to the fixed seed §11 sections by their top-level folder
  (``characters/`` → Characters, ``world/`` → World elements, ``scenes/`` →
  Scenes, ``drafts/`` → Drafts, ``sessions/`` → Sessions, ``feedback/`` →
  Feedback, ``revisions/`` → Revisions); root-level files and files in
  unmapped folders (``prompts/``, anything an operator invents) land under
  Story files, with their relative path shown as always.
- every section is always present, in the seed §11 order, with ``(none)``
  under empty ones — an index for a brand-new story still renders complete.

Per-file entry (one bullet): title (frontmatter ``title``/``name``, else the
first H1 text, else the filename stem), ``type``/``status`` from frontmatter
(else ``-``), the story-relative path, and the first non-empty body line
(leading ``#`` marks stripped, truncated ~80 chars; empty body → ``(empty)``).
Frontmatter-less operator files degrade gracefully by design (plan §3.3
fallbacks, §10 risk table).

The output carries NO generation timestamp: a timestamp would make every
regeneration a git diff even with unchanged content AND break the
byte-idempotency guarantee (two runs with no content change produce
byte-identical files — tested). The Recently modified block's per-file local
mtime dates preserve that guarantee (mtimes don't change between runs).

``ss export`` (plan §4 export row) concatenates ``drafts/*.md`` — files only,
lexicographic by filename ascending — into ``exports/manuscript.md``, each
part preceded by an ``## <filename>`` heading. The DEFAULT target has the
same derived-artifact semantics as index.md: regenerated freely through
:func:`~shake_spear.utils.write_text`, no ``--force`` needed, no backup, no
timestamp. An ``--out PATH`` override is operator-chosen, so it does NOT get
the derived free-overwrite pass (Step 11 review):

- a resolved target inside the story's ``drafts/`` tree is rejected outright
  (:class:`~shake_spear.utils.UsageError`, exit 1) — drafts are strictly
  read-only (plan §3.4) and must never be clobbered by their own
  concatenation;
- any other target routes through :func:`~shake_spear.utils.safe_write`
  ``mode="refuse"``: a non-existing target writes normally (exclusive
  create), an existing one exits 2 unless ``--force`` (which keeps and
  prints a timestamped ``.bak-`` backup) — except the default
  ``exports/manuscript.md`` path itself, which keeps derived semantics even
  when spelled via ``--out``;
- the resolved target is also excluded from the gathered draft set —
  defense in depth against self-concatenation (e.g. a symlinked draft
  aliasing an outside-``drafts/`` target);
- an unwritable target (an existing directory, a permission wall) is a
  clean :class:`~shake_spear.utils.UsageError` (exit 1), not a traceback.

Drafts are strictly read-only (plan §3.4): the command only ever READS
``drafts/``.

Two documented choices:

- Each draft's frontmatter is STRIPPED (via
  :func:`~shake_spear.utils.split_frontmatter`, which also CRLF-normalizes)
  and only the body is exported: the manuscript should read as continuous
  prose, and ``status:``/``tags:`` metadata is workshop bookkeeping, not
  manuscript content. The metadata stays untouched in the source drafts.
- An empty ``drafts/`` prints a friendly message and exits 0 WITHOUT writing
  a file (not even with ``--out``): there is nothing to derive, and an empty
  manuscript on disk would look like lost work rather than absent input.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

from shake_spear.utils import (
    Frontmatter,
    UsageError,
    resolve_project,
    safe_write,
    split_frontmatter,
    write_text,
)

INDEX_NAME = "index.md"

#: Top-level story folder -> seed §11 section (everything else → Story files).
_FOLDER_SECTIONS: dict[str, str] = {
    "characters": "Characters",
    "world": "World elements",
    "scenes": "Scenes",
    "drafts": "Drafts",
    "sessions": "Sessions",
    "feedback": "Feedback",
    "revisions": "Revisions",
}

STORY_FILES_SECTION = "Story files"

#: The fixed seed §11 per-file sections, in render order.
SECTIONS: tuple[str, ...] = (STORY_FILES_SECTION, *_FOLDER_SECTIONS.values())

RECENT_SECTION = "Recently modified files"
RECENT_COUNT = 10

#: Soft cap for the first-line summary (plan §4: "short first-line summary").
_SUMMARY_LIMIT = 80

#: A TRUE markdown H1: exactly one ``#`` then whitespace then text.
_H1_RE = re.compile(r"# +(\S.*)")

_HEADER = "# Project Index\n\n_(Derived file: regenerated by `ss index`; safe to overwrite.)_\n"


def _scan(story_root: Path) -> list[Path]:
    """All indexable ``*.md`` under the story, sorted by relative path.

    Excludes dot-directories (and dot-files — any path part starting with
    ``.``), the ``exports/`` tree, and the root ``index.md`` itself.
    """
    files: list[Path] = []
    for path in story_root.rglob("*.md"):
        if not path.is_file():
            continue
        parts = path.relative_to(story_root).parts
        if any(part.startswith(".") for part in parts):
            continue
        if parts[0] == "exports" or parts == (INDEX_NAME,):
            continue
        files.append(path)
    files.sort(key=lambda p: p.relative_to(story_root).as_posix())
    return files


def _display(value: str | list[str] | None) -> str:
    """A frontmatter value as display text: lists joined ``", "``, stripped."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(value).strip()
    return value.strip()


def _title(data: Frontmatter, body: str, path: Path) -> str:
    """Entry title: frontmatter ``title``/``name`` → first H1 text → filename stem."""
    for key in ("title", "name"):
        text = _display(data.get(key))
        if text:
            return text
    for line in body.split("\n"):
        match = _H1_RE.fullmatch(line.strip())
        if match:
            return match.group(1).strip()
    return path.stem


def _meta(data: Frontmatter, key: str) -> str:
    """``type``/``status`` display value; missing or empty → ``-`` (plan §4)."""
    return _display(data.get(key)) or "-"


def _summary(body: str) -> str:
    """First non-empty body line, heading marks stripped, ~80 chars; else ``(empty)``.

    A marker-only heading line (``##``) strips to nothing and falls through
    to the next non-empty line rather than yielding a blank summary.
    """
    for raw in body.split("\n"):
        line = raw.strip().lstrip("#").strip()
        if line:
            if len(line) > _SUMMARY_LIMIT:
                return line[: _SUMMARY_LIMIT - 3] + "..."
            return line
    return "(empty)"


def _entry(path: Path, story_root: Path) -> str:
    """One per-file bullet: title, type, status, relative path, first-line summary."""
    data, body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    relpath = path.relative_to(story_root).as_posix()
    return (
        f"- **{_title(data, body, path)}** — type: {_meta(data, 'type')}, "
        f"status: {_meta(data, 'status')} — `{relpath}` — {_summary(body)}"
    )


def _section_for(relparts: tuple[str, ...]) -> str:
    """The seed §11 section for a scanned file, by its top-level folder."""
    if len(relparts) > 1:
        return _FOLDER_SECTIONS.get(relparts[0], STORY_FILES_SECTION)
    return STORY_FILES_SECTION


def _recent_lines(files: list[Path], story_root: Path) -> list[str]:
    """Top-:data:`RECENT_COUNT` by mtime desc: ``- `relpath` (YYYY-MM-DD)`` bullets."""
    if not files:
        return ["(none)"]
    stamped = [(path, path.stat().st_mtime) for path in files]
    stamped.sort(key=lambda item: (-item[1], item[0].relative_to(story_root).as_posix()))
    return [
        f"- `{path.relative_to(story_root).as_posix()}` "
        f"({datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')})"
        for path, mtime in stamped[:RECENT_COUNT]
    ]


def build_index(story_root: Path) -> str:
    """Render the full index.md content for ``story_root`` (pure; writes nothing)."""
    files = _scan(story_root)
    grouped: dict[str, list[str]] = {section: [] for section in SECTIONS}
    for path in files:
        section = _section_for(path.relative_to(story_root).parts)
        grouped[section].append(_entry(path, story_root))
    blocks = [_HEADER]
    for section in SECTIONS:
        entries = grouped[section] or ["(none)"]
        blocks.append(f"## {section}\n\n" + "\n".join(entries) + "\n")
    blocks.append(f"## {RECENT_SECTION}\n\n" + "\n".join(_recent_lines(files, story_root)) + "\n")
    return "\n".join(blocks)


def write_index(story_root: Path) -> Path:
    """Regenerate ``<story>/index.md`` (derived: plain overwrite, no backup)."""
    target = story_root / INDEX_NAME
    write_text(target, build_index(story_root))
    return target


def cmd_index(args: argparse.Namespace) -> int:
    """``ss index [PROJECT]`` — regenerate index.md; print the written path."""
    story_root = resolve_project(args.project, Path.cwd())
    print(write_index(story_root))
    return 0


# ---------------------------------------------------------------------------
# ss export (plan §4 export row, §11 Step 11)
# ---------------------------------------------------------------------------

DRAFTS_DIR = "drafts"
MANUSCRIPT_PATH = Path("exports") / "manuscript.md"

NO_DRAFTS_MESSAGE = "(no drafts yet — nothing to export)"

_MANUSCRIPT_TITLE = "# Manuscript"
_MANUSCRIPT_NOTE = "_(Derived file: regenerated by `ss export`; safe to overwrite.)_"


def _draft_files(story_root: Path, exclude: Path | None = None) -> list[Path]:
    """``drafts/*.md`` — files only, lexicographic by filename ascending.

    A missing ``drafts/`` directory is simply empty (fresh stories carry one,
    but the export contract degrades gracefully either way). Non-files that
    match the glob (a directory named ``notes.md``) are excluded; nested
    files (``drafts/sub/x.md``) never match the non-recursive glob.

    ``exclude`` (a fully RESOLVED path) drops the export target itself from
    the gathered set — defense in depth against self-concatenation, on top
    of :func:`cmd_export`'s drafts/-tree rejection (a draft that is a
    symlink to an outside-``drafts/`` target resolves equal to it without
    living under ``drafts/``).
    """
    return sorted(
        (
            path
            for path in (story_root / DRAFTS_DIR).glob("*.md")
            if path.is_file() and (exclude is None or path.resolve() != exclude)
        ),
        key=lambda path: path.name,
    )


def build_manuscript(draft_paths: list[Path]) -> str:
    """Render the manuscript content for ``draft_paths`` (pure; writes nothing).

    Header (``# Manuscript`` + derived-note line + ``N parts`` line), then one
    part per draft: an ``## <filename>`` heading (the bare filename, ``.md``
    kept — plan §4's ``## <filename>`` literally) and the draft's BODY with
    frontmatter stripped (see the module docstring for why). Blocks are
    separated by blank lines; :func:`split_frontmatter` CRLF-normalizes, so
    the manuscript is LF-only even from CRLF drafts.
    """
    count = len(draft_paths)
    blocks = [
        _MANUSCRIPT_TITLE,
        _MANUSCRIPT_NOTE,
        f"{count} part{'' if count == 1 else 's'}.",
    ]
    for path in draft_paths:
        _, body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        blocks.append(f"## {path.name}")
        body = body.strip("\n")
        if body:
            blocks.append(body)
    return "\n\n".join(blocks) + "\n"


def cmd_export(args: argparse.Namespace) -> int:
    """``ss export [PROJECT] [--out PATH] [--force]`` — drafts → manuscript.

    Reads ``drafts/`` only (strictly read-only w.r.t. drafts, plan §3.4). The
    default ``<story>/exports/manuscript.md`` target is derived output and is
    overwritten freely; an ``--out PATH`` override (relative PATH resolves
    against the current directory; parent directories are created) is
    operator-chosen and guarded — see the module docstring. Empty ``drafts/``
    → friendly message, exit 0, nothing written. Prints the written path,
    plus the ``.bak-`` backup path when ``--force`` created one.
    """
    story_root = resolve_project(args.project, Path.cwd())
    default_target = (story_root / MANUSCRIPT_PATH).resolve()
    if args.out is None:
        target = default_target
    else:
        out = Path(args.out)
        if not out.is_absolute():
            out = Path.cwd() / out
        target = out.resolve()
        drafts_dir = (story_root / DRAFTS_DIR).resolve()
        if target == drafts_dir or drafts_dir in target.parents:
            raise UsageError("--out may not point inside drafts/ - drafts are read-only")
    drafts = _draft_files(story_root, exclude=target)
    if not drafts:
        print(NO_DRAFTS_MESSAGE)
        return 0
    content = build_manuscript(drafts)
    if target.is_dir():  # deterministic cross-platform; the except below is the net
        raise UsageError(f"cannot write manuscript to {target}")
    backups: list[Path] = []
    try:
        if target == default_target:
            write_text(target, content)  # derived: regenerate freely (plan §3.4)
        else:
            safe_write(target, content, "refuse", force=args.force, backups=backups)
    except (IsADirectoryError, PermissionError) as exc:
        raise UsageError(f"cannot write manuscript to {target}") from exc
    print(target)
    for backup in backups:
        print(backup)
    return 0
