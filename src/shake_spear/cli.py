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

from shake_spear import __version__, creators, scaffold, session
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
