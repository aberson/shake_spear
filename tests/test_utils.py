"""Unit tests for ``shake_spear.utils`` (plan §3.2–§3.4, Appendix D; §11 Step 6).

tmp_path-based — the filesystem is the real dependency (the only test double
is a frozen clock for backup-name collision coverage).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from shake_spear.utils import (
    RefuseError,
    UsageError,
    find_story_root,
    find_workshop_root,
    parse_frontmatter,
    render_frontmatter,
    render_template,
    safe_write,
    slugify,
    split_frontmatter,
    validate_slug,
)

# ---------------------------------------------------------------------------
# slugify (plan §3.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Hello World", "hello_world"),
        ("Kids Space Bakery", "kids_space_bakery"),
        ("Hello, World!", "hello_world"),
        ("Rocket finds the moon oven", "rocket_finds_the_moon_oven"),
        ("Café crème brûlée", "caf_cr_me_br_l_e"),  # unicode letters are non-[a-z0-9]
        ("--Hello--", "hello"),
        ("a---b___c", "a_b_c"),
        ("UPPER lower 123", "upper_lower_123"),
        ("  spaces   everywhere  ", "spaces_everywhere"),
    ],
)
def test_slugify(text: str, expected: str) -> None:
    assert slugify(text) == expected


@pytest.mark.parametrize("text", ["", "!!!", "___", "—", "   "])
def test_slugify_empty_result_raises(text: str) -> None:
    with pytest.raises(UsageError):
        slugify(text)


@pytest.mark.parametrize("text", ["Nul", "CON", "com1", "Lpt9", "  AUX  "])
def test_slugify_reserved_device_name_raises(text: str) -> None:
    """Titles that slugify to Windows reserved device names must be rejected."""
    with pytest.raises(UsageError, match="reserved Windows device name"):
        slugify(text)


# ---------------------------------------------------------------------------
# validate_slug — the single slug validator (plan §3.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug",
    ["kids_space_bakery", "a", "x1", "a_b_c", "com10", "constant", "nul2", "template"],
)
def test_validate_slug_accepts_valid(slug: str) -> None:
    assert validate_slug(slug) == slug


@pytest.mark.parametrize(
    "slug",
    [
        "",  # empty
        "Bad Slug",  # space + uppercase
        "UPPER",  # uppercase outside [a-z0-9_]
        "hyphen-ated",  # hyphen outside [a-z0-9_]
        "_foo",  # leading underscore
        "foo_",  # trailing underscore
        "___",  # no [a-z0-9] at all
        "_template",  # the pristine skeleton
        "con",  # reserved Windows device names —
        "prn",
        "aux",
        "nul",
        "com1",
        "com9",
        "lpt1",
        "lpt9",
    ],
)
def test_validate_slug_rejects(slug: str) -> None:
    with pytest.raises(UsageError):
        validate_slug(slug)


# ---------------------------------------------------------------------------
# frontmatter parse/render (plan §3.3, Appendix D)
# ---------------------------------------------------------------------------

SAMPLE = """---
type: scene
title: Rocket finds the moon oven
status: planned
characters: [Nova, Rocket]
tags: []
user-invocable: true
audience:
---

# Body heading

