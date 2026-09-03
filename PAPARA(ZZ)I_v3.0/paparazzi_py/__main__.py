"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .ui import launch


def main() -> None:
    parser = argparse.ArgumentParser(description="PAPARA(ZZ)I Python")
    parser.add_argument("image_dir", nargs="?", type=Path, help="Optionaler Bilderordner")
    parser.add_argument("--user", help="Optionaler Benutzername")
    arguments = parser.parse_args()
    launch(arguments.image_dir, arguments.user)


if __name__ == "__main__":
    main()

