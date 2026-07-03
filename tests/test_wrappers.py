"""Validation tests for the workshop-root Claude Code wrappers + root guides
(plan §5.2, §11 Step 5).

The expected wrapper set is derived by globbing ``skills/*.md`` at test time,
so the tests stay correct if skills are ever added. The frontmatter checks
reimplement the plan §3.3 / Appendix D grammar in miniature, deliberately
local to this test file: the production parser lands in ``utils.py`` in
Step 6 and must not exist yet.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
WRAPPERS_DIR = ROOT / ".claude" / "skills"

# kebab wrapper name -> snake skill filename, derived from disk (README excluded).
EXPECTED = {
    p.stem.replace("_", "-"): p.name for p in SKILLS_DIR.glob("*.md") if p.name != "README.md"
}

# Root guide files authored in Step 5, held to the same encoding contract.
GUIDE_FILES = ["AGENTS.md", "CLAUDE.md"]

KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")


def _wrapper_path(kebab: str) -> Path:
    return WRAPPERS_DIR / kebab / "SKILL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _split_frontmatter(text: str, name: str) -> tuple[dict[str, str], str]:
    """Parse ``key: value`` frontmatter (plan §3.3 grammar, strict) + return body.

    Hyphenated keys (``user-invocable``) are part of the Appendix D contract.
    """
    lines = text.split("\n")
    assert lines[0] == "---", f"{name}: frontmatter must open with '---' as the first line"
    assert "---" in lines[1:], f"{name}: opening '---' has no closing '---'"
    end = lines.index("---", 1)
    parsed: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        assert ":" in line, f"{name}: not a 'key: value' pair: {line!r}"
        key, _, raw_value = line.partition(":")
        assert KEY_RE.fullmatch(key), f"{name}: bad frontmatter key: {key!r}"
        parsed[key] = raw_value.strip()
    return parsed, "\n".join(lines[end + 1 :])


def test_expected_set_is_nonempty() -> None:
    """Guard the deriving glob itself: an empty skills/ dir must not vacuously pass."""
    assert EXPECTED, "no skills/*.md found — wrapper expectations would be vacuous"
    assert "README.md" not in EXPECTED.values()


def test_one_wrapper_dir_per_skill() -> None:
    """Exactly one wrapper dir per skills/*.md (README excluded) — no extras."""
    assert WRAPPERS_DIR.is_dir(), f"missing wrapper root: {WRAPPERS_DIR}"
    on_disk = {d.name for d in WRAPPERS_DIR.iterdir() if d.is_dir()}
    assert on_disk == set(EXPECTED), (
        f"wrapper dirs != expected kebab names: "
        f"missing={sorted(set(EXPECTED) - on_disk)} extra={sorted(on_disk - set(EXPECTED))}"
    )
    for kebab in EXPECTED:
        assert _wrapper_path(kebab).is_file(), f"missing {kebab}/SKILL.md"


@pytest.mark.parametrize("kebab", sorted(EXPECTED))
def test_wrapper_frontmatter(kebab: str) -> None:
    parsed, _ = _split_frontmatter(_read(_wrapper_path(kebab)), kebab)
    assert parsed.get("name") == kebab, (
        f"{kebab}: frontmatter name {parsed.get('name')!r} != dir name {kebab!r}"
    )
    description = parsed.get("description", "")
    assert description, f"{kebab}: description must be nonempty"
    # Sanity guard only (not a plan requirement): a description should be a
    # one-liner, not a paragraph.
    assert len(description) <= 200, (
        f"{kebab}: description is {len(description)} chars — not a one-liner"
    )
    assert parsed.get("user-invocable") == "true", (
        f"{kebab}: 'user-invocable: true' missing or wrong: {parsed.get('user-invocable')!r}"
    )


@pytest.mark.parametrize("kebab", sorted(EXPECTED))
def test_wrapper_frontmatter_values_are_strict_yaml_safe(kebab: str) -> None:
    """No frontmatter VALUE may contain a ``: `` (colon+space) sequence.

    This is the stdlib-only stand-in for strict-YAML validation of Claude Code
    skill frontmatter: an unquoted ``: `` inside a plain-scalar value makes real
    YAML parsers reject the line ("mapping values are not allowed here"), so
    the skill may silently fail to load. The §3.3 grammar in
    ``_split_frontmatter`` is deliberately lenient and would not catch this.
    """
    text = _read(_wrapper_path(kebab))
    lines = text.split("\n")
    end = lines.index("---", 1)
    for line in lines[1:end]:
        if not line.strip():
            continue
        _key, _, value = line.partition(":")
        assert ": " not in value, (
            f"{kebab}: frontmatter value contains ': ' (strict YAML would reject "
            f"this as a nested mapping): {line!r}"
        )


@pytest.mark.parametrize("kebab", sorted(EXPECTED))
def test_wrapper_body_references_existing_skill_file(kebab: str) -> None:
    skill_filename = EXPECTED[kebab]
    _, body = _split_frontmatter(_read(_wrapper_path(kebab)), kebab)
    reference = f"`skills/{skill_filename}`"
    assert reference in body, f"{kebab}: body must reference {reference}"
    # Existence is checked on the paths the BODY actually names (not on
    # EXPECTED[kebab], which is derived from a disk glob and trivially exists):
    # a body referencing skills/typo.md must fail here.
    referenced = re.findall(r"skills/([\w.-]+\.md)", body)
    assert referenced, f"{kebab}: body names no skills/<file>.md path"
    for filename in referenced:
        assert (SKILLS_DIR / filename).is_file(), (
            f"{kebab}: body references skills/{filename}, which does not exist"
        )


@pytest.mark.parametrize(
    "rel_path",
    sorted([f".claude/skills/{kebab}/SKILL.md" for kebab in EXPECTED] + GUIDE_FILES),
)
def test_utf8_lf_no_bom(rel_path: str) -> None:
    path = ROOT / rel_path
    assert path.is_file(), f"missing file: {rel_path}"
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{rel_path}: has a UTF-8 BOM"
    assert b"\r" not in raw, f"{rel_path}: contains CR bytes (must be LF-only)"
    raw.decode("utf-8")  # must be valid UTF-8
