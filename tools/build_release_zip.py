from __future__ import annotations

import argparse
import hashlib
import os
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "nano_banana_render"
DEFAULT_OUTPUT = PROJECT_ROOT / "dist" / "Nanode_AI_Render_Engine.zip"
EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def iter_package_files() -> list[Path]:
    files = [
        path
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file()
        and not EXCLUDED_PARTS.intersection(path.parts)
        and path.suffix.lower() not in EXCLUDED_SUFFIXES
    ]
    return sorted(files, key=lambda path: path.as_posix())


def build_archive(output: Path) -> tuple[int, str]:
    if not (PACKAGE_ROOT / "__init__.py").is_file():
        raise FileNotFoundError(f"Invalid add-on package: {PACKAGE_ROOT}")

    files = iter_package_files()
    if not files:
        raise RuntimeError("No add-on files found")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_suffix(f"{output.suffix}.tmp")

    try:
        with zipfile.ZipFile(
            temporary_output,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for source in files:
                relative_path = source.relative_to(PROJECT_ROOT).as_posix()
                info = zipfile.ZipInfo(relative_path, date_time=ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o644 & 0xFFFF) << 16
                archive.writestr(info, source.read_bytes(), compresslevel=9)
        os.replace(temporary_output, output)
    finally:
        temporary_output.unlink(missing_ok=True)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return len(files), digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a clean Nanode Blender add-on ZIP")
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output archive path (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    file_count, digest = build_archive(args.output)
    output = args.output.resolve()
    print(f"Built {output}")
    print(f"Files: {file_count}")
    print(f"Size: {output.stat().st_size} bytes")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
