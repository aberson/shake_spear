"""Command-line interface for shake_spear (the ``ss`` entry point).

The parser is built in :func:`build_parser`; subcommands register there and
dispatch through ``args.func``. Error mapping per plan §4: ``UsageError`` →
exit 1, ``RefuseError`` → exit 2 (argparse usage errors also exit 1 via
:class:`_Parser`).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from typing import NoReturn

from shake_spear import __version__, creators, indexer, scaffold, session
from shake_spear.utils import RefuseError, UsageError

PROG = "ss"


class _Parser(argparse.ArgumentParser):
    """ArgumentParser honoring the plan §4 exit-code contract for usage errors.

    argparse's default error path exits 2, which §4 reserves for refused
    overwrites; usage errors (unknown command, bad/missing arguments) must
    print help and exit 1. Subparsers inherit this class automatically.
    """

    def error(self, message: str) -> NoReturn:
        self.print_help(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``ss`` argument parser with all subcommands."""
    parser = _Parser(
        prog=PROG,
        description="shake_spear: markdown-first creative writing workshop CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    new_story = subparsers.add_parser(
        "new-story",
        help="scaffold projects/<slug>/ from the skeleton + templates",
        description="Scaffold a new story project (plan §3.1 anatomy) and git-init it.",
    )
    new_story.add_argument("title", help='story title, e.g. "Kids Space Bakery"')
    new_story.add_argument("--slug", help="explicit slug [a-z0-9_]+ (default: slugified title)")
    new_story.add_argument("--genre", default="", help="genre recorded in story_bible.md")
    new_story.add_argument("--mode", default="", help="mode recorded in story_bible.md")
    new_story.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing project's generated files (keeps .bak- backups)",
    )
    new_story.add_argument(
        "--no-git",
        dest="no_git",
        action="store_true",
        help="skip git init + initial commit",
    )
    new_story.set_defaults(func=scaffold.cmd_new_story)

    list_projects = subparsers.add_parser(
        "list-projects",
        help="table of story projects under projects/ (writes nothing)",
        description="List projects/* (excluding _template): slug, title, genre, status.",
    )
    list_projects.set_defaults(func=scaffold.cmd_list_projects)

    creator_funcs = {
        "scene": creators.cmd_scene,
        "character": creators.cmd_character,
        "world": creators.cmd_world,
    }
    for kind, spec in creators.SPECS.items():
        noun = spec.placeholder.upper()  # TITLE / NAME
        creator = subparsers.add_parser(
            kind,
            help=f"create {spec.folder}/<slug>.md from templates/{spec.template}",
            description=(
                f"Create {spec.folder}/<slugified {spec.placeholder}>.md from "
                f"templates/{spec.template} with the {spec.placeholder} filled into "
                f"frontmatter. Positionals: [PROJECT] {noun} - one positional is the "
                f"{noun} (the project is detected by walking up from the current "
                f"directory); two positionals are PROJECT then {noun}. PROJECT accepts "
                "a bare slug, projects/<slug>, or an absolute path. An existing target "
                "exits 2 unless --force (which keeps a .bak- backup)."
            ),
        )
        creator.add_argument(
            "positionals",
            nargs="*",
            metavar=f"[PROJECT] {noun}",
            help=f"optional project, then the {spec.placeholder} (quote multi-word values)",
        )
        creator.add_argument(
            "--force",
            action="store_true",
            help="overwrite an existing file (a timestamped .bak- backup is kept)",
        )
        creator.set_defaults(func=creator_funcs[kind])

    project_help = (
        "optional story project: a bare slug, projects/<slug>, or an absolute path "
        "(omit it when the current directory is inside a story)"
    )

    session_cmd = subparsers.add_parser(
        "session",
        help="create sessions/<date>_<type>_<minutes>min.md from templates/session_log.md",
        description=(
            "Create a dated session log with the frontmatter filled, a summary pulled "
            "from active_state.md, and links to the type-relevant shared skills. A "
            "same-day collision appends _b.._z instead of refusing. Put flags after "
            "the project, e.g.: ss session kids_space_bakery --type scene --minutes 45"
        ),
    )
    session_cmd.add_argument("project", nargs="?", metavar="PROJECT", help=project_help)
    session_cmd.add_argument(
        "--type",
        default=session.DEFAULT_TYPE,
        help=(
            f"session type (default: {session.DEFAULT_TYPE}); known types: "
            f"{', '.join(session.KNOWN_TYPES)}; free-form values are accepted "
            "and slugified into the filename"
        ),
    )
    session_cmd.add_argument(
        "--minutes",
        type=int,
        default=session.DEFAULT_MINUTES,
        help=f"planned session length in minutes, positive (default: {session.DEFAULT_MINUTES})",
    )
    session_cmd.set_defaults(func=session.cmd_session)

    daily = subparsers.add_parser(
        "daily",
        help="daily freewrite log (sugar for: ss session PROJECT --type freewrite --minutes 15)",
        description=(
            "Create today's freewrite session log - the same code path as "
            "ss session PROJECT --type freewrite --minutes 15."
        ),
    )
    daily.add_argument("project", nargs="?", metavar="PROJECT", help=project_help)
    daily.set_defaults(func=session.cmd_daily)

    index_cmd = subparsers.add_parser(
        "index",
        help="regenerate the derived index.md (sections + recently-modified, no --force)",
        description=(
            "Regenerate <story>/index.md from the story's markdown files: per-file "
            "sections (story files, characters, world elements, scenes, drafts, "
            "sessions, feedback, revisions) plus the top-10 recently-modified block. "
            "index.md is a derived artifact - regenerated freely, never backed up. "
            "Dot-directories (.claude/, .git/) and exports/ are not scanned."
        ),
    )
    index_cmd.add_argument("project", nargs="?", metavar="PROJECT", help=project_help)
    index_cmd.set_defaults(func=indexer.cmd_index)

    export_cmd = subparsers.add_parser(
        "export",
        help="concatenate drafts/*.md into the derived exports/manuscript.md",
        description=(
            "Concatenate drafts/*.md (files only, lexicographic filename order) into "
            "exports/manuscript.md, each part preceded by an '## <filename>' heading "
            "with its frontmatter stripped so the manuscript reads as prose. The "
            "default manuscript is a derived artifact - regenerated freely, never "
            "backed up; drafts are strictly read-only (--out may not point inside "
            "drafts/). An existing --out target other than the default exits 2 "
            "unless --force. An empty drafts/ prints a friendly message and writes "
            "nothing (exit 0)."
        ),
    )
    export_cmd.add_argument("project", nargs="?", metavar="PROJECT", help=project_help)
    export_cmd.add_argument(
        "--out",
        metavar="PATH",
        help=(
            "write the manuscript to PATH instead of <story>/exports/manuscript.md "
            "(relative PATH resolves against the current directory; parents created); "
            "may not point inside the story's drafts/ tree"
        ),
    )
    export_cmd.add_argument(
        "--force",
        action="store_true",
        help=(
            "overwrite an existing --out target (a timestamped .bak- backup is kept); "
            "the default exports/manuscript.md regenerates freely without it"
        ),
    )
    export_cmd.set_defaults(func=indexer.cmd_export)

    recap_cmd = subparsers.add_parser(
        "recap",
        help='rewrite ONLY the ss:recap marker block in active_state.md ("start here next time")',
        description=(
            "Read active_state.md, continuity.md, the latest 3 session logs, and cheap "
            "index counts; rewrite ONLY the text between the <!-- ss:recap:start --> and "
            "<!-- ss:recap:end --> markers in active_state.md (the block is appended at "
            "the end of the file if the markers are absent). Everything outside the "
            "markers is preserved byte-for-byte. A fresh story still writes the block "
            "with placeholders and exits 0."
        ),
    )
    recap_cmd.add_argument("project", nargs="?", metavar="PROJECT", help=project_help)
    recap_cmd.set_defaults(func=session.cmd_recap)

    status_cmd = subparsers.add_parser(
        "status",
        help="print current status / scene / open loops / next tiny action (writes nothing)",
        description=(
            "Print (stdout only, writes nothing): Current status, Current scene or "
            "chapter, Open loops, and Next tiny action from active_state.md, plus the "
            "newest session filename."
        ),
    )
    status_cmd.add_argument("project", nargs="?", metavar="PROJECT", help=project_help)
    status_cmd.set_defaults(func=session.cmd_status)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Accepts an explicit ``argv`` for testability; ``None`` means
    ``sys.argv[1:]``. Returns the process exit code (``--version`` and
    ``--help`` exit via :class:`SystemExit` raised by argparse).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    func: Callable[[argparse.Namespace], int] | None = getattr(args, "func", None)
    if func is None:
        # Bare `ss`: print help and succeed.
        parser.print_help()
        return 0
    try:
        return func(args)
    except UsageError as exc:
        print(f"{PROG}: error: {exc}", file=sys.stderr)
        return 1
    except RefuseError as exc:
        print(f"{PROG}: refused: {exc}", file=sys.stderr)
        return 2
