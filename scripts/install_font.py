#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_NAMES = ("SunGallant-Regular.ttf", "sunGallantVector.ttf")


def font_directory() -> Path:
    override = os.environ.get("SUN_GALLANT_FONT_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Fonts"
    if system == "Windows":
        raise SystemExit("on Windows, install the TTF files in dist/ from Explorer")

    data_home = os.environ.get("XDG_DATA_HOME")
    return Path(data_home) / "fonts" if data_home else Path.home() / ".local" / "share" / "fonts"


def refresh_cache() -> None:
    if platform.system() == "Linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove", action="store_true", help="uninstall instead of install")
    args = parser.parse_args()

    destinations = [font_directory() / name for name in FONT_NAMES]
    if args.remove:
        removed = []
        for destination in destinations:
            if destination.exists():
                destination.unlink()
                removed.append(destination)
                print(f"Removed {destination}")
            else:
                print(f"Not installed: {destination}")
        if removed:
            refresh_cache()
        return

    sources = [ROOT / "dist" / name for name in FONT_NAMES]
    missing = [source for source in sources if not source.exists()]
    if missing:
        raise SystemExit(f"{missing[0]} does not exist; run make build first")
    destinations[0].parent.mkdir(parents=True, exist_ok=True)
    for source, destination in zip(sources, destinations, strict=True):
        shutil.copy2(source, destination)
        print(f"Installed {destination}")
    refresh_cache()


if __name__ == "__main__":
    main()
