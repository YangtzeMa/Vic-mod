"""Link this mod into the real Windows Documents directory without overwriting data."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if os.name != "nt":
        raise SystemExit("This local setup helper is for Windows directory junctions.")
    target = (ROOT / "mod").resolve(strict=True)
    if not (target / ".metadata/metadata.json").is_file():
        raise SystemExit("The repository mod metadata is missing.")
    buffer = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer)
    if result != 0 or not buffer.value:
        raise SystemExit("Windows did not return the real Documents directory.")
    parent = Path(buffer.value) / "Paradox Interactive/Victoria 3/mod"
    parent.mkdir(parents=True, exist_ok=True)
    link = parent / "vic-mod-dev"
    if os.path.lexists(link):
        if link.is_junction() and link.resolve(strict=True) == target:
            print(f"Already linked: {link} -> {target}")
            return
        raise SystemExit(f"Destination exists and is not this project's junction: {link}")
    subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)], check=True)
    if not link.is_junction() or link.resolve(strict=True) != target:
        raise SystemExit("The created junction does not point to this mod.")
    print(f"Linked: {link} -> {target}")
    print("Add Vic Mod Template to a dedicated playset in the Paradox Launcher.")


if __name__ == "__main__":
    main()
