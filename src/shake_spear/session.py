"""``ss session`` + ``ss daily`` (plan §4, §11 Step 8) and ``ss recap`` +
``ss status`` (plan §4, §3.4, §11 Step 10).

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

``ss recap`` (:func:`write_recap`) rewrites ONLY the text between the
``<!-- ss:recap:start -->`` / ``<!-- ss:recap:end -->`` markers in the
story's ``active_state.md`` — byte-level surgery: everything outside the
markers is the ORIGINAL bytes (operator CRLF, trailing whitespace, BOM —
all preserved; plan §3.4). Markers count only as whole LINES (an inline
prose mention of a marker string is operator content, never a marker).
Marker lines absent → the block is appended at EOF; a stray, out-of-order,
or duplicated marker layout → :class:`~shake_spear.utils.UsageError` (never
guess). The rewrite lands via a sibling temp file + ``os.replace`` so a
crash mid-write can never truncate the operator's file. ``ss status``
(:func:`cmd_status`) prints the §4 active-state fields + the newest session
filename to stdout and writes NOTHING.
"""

from __future__ import annotations

import argparse
import os
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
    body = _strip_recap_block(split_frontmatter(path.read_text(encoding="utf-8"))[1])
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


# ---------------------------------------------------------------------------
# ss recap + ss status (plan §4, §3.4, §11 Step 10)
# ---------------------------------------------------------------------------

#: The literal marker lines (plan Appendix B). Recap replaces text strictly
#: BETWEEN them; both marker lines themselves are kept.
RECAP_START = "<!-- ss:recap:start -->"
RECAP_END = "<!-- ss:recap:end -->"

#: How many latest session logs the recap block lists (plan §4 recap row).
RECAP_SESSION_COUNT = 3

#: Recap placeholders (plan §4: zero sessions / empty inputs still exit 0).
NO_SESSIONS_YET = "no sessions yet — run `ss session` to start"
NO_NEXT_ACTION = "(not set — decide one tiny action before stopping)"
NONE_RECORDED = "(none recorded)"
NONE_YET = "(none yet)"

#: Soft cap for per-session snippet lines in the recap block.
_SNIPPET_LIMIT = 80

#: ``ss status`` fields, in print order — the §4 status row's four
#: active_state.md sections (each falls back to ``(not set)``).
STATUS_SECTIONS: tuple[str, ...] = (
    "Current status",
    "Current scene or chapter",
    "Open loops",
    "Next tiny action",
)

#: "Story so far" count folders -> singular noun (cheap index data — counted
#: directly, does NOT require ``ss index`` to have run).
_COUNT_FOLDERS: tuple[tuple[str, str], ...] = (
    ("scenes", "scene"),
    ("characters", "character"),
    ("world", "world element"),
    ("drafts", "draft"),
)


def _strip_recap_block(body: str) -> str:
    """Remove the ss:recap marker block(s) from section-extraction input.

    The marker block is GENERATED output living inside the operator's file.
    When it directly follows a section (no heading between — e.g. markers
    right after ``## Next tiny action``), naive heading-to-heading extraction
    would swallow it, and recap would feed its own previous output back into
    itself — nesting marker lines inside the new block and corrupting the
    next surgical write. Every section read of active_state.md goes through
    this strip first; the FILE bytes are untouched (this is read-side only).

    Markers count only as whole LINES — a line that, rstripped, equals the
    marker exactly (mirroring :func:`_marker_line_offsets` on the write side).
    An inline prose mention of a marker string is operator content and is
    kept, as is a start-marker line with no end-marker line after it.
    """
    lines = body.split("\n")
    kept: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].rstrip() == RECAP_START:
            j = i + 1
            while j < len(lines) and lines[j].rstrip() != RECAP_END:
                j += 1
            if j < len(lines):  # complete block: drop lines i..j inclusive
                i = j + 1
                continue
        kept.append(lines[i])
        i += 1
    return "\n".join(kept)


def _marker_line_offsets(raw: bytes, marker: bytes) -> list[int]:
    """Byte offsets of every LINE-anchored occurrence of ``marker`` in ``raw``.

    A marker LINE starts its line (offset 0 or right after ``\\n``) and the
    rest of the line is only trailing whitespace before ``\\n``/EOF — i.e. the
    line, rstripped of spaces/tabs/``\\r``, equals the marker exactly. An
    inline mention (any other text on the line) is operator prose, never a
    marker — so the surgery can never latch onto e.g. a marker string quoted
    under "## Notes for AI assistants" or inside a code fence.
    """
    offsets: list[int] = []
    pos = 0
    while (at := raw.find(marker, pos)) != -1:
        pos = at + 1
        if at > 0 and raw[at - 1 : at] != b"\n":
            continue
        rest = raw[at + len(marker) :]
        newline = rest.find(b"\n")
        tail = rest if newline == -1 else rest[:newline]
        if not tail.strip(b" \t\r"):
            offsets.append(at)
    return offsets


