import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
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

class LanguageTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.storage = Storage()
        self.engine = TranslationEngine(self.storage)
        
        # UI State
        self.current_theme_name = self.storage.get("theme", "dark")
        self.theme_colors = get_theme(self.current_theme_name)
        
        # Configure Window
        self.title("Premium Language Translator")
        geometry = self.storage.get("geometry", "1150x780")
        self.geometry(geometry)
        self.minsize(1000, 650)
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.theme_colors["bg"])

        self.init_variables()
        self.build_ui()
        
        # Shortcuts
        self.bind("<Control-Return>", lambda e: self.perform_translation())
        self.debounce_id = None

    def init_variables(self):
        self.src_lang_var = tk.StringVar(value=self.storage.get("src_lang", "Auto-Detect (auto)"))
        self.tgt_lang_var = tk.StringVar(value=self.storage.get("tgt_lang", "Hindi (hi)"))
        self.mode_var = tk.StringVar(value=self.storage.get("mode", "general"))
        self.real_time_var = tk.BooleanVar(value=self.storage.get("real_time", False))
        self.status_var = tk.StringVar(value="Ready")
        self.char_count_var = tk.StringVar(value="0 characters")
        self.word_count_var = tk.StringVar(value="0 words")
        self.sidebar_search_var = tk.StringVar()
        self.sidebar_search_var.trace_add("write", lambda *args: self.refresh_history())

    def build_ui(self):
        # 1. SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=self.theme_colors["sidebar_bg"], border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Search
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(25, 10))
        
        self.sidebar_search = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search", 
                                        height=40, font=("Inter", 13),
                                        fg_color=self.theme_colors["input_bg"],
                                        border_color=self.theme_colors["border"],
                                        textvariable=self.sidebar_search_var)
        self.sidebar_search.pack(fill="x")

        ctk.CTkLabel(self.sidebar, text="History", font=("Inter", 14, "bold"), text_color=self.theme_colors["fg_secondary"]).pack(anchor="w", padx=20, pady=(15, 10))

        # Scrollable History List
        self.history_container = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0)
        self.history_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_history()

        # 2. MAIN CONTENT
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=40, pady=30)

        # Header: From -> To
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))

        # Labels
        labels_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        labels_frame.pack(fill="x")
        ctk.CTkLabel(labels_frame, text="From", font=("Inter", 13, "bold"), text_color=self.theme_colors["fg"]).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(labels_frame, text="To", font=("Inter", 13, "bold"), text_color=self.theme_colors["fg"]).pack(side="right", padx=(10, 0))

        # Combos
        selectors_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        selectors_frame.pack(fill="x", pady=10)

        self.src_combo = ctk.CTkComboBox(selectors_frame, values=self.engine.language_list() + ["Auto-Detect (auto)"],
                                       variable=self.src_lang_var, width=380, height=45,
                                       fg_color=self.theme_colors["card_bg"],
                                       border_color=self.theme_colors["border"],
                                       button_color=self.theme_colors["border"],
                                       button_hover_color=self.theme_colors["active_border"])
        self.src_combo.pack(side="left")

        swap_btn = ctk.CTkButton(selectors_frame, text="⇄", width=50, height=45, font=("Inter", 20),
                                fg_color=self.theme_colors["card_bg"],
                                text_color=self.theme_colors["accent"],
                                hover_color=self.theme_colors["border"],
                                command=self.swap_languages)
        swap_btn.pack(side="left", padx=15)

        self.tgt_combo = ctk.CTkComboBox(selectors_frame, values=self.engine.language_list(),
                                       variable=self.tgt_lang_var, width=380, height=45,
                                       fg_color=self.theme_colors["card_bg"],
                                       border_color=self.theme_colors["border"],
                                       button_color=self.theme_colors["border"],
                                       button_hover_color=self.theme_colors["active_border"])
        self.tgt_combo.pack(side="right")

        # 3. TEXT PANELS
        panels_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        panels_frame.pack(fill="both", expand=True)

        # Input Panel
        self.input_card = ctk.CTkFrame(panels_frame, fg_color=self.theme_colors["card_bg"], 
                                     border_width=1, border_color=self.theme_colors["accent"])
        self.input_card.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Input Toolbar
        in_toolbar = ctk.CTkFrame(self.input_card, fg_color="transparent", height=40)
        in_toolbar.pack(fill="x", padx=15, pady=(10, 0))
        
        ctk.CTkButton(in_toolbar, text="📋 Paste", width=70, height=28, font=("Inter", 12),
                     fg_color="transparent", text_color=self.theme_colors["fg_secondary"],
                     hover_color=self.theme_colors["border"], command=self.paste_text).pack(side="left")
        
        ctk.CTkButton(in_toolbar, text="🗑️ Clear", width=70, height=28, font=("Inter", 12),
                     fg_color="transparent", text_color=self.theme_colors["fg_secondary"],
                     hover_color=self.theme_colors["border"], command=self.clear_text).pack(side="left", padx=10)

        ctk.CTkButton(in_toolbar, text="🔊 TTS", width=60, height=28, font=("Inter", 12),
                     fg_color="transparent", text_color=self.theme_colors["fg_secondary"],
                     hover_color=self.theme_colors["border"], command=lambda: self.play_tts("src")).pack(side="right")

        self.input_text = ctk.CTkTextbox(self.input_card, font=("Inter", 16), fg_color="transparent",
                                       text_color=self.theme_colors["fg"], wrap="word",
                                       padx=20, pady=10)
        self.input_text.pack(fill="both", expand=True, padx=5, pady=(0, 15))
        self.input_text.bind("<KeyRelease>", self.on_key_release)

        # Output Panel
        self.output_card = ctk.CTkFrame(panels_frame, fg_color=self.theme_colors["card_bg"], 
                                      border_width=1, border_color=self.theme_colors["border"])
        self.output_card.pack(side="right", fill="both", expand=True, padx=(15, 0))

        # Output Toolbar
        out_toolbar = ctk.CTkFrame(self.output_card, fg_color="transparent", height=40)
        out_toolbar.pack(fill="x", padx=15, pady=(10, 0))
        
        self.fav_btn = ctk.CTkButton(out_toolbar, text="☆ Favorite", width=80, height=28, font=("Inter", 12),
                                    fg_color="transparent", text_color=self.theme_colors["fg_secondary"],
                                    hover_color=self.theme_colors["border"], command=self.toggle_favorite)
        self.fav_btn.pack(side="left")

        ctk.CTkButton(out_toolbar, text="🔊 TTS", width=60, height=28, font=("Inter", 12),
                     fg_color="transparent", text_color=self.theme_colors["fg_secondary"],
                     hover_color=self.theme_colors["border"], command=lambda: self.play_tts("tgt")).pack(side="right")

        ctk.CTkButton(out_toolbar, text="📄 Copy", width=70, height=28, font=("Inter", 12),
                     fg_color="transparent", text_color=self.theme_colors["fg_secondary"],
                     hover_color=self.theme_colors["border"], command=self.copy_output).pack(side="right", padx=10)

        self.output_text = ctk.CTkTextbox(self.output_card, font=("Inter", 16), fg_color="transparent",
                                        text_color=self.theme_colors["fg"], wrap="word",
                                        padx=20, pady=10)
        self.output_text.pack(fill="both", expand=True, padx=5, pady=(0, 15))

        # 4. FOOTER
        footer = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer.pack(fill="x", pady=(25, 0))

        self.status_label = ctk.CTkLabel(footer, textvariable=self.status_var, font=("Inter", 13), 
                                       text_color=self.theme_colors["fg_secondary"])
        self.status_label.pack(side="left")

        self.translate_btn = ctk.CTkButton(footer, text="Translate", width=140, height=45, 
                                         font=("Inter", 14, "bold"),
                                         fg_color=self.theme_colors["accent"],
                                         text_color=self.theme_colors["btn_fg"],
                                         hover_color=self.theme_colors["accent_hover"],
                                         command=self.perform_translation)
        self.translate_btn.pack(side="right")

        stats_frame = ctk.CTkFrame(footer, fg_color="transparent")
        stats_frame.pack(side="right", padx=30)
        
        ctk.CTkLabel(stats_frame, textvariable=self.char_count_var, font=("Inter", 13), text_color=self.theme_colors["fg_secondary"]).pack(side="left", padx=10)
        ctk.CTkLabel(stats_frame, textvariable=self.word_count_var, font=("Inter", 13), text_color=self.theme_colors["fg_secondary"]).pack(side="left")

    # --- LOGIC ---

    def refresh_history(self):
        for widget in self.history_container.winfo_children():
            widget.destroy()
        
        q = self.sidebar_search_var.get().lower()
        items = self.storage.history
        if q:
            items = [i for i in items if q in i["src_text"].lower() or q in i["tgt_text"].lower()]

        for item in items:
            btn = ctk.CTkButton(self.history_container, text="", height=70, corner_radius=8,
                               fg_color="transparent", hover_color=self.theme_colors["card_bg"],
                               anchor="nw", command=lambda i=item: self.load_history_item(i))
            btn.pack(fill="x", pady=2)
            
            # Sub-labels for the button
            title = ctk.CTkLabel(btn, text=f"{item['src_lang'].upper()} ➔ {item['tgt_lang'].upper()}", 
                                font=("Inter", 11, "bold"), text_color=self.theme_colors["accent"])
            title.place(x=15, y=10)
            
            snippet = item["src_text"][:35] + ("..." if len(item["src_text"]) > 35 else "")
            txt = ctk.CTkLabel(btn, text=snippet, font=("Inter", 12), text_color=self.theme_colors["fg"])
            txt.place(x=15, y=35)

    def load_history_item(self, item):
        self.src_lang_var.set(self.engine.lang_name(item["src_lang"]))
        self.tgt_lang_var.set(self.engine.lang_name(item["tgt_lang"]))
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", item["src_text"])
        self.set_output(item["tgt_text"])
        self.update_stats()

    def on_key_release(self, event=None):
        self.update_stats()
        if self.real_time_var.get():
            if self.debounce_id: self.after_cancel(self.debounce_id)
            self.debounce_id = self.after(800, self.perform_translation)

    def update_stats(self):
        text = self.input_text.get("1.0", "end-1c")
        self.char_count_var.set(f"{len(text)} characters")
        self.word_count_var.set(f"{len(text.split())} words")

    def perform_translation(self):
        text = self.input_text.get("1.0", "end-1c").strip()
        if not text: return
        
        self.status_var.set("Translating...")
        self.translate_btn.configure(state="disabled")
        
        src_raw = self.src_lang_var.get()
        tgt_raw = self.tgt_lang_var.get()
        src_code = self.engine.parse_lang_selection(src_raw)
        tgt_code = self.engine.parse_lang_selection(tgt_raw)
        mode = self.mode_var.get().lower()

        if src_code == "auto":
            src_code = self.engine.detect(text)
            self.status_var.set(f"Detected: {self.engine.lang_name(src_code)}")

        def on_done(result):
            self.after(0, lambda: self._handle_success(text, result, src_code, tgt_code, mode))

        def on_error(err):
            self.after(0, lambda: self.status_var.set("Error"))
            self.after(0, lambda: self.translate_btn.configure(state="normal"))
            self.after(0, lambda: messagebox.showerror("Error", err))

        self.engine.translate(text, src_code, tgt_code, mode, on_done, on_error)

    def _handle_success(self, src, res, sl, tl, mode):
        self.set_output(res)
        self.status_var.set("Ready")
        self.translate_btn.configure(state="normal")
        self.storage.add_history(src, res, sl, tl, mode)
        self.refresh_history()

    def set_output(self, text):
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)

    def swap_languages(self):
        s, t = self.src_lang_var.get(), self.tgt_lang_var.get()
        if "auto" in s.lower(): return
        self.src_lang_var.set(t)
        self.tgt_lang_var.set(s)

    def clear_text(self):
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.update_stats()

    def paste_text(self):
        self.input_text.insert("insert", pyperclip.paste())
        self.update_stats()

    def copy_output(self):
        pyperclip.copy(self.output_text.get("1.0", "end-1c"))
        self.status_var.set("Copied!")
        self.after(2000, lambda: self.status_var.set("Ready"))

    def play_tts(self, side):
        txt = self.input_text.get("1.0", "end-1c") if side == "src" else self.output_text.get("1.0", "end-1c")
        if txt: tts_handler.speak(txt)

    def toggle_favorite(self):
        # Implementation similar to previous, but using storage
        pass

if __name__ == "__main__":
    app = LanguageTranslatorApp()
    app.mainloop()
