"""Shared invariants for the ``ss`` CLI (plan §3.2–§3.4, §6, Appendix D).

Single source of truth for the behaviors every other module imports:

- :func:`slugify` — the one slug algorithm (plan §3.2).
- :func:`parse_frontmatter` / :func:`split_frontmatter` / :func:`render_frontmatter`
  — the hand-rolled frontmatter grammar (plan §3.3, Appendix D).
- :func:`safe_write` — the creative-safety choke point with explicit
  ``mode="refuse" | "suffix"`` semantics (plan §3.4).
- :func:`find_workshop_root` / :func:`find_story_root` — cwd walk-up detection
  — plus :func:`require_workshop_root` (raise-on-missing variant) and
  :func:`resolve_project` (the §4 optional-PROJECT-argument contract, shared
  by every story-targeting command).
- :func:`reject_list_shaped` — the one guard against ``[bracketed]`` operator
  input that would round-trip out of frontmatter as a LIST (Appendix D).
- :func:`render_template` — ``{{placeholder}}`` replacement, no template engine.

All file I/O here uses ``encoding="utf-8"`` and ``newline="\\n"`` (no BOM, no
CRLF — plan §3.4).
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Literal

__all__ = [
    "Frontmatter",
    "RefuseError",
    "UsageError",
    "find_story_root",
    "find_workshop_root",
    "parse_frontmatter",
    "reject_list_shaped",
    "render_frontmatter",
    "render_template",
    "require_workshop_root",
    "resolve_project",
    "safe_write",
    "slugify",
    "split_frontmatter",
    "validate_slug",
]

#: Parsed frontmatter mapping. Values are plain strings or lists of strings —
#: no other types exist in the grammar (Appendix D).
Frontmatter = dict[str, str | list[str]]


class UsageError(Exception):
    """Usage/validation error — the CLI maps this to exit code 1 (plan §4)."""


class RefuseError(Exception):
    """Refused overwrite — the CLI maps this to exit code 2 (plan §4)."""


_NON_SLUG_RUN_RE = re.compile(r"[^a-z0-9]+")
_SLUG_CHARSET_RE = re.compile(r"[a-z0-9_]+")
_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")

#: Windows reserved device names — ``projects/nul`` etc. hit device-path
#: behavior or raw ``WinError`` tracebacks, so slugs must never collide.
_RESERVED_DEVICE_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{digit}" for digit in range(1, 10)}
    | {f"lpt{digit}" for digit in range(1, 10)}
)

#: Collision suffixes for ``mode="suffix"``: ``_b`` … ``_z`` (plan §3.2).
_SUFFIX_LETTERS = "bcdefghijklmnopqrstuvwxyz"

#: A value shaped like ``[...]`` would render ``key: [X]`` in frontmatter and
#: parse back as a LIST (Appendix D) — see :func:`reject_list_shaped`.
_BRACKETED_VALUE_RE = re.compile(r"\[.*\]", flags=re.DOTALL)


def reject_list_shaped(value: str, field: str) -> str:
    """Reject operator input that would round-trip out of frontmatter as a list.

    ``value`` goes into a ``{field}: {value}`` frontmatter line; a value shaped
    ``[...]`` would parse back as a LIST under the Appendix D grammar, so it is
    a :class:`UsageError`. Returns ``value`` unchanged when acceptable.
    """
    if _BRACKETED_VALUE_RE.fullmatch(value.strip()):
        raise UsageError(f"{field} would be parsed as a list - remove the surrounding brackets")
    return value


def validate_slug(slug: str) -> str:
    """The single slug validator (plan §3.2); every slug path funnels through here.

    A valid slug is non-empty, only ``[a-z0-9_]``, has no leading/trailing
    underscore (which also guarantees at least one ``[a-z0-9]``), is not a
    Windows reserved device name (case-insensitively), and is not
    ``_template`` (the pristine skeleton). Violations raise
    :class:`UsageError`; the slug is returned unchanged when valid.
    """
    if slug == "_template":
        raise UsageError("slug '_template' is the pristine skeleton and cannot be a story")
    if not slug or not _SLUG_CHARSET_RE.fullmatch(slug):
        raise UsageError(f"slug must be non-empty and match [a-z0-9_]+ (got {slug!r})")
    if slug.startswith("_") or slug.endswith("_"):
        raise UsageError(f"slug must not start or end with '_' (got {slug!r})")
    if not any(char != "_" for char in slug):  # defense-in-depth; unreachable after the above
        raise UsageError(f"slug needs at least one [a-z0-9] character (got {slug!r})")
    if slug.lower() in _RESERVED_DEVICE_NAMES:
        raise UsageError(
            f"slug {slug!r} is a reserved Windows device name (CON/PRN/AUX/NUL/COM1-9/LPT1-9); "
            "pick a different slug or title"
        )
    return slug


def slugify(text: str) -> str:
    """Slug per plan §3.2: lowercase; runs of non-``[a-z0-9]`` → one ``_``; strip ``_``.

    An empty result (nothing slug-worthy in ``text``) is a :class:`UsageError`,
    as is a result that lands on a Windows reserved device name (the derived
    slug is funneled through :func:`validate_slug`).
    """
    slug = _NON_SLUG_RUN_RE.sub("_", text.lower()).strip("_")
    if not slug:
        raise UsageError(f"cannot derive a slug from {text!r} (no [a-z0-9] characters)")
    return validate_slug(slug)


def split_frontmatter(text: str) -> tuple[Frontmatter, str]:
    """Parse an optional leading frontmatter block; return ``(data, body)``.

    Grammar (plan §3.3 / Appendix D): the block starts with a first line exactly
    ``---`` and ends at the next line exactly ``---``. Inside, ``key: value``
    pairs with key ``[A-Za-z_][A-Za-z0-9_-]*`` (stripped of surrounding
    whitespace first — external editors add stray spaces); a value shaped
    ``[a, b]`` is a list of stripped strings (empty brackets → ``[]``);
    anything else is a plain stripped string. Malformed lines are skipped
    silently. Absent (or unterminated) frontmatter → ``({}, text)``.

    Input newlines are normalized (``\\r\\n``/``\\r`` → ``\\n``) so CRLF files
    from external editors parse identically; WRITES elsewhere stay LF-only.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0] != "---":
        return {}, text
    try:
        end = lines.index("---", 1)
    except ValueError:
        # Unterminated block: not frontmatter at all — the whole text is body.
        return {}, text
    data: Frontmatter = {}
    for line in lines[1:end]:
        key, sep, raw_value = line.partition(":")
        key = key.strip()
        if not sep or not _KEY_RE.fullmatch(key):
            continue  # malformed line: skipped silently (Appendix D)
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [item.strip() for item in inner.split(",")] if inner else []
        else:
            data[key] = value
    return data, "\n".join(lines[end + 1 :])


