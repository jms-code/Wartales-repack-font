# Wartales-repack-font

A tool to repack fonts for the game Wartales.
It is assumed that you have already updated the localization files.


## manually download dependencies before running

### folder: `_tools_`

1. `fontgen\fontgen.exe` and its dependencies
   - [Fontgen V1.1.0](https://github.com/Yanrishatum/fontgen/releases/tag/1.1.0)
   - expected SHA256: `8E68482A506320B1AD509FD5E5AB885C571FD6845B60E593E2B923CD48F23D0D`

2. `txt2fnt\txt2fnt.exe` and its dependencies
   - [txt2fnt](https://github.com/code-jammed/txt2fnt)

3. `quickbms\quickbms.exe` & `quickbms\quickbms_4gb_files.exe` and their dependencies
   - [QuickBMS](https://aluigi.altervista.org/quickbms.htm)

4. Place your desired TTF font files in the `_tools_/ttf` folder.




# Wartales_repack_font

### `Wartales_repack_font.py` supports three main modes:

#### 1. Full Repack (Default)
`py Wartales_repack_font.py --res-pak res.pak -lang zh`

This runs the complete workflow:
1. **Extract**: Extracts localization files (`texts_zh.xml`, `export_zh.xml`) from `res.pak`.
2. **Generate**: Converts extracted XML + TTF into bitmap fonts (`.fnt`, `.png`) using `txt2fnt`.
3. **Repack**: Packs the generated fonts into `assets.pak`.

#### 2. Extract Only
`py Wartales_repack_font.py --res-pak res.pak -lang zh --extract-only`

- Performs only the extraction step.
- Useful if you want to inspect the XML files or manually edit them before generating fonts.
- Output files are in `workspace/extracted-txt/`.

#### 3. Inject XML (Translation Update)
`py Wartales_repack_font.py --res-pak res.pak -lang zh --inject-xml _new_xml_`

- Injects modified XML files from a folder (e.g., `_new_xml_`) back into `res.pak`.
- **Does not** touch fonts or `assets.pak`.
- Useful for testing translation changes without regenerating fonts.
- The source folder must contain `texts_{lang}.xml` and `export_{lang}.xml`.

---

### Detailed Steps (Full Repack)

1. check if working directories contain necessary files for next step:
   - `_tools_/quickbms/quickbms.exe`
2. empty the folder `workspace/extracted-res/` and
   use `quickbms.exe` to
   extract i18n files from Wartales res.pak into `workspace/extracted-res/`
   - e.g. expected files (under the folder):
      1. `lang/texts_zh.xml`
      2. `lang/export_zh.xml`
3. empty the folder `workspace/extracted-txt/` and
   copy all extracted files into `workspace/extracted-txt/` (no subdirs)
   - e.g. expected files (under the folder):
      1. `texts_zh.xml`
      2. `export_zh.xml`
4. check if working directories contain necessary files for next step:
   - `_tools_/fontgen/fontgen.exe`
   - `_tools_/txt2fnt/txt2fnt.exe`
   - `_tools_/ttf/**.ttf`
5. use `txt2fnt.exe` to convert the xml files into fnt files
   - e.g. expected command:

      `txt2fnt.exe -tf workspace/extracted-txt -fs 48 -ttf ChironHeiHK-Text-R-400 -o noto_sans_cjk_regular -ff workspace/modded-assets/ui/fonts`
   and check expected output files exist:
      1. `workspace/modded-assets/ui/fonts/noto_sans_cjk_regular.fnt`
      2. `workspace/modded-assets/ui/fonts/noto_sans_cjk_regular.png`
6. use `quickbms_4gb_files.exe` to repack the modified font files into `assets.pak`
   - e.g. expected command:

      `_tools_/quickbms_4gb_files.exe -w -r -r _script_/script-v2.bms ./assets.pak ./workspace/modded-assets`




### testing example

```bash
py -m source.example.test_extract
```


# Build executables
```bash
./build_exe.ps1
```

## build GUI only
```bash
pyinstaller --onefile --windowed Wartales_repack_font_gui.py
```


## run the GUI for debugging
```bash
py -m Wartales_repack_font_gui --debug
```
