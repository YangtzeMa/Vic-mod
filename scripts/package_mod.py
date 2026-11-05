"""Build a deterministic ZIP whose root is the actual Victoria 3 mod root."""

from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from validate_mod import ROOT, SCAFFOLD_FILES, validate


def main() -> None:
    mod_dir = ROOT / "mod"
    metadata = validate(mod_dir)
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / f"vic-mod-{metadata['version']}.zip"
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(SCAFFOLD_FILES):
            entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (mod_dir / name).read_bytes())
    with ZipFile(output) as archive:
        if set(archive.namelist()) != SCAFFOLD_FILES or archive.testzip() is not None:
            raise ValueError("Package verification failed")
        for name in SCAFFOLD_FILES:
            if archive.read(name) != (mod_dir / name).read_bytes():
                raise ValueError(f"Packaged bytes differ: {name}")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(f"PASS: {output.name}, {output.stat().st_size} bytes, {len(SCAFFOLD_FILES)} files")
    print(f"SHA256: {digest}")


if __name__ == "__main__":
    main()
