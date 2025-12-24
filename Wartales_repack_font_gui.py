"""Simple Tkinter GUI for Wartales_repack_font

This GUI provides a small interface for selecting the TTF, font size,
res.pak path and language and then invoking the repack flow. It runs the
existing `Wartales_repack_font.exe` via subprocess in a background thread so
it can capture stdout/stderr and show progress without blocking the UI.

Notes:
- Run from the repository root so relative paths (_tools_, workspace/) resolve.
- The TTF chooser reads from `_tools_/ttf/*.ttf`.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkfont
import threading
import os
import glob
import subprocess
from typing import List


TOOLS_TTF = os.path.join("_tools_", "ttf")


def find_ttfs() -> List[str]:
    """Return a list of TTF basenames found in `_tools_/ttf`."""
    pattern = os.path.join(TOOLS_TTF, "*.ttf")
    return [os.path.basename(p) for p in sorted(glob.glob(pattern))]


# debug arg: --debug
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Wartales Repack Font GUI")
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="enable debug mode (prints extra info to console)",
    )
    return parser.parse_args()

args = parse_args()
global IS_DEBUG
IS_DEBUG = args.debug


class ToolTip:
    """
    It creates a tooltip for a given widget as the mouse goes on it.
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     # milliseconds
        self.wraplength = 300   # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()


class HelpLabel(ttk.Label):
    """A clickable (?) label that shows a tooltip and a message box on click."""
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text="(?)", foreground="blue", cursor="hand2", **kwargs)
        self.msg = text
        ToolTip(self, text)
        self.bind("<Button-1>", self.show_msgbox)

    def show_msgbox(self, event):
        messagebox.showinfo("Help", self.msg)


class RepackApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Wartales 戰爭傳說 重打中文字體包")
        root.geometry("880x640")

        # Slightly increase base UI fonts for better readability
        # (this adjusts default named Tcl/Tk fonts used by ttk and Text widgets)
        font_increase = 2
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                f = tkfont.nametofont(name)
                f.configure(size=max(6, f.cget("size") + font_increase))
            except Exception:
                # Some platforms may not have every named font available
                pass

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Res.pak input (disabled, fixed to res.pak in cwd)
        row = 0
        ttk.Label(frm, text="res.pak path:").grid(column=0, row=row, sticky=tk.W)
        self.respak_var = tk.StringVar(value="res.pak")
        ttk.Entry(frm, textvariable=self.respak_var, width=50, state="disabled").grid(
            column=1, row=row, sticky=tk.W, columnspan=2
        )

        # Font size
        row += 1
        ttk.Label(frm, text="字體大小（清晰度，建議23~48）：").grid(column=0, row=row, sticky=tk.W)
        self.font_size_var = tk.IntVar(value=48)
        ttk.Spinbox(
            frm, from_=8, to=256, textvariable=self.font_size_var, width=6
        ).grid(column=1, row=row, sticky=tk.W)

        # TTF selector
        row += 1
        ttk.Label(frm, text="TTF（字體及字重）：").grid(column=0, row=row, sticky=tk.W)
        self.ttf_var = tk.StringVar()
        self.ttf_menu = ttk.Combobox(
            frm, textvariable=self.ttf_var, state="readonly", width=40
        )
        self._refresh_ttf_list()
        self.ttf_menu.grid(column=1, row=row, sticky=tk.W)
        ttk.Button(frm, text="Refresh", command=self._refresh_ttf_list).grid(
            column=2, row=row, sticky=tk.W
        )

        # Language (disabled for now)
        row += 1
        ttk.Label(frm, text="Language:").grid(column=0, row=row, sticky=tk.W)
        self.lang_var = tk.StringVar(value="zh")
        lang_box = ttk.Combobox(
            frm, textvariable=self.lang_var, values=["zh"], state="disabled", width=10
        )
        lang_box.grid(column=1, row=row, sticky=tk.W)

        # Run button and status
        row += 1

        # Col 0: Run button + Help
        run_frame = ttk.Frame(frm)
        run_frame.grid(column=0, row=row, sticky=tk.W)
        self.run_btn = ttk.Button(run_frame, text="重打字體", command=self._on_run)
        self.run_btn.pack(side=tk.LEFT)
        HelpLabel(run_frame, "執行字體重打包流程：\n1. 從 res.pak 提取中文文本\n2. 根據文本與選定 TTF 生成字體\n3. 將生成的字體打包進 assets.pak").pack(side=tk.LEFT, padx=2)

        # Col 1: Status
        self.status_lbl = tk.Label(frm, text="Ready")
        self.status_lbl.grid(column=1, row=row, sticky=tk.W)

        # Col 2: Extract button + Help
        extract_frame = ttk.Frame(frm)
        extract_frame.grid(column=2, row=row, sticky=tk.E)
        self.extract_btn = ttk.Button(extract_frame, text="只提取文本", command=self._on_extract_only)
        self.extract_btn.pack(side=tk.LEFT)
        HelpLabel(extract_frame, "僅執行第一步：\n1. 從 res.pak 提取中文文本\n(不生成字體也不打包)").pack(side=tk.LEFT, padx=2)

        # Col 3: Inject button + Help
        inject_frame = ttk.Frame(frm)
        inject_frame.grid(column=3, row=row, sticky=tk.W, padx=(5, 0))
        self.inject_btn = ttk.Button(inject_frame, text="只注入新翻譯", command=self._on_inject_xml)
        self.inject_btn.pack(side=tk.LEFT)
        HelpLabel(inject_frame, "將 _new_xml_ 資料夾中的翻譯檔注入 res.pak\n(Inject translation files from _new_xml_ folder into res.pak)").pack(side=tk.LEFT, padx=2)

        # Log area
        row += 1
        ttk.Label(frm, text="Output log:").grid(column=0, row=row, sticky=tk.W)
        row += 1
        self.log = scrolledtext.ScrolledText(frm, height=18, wrap=tk.WORD)
        self.log.grid(column=0, row=row, columnspan=4, sticky=tk.N + tk.S + tk.E + tk.W)

        # Configure resizing
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=1)
        frm.columnconfigure(3, weight=0)
        frm.rowconfigure(row, weight=1)

        # Status label fonts and colors for spinner
        self._status_font_normal = tkfont.Font(font=self.status_lbl.cget("font"))
        self._status_font_large = self._status_font_normal.copy()
        # Increase size and bold for visibility
        self._status_font_large.configure(size=max(self._status_font_normal.cget("size") + 6, 16), weight="bold")
        fg = self.status_lbl.cget("foreground")
        self._status_fg_normal = fg if fg else "black"

        # Internal state
        self._running = False
        self._spinner_phase = 0

    def _refresh_ttf_list(self):
        ttfs = find_ttfs()
        if not ttfs:
            self.ttf_menu["values"] = []
            self.ttf_var.set("")
            self.ttf_menu.set("(no TTFs found)")
        else:
            self.ttf_menu["values"] = ttfs
            # Prefer ChironGoRoundTC-400R.ttf if available, otherwise select the first entry
            preferred = "ChironGoRoundTC-400R.ttf"
            if not self.ttf_var.get() or self.ttf_var.get() not in ttfs:
                choice = preferred if preferred in ttfs else ttfs[0]
                self.ttf_var.set(choice)

    def _append_log(self, text: str):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def _animate_spinner(self):
        if not self._running:
            # Reset to normal appearance
            self.status_lbl.config(text="Ready", font=self._status_font_normal, foreground=self._status_fg_normal, anchor="w", justify="left")
            self.status_lbl.grid_configure(sticky=tk.W)
            return
        phases = ["Running.", "Running..", "Running...", "Running    "]
        self.status_lbl.config(
            text=phases[self._spinner_phase % len(phases)],
            font=self._status_font_large,
            foreground="red",
            anchor="center",
            justify="center"
        )
        # Use empty sticky so the label stays centered in its grid cell (Tk expects n/e/s/w strings)
        self.status_lbl.grid_configure(sticky='')
        self._spinner_phase += 1
        # schedule next animation frame
        self.root.after(400, self._animate_spinner)

    def _on_run(self):
        if self._running:
            return
        # verify ttf selection
        ttf = self.ttf_var.get()
        if not ttf:
            messagebox.showwarning(
                "No TTF",
                "No TTF selected. Please add a .ttf file to _tools_/ttf and Refresh.",
            )
            return

        respak = self.respak_var.get()
        font_size = self.font_size_var.get()
        lang = self.lang_var.get()

        # disable controls
        self.run_btn.config(state=tk.DISABLED)
        self._running = True
        self._append_log(
            f"Starting repack: ttf={ttf}, fs={font_size}, res_pak={respak}, lang={lang}\n"
        )
        self._animate_spinner()

        # run in background thread
        thread = threading.Thread(
            target=self._run_repack_thread,
            args=(ttf, font_size, respak, lang, "full"),
            daemon=True,
        )
        thread.start()

    def _on_extract_only(self):
        if self._running:
            return

        respak = self.respak_var.get()
        lang = self.lang_var.get()
        # ttf/font_size not strictly needed for extract only but we pass them to keep signature simple
        ttf = self.ttf_var.get() or "default"
        font_size = self.font_size_var.get()

        # disable controls
        self.run_btn.config(state=tk.DISABLED)
        self.extract_btn.config(state=tk.DISABLED)
        self.inject_btn.config(state=tk.DISABLED)
        self._running = True
        self._append_log(
            f"Starting extraction only: res_pak={respak}, lang={lang}\n"
        )
        self._animate_spinner()

        # run in background thread
        thread = threading.Thread(
            target=self._run_repack_thread,
            args=(ttf, font_size, respak, lang, "extract"),
            daemon=True,
        )
        thread.start()

    def _on_inject_xml(self):
        if self._running:
            return

        respak = self.respak_var.get()
        lang = self.lang_var.get()
        ttf = self.ttf_var.get() or "default"
        font_size = self.font_size_var.get()

        new_xml_dir = "_new_xml_"
        if not os.path.exists(new_xml_dir):
            messagebox.showerror("Error", f"Directory not found: {new_xml_dir}\nPlease create it and put xml files there.")
            return

        # disable controls
        self.run_btn.config(state=tk.DISABLED)
        self.extract_btn.config(state=tk.DISABLED)
        self.inject_btn.config(state=tk.DISABLED)
        self._running = True
        self._append_log(
            f"Starting injection: xml_dir={new_xml_dir}, res_pak={respak}, lang={lang}\n"
        )
        self._animate_spinner()

        # run in background thread
        thread = threading.Thread(
            target=self._run_repack_thread,
            args=(ttf, font_size, respak, lang, "inject"),
            daemon=True,
        )
        thread.start()

    def _run_repack_thread(self, ttf: str, font_size: int, respak: str, lang: str, mode: str):
        # Locate Wartales_repack_font.exe (expect in the repo root or same dir as this script)
        exe_name = "Wartales_repack_font.exe"
        exe_path = os.path.join(os.path.dirname(__file__), exe_name)
        if not os.path.exists(exe_path):
            exe_path = os.path.join(os.getcwd(), exe_name)
        if not os.path.exists(exe_path):
            msg = f"Executable not found: {exe_name}. Please build the exe and place it in the repository root.\n"
            self.root.after(0, self._on_finish, False, msg)
            return

        # Build argv for subprocess
        argv = [
            exe_path,
            "--ttf",
            ttf,
            "-fs",
            str(font_size),
            "--res-pak",
            respak,
            "-lang",
            lang,
        ]
        if mode == "extract":
            argv.append("--extract-only")
        elif mode == "inject":
            argv.append("--inject-xml")
            argv.append("_new_xml_")

        # Run subprocess and capture stdout/stderr
        if IS_DEBUG:
            print(f"Running subprocess: {' '.join(argv)}")
            # just sleep 5 seconds to simulate
            proc = subprocess.run(["sleep", "5"], capture_output=True, text=True)
            output = proc.stdout or ""
            exit_code = proc.returncode
        else:
          try:
              proc = subprocess.run(
                  argv,
                  stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT,
                  text=True,
                  creationflags=subprocess.CREATE_NO_WINDOW
              )
              output = proc.stdout or ""
              exit_code = proc.returncode
          except Exception as exc:
              output = f"Exception while running {exe_name}: {exc}\n"
              exit_code = 1

        success = exit_code == 0
        # Schedule GUI update with the captured output
        self.root.after(0, lambda: self._on_finish(success, output))

    def _on_finish(self, success: bool, output: str):
        # append output to log and re-enable controls
        self._append_log(output + "\n")
        if success:
            messagebox.showinfo("Repack finished", "Repack completed successfully.")
        else:
            messagebox.showerror(
                "Repack failed", "Repack failed. See output for details."
            )
        self._running = False
        self.run_btn.config(state=tk.NORMAL)
        self.extract_btn.config(state=tk.NORMAL)
        self.inject_btn.config(state=tk.NORMAL)
        self.status_lbl.config(text="Ready")


def main():
    root = tk.Tk()
    app = RepackApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
