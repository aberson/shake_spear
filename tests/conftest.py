"""Shared pytest fixtures: the tmp workshop built from the repo's REAL assets.

No mocks anywhere — the filesystem is the real dependency. ``workshop`` copies
the actual ``templates/``, ``skills/``, root ``.claude/skills`` wrappers, and
``projects/_template/`` skeleton into ``tmp_path`` and chdirs inside, so every
test drives the production CLI against real content.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


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
