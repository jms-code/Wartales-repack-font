import os
import shutil
import subprocess
import sys

quickbms_folder = os.path.join("_tools_", "quickbms")
script_folder = os.path.join("_script_")

def inject_i18n(
    res_pak: str,
    xml_source_dir: str,
    language: str = "zh"
) -> bool:
    """
    Inject i18n XML files from xml_source_dir into res_pak.
    
    The xml_source_dir is expected to contain:
      - texts_{language}.xml
      - export_{language}.xml
      
    These will be staged into workspace/inject-res/lang/ and then reimported
    using QuickBMS reimport mode (-w -r -r).
    """
    
    # 1. Verify inputs
    if not os.path.exists(res_pak):
        print(f"Error: res.pak not found at {res_pak}")
        return False
        
    if not os.path.exists(xml_source_dir):
        print(f"Error: XML source directory not found at {xml_source_dir}")
        return False

    bms_exe = os.path.join(quickbms_folder, "quickbms.exe")
    script_bms = os.path.join(script_folder, "script-v1.bms")
    
    if not os.path.exists(bms_exe):
        print(f"Error: QuickBMS executable not found at {bms_exe}")
        return False
        
    if not os.path.exists(script_bms):
        print(f"Error: BMS script not found at {script_bms}")
        return False

    # 2. Prepare staging area
    staging_dir = os.path.join("workspace", "inject-res")
    staging_lang_dir = os.path.join(staging_dir, "lang")
    
    # Clean staging area
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_lang_dir, exist_ok=True)
    
    # 3. Copy files to staging area with correct structure
    files_to_inject = [
        f"texts_{language}.xml",
        f"export_{language}.xml"
    ]
    
    found_any = False
    for fname in files_to_inject:
        src_path = os.path.join(xml_source_dir, fname)
        if os.path.exists(src_path):
            dst_path = os.path.join(staging_lang_dir, fname)
            shutil.copy2(src_path, dst_path)
            print(f"Staged for injection: {fname}")
            found_any = True
        else:
            print(f"Warning: {fname} not found in {xml_source_dir}")
            
    if not found_any:
        print("Error: No matching XML files found to inject.")
        return False

    # 4. Run QuickBMS reimport
    # Command: quickbms -w -r -r script.bms archive.pak input_folder
    cmd = [
        bms_exe,
        "-w", "-r", "-r",
        script_bms,
        res_pak,
        staging_dir
    ]
    
    print(f"Running reimport: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        # print(proc.stdout) # Verbose output might be too much, but useful for debug
        if proc.returncode != 0:
            print("QuickBMS reimport failed.")
            print(proc.stdout)
            print(proc.stderr)
            return False
            
        print("Injection successful.")
        return True
        
    except Exception as e:
        print(f"Exception during reimport: {e}")
        return False
