import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


class Notepad(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Untitled - Notepad")
        self.geometry("900x600")

        self.filepath = None
        self._ignore_modified = False

        self._build_ui()
        self._bind_shortcuts()
        self._update_title()
        self._set_status("Ready")

        # Track modifications
        self.text.edit_modified(False)
        self.text.bind("<<Modified>>", self._on_modified)

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.text.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.find_dialog)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        self.word_wrap_var = tk.BooleanVar(value=True)
        self.status_bar_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap_var, command=self.toggle_word_wrap)
        view_menu.add_checkbutton(label="Status Bar", variable=self.status_bar_var, command=self.toggle_status_bar)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

        # Text + scrollbars
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.v_scroll = ttk.Scrollbar(container, orient="vertical")
        self.h_scroll = ttk.Scrollbar(container, orient="horizontal")

        self.text = tk.Text(
            container,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
        )

        self.v_scroll.config(command=self.text.yview)
        self.h_scroll.config(command=self.text.xview)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.text.pack(side="left", fill="both", expand=True)

        # Status bar
        self.status = ttk.Label(self, anchor="w")
        self.status.pack(side="bottom", fill="x")
        self.text.bind("<KeyRelease>", lambda e: self._update_cursor_status())
        self.text.bind("<ButtonRelease>", lambda e: self._update_cursor_status())
        self._update_cursor_status()

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as())          # Ctrl+Shift+S on many systems
        self.bind("<Control-Shift-s>", lambda e: self.save_as())

        self.bind("<Control-a>", lambda e: self.select_all())
        self.bind("<Control-f>", lambda e: self.find_dialog())

        # Windows Notepad-style redo is Ctrl+Y; macOS often uses Cmd+Shift+Z, but we’ll keep it simple.

    # ---------- Core actions ----------
    def new_file(self):
        if not self._confirm_discard_changes():
            return
        self.filepath = None
        self._ignore_modified = True
        self.text.delete("1.0", "end")
        self.text.edit_modified(False)
        self._ignore_modified = False
        self._update_title()
        self._set_status("New file")

    def open_file(self):
        if not self._confirm_discard_changes():
            return

        path = filedialog.askopenfilename(
            title="Open",
            filetypes=[
                ("Text Documents", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # fallback for some Windows ANSI files
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as ex:
            messagebox.showerror("Open Error", f"Could not open file:\n{ex}")
            return

        self.filepath = path
        self._ignore_modified = True
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.edit_modified(False)
        self._ignore_modified = False
        self._update_title()
        self._set_status(f"Opened: {os.path.basename(path)}")

    def save_file(self):
        if self.filepath is None:
            return self.save_as()

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
        except Exception as ex:
            messagebox.showerror("Save Error", f"Could not save file:\n{ex}")
            return

        self.text.edit_modified(False)
        self._update_title()
        self._set_status(f"Saved: {os.path.basename(self.filepath)}")

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[
                ("Text Documents", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if not path:
            return

        self.filepath = path
        self.save_file()

    def on_exit(self):
        if self._confirm_discard_changes():
            self.destroy()

    # ---------- Edit actions ----------
    def undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    def select_all(self):
        self.text.tag_add("sel", "1.0", "end-1c")
        self.text.mark_set("insert", "1.0")
        self.text.see("insert")

    # ---------- Find ----------
    def find_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Find")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Find what:").grid(row=0, column=0, padx=10, pady=10, sticky="w")

        needle_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=needle_var, width=32)
        entry.grid(row=0, column=1, padx=10, pady=10)
        entry.focus_set()

        match_case = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Match case", variable=match_case).grid(
            row=1, column=1, padx=10, sticky="w"
        )

        def do_find():
            self._clear_find_highlight()
            needle = needle_var.get()
            if not needle:
                return

            start = self.text.index("insert")
            flags = 0 if match_case.get() else tk.INSERT

            # Tk text search supports nocase via option, not flags.
            idx = self.text.search(
                needle,
                start,
                stopindex="end",
                nocase=not match_case.get(),
            )
            if not idx:
                # Wrap around
                idx = self.text.search(
                    needle,
                    "1.0",
                    stopindex=start,
                    nocase=not match_case.get(),
                )
            if not idx:
                self._set_status("Not found")
                return

            end = f"{idx}+{len(needle)}c"
            self.text.tag_add("find_highlight", idx, end)
            self.text.tag_config("find_highlight", background="#ffe08a")
            self.text.mark_set("insert", end)
            self.text.see(idx)
            self._set_status(f"Found: {needle!r}")

        ttk.Button(dialog, text="Find Next", command=do_find).grid(
            row=0, column=2, padx=10, pady=10
        )
        ttk.Button(dialog, text="Close", command=dialog.destroy).grid(
            row=1, column=2, padx=10, pady=(0, 10)
        )

        dialog.bind("<Return>", lambda e: do_find())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _clear_find_highlight(self):
        self.text.tag_remove("find_highlight", "1.0", "end")

    # ---------- View ----------
    def toggle_word_wrap(self):
        if self.word_wrap_var.get():
            self.text.config(wrap="word")
            self.h_scroll.pack_forget()
        else:
            self.text.config(wrap="none")
            self.h_scroll.pack(side="bottom", fill="x")
        self._set_status("Word wrap " + ("on" if self.word_wrap_var.get() else "off"))

    def toggle_status_bar(self):
        if self.status_bar_var.get():
            self.status.pack(side="bottom", fill="x")
        else:
            self.status.pack_forget()

    # ---------- Status / helpers ----------
    def _on_modified(self, event=None):
        if self._ignore_modified:
            return
        # reset the modified flag so this event can fire again
        modified = self.text.edit_modified()
        self.text.edit_modified(False)
        if modified:
            self._update_title()
            self._update_cursor_status()

    def _update_title(self):
        name = os.path.basename(self.filepath) if self.filepath else "Untitled"
        star = "*" if self.text.edit_modified() else ""
        self.title(f"{name}{star} - Notepad")

    def _confirm_discard_changes(self):
        if not self.text.edit_modified():
            return True
        name = os.path.basename(self.filepath) if self.filepath else "Untitled"
        result = messagebox.askyesnocancel("Notepad", f"Do you want to save changes to {name}?")
        if result is None:  # Cancel
            return False
        if result is True:  # Yes
            self.save_file()
            return not self.text.edit_modified()  # if save failed, remain modified
        return True  # No

    def _set_status(self, msg):
        if self.status_bar_var.get():
            self.status.config(text=msg)

    def _update_cursor_status(self):
        # Line/column like Notepad
        line, col = self.text.index("insert").split(".")
        self._set_status(f"Ln {line}, Col {int(col) + 1}")

    def about(self):
        messagebox.showinfo(
            "About",
            "Tkinter Notepad\n\nA simple Notepad-like editor built with Python + Tkinter.",
        )


if __name__ == "__main__":
    app = Notepad()
    app.mainloop()
