import os
import subprocess


quickbms_folder = os.path.join("_tools_", "quickbms")
script_folder = os.path.join("_script_")


def repack_assets_font() -> bool:
    """
    Repack font assets into the assets.pak file using quickbms_4gb version.

    expected quickbms command:
    _tools_/quickbms_4gb_files.exe -w -r -r _script_/script-v2.bms ./assets.pak ./workspace/modded-assets
    """
    bms_4gb_exe = os.path.join(quickbms_folder, "quickbms_4gb_files.exe")
    script_bms = os.path.join(script_folder, "script-v2.bms")
    assets_pak = "./assets.pak"
    modded_assets_dir = "./workspace/modded-assets"

    # sanity checks
    if not os.path.exists(bms_4gb_exe):
        print(f"缺少 quickbms_4gb 執行檔: {bms_4gb_exe}")
        return False
    if not os.path.exists(script_bms):
        print(f"缺少腳本檔案: {script_bms}")
        return False

    cmd = [bms_4gb_exe, "-w", "-r", "-r", script_bms, assets_pak, modded_assets_dir]
    print("執行指令:", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # print(proc.stdout)
    # print(proc.stderr)

    if proc.returncode != 0:
        print(f"quickbms_4gb 返回非零退出代碼: {proc.returncode}")
        return False

    if not os.path.exists(assets_pak):
        print(f"未生成預期的資源包: {assets_pak}")
        return False

    print(f"已將資源重打包至 {assets_pak}")
    return True