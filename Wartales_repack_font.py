"""CLI orchestrator for the Wartales font repack workflow.

This script implements the high-level steps described in README.md:

- verify required tools exist
- extract localization files using QuickBMS
- copy extracted xml files into a flat folder for txt2fnt
- invoke txt2fnt for each TTF in `_tools_/ttf`

It purposefully keeps behaviour simple and transparent so it can be
used interactively or from CI.
"""

import argparse
import shutil
import subprocess
import sys
import os
import glob
from typing import List

from source.util.res_i18n_extractor import extract_i18n


# Use only relative paths (relative to current working directory)
TOOLS = os.path.join("_tools_")
WORKSPACE = os.path.join("workspace")
EXTRACTED_RES = os.path.join(WORKSPACE, "extracted-res")
extracted_txt_folder = os.path.join(WORKSPACE, "extracted-txt")
# txt2fnt writes font output files under workspace/modded-assets/ui/fonts per README
MODDED_ASSETS = os.path.join(WORKSPACE, "modded-assets", "ui", "fonts")


def check_file(path: str) -> bool:
    if not os.path.exists(path):
        print(f"Missing: {path}")
        return False
    return True


def find_ttfs(folder: str) -> List[str]:
    if not os.path.exists(folder):
        return []
    return sorted(glob.glob(os.path.join(folder, "*.ttf")))


def run_txt2fnt(
    ttf: str, fs: int = 48
) -> int:
    os.makedirs(MODDED_ASSETS, exist_ok=True)
    txt2fnt_exe = os.path.join(TOOLS, "txt2fnt", "txt2fnt.exe")

    cmd = [
        str(txt2fnt_exe),
        "-tf",
        extracted_txt_folder,
        "-fs",
        str(fs),
        "-ttf",
        ttf,
        "-o",
        "noto_sans_cjk_regular",
        "-ff",
        str(MODDED_ASSETS),
        # "--treat-xml-as-text"
    ]
    print("Running:", " ".join(cmd))
    # txt2fnt expects to be run from the folder containing the ttf (it loads by name)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    print(proc.stderr)
    return proc.returncode


def verify_txt2fnt_outputs() -> bool:
    """Verify that txt2fnt produced the expected .fnt and .png files."""
    fnt = os.path.join(MODDED_ASSETS, "noto_sans_cjk_regular.fnt")
    png = os.path.join(MODDED_ASSETS, "noto_sans_cjk_regular.png")
    ok = True
    if not os.path.exists(fnt):
        print(f"Missing expected output file: {fnt}")
        ok = False
    if not os.path.exists(png):
        print(f"Missing expected output file: {png}")
        ok = False
    return ok


def copy_extracted_to_flat(extracted_res: str, dest: str, language: str) -> None:
    os.makedirs(dest, exist_ok=True)
    # expected files according to README
    candidates = [
        os.path.join(extracted_res, "lang", f"texts_{language}.xml"),
        os.path.join(extracted_res, "lang", f"export_{language}.xml"),
    ]
    for p in candidates:
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dest, os.path.basename(p)))
            print(f"Copied {p} -> {os.path.join(dest, os.path.basename(p))}")
        else:
            print(f"Warning: expected extracted file not found: {p}")


def check_prereqs(
    require_quickbms: bool = True, require_font_tools: bool = True
) -> bool:
    ok = True
    if require_quickbms:
        ok = check_file(os.path.join(TOOLS, "quickbms", "quickbms.exe")) and ok
    if require_font_tools:
        ok = check_file(os.path.join(TOOLS, "fontgen", "fontgen.exe")) and ok
        ok = check_file(os.path.join(TOOLS, "txt2fnt", "txt2fnt.exe")) and ok
        ttfs = find_ttfs(os.path.join(TOOLS, "ttf"))
        if not ttfs:
            print(f"No TTFs found in {os.path.join(TOOLS, 'ttf')}")
            ok = False
    return ok


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Wartales repack font helper")
    parser.add_argument(
        "-lang",
        "--language",
        dest="language",
        default="zh",
        help="language token to extract (eg: zh)",
    )
    parser.add_argument(
        "--res-pak", default="res.pak", help="path to res.pak archive"
    )
    parser.add_argument(
        "-fs",
        "--font-size",
        default=48,
        type=int,
        help="font size to pass to txt2fnt (-fs)",
    )

    # ttf
    parser.add_argument(
        "--ttf",
        dest="ttf",
        default="ChironHeiHK-Text-R-400",
        help="specific TTF file to process (default: ChironHeiHK-Text-R-400.ttf)",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="only extract localization files and exit",
    )

    args = parser.parse_args(argv)

    # Step 1: check quickbms
    if not check_prereqs(require_quickbms=True, require_font_tools=False):
        print("Missing QuickBMS tool: please place _tools_/quickbms/quickbms.exe")
        return 2

    res_pak = args.res_pak
    if not os.path.exists(res_pak):
        print(f"res.pak not found: {res_pak}")
        return 3

    print("Extracting localization files...")
    ok = extract_i18n(
        language=args.language, res_pak=str(res_pak), list_only=False, verbose=True
    )
    if not ok:
        print("Extraction failed")
        return 4

    # Step 3: copy into flat folder
    print("Copying extracted xml to flat folder for txt2fnt input...")
    copy_extracted_to_flat(EXTRACTED_RES, extracted_txt_folder, args.language)

    if args.extract_only:
        print("Extraction complete. Stopping as requested.")
        return 0

    # Step 4: check font tools and available TTFs
    if not check_prereqs(require_quickbms=False, require_font_tools=True):
        print(
            "Missing font tools. Please ensure _tools_/fontgen, _tools_/txt2fnt and _tools_/ttf exist"
        )
        return 5

    ttfs = find_ttfs(os.path.join(TOOLS, "ttf"))
    if not ttfs:
        print("No TTF files to process")
        return 6

    # Step 5: run txt2fnt
    any_failures = False
    rc = run_txt2fnt(
        ttf=args.ttf,
        fs=args.font_size,
    )

    if rc != 0:
        print(f"txt2fnt failed with exit code: {rc}")
        any_failures = True
    else:
        if not verify_txt2fnt_outputs():
            any_failures = True

    if any_failures:
        print(".fnt failed to generate correctly")
        return 7

    # Step 6: repack modified font assets into assets.pak
    try:
        from source.util.assets_font_repacker import repack_assets_font
    except Exception as e:
        print(f"Failed to import assets repacker: {e}")
        return 8

    print("Repacking modified assets into assets.pak...")
    if not repack_assets_font():
        print("Repack failed")
        return 8

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
