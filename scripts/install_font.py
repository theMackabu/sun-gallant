#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_NAME = "SunGallant-Regular.ttf"


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

    destination = font_directory() / FONT_NAME
    if args.remove:
        if destination.exists():
            destination.unlink()
            refresh_cache()
            print(f"Removed {destination}")
        else:
            print(f"Not installed: {destination}")
        return

    source = ROOT / "dist" / FONT_NAME
    if not source.exists():
        raise SystemExit(f"{source} does not exist; run make build first")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    refresh_cache()
    print(f"Installed {destination}")


if __name__ == "__main__":
    main()