def parse_frontmatter(text: str) -> Frontmatter:
    """Frontmatter dict only (see :func:`split_frontmatter` for the body too)."""
    return split_frontmatter(text)[0]


def render_frontmatter(data: Frontmatter) -> str:
    """Render a frontmatter block; inverse of :func:`parse_frontmatter`.

    Round-trips everything :func:`parse_frontmatter` accepts:
    ``parse_frontmatter(render_frontmatter(data)) == data``.
    """
    lines = ["---"]
    for key, value in data.items():
        if not _KEY_RE.fullmatch(key):
            raise UsageError(f"invalid frontmatter key: {key!r}")
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            # rstrip so an empty value renders as "key:" (parses back to "").
            lines.append(f"{key}: {value}".rstrip())
    lines.append("---")
    return "\n".join(lines) + "\n"


def _write_text(path: Path, content: str, exclusive: bool = False) -> None:
    """The one low-level writer: UTF-8, LF, parents created (plan §3.4).

    ``exclusive=True`` uses open mode ``"x"`` (must-not-exist), making
    create-only writes race-free — an existing file raises
    :class:`FileExistsError` at open time, not at a separate check.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def _write_backup(path: Path) -> Path:
    """Copy ``path``'s OLD bytes to a fresh ``<name>.bak-<stamp>`` sibling.

    Same-second collisions fall back to a microsecond-suffixed name, then
    ``_2``/``_3``/… until a free name is found (exclusive create throughout).
    """
    data = path.read_bytes()
    now = datetime.now()
    base = f"{path.name}.bak-{now.strftime('%Y%m%d%H%M%S')}"
    micro = f"{base}{now.microsecond:06d}"
    names = [base, micro, *(f"{micro}_{n}" for n in range(2, 100))]
    for name in names:
        candidate = path.with_name(name)
        try:
            with candidate.open("xb") as handle:
                handle.write(data)
        except FileExistsError:
            continue
        return candidate
    raise UsageError(f"could not find a free backup name for {path.name}")


def safe_write(
    path: Path,
    content: str,
    mode: Literal["refuse", "suffix"],
    force: bool = False,
    backups: list[Path] | None = None,
) -> Path:
    """Write ``content`` under the explicit overwrite policy ``mode`` (plan §3.4).

    - ``mode="refuse"`` (named entities): an existing target raises
      :class:`RefuseError` (CLI exit 2) unless ``force=True``; ``force`` first
      writes a timestamped ``<name>.bak-YYYYMMDDHHMMSS`` backup of the OLD
      content next to the target, then overwrites.
    - ``mode="suffix"`` (dated logs): an existing target gets ``_b`` … ``_z``
      appended before the extension and a NEW file is created; exhaustion past
      ``_z`` is a :class:`UsageError`. ``force`` is meaningless here.

    All must-not-exist writes use exclusive-create (open mode ``"x"``), so the
    exists-vs-write race cannot silently clobber a file that appeared between
    a check and the write.

    When a ``.bak-`` backup is written, its path is appended to ``backups``
    (if provided) so callers can surface it (plan §4: every command prints the
    paths it created or updated).

    Returns the path actually written (differs from ``path`` under suffixing).
    """
    if mode == "refuse":
        try:
            _write_text(path, content, exclusive=True)
        except FileExistsError:
            if not force:
                raise RefuseError(
                    f"{path} already exists (use --force to overwrite; a .bak- backup is kept)"
                ) from None
            backup = _write_backup(path)
            if backups is not None:
                backups.append(backup)
            _write_text(path, content)
        return path
    if mode == "suffix":
        candidates = [path] + [
            path.with_name(f"{path.stem}_{letter}{path.suffix}") for letter in _SUFFIX_LETTERS
        ]
        for candidate in candidates:
            try:
                _write_text(candidate, content, exclusive=True)
            except FileExistsError:
                continue
            return candidate
        raise UsageError(f"all suffix slots taken for {path.name} (_b through _z exist)")
    raise UsageError(f"unknown safe_write mode: {mode!r}")  # runtime guard for untyped callers


def find_workshop_root(start: Path) -> Path | None:
    """Walk up from ``start`` to the workshop root: ``pyproject.toml`` + ``skills/``."""
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "skills").is_dir():
            return candidate
    return None


def require_workshop_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (default cwd) to the workshop root, or raise.

    The shared not-a-workshop :class:`UsageError` lives here so every command
    fails with the identical message.
    """
    root = find_workshop_root(start if start is not None else Path.cwd())
    if root is None:
        raise UsageError(
            "not inside a shake_spear workshop (no pyproject.toml + skills/ found walking up)"
        )
    return root


