"""Validation tests for the 7 Step-3 shared skill files (plan §5.1, seed §8).

Step 4 owns the other 7 skills plus ``skills/README.md`` and ships its own test
file; this one deliberately checks only the Step-3 seven so the two never collide.
Assertion sources: the seed-§8 skeleton, the immersive-session phase labels and
modes, the exact scene_planner / quick_feedback output blocks, the 12 revision
passes, and the continuity_auditor output labels.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

SKILL_NAMES = [
    "immersive_session.md",
    "scene_planner.md",
    "quick_feedback.md",
    "revision_passes.md",
    "continuity_auditor.md",
    "character_keeper.md",
    "world_keeper.md",
]

# The uniform seed-§8 skeleton, in required order.
SKELETON_HEADINGS = [
    "## Purpose",
    "## Use when",
    "## Inputs to read first",
    "## Process",
    "## Output format",
    "## Things to avoid",
]

SESSION_PHASE_LABELS = [
    "3-minute warm start",
    "5-minute orientation",
    "5-minute scene shaping",
    "20-minute writing block",
    "7-minute quick feedback",
    "5-minute shutdown",
]

SESSION_MODES = [
    "drafting",
    "revision",
    "character exploration",
    "worldbuilding",
    "dialogue practice",
    "kids story",
    "mystery",
    "freewrite",
]

# Exact seed-§8 output-format blocks: every line must appear verbatim.
SCENE_PLANNER_FIELDS = [
    "Scene title:",
    "POV:",
    "Location:",
    "Characters present:",
    "External goal:",
    "Internal/emotional goal:",
    "Conflict:",
    "Complication:",
    "Emotional turn:",
    "Sensory anchors:",
    "Key object:",
    "Ending image or line:",
    "Five scene beats:",
]

QUICK_FEEDBACK_FIELDS = [
    "What is working:",
    "Most important issue:",
    "Where I got confused:",
    "Most vivid detail:",
    "Most generic detail:",
    "One craft suggestion:",
    "Three concrete edits:",
    "Continuity notes:",
    "Next writing move:",
]

REVISION_PASSES = [
    "story logic",
    "character motivation",
    "emotional tension",
    "dialogue",
    "sensory detail",
    "pacing",
    "sentence polish",
    "line-level compression",
    "humor",
    "scarier/more suspenseful version",
    "quieter/more literary version",
    "kid-friendly clarity",
]

CONTINUITY_OUTPUT_LABELS = [
    "Continuity updates to add:",
    "Possible contradictions:",
    "Open questions:",
    "Reader promises:",
    "Suggested updates to files:",
]


def _read(name: str) -> str:
    return (SKILLS_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skill_exists(name: str) -> None:
    assert (SKILLS_DIR / name).is_file(), f"missing skill: skills/{name}"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_skeleton_headings_present_and_in_order(name: str) -> None:
    text = _read(name)
    positions = []
    for heading in SKELETON_HEADINGS:
        idx = text.find(f"\n{heading}\n")
        assert idx != -1, f"{name}: missing skeleton heading {heading!r} (as its own line)"
        positions.append(idx)
    assert positions == sorted(positions), f"{name}: skeleton headings out of seed-§8 order"


def test_immersive_session_phase_labels() -> None:
    text = _read("immersive_session.md")
    for label in SESSION_PHASE_LABELS:
        assert label in text, f"immersive_session.md: missing phase label {label!r}"


def test_immersive_session_modes() -> None:
    text = _read("immersive_session.md").lower()
    for mode in SESSION_MODES:
        assert mode in text, f"immersive_session.md: missing mode {mode!r}"


@pytest.mark.parametrize("field", SCENE_PLANNER_FIELDS)
def test_scene_planner_output_block_line(field: str) -> None:
    lines = _read("scene_planner.md").split("\n")
    assert field in lines, f"scene_planner.md: output-format line {field!r} not present verbatim"


@pytest.mark.parametrize("field", QUICK_FEEDBACK_FIELDS)
def test_quick_feedback_output_block_line(field: str) -> None:
    lines = _read("quick_feedback.md").split("\n")
    assert field in lines, f"quick_feedback.md: output-format line {field!r} not present verbatim"


@pytest.mark.parametrize("pass_name", REVISION_PASSES)
def test_revision_passes_names_all_twelve(pass_name: str) -> None:
    text = _read("revision_passes.md").lower()
    assert pass_name in text, f"revision_passes.md: missing pass {pass_name!r}"


@pytest.mark.parametrize("label", CONTINUITY_OUTPUT_LABELS)
def test_continuity_auditor_output_labels(label: str) -> None:
    lines = _read("continuity_auditor.md").split("\n")
    assert label in lines, f"continuity_auditor.md: output label {label!r} not present verbatim"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_utf8_lf_no_bom(name: str) -> None:
    raw = (SKILLS_DIR / name).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{name}: has a UTF-8 BOM"
    assert b"\r" not in raw, f"{name}: contains CR bytes (must be LF-only)"
    raw.decode("utf-8")  # must be valid UTF-8
