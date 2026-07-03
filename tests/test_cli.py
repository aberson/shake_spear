"""Tests for the ``ss`` CLI entry points (plan.md section 11 Step 1)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from shake_spear import __version__
from shake_spear.cli import build_parser, main


def _console_script() -> Path:
    """Path of the installed ``ss`` console script next to the interpreter."""
    name = "ss.exe" if os.name == "nt" else "ss"
    return Path(sys.executable).parent / name


def test_main_version_direct_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_main_help_direct_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    assert "usage: ss" in capsys.readouterr().out


def test_main_bare_prints_help_and_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: ss" in capsys.readouterr().out


def test_build_parser_prog_is_ss() -> None:
    assert build_parser().prog == "ss"


def test_unknown_command_prints_help_and_exits_1(capsys: pytest.CaptureFixture[str]) -> None:
    """Plan §4: usage errors exit 1 (argparse's default of 2 is reserved for refusals)."""
    with pytest.raises(SystemExit) as excinfo:
        main(["bogus-command"])
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "usage: ss" in err
    assert "bogus-command" in err


def test_module_form_version_subprocess() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "shake_spear", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_console_script_version_subprocess() -> None:
    ss = _console_script()
    if not ss.exists():
        pytest.skip("ss console script not installed next to this interpreter")
    result = subprocess.run(
        [str(ss), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_version_single_source_of_truth() -> None:
    """pyproject.toml must not carry its own version literal (hatch reads __init__)."""
    import tomllib

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    assert data["tool"]["hatch"]["version"]["path"] == "src/shake_spear/__init__.py"
