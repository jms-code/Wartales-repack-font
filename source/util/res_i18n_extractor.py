import os
import shutil
import subprocess
from typing import List

quickbms_folder = os.path.join("_tools_", "quickbms")
script_folder = os.path.join("_script_")

def _lang_to_filters(language: str) -> List[str]:
    """Generate filter patterns for a given language code."""
    return [
        f"lang/texts_{language}.xml",
        f"lang/export_{language}.xml",
    ]


def extract_i18n(
    language: str,
    res_pak: str,
    list_only: bool = False,
    verbose: bool = False,
) -> bool:
    """Extract or list localization files for a given language from res_pak.
    - `language` (e.g., 'zh').
    - `res_pak` path to the res.pak file.
    - `list_only` when True will only list matching files.
    The output directory is always `workspace/extracted-res/`.
    Returns a dict like {returncode, stdout, stderr, listed, extracted}.
    """
    # Validate language token (simple safety check)
    import re

    if not isinstance(language, str) or not re.match(r"^[A-Za-z0-9_-]+$", language):
        raise ValueError(f"Invalid language code: {language!r}")

    # Generate filters from patterns
    filters: List[str] = _lang_to_filters(language)

    bms_exe = os.path.join(quickbms_folder, "quickbms.exe")
    script_bms = os.path.join(script_folder, "script-v1.bms")
    # input_archive = os.path.join(input_archive)
    # output_dir is fixed
    output_dir = os.path.join("workspace", "extracted-res")

    # clear output dir
    if not list_only:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

    # Prepare filter string for quickbms (-f expects comma/semicolons and {} wildcard style)
    filt = ",".join(f"{{}}{p}" for p in filters)

    if list_only:
        args = ["-l", "-f", filt, script_bms, res_pak]
    else:
        args = ["-f", filt, script_bms, res_pak, output_dir]

    # logging the command and args
    print(f"執行 quickbms: {bms_exe} {' '.join(args)}")

    result = subprocess.run([bms_exe] + args, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)


    if not list_only:
        return True

    extracted: List[str] = []
    for p in filters:
        candidate = os.path.join(output_dir, p)
        if os.path.exists(candidate):
            extracted.append(candidate)

    isAllExtracted = len(extracted) == len(filters)

    if isAllExtracted:
        print("提取成功")
    else:
        print("提取失敗")
    return isAllExtracted