def _active_state_body(story_root: Path) -> str:
    """``active_state.md`` body for section reads (recap block stripped), or ``""``."""
    path = story_root / "active_state.md"
    if not path.is_file():
        return ""
    body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))[1]
    return _strip_recap_block(body)


def _session_logs(story_root: Path) -> list[Path]:
    """``sessions/*.md`` newest-first by FILENAME (plan Appendix A: the
    ``YYYY-MM-DD`` prefix makes lexicographic order chronological; the
    ``_b``…``_z`` collision suffixes sort after their base name)."""
    folder = story_root / "sessions"
    if not folder.is_dir():
        return []
    logs = [path for path in folder.glob("*.md") if path.is_file()]
    return sorted(logs, key=lambda path: path.name, reverse=True)


def _log_snippet(path: Path) -> str:
    """One resume-worthy line from a session log, or ``""``.

    First line of the log's ``## Next tiny action`` (the resume hook), else
    ``## Session goal``; truncated to ~:data:`_SNIPPET_LIMIT` chars.
    """
    body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))[1]
    for heading in ("Next tiny action", "Session goal"):
        text = _section_text(body, heading)
        if text:
            line = text.split("\n", 1)[0].strip()
            if len(line) > _SNIPPET_LIMIT:
                return line[: _SNIPPET_LIMIT - 3] + "..."
            return line
    return ""


def _latest_session_lines(story_root: Path) -> list[str]:
    """Up to :data:`RECAP_SESSION_COUNT` bullets: ``- `filename` — snippet``."""
    lines: list[str] = []
    for log in _session_logs(story_root)[:RECAP_SESSION_COUNT]:
        snippet = _log_snippet(log)
        lines.append(f"- `{log.name}` — {snippet}" if snippet else f"- `{log.name}`")
    return lines


def _continuity_note(story_root: Path) -> str:
    """One count/summary line for ``continuity.md``, or ``""`` when empty.

    Counts the non-empty, non-heading body lines and names the sections they
    sit under — a pointer, not a reproduction (the recap block is a bookmark).
    """
    path = story_root / "continuity.md"
    if not path.is_file():
        return ""
    body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))[1]
    count = 0
    sections: list[str] = []
    current = ""
    for raw in body.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if _HEADING_RE.match(line):
            current = line.lstrip("#").strip()
            continue
        count += 1
        if current and current not in sections:
            sections.append(current)
    if not count:
        return ""
    noun = "note line" if count == 1 else "note lines"
    where = f" under {', '.join(sections)}" if sections else ""
    return f"{count} {noun} in continuity.md{where}"


def _story_counts_line(story_root: Path) -> str:
    """``N scenes, N characters, N world elements, N drafts`` — direct counts."""
    parts: list[str] = []
    for folder, noun in _COUNT_FOLDERS:
        directory = story_root / folder
        count = (
            sum(1 for path in directory.glob("*.md") if path.is_file()) if directory.is_dir() else 0
        )
        parts.append(f"{count} {noun}" + ("" if count == 1 else "s"))
    return ", ".join(parts)


def _labeled(label: str, text: str) -> str:
    """``**label:** text`` inline; multi-line text goes on its own lines below."""
    if "\n" in text:
        return f"**{label}:**\n{text}"
    return f"**{label}:** {text}"


def build_recap_block(story_root: Path, body: str) -> str:
    """The recap content that goes BETWEEN the markers (LF-only, no markers).

    ``body`` is the story's active_state.md body (CRLF-normalized and
    recap-block-stripped — see :func:`_strip_recap_block`).
    Adapts ``skills/recap_and_resume.md``'s output shape to the plan §4 recap
    fields (drops What-is-emotionally-alive/Files-changed; adds Continuity
    notes/Story so far): current state, latest sessions, open loops,
    continuity notes, story so far, best next scene / one tiny next action.
    Empty inputs degrade to placeholders — never an error (plan §4).
    """
    session_lines = _latest_session_lines(story_root)
    # >=1 session: ALWAYS block form (label line, bullets below) — an inline
    # "**Latest sessions:** - `x`" single bullet would not render as a list.
    sessions = (
        "**Latest sessions:**\n" + "\n".join(session_lines)
        if session_lines
        else _labeled("Latest sessions", NONE_YET)
    )
    lines = [
        f"_Recap generated by `ss recap` on {_today()}. Everything outside the markers is yours._",
        "",
        _labeled("Current state", _section_text(body, "Current status") or NO_SESSIONS_YET),
        sessions,
        _labeled("Open loops", _section_text(body, "Open loops") or NONE_RECORDED),
        _labeled("Continuity notes", _continuity_note(story_root) or NONE_RECORDED),
        _labeled("Story so far", _story_counts_line(story_root)),
        _labeled(
            "Best next scene / one tiny next action",
            _section_text(body, "Next tiny action") or NO_NEXT_ACTION,
        ),
    ]
    return "\n".join(lines)


