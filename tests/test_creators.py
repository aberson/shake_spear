"""Integration tests for ``ss scene`` / ``ss character`` / ``ss world`` (plan §11 Step 7).

All tests go through the production CLI entry point — ``cli.main()``
in-process plus true ``python -m shake_spear`` subprocesses. The tmp workshop
comes from the shared ``workshop`` fixture (``conftest.py``, real templates/
skills/skeleton); the story fixture is scaffolded via the real ``new-story``
command. No mocks — the filesystem is the real dependency.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from shake_spear.cli import main
from shake_spear.utils import parse_frontmatter, split_frontmatter

SLUG = "kids_space_bakery"

#: (command, story subfolder, frontmatter field == template placeholder,
#:  frontmatter type, template default status) — the plan §4 creator rows.
CREATORS = [
    ("scene", "scenes", "title", "scene", "planned"),
    ("character", "characters", "name", "character", "active"),
    ("world", "world", "name", "world_element", "active"),
]


@pytest.fixture()
def story(workshop: Path) -> Path:
    """A real story scaffolded through the production CLI (``--no-git``)."""
    assert main(["new-story", "Kids Space Bakery", "--genre", "kids", "--no-git"]) == 0
    return workshop / "projects" / SLUG


# ---------------------------------------------------------------------------
# creation: right folder, right filename, right frontmatter (plan §4 rows)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("command", "folder", "field", "ftype", "status"), CREATORS)
def test_creates_file_with_filled_frontmatter(
    story: Path, command: str, folder: str, field: str, ftype: str, status: str
) -> None:
    value = "Rocket Finds the Moon Oven"
    assert main([command, SLUG, value]) == 0
    path = story / folder / "rocket_finds_the_moon_oven.md"
    assert path.is_file(), f"expected {folder}/rocket_finds_the_moon_oven.md"
    text = path.read_text(encoding="utf-8")
    assert "{{" not in text, "unrendered placeholder left behind"
    data, body = split_frontmatter(text)
    assert data["type"] == ftype
    assert data[field] == value, f"{field} must carry the operator's value verbatim"
    assert data["status"] == status
    assert body.strip(), "template body must survive the render"


def test_prints_created_path_one_per_line(story: Path, capsys: pytest.CaptureFixture[str]) -> None:
    capsys.readouterr()  # drop story-fixture output
    assert main(["scene", SLUG, "Launch Day"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [str(story / "scenes" / "launch_day.md")]


def test_written_file_is_utf8_lf_no_bom(story: Path) -> None:
    assert main(["character", SLUG, "Nova"]) == 0
    raw = (story / "characters" / "nova.md").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "has a UTF-8 BOM"
    assert b"\r" not in raw, "contains CR bytes"
    raw.decode("utf-8")


# ---------------------------------------------------------------------------
# PROJECT argument forms (plan §4 global convention, utils.resolve_project)
# ---------------------------------------------------------------------------


def test_project_as_projects_slash_slug(story: Path) -> None:
    assert main(["scene", f"projects/{SLUG}", "Form Two"]) == 0
    assert (story / "scenes" / "form_two.md").is_file()


def test_project_as_absolute_path(story: Path) -> None:
    assert main(["scene", str(story), "Form Three"]) == 0
    assert (story / "scenes" / "form_three.md").is_file()


def test_project_omitted_cwd_inside_story(story: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One positional = the title; the story comes from the cwd walk-up."""
    monkeypatch.chdir(story / "scenes")  # deep inside: walk-up must find the story root
    assert main(["scene", "Form Four"]) == 0
    assert (story / "scenes" / "form_four.md").is_file()


def test_project_omitted_outside_story_exits_1(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["scene", "No Story Here"]) == 1
    err = capsys.readouterr().err
    assert "no PROJECT given" in err
    assert "projects/<slug>" in err, "message must teach the accepted PROJECT forms"


