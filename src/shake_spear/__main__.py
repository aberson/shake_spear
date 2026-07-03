"""Make ``python -m shake_spear`` behave identically to the ``ss`` script."""

from shake_spear.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