def write_recap(story_root: Path) -> Path:
    """Rewrite ONLY the ss:recap marker block in ``active_state.md`` (plan §3.4).

    Byte-level surgery on the raw file — the file is read ONCE as bytes, and
    markers count only as whole LINES (:func:`_marker_line_offsets`), so an
    operator quoting a marker string in prose or a code fence never redirects
    the surgery:

    - one marker-line pair → replace strictly between them (both marker lines
      kept); everything before the start marker and from the end marker to
      EOF is the ORIGINAL bytes (operator CRLF/whitespace/BOM untouched);
    - no marker lines → append ``\\n`` + marker block + ``\\n`` at EOF (the
      original content is a byte-identical prefix);
    - exactly one marker line, markers out of order, or a second start-marker
      line after the first pair (multiple blocks) → :class:`UsageError`
      (exit 1), file untouched — recap never guesses at corrupt state.

    The write is crash-safe: the new bytes land in a sibling temp file which
    is then ``os.replace``d over active_state.md (atomic on the same
    filesystem), so a crash mid-write can never truncate the operator's file.
    The generated block itself is LF-only UTF-8 (plan §3.4). Returns the
    active_state.md path (the CLI prints it).
    """
    path = story_root / "active_state.md"
    raw = path.read_bytes()
    body = _strip_recap_block(split_frontmatter(raw.decode("utf-8", errors="replace"))[1])
    block = ("\n" + build_recap_block(story_root, body) + "\n").encode("utf-8")
    start = RECAP_START.encode("utf-8")
    end = RECAP_END.encode("utf-8")
    starts = _marker_line_offsets(raw, start)
    ends = _marker_line_offsets(raw, end)
    if not starts and not ends:
        updated = raw + b"\n" + start + block + end + b"\n"
    elif not starts or not ends:
        present, absent = (RECAP_END, RECAP_START) if not starts else (RECAP_START, RECAP_END)
        raise UsageError(
            f"active_state.md has {present} but no {absent} - fix or remove the "
            f"stray marker in {path} (recap only writes between a complete pair)"
        )
    elif ends[0] < starts[0]:
        raise UsageError(
            f"active_state.md has {RECAP_END} before {RECAP_START} - fix the "
            f"marker order in {path} (recap only writes between a complete pair)"
        )
    elif any(at > ends[0] for at in starts):
        raise UsageError(
            f"multiple recap marker blocks found - remove the duplicates in {path} "
            "(recap only writes between one pair)"
        )
    else:
        updated = raw[: starts[0] + len(start)] + block + raw[ends[0] :]
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_bytes(updated)
        tmp.replace(path)  # os.replace: atomic on the same filesystem
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


def cmd_recap(args: argparse.Namespace) -> int:
    """``ss recap [PROJECT]`` — rewrite the marker block; print the updated path."""
    story_root = resolve_project(args.project, Path.cwd())
    print(write_recap(story_root))
    return 0


def _print_field(label: str, text: str) -> None:
    """``label: text`` (single line) or label + indented lines; empty → ``(not set)``."""
    if not text:
        print(f"{label}: (not set)")
    elif "\n" in text:
        print(f"{label}:")
        for line in text.split("\n"):
            print(f"  {line}")
    else:
        print(f"{label}: {text}")


def cmd_status(args: argparse.Namespace) -> int:
    """``ss status [PROJECT]`` — print the §4 fields to stdout; write NOTHING."""
    story_root = resolve_project(args.project, Path.cwd())
    body = _active_state_body(story_root)
    for heading in STATUS_SECTIONS:
        _print_field(heading, _section_text(body, heading))
    logs = _session_logs(story_root)
    print(f"Newest session: {logs[0].name}" if logs else "Newest session: (none)")
    return 0