Body text.
"""


def test_parse_frontmatter_basic() -> None:
    data = parse_frontmatter(SAMPLE)
    assert data == {
        "type": "scene",
        "title": "Rocket finds the moon oven",
        "status": "planned",
        "characters": ["Nova", "Rocket"],
        "tags": [],
        "user-invocable": "true",
        "audience": "",
    }


def test_split_frontmatter_returns_body() -> None:
    data, body = split_frontmatter(SAMPLE)
    assert data["type"] == "scene"
    assert body.startswith("\n# Body heading")
    assert "Body text." in body


def test_parse_value_keeps_inner_colons() -> None:
    data = parse_frontmatter("---\nnote: a: b\n---\n")
    assert data == {"note": "a: b"}


def test_parse_malformed_lines_skipped_silently() -> None:
    text = "---\nno colon here\n1bad: starts with digit\nbad key!: punctuation\nok: yes\n---\n"
    assert parse_frontmatter(text) == {"ok": "yes"}


def test_parse_crlf_input_normalized() -> None:
    """CRLF files from external editors must parse identically (input-only fix)."""
    data, body = split_frontmatter(SAMPLE.replace("\n", "\r\n"))
    assert data["type"] == "scene"
    assert data["title"] == "Rocket finds the moon oven"
    assert data["characters"] == ["Nova", "Rocket"]
    assert "Body text." in body


def test_parse_bare_cr_input_normalized() -> None:
    assert parse_frontmatter("---\rkey: value\r---\r") == {"key": "value"}


def test_parse_key_whitespace_stripped() -> None:
    """Keys with stray whitespace (trailing space before the colon, indentation) parse."""
    text = "---\ntitle : Spaced Out\n  indented: leading space\n---\n"
    assert parse_frontmatter(text) == {"title": "Spaced Out", "indented": "leading space"}


def test_parse_absent_frontmatter_is_empty() -> None:
    assert parse_frontmatter("# Just a heading\n") == {}
    assert parse_frontmatter("") == {}
    # `---` later in the file does not open a block (must be the FIRST line).
    assert parse_frontmatter("intro\n---\nkey: value\n---\n") == {}


def test_parse_unterminated_block_is_body_not_frontmatter() -> None:
    text = "---\nkey: value\nno closing delimiter\n"
    data, body = split_frontmatter(text)
    assert data == {}
    assert body == text


def test_list_values_strip_items() -> None:
    data = parse_frontmatter("---\ncharacters: [ Nova ,  Rocket , Baker Zed ]\n---\n")
    assert data == {"characters": ["Nova", "Rocket", "Baker Zed"]}


def test_render_frontmatter_round_trip() -> None:
    data = {
        "type": "scene",
        "title": "Rocket finds the moon oven",
        "characters": ["Nova", "Rocket"],
        "tags": [],
        "user-invocable": "true",
        "audience": "",
    }
    rendered = render_frontmatter(data)
    assert rendered.startswith("---\n")
    assert rendered.endswith("---\n")
    assert parse_frontmatter(rendered) == data


def test_render_frontmatter_rejects_bad_key() -> None:
    with pytest.raises(UsageError):
        render_frontmatter({"1bad": "x"})


def test_render_then_split_preserves_body() -> None:
    text = render_frontmatter({"type": "note"}) + "\nBody line\n"
    data, body = split_frontmatter(text)
    assert data == {"type": "note"}
    assert body == "\nBody line\n"


# ---------------------------------------------------------------------------
# safe_write (plan §3.4)
# ---------------------------------------------------------------------------


def test_safe_write_refuse_creates_new_file(tmp_path: Path) -> None:
    target = tmp_path / "a.md"
    result = safe_write(target, "content\n", "refuse")
    assert result == target
    assert target.read_text(encoding="utf-8") == "content\n"


def test_safe_write_refuse_raises_on_existing(tmp_path: Path) -> None:
    target = tmp_path / "a.md"
    target.write_text("old\n", encoding="utf-8")
    with pytest.raises(RefuseError):
        safe_write(target, "new\n", "refuse")
    assert target.read_text(encoding="utf-8") == "old\n"  # untouched


def test_safe_write_refuse_force_backs_up_old_content_first(tmp_path: Path) -> None:
    target = tmp_path / "a.md"
    target.write_text("OLD BYTES\n", encoding="utf-8")
    result = safe_write(target, "NEW\n", "refuse", force=True)
    assert result == target
    assert target.read_text(encoding="utf-8") == "NEW\n"
    backups = list(tmp_path.glob("a.md.bak-*"))
    assert len(backups) == 1
    assert re.fullmatch(r"a\.md\.bak-\d{14}", backups[0].name)
    assert backups[0].read_text(encoding="utf-8") == "OLD BYTES\n"  # the OLD bytes


def test_safe_write_force_surfaces_backup_path(tmp_path: Path) -> None:
    """Plan §4: the backup path is exposed via the ``backups`` out-param."""
    target = tmp_path / "a.md"
    backups: list[Path] = []
    safe_write(target, "first\n", "refuse", backups=backups)
    assert backups == [], "fresh create must not report a backup"
    safe_write(target, "second\n", "refuse", force=True, backups=backups)
    assert len(backups) == 1
    assert backups[0].name.startswith("a.md.bak-")
    assert backups[0].read_text(encoding="utf-8") == "first\n"


def test_safe_write_backup_same_second_collisions_get_unique_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With a frozen clock, colliding stamps fall back to microseconds, then _2."""
    import datetime as real_datetime_module

    import shake_spear.utils as utils_module

    frozen = real_datetime_module.datetime(2026, 7, 2, 12, 0, 0, 123456)

    class _FrozenDatetime:
        @staticmethod
        def now() -> real_datetime_module.datetime:
            return frozen

    monkeypatch.setattr(utils_module, "datetime", _FrozenDatetime)
    target = tmp_path / "a.md"
    target.write_text("v1\n", encoding="utf-8")
    safe_write(target, "v2\n", "refuse", force=True)
    safe_write(target, "v3\n", "refuse", force=True)
    safe_write(target, "v4\n", "refuse", force=True)
    names = sorted(p.name for p in tmp_path.glob("a.md.bak-*"))
    assert names == [
        "a.md.bak-20260702120000",
        "a.md.bak-20260702120000123456",
        "a.md.bak-20260702120000123456_2",
    ]
    assert (tmp_path / names[0]).read_text(encoding="utf-8") == "v1\n"
    assert (tmp_path / names[1]).read_text(encoding="utf-8") == "v2\n"
    assert (tmp_path / names[2]).read_text(encoding="utf-8") == "v3\n"
    assert target.read_text(encoding="utf-8") == "v4\n"


