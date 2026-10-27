#!/usr/bin/env python3
"""Create a versioned, installable 0 A.D. mod archive and SHA-256 checksum."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "tolkien"
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{7,40}$")


def read_version() -> str:
    try:
        with (MOD / "mod.json").open(encoding="utf-8-sig") as file:
            metadata = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to read tolkien/mod.json: {error}") from error

    version = metadata.get("version") if isinstance(metadata, dict) else None
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise ValueError("tolkien/mod.json must have a numeric major.minor.patch version")
    return version


def ignored_names(_: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in {"__pycache__", "troll_trial3", "warg.dae", ".DS_Store"}:
            ignored.add(name)
        elif name.endswith((".pyc", ".pyo", ".blend1", ".bak", ".tmp")):
            ignored.add(name)
    return ignored


def write_archive(source: Path, archive: Path) -> None:
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as output:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            name = Path("tolkien") / path.relative_to(source)
            info = zipfile.ZipInfo(name.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            output.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--tag", help="Release tag; must equal v<mod version>")
    parser.add_argument("--commit", help="Commit SHA to include in a push artifact name")
    args = parser.parse_args()
    if args.tag and args.commit:
        parser.error("--tag and --commit cannot be used together")
    if args.commit and not COMMIT_PATTERN.fullmatch(args.commit):
        parser.error("--commit must be a hexadecimal Git SHA (7-40 characters)")
    return args


def main() -> int:
    args = parse_args()
    try:
        version = read_version()
        if args.tag and args.tag != f"v{version}":
            raise ValueError(
                f"Tag {args.tag!r} does not match mod version v{version}"
            )
        if not (ROOT / "LICENSE").is_file():
            raise ValueError("Root LICENSE file is missing")

        args.output_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"-{args.commit[:12].lower()}" if args.commit else ""
        archive = args.output_dir / f"tolkien-{version}{suffix}.zip"

        with tempfile.TemporaryDirectory(prefix="tolkien-mod-") as temp_dir:
            stage = Path(temp_dir) / "tolkien"
            shutil.copytree(MOD, stage, ignore=ignored_names)
            license_destination = stage / "LICENSE"
            if license_destination.exists():
                raise ValueError("tolkien/LICENSE already exists; refusing to overwrite it")
            shutil.copy2(ROOT / "LICENSE", license_destination)
            write_archive(stage, archive)

        digest = sha256(archive)
        (args.output_dir / f"{archive.name}.sha256").write_text(
            f"{digest}  {archive.name}\n", encoding="ascii"
        )
        print(f"Created {archive}")
        print(f"SHA-256 {digest}")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Packaging failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
