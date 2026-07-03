"""Shared pytest fixtures: the tmp workshop built from the repo's REAL assets.

No mocks anywhere — the filesystem is the real dependency. ``workshop`` copies
the actual ``templates/``, ``skills/``, root ``.claude/skills`` wrappers, and
``projects/_template/`` skeleton into ``tmp_path`` and chdirs inside, so every
test drives the production CLI against real content. ``story`` (slug
:data:`SLUG`) is scaffolded inside it through the production ``new-story``
command — the single definition shared by the creator + session suites.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from shake_spear.cli import main

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The slug ``new-story`` derives from the shared story fixture's title.
SLUG = "kids_space_bakery"

#: The nine story subfolders every scaffold must create (plan §3.1) — single
#: definition shared by the scaffold + smoke suites.
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

#: The nine root story files every scaffold must create (plan §3.1) — single
#: definition shared by the scaffold + smoke suites.
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


@pytest.fixture()
def workshop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A tmp workshop with the real templates/skills/wrappers/skeleton; cwd inside it."""
    root = tmp_path / "workshop"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "tmp-workshop"\n', encoding="utf-8")
    for rel in ("templates", "skills", ".claude/skills", "projects/_template"):
        shutil.copytree(REPO_ROOT / rel, root / rel)
    monkeypatch.chdir(root)
    return root


@pytest.fixture()
def story(workshop: Path) -> Path:
    """A real story scaffolded through the production CLI (``--no-git``)."""
    assert main(["new-story", "Kids Space Bakery", "--genre", "kids", "--no-git"]) == 0
    return workshop / "projects" / SLUG
