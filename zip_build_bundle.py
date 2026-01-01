"""zip_build_bundle.py

Zip the contents of the `dist/` folder into a single zip file stored in
`build/`.

Behavior:
- By default uses the Unicode filename: ``Wartales 戰爭傳說 重注中文字體包.zip``
  and stores it under the `build/` directory.
- If writing the Unicode filename fails (some platforms/encodings), the
  script will fall back to an ASCII-safe name: ``Wartales_repack_zh.zip``.

Usage:
  python zip_build_bundle.py [--dist DIST] [--build BUILD] [--zip-name ZIPNAME]
                            [--timestamp] [--dry-run] [--verbose]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
import shutil
from pathlib import Path
from typing import Optional

DEFAULT_ZIP_NAME = "Wartales 戰爭傳說 重注中文字體包.zip"
FALLBACK_ZIP_NAME = "Wartales_repack_zh.zip"


def zip_dir(dist: Path, zip_file: Path, verbose: bool = False) -> None:
    """Create a zip at ``zip_file`` containing everything under ``dist``.

    Files keep their path relative to ``dist`` (no leading directory).
    """
    if not dist.exists():
        raise FileNotFoundError(f"Dist directory not found: {dist}")
    # Ensure parent directory exists
    zip_file.parent.mkdir(parents=True, exist_ok=True)

    compression = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(zip_file, mode="w", compression=compression) as zf:
        for p in sorted(dist.rglob("*")):
            if p.is_dir():
                continue
            arcname = p.relative_to(dist).as_posix()
            if verbose:
                print(f"Adding: {p} -> {arcname}")
            zf.write(p, arcname)


def parse_args(argv: Optional[list[str]] = None):
    p = argparse.ArgumentParser(description="Zip the dist/ folder into build/.")
    p.add_argument("--dist", default="dist", help="dist folder to zip")
    p.add_argument("--build", default="build", help="output build folder")
    p.add_argument("--zip-name", default=None, help="Explicit zip filename to use")
    p.add_argument(
        "--timestamp", action="store_true", help="append timestamp to zip name"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="don't actually write the zip, just print what would happen",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="verbose output")
    return p.parse_args(argv)


def make_zip_name(base_name: str, timestamp: bool) -> str:
    if not timestamp:
        return base_name
    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem, ext = (base_name, "") if "." not in base_name else base_name.rsplit(".", 1)
    return f"{stem}-{ts}.{ext}" if ext else f"{stem}-{ts}"


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    dist = Path(args.dist)
    build = Path(args.build)
    build.mkdir(parents=True, exist_ok=True)

    # Ensure dist exists so we can copy the GUI README into it
    dist.mkdir(parents=True, exist_ok=True)

    # Copy README_GUI.md to dist as '使用說明.md' (skip actual copy in dry-run)
    readme_src = Path("README_GUI.md")
    readme_dst = dist / "使用說明.md"
    if readme_src.exists():
        if args.dry_run:
            if args.verbose:
                print(f"Would copy {readme_src} -> {readme_dst}")
        else:
            try:
                shutil.copy2(readme_src, readme_dst)
                if args.verbose:
                    print(f"Copied: {readme_src} -> {readme_dst}")
            except Exception as e:
                print(f"Warning: failed to copy {readme_src} to {readme_dst}: {e}")
    else:
        if args.verbose:
            print("README_GUI.md not found; skipping copy of 使用說明.md")

    requested = args.zip_name or DEFAULT_ZIP_NAME
    requested = make_zip_name(requested, args.timestamp)

    zip_path = build / requested

    if args.dry_run or args.verbose:
        print(f"dist: {dist}")
        print(f"build: {build}")
        print(f"zip: {zip_path}")

    if args.dry_run:
        return 0

    try:
        zip_dir(dist, zip_path, verbose=args.verbose)
    except FileNotFoundError as e:
        print(e)
        return 1
    except (UnicodeEncodeError, OSError) as first_exc:
        # Try fallback name if we were using the default unicode name
        if (requested == DEFAULT_ZIP_NAME) and (requested != FALLBACK_ZIP_NAME):
            fallback = make_zip_name(FALLBACK_ZIP_NAME, args.timestamp)
            fallback_path = build / fallback
            print(
                f"Failed to write unicode zip name ({first_exc}). Trying fallback: {fallback}"
            )
            try:
                zip_dir(dist, fallback_path, verbose=args.verbose)
                print(f"Packaged build into: {fallback_path}")
                return 0
            except Exception as second_exc:  # pylint: disable=broad-except
                print(f"Fallback attempt also failed: {second_exc}")
                return 2
        print(f"Failed to create zip: {first_exc}")
        return 3

    print(f"Packaged build into: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