def _is_story_root(path: Path) -> bool:
    """The one story-root marker check: ``story_bible.md`` + ``active_state.md`` (plan §4)."""
    return (path / "story_bible.md").is_file() and (path / "active_state.md").is_file()


def find_story_root(start: Path) -> Path | None:
    """Walk up from ``start`` to a story root (see :func:`_is_story_root`)."""
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if _is_story_root(candidate):
            return candidate
    return None


def resolve_project(arg: str | None, cwd: Path) -> Path:
    """Resolve the optional PROJECT argument to an existing story root (plan §4).

    The one implementation of the §4 global convention, shared by every
    story-targeting command (``scene``/``character``/``world`` and Steps 8-11).
    Accepted forms for ``arg``:

    - ``None`` (argument omitted) — walk up from ``cwd`` via
      :func:`find_story_root`; not being inside a story is a
      :class:`UsageError` (exit 1) telling the operator what to pass.
    - absolute path — used as-is.
    - bare slug or ``projects/<slug>`` — resolved against the workshop root's
      ``projects/`` directory (workshop root found by walking up from ``cwd``).

    Whatever form is given must name an existing story directory — one
    containing both ``story_bible.md`` and ``active_state.md`` — else
    :class:`UsageError`.
    """
    if arg is None:
        story = find_story_root(cwd)
        if story is None:
            raise UsageError(
                "no PROJECT given and the current directory is not inside a story project "
                "(no story_bible.md + active_state.md found walking up); pass a project as "
                "a bare slug, projects/<slug>, or an absolute path"
            )
        return story
    given = Path(arg)
    if given.is_absolute():
        story = given
    else:
        # Normalize "projects/<slug>" to a bare "<slug>", then anchor at projects/.
        if given.parts[:1] == ("projects",):
            given = Path(*given.parts[1:]) if given.parts[1:] else Path("")
        story = require_workshop_root(cwd) / "projects" / given
    if not _is_story_root(story):
        raise UsageError(
            f"{story} is not a story project (no story_bible.md + active_state.md there); "
            "create one with: ss new-story"
        )
    return story


def render_template(template_path: Path, context: dict[str, str]) -> str:
    """Render a template by plain ``{{key}}`` replacement — no engine (plan §5.3).

    Unknown placeholders are left untouched; callers own the context contract.
    """
    text = template_path.read_text(encoding="utf-8")
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", value)
    return text
