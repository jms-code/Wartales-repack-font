# Copilot / Agent instructions for Wartales-repack-font

Summary
- Purpose: small CLI tool to extract localization files from Wartales `res.pak`, convert them to bitmap fonts, and repack into `assets.pak`.
- Platform: Windows-first (expects `*.exe` tools in `_tools_`).
- Run from repo root; all paths in the code are relative to the current working directory.

Quick facts (what an agent needs to know)
- Key scripts:
  - `Wartales_repack_font.py` — orchestration CLI (main entrypoint).
  - `source/util/res_i18n_extractor.py` — uses QuickBMS to extract `lang/texts_{lang}.xml` and `lang/export_{lang}.xml` into `workspace/extracted-res/`.
  - `source/util/res_i18n_injector.py` — uses QuickBMS (reimport mode) to inject XML files from a source folder back into `res.pak`.
  - `source/util/assets_font_repacker.py` — repacks modified fonts into `assets.pak` using `quickbms_4gb_files.exe` and `script-v2.bms`.
- Tooling expectations (manual setup required in `_tools_`):
  - `_tools_/quickbms/quickbms.exe` and `_tools_/quickbms/quickbms_4gb_files.exe` (used by extractor & repacker).
  - `_tools_/txt2fnt/txt2fnt.exe` (produces `.fnt` + `.png` files).
  - `_tools_/fontgen/fontgen.exe` (optional/used by some workflows).
  - Place font files under `_tools_/ttf/` (agents must not assume system fonts).
- QuickBMS scripts used: `_script_/script-v1.bms` (extract/inject) and `_script_/script-v2.bms` (repack).

How to run the main flows (examples)
- Extract localization files (list-only):
  - Python API: `extract_i18n(language='zh', res_pak='test_data/res.pak', list_only=True)`
  - CLI (via orchestration script): `py Wartales_repack_font.py --res-pak test_data/res.pak -lang zh --extract-only`
- Inject localization files (update translation):
  - Python API: `inject_i18n(res_pak='test_data/res.pak', xml_source_dir='workspace/new_translation', language='zh')`
  - CLI: `py Wartales_repack_font.py --res-pak test_data/res.pak --inject-xml workspace/new_translation`
- Create fonts from extracted XML (txt2fnt):
  - Example command printed by `Wartales_repack_font.py`:
    `txt2fnt.exe -tf workspace/extracted-txt -fs 48 -ttf ChironHeiHK-Text-R-400.ttf -o noto_sans_cjk_regular -ff workspace/modded-assets/ui/fonts`
  - Note: `txt2fnt` is executed with cwd set to the TTF's directory — the tool loads the TTF by filename.
- Repack modified assets into `assets.pak`:
  - `_tools_/quickbms_4gb_files.exe -w -r -r _script_/script-v2.bms ./assets.pak ./workspace/modded-assets`

Tests and examples
- Example unit test: `test/test_res_i18n_extract.py` uses `unittest` and `test_data/res.pak`.
- Run example/test script: `py -m source.example.test_extract` or `python -m unittest discover -s test`.
- Tests assume `test_data/res.pak` present (checked into repo) and do not require external binaries for extract list-only checks.

Important project-specific patterns
- Relative-path-first design: constants like `_tools_`, `workspace/`, and `workspace/extracted-res` are hardcoded and expected by many functions — run commands from repo root.
- Safety checks and return codes: `Wartales_repack_font.py` uses return codes (2..8) for well-defined failure points — preserve these semantics when refactoring.
- Minimal external state: scripts intentionally print subprocess stdout/stderr rather than swallowing it — prefer explicit, observable behavior in edits.
- File expectations:
  - Extractor expects `workspace/extracted-res/lang/texts_{lang}.xml` and `workspace/extracted-res/lang/export_{lang}.xml`.
  - Injector stages files into `workspace/inject-res/lang/` before reimporting.
  - `txt2fnt` must output `workspace/modded-assets/ui/fonts/<outname>.fnt` and `.png`.

When editing or adding features (agent guidance)
- Verify tools in `_tools_/` and fail early: when adding code that runs external binaries, reuse `check_prereqs()` or equivalent safety checks.
- Preserve cross-platform considerations: project is Windows-focused (exe names), but keep paths relative to repo root and avoid hardcoding backslashes.
- For language changes, update `_lang_to_filters()` in `res_i18n_extractor.py` and add tests to `test/` that use `test_data/res.pak`.
- If changing `txt2fnt` invocation, test behavior with a local TTF in `_tools_/ttf/` and confirm that outputs appear in `workspace/modded-assets/ui/fonts/`.

Examples to reference in PRs
- "When you modify extraction filters, add a test that calls `extract_i18n(..., list_only=True)` and asserts the presence of `workspace/extracted-res/lang/...` files." ✅
- "If adding logging, prefer printing subprocess stdout/stderr as current scripts do to keep CLI debugging easy." 🔧

Do not assume
- Agents should not assume system-installed QuickBMS or fonts — required binaries are stored under `_tools_/` per README and must be present for full runs.
- Avoid making silent changes to the return codes or CLI contract without explicit tests and notes in the CHANGELOG/PR description.

If anything here is unclear or you'd like more detail (e.g., explicit example inputs, sample `txt2fnt` outputs, or a small integration test to add), tell me which area to expand. ✨


when using subprocess to run external .exe tools, never use cwd= to change the working directory; instead, always run the subprocess with the current working directory and adjust the command-line arguments accordingly.