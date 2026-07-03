"""Integration tests for ``ss new-story`` / ``ss list-projects`` (plan §11 Step 6).

All scaffold tests go through the production CLI entry point — ``cli.main()``
in-process (the exact function the ``ss`` console script calls) plus at least
one true ``python -m shake_spear`` subprocess. tmp_path-based: each test
builds a real tmp workshop (shared ``workshop`` fixture in ``conftest.py``)
from the repo's actual ``templates/``, ``skills/``, root wrappers, and
``projects/_template/`` skeleton. The only test double is a monkeypatched
``shutil.which`` for the no-git-on-PATH branch.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from shake_spear.cli import main
from shake_spear.utils import parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent

SUBFOLDERS = [
    "characters",
    "world",
    "scenes",
    "drafts",
    "sessions",
    "feedback",
    "revisions",
    "prompts",
    "exports",
]

STORY_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "story_bible.md",
    "active_state.md",
    "continuity.md",
    "decisions.md",
    "index.md",
    ".gitignore",
]

# kebab wrapper names derived from the real skills/ dir (README excluded).
EXPECTED_WRAPPERS = {
    p.stem.replace("_", "-") for p in (REPO_ROOT / "skills").glob("*.md") if p.name != "README.md"
}


def _new_story(*extra: str) -> int:
    """Run new-story through the production entry point with standard args."""
    return main(["new-story", "Kids Space Bakery", "--genre", "kids", "--mode", "playful", *extra])


# ---------------------------------------------------------------------------
# _template skeleton purity (plan §3.1: skeleton ONLY, no story files)
# ---------------------------------------------------------------------------


def test_template_skeleton_is_pure() -> None:
    template = REPO_ROOT / "projects" / "_template"
    assert not list(template.rglob("*.md")), "_template must hold no story files (plan §3.1)"
    assert not (template / ".gitkeep").exists(), "root .gitkeep removed once dir has content"
    for sub in SUBFOLDERS:
        assert (template / sub / ".gitkeep").is_file(), f"missing {sub}/.gitkeep"
    gitignore = (template / ".gitignore").read_text(encoding="utf-8")
    patterns = [
        line.strip()
        for line in gitignore.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for junk in (".DS_Store", "Thumbs.db", "~$*"):
        assert junk in patterns
    assert not any("exports" in p for p in patterns), "exports/ stays committed (plan §3.1)"
    assert not any("drafts" in p for p in patterns), "never ignore creative content"


# ---------------------------------------------------------------------------
# ss new-story — complete §3.1 anatomy
# ---------------------------------------------------------------------------


def test_new_story_creates_complete_anatomy(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    story = workshop / "projects" / "kids_space_bakery"
    for sub in SUBFOLDERS:
        assert (story / sub).is_dir(), f"missing folder {sub}/"
        assert (story / sub / ".gitkeep").is_file(), f"missing {sub}/.gitkeep"
    for name in STORY_FILES:
        assert (story / name).is_file(), f"missing story file {name}"
    wrappers = {d.name for d in (story / ".claude" / "skills").iterdir() if d.is_dir()}
    assert EXPECTED_WRAPPERS, "repo skills/ must yield at least one wrapper"
    assert wrappers == EXPECTED_WRAPPERS
    for kebab in wrappers:
        assert (story / ".claude" / "skills" / kebab / "SKILL.md").is_file()
    # index.md is the derived-file stub until `ss index` (Step 9) regenerates it.
    assert "ss index" in (story / "index.md").read_text(encoding="utf-8")


def test_new_story_renders_story_bible_frontmatter(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    bible = workshop / "projects" / "kids_space_bakery" / "story_bible.md"
    data = parse_frontmatter(bible.read_text(encoding="utf-8"))
    assert data["type"] == "story_bible"
    assert data["title"] == "Kids Space Bakery"
    assert data["genre"] == "kids"
    assert data["mode"] == "playful"
    assert data["audience"] == "", "audience is left blank for the operator (plan Appendix E)"
    assert data["status"] == "seed"


def test_new_story_renders_placeholders_in_guides(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    story = workshop / "projects" / "kids_space_bakery"
    for name in ("README.md", "AGENTS.md", "CLAUDE.md"):
        text = (story / name).read_text(encoding="utf-8")
        assert "{{" not in text, f"{name}: unrendered placeholder left behind"
        assert "Kids Space Bakery" in text
    assert "kids_space_bakery" in (story / "README.md").read_text(encoding="utf-8")


def test_new_story_prints_created_paths_then_story_root(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _new_story("--no-git") == 0
    lines = capsys.readouterr().out.strip().splitlines()
    story = workshop / "projects" / "kids_space_bakery"
    assert lines[-1] == str(story), "last line must be the story root"
    created = [Path(line) for line in lines[:-1]]
    assert created, "must print every created path, one per line"
    for path in created:
        assert path.exists(), f"printed path does not exist: {path}"
    printed = {str(p) for p in created}
    assert str(story / "story_bible.md") in printed
    assert str(story / ".gitignore") in printed
    assert str(story / ".claude" / "skills" / "immersive-session" / "SKILL.md") in printed


# ---------------------------------------------------------------------------
# refuse / --force semantics on the story dir (plan §3.4, §4)
# ---------------------------------------------------------------------------


def test_new_story_rerun_without_force_exits_2(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    assert _new_story("--no-git") == 2


def test_new_story_rerun_with_force_backs_up_and_overwrites(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    bible = workshop / "projects" / "kids_space_bakery" / "story_bible.md"
    bible.write_text("OPERATOR EDIT\n", encoding="utf-8")
    assert _new_story("--no-git", "--force") == 0
    backups = list(bible.parent.glob("story_bible.md.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "OPERATOR EDIT\n", "backup keeps OLD bytes"
    assert "OPERATOR EDIT" not in bible.read_text(encoding="utf-8")
    assert parse_frontmatter(bible.read_text(encoding="utf-8"))["title"] == "Kids Space Bakery"


def test_new_story_force_prints_backup_paths(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Plan §4: every path the command created or updated is printed — backups included."""
    assert _new_story("--no-git") == 0
    bible = workshop / "projects" / "kids_space_bakery" / "story_bible.md"
    bible.write_text("OPERATOR EDIT\n", encoding="utf-8")
    capsys.readouterr()  # drop first-run output
    assert _new_story("--no-git", "--force") == 0
    lines = capsys.readouterr().out.strip().splitlines()
    backup = next(bible.parent.glob("story_bible.md.bak-*"))
    assert str(backup) in lines, "--force output must surface the .bak- path"
    assert lines[-1] == str(bible.parent), "story root stays the last line"


