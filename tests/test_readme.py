"""Step 14 gate: the friendly root README + ``.vscode/tasks.json``.

README checks are anchor-based — one stable keyword per seed-§13 topic — so the
headings can keep friendly wording without the test going stale. The seed §16
"Tiny Scene" exercise is verified line-by-line VERBATIM against the fenced
block extracted from ``docs/seed.md`` itself, so the seed stays the single
source of truth (no second copy of the exercise text in this file to drift).
The tasks.json checks parse the real JSON: schema version, every required task
label, and that every ``${input:...}`` reference resolves to a declared
``promptString`` input.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
TASKS_JSON = REPO_ROOT / ".vscode" / "tasks.json"
SEED = REPO_ROOT / "docs" / "seed.md"

#: One stable, case-insensitive keyword per seed-§13 topic. Each must appear in
#: at least one README heading — that heading is the topic's section.
TOPIC_ANCHORS = [
    "what",  # 1. what this project is
    "install",  # 2. how to install/run locally
    "new story",  # 3. how to create a new story
    "session",  # 4. how to start a writing session
    "scene",  # 5. how to create a scene/character/world element
    "index",  # 6. how to regenerate an index
    "code .",  # 7. how to open a subproject directly
    "skills",  # 8. how to use the shared skills
    "exercise",  # 9. suggested first writing exercise
]

#: Every task label plan §11 Step 14 requires in .vscode/tasks.json.
REQUIRED_TASK_LABELS = [
    "ss: new-story",
    "ss: session",
    "ss: index",
    "ss: recap",
    "ss: status",
    "ss: list-projects",
    "ss: export",
    "pytest",
]

INPUT_REF_RE = re.compile(r"\$\{input:([A-Za-z0-9_]+)\}")


def _readme_headings() -> list[str]:
    text = README.read_text(encoding="utf-8")
    # Strip fenced code blocks first: bash comments and the embedded exercise
    # block start with '#' and would otherwise count as headings, making the
    # 'session'/'scene' topic gates vacuous (review finding, Step 14).
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return [m.group(1).strip().lower() for m in re.finditer(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)]


def _seed_exercise_lines() -> list[str]:
    """The non-empty lines of the seed §16 fenced ``markdown`` block, verbatim."""
    seed = SEED.read_text(encoding="utf-8")
    _, _, section = seed.partition("## 16.")
    assert section, "docs/seed.md has no '## 16.' section"
    match = re.search(r"```markdown\n(.*?)```", section, re.DOTALL)
    assert match, "seed §16 has no fenced ```markdown block"
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    assert lines, "seed §16 fenced block is empty"
    return lines


def _tasks_data() -> dict[str, Any]:
    data = json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


# --- README -----------------------------------------------------------------


@pytest.mark.parametrize("anchor", TOPIC_ANCHORS)
def test_readme_has_a_heading_per_seed_13_topic(anchor: str) -> None:
    headings = _readme_headings()
    assert any(anchor in heading for heading in headings), (
        f"no README heading contains {anchor!r}; headings: {headings}"
    )


def test_readme_contains_seed_16_exercise_verbatim() -> None:
    text = README.read_text(encoding="utf-8")
    for line in _seed_exercise_lines():
        assert line in text, f"seed §16 exercise line missing from README: {line!r}"


# --- .vscode/tasks.json ------------------------------------------------------


def test_tasks_json_schema_version() -> None:
    assert _tasks_data()["version"] == "2.0.0"


def test_tasks_json_has_all_required_task_labels() -> None:
    labels = [task["label"] for task in _tasks_data()["tasks"]]
    missing = [label for label in REQUIRED_TASK_LABELS if label not in labels]
    assert not missing, f"tasks.json missing task labels: {missing}"


def test_tasks_json_input_references_are_declared() -> None:
    data = _tasks_data()
    declared = {entry["id"] for entry in data.get("inputs", [])}
    referenced = set(INPUT_REF_RE.findall(json.dumps(data["tasks"])))
    assert referenced, "expected at least one ${input:...} reference in tasks"
    undeclared = referenced - declared
    assert not undeclared, f"tasks reference undeclared inputs: {undeclared}"
    for entry in data.get("inputs", []):
        assert entry["type"] == "promptString", f"input {entry['id']!r} is not a promptString"


# --- encoding ----------------------------------------------------------------


@pytest.mark.parametrize("path", [README, TASKS_JSON], ids=["README.md", ".vscode/tasks.json"])
def test_utf8_lf_no_bom(path: Path) -> None:
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path.name} has a UTF-8 BOM"
    raw.decode("utf-8")  # raises on non-UTF-8 bytes
    assert b"\r" not in raw, f"{path.name} contains CR (CRLF or bare-CR) line endings"
