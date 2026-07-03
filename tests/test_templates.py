"""Validation tests for the 14 markdown templates (plan §5.3, seed §9).

The frontmatter checks reimplement the plan §3.3 / Appendix D grammar in
miniature, deliberately local to this test file: the production parser lands
in ``utils.py`` in Step 6 and must not exist yet.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

TEMPLATE_NAMES = [
    "story_bible.md",
    "active_state.md",
    "session_log.md",
    "scene_card.md",
    "character_profile.md",
    "world_element.md",
    "story_project_README.md",
    "local_AGENTS.md",
    "local_CLAUDE.md",
    "chapter_draft.md",
    "feedback_note.md",
    "revision_plan.md",
    "continuity_log.md",
    "decision_log.md",
]

# Templates that are intentionally frontmatter-free (plan §3.3 allows this
# everywhere): active_state is the seed-§9 body verbatim; the two local guide
# files are instruction prose loaded raw into an assistant's context.
FRONTMATTER_FREE = {"active_state.md", "local_AGENTS.md", "local_CLAUDE.md"}

KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}")
ALLOWED_PLACEHOLDERS = {"title", "slug", "genre", "mode", "date", "type", "minutes", "name"}

# Tokens each template's primary producer is contractually required to fill
# (plan §5.3): missing one means the producer renders a hole, not a leak.
REQUIRED_PLACEHOLDERS = {
    "story_bible.md": {"title", "genre", "mode"},
    "session_log.md": {"date", "type", "minutes"},
    "scene_card.md": {"title"},
    "character_profile.md": {"name"},
    "world_element.md": {"name"},
}

# Templates rendered by `ss new-story` (plan §3.1). Its render context carries
# only {title, slug, genre, mode}; any other token would leak literally into
# the scaffolded project.
NEW_STORY_RENDERED = {
    "story_project_README.md",
    "local_AGENTS.md",
    "local_CLAUDE.md",
    "story_bible.md",
    "active_state.md",
    "continuity_log.md",
    "decision_log.md",
}
NEW_STORY_TOKENS = {"title", "slug", "genre", "mode"}

RECAP_START = "<!-- ss:recap:start -->"
RECAP_END = "<!-- ss:recap:end -->"


def _read(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _validate_frontmatter(text: str, name: str) -> dict[str, str | list[str]]:
    """Tiny reimplementation of the plan §3.3 grammar, strict for our own files.

    Checks: opening/closing ``---`` delimiters, every non-empty inner line is a
    ``key: value`` pair, keys match ``[A-Za-z_][A-Za-z0-9_-]*``, ``[...]`` list
    syntax is balanced.
    """
    lines = text.split("\n")
    assert lines[0] == "---", f"{name}: frontmatter must open with '---' as the first line"
    assert "---" in lines[1:], f"{name}: opening '---' has no closing '---'"
    end = lines.index("---", 1)
    parsed: dict[str, str | list[str]] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        assert ":" in line, f"{name}: not a 'key: value' pair: {line!r}"
        key, _, raw_value = line.partition(":")
        assert KEY_RE.fullmatch(key), f"{name}: bad frontmatter key: {key!r}"
        value = raw_value.strip()
        if value.startswith("[") or value.endswith("]"):
            assert value.startswith("[") and value.endswith("]"), (
                f"{name}: unbalanced list value: {value!r}"
            )
            inner = value[1:-1].strip()
            parsed[key] = [item.strip() for item in inner.split(",")] if inner else []
        else:
            parsed[key] = value
    return parsed


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_exists(name: str) -> None:
    assert (TEMPLATES_DIR / name).is_file(), f"missing template: templates/{name}"


def test_templates_dir_matches_template_names() -> None:
    """Disk vs list cross-check: a 15th/renamed template must not skip validation."""
    on_disk = {p.name for p in TEMPLATES_DIR.glob("*.md")}
    assert on_disk == set(TEMPLATE_NAMES)


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_frontmatter_valid(name: str) -> None:
    text = _read(name)
    if name in FRONTMATTER_FREE:
        assert not text.startswith("---"), f"{name}: expected no frontmatter"
        return
    assert text.startswith("---\n"), f"{name}: expected a frontmatter block"
    parsed = _validate_frontmatter(text, name)
    assert "type" in parsed, f"{name}: frontmatter must declare a 'type'"


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_placeholders_within_vocabulary(name: str) -> None:
    tokens = set(PLACEHOLDER_RE.findall(_read(name)))
    unknown = tokens - ALLOWED_PLACEHOLDERS
    assert not unknown, f"{name}: placeholders outside the §5.3 vocabulary: {sorted(unknown)}"


@pytest.mark.parametrize("name", sorted(REQUIRED_PLACEHOLDERS))
def test_required_placeholders_present(name: str) -> None:
    tokens = set(PLACEHOLDER_RE.findall(_read(name)))
    missing = REQUIRED_PLACEHOLDERS[name] - tokens
    assert not missing, f"{name}: missing required placeholders: {sorted(missing)}"


@pytest.mark.parametrize("name", sorted(NEW_STORY_RENDERED))
def test_new_story_rendered_templates_use_only_new_story_tokens(name: str) -> None:
    tokens = set(PLACEHOLDER_RE.findall(_read(name)))
    leaking = tokens - NEW_STORY_TOKENS
    assert not leaking, (
        f"{name}: rendered by `ss new-story` but uses tokens outside its "
        f"context {sorted(NEW_STORY_TOKENS)}: {sorted(leaking)} would leak literally"
    )


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_utf8_lf_no_bom(name: str) -> None:
    raw = (TEMPLATES_DIR / name).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{name}: has a UTF-8 BOM"
    assert b"\r" not in raw, f"{name}: contains CR bytes (must be LF-only)"
    raw.decode("utf-8")  # must be valid UTF-8


def test_active_state_has_recap_marker_block() -> None:
    text = _read("active_state.md")
    assert RECAP_START in text, "active_state.md: missing recap start marker"
    assert RECAP_END in text, "active_state.md: missing recap end marker"
    assert text.index(RECAP_START) < text.index(RECAP_END), (
        "active_state.md: recap markers out of order"
    )


def test_story_bible_pinned_frontmatter_fields() -> None:
    """Pinned delta (plan Appendix E): 'mode' exists; audience empty; status seed."""
    parsed = _validate_frontmatter(_read("story_bible.md"), "story_bible.md")
    assert "mode" in parsed
    assert parsed["audience"] == ""
    assert parsed["status"] == "seed"
