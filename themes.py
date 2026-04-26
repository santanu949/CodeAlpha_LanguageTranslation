"""
Theme system for the Language Translator application.
Optimized for CustomTkinter with colors matching the premium UI mockup.
"""

THEMES = {
    "dark": {
        "name": "Midnight Dark",
        "bg": "#12141d",
        "sidebar_bg": "#1a1c26",
        "card_bg": "#1e2130",
        "input_bg": "#1a1c26",
        "fg": "#e2e8f0",
        "fg_secondary": "#94a3b8",
        "accent": "#2dd4bf",
        "accent_hover": "#14b8a6",
        "border": "#2d3748",
        "btn_bg": "#2dd4bf",
        "btn_fg": "#0f172a",
        "success": "#10b981",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "active_border": "#2dd4bf",
    },
    "ocean": {
        "name": "Ocean Blue",
        "bg": "#0b1120",
        "sidebar_bg": "#0f172a",
        "card_bg": "#1e293b",
        "input_bg": "#0f172a",
        "fg": "#f1f5f9",
        "fg_secondary": "#94a3b8",
        "accent": "#38bdf8",
        "accent_hover": "#0ea5e9",
        "border": "#334155",
        "btn_bg": "#38bdf8",
        "btn_fg": "#0f172a",
        "success": "#34d399",
        "error": "#f87171",
        "warning": "#fbbf24",
        "active_border": "#38bdf8",
    }
}

def get_theme(name):
    return THEMES.get(name, THEMES["dark"])

def list_themes():
    return [(k, v["name"]) for k, v in THEMES.items()]
