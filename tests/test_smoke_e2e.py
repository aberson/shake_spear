"""End-to-end smoke gate: ONE real story lifecycle through the CLI (plan §11 Step 12).

In a tmp workshop, drive the installed CLI through the complete surface —
``new-story → scene → character → world → session → index → recap → status →
daily → export → list-projects`` — with ZERO mocks, every action a TRUE
subprocess (``python -m shake_spear …``, the production caller). Drift-gate
rationale (Step 12's Problem statement; workspace code-quality rule "tests with
mocks can't see producer→consumer drift"): the per-step suites assert each module
deeply but in isolation, so drift across the templates → scaffold → creators →
indexer → recap chain would stay invisible to them — this gate exists to crash
first when any producer's output stops matching the next consumer's expectation.

BREADTH, not depth: per-stage assertions here are deliberately shallow (exit 0,
the artifact exists where §3.1/§4 say, the derived content reflects the inputs);
test_scaffold/test_creators/test_session/test_indexer/test_recap_status/
test_export own the deep per-command behavior. Business-logic quality is out of
scope (plan §11 Step 12) — the deliverable is "pipeline completes one real cycle
without crashing". Done-when: this file alone passes in well under 60s; the whole
cycle is timed and a wall-clock guard enforces that budget.

This is also the only suite-default real-git story: ``new-story`` runs WITHOUT
``--no-git``, so ``git init`` + the initial commit are exercised for real.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import STORY_FILES, SUBFOLDERS
from shake_spear.session import RECAP_END, RECAP_START, STATUS_SECTIONS
from shake_spear.utils import parse_frontmatter

TITLE = "Smoke Test Voyage"
SLUG = "smoke_test_voyage"

#: Plan §11 Step 12 Done-when: the full cycle completes in well under 60s.
CYCLE_BUDGET_SECONDS = 60.0

#: (command argv, CompletedProcess) — the full-cycle transcript, kept so every
#: failure message and the final zero-traceback sweep carry the real evidence
#: (workspace tee-from-start discipline).
Transcript = list[tuple[tuple[str, ...], "subprocess.CompletedProcess[str]"]]


def _tree_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    """Every file under ``root`` -> (mtime_ns, size): the writes-nothing probe."""
    return {
        str(p.relative_to(root)): (p.stat().st_mtime_ns, p.stat().st_size)
        for p in root.rglob("*")
        if p.is_file()
    }


def _evidence(args: tuple[str, ...], result: subprocess.CompletedProcess[str]) -> str:
    """One command's captured stdout/stderr, formatted for an assertion message."""
    return (
        f"$ ss {' '.join(args)}  [exit {result.returncode}]\n"
        f"--- stdout ---\n{result.stdout}--- stderr ---\n{result.stderr}"
    )


