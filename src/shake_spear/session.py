"""``ss session`` + ``ss daily`` (plan §4, §11 Step 8).

Partial module: ``ss recap`` and ``ss status`` land in Step 10.

``create_session`` renders ``templates/session_log.md`` (frontmatter
``{{date}}/{{type}}/{{minutes}}`` — the RAW type string goes into
frontmatter, the slug into the filename) and appends two generated
sections:

- ``## Session summary (from active_state.md)`` — the text under the
  story's ``## Current status`` and ``## Next tiny action`` headings; if
  the file or either section is missing/empty, the literal line
  ``(no active state yet)`` (plan §4: never an error).
- ``## Relevant skills`` — inline-code bullets naming the type-relevant
  shared skills per plan Appendix F (base ritual trio always; per-type
  additions keyed by the slugified type; free-form/unknown → trio only).
  Paths are written relative to the STORY ROOT (``../../skills/...``),
  matching the story-local guides' convention — inline code, not
  clickable links, because a link resolved from ``sessions/`` would 404.

The target is ``sessions/<YYYY-MM-DD>_<type_slug>_<minutes>min.md`` via
:func:`shake_spear.utils.safe_write` with ``mode="suffix"`` (plan §3.2:
same-day collision → ``_b`` … ``_z``, never refuses). ``ss daily`` is
pure sugar: the same code path with type=freewrite, minutes=15.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

from shake_spear.utils import (
    UsageError,
    reject_list_shaped,
    render_template,
    resolve_project,
    safe_write,
    slugify,
    split_frontmatter,
    templates_dir,
)

DEFAULT_TYPE = "scene"
DEFAULT_MINUTES = 45
DAILY_TYPE = "freewrite"
DAILY_MINUTES = 15

#: Base ritual trio linked in EVERY session log (plan Appendix F).
_BASE_SKILLS = ("immersive_session.md", "quick_feedback.md", "recap_and_resume.md")

#: type slug -> additional linked skills (plan Appendix F). Keyed by the
#: SLUGIFIED type so casing/punctuation variants that produce the same
#: filename also link the same skills; unknown slugs -> trio only.
_TYPE_SKILLS: dict[str, tuple[str, ...]] = {
    "scene": ("scene_planner.md",),
    "revision": ("revision_passes.md",),
    "character": ("character_keeper.md",),
    "worldbuilding": ("world_keeper.md",),
    "dialogue": ("dialogue_doctor.md",),
    "kids": ("kids_story_mode.md",),
    "mystery": ("mystery_mode.md", "continuity_auditor.md"),
    "freewrite": ("voice_and_taste.md",),
}

#: The plan §4 type vocabulary (free-form values are accepted too; they get
#: slugified into the filename and link the base trio only). Derived from
#: the Appendix F mapping so the two can never drift.
KNOWN_TYPES = tuple(_TYPE_SKILLS)

#: The plan §4 fallback line when active_state.md gives no usable summary.
NO_ACTIVE_STATE = "(no active state yet)"

#: The two active_state.md sections the summary pulls (plan §4).
_SUMMARY_SECTIONS = ("Current status", "Next tiny action")

#: A TRUE markdown ATX heading: 1-6 ``#`` then whitespace. Prose lines that
#: merely start with ``#`` (e.g. "#nova") are content, not section ends.
_HEADING_RE = re.compile(r"#{1,6}\s")


def _today() -> str:
    """Local date for the session filename (plan §3.2). Test seam."""
    return datetime.now().strftime("%Y-%m-%d")


def _section_text(body: str, heading: str) -> str:
    """Text under ``## <heading>`` up to the next TRUE heading line, stripped.

    Heading-to-next-heading extraction: a section ends at the next markdown
    ATX heading (:data:`_HEADING_RE` — any level, ``#`` + whitespace), so
    prose like "#nova" never truncates a section. A missing section
    returns ``""``. Reused by recap (Step 10) — do not duplicate extraction.
    """
    lines = body.split("\n")
    matches = (i for i, line in enumerate(lines) if line.strip() == f"## {heading}")
    start = next(matches, None)
    if start is None:
        return ""
    collected: list[str] = []
    for line in lines[start + 1 :]:
        if _HEADING_RE.match(line):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def active_state_summary(story_root: Path) -> str:
    """The §4 session-summary text pulled from the story's ``active_state.md``.

    Both ``## Current status`` and ``## Next tiny action`` texts (labeled),
    or the literal :data:`NO_ACTIVE_STATE` line when the file or EITHER
    section is missing/empty — never an error.
    """
    path = story_root / "active_state.md"
    if not path.is_file():
        return NO_ACTIVE_STATE
    body = split_frontmatter(path.read_text(encoding="utf-8"))[1]
    parts: list[str] = []
    for heading in _SUMMARY_SECTIONS:
        text = _section_text(body, heading)
        if not text:
            return NO_ACTIVE_STATE
        parts.append(f"**{heading}:**\n\n{text}")
    return "\n\n".join(parts)


def linked_skills(type_slug: str) -> tuple[str, ...]:
    """Skill filenames for this session type (plan Appendix F): trio + per-type."""
    return _BASE_SKILLS + _TYPE_SKILLS.get(type_slug, ())


def _generated_sections(story_root: Path, type_slug: str) -> str:
    """The two appended blocks: session summary + relevant-skills bullets.

    Skills are listed as inline-code paths (story-root-relative by
    convention, matching the wrapper style) — a clickable markdown link
    resolved from ``sessions/`` would 404.
    """
    links = "\n".join(
        f"- `../../skills/{name}` — {name.removesuffix('.md')}" for name in linked_skills(type_slug)
    )
    return (
        "\n## Session summary (from active_state.md)\n\n"
        f"{active_state_summary(story_root)}\n\n"
        "## Relevant skills\n\n"
        "(paths relative to the story root)\n\n"
        f"{links}\n"
    )


def create_session(
    story_root: Path,
    session_type: str = DEFAULT_TYPE,
    minutes: int = DEFAULT_MINUTES,
) -> Path:
    """Create one dated session log; return the path actually written.

    ``session_type`` goes RAW into frontmatter (so it is rejected when
    list-shaped, Appendix D) and slugified into the filename (slugify
    raises :class:`UsageError` on empty/reserved results). ``minutes``
    must be a positive int. Collisions suffix ``_b`` … ``_z`` (plan §3.2).
    """
    if minutes <= 0:
        raise UsageError(f"--minutes must be a positive integer (got {minutes})")
    reject_list_shaped(session_type, "type")
    type_slug = slugify(session_type)
    template_path = templates_dir(story_root) / "session_log.md"
    if not template_path.is_file():
        raise UsageError(f"missing template: {template_path}")
    date = _today()
    content = render_template(
        template_path, {"date": date, "type": session_type, "minutes": str(minutes)}
    )
    if not content.endswith("\n"):
        content += "\n"
    content += _generated_sections(story_root, type_slug)
    target = story_root / "sessions" / f"{date}_{type_slug}_{minutes}min.md"
    return safe_write(target, content, "suffix")


def cmd_session(args: argparse.Namespace) -> int:
    """``ss session [PROJECT] [--type T] [--minutes N]`` → ``sessions/<...>.md``."""
    story_root = resolve_project(args.project, Path.cwd())
    print(create_session(story_root, session_type=args.type, minutes=args.minutes))
    return 0


def cmd_daily(args: argparse.Namespace) -> int:
    """``ss daily [PROJECT]`` — sugar for ``ss session PROJECT --type freewrite --minutes 15``."""
    story_root = resolve_project(args.project, Path.cwd())
    print(create_session(story_root, session_type=DAILY_TYPE, minutes=DAILY_MINUTES))
    return 0
