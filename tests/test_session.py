"""Integration tests for ``ss session`` / ``ss daily`` (plan §11 Step 8).

All tests go through the production CLI entry point — ``cli.main()``
in-process plus a true ``python -m shake_spear`` subprocess. The tmp
workshop and the scaffolded story (slug ``SLUG``) come from the shared
fixtures in ``conftest.py`` (real templates/skills/skeleton, real
``new-story`` run). The date is frozen through the ``session._today`` seam.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SLUG
from shake_spear import session
from shake_spear.cli import main
from shake_spear.utils import split_frontmatter

DATE = "2026-07-02"

#: Every session log links the base ritual trio (plan Appendix F).
TRIO = ("immersive_session.md", "quick_feedback.md", "recap_and_resume.md")


@pytest.fixture()
def frozen_date(monkeypatch: pytest.MonkeyPatch) -> str:
    """Pin ``session._today`` so filenames are deterministic across midnight."""
    monkeypatch.setattr(session, "_today", lambda: DATE)
    return DATE


def _skill_links(text: str) -> list[str]:
    """The ``../../skills/<file>.md`` inline-code targets in a session log's body."""
    return [part.split("`", 1)[0] for part in text.split("- `../../skills/")[1:]]


# ---------------------------------------------------------------------------
# creation: filename grammar, frontmatter, printed path (plan §3.2, §4)
# ---------------------------------------------------------------------------


