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
import glob
import os
import shutil
import subprocess
import sys
from typing import List

from source.util.res_i18n_extractor import extract_i18n
from source.util.res_i18n_injector import inject_i18n

# Use only relative paths (relative to current working directory)
TOOLS = os.path.join("_tools_")
WORKSPACE = os.path.join("workspace")
EXTRACTED_RES = os.path.join(WORKSPACE, "extracted-res")
extracted_txt_folder = os.path.join(WORKSPACE, "extracted-txt")
# txt2fnt writes font output files under workspace/modded-assets/ui/fonts per README
MODDED_ASSETS = os.path.join(WORKSPACE, "modded-assets", "ui", "fonts")


def check_file(path: str) -> bool:
    if not os.path.exists(path):
        print(f"缺少檔案: {path}")
        return False
    return True


def find_ttfs(folder: str) -> List[str]:
    if not os.path.exists(folder):
        return []
    return sorted(glob.glob(os.path.join(folder, "*.ttf")))


def run_txt2fnt(ttf: str, fs: int = 48) -> int:
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
    print("執行指令:", " ".join(cmd))
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
        print(f"缺少預期輸出檔案: {fnt}")
        ok = False
    if not os.path.exists(png):
        print(f"缺少預期輸出檔案: {png}")
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
            print(f"已複製 {p} -> {os.path.join(dest, os.path.basename(p))}")
        else:
            print(f"警告: 未找到預期的提取檔案: {p}")


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
            print(f"在 {os.path.join(TOOLS, 'ttf')} 中未找到 TTF 檔案")
            ok = False
    return ok


def main(argv: List[str]) -> int:
    # Force UTF-8 output for Windows consoles to avoid UnicodeEncodeError with Chinese characters
    if sys.stdout and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Wartales repack font helper")
    parser.add_argument(
        "-lang",
        "--language",
        dest="language",
        default="zh",
        help="language token to extract (eg: zh)",
    )
    parser.add_argument("--res-pak", default="res.pak", help="path to res.pak archive")
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
    parser.add_argument(
        "--inject-xml",
        dest="inject_xml_dir",
        help="directory containing XML files to inject into res.pak (skips other steps)",
    )
    parser.add_argument(
        "--continue-after-inject",
        action="store_true",
        help="continue with full repack flow after injection",
    )

    args = parser.parse_args(argv)

    # Handle injection mode
    if args.inject_xml_dir:
        print(f"正在將 XML 從 {args.inject_xml_dir} 注入到 {args.res_pak}...")
        if not check_prereqs(require_quickbms=True, require_font_tools=False):
            print("缺少 QuickBMS 工具")
            return 2

        if inject_i18n(args.res_pak, args.inject_xml_dir, args.language):
            print("注入完成。")
            if not args.continue_after_inject:
                return 0
        else:
            print("注入失敗。")
            return 1

    # Step 1: check quickbms
    if not check_prereqs(require_quickbms=True, require_font_tools=False):
        print("缺少 QuickBMS 工具：請放置 _tools_/quickbms/quickbms.exe")
        return 2

    res_pak = args.res_pak
    if not os.path.exists(res_pak):
        print(f"未找到 res.pak: {res_pak}")
        return 3

    print("正在提取本地化檔案...")
    ok = extract_i18n(
        language=args.language, res_pak=str(res_pak), list_only=False, verbose=True
    )
    if not ok:
        print("提取失敗")
        return 4

    # Step 3: copy into flat folder
    print("正在將提取的 xml 複製到 txt2fnt 輸入資料夾...")
    copy_extracted_to_flat(EXTRACTED_RES, extracted_txt_folder, args.language)

    if args.extract_only:
        print("提取完成。依請求停止。")
        return 0

    # Step 4: check font tools and available TTFs
    if not check_prereqs(require_quickbms=False, require_font_tools=True):
        print(
            "缺少字體工具。請確保 _tools_/fontgen, _tools_/txt2fnt 和 _tools_/ttf 存在"
        )
        return 5

    ttfs = find_ttfs(os.path.join(TOOLS, "ttf"))
    if not ttfs:
        print("沒有可處理的 TTF 檔案")
        return 6

    # Step 5: run txt2fnt
    any_failures = False
    rc = run_txt2fnt(
        ttf=args.ttf,
        fs=args.font_size,
    )

    if rc != 0:
        print(f"txt2fnt 執行失敗，退出代碼: {rc}")
        any_failures = True
    else:
        if not verify_txt2fnt_outputs():
            any_failures = True

    if any_failures:
        print(".fnt 生成失敗")
        return 7

    # Step 6: repack modified font assets into assets.pak
    try:
        from source.util.assets_font_repacker import repack_assets_font
    except Exception as e:
        print(f"無法導入 assets repacker: {e}")
        return 8

    print("正在將修改後的資源重打包進 assets.pak...")
    if not repack_assets_font():
        print("重打包失敗")
        return 8

    print("完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
