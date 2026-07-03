"""``ss scene`` / ``ss character`` / ``ss world`` (plan §4, §6).

Thin named-entity creators: each renders its template from the workshop's
``templates/``, fills the single ``{{title}}``/``{{name}}`` placeholder, and
writes ``<folder>/<slugified value>.md`` inside the resolved story through
:func:`shake_spear.utils.safe_write` with ``mode="refuse"`` (plan §3.4:
existing target → exit 2 unless ``--force``, which keeps a timestamped
``.bak-`` backup). All invariants live in ``utils`` — PROJECT resolution is
:func:`shake_spear.utils.resolve_project` (shared with Steps 8-11), slugs are
:func:`shake_spear.utils.slugify`, list-shaped input is rejected by
:func:`shake_spear.utils.reject_list_shaped`.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from shake_spear.utils import (
    UsageError,
    reject_list_shaped,
    render_template,
    resolve_project,
    safe_write,
    slugify,
    templates_dir,
)


@dataclass(frozen=True)
class CreatorSpec:
    """One named-entity creator (the plan §4 scene/character/world rows).

    ``placeholder`` is both the template's ``{{...}}`` token and the
    frontmatter field the value lands in; the CLI also derives the
    positional's display name (TITLE/NAME) from it.
    """

    template: str  # filename under templates/
    placeholder: str  # the template's one {{placeholder}}: "title" or "name"
    folder: str  # destination subfolder inside the story


#: command name -> spec; ``cli.build_parser`` iterates this (single source of
#: truth for the template/placeholder/folder mapping — no drift into help text).
SPECS: Mapping[str, CreatorSpec] = MappingProxyType(
    {
        "scene": CreatorSpec("scene_card.md", "title", "scenes"),
        "character": CreatorSpec("character_profile.md", "name", "characters"),
        "world": CreatorSpec("world_element.md", "name", "world"),
    }
)


def create_entity(
    kind: str, story_root: Path, value: str, *, force: bool = False
) -> tuple[Path, list[Path]]:
    """Create one named entity file; return ``(created_path, backup_paths)``.

    ``kind`` is a :data:`SPECS` key; ``value`` is the operator's title/name
    (slugified for the filename, verbatim in frontmatter). Overwrite policy is
    ``safe_write(mode="refuse")`` per plan §3.4.
    """
    spec = SPECS[kind]
    reject_list_shaped(value, spec.placeholder)
    slug = slugify(value)
    template_path = templates_dir(story_root) / spec.template
    if not template_path.is_file():
        raise UsageError(f"missing template: {template_path}")
    content = render_template(template_path, {spec.placeholder: value})
    backups: list[Path] = []
    target = story_root / spec.folder / f"{slug}.md"
    written = safe_write(target, content, "refuse", force=force, backups=backups)
    return written, backups


def _split_positionals(values: list[str], noun: str) -> tuple[str | None, str]:
    """Disambiguate the ``[PROJECT] <noun>`` positional pair (plan §4).

    One positional → it is the title/name (PROJECT omitted, cwd walk-up);
    two → PROJECT then title/name; any other count is a :class:`UsageError`.
    """
    if len(values) == 1:
        return None, values[0]
    if len(values) == 2:
        return values[0], values[1]
    raise UsageError(
        f"expected [PROJECT] {noun} (one or two positional arguments), got {len(values)}"
    )


def _cmd_create(args: argparse.Namespace, kind: str) -> int:
    """Shared ``args.func`` body: resolve, create, print paths (plan §4)."""
    noun = SPECS[kind].placeholder.upper()
    project_arg, value = _split_positionals(args.positionals, noun)
    story_root = resolve_project(project_arg, Path.cwd())
    written, backups = create_entity(kind, story_root, value, force=args.force)
    print(written)
    for backup in backups:
        print(backup)
    return 0


def cmd_scene(args: argparse.Namespace) -> int:
    """``ss scene [PROJECT] "Title" [--force]`` → ``scenes/<slug>.md``."""
    return _cmd_create(args, "scene")


def cmd_character(args: argparse.Namespace) -> int:
    """``ss character [PROJECT] "Name" [--force]`` → ``characters/<slug>.md``."""
    return _cmd_create(args, "character")


def cmd_world(args: argparse.Namespace) -> int:
    """``ss world [PROJECT] "Name" [--force]`` → ``world/<slug>.md``."""
    return _cmd_create(args, "world")