def test_session_defaults_create_named_and_filled_log(
    story: Path, frozen_date: str, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()  # drop story-fixture output
    assert main(["session", SLUG]) == 0
    path = story / "sessions" / f"{DATE}_scene_45min.md"
    assert path.is_file(), "default type=scene minutes=45 filename"
    assert capsys.readouterr().out.strip().splitlines() == [str(path)]
    text = path.read_text(encoding="utf-8")
    assert "{{" not in text, "unrendered placeholder left behind"
    data, body = split_frontmatter(text)
    assert data["type"] == "session_log"
    assert data["date"] == DATE
    assert data["session_type"] == "scene"
    assert data["minutes"] == "45"
    assert data["status"] == "open"
    assert "## Session summary (from active_state.md)" in body
    assert "## Relevant skills" in body
    assert "(paths relative to the story root)" in body


def test_written_file_is_utf8_lf_no_bom(story: Path, frozen_date: str) -> None:
    assert main(["session", SLUG]) == 0
    raw = (story / "sessions" / f"{DATE}_scene_45min.md").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "has a UTF-8 BOM"
    assert b"\r" not in raw, "contains CR bytes"


def test_same_day_rerun_gets_b_suffix(
    story: Path, frozen_date: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["session", SLUG]) == 0
    capsys.readouterr()
    assert main(["session", SLUG]) == 0
    first = story / "sessions" / f"{DATE}_scene_45min.md"
    second = story / "sessions" / f"{DATE}_scene_45min_b.md"
    assert first.is_file() and second.is_file(), "both files must exist after the rerun"
    assert capsys.readouterr().out.strip().splitlines() == [str(second)], (
        "the printed path must be the ACTUAL (_b) path safe_write returned"
    )


def test_type_and_minutes_flags_shape_the_filename(story: Path, frozen_date: str) -> None:
    assert main(["session", SLUG, "--type", "revision", "--minutes", "30"]) == 0
    assert (story / "sessions" / f"{DATE}_revision_30min.md").is_file()


# ---------------------------------------------------------------------------
# Appendix F: type -> linked skills (trio always; per-type additions)
# ---------------------------------------------------------------------------

#: Literal mirror of the plan Appendix F per-type-additions table. Kept as a
#: literal (NOT imported from session.py) so a drift in ``_TYPE_SKILLS``
#: fails against the plan, not against itself.
APPENDIX_F: dict[str, tuple[str, ...]] = {
    "scene": ("scene_planner.md",),
    "revision": ("revision_passes.md",),
    "character": ("character_keeper.md",),
    "worldbuilding": ("world_keeper.md",),
    "dialogue": ("dialogue_doctor.md",),
    "kids": ("kids_story_mode.md",),
    "mystery": ("mystery_mode.md", "continuity_auditor.md"),
    "freewrite": ("voice_and_taste.md",),
}


@pytest.mark.parametrize(
    ("session_type", "extra"),
    [*APPENDIX_F.items(), ("cyberpunk_noir", ())],
    ids=[*APPENDIX_F, "unknown-trio-only"],
)
def test_appendix_f_mapping_row(session_type: str, extra: tuple[str, ...]) -> None:
    """Every Appendix F row: trio + the row's additions (unknown -> trio only)."""
    assert session.linked_skills(session_type) == (*TRIO, *extra)


def test_known_types_are_exactly_the_appendix_f_rows() -> None:
    """KNOWN_TYPES is derived from the mapping — assert it against the plan mirror."""
    assert session.KNOWN_TYPES == tuple(APPENDIX_F)


def _created_log_links(story: Path, *args: str) -> list[str]:
    assert main(["session", SLUG, *args]) == 0
    logs = sorted((story / "sessions").glob("*.md"))
    assert len(logs) == 1
    return _skill_links(logs[0].read_text(encoding="utf-8"))


def test_scene_links_trio_plus_scene_planner(story: Path, frozen_date: str) -> None:
    links = _created_log_links(story, "--type", "scene")
    assert links == [*TRIO, "scene_planner.md"]


def test_mystery_links_trio_plus_mystery_mode_and_continuity_auditor(
    story: Path, frozen_date: str
) -> None:
    links = _created_log_links(story, "--type", "mystery")
    assert links == [*TRIO, "mystery_mode.md", "continuity_auditor.md"]


def test_freeform_type_slugified_filename_and_trio_only(story: Path, frozen_date: str) -> None:
    assert main(["session", SLUG, "--type", "cyberpunk noir"]) == 0
    path = story / "sessions" / f"{DATE}_cyberpunk_noir_45min.md"
    assert path.is_file(), "free-form type must be slugified into the filename"
    text = path.read_text(encoding="utf-8")
    data, _ = split_frontmatter(text)
    assert data["session_type"] == "cyberpunk noir", "frontmatter carries the RAW type"
    assert _skill_links(text) == list(TRIO), "unknown type links the base trio only"


def test_linked_skill_files_exist_in_the_workshop(
    workshop: Path, story: Path, frozen_date: str
) -> None:
    """The Appendix F link targets must not dangle against the real skills/."""
    for session_type in ("scene", "mystery", "freewrite", "kids"):
        for name in session.linked_skills(session_type):
            assert (workshop / "skills" / name).is_file(), f"dangling skill link: {name}"


# ---------------------------------------------------------------------------
# active_state.md summary pull (plan §4: never an error)
# ---------------------------------------------------------------------------


def test_summary_pulls_current_status_and_next_tiny_action(story: Path, frozen_date: str) -> None:
    (story / "active_state.md").write_text(
        "# Active State\n\n"
        "## Current status\n\nDrafting chapter two; Nova just found the oven.\n\n"
        "## Open loops\n\nWho lit the pilot light?\n\n"
        "## Next tiny action\n\nWrite the first oven-door paragraph.\n",
        encoding="utf-8",
    )
    assert main(["session", SLUG]) == 0
    text = (story / "sessions" / f"{DATE}_scene_45min.md").read_text(encoding="utf-8")
    summary = text.split("## Session summary (from active_state.md)", 1)[1]
    summary = summary.split("## Relevant skills", 1)[0]
    assert "Drafting chapter two; Nova just found the oven." in summary
    assert "Write the first oven-door paragraph." in summary
    assert "Who lit the pilot light?" not in summary, "only the two §4 sections are pulled"
    assert session.NO_ACTIVE_STATE not in summary


def test_crlf_active_state_yields_cr_free_session_log(story: Path, frozen_date: str) -> None:
    """A CRLF-edited active_state.md must not leak CR bytes into the generated
    log (plan §3.4 LF-only writes) — split_frontmatter normalizes at the source."""
    (story / "active_state.md").write_bytes(
        b"# Active State\r\n\r\n"
        b"## Current status\r\n\r\nDrafting chapter two.\r\n\r\n"
        b"## Next tiny action\r\n\r\nWrite the oven-door paragraph.\r\n"
    )
    assert main(["session", SLUG]) == 0
    raw = (story / "sessions" / f"{DATE}_scene_45min.md").read_bytes()
    assert b"\r" not in raw, "CRLF active_state leaked CR bytes into the session log"
    text = raw.decode("utf-8")
    assert "Drafting chapter two." in text
    assert "Write the oven-door paragraph." in text
    assert session.NO_ACTIVE_STATE not in text


def test_hash_prefixed_prose_does_not_truncate_summary(story: Path, frozen_date: str) -> None:
    """Only TRUE headings (# + whitespace) end a section — "#nova" is content."""
    (story / "active_state.md").write_text(
        "## Current status\n\nDrafting.\n#nova is mid-scene.\n\n"
        "## Next tiny action\n\nKeep going.\n",
        encoding="utf-8",
    )
    assert main(["session", SLUG]) == 0
    text = (story / "sessions" / f"{DATE}_scene_45min.md").read_text(encoding="utf-8")
    assert "#nova is mid-scene." in text, "prose starting with '#' was truncated"


def test_summary_excludes_recap_block_directly_after_section(story: Path, frozen_date: str) -> None:
    """A recap block IMMEDIATELY after '## Next tiny action' (no heading
    between) must not leak into the session summary — the summary read strips
    the generated block before heading-to-heading extraction."""
    (story / "active_state.md").write_text(
        "# Active State\n\n"
        "## Current status\n\nDrafting chapter two.\n\n"
        "## Next tiny action\n\n"
        "Write the oven-door paragraph.\n\n"
        "<!-- ss:recap:start -->\n"
        "_Recap generated by `ss recap` on 2026-07-01._\n"
        "**Current state:** STALE RECAP LINE\n"
        "<!-- ss:recap:end -->\n",
        encoding="utf-8",
    )
    assert main(["session", SLUG]) == 0
    text = (story / "sessions" / f"{DATE}_scene_45min.md").read_text(encoding="utf-8")
    summary = text.split("## Session summary (from active_state.md)", 1)[1]
    summary = summary.split("## Relevant skills", 1)[0]
    assert "Write the oven-door paragraph." in summary, "the real action text must be pulled"
    assert "ss:recap:" not in summary, "marker lines leaked into the session summary"
    assert "STALE RECAP LINE" not in summary, "recap block body leaked into the summary"
    assert "Recap generated by" not in summary


def test_fresh_story_empty_sections_fall_back(story: Path, frozen_date: str) -> None:
    """The scaffolded active_state.md has empty sections -> the fallback line."""
    assert main(["session", SLUG]) == 0
    text = (story / "sessions" / f"{DATE}_scene_45min.md").read_text(encoding="utf-8")
    assert session.NO_ACTIVE_STATE in text


def test_one_section_missing_falls_back(story: Path, frozen_date: str) -> None:
    (story / "active_state.md").write_text("## Current status\n\nFilled.\n", encoding="utf-8")
    assert main(["session", SLUG]) == 0
    text = (story / "sessions" / f"{DATE}_scene_45min.md").read_text(encoding="utf-8")
    assert session.NO_ACTIVE_STATE in text
    assert "Filled." not in text, "a partial active_state must not half-render"


def test_missing_active_state_file_falls_back(story: Path) -> None:
    """Function-level: resolve_project gates the CLI on active_state.md existing,
    so the missing-file branch of the §4 contract is exercised directly."""
    (story / "active_state.md").unlink()
    assert session.active_state_summary(story) == session.NO_ACTIVE_STATE


# ---------------------------------------------------------------------------
# ss daily (plan §4: pure sugar for --type freewrite --minutes 15)
# ---------------------------------------------------------------------------


def test_daily_is_freewrite_15min(
    story: Path, frozen_date: str, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    assert main(["daily", SLUG]) == 0
    path = story / "sessions" / f"{DATE}_freewrite_15min.md"
    assert path.is_file()
    assert capsys.readouterr().out.strip().splitlines() == [str(path)]
    text = path.read_text(encoding="utf-8")
    data, _ = split_frontmatter(text)
    assert data["session_type"] == "freewrite"
    assert data["minutes"] == "15"
    assert _skill_links(text) == [*TRIO, "voice_and_taste.md"], (
        "daily shares the session code path, so the freewrite mapping applies"
    )


# ---------------------------------------------------------------------------
# validation: minutes, type (exit 1, nothing written)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("minutes", ["0", "-30"])
def test_nonpositive_minutes_exits_1(
    story: Path, minutes: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["session", SLUG, "--minutes", minutes]) == 1
    assert "positive" in capsys.readouterr().err
    assert not list((story / "sessions").glob("*.md")), "no file may be created"


def test_non_integer_minutes_exits_1(story: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["session", SLUG, "--minutes", "lots"])
    assert excinfo.value.code == 1
    assert not list((story / "sessions").glob("*.md")), "no file may be created"


def test_unsluggable_type_exits_1(story: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["session", SLUG, "--type", "!!!"]) == 1
    assert "slug" in capsys.readouterr().err
    assert not list((story / "sessions").glob("*.md"))


def test_bracketed_type_exits_1(story: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A [bracketed] type would round-trip out of frontmatter as a LIST."""
    assert main(["session", SLUG, "--type", "[scene, kids]"]) == 1
    assert "parsed as a list" in capsys.readouterr().err
    assert not list((story / "sessions").glob("*.md")), "no file may be created"


# ---------------------------------------------------------------------------
# PROJECT resolution reuse (matrix proven in Step 7 — two spot checks)
# ---------------------------------------------------------------------------


def test_project_omitted_cwd_inside_story(
    story: Path, frozen_date: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(story / "sessions")  # deep inside: walk-up must find the story root
    assert main(["session"]) == 0
    assert (story / "sessions" / f"{DATE}_scene_45min.md").is_file()


def test_project_omitted_outside_story_exits_1(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["session"]) == 1
    assert "no PROJECT given" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# true subprocess test through python -m shake_spear
# ---------------------------------------------------------------------------


def test_subprocess_session_create(workshop: Path, story: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "shake_spear", "session", SLUG, "--minutes", "20"],
        cwd=workshop,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    logs = list((story / "sessions").glob("*_scene_20min.md"))
    assert len(logs) == 1, "exactly one dated scene_20min log (real local date)"
    assert result.stdout.strip().splitlines() == [str(logs[0])]