def test_project_unknown_slug_exits_1(workshop: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scene", "no_such_story", "Title"]) == 1
    assert "not a story project" in capsys.readouterr().err


def test_project_absolute_non_story_dir_exits_1(workshop: Path) -> None:
    assert main(["scene", str(workshop), "Title"]) == 1


def test_project_absolute_story_outside_workshop(
    workshop: Path, story: Path, tmp_path: Path
) -> None:
    """A story copied outside the workshop still works via absolute path (cwd
    stays inside the workshop, which supplies the templates)."""
    outside = tmp_path / "standalone_story"
    shutil.copytree(story, outside)
    assert main(["scene", str(outside), "Far Away"]) == 0
    assert (outside / "scenes" / "far_away.md").is_file()


# ---------------------------------------------------------------------------
# positional-count disambiguation ([PROJECT] TITLE via nargs="*")
# ---------------------------------------------------------------------------


def test_zero_positionals_exits_1(workshop: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scene"]) == 1
    assert "expected [PROJECT] TITLE" in capsys.readouterr().err


def test_three_positionals_exits_1(story: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scene", SLUG, "Unquoted", "Title"]) == 1
    assert "got 3" in capsys.readouterr().err


def test_character_noun_is_name_in_error(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["character"]) == 1
    assert "expected [PROJECT] NAME" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# refuse / --force / .bak semantics (plan §3.4, mirrors new-story)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("command", "folder", "field", "ftype", "status"), CREATORS)
def test_slug_collision_refused_exit_2(
    story: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    folder: str,
    field: str,
    ftype: str,
    status: str,
) -> None:
    assert main([command, SLUG, "Dup Entry"]) == 0
    capsys.readouterr()
    assert main([command, SLUG, "Dup Entry"]) == 2
    assert "--force" in capsys.readouterr().err, "refusal must mention --force"
    assert not list((story / folder).glob("*.bak-*")), "no backup without --force"


def test_force_overwrites_keeps_backup_and_prints_it(
    story: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["scene", SLUG, "Dup"]) == 0
    target = story / "scenes" / "dup.md"
    target.write_text("OPERATOR EDIT\n", encoding="utf-8")
    capsys.readouterr()
    assert main(["scene", SLUG, "Dup", "--force"]) == 0
    backups = list(target.parent.glob("dup.md.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "OPERATOR EDIT\n", "backup keeps OLD bytes"
    assert parse_frontmatter(target.read_text(encoding="utf-8"))["title"] == "Dup"
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0] == str(target)
    assert str(backups[0]) in lines, "--force output must surface the .bak- path"


def test_force_on_fresh_target_creates_without_backup(
    story: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    assert main(["world", SLUG, "Moon Oven", "--force"]) == 0
    target = story / "world" / "moon_oven.md"
    assert capsys.readouterr().out.strip().splitlines() == [str(target)]
    assert not list(target.parent.glob("*.bak-*"))


# ---------------------------------------------------------------------------
# bad titles/names: clean UsageError exit 1 (plan §3.2, Appendix D)
# ---------------------------------------------------------------------------


def test_reserved_device_title_exits_1(story: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scene", SLUG, "Nul"]) == 1
    assert "reserved Windows device name" in capsys.readouterr().err
    assert not list((story / "scenes").glob("*.md")), "no file may be created"


def test_unsluggable_title_exits_1(story: Path) -> None:
    assert main(["scene", SLUG, "!!!"]) == 1


def test_bracketed_name_exits_1(story: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A [bracketed] name would round-trip out of frontmatter as a LIST."""
    assert main(["character", SLUG, "[Nova, Rocket]"]) == 1
    assert "parsed as a list" in capsys.readouterr().err
    assert not list((story / "characters").glob("*.md"))


# ---------------------------------------------------------------------------
# true subprocess tests through python -m shake_spear
# ---------------------------------------------------------------------------


def _run_ss(workshop: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "shake_spear", *args],
        cwd=workshop,
        capture_output=True,
        text=True,
        check=False,
    )


def test_subprocess_scene_create_then_refuse(workshop: Path, story: Path) -> None:
    result = _run_ss(workshop, "scene", SLUG, "Subprocess Scene")
    assert result.returncode == 0, result.stderr
    target = story / "scenes" / "subprocess_scene.md"
    assert target.is_file()
    assert result.stdout.strip().splitlines() == [str(target)]

    rerun = _run_ss(workshop, "scene", SLUG, "Subprocess Scene")
    assert rerun.returncode == 2, "refused overwrite must exit 2 through the real process"
    assert "Traceback" not in rerun.stderr


def test_subprocess_reserved_title_clean_exit_1(workshop: Path, story: Path) -> None:
    """Reserved-name title dies as a clean UsageError — exit 1, no traceback."""
    result = _run_ss(workshop, "scene", SLUG, "Nul")
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "reserved Windows device name" in result.stderr
