"""Validation tests for the genre + meta shared skills (plan §5.1, seed §8).

Covers the Step 4 files only: story_bible_builder, dialogue_doctor,
voice_and_taste, kids_story_mode, mystery_mode, recap_and_resume,
prompt_smith, and skills/README.md. The Step 3 skills (immersive_session
and friends) are validated by their own test module; this file deliberately
asserts nothing about those FILES existing — the README may name them as
text only.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

SKILL_NAMES = [
    "story_bible_builder.md",
    "dialogue_doctor.md",
    "voice_and_taste.md",
    "kids_story_mode.md",
    "mystery_mode.md",
    "recap_and_resume.md",
    "prompt_smith.md",
]

ALL_FILES = [*SKILL_NAMES, "README.md"]

# Seed §8: every skill file uses this uniform section skeleton, in this order.
SKELETON_HEADINGS = [
    "## Purpose",
    "## Use when",
    "## Inputs to read first",
    "## Process",
    "## Output format",
    "## Things to avoid",
]

# Seed §8 recap_and_resume: the exact output block labels.
RECAP_LABELS = [
    "Current state:",
    "What I wrote last:",
    "What is emotionally alive:",
    "Open loops:",
    "Files changed:",
    "Best next scene:",
    "One tiny next action:",
]

# Seed §8 voice_and_taste: operator-fillable taste-profile sections.
TASTE_SECTIONS = [
    "Prose I like",
    "Prose I dislike",
    "Preferred sentence feel",
    "Humor level",
    "Darkness level",
    "Sincerity level",
    "Weirdness level",
    "Banned phrases",
    "Recurring images I like",
    "Style traits",
]

# Seed §8 mystery_mode: the eleven tracked elements.
MYSTERY_TRACKED = [
    "crime or central question",
    "suspects",
    "motives",
    "means",
    "opportunity",
    "clues",
    "red herrings",
    "reveals",
    "fair-play clue placement",
    "timeline",
    "detective knowledge vs reader knowledge",
]

# Plan §5.2: full catalog of all 14 shared skills the README table must name.
CATALOG_NAMES = [
    "immersive_session.md",
    "scene_planner.md",
    "quick_feedback.md",
    "revision_passes.md",
    "continuity_auditor.md",
    "character_keeper.md",
    "world_keeper.md",
    *SKILL_NAMES,
]

# Plan §5.2: the three invocation contexts the README documents.
README_CONTEXT_HEADINGS = [
    "## In Claude Code: slash wrappers",
    "## In any other assistant: paste or point",
    "## Inside a story folder",
]


def _read(name: str) -> str:
    return (SKILLS_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ALL_FILES)
def test_file_exists(name: str) -> None:
    assert (SKILLS_DIR / name).is_file(), f"missing file: skills/{name}"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_has_h1_title(name: str) -> None:
    first_line = _read(name).split("\n", 1)[0]
    assert re.fullmatch(r"# [^#].*", first_line), (
        f"{name}: first line must be an H1 title, got {first_line!r}"
    )


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_skeleton_headings_in_order(name: str) -> None:
    text = _read(name)
    positions: list[int] = []
    for heading in SKELETON_HEADINGS:
        match = re.search(rf"^{re.escape(heading)}$", text, flags=re.MULTILINE)
        assert match, f"{name}: missing skeleton heading {heading!r}"
        positions.append(match.start())
    assert positions == sorted(positions), f"{name}: skeleton headings out of seed-§8 order"


@pytest.mark.parametrize("label", RECAP_LABELS)
def test_recap_output_labels(label: str) -> None:
    lines = [line.strip() for line in _read("recap_and_resume.md").split("\n")]
    assert label in lines, (
        f"recap_and_resume.md: output block must contain the exact line {label!r}"
    )


def test_recap_output_labels_in_order() -> None:
    text = _read("recap_and_resume.md")
    positions = [text.index(label) for label in RECAP_LABELS]
    assert positions == sorted(positions), "recap_and_resume.md: output labels out of seed-§8 order"


@pytest.mark.parametrize("section", TASTE_SECTIONS)
def test_voice_and_taste_fillable_sections(section: str) -> None:
    text = _read("voice_and_taste.md")
    match = re.search(rf"^### {re.escape(section)}$", text, flags=re.MULTILINE)
    assert match, f"voice_and_taste.md: missing fillable section heading {section!r}"


def test_voice_and_taste_no_living_authors_rule() -> None:
    normalized = " ".join(_read("voice_and_taste.md").split())
    assert "describe style via craft traits, never by naming living authors to imitate" in (
        normalized
    ), "voice_and_taste.md: must state the no-living-authors rule explicitly"


@pytest.mark.parametrize("item", MYSTERY_TRACKED)
def test_mystery_mode_tracked_items(item: str) -> None:
    normalized = " ".join(_read("mystery_mode.md").split()).lower()
    assert item in normalized, f"mystery_mode.md: missing tracked element {item!r}"


@pytest.mark.parametrize("heading", README_CONTEXT_HEADINGS)
def test_readme_invocation_context_headings(heading: str) -> None:
    text = _read("README.md")
    match = re.search(rf"^{re.escape(heading)}", text, flags=re.MULTILINE)
    assert match, f"README.md: missing invocation-context heading {heading!r}"


@pytest.mark.parametrize("name", CATALOG_NAMES)
def test_readme_catalog_names_all_skills(name: str) -> None:
    """The catalog table names all 14 skills as text (files may live elsewhere)."""
    assert f"`{name}`" in _read("README.md"), f"README.md: catalog table must name {name}"


@pytest.mark.parametrize("name", ALL_FILES)
def test_utf8_lf_no_bom(name: str) -> None:
    raw = (SKILLS_DIR / name).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{name}: has a UTF-8 BOM"
    assert b"\r" not in raw, f"{name}: contains CR bytes (must be LF-only)"
    raw.decode("utf-8")  # must be valid UTF-8
