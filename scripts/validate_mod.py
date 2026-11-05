"""Validate the intentionally content-free V3 framework and its package boundary."""

from __future__ import annotations

import argparse
import binascii
import json
from pathlib import Path
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD_FILES = {
    ".metadata/metadata.json",
    ".metadata/thumbnail.png",
    "thumbnail.png",
}


def check_png(path: Path) -> None:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Invalid PNG signature: {path.name}")
    offset, chunks, pixels = 8, [], bytearray()
    width = height = color = depth = 0
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 8 + size
        if end + 4 > len(data):
            raise ValueError("Truncated PNG data")
        body = data[offset + 8 : end]
        crc = struct.unpack_from(">I", data, end)[0]
        if binascii.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise ValueError(f"PNG checksum error in {kind!r}")
        chunks.append(kind)
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", body
            )
            if (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError("Preview must be a non-interlaced 8-bit RGB PNG")
        elif kind == b"IDAT":
            pixels.extend(body)
        offset = end + 4
        if kind == b"IEND":
            break
    if chunks[:1] != [b"IHDR"] or chunks[-1:] != [b"IEND"] or offset != len(data):
        raise ValueError("Invalid PNG structure")
    if (width, height) != (1024, 1024):
        raise ValueError("Project preview size must be 1024x1024")
    if len(zlib.decompress(pixels)) != height * (width * 3 + 1):
        raise ValueError("PNG pixel data has an invalid length")
    if len(data) >= 1_000_000:
        raise ValueError("Keep the upload preview smaller than 1 MB")


def validate(mod_dir: Path) -> dict:
    if not mod_dir.is_dir() or mod_dir.is_symlink():
        raise ValueError("Validate the real repository mod directory, not a link")
    paths = list(mod_dir.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Links must not be packaged: {path}")
        relative = path.relative_to(mod_dir).as_posix()
        if not relative.isascii():
            raise ValueError(f"Non-ASCII game path: {relative}")
    files = {p.relative_to(mod_dir).as_posix() for p in paths if p.is_file()}
    if files != SCAFFOLD_FILES:
        raise ValueError(
            "Empty-framework boundary violated. "
            f"Missing: {sorted(SCAFFOLD_FILES - files)}; "
            f"unexpected: {sorted(files - SCAFFOLD_FILES)}"
        )
    metadata = json.loads((mod_dir / ".metadata/metadata.json").read_text("utf-8"))
    required = {
        "name", "id", "version", "game_id", "picture", "supported_game_version",
        "short_description", "tags", "relationships", "game_custom_data",
    }
    if set(metadata) != required:
        raise ValueError("Missing or unexpected metadata fields")
    for key in ("name", "id", "version", "short_description"):
        if not isinstance(metadata[key], str) or not metadata[key].strip():
            raise ValueError(f"Metadata {key} must be a nonempty string")
    if metadata["game_id"] != "victoria3":
        raise ValueError("game_id must be victoria3")
    if metadata["id"] != "com.github.YangtzeMa.Vic-mod":
        raise ValueError("The project mod ID must remain stable")
    if not re.fullmatch(r"\d+\.\d+\.\d+", metadata["version"]):
        raise ValueError("Use a numeric major.minor.patch mod version")
    if metadata["supported_game_version"] != "1.15.*":
        raise ValueError("The verified target is Victoria 3 1.15.x")
    if metadata["picture"] != "thumbnail.png":
        raise ValueError("picture must reference the supplied thumbnail.png")
    if metadata["tags"] != ["Utilities"] or metadata["relationships"] != []:
        raise ValueError("The empty framework has one Utilities tag and no dependencies")
    if metadata["game_custom_data"] != {"multiplayer_synchronized": True}:
        raise ValueError("Unexpected game-specific metadata")
    check_png(mod_dir / "thumbnail.png")
    if (mod_dir / "thumbnail.png").read_bytes() != (
        mod_dir / ".metadata/thumbnail.png"
    ).read_bytes():
        raise ValueError("Launcher and Workshop previews must match")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mod-dir", type=Path, default=ROOT / "mod")
    args = parser.parse_args()
    try:
        metadata = validate(args.mod_dir)
    except (OSError, ValueError, KeyError, TypeError, struct.error, zlib.error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {metadata['name']} {metadata['version']} / V3 {metadata['supported_game_version']}")
    print("PASS: metadata, previews, ASCII paths, no gameplay scripts or vanilla overrides")
    print("Game loading and achievement eligibility require separate in-game evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