def test_safe_write_suffix_appends_b_then_c(tmp_path: Path) -> None:
    target = tmp_path / "2026-07-02_scene_45min.md"
    assert safe_write(target, "one\n", "suffix") == target
    second = safe_write(target, "two\n", "suffix")
    assert second == tmp_path / "2026-07-02_scene_45min_b.md"
    third = safe_write(target, "three\n", "suffix")
    assert third == tmp_path / "2026-07-02_scene_45min_c.md"
    assert target.read_text(encoding="utf-8") == "one\n"  # originals never overwritten
    assert second.read_text(encoding="utf-8") == "two\n"


def test_safe_write_suffix_errors_past_z(tmp_path: Path) -> None:
    target = tmp_path / "log.md"
    target.write_text("x", encoding="utf-8")
    for letter in "bcdefghijklmnopqrstuvwxyz":
        (tmp_path / f"log_{letter}.md").write_text("x", encoding="utf-8")
    with pytest.raises(UsageError):
        safe_write(target, "overflow\n", "suffix")


def test_safe_write_creates_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "file.md"
    assert safe_write(target, "hi\n", "refuse") == target
    assert target.read_text(encoding="utf-8") == "hi\n"


def test_safe_write_utf8_lf_no_bom(tmp_path: Path) -> None:
    target = tmp_path / "bytes.md"
    safe_write(target, "line1\nline2 café\n", "refuse")
    raw = target.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "must not write a UTF-8 BOM"
    assert b"\r" not in raw, "must write LF-only newlines"
    assert raw.decode("utf-8") == "line1\nline2 café\n"


# ---------------------------------------------------------------------------
# root detection walk-ups (plan §4, §6)
# ---------------------------------------------------------------------------


def test_find_workshop_root_walks_up(tmp_path: Path) -> None:
    root = tmp_path / "workshop"
    (root / "skills").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    start = root / "projects" / "some_story" / "scenes"
    start.mkdir(parents=True)
    assert find_workshop_root(start) == root.resolve()
    assert find_workshop_root(root) == root.resolve()


def test_find_workshop_root_requires_both_markers(tmp_path: Path) -> None:
    # pyproject.toml alone (no skills/ dir) must not match.
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    inner = tmp_path / "sub"
    inner.mkdir()
    assert find_workshop_root(inner) is None


def test_find_workshop_root_not_found(tmp_path: Path) -> None:
    assert find_workshop_root(tmp_path) is None


def test_find_story_root_walks_up(tmp_path: Path) -> None:
    story = tmp_path / "projects" / "kids_space_bakery"
    (story / "scenes").mkdir(parents=True)
    (story / "story_bible.md").write_text("---\ntype: story_bible\n---\n", encoding="utf-8")
    (story / "active_state.md").write_text("# Active State\n", encoding="utf-8")
    assert find_story_root(story / "scenes") == story.resolve()
    assert find_story_root(story) == story.resolve()


def test_find_story_root_requires_both_files(tmp_path: Path) -> None:
    story = tmp_path / "half_story"
    story.mkdir()
    (story / "story_bible.md").write_text("x\n", encoding="utf-8")
    assert find_story_root(story) is None


# ---------------------------------------------------------------------------
# template rendering (plan §5.3)
# ---------------------------------------------------------------------------


def test_render_template_replaces_known_placeholders(tmp_path: Path) -> None:
    template = tmp_path / "t.md"
    template.write_text(
        "{{title}} ({{slug}}); {{title}} again; {{missing}} stays\n", encoding="utf-8"
    )
    result = render_template(template, {"title": "Space Bakery", "slug": "space_bakery"})
    assert result == "Space Bakery (space_bakery); Space Bakery again; {{missing}} stays\n"
