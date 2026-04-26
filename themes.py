"""
Theme system for the Language Translator application.
Provides multiple color palettes for dark, light, ocean, and sunset themes.
"""

THEMES = {
    "dark": {
        "name": "Midnight Dark",
        "bg": "#1e1e2e",
        "bg_secondary": "#282840",
        "bg_tertiary": "#313150",
        "fg": "#e8e8f0",
        "fg_secondary": "#a0a0b8",
        "accent": "#7c6ff7",
        "accent_hover": "#9588ff",
        "success": "#50c878",
        "warning": "#ffb347",
        "error": "#ef5350",
        "border": "#3e3e5c",
        "input_bg": "#2a2a42",
        "button_bg": "#7c6ff7",
        "button_fg": "#ffffff",
        "scrollbar": "#4a4a6a",
        "selection": "#7c6ff744",
        "history_alt": "#252540",
    },
    "light": {
        "name": "Clean Light",
        "bg": "#f0f2f5",
        "bg_secondary": "#ffffff",
        "bg_tertiary": "#e4e6eb",
        "fg": "#1c1e21",
        "fg_secondary": "#606770",
        "accent": "#4a6cf7",
        "accent_hover": "#5a7cff",
        "success": "#43a047",
        "warning": "#fb8c00",
        "error": "#e53935",
        "border": "#d0d3d9",
        "input_bg": "#ffffff",
        "button_bg": "#4a6cf7",
        "button_fg": "#ffffff",
        "scrollbar": "#c0c3c9",
        "selection": "#4a6cf733",
        "history_alt": "#f7f8fa",
    },
    "ocean": {
        "name": "Ocean Blue",
        "bg": "#0b1622",
        "bg_secondary": "#112240",
        "bg_tertiary": "#1a3358",
        "fg": "#ccd6f6",
        "fg_secondary": "#8892b0",
        "accent": "#64ffda",
        "accent_hover": "#7cffe4",
        "success": "#64ffda",
        "warning": "#ffd54f",
        "error": "#ff6b6b",
        "border": "#233554",
        "input_bg": "#0b1622",
        "button_bg": "#64ffda",
        "button_fg": "#0b1622",
        "scrollbar": "#233554",
        "selection": "#64ffda22",
        "history_alt": "#0e1b2e",
    },
    "sunset": {
        "name": "Sunset Warm",
        "bg": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_tertiary": "#0f3460",
        "fg": "#eee2dc",
        "fg_secondary": "#c4b7b1",
        "accent": "#e94560",
        "accent_hover": "#f05672",
        "success": "#00b894",
        "warning": "#fdcb6e",
        "error": "#e94560",
        "border": "#2a2a4a",
        "input_bg": "#16213e",
        "button_bg": "#e94560",
        "button_fg": "#ffffff",
        "scrollbar": "#2a2a4a",
        "selection": "#e9456033",
        "history_alt": "#141429",
    },
}

def get_theme(name):
    """Return a theme dict by name, defaulting to dark."""
    return THEMES.get(name, THEMES["dark"])

def list_themes():
    """Return list of (key, display_name) tuples."""
    return [(k, v["name"]) for k, v in THEMES.items()]