def test_full_cycle_smoke(workshop: Path) -> None:
    """new-story → scene → character → world → session → index → recap → status →
    daily → export → list-projects: one real cycle, real subprocesses, no crash."""
    if shutil.which("git") is None:  # pragma: no cover - git is on PATH in CI + dev
        pytest.skip("git not on PATH (this cycle exercises the real-git scaffold path)")

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Smoke Test",
        "GIT_AUTHOR_EMAIL": "smoke@example.com",
        "GIT_COMMITTER_NAME": "Smoke Test",
        "GIT_COMMITTER_EMAIL": "smoke@example.com",
    }
    transcript: Transcript = []
    started = time.perf_counter()

    def ss(*args: str) -> subprocess.CompletedProcess[str]:
        """One production call: ``python -m shake_spear …`` in the tmp workshop."""
        result = subprocess.run(
            [sys.executable, "-m", "shake_spear", *args],
            cwd=workshop,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        transcript.append((args, result))
        assert result.returncode == 0, _evidence(args, result)
        return result

    # -----------------------------------------------------------------------
    # new-story: full §3.1 anatomy + the real-git path (no --no-git)
    # -----------------------------------------------------------------------
    out = ss("new-story", TITLE, "--genre", "kids", "--mode", "playful")
    story = workshop / "projects" / SLUG
    assert Path(out.stdout.strip().splitlines()[-1]) == story, _evidence(*transcript[-1])
    for sub in SUBFOLDERS:
        assert (story / sub).is_dir(), f"missing folder {sub}/ (plan §3.1)"
    for name in STORY_FILES:
        assert (story / name).is_file(), f"missing root file {name} (plan §3.1)"
    index_stub = (story / "index.md").read_text(encoding="utf-8")
    assert "ss index" in index_stub, "index.md must start life as the derived-file stub"
    wrappers = {d.name for d in (story / ".claude" / "skills").iterdir() if d.is_dir()}
    skills = {p.stem for p in (workshop / "skills").glob("*.md") if p.name != "README.md"}
    assert len(wrappers) == len(skills), "one wrapper per skills/*.md (README excluded)"
    assert wrappers == {name.replace("_", "-") for name in skills}
    assert (story / ".git").is_dir(), "new-story without --no-git must git-init (plan §3.5)"
    rev_list = subprocess.run(
        ["git", "-C", str(story), "rev-list", "--count", "HEAD"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rev_list.returncode == 0, rev_list.stderr
    assert rev_list.stdout.strip() == "1", "exactly one initial commit (plan §3.5)"

    # -----------------------------------------------------------------------
    # scene / character / world: right folder, parseable frontmatter
    # -----------------------------------------------------------------------
    # (Actions via subprocess; the in-process utils parser is used for ASSERTIONS only.)
    creators = [
        ("scene", "scenes", "title", "The Moon Oven Ignites", "the_moon_oven_ignites.md"),
        ("character", "characters", "name", "Nova", "nova.md"),
        ("world", "world", "name", "The Crumb Belt", "the_crumb_belt.md"),
    ]
    for command, folder, field, value, filename in creators:
        result = ss(command, SLUG, value)
        target = story / folder / filename
        assert target.is_file(), _evidence(*transcript[-1])
        assert result.stdout.strip() == str(target), (
            f"must print the created path {target}\n{_evidence(*transcript[-1])}"
        )
        data = parse_frontmatter(target.read_text(encoding="utf-8"))
        assert data[field] == value, (
            f"{command}: frontmatter {field} must carry {value!r}, got {data[field]!r}"
        )
        assert data["type"], f"{command}: frontmatter type must be filled, got {data['type']!r}"

    # -----------------------------------------------------------------------
    # session: dated log with the generated links block
    # -----------------------------------------------------------------------
    result = ss("session", SLUG)
    session_log = Path(result.stdout.strip())
    assert session_log.is_file(), _evidence(*transcript[-1])
    assert session_log.parent == story / "sessions"
    assert session_log.name.endswith("_scene_45min.md"), (
        f"defaults are --type scene --minutes 45, got {session_log.name!r}"
    )
    session_text = session_log.read_text(encoding="utf-8")
    assert "## Relevant skills" in session_text, (
        f"generated links block missing from {session_log.name}:\n{session_text}"
    )
    assert "`../../skills/" in session_text, (
        f"skill links must be story-root-relative paths, got:\n{session_text}"
    )

    # -----------------------------------------------------------------------
    # index: stub replaced; every created entity appears
    # -----------------------------------------------------------------------
    ss("index", SLUG)
    index_text = (story / "index.md").read_text(encoding="utf-8")
    assert index_text != index_stub, "ss index must regenerate the new-story stub"
    assert "# Project Index" in index_text
    for rel in (
        "scenes/the_moon_oven_ignites.md",
        "characters/nova.md",
        "world/the_crumb_belt.md",
        f"sessions/{session_log.name}",
    ):
        assert rel in index_text, f"index.md must list {rel}"

    # -----------------------------------------------------------------------
    # recap: marker block populated, placeholder replaced (breadth only)
    # -----------------------------------------------------------------------
    # (Byte-level surgical-write preservation is tests/test_recap_status.py's depth.)
    ss("recap", SLUG)
    active_state_text = (story / "active_state.md").read_text(encoding="utf-8")
    block = active_state_text.partition(RECAP_START)[2].partition(RECAP_END)[0]
    assert "Recap generated by `ss recap`" in block, f"marker block not populated:\n{block}"
    assert "ss recap writes the" not in block, f"template placeholder must be replaced:\n{block}"

    # -----------------------------------------------------------------------
    # status: prints the 4 fields + newest session; writes NOTHING
    # -----------------------------------------------------------------------
    snapshot = _tree_snapshot(workshop)
    result = ss("status", SLUG)
    for field in STATUS_SECTIONS:
        assert field in result.stdout, _evidence(*transcript[-1])
    assert "Newest session:" in result.stdout, _evidence(*transcript[-1])
    assert _tree_snapshot(workshop) == snapshot, "ss status must write nothing (plan §4)"

    # -----------------------------------------------------------------------
    # daily: the freewrite/15 sugar
    # -----------------------------------------------------------------------
    result = ss("daily", SLUG)
    daily_log = Path(result.stdout.strip())
    assert daily_log.is_file(), _evidence(*transcript[-1])
    assert daily_log.parent == story / "sessions"
    assert daily_log.name.endswith("_freewrite_15min.md"), (
        f"daily = freewrite/15min (plan §4), got {daily_log.name!r}"
    )

    # -----------------------------------------------------------------------
    # export: manuscript carries the (operator-authored) draft
    # -----------------------------------------------------------------------
    draft_body = "The oven hummed to life over the quiet sea of dust."
    (story / "drafts" / "chapter_01.md").write_text(draft_body + "\n", encoding="utf-8")
    ss("export", SLUG)
    manuscript = story / "exports" / "manuscript.md"
    assert manuscript.is_file(), (
        f"export must write exports/manuscript.md (plan §4)\n{_evidence(*transcript[-1])}"
    )
    manuscript_text = manuscript.read_text(encoding="utf-8")
    assert "## chapter_01.md" in manuscript_text, (
        f"per-draft `## <filename>` heading missing from:\n{manuscript_text}"
    )
    assert draft_body in manuscript_text, (
        f"draft body must survive into the manuscript, got:\n{manuscript_text}"
    )

    # -----------------------------------------------------------------------
    # list-projects: the story shows up with its title
    # -----------------------------------------------------------------------
    result = ss("list-projects")
    assert SLUG in result.stdout, _evidence(*transcript[-1])
    assert TITLE in result.stdout, _evidence(*transcript[-1])

    # -----------------------------------------------------------------------
    # FINAL: zero tracebacks anywhere; whole cycle inside the budget
    # -----------------------------------------------------------------------
    elapsed = time.perf_counter() - started
    for args, result in transcript:
        assert "Traceback" not in result.stderr, _evidence(args, result)
    assert elapsed < CYCLE_BUDGET_SECONDS, (
        f"full cycle took {elapsed:.1f}s — plan §11 Step 12 Done-when demands well under "
        f"{CYCLE_BUDGET_SECONDS:.0f}s"
    )
