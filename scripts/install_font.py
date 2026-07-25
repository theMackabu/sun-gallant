#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_NAMES = ("SunGallant-Regular.ttf", "SunGallantClassic-Regular.ttf")


def font_directory() -> Path:
    override = os.environ.get("SUN_GALLANT_FONT_DIR")
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Fonts"
    if system == "Windows":
        raise SystemExit("on Windows, install dist/SunGallant-Regular.ttf from Explorer")

    data_home = os.environ.get("XDG_DATA_HOME")
    return Path(data_home) / "fonts" if data_home else Path.home() / ".local" / "share" / "fonts"


def refresh_cache() -> None:
    if platform.system() == "Linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remove", action="store_true", help="uninstall instead of install")
    args = parser.parse_args()

    if args.remove:
        removed = False
        for font_name in FONT_NAMES:
            destination = font_directory() / font_name
            if destination.exists():
                destination.unlink()
                removed = True
                print(f"Removed {destination}")
            else:
                print(f"Not installed: {destination}")
        if removed:
            refresh_cache()
        return

    sources = [ROOT / "dist" / font_name for font_name in FONT_NAMES]
    missing = [source for source in sources if not source.exists()]
    if missing:
        raise SystemExit(f"{missing[0]} does not exist; run make build first")

    destination_directory = font_directory()
    destination_directory.mkdir(parents=True, exist_ok=True)
    for source in sources:
        destination = destination_directory / source.name
        shutil.copy2(source, destination)
        print(f"Installed {destination}")
    refresh_cache()


if __name__ == "__main__":
    main()
