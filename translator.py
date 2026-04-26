import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import pyperclip
from PIL import Image, ImageTk
import os

# Local modules
from themes import get_theme, list_themes
from storage import Storage
from engine import TranslationEngine, LANG_CODES, MODES
import tts_handler

class LanguageTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.storage = Storage()
        self.engine = TranslationEngine(self.storage)
        
        # Load settings
        self.current_theme_name = self.storage.get("theme", "dark")
        self.theme = get_theme(self.current_theme_name)
        
        self.setup_window()
        self.init_variables()
        self.create_styles()
        self.build_ui()
        
        # Initial state
        self.update_counts()
        self.root.after(100, self.apply_theme)
        
        # Debounce timer
        self.debounce_id = None

    def setup_window(self):
        self.root.title("Premium Language Translator")
        geometry = self.storage.get("geometry", "1100x750")
        self.root.geometry(geometry)
        self.root.minsize(900, 600)
        self.root.configure(bg=self.theme["bg"])
        
        # Icons (placeholders for now or simple canvas-drawn)
        self.root.bind("<Control-Return>", lambda e: self.perform_translation())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_variables(self):
        self.src_lang_var = tk.StringVar(value=self.storage.get("src_lang", "auto"))
        self.tgt_lang_var = tk.StringVar(value=self.storage.get("tgt_lang", "hi"))
        self.mode_var = tk.StringVar(value=self.storage.get("mode", "general"))
        self.auto_detect_var = tk.BooleanVar(value=(self.src_lang_var.get() == "auto"))
        self.real_time_var = tk.BooleanVar(value=self.storage.get("real_time", False))
        self.char_count_var = tk.StringVar(value="0 characters")
        self.word_count_var = tk.StringVar(value="0 words")
        self.status_var = tk.StringVar(value="Ready")

    def create_styles(self):
        self.style = ttk.Style()
        # We'll use custom frame colors mostly, but some basic ttk styling
        self.style.theme_use('clam')
        self.style.configure("TCombobox", fieldbackground=self.theme["input_bg"], background=self.theme["bg_secondary"], foreground=self.theme["fg"])

    def build_ui(self):
        # Sidebar for History/Favorites
        self.sidebar = tk.Frame(self.root, bg=self.theme["bg_secondary"], width=280)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.build_sidebar()

        # Main Content Area
        self.main_container = tk.Frame(self.root, bg=self.theme["bg"])
        self.main_container.pack(side="right", fill="both", expand=True)

        # Header with Controls
        self.header = tk.Frame(self.main_container, bg=self.theme["bg"], height=80)
        self.header.pack(fill="x", padx=30, pady=(20, 10))
        
        self.build_header()

        # Text Areas
        self.text_frame = tk.Frame(self.main_container, bg=self.theme["bg"])
        self.text_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.build_text_areas()

        # Footer
        self.footer = tk.Frame(self.main_container, bg=self.theme["bg"], height=40)
        self.footer.pack(fill="x", padx=30, pady=(10, 20))
        
        self.build_footer()

    def build_sidebar(self):
        # Tabs for History and Favorites
        tab_frame = tk.Frame(self.sidebar, bg=self.theme["bg_secondary"])
        tab_frame.pack(fill="x")
        
        self.hist_tab_btn = tk.Button(tab_frame, text="History", font=("Inter", 10, "bold"), 
                                    bg=self.theme["bg_tertiary"], fg=self.theme["fg"],
                                    relief="flat", bd=0, padx=20, pady=10,
                                    command=lambda: self.show_sidebar_tab("history"))
        self.hist_tab_btn.pack(side="left", fill="x", expand=True)
        
        self.fav_tab_btn = tk.Button(tab_frame, text="Favorites", font=("Inter", 10), 
                                   bg=self.theme["bg_secondary"], fg=self.theme["fg_secondary"],
                                   relief="flat", bd=0, padx=20, pady=10,
                                   command=lambda: self.show_sidebar_tab("favorites"))
        self.fav_tab_btn.pack(side="left", fill="x", expand=True)

        # Search Bar for Sidebar
        search_frame = tk.Frame(self.sidebar, bg=self.theme["bg_secondary"], padx=10, pady=10)
        search_frame.pack(fill="x")
        
        self.sidebar_search_var = tk.StringVar()
        self.sidebar_search_var.trace_add("write", lambda *args: self.refresh_sidebar_list())
        
        search_entry = tk.Entry(search_frame, textvariable=self.sidebar_search_var, 
                               bg=self.theme["input_bg"], fg=self.theme["fg"],
                               insertbackground=self.theme["fg"], relief="flat", font=("Inter", 10))
        search_entry.pack(fill="x", ipady=5, padx=5)
        tk.Label(search_frame, text="🔍 Search...", font=("Inter", 8), bg=self.theme["bg_secondary"], fg=self.theme["fg_secondary"]).pack(anchor="w", padx=5)

        # List Area
        self.sidebar_list_frame = tk.Frame(self.sidebar, bg=self.theme["bg_secondary"])
        self.sidebar_list_frame.pack(fill="both", expand=True)
        
        self.sidebar_canvas = tk.Canvas(self.sidebar_list_frame, bg=self.theme["bg_secondary"], highlightthickness=0)
        self.sidebar_scrollbar = ttk.Scrollbar(self.sidebar_list_frame, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_scroll_frame = tk.Frame(self.sidebar_canvas, bg=self.theme["bg_secondary"])
        
        self.sidebar_scroll_frame.bind("<Configure>", lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all")))
        self.sidebar_canvas.create_window((0, 0), window=self.sidebar_scroll_frame, anchor="nw", width=260)
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
        
        self.sidebar_canvas.pack(side="left", fill="both", expand=True)
        self.sidebar_scrollbar.pack(side="right", fill="y")
        
        self.current_sidebar_tab = "history"
        self.refresh_sidebar_list()

    def build_header(self):
        # Language Selectors
        lang_frame = tk.Frame(self.header, bg=self.theme["bg"])
        lang_frame.pack(fill="x")

        # Source Lang
        src_frame = tk.Frame(lang_frame, bg=self.theme["bg"])
        src_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(src_frame, text="From", font=("Inter", 9, "bold"), bg=self.theme["bg"], fg=self.theme["fg_secondary"]).pack(anchor="w")
        
        self.src_lang_combo = ttk.Combobox(src_frame, textvariable=self.src_lang_var, values=self.engine.language_list() + ["Auto-Detect (auto)"])
        self.src_lang_combo.pack(fill="x", pady=5, padx=(0, 10))
        self.src_lang_combo.bind("<<ComboboxSelected>>", self.on_lang_change)

        # Swap Button
        swap_btn = tk.Button(lang_frame, text="⇄", font=("Inter", 16), 
                           bg=self.theme["bg_secondary"], fg=self.theme["accent"],
                           relief="flat", bd=0, width=3, cursor="hand2",
                           command=self.swap_languages)
        swap_btn.pack(side="left", pady=(15, 0))

        # Target Lang
        tgt_frame = tk.Frame(lang_frame, bg=self.theme["bg"])
        tgt_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(tgt_frame, text="To", font=("Inter", 9, "bold"), bg=self.theme["bg"], fg=self.theme["fg_secondary"]).pack(anchor="w", padx=(10, 0))
        
        self.tgt_lang_combo = ttk.Combobox(tgt_frame, textvariable=self.tgt_lang_var, values=self.engine.language_list())
        self.tgt_lang_combo.pack(fill="x", pady=5, padx=(10, 0))
        self.tgt_lang_combo.bind("<<ComboboxSelected>>", self.on_lang_change)

        # Mode and Real-time toggle
        opt_frame = tk.Frame(self.header, bg=self.theme["bg"])
        opt_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(opt_frame, text="Mode:", font=("Inter", 9), bg=self.theme["bg"], fg=self.theme["fg_secondary"]).pack(side="left")
        mode_menu = ttk.OptionMenu(opt_frame, self.mode_var, self.mode_var.get(), *MODES.values())
        mode_menu.pack(side="left", padx=5)
        
        rt_check = tk.Checkbutton(opt_frame, text="Real-time", variable=self.real_time_var, 
                                 bg=self.theme["bg"], fg=self.theme["fg"], 
                                 activebackground=self.theme["bg"], selectcolor=self.theme["bg_secondary"],
                                 font=("Inter", 9), command=self.on_realtime_toggle)
        rt_check.pack(side="left", padx=15)
        
        theme_label = tk.Label(opt_frame, text="Theme:", font=("Inter", 9), bg=self.theme["bg"], fg=self.theme["fg_secondary"])
        theme_label.pack(side="right")
        self.theme_var = tk.StringVar(value=self.current_theme_name)
        theme_menu = ttk.OptionMenu(opt_frame, self.theme_var, self.current_theme_name, *[t[0] for t in list_themes()], command=self.change_theme)
        theme_menu.pack(side="right", padx=5)

    def build_text_areas(self):
        # Input Section
        self.input_container = tk.Frame(self.text_frame, bg=self.theme["bg_secondary"], highlightbackground=self.theme["border"], highlightthickness=1)
        self.input_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        input_toolbar = tk.Frame(self.input_container, bg=self.theme["bg_tertiary"], height=35)
        input_toolbar.pack(fill="x")
        input_toolbar.pack_propagate(False)
        
        tk.Label(input_toolbar, text="Source Text", font=("Inter", 8, "bold"), bg=self.theme["bg_tertiary"], fg=self.theme["fg_secondary"]).pack(side="left", padx=10)
        
        # Tools
        tk.Button(input_toolbar, text="📋 Paste", font=("Inter", 8), bg=self.theme["bg_tertiary"], fg=self.theme["fg"], relief="flat", command=self.paste_text).pack(side="right", padx=5)
        tk.Button(input_toolbar, text="🗑️ Clear", font=("Inter", 8), bg=self.theme["bg_tertiary"], fg=self.theme["error"], relief="flat", command=self.clear_input).pack(side="right", padx=5)
        tk.Button(input_toolbar, text="🔊", font=("Inter", 10), bg=self.theme["bg_tertiary"], fg=self.theme["fg"], relief="flat", command=lambda: self.play_tts("src")).pack(side="right", padx=5)

        self.input_text = tk.Text(self.input_container, font=("Inter", self.storage.get("font_size", 13)), 
                                 bg=self.theme["input_bg"], fg=self.theme["fg"], 
                                 insertbackground=self.theme["fg"], relief="flat", borderwidth=0,
                                 padx=15, pady=15, undo=True)
        self.input_text.pack(fill="both", expand=True)
        self.input_text.bind("<<Modified>>", self.on_text_modified)

        # Output Section
        self.output_container = tk.Frame(self.text_frame, bg=self.theme["bg_secondary"], highlightbackground=self.theme["border"], highlightthickness=1)
        self.output_container.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        output_toolbar = tk.Frame(self.output_container, bg=self.theme["bg_tertiary"], height=35)
        output_toolbar.pack(fill="x")
        output_toolbar.pack_propagate(False)
        
        tk.Label(output_toolbar, text="Translation", font=("Inter", 8, "bold"), bg=self.theme["bg_tertiary"], fg=self.theme["fg_secondary"]).pack(side="left", padx=10)
        
        self.fav_btn = tk.Button(output_toolbar, text="☆", font=("Inter", 12), bg=self.theme["bg_tertiary"], fg=self.theme["warning"], relief="flat", command=self.toggle_favorite)
        self.fav_btn.pack(side="right", padx=5)
        tk.Button(output_toolbar, text="📄 Copy", font=("Inter", 8), bg=self.theme["bg_tertiary"], fg=self.theme["fg"], relief="flat", command=self.copy_output).pack(side="right", padx=5)
        tk.Button(output_toolbar, text="🔊", font=("Inter", 10), bg=self.theme["bg_tertiary"], fg=self.theme["fg"], relief="flat", command=lambda: self.play_tts("tgt")).pack(side="right", padx=5)

        self.output_text = tk.Text(self.output_container, font=("Inter", self.storage.get("font_size", 13)), 
                                  bg=self.theme["input_bg"], fg=self.theme["fg"], 
                                  insertbackground=self.theme["fg"], relief="flat", borderwidth=0,
                                  padx=15, pady=15)
        self.output_text.pack(fill="both", expand=True)
        self.output_text.configure(state="disabled") # Start as disabled

    def build_footer(self):
        # Stats
        stats_frame = tk.Frame(self.footer, bg=self.theme["bg"])
        stats_frame.pack(side="left")
        
        tk.Label(stats_frame, textvariable=self.char_count_var, font=("Inter", 9), bg=self.theme["bg"], fg=self.theme["fg_secondary"]).pack(side="left")
        tk.Label(stats_frame, text=" | ", font=("Inter", 9), bg=self.theme["bg"], fg=self.theme["fg_secondary"]).pack(side="left", padx=5)
        tk.Label(stats_frame, textvariable=self.word_count_var, font=("Inter", 9), bg=self.theme["bg"], fg=self.theme["fg_secondary"]).pack(side="left")
        
        # Status
        self.status_label = tk.Label(self.footer, textvariable=self.status_var, font=("Inter", 9, "italic"), bg=self.theme["bg"], fg=self.theme["fg_secondary"])
        self.status_label.pack(side="right", padx=20)
        
        # Action Buttons
        self.translate_btn = tk.Button(self.footer, text="Translate (Ctrl+Enter)", font=("Inter", 10, "bold"), 
                                     bg=self.theme["accent"], fg=self.theme["button_fg"],
                                     activebackground=self.theme["accent_hover"], activeforeground=self.theme["button_fg"],
                                     relief="flat", bd=0, padx=25, pady=8, cursor="hand2",
                                     command=self.perform_translation)
        self.translate_btn.pack(side="right")

    # ── Logic ──────────────────────────────────────────────────

    def on_text_modified(self, event=None):
        if self.input_text.edit_modified():
            self.update_counts()
            if self.real_time_var.get():
                self.debounce_translation()
            self.input_text.edit_modified(False)

    def update_counts(self):
        text = self.input_text.get("1.0", "end-1c")
        chars = len(text)
        words = len(text.split())
        self.char_count_var.set(f"{chars} characters")
        self.word_count_var.set(f"{words} words")

    def debounce_translation(self):
        if self.debounce_id:
            self.root.after_cancel(self.debounce_id)
        self.debounce_id = self.root.after(800, self.perform_translation)

    def perform_translation(self):
        text = self.input_text.get("1.0", "end-1c").strip()
        if not text:
            self.set_output("")
            return
        
        self.status_var.set("Translating...")
        self.translate_btn.configure(state="disabled")
        
        # Get codes
        src_raw = self.src_lang_var.get()
        tgt_raw = self.tgt_lang_var.get()
        
        src_code = self.engine.parse_lang_selection(src_raw)
        tgt_code = self.engine.parse_lang_selection(tgt_raw)
        mode = self.mode_var.get().lower()

        # Auto-detect if needed
        if src_code == "auto":
            detected = self.engine.detect(text)
            self.status_var.set(f"Detected: {self.engine.lang_name(detected)} | Translating...")
            src_code = detected

        def on_success(result):
            self.root.after(0, lambda: self._handle_success(text, result, src_code, tgt_code, mode))

        def on_fail(err):
            self.root.after(0, lambda: self._handle_error(err))

        self.engine.translate(text, src_code, tgt_code, mode, on_success, on_fail)

    def _handle_success(self, src_text, result, src_code, tgt_code, mode):
        self.set_output(result)
        self.status_var.set("Ready")
        self.translate_btn.configure(state="normal")
        
        # Save to history
        entry = self.storage.add_history(src_text, result, src_code, tgt_code, mode)
        if entry:
            self.refresh_sidebar_list()
        
        # Update favorite icon
        self.update_fav_icon()

    def _handle_error(self, err):
        self.status_var.set("Error occurred")
        self.translate_btn.configure(state="normal")
        messagebox.showerror("Translation Error", f"Failed to translate: {err}")

    def set_output(self, text):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def swap_languages(self):
        s, t = self.src_lang_var.get(), self.tgt_lang_var.get()
        if "Auto-Detect" in s:
            return # Can't swap auto-detect
        self.src_lang_var.set(t)
        self.tgt_lang_var.set(s)
        
        # If there's text in output, maybe swap that too?
        in_text = self.input_text.get("1.0", "end-1c")
        out_text = self.output_text.get("1.0", "end-1c")
        if out_text:
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", out_text)
            self.set_output(in_text)

    def on_lang_change(self, event=None):
        if self.real_time_var.get():
            self.perform_translation()

    def on_realtime_toggle(self):
        if self.real_time_var.get():
            self.perform_translation()

    def clear_input(self):
        self.input_text.delete("1.0", "end")
        self.set_output("")
        self.update_counts()

    def paste_text(self):
        try:
            text = self.root.clipboard_get()
            self.input_text.insert("insert", text)
            self.update_counts()
        except:
            pass

    def copy_output(self):
        text = self.output_text.get("1.0", "end-1c")
        if text:
            pyperclip.copy(text)
            self.status_var.set("Copied to clipboard!")
            self.root.after(2000, lambda: self.status_var.set("Ready"))

    def play_tts(self, side):
        text = self.input_text.get("1.0", "end-1c") if side == "src" else self.output_text.get("1.0", "end-1c")
        if text:
            tts_handler.speak(text, rate=self.storage.get("tts_rate", 160))

    def toggle_favorite(self):
        src = self.input_text.get("1.0", "end-1c").strip()
        tgt = self.output_text.get("1.0", "end-1c").strip()
        if not src or not tgt: return
        
        sl = self.engine.parse_lang_selection(self.src_lang_var.get())
        tl = self.engine.parse_lang_selection(self.tgt_lang_var.get())
        
        entry = {"src_text": src, "tgt_text": tgt, "src_lang": sl, "tgt_lang": tl, "timestamp": time.ctime()}
        is_fav = self.storage.toggle_favorite(entry)
        self.update_fav_icon()
        if self.current_sidebar_tab == "favorites":
            self.refresh_sidebar_list()

    def update_fav_icon(self):
        src = self.input_text.get("1.0", "end-1c").strip()
        tl = self.engine.parse_lang_selection(self.tgt_lang_var.get())
        if self.storage.is_favorite(src, tl):
            self.fav_btn.configure(text="★", fg=self.theme["warning"])
        else:
            self.fav_btn.configure(text="☆", fg=self.theme["fg_secondary"])

    def show_sidebar_tab(self, tab):
        self.current_sidebar_tab = tab
        if tab == "history":
            self.hist_tab_btn.configure(bg=self.theme["bg_tertiary"], fg=self.theme["fg"])
            self.fav_tab_btn.configure(bg=self.theme["bg_secondary"], fg=self.theme["fg_secondary"])
        else:
            self.fav_tab_btn.configure(bg=self.theme["bg_tertiary"], fg=self.theme["fg"])
            self.hist_tab_btn.configure(bg=self.theme["bg_secondary"], fg=self.theme["fg_secondary"])
        self.refresh_sidebar_list()

    def refresh_sidebar_list(self):
        # Clear current list
        for widget in self.sidebar_scroll_frame.winfo_children():
            widget.destroy()
        
        q = self.sidebar_search_var.get().lower()
        items = self.storage.history if self.current_sidebar_tab == "history" else self.storage.favorites
        
        if q:
            items = [i for i in items if q in i["src_text"].lower() or q in i["tgt_text"].lower()]

        if not items:
            tk.Label(self.sidebar_scroll_frame, text="No items found", bg=self.theme["bg_secondary"], fg=self.theme["fg_secondary"], pady=20).pack()
            return

        for idx, item in enumerate(items):
            self.create_sidebar_item(idx, item)

    def create_sidebar_item(self, idx, item):
        frame = tk.Frame(self.sidebar_scroll_frame, bg=self.theme["bg_secondary"], padx=10, pady=8, cursor="hand2")
        frame.pack(fill="x", pady=1)
        
        # Hover effect
        frame.bind("<Enter>", lambda e: frame.configure(bg=self.theme["bg_tertiary"]))
        frame.bind("<Leave>", lambda e: frame.configure(bg=self.theme["bg_secondary"]))
        frame.bind("<Button-1>", lambda e: self.load_from_sidebar(item))

        langs = tk.Label(frame, text=f"{item['src_lang'].upper()} ➔ {item['tgt_lang'].upper()}", font=("Inter", 7, "bold"), bg=frame["bg"], fg=self.theme["accent"])
        langs.pack(anchor="w")
        
        txt = item["src_text"][:40] + "..." if len(item["src_text"]) > 40 else item["src_text"]
        lbl = tk.Label(frame, text=txt, font=("Inter", 9), bg=frame["bg"], fg=self.theme["fg"], justify="left", wraplength=220)
        lbl.pack(anchor="w")
        
        # Sub-widgets need event binding too
        langs.bind("<Button-1>", lambda e: self.load_from_sidebar(item))
        lbl.bind("<Button-1>", lambda e: self.load_from_sidebar(item))

    def load_from_sidebar(self, item):
        self.src_lang_var.set(self.engine.lang_name(item["src_lang"]))
        self.tgt_lang_var.set(self.engine.lang_name(item["tgt_lang"]))
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", item["src_text"])
        self.set_output(item["tgt_text"])
        self.update_counts()
        self.update_fav_icon()

    def change_theme(self, name):
        self.current_theme_name = name
        self.theme = get_theme(name)
        self.storage.set("theme", name)
        self.apply_theme()

    def apply_theme(self):
        # This is a bit manual in pure tkinter
        self.root.configure(bg=self.theme["bg"])
        self.sidebar.configure(bg=self.theme["bg_secondary"])
        self.sidebar_canvas.configure(bg=self.theme["bg_secondary"])
        self.sidebar_scroll_frame.configure(bg=self.theme["bg_secondary"])
        self.main_container.configure(bg=self.theme["bg"])
        self.header.configure(bg=self.theme["bg"])
        self.footer.configure(bg=self.theme["bg"])
        self.input_container.configure(bg=self.theme["bg_secondary"], highlightbackground=self.theme["border"])
        self.output_container.configure(bg=self.theme["bg_secondary"], highlightbackground=self.theme["border"])
        
        self.input_text.configure(bg=self.theme["input_bg"], fg=self.theme["fg"], insertbackground=self.theme["fg"])
        self.output_text.configure(bg=self.theme["input_bg"], fg=self.theme["fg"])
        
        self.refresh_sidebar_list()
        self.show_sidebar_tab(self.current_sidebar_tab)
        # More thorough apply would be needed for all buttons/labels

    def on_close(self):
        self.storage.set("geometry", self.root.winfo_geometry())
        self.storage.set("src_lang", self.src_lang_var.get())
        self.storage.set("tgt_lang", self.tgt_lang_var.get())
        self.storage.set("real_time", self.real_time_var.get())
        self.storage.set("mode", self.mode_var.get())
        self.storage.save_settings()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # Handle DPI scaling for sharp text on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = LanguageTranslatorApp(root)
    root.mainloop()
