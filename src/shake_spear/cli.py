"""Command-line interface for shake_spear (the ``ss`` entry point).

No subcommands yet — they land in later build steps. The parser is built in
:func:`build_parser` so subparsers can be registered there without touching
:func:`main`.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from shake_spear import __version__

PROG = "ss"


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level ``ss`` argument parser.

    Later steps add subcommands here via ``parser.add_subparsers()``.
    """
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="shake_spear: markdown-first creative writing workshop CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Accepts an explicit ``argv`` for testability; ``None`` means
    ``sys.argv[1:]``. Returns the process exit code (``--version`` and
    ``--help`` exit via :class:`SystemExit` raised by argparse).
    """
    parser = build_parser()
    parser.parse_args(argv)
    # No subcommands yet: bare `ss` prints help and succeeds.
    parser.print_help()
    return 0