@pytest.mark.parametrize("bad_slug", ["Bad Slug", "_foo", "foo_", "___", "_template", "nul"])
def test_new_story_bad_slug_exits_1(workshop: Path, bad_slug: str) -> None:
    assert main(["new-story", "X", "--slug", bad_slug, "--no-git"]) == 1
    # No story was scaffolded there (for _template: the pristine skeleton stays file-free;
    # .exists() on the bare "nul" path would hit the Windows device, so check a child).
    assert not (workshop / "projects" / bad_slug / "story_bible.md").exists()


def test_new_story_unsluggable_title_exits_1(workshop: Path) -> None:
    assert main(["new-story", "!!!", "--no-git"]) == 1


def test_new_story_reserved_device_title_exits_1(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """slugify("Nul") -> "nul" must be rejected before any projects/nul path exists."""
    assert main(["new-story", "Nul", "--no-git"]) == 1
    assert "reserved Windows device name" in capsys.readouterr().err
    assert not (workshop / "projects" / "nul" / "story_bible.md").exists()


def test_new_story_bracketed_title_exits_1(
    workshop: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A [bracketed] title would round-trip out of story_bible frontmatter as a LIST."""
    assert main(["new-story", "[Nova, Rocket]", "--no-git"]) == 1
    assert "parsed as a list" in capsys.readouterr().err
    assert not (workshop / "projects" / "nova_rocket").exists()


def test_new_story_outside_workshop_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["new-story", "Lost Story", "--no-git"]) == 1


# ---------------------------------------------------------------------------
# git model (plan §3.5)
# ---------------------------------------------------------------------------


def test_new_story_no_git_skips_repo(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    assert not (workshop / "projects" / "kids_space_bakery" / ".git").exists()


def test_new_story_git_missing_on_path_is_graceful(
    workshop: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Plan §3.5: no git on PATH degrades to a notice — scaffold still succeeds."""
    import shake_spear.scaffold as scaffold_module

    monkeypatch.setattr(scaffold_module.shutil, "which", lambda _cmd: None)
    assert _new_story() == 0  # WITHOUT --no-git: the git branch is actually reached
    story = workshop / "projects" / "kids_space_bakery"
    assert story.is_dir()
    assert (story / "story_bible.md").is_file()
    assert not (story / ".git").exists()
    err = capsys.readouterr().err
    assert "ss: notice:" in err
    assert "git not found on PATH" in err


def test_new_story_git_init_plus_one_commit(
    workshop: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    for var, value in (
        ("GIT_AUTHOR_NAME", "Test"),
        ("GIT_AUTHOR_EMAIL", "test@example.com"),
        ("GIT_COMMITTER_NAME", "Test"),
        ("GIT_COMMITTER_EMAIL", "test@example.com"),
    ):
        monkeypatch.setenv(var, value)
    assert _new_story() == 0
    story = workshop / "projects" / "kids_space_bakery"
    assert (story / ".git").is_dir()
    count = subprocess.run(
        ["git", "-C", str(story), "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert count.returncode == 0
    assert count.stdout.strip() == "1"
    subject = subprocess.run(
        ["git", "-C", str(story), "log", "-1", "--format=%s"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert subject.stdout.strip() == "story scaffold: kids_space_bakery"


# ---------------------------------------------------------------------------
# story-local wrappers (plan §5.2, Appendix C)
# ---------------------------------------------------------------------------


def test_wrapper_frontmatter_and_body(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    story = workshop / "projects" / "kids_space_bakery"
    for kebab in EXPECTED_WRAPPERS:
        skill_filename = kebab.replace("-", "_") + ".md"
        text = (story / ".claude" / "skills" / kebab / "SKILL.md").read_text(encoding="utf-8")
        data = parse_frontmatter(text)
        assert data["name"] == kebab
        assert data["user-invocable"] == "true"
        root_wrapper = (workshop / ".claude" / "skills" / kebab / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert data["description"] == parse_frontmatter(root_wrapper)["description"], (
            f"{kebab}: description must be reused from the root wrapper (single source of truth)"
        )
        assert f"`../../skills/{skill_filename}`" in text, (
            f"{kebab}: body must reference ../../skills/{skill_filename}"
        )
        assert "standalone clone" in text, f"{kebab}: missing degradation line (Appendix C)"
        assert (workshop / "skills" / skill_filename).is_file()


def test_written_files_are_utf8_lf_no_bom(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    story = workshop / "projects" / "kids_space_bakery"
    checked = [
        story / "story_bible.md",
        story / "README.md",
        story / ".gitignore",
        story / ".claude" / "skills" / "immersive-session" / "SKILL.md",
    ]
    for path in checked:
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{path.name}: has a UTF-8 BOM"
        assert b"\r" not in raw, f"{path.name}: contains CR bytes"
        raw.decode("utf-8")


# ---------------------------------------------------------------------------
# true subprocess test through the installed entry point
# ---------------------------------------------------------------------------


def test_subprocess_new_story_then_list_projects(workshop: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shake_spear",
            "new-story",
            "Space Bakery",
            "--slug",
            "space_bakery",
            "--genre",
            "kids",
            "--no-git",
        ],
        cwd=workshop,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    story = workshop / "projects" / "space_bakery"
    assert story.is_dir()
    lines = result.stdout.strip().splitlines()
    assert lines[-1] == str(story)
    assert (story / "story_bible.md").is_file()

    listing = subprocess.run(
        [sys.executable, "-m", "shake_spear", "list-projects"],
        cwd=workshop,
        capture_output=True,
        text=True,
        check=False,
    )
    assert listing.returncode == 0, listing.stderr
    assert "space_bakery" in listing.stdout
    assert "Space Bakery" in listing.stdout

    rerun = subprocess.run(
        [sys.executable, "-m", "shake_spear", "new-story", "Space Bakery", "--no-git"],
        cwd=workshop,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rerun.returncode == 2, "refused overwrite must exit 2 through the real process"


# ---------------------------------------------------------------------------
# ss list-projects
# ---------------------------------------------------------------------------


def test_list_projects_empty(workshop: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["list-projects"]) == 0
    assert "(no story projects yet)" in capsys.readouterr().out


def test_list_projects_table(workshop: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _new_story("--no-git") == 0
    # A hand-made project dir with no story_bible.md degrades to blanks.
    (workshop / "projects" / "bare_dir").mkdir()
    capsys.readouterr()  # drop new-story output
    assert main(["list-projects"]) == 0
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert lines[0].split() == ["slug", "title", "genre", "status"]
    rows = {line.split()[0]: line for line in lines[1:]}
    assert "kids_space_bakery" in rows
    assert "Kids Space Bakery" in rows["kids_space_bakery"]
    assert "kids" in rows["kids_space_bakery"]
    assert "seed" in rows["kids_space_bakery"]
    assert "bare_dir" in rows, "projects without story_bible.md still get a row"
    assert rows["bare_dir"].split() == ["bare_dir"], "missing fields degrade to blanks"
    assert "_template" not in rows


def test_list_projects_crlf_story_bible(workshop: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A CRLF story_bible.md (external editor) must still yield a populated row."""
    project = workshop / "projects" / "crlf_story"
    project.mkdir(parents=True)
    (project / "story_bible.md").write_bytes(
        b"---\r\ntype: story_bible\r\ntitle: CRLF Story\r\n"
        b"genre: mystery\r\nstatus: seed\r\n---\r\nBody\r\n"
    )
    assert main(["list-projects"]) == 0
    out = capsys.readouterr().out
    row = next(line for line in out.splitlines() if line.startswith("crlf_story"))
    assert "CRLF Story" in row
    assert "mystery" in row
    assert "seed" in row


def test_list_projects_writes_nothing(workshop: Path) -> None:
    assert _new_story("--no-git") == 0
    story = workshop / "projects" / "kids_space_bakery"
    before = {p: p.stat().st_mtime_ns for p in story.rglob("*") if p.is_file()}
    assert main(["list-projects"]) == 0
    after = {p: p.stat().st_mtime_ns for p in story.rglob("*") if p.is_file()}
    assert before == after
